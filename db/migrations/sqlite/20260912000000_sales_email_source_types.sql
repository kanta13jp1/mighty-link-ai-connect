-- sqlite-rebuild
-- Run through manage_db_migrations.py: one transaction, foreign key validation.
CREATE TEMP TABLE sales_source_sequences AS
SELECT name, seq FROM sqlite_sequence WHERE name IN ('sales_mailbox_sources', 'sales_email_messages');

CREATE TABLE sales_mailbox_sources_new (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    source_key VARCHAR(120) NOT NULL UNIQUE,
    display_name VARCHAR(160) NOT NULL,
    source_type VARCHAR(32) NOT NULL CHECK (source_type IN ('gmail', 'manual_upload', 'eml', 'txt', 'csv', 'api', 'imap', 'pop3', 'thunderbird_local')),
    owner_user_id VARCHAR(255),
    retention_days INTEGER NOT NULL DEFAULT 90 CHECK (retention_days BETWEEN 1 AND 365),
    metadata TEXT NOT NULL DEFAULT '{}',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
INSERT INTO sales_mailbox_sources_new SELECT * FROM sales_mailbox_sources;
DROP TABLE sales_mailbox_sources;
ALTER TABLE sales_mailbox_sources_new RENAME TO sales_mailbox_sources;

CREATE TABLE sales_email_messages_new (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    mailbox_source_id INTEGER,
    message_id_hash CHAR(64),
    dedupe_key CHAR(64) NOT NULL UNIQUE,
    sender_hash CHAR(64) NOT NULL,
    sender_domain VARCHAR(255),
    normalized_subject VARCHAR(300) NOT NULL,
    received_at TIMESTAMP,
    body_hash CHAR(64) NOT NULL,
    body_excerpt TEXT,
    source_path TEXT,
    source_type VARCHAR(32) NOT NULL CHECK (source_type IN ('gmail', 'manual_upload', 'eml', 'txt', 'csv', 'api', 'imap', 'pop3', 'thunderbird_local')),
    raw_storage_policy VARCHAR(64) NOT NULL DEFAULT 'hash_and_redacted_excerpt_only',
    ingest_status VARCHAR(32) NOT NULL DEFAULT 'new' CHECK (ingest_status IN ('new', 'deduped', 'parsed', 'reviewed', 'rejected', 'error')),
    duplicate_of_id INTEGER,
    metadata TEXT NOT NULL DEFAULT '{}',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CHECK (raw_storage_policy = 'hash_and_redacted_excerpt_only'),
    FOREIGN KEY(mailbox_source_id) REFERENCES sales_mailbox_sources(id) ON DELETE SET NULL,
    FOREIGN KEY(duplicate_of_id) REFERENCES sales_email_messages(id) ON DELETE SET NULL
);
INSERT INTO sales_email_messages_new SELECT * FROM sales_email_messages;
DROP TABLE sales_email_messages;
ALTER TABLE sales_email_messages_new RENAME TO sales_email_messages;
CREATE INDEX idx_sales_email_messages_dedupe_key ON sales_email_messages(dedupe_key);
CREATE INDEX idx_sales_email_messages_body_hash ON sales_email_messages(body_hash);
CREATE INDEX idx_sales_email_messages_sender_domain ON sales_email_messages(sender_domain);
UPDATE sqlite_sequence SET seq = max(seq, (SELECT seq FROM sales_source_sequences WHERE name = sqlite_sequence.name))
WHERE name IN (SELECT name FROM sales_source_sequences);
DROP TABLE sales_source_sequences;
