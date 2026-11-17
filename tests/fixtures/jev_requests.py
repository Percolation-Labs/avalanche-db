"""Writes tests/fixtures/jev-requests.json: door pages and the exact request bytes the lab sends Jev for them.

The lab's own code builds every byte: walklab.describe.lines for each door's text, walklab.jevcache.requests for the
cut, percolate_core.decide.Noul for the question wire, and httpx's own JSON encoder for the body (what Jev.ask posts).
Nothing is sent. tests/jev.rs must reproduce the bytes.

    git -C ~/code/p8-subsystems show origin/main:meta/lab/walklab/{__init__,describe,jevcache,engine}.py > WALKLAB/walklab/
    git -C ~/code/p8-subsystems show origin/main:meta/lab/worlds/kappa_state.py > WALKLAB/kappa_state.py
    uv run -q --with 'percolate-core==0.2.15' python tests/fixtures/jev_requests.py WALKLAB \
        [SAVED_WALKS.jsonl PAGE FIXTURE_DIR [JEV_CACHE.jsonl]]

Page 1 is synthetic (quotes, backslashes, control characters, unicode, sittings and dates, cut by count and bytes).
Page 2, when a saved walk is given, is a real MuSiQue page from the lab's a-k1 Jev run (its door texts are checked
equal to the texts that run sent, and its docs are cut to the three shown per door, 400 characters each). With the
lab's Jev cache, each of its requests is looked up under jevcache's own key, and the P Jev gave that run is kept as
`recorded`: the replay test ranks the page from those answers with no network.
"""
import hashlib
import json
import random
import sys

sys.path.insert(0, sys.argv[1])
from httpx._content import encode_json  # noqa: E402
from percolate_core.decide import MODEL, Noul  # noqa: E402
from walklab import describe, jevcache  # noqa: E402
from kappa_state import relations  # noqa: E402


class C:
    def __init__(self, c):
        self.key, self.kind, self.x, self.source, self.targets = c["key"], c["kind"], c["x"], c["source"], c["targets"]


def bodies(question, texts, found=None):
    state = {"question": question, "task": jevcache.TASK_LINES}
    if found:
        state["found"] = found
    out = []
    for ks in jevcache.requests({k: None for k in texts}, texts):
        body = {"model": MODEL, "state": state, "questions": {f"c{j}": Noul(texts[k]).wire() for j, k in enumerate(ks)}}
        _, stream = encode_json(body)
        out.append(b"".join(stream).decode())
    return out


def page(name, question, docs, clues, post, found=None):
    graph = {"post": {t: [None] * n for t, n in post.items()}}
    texts = {c["key"]: describe.lines(C(c), c["targets"], docs, graph) for c in clues}
    return {"name": name, "question": question, "found": found, "docs": docs, "clues": clues, "post": post,
            "texts": texts, "bodies": bodies(question, texts, found)}


def synthetic():
    r = random.Random(837)
    words = ["invoice", "rounding", "cent", "ledger", "état", "naïve", "東京", "say \"hi\"", "back\\slash", "tab\there",
             "line\nbreak", "sep\x1cchar", "ctl\x01x", "nbsp gap", "emoji 🎉", "€uro"]
    docs = {}
    for i in range(300):
        d = f"d{i:03d}"
        said = " ".join(r.choice(words) for _ in range(r.randint(5, 80)))
        x = {"uri": d, "title": f"Doc {i}", "said": said if i % 17 else None,
             "sitting": (f"s{i // 20}" if i % 3 else None), "position": (i % 20 if i % 5 else None),
             "said_at": (f"2026-0{1 + i % 9}-{10 + i % 18:02d}T{i % 24:02d}:00:00" if i % 4 else None)}
        docs[d] = x
    clues, post = [], {}
    names = ["Rounding", "rounding-rule", "round up", "état", "ADR 007", "a.b", "Cent", "cents", "ledger", "z"]
    for j in range(150):
        kind = ["term", "next", "near"][j % 3]
        src = f"d{r.randrange(300):03d}"
        targets = sorted({f"d{r.randrange(300):03d}" for _ in range(r.randint(1, 12))} | ({"ghost-doc"} if j == 7 else set()))
        if kind == "term":
            x = f"{names[j % len(names)]} {j}"
            post[x] = len(targets) + r.randint(0, 40)
            clues.append({"key": f"term:{x}", "kind": "term", "x": x, "source": src, "targets": targets})
        else:
            clues.append({"key": f"{kind}:{src}#{j}", "kind": kind, "x": src, "source": src, "targets": targets})
    return page("synthetic", "Why is the invoice a cent off, and what did ADR-007 say about \"rounding\"?", docs, clues,
                post)


