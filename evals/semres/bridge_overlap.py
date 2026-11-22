"""Power check for reward-driven bridge weighting (gold used only to label bridges; no walks scored).
Bridges = (passage, key) memberships whose key is a door key (2<=df<=100) shared by two consecutive gold hops.
Split questions by sha256(id) parity. What share of half-1 questions have at least one bridge membership also bridged
by a half-0 question, and what share of half-1 bridge memberships are?"""
import hashlib, json, sys
from collections import Counter
for name, gpath, src in (("dev", sys.argv[1], sys.argv[2]), ("train", sys.argv[3], sys.argv[4])):
    rows = [json.loads(l) for l in open(gpath)]; keys = {r["d"]: set(r["keys"]) for r in rows}
    df = Counter(k for r in rows for k in r["keys"])
    hid = lambda p: "mq:" + hashlib.sha256((p["title"] + "\n" + p["paragraph_text"]).encode()).hexdigest()[:16]
    half = lambda mid: int(hashlib.sha256(mid.encode()).hexdigest()[:8], 16) % 2
    B = {0: set(), 1: set()}; perq = []
    for r in map(json.loads, open(src)):
        if not r["answerable"]: continue
        P = {p["idx"]: p for p in r["paragraphs"]}; hops = [hid(P[s["paragraph_support_idx"]]) for s in r["question_decomposition"]]
        mb = set()
        for a, b in zip(hops, hops[1:]):
            for k in keys.get(a, set()) & keys.get(b, set()):
                if 2 <= df[k] <= 100: mb |= {(a, k), (b, k)}
        B[half(r["id"])] |= mb; perq.append((half(r["id"]), mb))
    h1q = [mb for h, mb in perq if h == 1 and mb]
    print(f"{name}: bridges half0 {len(B[0])}, half1 {len(B[1])}, shared {len(B[0] & B[1])}; "
          f"half-1 bridge memberships also half-0 bridges {len(B[0] & B[1]) / max(len(B[1]), 1):.3f}; "
          f"half-1 questions with >=1 bridge {len(h1q)}, of which touch a half-0 bridge {sum(bool(mb & B[0]) for mb in h1q) / max(len(h1q), 1):.3f}")
