import json, hashlib, re, sys
from collections import Counter
G = sys.argv[2]; keys = {}
for l in open(G):
    r = json.loads(l); keys[r["d"]] = r["keys"]
hid = lambda p: "mq:" + hashlib.sha256((p["title"] + "\n" + p["paragraph_text"]).encode()).hexdigest()[:16]
norm = lambda s: " ".join(re.findall(r"[a-z0-9]+", s.lower()))
c = Counter(); ex = []
for l in open(sys.argv[1]):
    r = json.loads(l)
    if not r.get("answerable"): continue
    t = r["id"].split("__")[0]
    P = {p["idx"]: p for p in r["paragraphs"]}
    last = P[r["question_decomposition"][-1]["paragraph_support_idx"]]
    golds = {norm(a) for a in [r["answer"]] + r.get("answer_aliases", [])}
    ks = {norm(k) for k in keys.get(hid(last), [])}
    intext = any(g and g in norm(last["paragraph_text"] + " " + last["title"]) for g in golds)
    c[t, "n"] += 1; c[t, "key"] += bool(golds & ks); c[t, "text"] += intext
    if not (golds & ks) and len(ex) < 12: ex.append(r["answer"])
for t in sorted({k[0] for k in c}):
    n = c[t, "n"]; print(f"{t:6s} n {n:5d}  gold answer is a key of the answer passage {c[t,'key']/n:.3f}  in its text {c[t,'text']/n:.3f}")
print("examples not a key:", ex)
