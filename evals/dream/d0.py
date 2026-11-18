"""D0 (evals/dream/REGISTERED-D0.md). python3 d0.py SET STORE CAP [--probe]"""
import ast, hashlib, json, os, subprocess, sys, urllib.request, re
SET, STORE, CAP = sys.argv[1], sys.argv[2], float(sys.argv[3]); PROBE = "--probe" in sys.argv
MIDB = "../floor/midb-like"; KEY = os.environ["AVALANCHE_MODEL_KEY"]; ENDPOINT = "https://api.typesafe.ai/v1/systemone"
OUT = f"d0-{SET}.jsonl"; PRICE = 0.042 / 1e6
js = lambda s: json.dumps(s, ensure_ascii=False)

def body(req):
    st = req["state"]; s = '{"model":%s,"state":{"question":%s,"task":%s' % (js(req["model"]), js(st["question"]), js(st["task"]))
    if "found" in st: s += ',"found":' + json.dumps(st["found"], ensure_ascii=False, separators=(",", ":"))
    return s + '},"questions":{' + ",".join('%s:{"type":"noul","instructions":%s}' % (js(k), js(v["instructions"])) for k, v in sorted(req["questions"].items(), key=lambda kv: int(kv[0].split("_")[0]) if kv[0].split("_")[0].isdigit() else 0)) + "}}"

# the store's recorded requests, by option text
cases = [json.loads(l) for l in open(f"dt-{SET}.jsonl")]
qset = {c["question"] for c in cases}
reqs = []
for l in open(f"{STORE}/.avalanche/decisions.jsonl"):
    r = json.loads(l); q = r["request"]
    if q["state"]["question"] in qset: reqs.append((r["key"], q, r["response"]))
print("requests for these questions:", len(reqs), file=sys.stderr)

mcp = subprocess.Popen([MIDB, "--dir", STORE, "mcp"], stdin=subprocess.PIPE, stdout=subprocess.PIPE, text=True, bufsize=1, env=dict(os.environ, AVALANCHE_MODEL_KEY="invalid-replay-only"))
n = 0
def rpc(m, p):
    global n; n += 1
    mcp.stdin.write(json.dumps({"jsonrpc": "2.0", "id": n, "method": m, "params": p}) + "\n"); mcp.stdin.flush()
    return json.loads(mcp.stdout.readline())["result"]
rpc("initialize", {"protocolVersion": "2025-06-18", "capabilities": {}, "clientInfo": {"name": "d0", "version": "1"}})
mcp.stdin.write(json.dumps({"jsonrpc": "2.0", "method": "notifications/initialized"}) + "\n")
def doc(i):
    t = rpc("tools/call", {"name": "read_document", "arguments": {"id": i}})["content"][0]["text"]
    head, _, rest = t.partition("\n"); _, _, content = rest.partition("\n\n")
    return head.split("  ", 1)[1] if "  " in head else i, content

def body_of(title, text):
    lines = text.split("\n"); i = 0
    while i < len(lines) and (not lines[i].strip() or lines[i].lstrip().startswith("#")): i += 1
    if i < len(lines) and lines[i].strip() and lines[i].strip()[:40] in title: i += 1
    rest = "\n".join(lines[i:]).strip()
    return rest if rest else text

def sentences(text):
    flat = " ".join(text.split()); out = []; start = 0
    for i, c in enumerate(flat):
        if c in ".!?" and flat[i + 1:i + 2] == " " and i - start > 20:
            out.append(flat[start:i + 1]); start = i + 2
    if start < len(flat): out.append(flat[start:])
    return [s[:200] for s in out if s]

words = lambda s: set(re.findall(r"[a-z0-9]+", s.lower()))

def variants(door, question):
    """lead lines rebuilt per rule; returns {rule: text}, and how many leads had an alternative sentence."""
    imm = door["attrs"]["immediate"]; targets = door["targets"]; info = {t: doc(t) for t in targets}
    out = {r: [] for r in ("second", "last", "longest", "q-best")}; alt = leads = 0
    for j, line in enumerate(imm):
        hit = None
        if j >= 2 and line.startswith("- ") and not line.startswith("Names in its"):
            for t, (title, text) in info.items():
                st = " ".join(title.split())[:120]
                if line.startswith(f"- {st}: "): hit = (st, sentences(body_of(title, text))); break
        if not hit:
            for r in out: out[r].append(line)
            continue
        st, ss = hit; leads += 1; alt += len(ss) > 1
        pick = {"second": ss[1] if len(ss) > 1 else ss[0], "last": ss[-1], "longest": max(ss, key=len),
                "q-best": max(ss, key=lambda s: len(words(s) & words(question)))}
        for r, s in pick.items(): out[r].append(f"- {st}: {s}")
    return {r: "\n".join(v) for r, v in out.items()}, leads, alt

def ask(b):
    rq = urllib.request.Request(ENDPOINT, data=b.encode(), headers={"Authorization": f"Bearer {KEY}", "Content-Type": "application/json"})
    return json.load(urllib.request.urlopen(rq, timeout=120))

done = set(); spent = 0.0
if os.path.exists(OUT):
    for l in open(OUT): r = json.loads(l); done.add(r["qid"]); spent += r["cost"]
with open(OUT, "a") as f:
    for c in cases:
        b = c["batch1"]; g = set(c["gold"]); tg = {d["key"]: d for d in b["doors"]}
        order = [x["key"] for x in b["ranking"]]; P = {x["key"]: x["score"] for x in b["ranking"]}
        gi = [i for i, k in enumerate(order) if g & set(tg[k]["targets"])]
        if not gi or gi[0] == 0 or c["qid"] in done: continue
        if spent >= CAP: sys.exit(f"cap reached ${spent:.4f}")
        rec = {"qid": c["qid"], "gold_rank": gi[0], "n": len(order), "cost": 0.0, "doors": {}}
        for role, k in (("gold", order[gi[0]]), ("control", order[0])):
            text = "\n".join(tg[k]["attrs"]["immediate"])
            hit = [(key, q, a, o) for key, q, a in reqs for o, v in q["questions"].items() if v["instructions"] == text and q["state"]["question"] == c["question"]]
            if not hit: rec["doors"][role] = {"error": "request not found"}; continue
            key, q, a, opt = hit[0]
            assert hashlib.sha256(body(q).encode()).hexdigest() == key, "builder check failed"
            assert abs(a["answers"][opt]["noul"] - P[k]) < 1e-6
            vs, leads, alt = variants(tg[k], c["question"]); d = {"key": k, "p": P[k], "leads": leads, "alt": alt, "v": {}}
            for rule, vt in vs.items():
                if vt == text: d["v"][rule] = P[k]; continue
                q2 = json.loads(json.dumps(q)); q2["questions"][opt]["instructions"] = vt
                ans = ask(body(q2)); p2 = ans["answers"][opt]["noul"]; cost = ans.get("usage", {}).get("input_tokens", 0) * PRICE
                rec["cost"] += cost; spent += cost; d["v"][rule] = p2
            others = [P[x] for x in order if x != k]
            d["rank"] = {rule: sum(o > p for o in others) for rule, p in d["v"].items()}; d["rank0"] = sum(o > P[k] for o in others)
            rec["doors"][role] = d
        f.write(json.dumps(rec) + "\n"); f.flush()
        if PROBE: sys.exit(f"probe: ${rec['cost']:.5f} {json.dumps(rec)[:600]}")
print(f"done {SET}: ${spent:.4f}")
