# MightyLINK Antigravity Live Demo

This public repository supports the August 26 Antigravity workshop. It demonstrates a test-first workflow: define acceptance criteria, build with an IDE agent, inspect the same workspace from CLI and SDK, verify in a browser, and publish to GitHub Pages.

- All content is synthetic. Customer, employee, credential, and production data are prohibited.
- The comparison covers only Codex, Claude Code, Claude Cowork, Kiro, and Antigravity.
- Product facts were checked against official sources on 2026-08-13 JST.
- Official icons are stored locally so they remain visible on GitHub Pages; `ICON_SOURCES.md` records provenance.
- `/grill-me` and `/find-skills` are baseline workspace Skills in `.agents/skills/`.
- `anthropics/skills@frontend-design` is installed project-locally during the demo and removed after rehearsal.
- The production MightyLINK repository and Firebase Hosting are not used.

## Test-first flow

Read `TEST_SPEC.md` before implementation. Run the contract tests after every material change:

```powershell
python -m unittest discover -s tests -v
node --check app.js
node --check product-data.js
```

The tests prevent scope drift, missing official icons, undated updates, unofficial source domains, incomplete comparison axes, and the return of unverified fixed quota claims.

## Demo files

1. `PROMPT_00_GRILL_ME.txt`
2. `PROMPT_01_FIND_SKILLS.txt`
3. `PROMPT_02_INSTALL_SKILL.txt`
4. `PROMPT_03_BUILD.txt`
5. `PROMPT_04_APPLY_SKILL.txt`
6. `PROMPT_05_MCP_CHECK.txt`
7. `PROMPT_06_PUBLISH.txt`
8. `PROMPT_10_CLI_READONLY.txt`
9. `PROMPT_11_SDK_READONLY.txt`

`SOURCE_AUDIT.md` records the official evidence behind each product card. `SELF_REVIEW.md` records ten distinct review passes and the resulting fixes. `antigravity_sdk_readonly.py` runs the SDK audit with `BuiltinTools.read_only()`.

## Rehearsal reset

Remove only the live-installed Skill, then revert the rehearsal publish commit and push the revert. Do not use `reset --hard` or force push.

```powershell
npx skills remove frontend-design --agent antigravity -y
$skillsRoot = (Resolve-Path .agents/skills).Path
$skillPath = Join-Path $skillsRoot 'frontend-design'
if (Test-Path -LiteralPath $skillPath) {
  if ((Split-Path $skillPath -Parent) -ne $skillsRoot) { throw 'Unexpected Skill path' }
  Get-ChildItem -LiteralPath $skillPath -File | Remove-Item -Force
  Remove-Item -LiteralPath $skillPath -Force
}
if (Test-Path -LiteralPath .\skills-lock.json) { Remove-Item -LiteralPath .\skills-lock.json -Force }
npx skills list --json
git revert --no-edit <rehearsal-publish-commit-sha>
git push origin main
```
