# knowledge-vault MCP server

Local stdio MCP server (v1.0, 2026-08-17) giving any AI agent safe operating
access to the KNOWLEDGE math vault. Zero dependencies — Python 3.10+ stdlib.

- **Server:** `server.py` · **Tests:** `test_server.py` (14/14 passing, 2026-08-17)
- **Contract:** the agent-facing rules live in `D:\KNOWLEDGE\AGENTS.md` (ZCode and
  other AGENTS.md-aware clients load it automatically when working in the vault).

## Tools (7)

| Tool | Access | Notes |
|---|---|---|
| `vault_search` | read | substring scan of `.md` notes |
| `read_note` | read | any vault note, incl. protected (reading is fine) |
| `write_note` | write | **refuses protected paths**; audit-logged |
| `note_from_template` | write | ts/tc/tp/tt/tf/tr/tx templates; refuses protected destinations |
| `card_status` | write | approve→`50-srs/Yanki`, reject→`deferred_queue`; requires `user_approved:true` |
| `mastery_read` | read | read-only SQLite summary from `_math-system/registry/math.db` |
| `health_check` | read | vault + git HEAD + protection hook + REST API status |

Protected paths, security model, and the audit log (`80-agent/decisions/mcp-audit.jsonl`)
are defined in `AGENTS.md`.

## Client setup

### ZCode — REGISTERED 2026-08-17
`~/.zcode/cli/config.json` → `mcp.servers.knowledge-vault`

### Claude Code
```bash
claude mcp add knowledge-vault -- python "D:\KNOWLEDGE\.system\mcp-knowledge-vault\server.py"
```

### Open WebUI / LibreChat
Add an MCP server entry with command `python` and the server path above.

## Run the tests

```bash
cd "D:\KNOWLEDGE\.system\mcp-knowledge-vault"
python test_server.py    # spawns the server, drives the full JSON-RPC handshake
```

## Limits (honest)

- Search is substring-only; Omnisearch ranking stays in-app.
- `mastery_read` reads the DB summary; live concept status truth is note frontmatter.
- No render/screenshot tool (that's the CDP discipline in AGENTS.md).
- stdio only — one client process at a time per launch; no network surface.
