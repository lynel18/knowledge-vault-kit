---
name: vault-health
description: Read-only diagnostic health check for the KNOWLEDGE math vault. Use when the user asks for a vault health check, vault status, system checkup, diagnostics, sanity check, or "is my vault healthy" — checks git, protection hook, MCP server, pipeline tests, templates, Dataview, snippets, junk files, vault purity, Yanki queue, and exercise ladder; prints a report table. Diagnostics only — never fixes, never prints secrets.
---

# vault-health — read-only diagnostics

Governing contract: `D:\KNOWLEDGE\AGENTS.md`. This skill ONLY observes and reports.
No fixes (that is `vault-doctor`). Never print the REST API key, tokens, or any
secret found in config files — report "key present" at most.

Python: `C:\Users\User\AppData\Local\Programs\Python\Python314\python.exe`

## Procedure

Run every check below, then print one report table. Track today's date (for due
calculations) before you start.

1. **Git state** — Run `git -C "D:\KNOWLEDGE" status --porcelain` and
   `git -C "D:\KNOWLEDGE" log -3 --oneline`.
   Good: clean tree or only intentional untracked study notes; on branch `master`.
   Report: dirty-file count, last commit hash+subject.

2. **Protection hook** — Check `"D:\KNOWLEDGE\.git\hooks\pre-commit"` exists
   (`ls -la`), then read it.
   Good: present, and contains the `VAULT_UNLOCK=1` bypass plus the protected
   globs (`90-templates/* .obsidian/* _math-system/* .true-recall/* 50-srs/Yanki/* 00-home/* .zcode/* AI-Math-Note-Protocol.md AGENTS.md`).
   Report: present/absent, matches spec or not. Never edit it here.

3. **MCP registration** — Read `C:\Users\User\.zcode\cli\config.json` and locate
   `mcp.servers.knowledge-vault` WITHOUT printing the whole file.
   Good: `command` runs Python with arg `D:\KNOWLEDGE\.system\mcp-knowledge-vault\server.py`.
   Then call the MCP tool `health_check` (available in-session).
   Good: returns vault path, git HEAD, hook status, REST API status without error.
   If the tool is missing → report FAIL "knowledge-vault not connected in this session
   (restart session or fix registration)". If the registered path is NOT the
   `.system` one → report WARN with the wrong path.

4. **Pipeline tests** — Run:
   `cd "D:\KNOWLEDGE\.system\pipeline" && "C:\Users\User\AppData\Local\Programs\Python\Python314\python.exe" -m pytest -q`
   Good: exit 0, "N passed", 0 failed.
   If import errors (e.g. pydantic missing) → FAIL with the exact error; do not retry blindly.

5. **Templates present** — List `D:\KNOWLEDGE\90-templates\` (read-only; protected).
   Good: `ts-section.md tc-concept.md tt-theorem.md tf-formula.md tp-problem.md tr-review.md`
   (plus optionally `tx-exercise.md`). Report missing ones by name.

6. **Dataview JS** — Read `D:\KNOWLEDGE\.obsidian\plugins\dataview\data.json`.
   Good: `"enableDataviewJs": true`. Report actual value if false/absent.

7. **Snippets** — List `D:\KNOWLEDGE\.obsidian\snippets\`.
   Good: at least one `.css` (expected set includes math-clarity.css). Report count.

8. **Junk files at vault root** — List `D:\KNOWLEDGE` root. Legitimate root entries:
   the lane dirs (00-home … 90-templates), `AGENTS.md`, `_math-system`, `Math Texbook JSON`,
   `.git`, `.obsidian`, `.zcode`, `.trash`.
   Junk = anything else, e.g. `Untitled.md`, `null`, `*.tmp`, stray exports.
   Report each junk item by exact name.

9. **Vault purity** — Run
   `git -C "D:\KNOWLEDGE" ls-files | grep -Ei "\.(py|js|exe|sh|bat)$"`,
   excluding paths starting `.obsidian/plugins/`, `.system/`, `_math-system/`.
   Good: no hits outside those prefixes (AGENTS.md: never create code files here).
   Report any violating path.

10. **Yanki + queues** — Count files in `D:\KNOWLEDGE\50-srs\Yanki\` (expect `.md`
    cards; flag any `.json` there), `D:\KNOWLEDGE\50-srs\pending_anki\` (staged
    `card_*.json` awaiting approval), and `D:\KNOWLEDGE\50-srs\deferred_queue\`.
    Report: counts + oldest pending file's date. Pending > 0 is not an error —
    it means an approval review is due; say that.

11. **Exercise ladder sanity** — Scan `D:\KNOWLEDGE\30-study\Exercises\*.md`
    frontmatter. Fields: `status: active|mastered`, `ladder_step: 0-5`,
    `next_due: YYYY-MM-DD`, `last_result: pass|fail`.
    Due today = `status: active` AND `next_due <= today`.
    Good: parseable frontmatter; report due count (with names), malformed notes,
    and any `status: mastered` with `ladder_step < 5` or active-with-invalid-step.
    If the folder is empty → report "no exercises yet" (PASS, not a failure).

12. **Training Ladder scheduler** — Check
    `D:\KNOWLEDGE\.system\scheduler\logs\heartbeat.jsonl` (last line): its `date`
    should be today or yesterday (runs daily 07:00 via Task Scheduler job
    "KNOWLEDGE Training Ladder Scheduler"; `schtasks /Query /TN "KNOWLEDGE Training Ladder Scheduler"`).
    Also confirm today's digest exists: `30-study/Reviews/training-digest-<today>.md`.
    Stale > 36h or missing task → WARN with fix: run
    `python D:\KNOWLEDGE\.system\scheduler\exercise_scheduler.py` and check Task Scheduler.
    `"ok": false` in the heartbeat → list its warnings.

## Report format

Print:

```
| # | Check | Status | Detail |
|---|-------|--------|--------|
```

Status: PASS / FAIL / WARN (WARN = degraded but usable). Then one line per FAIL
with the exact evidence (command output snippet). Never invent a PASS — if you
could not run a check, mark it FAIL with "not run: <reason>".

Optionally offer to save the report via MCP `write_note` to
`80-agent/decisions/YYYY-MM-DD-health.md` (unprotected lane) — ask the user
first; do not save unasked.
