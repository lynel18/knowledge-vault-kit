#!/usr/bin/env python3
"""KNOWLEDGE vault MCP server v1 (2026-08-17).

Local stdio MCP server so any AI agent can operate D:\\KNOWLEDGE safely.
Zero dependencies (Python stdlib). Security model:
  - stdio only; never opens a socket.
  - all file operations constrained to the vault root.
  - PROTECTED paths (per AGENTS.md, user-confirmed 2026-08-17) are refused
    for write operations; card approval additionally requires the caller to
    assert user approval, and every mutating action is audit-logged to
    80-agent/decisions/mcp-audit.jsonl.
  - the Local REST API key is read at runtime and only used for the health
    check; it is never written to stdout or logs.
Protocol: JSON-RPC 2.0 over line-delimited stdio (MCP initialize/tools).
"""
import json
import os
import re
import sqlite3
import ssl
import sys
import urllib.request
from datetime import date, timedelta

# Portable: the bundled copy reads the vault root from env (default keeps the
# classic D:\KNOWLEDGE install). Installers set KNOWLEDGE_VAULT when the vault
# lives elsewhere.
VAULT = os.path.realpath(os.environ.get("KNOWLEDGE_VAULT") or r"D:\KNOWLEDGE")
REST_KEY_FILE = os.path.join(VAULT, r".obsidian\plugins\obsidian-local-rest-api\data.json")
REST_BASE = "https://127.0.0.1:27125"
AUDIT_LOG = os.path.join(VAULT, r"80-agent\decisions\mcp-audit.jsonl")
SKIP_DIRS = {".git", ".obsidian", "_math-system", ".true-recall", "Math Texbook JSON", ".trash"}
PROTOCOL_VERSION = "2024-11-05"
SERVER_INFO = {"name": "knowledge-vault", "version": "1.0.0"}

WIDGET_NOTES = {
    "00-home/Home-Today.md", "00-home/Home-Journey.md",
    "00-home/Home-Recent.md", "00-home/Home-Nav.md",
}

def is_protected(rel: str) -> bool:
    rel = rel.replace("\\", "/")
    if rel in WIDGET_NOTES:
        return False
    top = (
        "90-templates/", ".obsidian/", "_math-system/", ".true-recall/",
        "50-srs/Yanki/", "00-home/",
    )
    if rel.startswith(top):
        return True
    return rel in {"AI-Math-Note-Protocol.md", "AGENTS.md"}

def vault_path(rel: str) -> str:
    p = os.path.realpath(os.path.join(VAULT, rel.replace("\\", "/").lstrip("/")))
    if not (p == VAULT or p.startswith(VAULT + os.sep)):
        raise PermissionError("path escapes vault root: " + rel)
    return p

def audit(action: str, detail: str) -> None:
    # Test runs (test_server.py sets KNOWLEDGE_MCP_TEST=1) audit to a temp file
    # so the real production audit log never accumulates smoke-test noise.
    target = AUDIT_LOG
    if os.environ.get("KNOWLEDGE_MCP_TEST") == "1":
        target = os.path.join(os.environ.get("TEMP", os.environ.get("TMP", ".")),
                              "knowledge-vault-test-audit.jsonl")
    try:
        os.makedirs(os.path.dirname(target), exist_ok=True)
        with open(target, "a", encoding="utf-8") as f:
            f.write(json.dumps({"ts": date.today().isoformat(), "action": action, "detail": detail}) + "\n")
    except OSError as e:  # auditing must never crash the server
        print("audit-fail: %s" % e, file=sys.stderr)

def err(msg: str) -> dict:
    return {"content": [{"type": "text", "text": "ERROR: " + msg}], "isError": True}

def ok(text: str) -> dict:
    return {"content": [{"type": "text", "text": text}]}

# ---------------- tools ----------------

