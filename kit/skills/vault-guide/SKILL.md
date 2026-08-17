---
name: vault-guide
description: Guide the learner through every feature of the KNOWLEDGE math vault — home board, study flow, Training Ladder exercises, cards/Anki, scheduler and notifications, AI surfaces. Use when the user asks for help, a tour, "what can this vault do", "how do I study/use X", or is confused about where something lives.
---

# Vault Guide — walking the learner through the system

You are guiding the **learner** (not another AI). Be warm, concrete, and short.
Never dump this whole file at them — answer their question, then offer the next
step. Numbers and paths below are real; verify live state before stating it.

## The one-minute map

- **One vault, two planes.** Everything you see in Obsidian is the *human plane*.
  The machinery (pipeline, MCP server, scheduler) hides in `.system\`.
  Map: `00-home/SYSTEM-MAP.md`.
- **Your day starts on the Home board**: Today's Journey, Today's Training,
  Destinations, Recently Studied, Learning Journey bars, calendar, graph +
  galaxy observatory, scenery strip.

## Daily study flow (the intended loop)

1. Open **Home** → read *Today's Journey* → click the current section link.
2. Study the section note (objectives → representations → worked examples →
   retrieval quintet → mastery check — the order is designed).
3. Solve exercises on paper; log each one.
4. Re-attempt due exercises (*Today's Training* panel or the daily digest).
5. Review cards: true-recall inside Obsidian, or `yanki:sync` then Anki.
6. Write the day's session note: `30-study/Sessions/YYYY-MM-DD.md`.

## Feature inventory

| Feature | Where | How the learner uses it |
|---|---|---|
| Home board widgets | `00-home/Home-*.md` | open Home; live frontmatter |
| Training Ladder | `30-study/Exercises/` | log / pass / fail via AI or by hand |
| Daily digest | `30-study/Reviews/training-digest-*.md` | written every morning 07:00 |
| Morning notification | Windows toast (+ webhook) | automatic; GitHub watchdog |
| Cards | `50-srs/Yanki/*.md` | AI generates → user approves → `yanki:sync` |
| Review room | true-recall plugin | themed review |
| Sections & concepts | `10-math/` | generated via the math-section skill |
| Research library | `80-agent/Research/` | evidence behind design decisions |
| Pipeline & MCP | `.system/` | any AI plugs in via MCP + AGENTS.md |

## "I want to…" routing

- **Add/study a new section** → `math-section` skill.
- **Log an exercise / record pass/fail** → `exercise-log` skill.
- **Check everything works** → `vault-health` skill.
- **Fix something** → `vault-doctor` skill.
- **See what's due without Obsidian** → digest, toast, or GitHub watchdog message.
- **Understand a design choice** → `80-agent/Research/`.
- **Know what the AI may/may not touch** → `AGENTS.md`.

## Facts worth knowing (don't guess — verify)

- Ladder intervals: **1 → 3 → 7 → 14 → 30 → 60 days**; fail resets to +1 day.
- FSRS-6 everywhere, desired retention 0.90.
- Scheduler job: "KNOWLEDGE Training Ladder Scheduler" (Task Scheduler, 07:00).
