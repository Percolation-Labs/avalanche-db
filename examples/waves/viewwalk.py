"""viewwalk.py -- a set walk steered by choices, not by written queries.

setwalk.py lets a generative model write each step's SQL. Here no step is written. The schema's
own grammar produces the candidate sets ("views"), and a decider only chooses among them. A view
is a set of keys described by one production:

  rare value   rows whose <column> is a value under 1% of all rows (kind = 'refund', merchant
               QuickWire Ltd), per key
  rare hours   rows in hours of the day that each hold under 1% of all rows, per key
  anchor       rows whose <column> is a value the question names (likeness, then connection)
  outlier      keys whose per-key aggregate (largest |amount|, row count, most rows on one day,
               most repeats of one merchant and amount) sits k robust deviations above the median

Every view is counted before it is read. Over the walker's capacity it raises a semantic
exception, and the only move on it is to tighten it (an outlier view raises k). The menu at each
step is every view not yet taken, with its count, plus "stop", so the walk always knows what it
has not looked at.

Two deciders, neither of which writes anything:
  symbolic  spends no tokens: takes the most selective non-empty view within capacity, adds its
            keys, tightens an over-capacity view when nothing else is left, and stops when the
            menu holds nothing it can read
  jev       a decision model: one Choice picks the next view or stop, and one request of Nouls
            judges every key a view returns before it enters the result set

    python3 viewwalk.py questions/<q>.json [--decider symbolic|jev] [--capacity 20] [--steps 12] [--patience 2]

--patience p stops the walk after p views in a row that add no new key (0 turns it off).

The result set is the keys returned to the caller, each with why; kappa (what the decider reads to
choose) is the question, the result set and the views taken so far.
"""
import hashlib, json, math, os, sqlite3, statistics, sys, urllib.request
from collections import Counter, defaultdict

HERE = os.path.dirname(os.path.abspath(__file__))
STATE = os.path.join(HERE, ".waves")
os.makedirs(STATE, exist_ok=True)
RARE = 0.01
KS = [3, 5, 8, 13, 21, 34]


def fk_path(db, src, dst):
    """The foreign-key path from table src to table dst, as (table, column, ref_table, ref_column)."""
    edges = defaultdict(list)
    for (t,) in db.execute("select name from sqlite_master where type='table'"):
        for f in db.execute(f"pragma foreign_key_list({t})"):
            edges[t].append((t, f[3], f[2], f[4]))
    frontier, seen = [(src, [])], {src}
    while frontier:
        t, path = frontier.pop(0)
        if t == dst:
            return path
        for e in edges[t]:
            if e[2] not in seen:
                seen.add(e[2])
                frontier.append((e[2], path + [e]))
    return None


def load(db, key_table):
    """Every row of the largest table, with the key it belongs to and the columns of the tables it
    references (merchant name and category), so a production can range over all of them."""
    tables = [t for (t,) in db.execute("select name from sqlite_master where type='table'")]
    fact = max(tables, key=lambda t: db.execute(f"select count(*) from {t}").fetchone()[0])
    path = fk_path(db, fact, key_table)
    sql = f"select {fact}.*, {path[-1][0]}.{path[-1][1]} as _key"
    joins = ""
    for t, c, rt, rc in path[:-1]:
        joins += f" join {rt} on {t}.{c} = {rt}.{rc}"
    looked = {p[2] for p in path}
    for f in db.execute(f"pragma foreign_key_list({fact})"):
        if f[2] not in looked:  # a referenced table off the key path: bring its descriptive columns
            for c in db.execute(f"pragma table_info({f[2]})"):
                if c[1] != f[4]:
                    sql += f", {f[2]}.{c[1]} as \"{f[2]}.{c[1]}\""
            joins += f" left join {f[2]} on {fact}.{f[3]} = {f[2]}.{f[4]}"
    db.row_factory = sqlite3.Row
    rows = [dict(r) for r in db.execute(sql + f" from {fact}" + joins)]
    return fact, rows