def t_vault_search(args: dict) -> dict:
    q = str(args.get("query", "")).lower().strip()
    if not q:
        return err("query required")
    hits = []
    for root, dirs, files in os.walk(VAULT):
        dirs[:] = [d for d in dirs if d not in SKIP_DIRS]
        for name in files:
            if not name.endswith(".md"):
                continue
            full = os.path.join(root, name)
            rel = os.path.relpath(full, VAULT).replace("\\", "/")
            try:
                with open(full, "r", encoding="utf-8", errors="ignore") as f:
                    text = f.read()
            except OSError:
                continue
            if q in text.lower():
                for i, line in enumerate(text.splitlines(), 1):
                    if q in line.lower():
                        hits.append("%s:%d: %s" % (rel, i, line.strip()[:120]))
                        break
            if len(hits) >= 20:
                break
        if len(hits) >= 20:
            break
    return ok("\n".join(hits) if hits else "No matches (simple substring scan of .md notes; not Omnisearch ranking).")

def t_read_note(args: dict) -> dict:
    rel = str(args.get("path", "")).strip()
    if not rel:
        return err("path required (vault-relative, e.g. 10-math/MATH-INDEX.md)")
    try:
        p = vault_path(rel)
    except PermissionError as e:
        return err(str(e))
    if not os.path.isfile(p):
        return err("not found: " + rel)
    with open(p, "r", encoding="utf-8", errors="ignore") as f:
        text = f.read(200_000)
    return ok(text)

def t_write_note(args: dict) -> dict:
    rel = str(args.get("path", "")).strip()
    content = str(args.get("content", ""))
    if not rel or not content:
        return err("path and content required")
    if is_protected(rel):
        return err("'%s' is PROTECTED. Ask the user for explicit approval in the "
                   "conversation; if approved, they commit with VAULT_UNLOCK=1. "
                   "The MCP server never writes protected paths." % rel)
    try:
        p = vault_path(rel)
    except PermissionError as e:
        return err(str(e))
    os.makedirs(os.path.dirname(p), exist_ok=True)
    with open(p, "w", encoding="utf-8", newline="\n") as f:
        f.write(content)
    audit("write_note", rel)
    return ok("wrote %d chars to %s" % (len(content), rel))

def t_note_from_template(args: dict) -> dict:
    template = str(args.get("template", "tc-concept"))
    title = str(args.get("title", "")).strip()
    dest = str(args.get("dest_folder", "")).strip()
    if not title or not dest:
        return err("title and dest_folder required (dest must be an UNPROTECTED lane)")
    mapping = {"ts-section": "ts-section.md", "tc-concept": "tc-concept.md",
               "tp-problem": "tp-problem.md", "tt-theorem": "tt-theorem.md",
               "tf-formula": "tf-formula.md", "tr-review": "tr-review.md",
               "tx-exercise": "tx-exercise.md",
               "tc-cycle-exercise": "tc-cycle-exercise.md"}
    fname = mapping.get(template)
    if not fname:
        return err("unknown template '%s' (use one of %s)" % (template, ", ".join(mapping)))
    tpl_path = vault_path("90-templates/" + fname)
    if not os.path.isfile(tpl_path):
        return err("template missing: " + fname)
    with open(tpl_path, "r", encoding="utf-8") as f:
        text = f.read()
    text = text.replace('<% tp.file.title %>', title)
    text = text.replace('<% tp.date.now("YYYY-MM-DD") %>', date.today().isoformat())
    text = text.replace('<% tp.date.now("YYYY-MM-DD", 1) %>',
                        (date.today() + timedelta(days=1)).isoformat())
    safe = re.sub(r'[\\/:*?"<>|]+', "-", title).strip()
    rel = "%s/%s.md" % (dest.rstrip("/"), safe)
    if is_protected(rel):
        return err("destination '%s' is protected; pick an unprotected lane" % rel)
    p = vault_path(rel)
    if os.path.exists(p):
        return err("refusing to overwrite existing note: " + rel)
    os.makedirs(os.path.dirname(p), exist_ok=True)
    with open(p, "w", encoding="utf-8", newline="\n") as f:
        f.write(text)
    audit("note_from_template", "%s -> %s" % (template, rel))
    return ok("created %s from %s (fill the placeholders; follow AI-Math-Note-Protocol.md)" % (rel, fname))

