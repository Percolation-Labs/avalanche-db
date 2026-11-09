"""evals/p8ql/score.py RUNS_DIR -- score every run: RUNS_DIR/<arm>-<qid>[-<rep>]/answer.json is the
agent's {"ids": [...]} and calls.log its midb calls; SET=history scores history/questions.jsonl. Prints recall, precision and calls per
question and arm (means over replicates, with the range of calls), then per arm."""
import json, os, re, sys
from collections import defaultdict
runs = sys.argv[1]
qs = os.path.join(os.path.dirname(os.path.abspath(__file__)), os.environ.get("SET", ""), "questions.jsonl")
gold = {q["id"]: q for q in map(json.loads, open(qs))}
cells = defaultdict(list)
for d in sorted(os.listdir(runs)):
    m = re.fullmatch(r"(p8ql|baseline)-([A-Z]\d+)(?:-(\d+))?", d)
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
    try:
        a = json.load(open(os.path.join(p, "agent.json")))
        turns, cost = a.get("num_turns", 0), a.get("total_cost_usd", 0.0)
    except Exception:
        turns, cost = 0, 0.0
    cells[(qid, arm)].append((hit / len(g), hit / len(ids) if ids else 0.0, len(calls), turns, cost))
mean = lambda xs: sum(xs) / len(xs)
# calls counts midb invocations; one agent turn can run many (a shell loop), so turns and
# cost (from agent.json, written by run.sh) are the measure of the agent's work.
print(f"{'q':<4} {'tier':<14} {'arm':<9} runs  recall  precision  calls (range)  turns  cost")
for (qid, arm), rs in sorted(cells.items()):
    c = [r[2] for r in rs]
    print(f"{qid:<4} {gold[qid]['tier']:<14} {arm:<9} {len(rs):>4}  {mean([r[0] for r in rs]):>6.2f}  {mean([r[1] for r in rs]):>9.2f}  {mean(c):>5.1f} ({min(c)}-{max(c)})  {mean([r[3] for r in rs]):>5.1f}  ${mean([r[4] for r in rs]):.3f}")
for arm in sorted({a for _, a in cells}):
    rs = [r for (q, a), v in cells.items() if a == arm for r in v]
    print(f"{arm:<9} mean recall {mean([r[0] for r in rs]):.2f}, precision {mean([r[1] for r in rs]):.2f}, calls {mean([r[2] for r in rs]):.1f}, turns {mean([r[3] for r in rs]):.1f}, cost ${mean([r[4] for r in rs]):.3f} over {len(rs)} runs")
