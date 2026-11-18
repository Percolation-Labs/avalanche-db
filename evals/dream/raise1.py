import json, subprocess, sys, os
midb, store, qf, out = sys.argv[1:5]
env = {k: v for k, v in os.environ.items() if k != "AVALANCHE_MODEL_KEY"}; env["HOME"] = os.path.abspath("../floor/nohome")
with open(out, "w") as f:
    for q in map(json.loads, open(qf)):
        p = subprocess.run([midb, "--dir", store, "walk", "--budget", "10", "--trace", q["question"]], capture_output=True, text=True, env=env)
        w = json.loads(p.stdout); assert w["decider"] == "search-order"
        b = w["trace"]["batches"][0]
        f.write(json.dumps({"qid": q["qid"], "gold": q["gold"], "doors": [{"key": d["key"], "targets": d["targets"]} for d in b["doors"]]}) + "\n")
