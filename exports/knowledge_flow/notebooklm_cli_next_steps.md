# NotebookLM CLI Next Steps

Generated: 2026-05-22T00:56:13+09:00

## Current Status

- Google Drive sync: done
- Workspace account: `k-umezawa@ml-mightylink.com`
- NotebookLM CLI status: `auth_required`

## Google Docs Synced From docs/

- `docs/ANTIGRAVITY_GUIDE.md`: https://docs.google.com/document/d/1d0SMuvOQXnGLxmNj7d1ktfWczSmxlWL0wblxlYDMH4E/edit?usp=drivesdk
- `docs/BACKEND_AI_PIPELINE.md`: https://docs.google.com/document/d/1duxDhC6yjS-XlyWxse_XdaiRjq88cZz8aBCt0GRxUWg/edit?usp=drivesdk
- `docs/CEO_PRESENTATION_DECISION_PACK_2026-06-02.md`: https://docs.google.com/document/d/1XJeHY18JEEeaz4Dc28UHrOYbA7hhZ7ENfyI3TEGPnqc/edit?usp=drivesdk
- `docs/CEO_PRESENTATION_PREP_2026-06-02.md`: https://docs.google.com/document/d/1hIcqCfKtRPPVtXrKizMesGpI7j9VACrXgQicHy4XD6o/edit?usp=drivesdk
- `docs/CODEX_CONTINUATION_NOTES.md`: https://docs.google.com/document/d/1akLsJ_85jkqcH3aTaae8h5u1xmHGooJn5UlklHvQyfE/edit?usp=drivesdk
- `docs/database.md`: https://docs.google.com/document/d/1WVp_vmYeiCZfFWbCpHNfmwGoUeBADuMjyLySBHrh9bI/edit?usp=drivesdk
- `docs/DEVELOPMENT_KNOWLEDGE_FLOW.md`: https://docs.google.com/document/d/1SS44DK0H57KFdX4jHDucbYe6PRN2ofUllaaLr5zioYU/edit?usp=drivesdk
- `docs/GOOGLE_WORKSPACE_MIGRATION_RUNBOOK.md`: https://docs.google.com/document/d/1xb9e3AQt7uGSvQvu-D12CGqchlh5Z01FFn44Dkhza8I/edit?usp=drivesdk
- `docs/INTEGRATION_DEMO_EVIDENCE_2026-06-02.md`: https://docs.google.com/document/d/1AV77haOyRnghdHXeYQgUUWosS07YA5semyeOadAzfUs/edit?usp=drivesdk
- `docs/PROJECT_STRUCTURE.md`: https://docs.google.com/document/d/1ACZgUCWCCSM6o7oNh9qsAIk5wfyq7mKsHCiyQxNsrcg/edit?usp=drivesdk
- `docs/requirements.md`: https://docs.google.com/document/d/1G6XmZoa-LhnKuq4At6PVPJrr7IaT5XrP7IYYnwPKAPA/edit?usp=drivesdk
- `docs/SETUP_GUIDE.md`: https://docs.google.com/document/d/16DonChND2WzQFWDZ8aubajlZdVB1aVnMsXnYLXE7xUI/edit?usp=drivesdk
- `docs/WBS.md`: https://docs.google.com/document/d/16s5eoPSBLInfS6Kr9Hj4Qgc3y4QXjyjNSbojvZNxBuQ/edit?usp=drivesdk
- `docs/WBS_SYNC_GUIDE.md`: https://docs.google.com/document/d/1QFWYMFWM-_a2z8YC_hnxpAiAomzIb3t1mO_uPPPYjnY/edit?usp=drivesdk

## Re-authentication

NotebookLM CLI currently needs browser re-authentication before sources can be added to NotebookLM.

```powershell
notebooklm login
python scripts/sync_docs_to_notebooklm.py
```

During `notebooklm login`, select `k-umezawa@ml-mightylink.com`.

## Last CLI Error

```text
Authentication expired or invalid. Run 'notebooklm login' to re-authenticate.
```

## Agent Retrieval Command

After authentication, the script will add the Drive docs as NotebookLM sources and write:

- `exports/knowledge_flow/notebooklm_agent_brief.md`
- `exports/knowledge_flow/notebooklm_agent_brief.json`

These files are the agent-facing design and roadmap summary for subsequent Codex work.
