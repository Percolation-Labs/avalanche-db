"""Uncapped-keys look (22 Nov, james, $0, no Jev; bill 17:03Z). For each graph variant, on train answerable chains
(2hop, 3hop1, 4hop1), per chain step i -> i+1 (gold decomposition):
  keyed   hop i and hop i+1 share a door key (not contained in the question)
  |S|     for the shared key the name step would most want (the lowest-df shared key), the number of passages in the
          question's own pool of 20, other than hop i, that hold it (the name step's candidate set; 1 = a sure step)
  |R|     the number of door keys on hop i (the name request's options)
    python3 keys_look.py TRAIN_CORPUS GRAPH.jsonl [GRAPH.jsonl ...]"""
import hashlib, json, re, statistics as st, sys
from collections import Counter, defaultdict
src, graphs = sys.argv[1], sys.argv[2:]
hid = lambda p: "mq:" + hashlib.sha256((p["title"] + "\n" + p["paragraph_text"]).encode()).hexdigest()[:16]
Qs = [r for r in map(json.loads, open(src)) if r["answerable"] and r["id"].split("__")[0] in ("2hop", "3hop1", "4hop1")]
for g in graphs:
    rows = [json.loads(l) for l in open(g)]; keys = {r["d"]: set(r["keys"]) for r in rows}
    df = Counter(k for r in rows for k in r["keys"])
    agg = defaultdict(lambda: defaultdict(list))
    for r in Qs:
        t = r["id"].split("__")[0]; qt = set(re.findall(r"[a-z0-9]+", r["question"].lower()))
        P = sorted(r["paragraphs"], key=lambda p: p["idx"]); ix = {p["idx"]: i for i, p in enumerate(P)}
        D = [{k for k in keys.get(hid(p), ()) if df[k] >= 2 and not set(k.split()) <= qt} for p in P]
        hops = [ix[s["paragraph_support_idx"]] for s in r["question_decomposition"]]
        for i in range(len(hops) - 1):
            a, b = hops[i], hops[i + 1]; sh = D[a] & D[b]; stp = "first" if i == 0 else "later"
            A = agg[(t if t == "2hop" else "3-4hop", stp)]
            A["keyed"].append(bool(sh)); A["R"].append(len(D[a]))
            if sh:
                k = min(sh, key=lambda k: (df[k], k))
                A["S"].append(sum(k in D[v] for v in range(len(P)) if v != a))
                A["dfk"].append(df[k])
    print(f"== {g.rsplit('/', 1)[-1]}")
    for (t, stp), A in sorted(agg.items()):
        S = A["S"]
        print(f"   {t:6s} {stp:5s} steps {len(A['keyed']):4d}  keyed {sum(A['keyed']) / len(A['keyed']):.2f}  "
              f"|R| median {st.median(A['R']):.0f}  |S| median {st.median(S) if S else 0:.0f}, |S|=1 {sum(s == 1 for s in S) / max(1, len(S)):.2f}, "
              f"|S|>=5 {sum(s >= 5 for s in S) / max(1, len(S)):.2f}  bridge-key df median {st.median(A['dfk']) if A['dfk'] else 0:.0f}")
