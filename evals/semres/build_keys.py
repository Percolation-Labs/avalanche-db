"""Door-key graph for a set of MuSiQue passages, with percolate-core's frequency strategy at the dev fixture's declared
limits (fixture-musique manifest: max_n 3, min_df 2, df_floor 20, df_share .02, nest .9), keeping keys with
2 <= df <= 100 as d1probe's dump does. Ids are dream-d1's: "mq:" + sha256(title + "\n" + paragraph_text)[:16].
Text is the fixture's "said": title + "\n\n" + paragraph_text.
    uv run --with 'percolate-core==0.2.16' python build_keys.py MUSIQUE_JSONL [MUSIQUE_JSONL ...] OUT.jsonl"""
import hashlib, json, sys
from percolate_core.walk import terms as T
*srcs, out = sys.argv[1:]
docs = {}
for s in srcs:
    for r in map(json.loads, open(s)):
        for p in r["paragraphs"]:
            d = "mq:" + hashlib.sha256((p["title"] + "\n" + p["paragraph_text"]).encode()).hexdigest()[:16]
            docs.setdefault(d, p["title"] + "\n\n" + p["paragraph_text"])
ids = sorted(docs)
post = T.frequency([docs[d] for d in ids], max_n=3, min_df=2, df_floor=20, df_share=0.02, nest=0.9)
keys = {d: [] for d in ids}
for k, ix in post.items():
    if 2 <= len(ix) <= 100:
        for i in ix: keys[ids[i]].append(k)
with open(out, "w") as f:
    for d in ids: f.write(json.dumps({"d": d, "keys": sorted(keys[d])}) + "\n")
print(f"{len(ids)} passages, {sum(map(len, keys.values()))} keys -> {out}")
