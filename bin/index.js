#!/usr/bin/env node
/*
 * knowledge-vault-kit — one-shot installer for the KNOWLEDGE math-learning
 * vault, usable by any local AI tool with an MCP client.
 */
'use strict';

const fs = require('fs');
const os = require('os');
const path = require('path');
const { spawnSync } = require('child_process');

const KIT_ROOT = path.resolve(__dirname, '..');
const PAYLOAD = path.join(KIT_ROOT, 'kit');

function log(msg, kind = 'info') {
  const p = kind === 'ok' ? '✅' : kind === 'warn' ? '⚠️ ' : kind === 'err' ? '❌' : '·';
  console.log(`${p} ${msg}`);
}

function findPython() {
  const pins = [
    path.join(process.env.LOCALAPPDATA || '', 'Programs', 'Python', 'Python314', 'python.exe'),
    path.join(process.env.LOCALAPPDATA || '', 'Programs', 'Python', 'Python312', 'python.exe'),
  ];
  for (const p of pins) {
    if (p && fs.existsSync(p)) return p;
  }
  const probe = process.platform === 'win32' ? 'python' : 'python3';
  const r = spawnSync(probe, ['-c', 'import sys; print(sys.executable)'], { encoding: 'utf8' });
  if (r.status === 0) return r.stdout.trim();
  return probe;
}

function backupJson(file) {
  if (!fs.existsSync(file)) return null;
  const bak = file + '.bak';
  fs.copyFileSync(file, bak);
  return bak;
}

function readJson(file) {
  if (!fs.existsSync(file)) return null;
  try {
    return JSON.parse(fs.readFileSync(file, 'utf8'));
  } catch {
    return null;
  }
}

function writeJson(file, obj) {
  fs.mkdirSync(path.dirname(file), { recursive: true });
  fs.writeFileSync(file, JSON.stringify(obj, null, 2) + '\n', 'utf8');
}

function deepMerge(...srcs) {
  const out = {};
  for (const s of srcs) {
    if (!s) continue;
    for (const [k, v] of Object.entries(s)) {
      out[k] = v && typeof v === 'object' && !Array.isArray(v)
        ? deepMerge(out[k] || {}, v)
        : v;
    }
  }
  return out;
}

function resolveVaultRoot(argv) {
  const candidates = [
    argv['--vault'],
    process.env.KNOWLEDGE_VAULT,
    'D:\\KNOWLEDGE',
  ].filter(Boolean);
  for (const c of candidates) {
    const abs = path.resolve(c);
    if (fs.existsSync(path.join(abs, 'AGENTS.md')) && fs.existsSync(path.join(abs, '.system'))) {
      return abs;
    }
  }
  throw new Error(
    `Cannot find the KNOWLEDGE vault. Set --vault <path> or KNOWLEDGE_VAULT. ` +
    `Tried: ${candidates.join(', ')}`
  );
}

function installMcpServer(vaultRoot) {
  const dst = path.join(vaultRoot, '.system', 'mcp-knowledge-vault');
  fs.mkdirSync(dst, { recursive: true });
  let installed = 0;
  for (const f of ['server.py', 'test_server.py', 'README.md']) {
    const from = path.join(PAYLOAD, 'mcp', f);
    const to = path.join(dst, f);
    const src = fs.readFileSync(from, 'utf8');
    // Idempotency: only touch a file whose content differs from the kit copy.
    const same = fs.existsSync(to) && fs.readFileSync(to, 'utf8') === src;
    if (!same) {
      if (fs.existsSync(to)) fs.copyFileSync(to, to + '.bak');
      fs.writeFileSync(to, src, 'utf8');
      installed++;
    }
  }
  log(`MCP server ready at ${path.join(dst, 'server.py')}${installed ? ` (${installed} file(s) installed)` : ' (already present)'}`);
  return dst;
}

function pythonArgs(python, serverPath) {
  return [serverPath];
}

