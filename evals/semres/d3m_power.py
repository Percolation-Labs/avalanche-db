"""D3m power check (gold-blind: no test outcomes are scored). Memory = memberships traversed by SR-BW's Jev-named walks
(entry e = argmax cos(q, ·); K = Jev's named key; step s = name's step), on SR-BW questions not in D3's MuSiQue test.
Counts: memory size; how many D3 (q .05) would remove; how many of those keys are offered as doors in D3's test waves."""
import collections, gzip, hashlib, json, re, subprocess, sys
import numpy as np
src = open("d3_src.py").read(); src = src[:src.index("def random_edit")]; ns = {}; exec(src, ns); G, votes = ns["G"], ns["votes"]
D1 = "/private/tmp/claude-501/-Users-sirsh-code-p8-subsystems/afff46e9-e53a-4040-8740-ac4e25fa389d/scratchpad"
rows = [json.loads(l) for l in open(f"{D1}/dream/d1/graph-mq.jsonl")]; g = G(rows)
hid = lambda p: "mq:" + hashlib.sha256((p["title"] + "\n" + p["paragraph_text"]).encode()).hexdigest()[:16]
test = {json.loads(l)["qid"].split(":", 1)[1] for l in open(f"{D1}/floor/q-musique-questions.jsonl")}
qs = [r for r in map(json.loads, open("/Users/sirsh/.cache/walklab/musique-src/musique_ans_v1.0_dev.jsonl")) if r["id"].startswith("2hop") and r["answerable"]]
bw = json.loads(subprocess.run(["git", "-C", sys.argv[1], "show", "origin/main:evals/semres/out/srbw-fresh.json"], capture_output=True, text=True).stdout)["out"]
from sentence_transformers import SentenceTransformer
m = SentenceTransformer("BAAI/bge-small-en-v1.5", device="cpu"); QP = "Represent this sentence for searching relevant passages: "
memix = {(int(u), int(j)): i for i, (u, j) in enumerate(g.mem)}; df0 = g.df.copy()
mem = set(); used = 0; skipped = 0
for o in bw:
    r = qs[o["qi"]]
    if r["id"] in test: skipped += 1; continue
    P = sorted(r["paragraphs"], key=lambda p: p["idx"]); T = [p["title"] + ". " + p["paragraph_text"] for p in P]
    E = m.encode([QP + r["question"]] + T, normalize_embeddings=True); e = int(np.argmax(E[1:] @ E[0])); K = o["K"]
    j = g.kix.get(K); ue = g.ix[hid(P[e])]
    if j is None: continue
    used += 1; mem.add(memix[(ue, j)])
    for v, p in enumerate(P):   # every pool passage sharing K is a sharer the step considered; the step itself picks one
        if v != e and K in rows[g.ix[hid(p)]]["keys"]: mem.add(memix[(g.ix[hid(p)], j)])
print(f"SR-BW walks {len(bw)}; in D3 test {skipped}; used {used}; memory memberships {len(mem)}")
keep = g.keep.copy(); owned = set(g.owned)
for rnd in range(4):
    ratio, oratio = votes(g); drop = keep & (ratio < 0.05); odrop = {d for d in owned if oratio.get(d, np.inf) < 0.05}
    ch = (drop.sum() + len(odrop)) / (keep.sum() + len(owned)); keep &= ~drop; owned -= odrop; g.build(keep, owned)
    if ch < 0.01: break
M = np.array(sorted(mem)); rem = M[~keep[M]]
print(f"D3 removes {len(rem)} of the {len(M)} memory memberships ({len(rem) / len(M):.3f}); D3 removes {(~keep).sum()} memberships in all")
tk = collections.Counter()
for r in map(json.loads, gzip.decompress(subprocess.run(["git", "-C", "/Users/sirsh/code/avalanche-d1", "show", "origin/main:evals/structural/out/ft-mq.jsonl.gz"], capture_output=True).stdout).decode().splitlines()):
    if r["key"].startswith("term:"): tk[r["key"][5:]] += 1
remk = {rows[g.mem[i, 0]]["d"] for i in rem}; kk = {list(g.kix)[g.mem[i, 1]] for i in rem} if len(rem) < 5000 else set()
inv = {v: k for k, v in g.kix.items()}
hit = [i for i in rem if inv[g.mem[i, 1]] in tk]
print(f"of those, keys offered as a door in D3's test waves: {len(hit)} memberships ({len({inv[g.mem[i, 1]] for i in hit})} keys, {sum(tk[inv[g.mem[i, 1]]] for i in hit)} door offers)")
