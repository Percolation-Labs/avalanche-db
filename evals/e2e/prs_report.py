"""REGISTERED-prs.md's reported extras at k=10: gold commits split by how many title words they share with the
question (lowercase [a-z0-9]+ tokens of three or more characters, in the commit's subject), and the door each gold
commit the walk returned came through.

    python3 prs_report.py REPO QUESTIONS.jsonl WALK.jsonl CTL_PREFIX
"""
import collections, json, re, subprocess, sys

repo, qpath, wpath, ctl = sys.argv[1:5]
K = 10
qs = {q["qid"]: q for q in map(json.loads, open(qpath))}
walk = {r["qid"]: r for r in map(json.loads, open(wpath)) if r["k"] == K}
ctlr = {r["qid"]: r for r in map(json.loads, open(f"{ctl}.k{K}.jsonl"))}
words = lambda s: {w for w in re.findall(r"[a-z0-9]+", s.lower()) if len(w) >= 3}
subj = {}
for qid, q in qs.items():
    for g in q["gold"]:
        subj[g] = subprocess.run(["git", "-C", repo, "log", "-1", "--format=%s", g.split("/")[1]],
                                 capture_output=True, text=True).stdout.strip()
groups = collections.defaultdict(lambda: [0, 0, 0])   # n, search hits, walk hits
via = collections.Counter()
for qid, q in qs.items():
    if qid not in walk:
        continue
    title = words(q["question"].split(":", 1)[1])
    s, w = set(ctlr[qid]["search"][:K]), walk[qid]["docs"][:K]
    for g in q["gold"]:
        key = "<=1 shared" if len(title & words(subj[g])) <= 1 else ">=2 shared"
        groups[key][0] += 1
        groups[key][1] += g in s
        groups[key][2] += g in w
    for d, v in zip(w, walk[qid]["via"]):
        if d in q["gold"]:
            via["search" if v == "search" else v.split(":")[0] + (":session" if "session_" in v else "")] += 1
print(f"gold commits by title words shared, k={K}: n, search, walk")
for k in sorted(groups):
    n, s, w = groups[k]
    print(f"  {k}: {n}  search {s/n:.2f}  walk {w/n:.2f}")
print("gold returned by the walk, by door kind:", dict(via.most_common()))