function registerZCode(python, serverPath) {
  const cfg = path.join(os.homedir(), '.zcode', 'cli', 'config.json');
  const json = readJson(cfg) || {};
  const cur = json.mcp?.servers?.['knowledge-vault'];
  if (cur && cur.command === python && (cur.args || []).includes(serverPath)) {
    log('ZCode: knowledge-vault already registered (unchanged)');
    return;
  }
  backupJson(cfg);
  const next = deepMerge(json, {
    mcp: { servers: { 'knowledge-vault': { command: python, args: pythonArgs(python, serverPath) } } },
  });
  writeJson(cfg, next);
  log(`ZCode: registered in ${cfg}`, 'ok');
}

function registerClaude(python, serverPath) {
  const r = spawnSync('claude', ['mcp', 'add', 'knowledge-vault', '--', python, ...pythonArgs(python, serverPath)], { encoding: 'utf8' });
  if (r.status === 0) log('Claude Code: registered (claude mcp add)', 'ok');
  else log(`Claude Code: could not run 'claude mcp add' — add manually (${r.stderr?.trim() || r.error?.message})`, 'warn');
}

function registerOpenCode(python, serverPath) {
  const cfg = path.join(os.homedir(), '.config', 'opencode', 'opencode.json');
  const json = readJson(cfg) || { $schema: 'https://opencode.ai/config.json' };
  const cur = json.mcp?.['knowledge-vault'];
  if (cur && cur.type === 'stdio' && (cur.command === python)) {
    log('OpenCode: knowledge-vault already registered (unchanged)');
    return;
  }
  backupJson(cfg);
  const next = deepMerge(json, {
    mcp: {
      'knowledge-vault': {
        type: 'stdio',
        command: python,
        args: pythonArgs(python, serverPath),
      },
    },
  });
  writeJson(cfg, next);
  log(`OpenCode: registered in ${cfg}`, 'ok');
}

function registerGeneric(vaultRoot, python, serverPath) {
  const rel = path.relative(vaultRoot, serverPath).replace(/\\/g, '/');
  log('Generic mappings (for DSH Harness, OpenWebUI, LibreChat, ...):', 'ok');
  console.log('');
  console.log('  # DSH Harness — add this row to profiles/<name>/cordis.patch.yml:');
  console.log(`  - insert:`);
  console.log(`      - id: mcp-knowledge-vault`);
  console.log(`        name: '@deepseek-ai/dsh-mcp-client'`);
  console.log(`        config:`);
  console.log(`          serverName: knowledge-vault`);
  console.log(`          transport: stdio`);
  console.log(`          command: ${JSON.stringify(python)}`);
  console.log(`          args: ${JSON.stringify([serverPath])}`);
  console.log('');
  console.log('  # OpenWebUI / LibreChat — MCP server entry:');
  console.log(`  command: ${JSON.stringify(python)}`);
  console.log(`  args:    ${JSON.stringify([serverPath])}`);
  console.log('');
}

function installSkills(vaultRoot, argv) {
  const src = path.join(PAYLOAD, 'skills');
  const names = fs.readdirSync(src).filter(n => fs.statSync(path.join(src, n)).isDirectory());
  const targets = [];
  if (argv['--no-zcode-skills'] !== true) {
    targets.push(path.join(vaultRoot, '.zcode', 'skills'));
  }
  if (argv['--dsh-skills']) {
    targets.push(path.join(process.env.DSH_HOME || path.join(os.homedir(), '.dsh'), 'skills'));
  }
  if (targets.length === 0) {
    log('Skills: no target (use --dsh-skills to mirror into $DSH_HOME/skills)');
    return;
  }
  for (const t of targets) {
    let n = 0;
    for (const name of names) {
      const from = path.join(src, name, 'SKILL.md');
      if (!fs.existsSync(from)) continue;
      const to = path.join(t, name, 'SKILL.md');
      fs.mkdirSync(path.dirname(to), { recursive: true });
      const cur = fs.existsSync(to) ? fs.readFileSync(to, 'utf8') : null;
      const next = fs.readFileSync(from, 'utf8');
      if (cur !== next) {
        fs.copyFileSync(from, to);
        n++;
      }
    }
    log(`Skills: ${n}/${names.length} copied → ${t}${n ? '' : ' (up to date)'}`);
  }
}

