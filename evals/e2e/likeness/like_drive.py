"""Likeness-door arms via `midb walk --trace`. Resumable on (qid, arm); stops before a walk once spend >= cap.
    python3 like_drive.py MIDB STORE QUESTIONS OUT --arm none|match|search|plain --cap 0.30 [--n N]"""
import argparse, json, os, subprocess, sys
ap = argparse.ArgumentParser()
for a in ("midb", "store", "questions", "out"): ap.add_argument(a)
ap.add_argument("--arm", required=True); ap.add_argument("--cap", type=float, required=True); ap.add_argument("--n", type=int, default=0)
a = ap.parse_args()
qs = [json.loads(l) for l in open(a.questions) if l.strip()][: a.n or None]
done, spent = set(), 0.0
if os.path.exists(a.out):
    for l in open(a.out):
        r = json.loads(l); spent += r["cost_usd"]
        if r["arm"] == a.arm: done.add(r["qid"])
with open(a.out, "a") as f:
    for q in qs:
        if q["qid"] in done: continue
        if spent >= a.cap: sys.exit(f"cap ${a.cap:.2f} reached: ${spent:.4f}")
        cmd = [a.midb, "--dir", a.store, "walk", "--budget", "10", "--trace"] + ([] if a.arm == "none" else ["--like", a.arm]) + [q["question"]]
        p = subprocess.run(cmd, capture_output=True, text=True)
        if p.returncode: sys.exit(f"{q['qid']}: {p.stderr[-400:]}")
        w = json.loads(p.stdout); spent += w["cost_usd"]
        like = []
        for b in w["trace"]["batches"]:
            sc = {r["key"]: (i, r["score"]) for i, r in enumerate(b["ranking"])}
            for d in b["doors"]:
                if d["kind"] == "like":
                    like.append({"wave": b["wave"], "pos": sc.get(d["key"], (None, None))[0], "p": sc.get(d["key"], (None, None))[1], "of": len(b["ranking"]), "opened": d["key"] in b["opened"]})
            top = b["ranking"][0]["score"] if b["ranking"] else None
            if like and like[-1]["wave"] == b["wave"]: like[-1]["top"] = top
        f.write(json.dumps({"qid": q["qid"], "arm": a.arm, "docs": [d["id"] for d in w["documents"]], "via": [d["via"] for d in w["documents"]],
                            "like": like, "requests": w["requests"], "called": w["called"], "cost_usd": w["cost_usd"]}) + "\n"); f.flush()
print(f"done {a.arm}: ${spent:.4f} in this file")
