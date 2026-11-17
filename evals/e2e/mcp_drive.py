"""The walk arm of REGISTERED.md, driven exactly as Claude drives it: `midb mcp` over stdio JSON-RPC, `initialize`,
then one `tools/call walk` per question at budget k, with the documents returned read from the JSON. Resumable: a
(qid, k, kappa) already in OUT is not asked again. Spend is the walk's own report (cost_usd), summed, and the run
stops before a call once the cap is reached.

    python3 mcp_drive.py MIDB STORE_DIR QUESTIONS.jsonl OUT.jsonl --k 10 [--k 5 ...] [--n 5] [--no-kappa] --cap 1.00
"""
import argparse
import json
import subprocess
import sys

ap = argparse.ArgumentParser()
ap.add_argument("midb")
ap.add_argument("store")
ap.add_argument("questions")
ap.add_argument("out")
ap.add_argument("--k", type=int, action="append", required=True)
ap.add_argument("--n", type=int, default=0, help="only the first n questions (the pilot)")
ap.add_argument("--no-kappa", action="store_true")
ap.add_argument("--cap", type=float, required=True)
a = ap.parse_args()

qs = [json.loads(l) for l in open(a.questions) if l.strip()]
if a.n:
    qs = qs[: a.n]
done, spent = set(), 0.0
try:
    for l in open(a.out):
        r = json.loads(l)
        done.add((r["qid"], r["k"], r["kappa"]))
        spent += r["cost_usd"]
except FileNotFoundError:
    pass

p = subprocess.Popen([a.midb, "--dir", a.store, "mcp"], stdin=subprocess.PIPE, stdout=subprocess.PIPE, text=True, bufsize=1)
n = 0


def rpc(method, params):
    global n
    n += 1
    p.stdin.write(json.dumps({"jsonrpc": "2.0", "id": n, "method": method, "params": params}) + "\n")
    p.stdin.flush()
    r = json.loads(p.stdout.readline())
    if "error" in r:
        raise SystemExit(f"{method}: {r['error']}")
    return r["result"]


rpc("initialize", {"protocolVersion": "2025-06-18", "capabilities": {}, "clientInfo": {"name": "e2e", "version": "1"}})
p.stdin.write(json.dumps({"jsonrpc": "2.0", "method": "notifications/initialized"}) + "\n")
tools = {t["name"] for t in rpc("tools/list", {})["tools"]}
assert {"walk", "read_document", "ingest_repo"} <= tools, tools
kappa = not a.no_kappa
with open(a.out, "a") as f:
    for q in qs:
        for k in a.k:
            if (q["qid"], k, kappa) in done:
                continue
            if spent >= a.cap:
                sys.exit(f"cap ${a.cap:.2f} reached: ${spent:.4f} spent")
            res = rpc("tools/call", {"name": "walk", "arguments": {"question": q["question"], "budget": k, "kappa": kappa, "json": True}})
            if res.get("isError"):
                raise SystemExit(f"{q['qid']}: {res['content'][0]['text']}")
            w = json.loads(res["content"][0]["text"])
            spent += w["cost_usd"]
            f.write(json.dumps({"qid": q["qid"], "k": k, "kappa": kappa, "decider": w["decider"], "note": w.get("note"),
                                "docs": [d["id"] for d in w["documents"]], "via": [d["via"] for d in w["documents"]],
                                "requests": w["requests"], "called": w["called"], "replayed": w["replayed"],
                                "cost_usd": w["cost_usd"], "seconds": w["seconds"]}) + "\n")
            f.flush()
print(f"done: ${spent:.4f} spent in all, {len(qs)} questions, k {a.k}")
p.stdin.close()
p.wait()
