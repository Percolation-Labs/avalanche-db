"""evals/p8ql/score.py RUNS_DIR -- score every run: RUNS_DIR/<arm>-<qid>[-<rep>]/answer.json is the
agent's {"ids": [...]} and calls.log its midb calls. Prints recall, precision and calls per
question and arm (means over replicates, with the range of calls), then per arm."""
import json, os, re, sys
from collections import defaultdict
runs = sys.argv[1]
gold = {q["id"]: q for q in map(json.loads, open(os.path.join(os.path.dirname(__file__), "questions.jsonl")))}
cells = defaultdict(list)
for d in sorted(os.listdir(runs)):
    m = re.fullmatch(r"(p8ql|baseline)-(Q\d+)(?:-(\d+))?", d)
    if not m:
        continue
    arm, qid = m.group(1), m.group(2)
    p = os.path.join(runs, d)
    try:
        ids = set(json.load(open(os.path.join(p, "answer.json")))["ids"])
    except Exception:
        ids = set()
    calls = [l for l in open(os.path.join(p, "calls.log")).read().splitlines() if l.strip()]
    g = set(gold[qid]["gold"])
    hit = len(ids & g)
    cells[(qid, arm)].append((hit / len(g), hit / len(ids) if ids else 0.0, len(calls)))
mean = lambda xs: sum(xs) / len(xs)
print(f"{'q':<4} {'tier':<14} {'arm':<9} runs  recall  precision  calls (range)")
for (qid, arm), rs in sorted(cells.items()):
    c = [r[2] for r in rs]
    print(f"{qid:<4} {gold[qid]['tier']:<14} {arm:<9} {len(rs):>4}  {mean([r[0] for r in rs]):>6.2f}  {mean([r[1] for r in rs]):>9.2f}  {mean(c):>5.1f} ({min(c)}-{max(c)})")
for arm in sorted({a for _, a in cells}):
    rs = [r for (q, a), v in cells.items() if a == arm for r in v]
    print(f"{arm:<9} mean recall {mean([r[0] for r in rs]):.2f}, precision {mean([r[1] for r in rs]):.2f}, calls {mean([r[2] for r in rs]):.1f} over {len(rs)} runs")
