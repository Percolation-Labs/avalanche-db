"""The $0 gates of REGISTERED.md from the probe's rows (probe/): G0, the door signal, and G1, the oracle ceiling,
plus every arm no model decides, scored as registered.

    python3 score0.py NAME PROBE.jsonl [NAME PROBE.jsonl ...]

G0's AUC is p8-subsystems meta/lab/worlds/door_signal.py's, copied: per question, every gold door against every other
door, pairs pooled, ties half; overlap is the count of question words in the door's text (D6, whole).
"""
import json
import random
import re
import sys

TOK = re.compile(r"[a-z0-9]+")
STOP = set("the a an of in on to and is was which what who that by for with from at as its it his her their this be "
           "are were has had did does do when where how".split())
ARMS = ["search", "oracle", "width", "coin", "search-order"]


def toks(s):
    return set(TOK.findall(s.lower())) - STOP


def auc(groups):
    win = tot = 0
    for g in groups:
        pos = [s for s, y in g if y]
        neg = [s for s, y in g if not y]
        for a in pos:
            for b in neg:
                tot += 1
                win += 1 if a > b else .5 if a == b else 0
    return win / tot if tot else float("nan")


def recall(docs, gold, k):
    return len(set(docs[:k]) & set(gold)) / len(gold) if gold else 0.0


def paired(a, b, n=10000, seed=1118):
    d = [x - y for x, y in zip(a, b)]
    r = random.Random(seed)
    means = sorted(sum(r.choice(d) for _ in d) / len(d) for _ in range(n))
    return sum(d) / len(d), means[int(.025 * n)], means[int(.975 * n) - 1]


def main(name, path, questions):
    rows = [json.loads(l) for l in open(path)]
    qtext = {q["qid"]: q["question"] for q in questions}
    print(f"\n== {name}: {len(rows)} questions")
    # G0
    rounds = []
    for r in rows:
        ds = [(d["width"], d["text"], d["gold"] > 0) for d in r["doors"].values()]
        if any(y for *_, y in ds) and not all(y for *_, y in ds):
            rounds.append((qtext[r["qid"]], ds))
    w = [[(wd, y) for wd, _, y in ds] for _, ds in rounds]
    o = [[(len(toks(q) & toks(t)), y) for _, t, y in ds] for q, ds in rounds]
    doors = sum(len(r["doors"]) for r in rows)
    print(f"G0  questions with a gold door and another: {len(rounds)}/{len(rows)}; doors per question {doors / len(rows):.0f}")
    print(f"    AUC width {auc(w):.3f}   AUC question-door overlap {auc(o):.3f}   (A requires overlap >= .55)")
    # recall at k for every arm
    arm = {a: [(r["search"] if a == "search" else r["walks"][a]) for r in rows] for a in ARMS}
    gold = [r["gold"] for r in rows]
    for k in (5, 10, 20):
        cells = "  ".join(f"{a} {sum(recall(d, g, k) for d, g in zip(arm[a], gold)) / len(rows):.3f}" for a in ARMS)
        print(f"recall@{k:<2d} {cells}")
    full = "  ".join(f"{a} {sum(set(g) <= set(d[:10]) for d, g in zip(arm[a], gold)) / len(rows):.3f}" for a in ARMS)
    print(f"full support @10  {full}")
    r10 = {a: [recall(d, g, 10) for d, g in zip(arm[a], gold)] for a in ARMS}
    for a in ("oracle", "width", "coin", "search-order"):
        m, lo, hi = paired(r10[a], r10["search"])
        print(f"    {a:13s} - search  recall@10  {m:+.3f} [{lo:+.3f}, {hi:+.3f}]")
    m = paired(r10["oracle"], r10["search"])[0]
    print(f"G1  oracle - search recall@10 {m:+.3f}: {'PASS' if m >= .10 else 'FAIL'} (>= .10)")


if __name__ == "__main__":
    a = sys.argv[1:]
    for name, path in zip(a[::2], a[1::2]):
        qfile = "musique-questions.jsonl" if "mq" in path or "musique" in name.lower() else "cards.jsonl"
        here = __file__.rsplit("/", 1)[0]
        main(name, path, [json.loads(l) for l in open(f"{here}/{qfile}")])
