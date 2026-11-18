import json, subprocess, sys, os
midb, store, qf, out = sys.argv[1:5]
env = dict(os.environ, AVALANCHE_MODEL_KEY="invalid-replay-only")
with open(out, "w") as f:
    for q in map(json.loads, open(qf)):
        p = subprocess.run([midb, "--dir", store, "walk", "--budget", "10", "--trace", q["question"]], capture_output=True, text=True, env=env)
        if p.returncode: print(q["qid"], p.stderr[-200:], file=sys.stderr); continue
        w = json.loads(p.stdout); assert w["called"] == 0
        f.write(json.dumps({"qid": q["qid"], "question": q["question"], "gold": q["gold"], "docs": [d["id"] for d in w["documents"]], "batch1": w["trace"]["batches"][0]}) + "\n")
