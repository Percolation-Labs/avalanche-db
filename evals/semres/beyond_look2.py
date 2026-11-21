"""'Beyond the name' look 2 (unregistered, $0, cached pj from SR-BN's fresh 300, now seen). Prices a pipeline where Jev
judges passages only inside the named set:
  name   K = Jev's named key (SR-BN). S = the options sharing K.
  |S| = 0  -> k (SR-K's sum, ties by qr)       |S| = 1 -> that option       |S| > 1 -> argmax of Jev's pj within S
pj was scored per option over all 19, so restricting it to S approximates a request over S alone (Noul scores each
option on its own). Cost proxy: passages Jev reads, as a share of 19. Also: jev_pass by named-set structure (gold B).
    python3 beyond_look2.py MUSIQUE_DEV GRAPH_MQ"""
import hashlib, json, re, sys
from collections import Counter
src, gpath = sys.argv[1], sys.argv[2]
rows = [json.loads(l) for l in open(gpath)]; keys = {r["d"]: set(r["keys"]) for r in rows}
df = Counter(k for r in rows for k in r["keys"])
hid = lambda p: "mq:" + hashlib.sha256((p["title"] + "\n" + p["paragraph_text"]).encode()).hexdigest()[:16]
qs = [r for r in map(json.loads, open(src)) if r["id"].startswith("2hop") and r["answerable"]]
N = json.load(open("out/srbn-names-fresh.json")); RK = json.load(open("out/srbn-name-fresh.json"))["ranks"]
wd = lambda s: set(re.findall(r"[a-z0-9]+", s.lower())); W = lambda k: 1 / (df[k] - 1)
hit = Counter(); read = 0; struct = Counter(); n = 0
for j, (qi, v) in enumerate(N.items()):
    r = qs[int(qi)]; d = r["question_decomposition"]; h1, h2 = d[0]["paragraph_support_idx"], d[1]["paragraph_support_idx"]
    P = {p["idx"]: p for p in r["paragraphs"]}; opts = sorted(i for i in P if i != h1); h = opts.index(h2); R = set(v["R"]); n += 1
    sh = [keys[hid(P[i])] & R for i in opts]; pj = v["pj"]; K = v["jev"]
    S = [i for i, x in enumerate(sh) if K in x]
    if not S: pick = None; kind = "k fallback"        # SR-BN's step: ties by k, then qr -> same as k when K unshared
    elif len(S) == 1: pick = S[0]; kind = "one"
    else: pick = max(S, key=lambda i: pj[i]); kind = "twins"; read += len(S)
    ok = (RK["k"][j] == 1) if pick is None else (pick == h)
    hit[kind, ok] += 1; hit["all", ok] += 1
    B = {k for k in R if set(k.split()) <= wd(d[0]["answer"])}; G = [i for i, x in enumerate(sh) if x & B]
    g = "hop 2 outside gold-named set" if h not in G else ("gold twins" if len(G) > 1 else "gold alone")
    struct[g, RK["jev_pass"][j] == 1] += 1; struct[g, "lex"] += RK["ceiling_k"][j] == 1
for kind in ("one", "twins", "k fallback", "all"):
    t = hit[kind, True] + hit[kind, False]; print(f"name→{kind:10s} n {t:3d}  top-1 {hit[kind, True] / t:.3f}")
print(f"passages Jev reads in the twin step: {read / n:.2f} per question ({read / n / 19:.3f} of a 19-passage request)")
for g in ("gold alone", "gold twins", "hop 2 outside gold-named set"):
    t = struct[g, True] + struct[g, False]
    print(f"{g:30s} n {t:3d}  jev_pass {struct[g, True] / t:.3f}  gold-named lexical {struct[g, 'lex'] / t:.3f}")