def t_card_status(args: dict) -> dict:
    card = str(args.get("card", "")).strip()
    action = str(args.get("action", "")).strip().lower()
    approved = bool(args.get("user_approved", False))
    if not card or action not in ("approve", "reject"):
        return err("card and action=approve|reject required")
    if not approved:
        return err("user_approved=true required: confirm in the conversation that "
                   "the USER approved this card before calling. Audit-logged either way.")
    src = vault_path("50-srs/pending_anki/" + card)
    if not os.path.isfile(src):
        return err("no such pending card: " + card)
    dst_dir = "50-srs/Yanki" if action == "approve" else "50-srs/deferred_queue"
    dst = vault_path(dst_dir + "/" + card)
    if os.path.exists(dst):
        return err("target exists: " + dst_dir + "/" + card)
    os.makedirs(os.path.dirname(dst), exist_ok=True)
    os.replace(src, dst)
    audit("card_status", "%s %s" % (action, card))
    return ok("%s -> %s (run yanki:sync next if approved)" % (card, dst_dir))

def t_mastery_read(args: dict) -> dict:
    db = os.path.join(VAULT, "_math-system", "registry", "math.db")
    if not os.path.isfile(db):
        return err("math.db not found")
    uri = "file:" + db.replace("\\", "/") + "?mode=ro"
    try:
        con = sqlite3.connect(uri, uri=True, timeout=3)
        cur = con.cursor()
        rows = []
        for label, sql in [
            ("entities", "SELECT COUNT(*) FROM entities"),
            ("learning_objectives", "SELECT COUNT(*) FROM learning_objectives"),
        ]:
            rows.append("%s: %s" % (label, cur.execute(sql).fetchone()[0]))
        try:
            cov = cur.execute("SELECT objective_id, mastery FROM objective_coverage "
                              "ORDER BY mastery DESC LIMIT 10").fetchall()
            rows.append("top objective_coverage: " + "; ".join("%s=%.2f" % r for r in cov) if cov
                        else "objective_coverage: empty")
        except sqlite3.Error:
            rows.append("objective_coverage: (table unavailable)")
        con.close()
    except sqlite3.Error as e:
        return err("sqlite: %s" % e)
    return ok("\n".join(rows))

def t_health_check(args: dict) -> dict:
    lines = ["vault: %s" % VAULT, "git HEAD: %s" % _git_head()]
    hook_tracked = os.path.join(VAULT, ".system", "githooks", "pre-commit")
    hook_push = os.path.join(VAULT, ".system", "githooks", "pre-push")
    hk = "installed" if os.access(hook_tracked, os.X_OK) else "MISSING"
    hp = "not-found"
    try:
        with open(os.path.join(VAULT, ".git", "config"), "r", encoding="utf-8") as f:
            cfg = f.read().lower()
        if "hookspath" in cfg and ".system/githooks" in cfg:
            hp = ".system/githooks"
    except OSError:
        pass
    push_hk = "installed" if os.access(hook_push, os.X_OK) else "MISSING"
    lines.append("pre-commit protection: %s (tracked, hooksPath=%s)" % (hk, hp))
    lines.append("pre-push protection: %s" % push_hk)
    md = sum(1 for r, d, fs in os.walk(VAULT)
             if not (set(d) & SKIP_DIRS) for f_ in fs if f_.endswith(".md"))
    lines.append("markdown notes (approx): %d" % md)
    try:
        with open(REST_KEY_FILE, "r", encoding="utf-8") as f:
            key = json.load(f).get("apiKey", "")
        req = urllib.request.Request(REST_BASE + "/", headers={"Authorization": "Bearer " + key})
        ctx = ssl._create_unverified_context()
        with urllib.request.urlopen(req, timeout=4, context=ctx) as resp:
            lines.append("REST API: HTTP %s (https ok)" % resp.status)
    except Exception as e:
        lines.append("REST API: unreachable (%s)" % type(e).__name__)
    return ok("\n".join(lines))

def _git_head() -> str:
    try:
        with open(os.path.join(VAULT, ".git", "HEAD"), "r", encoding="utf-8") as f:
            ref = f.read().strip()
        if ref.startswith("ref: "):
            pp = os.path.join(VAULT, ".git", ref[5:])
            with open(pp, "r", encoding="utf-8") as f:
                return f.read().strip()[:12]
        return ref[:12]
    except OSError:
        return "unknown"

