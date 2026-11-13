"""derive.py -- a question answered as a derivation, each production one small choice.

Where viewwalk.py searches views for a question that names nothing, this takes a question that
names things and builds its plan from four productions, in the order the draft's grammar gives them:

  anchor      the rows holding every value the question names (likeness first)
  time        the question names a date: keep rows on or after it, on it, before it, or ignore it
  hop         from the anchor rows' keys: stay on the anchor rows, go to the keys' other rows, or
              to their other rows on the same day as the anchor row
  project     the answer column, the one whose name is most like the question's answer hint;
              a value the question names is never returned as its own answer

Each derivation runs with no tokens, so the whole decision space is printed: every plan the
grammar allows and the set it returns. A decider then makes the choices the grammar cannot: one
Choice per production with more than one reading (`--decider jev`, untested while Jev is 402).

    python3 derive.py questions/<q>.json [--decider jev|standin]
"""
import json, os, re, sqlite3, sys
from itertools import product
from viewwalk import HERE, jev, load

MONTHS = "january february march april may june july august september october november december".split()


def anchors(rows, question):
    q = question.lower()
    named = {}
    for c in rows[0]:
        if c in ("_key", "id") or c.endswith("_id") or not isinstance(rows[0][c], str):
            continue
        for v in {r[c] for r in rows if r[c]}:
            if len(v) > 3 and v.lower() in q:
                named[c] = v
    return named


def named_date(question):
    m = re.search(r"(\d{1,2}) (" + "|".join(MONTHS) + r") (\d{4})", question.lower())
    return f"{m.group(3)}-{MONTHS.index(m.group(2)) + 1:02d}-{int(m.group(1)):02d}" if m else None


def stem(w):
    return w.lower().rstrip("s")


def answer_column(rows, hint, key_table):
    words = {stem(w) for w in re.findall(r"[a-z]+", hint.lower())}
    cols = {c: c for c in rows[0] if c not in ("_key", "id") and not c.endswith("_id")}
    cols["_key"] = f"{key_table}.id"
    score = {c: len(words & {stem(w) for w in re.findall(r"[a-z]+", name)}) for c, name in cols.items()}
    return max(score, key=score.get)


def run(rows, named, date, time_rule, hop, col):
    tcol = "at"
    R = [r for r in rows if all(r[c] == v for c, v in named.items())]
    if date and time_rule != "ignore":
        R = [r for r in R if {"on or after": r[tcol][:10] >= date, "on": r[tcol][:10] == date,
                              "before": r[tcol][:10] < date}[time_rule]]
    if hop == "stay":
        out = R
    else:
        days = {(r["_key"], r[tcol][:10]) for r in R}
        keys = {k for k, _ in days}
        ids = {r["id"] for r in R}
        out = [r for r in rows if r["_key"] in keys and r["id"] not in ids and
               (hop == "other rows" or (r["_key"], r[tcol][:10]) in days)]
    vals = {r[col] for r in out} - set(named.values())
    return sorted(v for v in vals if v)


TIME = {"ignore": "the date does not limit which rows count",
        "on or after": "only rows on or after the named date count",
        "on": "only rows on the named date itself count",
        "before": "only rows before the named date count"}
HOP = {"stay": "the answer is read from the anchor rows themselves",
       "other rows": "the answer is read from the same keys' other rows, at any time",
       "other rows the same day": "the answer is read from the same keys' other rows on the same day as their anchor row"}


def jev_choose(question, named, date):
    """One request: a Choice for each production with more than one reading. Option keys are
    named for what they mean, since Jev reads the key (decide.py, 30 Sept)."""
    key = lambda s: s.replace(" ", "_")
    qs = {"time": {"type": "choice", "instructions": f"How does `question` use the date {date}?",
                   "criteria": {key(k): v for k, v in TIME.items()}},
          "hop": {"type": "choice", "instructions": "Which rows does `question` ask about, given the anchor rows "
                  f"(those with {named})?", "criteria": {key(k): v for k, v in HOP.items()}}}
    ans, _ = jev({"question": question}, qs)
    back = lambda a: a["choice"].replace("_", " ")
    return back(ans["time"]), back(ans["hop"])


def standin_choose(question, named, date):
    """The Jev stand-in (standin.py): each production's Choice as one Noul per option, best wins."""
    from standin import choice
    inst = "Judge whether the document states how the query means its words."
    t, ts = choice(question, inst, {k: f"In this question, {v} ({date})." for k, v in TIME.items()})
    h, hs = choice(question, inst, {k: f"In this question, {v}." for k, v in HOP.items()})
    fmt = lambda d: ", ".join(f"{k} {p:.2f}" for k, p in sorted(d.items(), key=lambda x: -x[1]))
    print(f"stand-in, time: {fmt(ts)}\nstand-in, hop: {fmt(hs)}")
    return t, h


def main(qfile, decider=None):
    plan = json.load(open(qfile))
    db = sqlite3.connect(os.path.join(HERE, plan["set_data"]))
    fact, rows = load(db, plan.get("key_table", "customers"))
    named, date = anchors(rows, plan["question"]), named_date(plan["question"])
    col = answer_column(rows, plan["answer_hint"], plan.get("key_table", "customers"))
    print(f"question: {plan['question']}")
    print(f"anchor: {named}; date named: {date}; answer column: {col}")
    gold = set(plan["gold"])
    times = ["ignore", "on or after", "on", "before"] if date else ["ignore"]
    hops = ["stay", "other rows", "other rows the same day"]
    print(f"{len(times) * len(hops)} derivations:")
    for t, h in product(times, hops):
        got = run(rows, named, date, t, h, col)
        hit = len(gold & set(got))
        mark = "  <- the planted answer" if set(got) == gold else ""
        shown = ", ".join(got[:6]) + (f" and {len(got) - 6} more" if len(got) > 6 else "")
        print(f"  time {t:12} hop {h:24} -> {len(got):3} ({shown or 'empty'}); recall {hit / len(gold):.2f}{mark}")
    if decider in ("jev", "standin"):
        pick = jev_choose if decider == "jev" else standin_choose
        t, h = pick(plan["question"], named, date) if date else ("ignore", "stay")
        got = run(rows, named, date, t, h, col)
        hit = len(gold & set(got))
        print(f"{decider} chose time {t!r}, hop {h!r} -> {', '.join(got) or 'empty'}; "
              f"recall {hit / len(gold):.2f}, precision {hit / max(1, len(got)):.2f}")


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[sys.argv.index("--decider") + 1] if "--decider" in sys.argv else None)
