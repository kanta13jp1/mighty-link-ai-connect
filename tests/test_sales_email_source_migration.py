"""Exercise the real upgrade on populated SQLite databases."""

import sys
from pathlib import Path
from types import SimpleNamespace

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import manage_db_migrations as migrations
from sync_sales_emails import sync_raw_email_list
from sales_email_ingest import RawSalesEmail


def legacy_database(path):
    conn = migrations.connect_sqlite(path)
    migrations.ensure_ledger(conn, "sqlite")
    items = migrations.load_migrations(migrations.default_migration_dir("sqlite"))
    for item in items[:-1]:
        migrations.execute_migration(conn, "sqlite", item)
    return conn, items[-1]


def test_upgrade_preserves_rows_relations_sequences_and_dedupe(tmp_path):
    conn, upgrade = legacy_database(tmp_path / "mail.db")
    conn.execute("INSERT INTO sales_mailbox_sources(id,source_key,display_name,source_type) VALUES(7,'legacy','Legacy','api')")
    conn.execute("INSERT INTO sales_email_messages(id,mailbox_source_id,dedupe_key,sender_hash,normalized_subject,body_hash,source_type) VALUES(11,7,'old','sender','Old mail','body','api')")
    conn.execute("INSERT INTO sales_email_messages(id,duplicate_of_id,dedupe_key,sender_hash,normalized_subject,body_hash,source_type) VALUES(12,11,'copy','sender','Copy','body','api')")
    conn.execute("INSERT INTO project_requirements(id,message_id,title) VALUES(8,11,'Existing project')")
    conn.execute("INSERT INTO sales_email_entities(message_id,entity_type,label,normalized_label) VALUES(11,'skill','Python','python')")
    conn.execute("UPDATE sqlite_sequence SET seq=100 WHERE name IN ('sales_email_messages','sales_mailbox_sources')")
    conn.commit()
    before = {table: conn.execute(f"SELECT * FROM {table}").fetchall() for table in ('sales_mailbox_sources','sales_email_messages','project_requirements','sales_email_entities')}
    migrations.execute_migration(conn, "sqlite", upgrade)
    for table, rows in before.items():
        assert conn.execute(f"SELECT * FROM {table}").fetchall() == rows
    assert conn.execute("PRAGMA foreign_keys").fetchone()[0] == 1
    assert conn.execute("PRAGMA foreign_key_check").fetchall() == []
    indexes = {row[1] for row in conn.execute("PRAGMA index_list(sales_email_messages)")}
    assert {'idx_sales_email_messages_dedupe_key', 'idx_sales_email_messages_body_hash',
            'idx_sales_email_messages_sender_domain'} <= indexes
    db = SimpleNamespace(use_supabase=False, sqlite_conn=conn)
    for source in ('imap','pop3','thunderbird_local'):
        mail = RawSalesEmail(source_path=f'{source}://test', source_type=source, sender='test@example.test', subject=source, body='Synthetic mail')
        assert sync_raw_email_list(db, [mail]) == 1
        assert sync_raw_email_list(db, [mail]) == 0
        row = conn.execute("SELECT id,source_type FROM sales_email_messages WHERE normalized_subject=?", (source,)).fetchone()
        assert row[0] > 100 and row[1] == source
    with pytest.raises(Exception, match='CHECK constraint'):
        conn.execute("UPDATE sales_email_messages SET source_type='invalid'")
    conn.rollback()
    conn.close()
    assert migrations.main(['apply','--engine','sqlite','--sqlite-path',str(tmp_path / 'mail.db')]) == 0


def test_empty_tables_keep_previous_autoincrement_high_watermark(tmp_path):
    conn, upgrade = legacy_database(tmp_path / 'empty.db')
    conn.execute("INSERT INTO sales_mailbox_sources(id,source_key,display_name,source_type) VALUES(150,'gone','Gone','api')")
    conn.execute('DELETE FROM sales_mailbox_sources')
    conn.commit()
    migrations.execute_migration(conn, 'sqlite', upgrade)
    conn.execute("INSERT INTO sales_mailbox_sources(source_key,display_name,source_type) VALUES('new','New','imap')")
    assert conn.execute('SELECT id FROM sales_mailbox_sources').fetchone()[0] == 151
    conn.close()


def test_failed_rebuild_rolls_back_schema_data_and_ledger(tmp_path):
    conn, upgrade = legacy_database(tmp_path / 'mail.db')
    conn.execute('PRAGMA foreign_keys=OFF')
    conn.execute("INSERT INTO project_requirements(message_id,title) VALUES(999,'Orphan')")
    conn.commit()
    conn.execute('PRAGMA foreign_keys=ON')
    schema = conn.execute("SELECT sql FROM sqlite_master WHERE name='sales_email_messages'").fetchone()[0]
    with pytest.raises(migrations.MigrationError, match='foreign key validation'):
        migrations.execute_migration(conn, 'sqlite', upgrade)
    assert conn.execute("SELECT sql FROM sqlite_master WHERE name='sales_email_messages'").fetchone()[0] == schema
    assert conn.execute('SELECT message_id FROM project_requirements').fetchone()[0] == 999
    assert upgrade.version not in migrations.load_applied(conn)
    assert conn.execute('PRAGMA foreign_keys').fetchone()[0] == 1
    assert not conn.in_transaction
    conn.close()
