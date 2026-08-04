#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Connect all markdown nodes in the project knowledge graph so that no isolated markdown files exist.

Generates docs/MASTER_KNOWLEDGE_GRAPH.md and links all orphan/isolated files
to master index hubs, ensuring 100% connectivity in Obsidian Graph View.
"""

import re
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
DOCS_DIR = PROJECT_ROOT / "docs"
VAULT_HOME = PROJECT_ROOT / "exports" / "knowledge_flow" / "obsidian_vault" / "Mighty Skill-Bridge Home.md"
MASTER_GRAPH_FILE = DOCS_DIR / "MASTER_KNOWLEDGE_GRAPH.md"


def collect_md_files() -> list[Path]:
    return [
        p for p in PROJECT_ROOT.glob("**/*.md")
        if not any(part.startswith(".") or part in ["venv", "node_modules"] for part in p.parts)
    ]


def build_path_map(md_files: list[Path]) -> dict[str, Path]:
    path_map = {}
    for p in md_files:
        rel = p.relative_to(PROJECT_ROOT).as_posix()
        path_map[rel] = p
        path_map[p.stem] = p
        path_map[p.name] = p
    return path_map


def get_outgoing_links(p: Path, path_map: dict[str, Path]) -> set[Path]:
    try:
        content = p.read_text(encoding="utf-8", errors="ignore")
    except Exception:
        return set()
    wikilinks = re.findall(r"\[\[([^\]\|]+)(?:\|[^\]]+)?\]\]", content)
    mdlinks = re.findall(r"\[[^\]]*\]\(([^)]+)\)", content)
    res = set()
    for l in wikilinks + mdlinks:
        l_clean = l.split("#")[0].strip()
        if not l_clean:
            continue
        target = path_map.get(l_clean) or path_map.get(l_clean + ".md") or path_map.get(Path(l_clean).name)
        if target:
            res.add(target)
    return res


def find_isolated_files() -> list[Path]:
    md_files = collect_md_files()
    path_map = build_path_map(md_files)
    links = {p: get_outgoing_links(p, path_map) for p in md_files}
    backlinks = {p: set() for p in md_files}
    for p, targets in links.items():
        for t in targets:
            if t in backlinks:
                backlinks[t].add(p)
    return [p for p in md_files if len(links[p]) == 0 and len(backlinks[p]) == 0]


def generate_master_knowledge_graph() -> None:
    md_files = collect_md_files()
    
    docs_files = []
    export_files = []
    knowledge_flow_files = []
    vault_files = []
    other_files = []
    
    for p in sorted(md_files):
        rel = p.relative_to(PROJECT_ROOT).as_posix()
        if p == MASTER_GRAPH_FILE:
            continue
        if rel.startswith("docs/"):
            docs_files.append(rel)
        elif rel.startswith("exports/knowledge_flow/obsidian_vault/"):
            vault_files.append(rel)
        elif rel.startswith("exports/knowledge_flow/"):
            knowledge_flow_files.append(rel)
        elif rel.startswith("exports/"):
            export_files.append(rel)
        else:
            other_files.append(rel)

    content = [
        "# Master Knowledge Graph Index",
        "",
        "全ナレッジノード（ドキュメント・監査レポート・WBS・ADR・Obsidian Vault）を統合するマスター知識グラフ索引起点です。",
        "Obsidian Graph View において全ノードの接続性を担保し、孤立ノード（Isolates）を排除します。",
        "",
        "## 1. 主要インデックス & ガバナンス",
        "- [WBS Management Table](WBS.md)",
        "- [Handover Documentation Package](HANDOVER_DOCUMENTATION_PACKAGE.md)",
        "- [Operations Runbook Catalog](OPERATIONS_RUNBOOK_CATALOG.md)",
        "- [Quality Guard Catalog](QUALITY_GUARD_CATALOG.md)",
        "- [Architecture Decision Records (ADR)](ARCHITECTURE_DECISION_RECORDS.md)",
        "- [Project Glossary](PROJECT_GLOSSARY.md)",
        "- [Obsidian Development Workflow](OBSIDIAN_DEVELOPMENT_WORKFLOW.md)",
        "- [Development Knowledge Flow](DEVELOPMENT_KNOWLEDGE_FLOW.md)",
        "",
        "## 2. ドキュメント全一覧 (docs/)",
    ]
    
    for rel in docs_files:
        p = PROJECT_ROOT / rel
        rel_from_docs = p.relative_to(DOCS_DIR).as_posix()
        content.append(f"- [{p.name}]({rel_from_docs})")
        
    content.extend([
        "",
        "## 3. 監査 & 報告レポート一覧 (exports/)",
    ])
    for rel in export_files:
        p = PROJECT_ROOT / rel
        rel_from_docs = "../" + rel
        content.append(f"- [{p.name}]({rel_from_docs})")
        
    content.extend([
        "",
        "## 4. ナレッジフロー成果物一覧 (exports/knowledge_flow/)",
    ])
    for rel in knowledge_flow_files:
        p = PROJECT_ROOT / rel
        rel_from_docs = "../" + rel
        content.append(f"- [{p.name}]({rel_from_docs})")

    content.extend([
        "",
        "## 5. Obsidian Vault 雛形一覧 (exports/knowledge_flow/obsidian_vault/)",
    ])
    for rel in vault_files:
        p = PROJECT_ROOT / rel
        rel_from_docs = "../" + rel
        content.append(f"- [{p.name}]({rel_from_docs})")

    content.extend([
        "",
        "## 6. プロジェクト構成・レポート・その他 (root / db / reports)",
    ])
    for rel in other_files:
        p = PROJECT_ROOT / rel
        rel_from_docs = "../" + rel
        content.append(f"- [{p.name}]({rel_from_docs})")

    MASTER_GRAPH_FILE.write_text("\n".join(content) + "\n", encoding="utf-8")
    print(f"[+] Updated {MASTER_GRAPH_FILE.relative_to(PROJECT_ROOT)} with links to {len(md_files)} markdown files.")


def update_obsidian_vault_home() -> None:
    if not VAULT_HOME.exists():
        return
    home_content = VAULT_HOME.read_text(encoding="utf-8")
    additions = [
        "- [[00_Inbox/README|00_Inbox]]",
        "- [[10_ADR_Drafts/README|10_ADR_Drafts]]",
        "- [[20_Prompts/README|20_Prompts]]",
        "- [[30_Meetings/README|30_Meetings]]",
        "- [[40_Canvas/README|40_Canvas]]",
        "- [Master Knowledge Graph Index](../../../docs/MASTER_KNOWLEDGE_GRAPH.md)",
        "- [Obsidian Development Workflow Guide](../../../docs/OBSIDIAN_DEVELOPMENT_WORKFLOW.md)",
    ]
    new_lines = []
    for line in home_content.splitlines():
        new_lines.append(line)
        if line.strip() == "## Key Notes":
            for add in additions:
                if add not in home_content:
                    new_lines.append(add)
    VAULT_HOME.write_text("\n".join(new_lines) + "\n", encoding="utf-8")
    
    # Ensure vault READMEs have backlinks to Home Note and Master Index
    vault_readmes = [
        PROJECT_ROOT / "exports" / "knowledge_flow" / "obsidian_vault" / "00_Inbox" / "README.md",
        PROJECT_ROOT / "exports" / "knowledge_flow" / "obsidian_vault" / "10_ADR_Drafts" / "README.md",
        PROJECT_ROOT / "exports" / "knowledge_flow" / "obsidian_vault" / "20_Prompts" / "README.md",
        PROJECT_ROOT / "exports" / "knowledge_flow" / "obsidian_vault" / "30_Meetings" / "README.md",
        PROJECT_ROOT / "exports" / "knowledge_flow" / "obsidian_vault" / "40_Canvas" / "README.md",
    ]
    for rme in vault_readmes:
        if rme.exists():
            txt = rme.read_text(encoding="utf-8")
            if "Mighty Skill-Bridge Home" not in txt:
                txt += "\n\n- [[Mighty Skill-Bridge Home]]\n- [Master Knowledge Graph Index](../../../../docs/MASTER_KNOWLEDGE_GRAPH.md)\n"
                rme.write_text(txt, encoding="utf-8")

    # Ensure db/migrations/README.md has a link to Master Index
    db_readme = PROJECT_ROOT / "db" / "migrations" / "README.md"
    if db_readme.exists():
        txt = db_readme.read_text(encoding="utf-8")
        if "MASTER_KNOWLEDGE_GRAPH" not in txt:
            txt += "\n\n- [Master Knowledge Graph Index](../../docs/MASTER_KNOWLEDGE_GRAPH.md)\n"
            db_readme.write_text(txt, encoding="utf-8")


def connect_all_knowledge_nodes() -> list[Path]:
    generate_master_knowledge_graph()
    update_obsidian_vault_home()
    return find_isolated_files()


def main():
    print("[*] Connecting all nodes in Knowledge Graph...")
    isolated = connect_all_knowledge_nodes()
    print(f"[*] Remaining isolated files: {len(isolated)}")
    if isolated:
        for p in isolated:
            print("  -", p.relative_to(PROJECT_ROOT))
    else:
        print("[SUCCESS] All 100% of markdown files are now connected in the Knowledge Graph! (Isolated: 0)")


if __name__ == "__main__":
    main()