def views(rows, question=""):
    """The grammar's productions over these rows: name -> (description, per-key value, kind)."""
    n = len(rows)
    out = {}
    cols = [c for c in rows[0] if c not in ("_key", "id") and not c.endswith("_id")]
    q = question.lower()
    for c in cols:  # likeness first: a value the question names is an anchor
        if isinstance(rows[0][c], str):
            for v in {r[c] for r in rows if r[c]}:
                if len(v) > 3 and v.lower() in q:
                    per = Counter(r["_key"] for r in rows if r[c] == v)
                    out[f"anchor {c} = {v!r}"] = (f"rows whose {c} is {v!r}, named in the question", per, "anchor")
    rare_rows = defaultdict(int)  # per key: rows that are rare on any column or hour
    rare_ids = set()
    for c in cols:
        vals = Counter(r[c] for r in rows)
        if isinstance(rows[0][c], (int, float)) or len(vals) > 60:
            continue
        rare = {v for v, m in vals.items() if v not in (None, "") and m / n < RARE}
        if not rare:
            continue
        hit = [r for r in rows if r[c] in rare]
        rare_ids |= {r["id"] for r in hit}
        per = Counter(r["_key"] for r in hit)
        shown = ", ".join(repr(v) for v in sorted(rare, key=str)[:4]) + (" ..." if len(rare) > 4 else "")
        out[f"rare {c}"] = (f"rows whose {c} is one of {len(rare)} values each under 1% of rows ({shown}; {len(hit)} rows)", per, "rare")
    times = [c for c in cols if isinstance(rows[0][c], str) and len(rows[0][c]) >= 13 and rows[0][c][10] in " T"]
    for c in times:
        hours = Counter(r[c][11:13] for r in rows)
        rare = {h for h, m in hours.items() if m / n < RARE}
        if rare:
            per = Counter(r["_key"] for r in rows if r[c][11:13] in rare)
            out[f"rare hours of {c}"] = (f"rows at hours {', '.join(sorted(rare))}, each under 1% of rows", per, "rare")
            rare_ids |= {r["id"] for r in rows if r[c][11:13] in rare}
        day = Counter((r["_key"], r[c][:10]) for r in rows)
        burst = defaultdict(int)
        for (k, _), m in day.items():
            burst[k] = max(burst[k], m)
        out[f"most rows on one day by {c}"] = ("the most rows a key has on one day", burst, "outlier")
    nums = [c for c in cols if isinstance(rows[0][c], float)]
    for c in nums:
        big = defaultdict(float)
        for r in rows:
            big[r["_key"]] = max(big[r["_key"]], abs(r[c] or 0))
        out[f"largest |{c}|"] = (f"a key's largest |{c}|", big, "outlier")
        rep = Counter((r["_key"], r.get("merchants.name"), r[c]) for r in rows)
        most = defaultdict(int)
        for (k, _, _), m in rep.items():
            most[k] = max(most[k], m)
        out[f"repeats of one {c}"] = (f"the most rows a key has with one merchant and one exact {c}", most, "outlier")
    for r in rows:
        if r["id"] in rare_ids:
            rare_rows[r["_key"]] += 1
    for r in rows:
        rare_rows.setdefault(r["_key"], 0)
    out["rare rows per key"] = ("how many of a key's rows are rare on some column or hour", rare_rows, "outlier")
    out["row count"] = ("a key's number of rows", Counter(r["_key"] for r in rows), "outlier")
    return out


def members(view, k):
    """The keys a view holds at tightness k, with each key's value."""
    desc, per, kind = view
    if kind in ("rare", "anchor"):
        return {key: v for key, v in per.items() if v}
    vals = list(per.values())
    med = statistics.median(vals)
    scale = 1.4826 * statistics.median(abs(v - med) for v in vals)
    if not scale:  # most keys share one value (a count of 0): the spread is the standard deviation
        scale = statistics.pstdev(vals) or 1e-9
    return {key: v for key, v in per.items() if (v - med) / scale > k}