def real(saved, page_id, fixture):
    row = next(json.loads(l) for l in open(saved) if json.loads(l)["qid"] == page_id.split("|")[0])
    pg = next(p for p in row["pages"] if p["page"] == page_id)
    conv = page_id.split(":")[1]
    g = next(json.loads(l) for l in open(f"{fixture}/graphs.jsonl") if json.loads(l)["conv"] == conv)["graph"]
    clues = []
    for d in pg["doors"]:
        kind, x = d["key"].split(":", 1)
        clues.append({"key": d["key"], "kind": kind, "x": x, "source": "" if kind == "term" else x,
                      "targets": d["targets"]})
    shown = set()
    for c in clues:
        shown |= set(sorted(c["targets"], key=lambda t: hashlib.md5(f"{c['key']}:{t}".encode()).hexdigest())[:3])
    docs = {}
    for l in open(f"{fixture}/docs.jsonl"):
        x = json.loads(l)
        if x["uri"] in shown:
            x["said"] = (x["said"] or "")[:400]
            docs[x["uri"]] = x
    post = {c["x"]: len(g["post"].get(c["x"], [])) for c in clues if c["kind"] == "term"}
    p = page(page_id, pg["question"], docs, clues, post)
    sent = {d["key"]: d["text"] for d in pg["doors"]}
    assert p["texts"] == sent, "the door texts differ from the texts the saved run sent"
    return p


def kappas():
    """kappa_state.relations (round 3's K6, round 4's K7) on reads with tricky sentence ends, door and search reads,
    and enough text to hit both caps."""
    r = random.Random(46)
    ends = ["It ended.", "Really?! Yes.", "No end here", "Dr. Who met Mr. X. Then left.", "v1.2 shipped.\nNext",
            "Wow!", "a.b?c", "trailing sep.\x1c more", "  padded.  ", "é" * 250 + ".", "Q? A."]
    out = []
    for n in (0, 3, 40, 400):
        texts = [" ".join(r.choice(ends) for _ in range(r.randint(1, 4))) for _ in range(n)]
        via = [r.choice([None, "search", "search:bm25", "term:rounding", "near:d001", ""]) for _ in range(n)]
        for recent_last, door_first in ((True, True), (False, True), (True, False)):
            out.append({"texts": texts, "via": via, "recent_last": recent_last, "door_first": door_first,
                        "found": relations(texts, via, recent_last=recent_last, door_first=door_first)})
    return out


def cuts():
    """jevcache.requests on texts of chosen lengths: cumulative bytes landing one short of, on, and one past 24,000,
    with the 60-option cut, and keys whose collation differs from byte order."""
    out = []
    for total in (23999, 24000, 24001):
        texts = {f"k{i:03d}": "x" * (480 - 4 - 64) for i in range(49)}
        texts["k049"] = "y" * (total - 49 * 480 - 4 - 64)
        texts.update({f"k{i:03d}": "z" * 10 for i in range(50, 130)})
        out.append({"texts": texts, "requests": jevcache.requests({k: None for k in texts}, texts)})
    r = random.Random(1172)
    keys = ["term:a b", "term:A-c", "term:ab", "near:mq:00ff", "term:Ab", "next:x", "term:é", "term:a.b.c", "term:Z"]
    for n in (5, 61, 200):
        texts = {f"{r.choice(keys)}{i}": "w" * r.randint(0, 2000) for i in range(n)}
        out.append({"texts": texts, "requests": jevcache.requests({k: None for k in texts}, texts)})
    return out


if __name__ == "__main__":
    pages = [synthetic()]
    pages.append(page("found", "Who signed it?", pages[0]["docs"], pages[0]["clues"][:5], pages[0]["post"],
                      found=["a memory line", "another \"one\""]))
    if len(sys.argv) > 2:
        pages.append(real(sys.argv[2], sys.argv[3], sys.argv[4]))
    if len(sys.argv) > 5:
        cache = jevcache.Cache(__import__("pathlib").Path(sys.argv[5]))
        rec = []
        for b in pages[-1]["bodies"]:
            v = json.loads(b)
            texts = [q["instructions"] for q in v["questions"].values()]
            k = hashlib.sha256(json.dumps({"model": v["model"], "state": v["state"], "options": texts},
                                          sort_keys=True).encode()).hexdigest() + ":0"
            rec.append(cache.d[k])
        pages[-1]["recorded"] = rec
    k = kappas()
    # round 3's request shape: the same doors, with K6 of a walk's reads as `found` beside the question and task
    pages.append(page("round3", pages[0]["question"], pages[0]["docs"], pages[0]["clues"][:70], pages[0]["post"],
                      found=k[-3]["found"]))
    out = {"model": MODEL, "task": jevcache.TASK_LINES, "pages": pages, "cuts": cuts(), "kappa": k}
    with open("tests/fixtures/jev-requests.json", "w") as f:
        json.dump(out, f, ensure_ascii=False, indent=0)
    for p in pages:
        print(p["name"], len(p["clues"]), "doors,", len(p["bodies"]), "requests,", sum(map(len, p["bodies"])), "bytes")
