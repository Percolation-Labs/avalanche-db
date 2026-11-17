"""REGISTERED-leads.md's $0 step: per candidate, Shown (gold-bearing doors whose text shows a gold commit, by its
`commit {sha7}` title) and the question-door overlap AUC (score0.py's), from the probe's door rows.

    python3 score_leads.py QUESTIONS.jsonl NAME=PROBE.jsonl ...
"""
import json
import sys

from score0 import auc, toks


def main(qpath, *runs):
    qs = {q["qid"]: q for q in map(json.loads, open(qpath))}
    for run in runs:
        name, path = run.split("=")
        rows = [json.loads(l) for l in open(path)]
        shown = gold_doors = id_shown = id_doors = 0
        groups = []
        for r in rows:
            gold = [g.split("/")[1][:7] for g in r["gold"]]
            q = qs[r["qid"]]["question"]
            ds = []
            for key, d in r["doors"].items():
                y = d["gold"] > 0
                ds.append((len(toks(q) & toks(d["text"])), y))
                if y:
                    s = any(f"commit {g}" in d["text"] for g in gold)
                    gold_doors += 1
                    shown += s
                    if key.startswith("term:rem "):
                        id_doors += 1
                        id_shown += s
            if any(y for _, y in ds) and not all(y for _, y in ds):
                groups.append(ds)
        print(f"{name:5s} Shown {shown / gold_doors:.3f} ({shown}/{gold_doors})  id door Shown {id_shown / max(id_doors, 1):.3f} "
              f"({id_shown}/{id_doors})  overlap AUC {auc(groups):.3f}  ({len(rows)} cards)")


if __name__ == "__main__":
    main(*sys.argv[1:])
