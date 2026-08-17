#!/usr/bin/env python3
"""End-to-end test driver for the KNOWLEDGE MCP server (spawns server.py)."""
import json, os, subprocess, sys
from datetime import date, timedelta

HERE = os.path.dirname(os.path.abspath(__file__))
SERVER = os.path.join(HERE, "server.py")
VAULT = r"D:\KNOWLEDGE"

test_env = dict(os.environ, KNOWLEDGE_MCP_TEST="1")
p = subprocess.Popen([sys.executable, SERVER], stdin=subprocess.PIPE,
                     stdout=subprocess.PIPE, stderr=subprocess.DEVNULL,
                     text=True, encoding="utf-8", env=test_env)

def send(obj):
    p.stdin.write(json.dumps(obj) + "\n"); p.stdin.flush()
    line = p.stdout.readline()
    return json.loads(line) if line.strip() else None

def notify(obj):
    p.stdin.write(json.dumps(obj) + "\n"); p.stdin.flush()

def call(name, args):
    return send({"jsonrpc": "2.0", "id": abs(hash(name + json.dumps(args, sort_keys=True))) % 10000,
                 "method": "tools/call", "params": {"name": name, "arguments": args}})

results = []
def check(label, cond, detail=""):
    results.append((label, bool(cond)))
    print(("PASS" if cond else "FAIL"), "-", label, ("| " + str(detail)[:100] if detail and not cond else ""))

r = send({"jsonrpc": "2.0", "id": 1, "method": "initialize",
          "params": {"protocolVersion": "2024-11-05", "capabilities": {}, "clientInfo": {"name": "test"}}})
check("initialize returns serverInfo", r and r["result"]["serverInfo"]["name"] == "knowledge-vault")
notify({"jsonrpc": "2.0", "method": "notifications/initialized"})

r = send({"jsonrpc": "2.0", "id": 2, "method": "tools/list"})
names = [t["name"] for t in r["result"]["tools"]]
check("tools/list exposes 7 tools", len(names) == 7, names)

r = call("health_check", {})
txt = r["result"]["content"][0]["text"]
check("health_check reports hook installed", "pre-commit protection: installed" in txt, txt)
check("health_check reaches REST", "REST API: HTTP" in txt, txt)

r = call("vault_search", {"query": "complex fraction"})
txt = r["result"]["content"][0]["text"]
check("search finds complex-fraction content", ".md:" in txt and len(txt.splitlines()) >= 1, txt[:200])

r = call("read_note", {"path": "10-math/MATH-INDEX.md"})
check("read_note returns content", "mathematics" in r["result"]["content"][0]["text"].lower())

r = call("write_note", {"path": "00-home/User-Manual.md", "content": "x"})
check("write_note refuses protected path", r["result"].get("isError") is True)

r = call("write_note", {"path": "30-study/mcp-smoke-test.md", "content": "smoke"})
check("write_note writes unprotected lane", "wrote" in r["result"]["content"][0]["text"])
os.remove(os.path.join(VAULT, "30-study", "mcp-smoke-test.md"))

r = call("read_note", {"path": "../../outside-vault/server.py"})
check("path escape refused", r["result"].get("isError") is True)

r = call("note_from_template", {"template": "tc-concept", "title": "MCP Smoke Test Concept",
                                "dest_folder": "30-study"})
check("note_from_template creates note", "created" in r["result"]["content"][0]["text"],
      r["result"]["content"][0]["text"])
made = os.path.join(VAULT, "30-study", "MCP Smoke Test Concept.md")
check("templated note has today's date", os.path.isfile(made) and date.today().isoformat() in open(made, encoding="utf-8").read())
if os.path.exists(made): os.remove(made)

r = call("note_from_template", {"template": "tx-exercise", "title": "MCP Smoke Exercise",
                                "dest_folder": "30-study"})
made_x = os.path.join(VAULT, "30-study", "MCP Smoke Exercise.md")
okx = "created" in r["result"]["content"][0]["text"]
if okx and os.path.exists(made_x):
    body = open(made_x, encoding="utf-8").read()
    from datetime import date as _d, timedelta as _td
    okx = (_d.today() + _td(days=1)).isoformat() in body and "tp.date.now" not in body
    os.remove(made_x)
check("tx-exercise template fills tomorrow next_due", okx, True)

r = call("card_status", {"card": "nonexistent.md", "action": "approve", "user_approved": False})
check("card_status requires user_approved", r["result"].get("isError") is True)

r = call("mastery_read", {})
txt = r["result"]["content"][0]["text"]
check("mastery_read returns counts", "entities:" in txt, txt)

p.stdin.close(); p.terminate()
fails = [l for l, c in results if not c]
print("\n%d/%d passed" % (len(results) - len(fails), len(results)))
sys.exit(1 if fails else 0)
