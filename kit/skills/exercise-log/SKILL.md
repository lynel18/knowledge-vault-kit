---
name: exercise-log
description: Track math practice exercises in the KNOWLEDGE vault with the ladder spaced-repetition system. Use when the user asks to log an exercise, record a pass or fail, mark an exercise mastered, list exercises due today, or check the exercise ladder — operates on notes in 30-study/Exercises with ladder_step 0-5 and intervals 1/3/7/14/30/60 days.
---

# exercise-log — exercise ladder operations

Governing contract: `D:\KNOWLEDGE\AGENTS.md`. Notes live in
`D:\KNOWLEDGE\30-study\Exercises\` (unprotected lane — writable via MCP `write_note`).

Ladder intervals (days, by step): `[1, 3, 7, 14, 30, 60]`.
Frontmatter fields: `kind: exercise`, `book`, `section`, `exercise`, `status:
active|mastered`, `ladder_step: 0-5`, `next_due: YYYY-MM-DD`, `last_result: pass|fail`.

**Review semantics (state before every pass/fail):** a re-attempt means solving
the problem fresh, from scratch, WITHOUT looking at the previous solution or the
worked example first. Looking first invalidates the attempt — log nothing.

Naming: `ex-<ch>-<ss>-<num>-<slug>.md`.

## Operations

### `log` — create an exercise note

1. Collect from the user: book (default `prealgebra_martingay_8e`), chapter,
   section, exercise number, short slug, and the problem statement.
2. Preferred: MCP `note_from_template` with `template: "tx-exercise"`,
   `title: "ex-<ch>-<ss>-<num>-<slug>"`, `dest_folder: "30-study/Exercises"` —
   it fills the title, today's date, and `next_due` = tomorrow automatically.
   Then `write_note` (or an edit) to set `book`, `section`, `exercise`, and the
   problem statement.
   Fallback: `read_note` the template `90-templates/tx-exercise.md`, fill
   placeholders manually, then `write_note`.
3. Initial state: `status: active`, `ladder_step: 0`, `next_due:` today+1 day.
4. Verify: re-read the note; confirm frontmatter parses.

### `pass <note>` — record a passed attempt

1. Confirm a fresh solve. If the user peeked → log as fail.
2. Update `last_result: pass`. New step = `ladder_step + 1`.
   - New step > 5 (was 5): `status: mastered`, clear `next_due`, keep `ladder_step: 5`.
   - Else: `next_due:` today + interval[new step].
3. Append `| YYYY-MM-DD | pass | <note> |` to `## Attempt log`.
4. Verify by re-reading.

### `fail <note>` — record a failed attempt

1. Update `last_result: fail`, `ladder_step: 0`, `next_due:` tomorrow.
2. Append `| YYYY-MM-DD | fail | <what went wrong> |` — one concrete cause.
3. `status` stays `active`. Verify by re-reading.

### `due` — list exercises due today

1. Due = `status: active` AND `next_due <= today`. Overdue marked "overdue (N days)".
2. Report a table: note link | book § | ladder_step | next_due | last_result.
3. Also report: active count, mastered count, malformed notes — never skip silently.

### `mastered` (explicit)

Only on explicit user confirmation (AGENTS.md honesty rule). Set `status: mastered`;
do not delete the note.

## Rules

1. Only `pass`/`fail` from a REAL attempt the user just made.
2. Never edit `_math-system/` or `.true-recall/` from this skill.
3. Dates are ISO `YYYY-MM-DD`.
4. After any update, re-read the note and quote changed frontmatter — verification
   before claims.