function ensureContract(vaultRoot) {
  const dst = path.join(vaultRoot, 'AGENTS.md');
  if (fs.existsSync(dst)) {
    log('AGENTS.md: already present (left untouched)');
    return;
  }
  fs.copyFileSync(path.join(PAYLOAD, 'AGENTS.md'), dst);
  log('AGENTS.md: installed operating contract', 'ok');
}

function selftest(python, serverPath) {
  const payload =
    '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2024-11-05","capabilities":{},"clientInfo":{"name":"kv-kit-test","version":"1"}}}\n' +
    '{"jsonrpc":"2.0","id":2,"method":"tools/list","params":{}}\n';
  const r = spawnSync(python, [serverPath], { input: payload, encoding: 'utf8', timeout: 15000 });
  if (r.status !== 0) {
    log(`Self-test failed: ${r.stderr?.trim() || r.error?.message}`, 'err');
    return false;
  }
  const lines = (r.stdout || '').trim().split('\n').filter(Boolean);
  const init = lines.find(l => l.includes('"id": 1'));
  const tools = lines.find(l => l.includes('"tools":'));
  if (!init || !tools) {
    log('Self-test: server responded but payload unexpected', 'err');
    return false;
  }
  const names = (tools.match(/"name":\s*"([^"]+)"/g) || []).map(s => s.replace(/"name":\s*/, '').replace(/"/g, ''));
  log(`Self-test: server handshake OK (${names.length} tools: ${names.join(', ')})`, 'ok');
  return true;
}

function main(argv) {
  console.log('knowledge-vault-kit 0.1.0 — KNOWLEDGE vault installer\n');
  const vaultRoot = resolveVaultRoot(argv);
  log(`vault root: ${vaultRoot}`);
  const python = argv['--python'] || findPython();
  log(`python: ${python}`);
  const serverDir = installMcpServer(vaultRoot);
  const serverPath = path.join(serverDir, 'server.py');
  const clients = (argv['--clients'] || 'zcode,claude,opencode,generic').split(',').map(s => s.trim());
  if (clients.includes('zcode')) registerZCode(python, serverPath);
  if (clients.includes('claude')) registerClaude(python, serverPath);
  if (clients.includes('opencode')) registerOpenCode(python, serverPath);
  if (clients.includes('generic')) registerGeneric(vaultRoot, python, serverPath);
  installSkills(vaultRoot, argv);
  ensureContract(vaultRoot);
  if (argv['--no-test'] !== true) {
    console.log('');
    log('Running server self-test…');
    const ok = selftest(python, serverPath);
    if (!ok) process.exitCode = 1;
  }
  console.log('');
  log('Done. Restart your AI client so it re-reads MCP config.', 'ok');
}

const args = {};
for (let i = 2; i < process.argv.length; i++) {
  const a = process.argv[i];
  if (a.startsWith('--')) {
    const eq = a.indexOf('=');
    if (eq !== -1) {
      args[a.slice(0, eq)] = a.slice(eq + 1);
      continue;
    }
    args[a] = true;
    if (i + 1 < process.argv.length && !process.argv[i + 1].startsWith('--')) {
      args[a] = process.argv[i + 1];
      i++;
    }
  }
}

if (args['--help'] || args['-h']) {
  console.log(`Usage:
  npx knowledge-vault-kit [options]

Options:
  --vault <path>       vault root (default: $KNOWLEDGE_VAULT or D:\\KNOWLEDGE)
  --python <path>      python interpreter for the MCP server
  --clients <list>     comma list: zcode,claude,opencode,generic
                       (default: "zcode,claude,opencode,generic")
  --dsh-skills         also mirror skills into $DSH_HOME/skills
  --no-zcode-skills    skip writing skills under <vault>/.zcode/skills
  --no-test            skip the server self-test
  --help               this message`);
  process.exit(0);
}

try {
  main(args);
} catch (e) {
  log(e.message, 'err');
  process.exitCode = 1;
}