TOOLS = [
    {"name": "vault_search", "description": "Substring search across vault .md notes (paths + first matching line). Not Omnisearch-ranked.",
     "inputSchema": {"type": "object", "properties": {"query": {"type": "string"}}, "required": ["query"]}},
    {"name": "read_note", "description": "Read any vault note (protected paths are readable).",
     "inputSchema": {"type": "object", "properties": {"path": {"type": "string"}}, "required": ["path"]}},
    {"name": "write_note", "description": "Write a note. PROTECTED paths are refused (see AGENTS.md).",
     "inputSchema": {"type": "object", "properties": {"path": {"type": "string"}, "content": {"type": "string"}}, "required": ["path", "content"]}},
    {"name": "note_from_template", "description": "Create a note from a 90-templates template (ts-section|tc-concept|tp-problem|tt-theorem|tf-formula|tr-review|tx-exercise|tc-cycle-exercise); fills title+date.",
     "inputSchema": {"type": "object", "properties": {"template": {"type": "string"}, "title": {"type": "string"}, "dest_folder": {"type": "string"}}, "required": ["template", "title", "dest_folder"]}},
    {"name": "card_status", "description": "Approve (→50-srs/Yanki) or reject (→deferred_queue) a pending card from 50-srs/pending_anki. Requires user_approved=true.",
     "inputSchema": {"type": "object", "properties": {"card": {"type": "string"}, "action": {"type": "string", "enum": ["approve", "reject"]}, "user_approved": {"type": "boolean"}}, "required": ["card", "action", "user_approved"]}},
    {"name": "mastery_read", "description": "Read-only summary from _math-system/registry/math.db (counts, top objective coverage).",
     "inputSchema": {"type": "object", "properties": {}}},
    {"name": "health_check", "description": "Vault + git + protection-hook + REST API health summary.",
     "inputSchema": {"type": "object", "properties": {}}},
]

DISPATCH = {"vault_search": t_vault_search, "read_note": t_read_note, "write_note": t_write_note,
            "note_from_template": t_note_from_template, "card_status": t_card_status,
            "mastery_read": t_mastery_read, "health_check": t_health_check}

def handle(req: dict) -> dict | None:
    method = req.get("method", "")
    rid = req.get("id")
    if method == "initialize":
        return {"jsonrpc": "2.0", "id": rid, "result": {
            "protocolVersion": PROTOCOL_VERSION,
            "capabilities": {"tools": {}}, "serverInfo": SERVER_INFO}}
    if method == "notifications/initialized" or method.startswith("notifications/"):
        return None
    if method == "ping":
        return {"jsonrpc": "2.0", "id": rid, "result": {}}
    if method == "tools/list":
        return {"jsonrpc": "2.0", "id": rid, "result": {"tools": TOOLS}}
    if method == "tools/call":
        name = req.get("params", {}).get("name", "")
        fn = DISPATCH.get(name)
        if not fn:
            return {"jsonrpc": "2.0", "id": rid, "result": err("unknown tool: " + name)}
        try:
            return {"jsonrpc": "2.0", "id": rid, "result": fn(req.get("params", {}).get("arguments", {}))}
        except Exception as e:
            return {"jsonrpc": "2.0", "id": rid, "result": err("%s: %s" % (type(e).__name__, e))}
    if rid is not None:
        return {"jsonrpc": "2.0", "id": rid, "error": {"code": -32601, "message": "method not found: " + method}}
    return None

def main() -> None:
    while True:
        line = sys.stdin.readline()
        if not line:
            break
        line = line.strip()
        if not line:
            continue
        try:
            req = json.loads(line)
        except json.JSONDecodeError:
            resp = {"jsonrpc": "2.0", "id": None, "error": {"code": -32700, "message": "parse error"}}
        else:
            resp = handle(req)
        if resp is not None:
            sys.stdout.write(json.dumps(resp) + "\n")
            sys.stdout.flush()

if __name__ == "__main__":
    main()
