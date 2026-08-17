---
name: vault-doctor
description: Diagnose AND fix vault problems for the KNOWLEDGE math vault. Use when the user asks to fix the vault, repair the vault, run the vault doctor, clean junk, restore the hook, re-enable Dataview, or fix MCP registration — runs the same checks as vault-health, then applies SAFE-FIXes (verified after each) and asks before anything touching protected paths, notes, templates, or databases. Never fabricates success.
---

# vault-doctor — diagnose, then fix

Governing contract: `D:\KNOWLEDGE\AGENTS.md` (protected paths, ask-first rule).
Python: `C:\Users\User\AppData\Local\Programs\Python\Python314\python.exe`.

## Phase 1 — Diagnose (read-only)

Run every check from the `vault-health` skill (git state, pre-commit hook, MCP
registration + `health_check` tool, `pytest -q` in `D:\KNOWLEDGE\.system\pipeline`,
templates in `90-templates`, `"enableDataviewJs": true` in
`D:\KNOWLEDGE\.obsidian\plugins\dataview\data.json`, snippets in
`.obsidian/snippets`, junk at vault root, code-file purity, Yanki/pending/deferred
queue counts, exercise ladder). If that skill is not loaded, re-run its checks
manually — same commands, same PASS/FAIL criteria. Never print secrets
(REST API key, tokens) — "key present" is the maximum disclosure.

## Phase 2 — Classify every finding

Show the user a table before touching anything:

| Finding | Class | Proposed action |
|---|---|---|

**SAFE-FIX — apply immediately, verify after each:**

1. Junk files at vault root (e.g. `Untitled.md`, `null`, `*.tmp`): show the exact
   list AND `head` each file first. Delete only files that are empty or clearly
   junk; if a file has real content → reclassify ASK-FIRST.
2. MCP config re-point: if `C:\Users\User\.zcode\cli\config.json` →
   `mcp.servers.knowledge-vault` does not point at
   `D:\KNOWLEDGE\.system\mcp-knowledge-vault\server.py`, fix that one value
   (careful JSON edit; change nothing else in the file).
   Verify: re-read the key. Note: tools reconnect only in a NEW session — say so.
3. Missing pre-commit hook: recreate `D:\KNOWLEDGE\.git\hooks\pre-commit` exactly
   per the spec — sh script, exits 0 when `VAULT_UNLOCK=1`, else scans
   `git diff --cached --name-only --diff-filter=ACDMR` and blocks
   `90-templates/* .obsidian/* _math-system/* .true-recall/* 50-srs/Yanki/* 00-home/*`
   (except `00-home/Home-{Today,Journey,Recent,Nav}.md`), `AI-Math-Note-Protocol.md`,
   `AGENTS.md`. chmod +x it.
   Verify: `ls -la` shows executable; test with a dry `git diff --cached` run.
4. DataviewJS disabled: set `"enableDataviewJs": true` in
   `D:\KNOWLEDGE\.obsidian\plugins\dataview\data.json` (edit the one key only).
   This is a protected path by AGENTS.md — allowed here only because the user
   invoked the doctor for this fix; state it in the summary. Verify by re-reading.
5. Gitignore hygiene: add obvious junk patterns (e.g. `Untitled.md`, `null`) to
   `.gitignore` if missing. Never add ignore rules for protected content lanes.
6. Missing unprotected folders the system expects (e.g. `30-study\Exercises`):
   create the empty folder only — no content.

**ASK-FIRST — require an explicit user "yes" in this conversation before acting:**

- Anything else under protected paths: `90-templates/`, `00-home/` (beyond the
  four Home-* widgets), `.obsidian/` (beyond fix 4), `_math-system/`,
  `.true-recall/`, `50-srs/Yanki/`, `00-home/AI-Math-Note-Protocol.md`.
- Deleting or rewriting ANY note, junk included, once it has real content.
- Any template change.
- Any database operation (`math.db`, FSRS db) — never hand-edit; if corrupt,
  offer `"C:\...\Python314\python.exe" "D:\KNOWLEDGE\.system\pipeline\verify_db.py"`
  (no args) and STOP for user instruction.
- Pending-card approvals/rejects (`card_status`) — needs explicit user approval
  of each card, not a blanket "fix everything".

## Phase 3 — Apply and verify

1. Apply SAFE-FIXes one at a time. After each, re-run that specific check and
   confirm it now PASSes. If a fix does not verify, REVERT it if reversible and
   report FAIL with the error output.
2. Present the ASK-FIRST list. Wait for explicit approval per item — silence or
   "maybe" is not approval. Then apply + verify the same way.
3. If any fix fails or you are unsure → do nothing, report, and recommend
   `vault-health` for a clean re-scan.

## Phase 4 — Summary

End with:

- **Applied + verified:** each fix and its post-check evidence (one line each).
- **Awaiting approval:** ASK-FIRST items not yet approved.
- **Not done (failed/declined):** with reason.
- **Residual risks:** e.g. "MCP re-point takes effect next session".

Honesty rule: never report a fix as done without re-running its check. If you
did not verify it, it is "applied, unverified" — say exactly that.
