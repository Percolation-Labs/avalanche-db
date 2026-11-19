"""J1 (REGISTERED-J1.md): fill MuSiQue sub-questions with the title of a chosen search hit, round by round.
    python3 j1.py SCRATCH PROBE STORE OUTDIR CHOOSERS CAP [N]
CHOOSERS: comma list of J (Jev), T (search's first hit), O (gold passage). N: first N questions (stage 0 picks)."""
import hashlib, json, os, re, subprocess, sys, urllib.request

SRC = os.path.expanduser("~/.cache/walklab/musique-src/musique_ans_v1.0_dev.jsonl")
ENDPOINT = "https://api.typesafe.ai/v1/systemone"
PRICE = 0.042 / 1e6
scr, probe, store, od, choosers, cap = sys.argv[1:7]
choosers = choosers.split(","); cap = float(cap)
N = sys.argv[7] if len(sys.argv) > 7 else None
os.makedirs(od, exist_ok=True)

src, text = {}, {}
for l in open(SRC):
    r = json.loads(l); src[r["id"]] = r
    for p in r["paragraphs"]:
        h = "mq:" + hashlib.sha256((p["title"] + "\n" + p["paragraph_text"]).encode()).hexdigest()[:16]
        text[h] = (p["title"], p["paragraph_text"])

qs = [json.loads(l)["qid"] for l in open(f"{scr}/floor/trace-mq.jsonl")]
if N == "stage0":
    qs = [q for q in qs if len(src[q.split(":", 1)[1]]["question_decomposition"]) >= 3][:4]
elif N:
    qs = qs[:int(N)]


def search(batch):
    """batch: {key: query} -> {key: [doc ids]}"""
    tf, of = f"{od}/_q.jsonl", f"{od}/_s.jsonl"
    with open(tf, "w") as f:
        for k, q in batch.items():
            f.write(json.dumps({"qid": k, "walk": {"question": q}}) + "\n")
    subprocess.run([probe, store, "x", of], env=dict(os.environ, E2E_SEARCHDUMP=tf), check=True, capture_output=True)
    return {r["qid"]: [d for d, _ in r["S"]] for r in map(json.loads, open(of))}


spent = 0.0
CAPW = r"[A-Z][\w'’.\-]*"
WIDE = os.environ.get("J1_WIDE") == "1"  # J2 (REGISTERED-J2.md): top 5 passages, no 'and' joins, any digit token, cap 40
NTOP, NMAX = (5, 40) if WIDE else (3, 24)
SPAN = (re.compile(rf"{CAPW}(?:\s+(?:(?:of|the|de)\s+)?{CAPW})*|\b[\w,.\-]*\d[\w,.\-]*\b") if WIDE
        else re.compile(rf"{CAPW}(?:\s+(?:(?:of|the|de|and)\s+)?{CAPW})*|\b\d{{4}}\b"))


DOORS = os.environ.get("J1_DOORS") == "1"  # J5 (REGISTERED-J5.md): show where each candidate leads
if DOORS:
    import math
    from collections import defaultdict
    keymem = defaultdict(list)
    for r in map(json.loads, open(f"{scr}/dream/d1/graph-mq.jsonl")):
        for k in r["keys"]:
            keymem[k].append(r["d"])
    tokf = lambda x: re.findall(r"[a-z0-9]+", x.lower())
    dtok = {h: tokf(t + ". " + x) for h, (t, x) in text.items()}
    dfc = defaultdict(int)
    for ts in dtok.values():
        for t in set(ts):
            dfc[t] += 1
    NDOC = len(dtok); AVG = sum(map(len, dtok.values())) / NDOC

    def bm25(qt, h):
        ts = dtok.get(h, []); L = len(ts); sc = 0.0
        for t in qt:
            f = ts.count(t)
            if f:
                sc += math.log(1 + (NDOC - dfc[t] + .5) / (dfc[t] + .5)) * f * 2.2 / (f + 1.2 * (.25 + .75 * L / AVG))
        return sc

    def door(a, whole, read):
        ms = keymem.get(a.lower(), [])
        if not (2 <= len(ms) <= 100):
            return " — leads nowhere in the graph"
        rest = [m for m in ms if m not in read]
        if not rest:
            return f" — leads to {len(ms)} passages, all already read"
        qt = set(tokf(whole)); b = max(rest, key=lambda m: bm25(qt, m))
        t, x = text.get(b, ("", ""))
        first = re.split(r"(?<=[.!?])\s+", x)[0][:300]
        return f" — leads to {len(ms)} passages; closest to the question: {t}: {first}"


