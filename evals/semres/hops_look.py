"""Hops look (22 Nov, james, $0, no Jev): where does the cheap walk's one-bridge-per-read step break past 2 hops?
On MuSiQue train answerable questions (2-hop as the reference) in train-corpus.jsonl, with the train graph's door keys (the same
filter as SR-BX: 2 <= df <= 100, not contained in the question). For each hop i >= 2, by the decomposition's #j refs:
  refs     which earlier hops hop i names (#j); none = a fresh sub-question (a second entry, not a step)
  last     does hop i depend on hop i-1 (the last read) or only on an earlier read
  key      does hop i share a door key with a hop it depends on (the name step can reach it at all)
    uv run --with numpy python hops_look.py ~/.cache/walklab/mq-train/train-corpus.jsonl ~/.cache/walklab/mq-train/graph-train-pc.jsonl
"""
import hashlib, json, re, sys
from collections import Counter, defaultdict
src, gpath = sys.argv[1], sys.argv[2]
rows = [json.loads(l) for l in open(gpath)]; keys = {r["d"]: set(r["keys"]) for r in rows}
df = Counter(k for r in rows for k in r["keys"])
hid = lambda p: "mq:" + hashlib.sha256((p["title"] + "\n" + p["paragraph_text"]).encode()).hexdigest()[:16]
by = defaultdict(Counter); nq = Counter(); miss = Counter()
for r in map(json.loads, open(src)):
    t = r["id"].split("__")[0]
    if not r["answerable"]: continue
    nq[t] += 1; qt = set(re.findall(r"[a-z0-9]+", r["question"].lower()))
    P = {p["idx"]: p for p in r["paragraphs"]}; d = r["question_decomposition"]
    hop = [P[s["paragraph_support_idx"]] for s in d]
    D = [{k for k in keys.get(hid(p), ()) if 2 <= df[k] <= 100 and not set(k.split()) <= qt} for p in hop]
    miss[t] += sum(hid(p) not in keys for p in hop)
    for i in range(1, len(d)):
        refs = {int(j) - 1 for j in re.findall(r"#(\d)", d[i]["question"])}
        c = by[t]; c["steps"] += 1
        if not refs: c["fresh (no ref): a second entry"] += 1; continue
        c["depends on the last read" if i - 1 in refs else "depends only on an earlier read"] += 1
        if len(refs) > 1: c["depends on 2+ reads"] += 1
        c["shares a door key with a read it depends on"] += any(D[i] & D[j] for j in refs)
        c["shares a door key with the last read"] += bool(D[i] & D[i - 1])
        if len(refs) == 1 and i - 1 in refs: c[f"chain step {i}->{i + 1}"] += 1; c[f"chain step {i}->{i + 1} keyed"] += bool(D[i] & D[i - 1])
        c["shares a door key with any earlier hop"] += any(D[i] & D[j] for j in range(i))
for t in sorted(nq):
    print(f"{t}: {nq[t]} questions, hop passages missing from the graph {miss[t]}")
    c = by[t]; s = c.pop("steps")
    for k, v in c.items(): print(f"   {k:48s} {v:4d} of {s} steps ({v / s:.2f})")
