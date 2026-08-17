# AGENTS.md — Operating Contract for AI Agents in D:\KNOWLEDGE

**You are inside a human's lifelong math-learning vault.** Read this before touching anything.
Full system context: `00-home/SYSTEM-MAP.md` (what lives where) and
`C:\Users\User\Downloads\Overview\KNOWLEDGE-Vault-Snapshot.md` (verified state).

## The one rule that precedes all others

This vault is **one root, two planes**. The **human plane** is everything
Obsidian shows: notes a learner reads. The **control plane** is `.system\`
(a dot-folder Obsidian never indexes) — the ONLY place code files
(`.py/.js/.exe/.sh/.bat`) are allowed, besides plugin binaries under
`.obsidian/plugins/`. Never create code files anywhere else.

## Protected paths — ASK THE USER FIRST (confirmed 2026-08-17)

Modifying, moving, or deleting anything below requires explicit user approval
in the current conversation. A git pre-commit hook also blocks commits touching
these paths unless the user unlocked the session (`VAULT_UNLOCK=1`).

```
90-templates/                       (the note grammar)
00-home/                            (home surface, manuals, protocol, widgets)
  └─ except: Home-Today.md, Home-Journey.md, Home-Recent.md, Home-Nav.md
     (these four are AI-maintained dashboard widgets — editable)
.obsidian/                          (theme, snippets, plugin configs)
.zcode/                             (skills that steer future AI sessions)
_math-system/                       (pipeline DB — never hand-edit)
.true-recall/                       (FSRS database — never hand-edit)
50-srs/Yanki/                       (sync-owned: yanki overwrites from these)
00-home/AI-Math-Note-Protocol.md    (the writing law)
```

`.system\` is AI-writable (it is the working control plane). Everything else
(Sections, Concepts, Sessions, Exercises) is writable — that is where learning
content is supposed to grow.

## How to write here (the grammar)

1. `00-home/AI-Math-Note-Protocol.md` is law: math rendering (LMath first,
   Desmos for bounds), callout vocabulary, frontmatter requirements.
2. `90-templates/ts-section.md` is the **structural default** for section notes;
   `tc-concept.md` mirrors one objective block. Follow their block order — the
   order is a reading-comfort design, not a suggestion.
3. Frontmatter is mandatory: `kind`, `status`, `tags`, `cssclasses`, `section`,
   `prerequisites`. Concept `status` lifecycle starts at `UNSEEN`.
4. Cards go to `50-srs/Yanki/` with `recall_type:` (definition | why |
   recognition | procedure | error) — cloze for procedures, basic for pairs.
   Sync is one-way (`yanki:sync` inside Obsidian); never edit yanki cards
   inside Anki.
5. Exercises go to `30-study/Exercises/` from `tx-exercise.md` (or the
   `exercise-log` skill). Re-attempt ladder: 1→3→7→14→30→60 days; pass climbs,
   fail resets to +1 day, pass at step 5 → `status: mastered`. Fine print in
   `30-study/Exercises/README.md`.
6. Honesty rules: never fabricate verification, never fake progress states,
   mastery numbers come only from real attempts.

## Automation surface

- **MCP server (preferred)**: `.system\mcp-knowledge-vault\server.py` — stdio,
  local-only, 7 tools; `note_from_template` maps ts/tc/tp/tt/tf/tr/tx. Registered in ZCode as `knowledge-vault`; see its README for
  other clients (Claude Code, OpenWebUI).
- **Skills** (ZCode workspace scope): `.zcode/skills/` — `vault-health`
  (diagnostics), `vault-doctor` (safe fixes + ask-first), `math-section`
  (ingest → candidates → approval → cards → section note), `exercise-log`
  (training ladder ops). Other AI clients: these are plain markdown — read and
  follow them.
- **Pipeline**: `.system\pipeline\` (21 stages, self-contained; run via
  `C:\Users\User\AppData\Local\Programs\Python\Python314\python.exe`;
  tests: `python -m pytest -q` there).
- **Training Ladder scheduler**: `.system\scheduler\exercise_scheduler.py` —
  daily 07:00 Task Scheduler job; writes the digest to
  `30-study\Reviews\`, heartbeat to its `logs\`, optional webhook/GitHub
  watchdog (see its README). Observes only — never moves ladders.
- **Local REST API**: HTTPS `https://127.0.0.1:27125`, key in the gitignored
  plugin data.json — never print, commit, or log it.
- **CDP** (visual verification only): relaunch Obsidian with
  `--remote-debugging-port=9222`, verify, then **relaunch clean**. Always.
- AnkiConnect `127.0.0.1:8765`; FSRS-6 everywhere; desired retention 0.90.

## When unsure

Ask the user. A blocked question costs one turn; a wrong edit inside a
protected path costs trust in the whole system.
