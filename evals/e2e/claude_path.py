"""The README's hello-world path: drive the server .mcp.json registers, as Claude does (initialize, tools/list,
ingest_repo, walk, read_document).   python3 claude_path.py REPO/.mcp.json "question" ..."""
import json, subprocess, sys, time
cfg = json.load(open(sys.argv[1]))["mcpServers"]["avalanche"]
p = subprocess.Popen([cfg["command"], *cfg["args"]], stdin=subprocess.PIPE, stdout=subprocess.PIPE, text=True, bufsize=1)
n = 0
def rpc(m, params):
    global n; n += 1
    p.stdin.write(json.dumps({"jsonrpc": "2.0", "id": n, "method": m, "params": params}) + "\n"); p.stdin.flush()
    r = json.loads(p.stdout.readline()); assert "error" not in r, r; return r["result"]
rpc("initialize", {"protocolVersion": "2025-06-18", "capabilities": {}, "clientInfo": {"name": "hw", "version": "1"}})
p.stdin.write(json.dumps({"jsonrpc": "2.0", "method": "notifications/initialized"}) + "\n")
print("tools:", ", ".join(t["name"] for t in rpc("tools/list", {})["tools"][:3]), "...")
t = time.time(); print(rpc("tools/call", {"name": "ingest_repo", "arguments": {}})["content"][0]["text"], f"[{time.time()-t:.1f}s]")
for q in sys.argv[2:]:
    t = time.time(); w = rpc("tools/call", {"name": "walk", "arguments": {"question": q, "budget": 10}})["content"][0]["text"]
    print(w, f"[{time.time()-t:.1f}s]")
    first = w.splitlines()[[i for i, l in enumerate(w.splitlines()) if l.strip().startswith("1 ")][0]].split()[1]
    print(rpc("tools/call", {"name": "read_document", "arguments": {"id": first}})["content"][0]["text"][:400])
