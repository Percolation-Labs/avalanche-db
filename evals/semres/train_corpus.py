"""A train corpus matched to dev's: dev's door-key graph is built over the pools of all 2,417 dev questions (21,100
passages), so df and the 2 <= df <= 100 cap depend on that size and mix. Draw train questions (seed 1342) stratified to
dev's exact count per hop type (id prefix, e.g. 2hop, 3hop1, 4hop2), answerable or not, as dev's file holds both.
Writes the sampled rows as MuSiQue jsonl; build_keys.py then makes the graph over their pools.
    python3 train_corpus.py MUSIQUE_DEV MUSIQUE_TRAIN OUT.jsonl"""
import json, random, sys
from collections import Counter, defaultdict
dev, train, out = sys.argv[1:4]
kind = lambda r: (r["id"].split("__")[0], r["answerable"])
want = Counter(kind(json.loads(l)) for l in open(dev))
by = defaultdict(list)
for l in open(train): r = json.loads(l); by[kind(r)].append(l)
rng = random.Random(1342); pick = []
for k, n in sorted(want.items()):
    have = by.get(k, [])
    if len(have) < n: sys.exit(f"train has only {len(have)} of {k}, dev has {n}")
    pick += rng.sample(have, n)
open(out, "w").writelines(pick)
print(f"{len(pick)} train questions, stratified to dev's {dict(sorted(want.items()))}")
