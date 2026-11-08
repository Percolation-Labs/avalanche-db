"""evals/p8ql/score.py RUNS_DIR -- score every run: RUNS_DIR/<arm>-<qid>/answer.json is the
agent's {"ids": [...]} and calls.log its midb calls. Prints recall, precision and calls."""
import json, os, sys
runs = sys.argv[1]
gold = {q["id"]: q for q in map(json.loads, open(os.path.join(os.path.dirname(__file__), "questions.jsonl")))}
rows = []
for d in sorted(os.listdir(runs)):
    arm, qid = d.rsplit("-", 1)
    p = os.path.join(runs, d)
    try:
        ids = set(json.load(open(os.path.join(p, "answer.json")))["ids"])
    except Exception:
        ids = set()
    calls = [l for l in open(os.path.join(p, "calls.log")).read().splitlines() if l.strip()]
    refused = sum(1 for l in calls if l.split()[0] not in ("query", "schema", "search", "ask", "step", "why", "edges"))
    g = set(gold[qid]["gold"])
    hit = len(ids & g)
    rows.append((qid, gold[qid]["tier"], arm, hit / len(g), hit / len(ids) if ids else 0.0, len(calls)))
print(f"{'q':<4} {'tier':<14} {'arm':<9} recall  precision  calls")
for r in sorted(rows):
    print(f"{r[0]:<4} {r[1]:<14} {r[2]:<9} {r[3]:>6.2f}  {r[4]:>9.2f}  {r[5]:>5}")
for arm in sorted({r[2] for r in rows}):
    a = [r for r in rows if r[2] == arm]
    print(f"{arm:<9} mean recall {sum(r[3] for r in a)/len(a):.2f}, precision {sum(r[4] for r in a)/len(a):.2f}, calls {sum(r[5] for r in a)/len(a):.1f} over {len(a)} questions")
