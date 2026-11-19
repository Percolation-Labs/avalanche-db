"""J5 diagnostic ($0, not registered): did the door text carry the next hop's gold?  python j5diag.py SCRATCH J5DIR"""
import hashlib, json, math, os, re, sys
from collections import defaultdict
scr, d = sys.argv[1:3]
SRC = os.path.expanduser("~/.cache/walklab/musique-src/musique_ans_v1.0_dev.jsonl")
src, text = {}, {}
hid = lambda p: "mq:" + hashlib.sha256((p["title"] + "\n" + p["paragraph_text"]).encode()).hexdigest()[:16]
for l in open(SRC):
    r = json.loads(l); src[r["id"]] = r
    for p in r["paragraphs"]:
        text[hid(p)] = p["title"] + ". " + p["paragraph_text"]
km = defaultdict(list)
for r in map(json.loads, open(f"{scr}/dream/d1/graph-mq.jsonl")):
    for k in r["keys"]:
        km[k].append(r["d"])
tok = lambda x: re.findall(r"[a-z0-9]+", x.lower())
dt = {h: tok(t) for h, t in text.items()}; df = defaultdict(int)
for ts in dt.values():
    for t in set(ts): df[t] += 1
N = len(dt); AV = sum(map(len, dt.values())) / N
def bm(qt, h):
    ts = dt.get(h, []); L = len(ts); s = 0
    for t in qt:
        f = ts.count(t)
        if f: s += math.log(1 + (N - df[t] + .5) / (df[t] + .5)) * f * 2.2 / (f + 1.2 * (.25 + .75 * L / AV))
    return s
n = door = top = 0; dist_door = []
for r in map(json.loads, open(f"{d}/j1-J.jsonl")):
    s = src[r["qid"].split(":", 1)[1]]; dec = s["question_decomposition"]; qt = set(tok(s["question"]))
    for p in r["picks"]:
        if not p["gold_is_cand"]: continue
        n += 1; ms = km.get(p["gold_answer"].lower().strip(), [])
        if 2 <= len(ms) <= 100:
            door += 1
            nxt = hid(next(x for x in s["paragraphs"] if x["idx"] == dec[p["hop"]]["paragraph_support_idx"]))
            top += max(ms, key=lambda m: bm(qt, m)) == nxt
print(f"decisions with gold a candidate: {n}; gold answer has a door (key in 2-100): {door} ({door/n:.2f}); "
      f"the door's closest passage is the next hop's gold: {top} ({top/n:.2f})")
