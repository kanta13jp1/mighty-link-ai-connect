import json
import sys

with open("exports/session_audit_summary.json", "r", encoding="utf-8") as f:
    data = json.load(f)

print(f"Total sessions: {len(data)}\n")
for i, s in enumerate(data[:25]):
    print(f"[{i+1}] ID: {s['id']} | JST: {s['mtime_jst']} | Steps: {s['steps']} | Status: {s['status']}")
    print(f"    Role:  {s['role']}")
    print(f"    First: {s['first_user_msg'][:100]}")
    print(f"    LastU: {s['last_user_msg'][:100]}")
    print(f"    LastM: {s['last_model_msg'][:100]}")
    print(f"    Tool:  {s['last_tool_call']}")
    print("-" * 70)
