"""Parity of the lab walk across the decider refactor (specs/doors.md), on a real fixture.

    python3 -I parity.py MIDB STORE SEARCH_JSONL OUT_JSONL [--new]

Drives `MIDB lab serve --store STORE` for every question in SEARCH_JSONL (walklab's search.jsonl: {qid, order}), with
the conversation read from the qid (MQ:<conv>:...). Every judgement is answered with a fixed P per key (SHA-256 of
the key, mod 1000, over 1000), so two binaries can be compared walk for walk without any model. The settings are
the product's V0: gate .5, order per_target, the engine's defaults otherwise. Writes one {qid, walk} line per
question, with walk's batches dropped (the old engine has none).
"""
import hashlib, json, subprocess, sys

midb, store, search, out = sys.argv[1:5]

def p_of(key):
    return int.from_bytes(hashlib.sha256(key.encode()).digest()[:8], "big") % 1000 / 1000

proc = subprocess.Popen([midb, "lab", "serve", "--store", store], stdin=subprocess.PIPE, stdout=subprocess.PIPE, text=True, bufsize=1)
with open(search) as f, open(out, "w") as o:
    for line in f:
        q = json.loads(line)
        conv = q["qid"].split(":")[1]
        req = {"walk": {"conv": conv, "order": q["order"], "settings": {"gate": 0.5, "order": "per_target"}}}
        proc.stdin.write(json.dumps(req) + "\n")
        while True:
            msg = json.loads(proc.stdout.readline())
            if "judge" in msg:
                proc.stdin.write(json.dumps({"p": {c["key"]: p_of(c["key"]) for c in msg["judge"]["clues"]}}) + "\n")
                continue
            if "error" in msg:
                raise SystemExit(f"{q['qid']}: {msg['error']}")
            walk = msg["done"]
            walk.pop("batches", None)
            walk.pop("keys_read", None)
            o.write(json.dumps({"qid": q["qid"], "walk": walk}, sort_keys=True) + "\n")
            break
proc.stdin.close()
proc.wait()
