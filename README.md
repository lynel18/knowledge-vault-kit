# knowledge-vault-kit

Bundle installer for the KNOWLEDGE math-learning Obsidian vault. One command wires any local AI tool (ZCode, Claude Code, DSH Harness, OpenCode, OpenWebUI) to the vault.

- MCP server — `kit/mcp/server.py` (zero-dependency Python stdlib, 7 tools, path-jailed, protected-path enforced, self-auditing)
- Agent skills — `kit/skills/*/SKILL.md` (vault-health, vault-doctor, math-section, exercise-log, vault-guide)
- Operating contract — `kit/AGENTS.md`

Run: `npx -y knowledge-vault-kit --vault "D:\KNOWLEDGE"` · or `node bin/index.js --help`
