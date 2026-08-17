import json

with open("exports/session_audit_summary.json", "r", encoding="utf-8") as f:
    data = json.load(f)

for i, s in enumerate(data[:16]):
    print(f"=== [{i+1}] {s['id']} | JST: {s['mtime_jst']} ===")
    print(f"Role: {s['role']} | Steps: {s['steps']} | ToolsCalled: {s['tools_called_count']}")
    print(f"First User: {s['first_user_msg'][:120]}")
    print(f"Last User:  {s['last_user_msg'][:150]}")
    print(f"Last Model: {s['last_model_msg'][:150]}")
    print(f"Last Tool:  {s['last_tool_call']}")
    print()
