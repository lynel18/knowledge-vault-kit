---
name: math-section
description: End-to-end workflow for adding a new textbook section to the KNOWLEDGE math vault — ingest textbook JSON, generate card candidates, human approval gate, compile cards to 50-srs/Yanki, build the section note from the ts-section template, and sync to Anki. Use when the user asks to add/process/generate a math section, set up a new chapter section, create section cards, or push a section through the pipeline.
---

# math-section — add a textbook section end to end

Governing contract: `D:\KNOWLEDGE\AGENTS.md`. MCP tools (knowledge-vault) are
available in-session. Python: `C:\Users\User\AppData\Local\Programs\Python\Python314\python.exe`
(shortened below as `PY`).

Inputs to confirm with the user first: chapter N, section M (book section N.M,
e.g. 4.2 → `--chapter 4 --section 2`), and the section title.

## Steps

1. **Ingest / verify source data.**
   1. Check DB health: `PY "D:\KNOWLEDGE\.system\pipeline\verify_db.py"` (no args).
   2. Ingest if needed (defaults already point at the right JSON and DB):
      `PY "D:\KNOWLEDGE\.system\pipeline\ingest_marker.py"`
      Good: prints `Ingested <n> blocks … for prealgebra_martingay_8e`.
   3. `--fresh` deletes this book's fragments first — only with explicit user
      approval. If `math_textbook.json` moved, pass
      `--json "D:\KNOWLEDGE\Math Texbook JSON\…"`.
   4. If ingest fails → note the exact error, go to step 8 (fallback). Do not
      hand-edit `D:\KNOWLEDGE\_math-system\registry\math.db` (never hand-edit).

2. **Generate candidates for the section.**
   `PY "D:\KNOWLEDGE\.system\pipeline\generate_candidates.py" --chapter N --section M`
   (optional `--minutes 30` daily workload target).
   Good: prints JSON including `staged_files` count; ACTIVE candidates are staged
   as `card_*.json` in `D:\KNOWLEDGE\50-srs\pending_anki\`. DEFERRED candidates
   stay in the DB queue (retained, not discarded).
   If 0 candidates → the section may not be ingested (re-check step 1) or has no
   objectives; report honestly and go to step 8.

3. **Approval gate — human decides.**
   1. List `D:\KNOWLEDGE\50-srs\pending_anki\*.json` for this section; read each
      JSON (fields: `front`, `back` or `cloze_text`, `queue_class` A/B/C, `rationale`).
   2. Show the user a preview table: card front, queue class, rationale.
   3. For each card the user explicitly approves, call MCP `card_status`
      `{card: "<filename>", action: "approve", user_approved: true}`.
      `user_approved: true` ONLY after the user said yes to that card in this
      conversation. Rejections: `action: "reject"` → moves to `50-srs/deferred_queue`.
   4. If the user has not reviewed yet → STOP. Never self-approve.

4. **Compile approved cards into 50-srs/Yanki.**
   `card_status` approve moves the staged file into `D:\KNOWLEDGE\50-srs\Yanki\`.
   The Yanki plugin syncs markdown, so also author one card note per approved
   candidate in `50-srs/Yanki\`:
   - Frontmatter `recall_type:` one of `definition | why | recognition | procedure | error`.
   - Cloze (`{{c1::…}}` deletions) for procedures — the steps sequence;
     basic front/back pair otherwise. Body: question, `---`, answer.
   - `50-srs/Yanki/` is protected; `write_note` refuses it by design. Writing the
     .md directly is permitted ONLY for cards the user approved in step 3.
   - Git note: the pre-commit hook blocks committing `50-srs/Yanki/*` without
     `VAULT_UNLOCK=1` — normal; ask the user, never bypass silently.

5. **Build the section note.**
   1. Look at `D:\KNOWLEDGE\10-math\Sections\` naming: `sec-<ch>-<ss>-<slug>.md`.
   2. MCP `note_from_template` `{template: "ts-section", title: "sec-<ch>-<ss>-<slug>",
      dest_folder: "10-math/Sections"}` → creates the note with title + date filled.
   3. Fill frontmatter via `write_note` (lane is unprotected): `book:
      prealgebra_martingay_8e`, `chapter: N`, `section: N.M`, plus `status`,
      `objectives`, `prerequisites` per the template. Fix the H1 to the human
      title. `--home` rebuilds `70-dashboards/MATH-OS.md`.
   5. Content rules: `00-home/AI-Math-Note-Protocol.md` is law (LMath first,
      callout vocabulary); follow ts-section block order exactly.

6. **Sync to Anki.**
   Tell the user to run the Yanki sync command inside Obsidian (`yanki:sync`).
   One-way vault → Anki. NEVER edit cards inside Anki; correct the vault note and
   re-sync. AnkiConnect endpoint 127.0.0.1:8765 is for the pipeline only.

7. **Report honestly.** List: commands run + key output lines, cards
   approved/rejected (counts + filenames), note path created, what was NOT done.
   Never claim verification you did not see.

8. **Fallback if a pipeline stage fails.**
   - Section note: step 5 works without the pipeline — MCP `note_from_template`
     + `write_note` still allowed; author objectives from the textbook directly.
   - Cards: author candidate JSON (`front`/`back`, `rationale`) into
     `50-srs\pending_anki\` via `write_note` (lane is unprotected), then run
     step 3-4 as normal.
   - Say explicitly: "pipeline stage X failed: <error>; manual path used instead".