def candidates(question, hits):
    """Names and years in the top 3 hits, not in the question, reading order, at most 24: [(answer, sentence)]."""
    out, seen = [], set()
    ql = question.lower()
    for d in hits[:NTOP]:
        t, x = text.get(d, ("", ""))
        for sent in re.split(r"(?<=[.!?])\s+", f"{t}. {x}"):
            for m in SPAN.finditer(sent):
                a = m.group(0).strip(" .")
                if len(a) < 2 or a.lower() in ql or a.lower() in seen or a in ("The", "A", "An", "In", "It", "He", "She", "This"):
                    continue
                seen.add(a.lower()); out.append((a, sent.strip()[:300]))
                if len(out) >= NMAX:
                    return out
    return out


def jev(question, cands, whole=None, read=()):
    global spent
    qs_ = {}
    for i, (a, sent) in enumerate(cands):
        key = f"{i}_" + re.sub(r"[^a-z0-9]+", "_", a.lower()).strip("_")[:60]
        qs_[key] = {"type": "noul", "instructions": f"`{a}`, from: {sent}" + (door(a, whole, read) if DOORS else "")}
    if os.environ.get("J1_SHOW") == "1":
        print(json.dumps(qs_, indent=1)[:3000], flush=True)
    body = {"model": "jev-1.13.0", "state": {"question": question, "task": "Which of these is the answer to the question?"}, "questions": qs_}
    rq = urllib.request.Request(ENDPOINT, data=json.dumps(body).encode(), headers={"Authorization": f"Bearer {os.environ['AVALANCHE_MODEL_KEY']}", "Content-Type": "application/json"})
    a = json.load(urllib.request.urlopen(rq, timeout=120))
    spent += a.get("usage", {}).get("input_tokens", 0) * PRICE
    sc = {k: v["noul"] for k, v in a["answers"].items()}
    keys = list(qs_)
    best = max(range(len(cands)), key=lambda i: sc.get(keys[i], 0))
    return best, [sc.get(k) for k in keys]


def run(ch):
    out = f"{od}/j1-{ch}.jsonl"
    done = {json.loads(l)["qid"] for l in open(out)} if os.path.exists(out) else set()
    todo = [q for q in qs if q not in done]
    st = {}
    for q in todo:
        d = src[q.split(":", 1)[1]]["question_decomposition"]
        st[q] = {"subq": [s["question"] for s in d], "ans": [s["answer"] for s in d], "gold": [("mq:" + hashlib.sha256((p := next(x for x in src[q.split(':', 1)[1]]["paragraphs"] if x["idx"] == s["paragraph_support_idx"]))["title"].encode() + b"\n" + p["paragraph_text"].encode()).hexdigest()[:16]) for s in d],
                 "fill": {}, "hits": [], "queries": [], "picks": []}
    nh = max((len(s["subq"]) for s in st.values()), default=0)
    for j in range(nh):
        batch = {}
        for q, s in st.items():
            if j < len(s["subq"]):
                t = re.sub(r"#(\d+)", lambda m: s["fill"].get(int(m.group(1)), ""), s["subq"][j])
                s["queries"].append(" ".join(t.split())); batch[q] = s["queries"][-1]
        res = search(batch)
        for q, s in st.items():
            if q not in res:
                continue
            h = res[q]; s["hits"].append(h[:5])
            needed = any(f"#{j + 1}" in x for x in s["subq"][j + 1:])
            if not needed:
                continue
            cands = candidates(s["queries"][-1], h[:NTOP]); ga = s["ans"][j].lower().strip()
            gi = next((i for i, (a, _) in enumerate(cands) if a.lower() == ga), None)
            if not cands:
                i, scores = None, None
            elif ch == "T":
                i, scores = 0, None
            elif ch == "O":
                i, scores = (gi if gi is not None else 0), None
            else:
                if spent >= cap:
                    sys.exit(f"cap reached ${spent:.4f}")
                i, scores = jev(s["queries"][-1], cands, src[q.split(":", 1)[1]]["question"], {x for h in s["hits"] for x in h})
            s["fill"][j + 1] = cands[i][0] if i is not None else ""
            s["picks"].append({"hop": j + 1, "pick": i, "n_cands": len(cands), "gold_is_cand": gi is not None, "correct": i is not None and i == gi,
                               "gold_answer": s["ans"][j], "fill": s["fill"][j + 1], "scores": scores})
    with open(out, "a") as f:
        for q, s in st.items():
            seeds, k = [], 0
            while len(seeds) < 5 and any(k < len(h) for h in s["hits"]):
                for h in s["hits"]:
                    if k < len(h) and h[k] not in seeds and len(seeds) < 5:
                        seeds.append(h[k])
                k += 1
            f.write(json.dumps({"qid": q, "queries": s["queries"], "picks": s["picks"], "seeds": seeds}) + "\n")
    print(f"{ch}: {len(st)} questions, spent ${spent:.4f}", flush=True)


for ch in choosers:
    run(ch)