def evidence(rows, key, limit=6):
    """What a person would read about one key: its unusual rows first, then how its month looks."""
    mine = [r for r in rows if r["_key"] == key]
    amounts = [abs(r["amount"]) for r in mine if r.get("amount") is not None]
    lines = [f"{len(mine)} rows this month, median |amount| {statistics.median(amounts):.2f}" if amounts else f"{len(mine)} rows"]
    kinds = Counter(r.get("kind") for r in mine)
    lines.append("kinds: " + ", ".join(f"{k} {m}" for k, m in kinds.most_common()))
    return lines


# ------------------------------------------------------------------ deciders

def symbolic_choose(menu, result, taken):
    anchors = [(m["count"], name) for name, m in menu.items() if name.startswith("anchor") and 0 < m["count"] <= m["capacity"]]
    if anchors:
        return min(anchors)[1], "a value the question names"
    if any(t.startswith("anchor") for t in taken):
        return "stop", "the anchors are read; nothing else in the grammar is tied to the question"
    readable = [(m["count"], name) for name, m in menu.items() if 0 < m["count"] <= m["capacity"]]
    if readable:
        return min(readable)[1], "the most selective view not yet read"
    over = [(m["count"], name) for name, m in menu.items() if m["count"] > m["capacity"] and m["can_tighten"]]
    if over:
        return min(over)[1], "nothing readable is left; tighten the smallest view over capacity"
    return "stop", "every view is read, empty, or over capacity at its tightest"


def symbolic_keep(question, view_name, keys, rows):
    return {k: True for k in keys}


JEV_ENDPOINT = "https://api.typesafe.ai/v1/systemone"
JEV_MODEL = "jev-1.13.0"


