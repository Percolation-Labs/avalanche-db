"""Train-graph key files without the df <= 100 dump cap (james, for the uncapped-keys look; bill 17:03Z).
Same frequency strategy and declared limits as build_keys.py, then two variants:
  cap508  keep every key the strategy keeps (its own cap = max(df_floor, df_share * N) = 508 here); no dump cap
  nocap   df_share = 1 (no ceiling at all), every key with df >= 2
    uv run --with 'percolate-core==0.2.16' python build_keys_uncapped.py MUSIQUE_JSONL OUT_PREFIX"""
import hashlib, json, sys
from percolate_core.walk import terms as T
src, pre = sys.argv[1:]
docs = {}
for r in map(json.loads, open(src)):
    for p in r["paragraphs"]:
        d = "mq:" + hashlib.sha256((p["title"] + "\n" + p["paragraph_text"]).encode()).hexdigest()[:16]
        docs.setdefault(d, p["title"] + "\n\n" + p["paragraph_text"])
ids = sorted(docs)
for name, share in (("cap508", 0.02), ("nocap", 1.0)):
    post = T.frequency([docs[d] for d in ids], max_n=3, min_df=2, df_floor=20, df_share=share, nest=0.9)
    keys = {d: [] for d in ids}
    for k, ix in post.items():
        for i in ix: keys[ids[i]].append(k)
    with open(f"{pre}-{name}.jsonl", "w") as f:
        for d in ids: f.write(json.dumps({"d": d, "keys": sorted(keys[d])}) + "\n")
    top = sorted(post, key=lambda k: -len(post[k]))[:15]
    print(f"{name}: {len(ids)} passages, {len(post)} keys, {sum(map(len, keys.values()))} memberships; top df: "
          + ", ".join(f"{k} {len(post[k])}" for k in top), flush=True)
