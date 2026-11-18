import json, subprocess, sys, os, time
midb, store, qfile, out, cap = sys.argv[1], sys.argv[2], sys.argv[3], sys.argv[4], float(sys.argv[5])
done = set()
if os.path.exists(out):
    done = {json.loads(l)["qid"] for l in open(out)}
spent = 0.0
with open(out, "a") as f:
    for l in open(qfile):
        q = json.loads(l)
        if q["qid"] in done: continue
        t = time.time()
        r = subprocess.run([midb, "--dir", store, "walk", "--budget", "10", "--trace", q["question"]], capture_output=True, text=True)
        if r.returncode: print("ERR", q["qid"], r.stderr[:200]); continue
        w = json.loads(r.stdout); spent += w["cost_usd"]
        f.write(json.dumps({"qid": q["qid"], "gold": q["gold"], "walk": w}) + "\n"); f.flush()
        print(q["qid"], w["called"], round(w["cost_usd"],4), round(time.time()-t,1), flush=True)
        if spent > cap: print("CAP", spent); break
print("spent", spent)