def jev(state, questions):
    body = {"model": JEV_MODEL, "state": state, "questions": questions}
    key = hashlib.sha256(json.dumps(body, sort_keys=True).encode()).hexdigest()
    log = os.path.join(STATE, "jev.jsonl")
    if os.path.exists(log):
        for line in open(log):
            d = json.loads(line)
            if d["key"] == key:
                return d["answers"], True
    req = urllib.request.Request(JEV_ENDPOINT, data=json.dumps(body).encode(), method="POST", headers={
        "Authorization": f"Bearer {os.environ['JEV_API_KEY']}", "Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=120) as resp:
        data = json.load(resp)
    with open(log, "a") as f:
        f.write(json.dumps({"key": key, "answers": data["answers"], "usage": data.get("usage")}) + "\n")
    return data["answers"], False


def slug(name):
    return "".join(ch if ch.isalnum() else "_" for ch in name.lower()).strip("_")[:60]


def jev_choose(question, menu, result, taken):
    opts, back = {}, {}
    for name, m in menu.items():
        if m["count"] == 0:
            continue
        s = slug(name) if m["count"] <= m["capacity"] else "tighten_" + slug(name)
        what = (f"read the {m['count']} keys in: {m['desc']}" if m["count"] <= m["capacity"] else
                f"{m['desc']}: {m['count']} keys, over capacity; tighten it before it can be read")
        opts[s], back[s] = what, name
    opts["stop_the_result_set_answers_the_question"] = "every remaining view is unrelated to the question, or repeats what is already found"
    back["stop_the_result_set_answers_the_question"] = "stop"
    state = {"question": question, "result_set": result, "views_read": taken}
    ans, _ = jev(state, {"next": {"type": "choice", "instructions":
                 "Which view should the walk read next to answer `question`, given `result_set` and `views_read`?",
                 "criteria": opts}})
    a = ans["next"]
    return back[a["choice"]], f"Jev chose {a['choice']} (p={a.get('probabilities', {}).get(a['choice'], 0):.2f})"


def jev_keep(question, view_name, keys, rows):
    qs = {}
    state = {"question": question, "view": view_name, "keys": {}}
    for k, v in keys.items():
        mine = [r for r in rows if r["_key"] == k]
        state["keys"][k] = {"value_in_view": v, "month": evidence(rows, k),
                            "rows": [{c: r[c] for c in r if c not in ("id", "_key") and not c.endswith("_id")}
                                     for r in sorted(mine, key=lambda r: -abs(r.get("amount") or 0))[:6]]}
        qs[k] = {"type": "noul", "instructions": f"Does `keys.{k}` show activity that answers `question`, "
                 f"rather than activity its own rows explain?",
                 "criteria": {"true": "it belongs in the answer", "false": "it is ordinary or explained"}}
    ans, _ = jev(state, qs)
    return {k: float(ans[k]["noul"]) >= 0.5 for k in keys}


# ------------------------------------------------------------------ the walk

def walk(qfile, decider="symbolic", capacity=20, steps=12, patience=2):
    plan = json.load(open(qfile))
    db = sqlite3.connect(os.path.join(HERE, plan["set_data"]))
    fact, rows = load(db, plan.get("key_table", "customers"))
    grammar = views(rows, plan["question"])
    tight = {name: 0 for name in grammar}
    taken, result, rows_read, idle = [], {}, 0, 0
    choose, keep = (symbolic_choose, symbolic_keep) if decider == "symbolic" else (jev_choose, jev_keep)
    print(f"question: {plan['question']}\n{len(grammar)} views from the schema of {fact}; capacity {capacity}; decider {decider}")
    for n in range(1, steps + 1):
        menu = {}
        for name, v in grammar.items():
            if name in taken:
                continue
            mem = members(v, KS[tight[name]])
            menu[name] = {"desc": v[0] + (f", k={KS[tight[name]]}" if v[2] == "outlier" else ""), "count": len(mem),
                          "capacity": capacity, "can_tighten": v[2] == "outlier" and tight[name] < len(KS) - 1}
        pick, why = choose(plan["question"], menu, {k: w for k, w in result.items()}, taken) if decider != "symbolic" \
            else choose(menu, result, taken)
        if pick == "stop":
            print(f"step {n}: stop  ({why})")
            break
        m = menu[pick]
        if m["count"] > capacity:
            if m["can_tighten"]:
                tight[pick] += 1
            else:
                taken.append(pick)
            print(f"step {n}: {pick}: {m['count']} keys, semantic exception; tightened  ({why})")
            continue
        mem = members(grammar[pick], KS[tight[pick]])
        rows_read += len(mem)
        kept = keep(plan["question"], pick, mem, rows)
        new = [k for k, yes in kept.items() if yes and k not in result]
        for k in new:
            result[k] = f"{pick} ({mem[k]:g})"
        idle = 0 if new else idle + 1
        taken.append(pick)
        print(f"step {n}: {pick}: {len(mem)} keys read, kept {', '.join(sorted(k for k, y in kept.items() if y)) or 'none'}"
              f"{'' if new else ', nothing new'}  ({why})")
        if patience and idle >= patience:
            print(f"stop: {patience} views in a row added no new key")
            break
    else:
        print(f"budget of {steps} steps spent")
    left = [name for name in grammar if name not in taken]
    ids, gold = sorted(result), set(plan["gold"])
    hit = len(gold & set(ids))
    print(f"result set: {', '.join(ids) or '(empty)'}")
    print(f"against the planted answer {sorted(gold)}: recall {hit / len(gold):.2f}, precision {hit / max(1, len(ids)):.2f}; "
          f"{rows_read} keys read; views not read: {len(left)}")


if __name__ == "__main__":
    a = sys.argv
    walk(a[1], a[a.index("--decider") + 1] if "--decider" in a else "symbolic",
         int(a[a.index("--capacity") + 1]) if "--capacity" in a else 20,
         int(a[a.index("--steps") + 1]) if "--steps" in a else 12,
         int(a[a.index("--patience") + 1]) if "--patience" in a else 2)
