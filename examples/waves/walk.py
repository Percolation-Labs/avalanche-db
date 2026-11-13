"""walk.py -- familiar queries as durable walks, with a decider inside them.

A walk starts from a question and a start: a SQL select over one table, or a node lookup in a
property graph. That gives the first wave. Each hop is the familiar join, along a foreign key or a
relationship type, from the wave to its neighbours. Between hops, a decision model reads the
question, the path so far and the wave's rows, and keeps only the rows that bear on the question.
The next join runs from what it kept. With --no-decider every row goes forward, which is the
declarative query written one join at a time.

    python3 walk.py run   questions/<q>.json [--no-decider]   # the whole walk
    python3 walk.py start questions/<q>.json                  # the first wave; prints a token
    python3 walk.py step  <token>                             # one more hop, from the token

A token is a file under .waves/ holding the question, the plan, the current wave, every choice
made and the data's fingerprint at the start. A step from a token reads the data as it was: if
the data has changed since, the walk says so and goes on reading the original copy. The
decider's answers are recorded in .waves/decisions.jsonl, keyed by the exact prompt, so a rerun
replays them and calls nothing.
"""
import hashlib, json, os, re, shutil, sqlite3, subprocess, sys, time

HERE = os.path.dirname(os.path.abspath(__file__))
STATE = os.path.join(HERE, ".waves")
os.makedirs(STATE, exist_ok=True)
SHOWN = 60  # rows a decider is shown in one call; a wider wave is cut at this many, and says so


# --- the data -----------------------------------------------------------------------------

def fingerprint(path):
    return hashlib.sha256(open(path, "rb").read()).hexdigest()[:12]


class Relational:
    """SQLite: tables are node kinds, foreign keys are edges, rows are nodes."""

    def __init__(self, path):
        self.db = sqlite3.connect(path)
        self.db.row_factory = sqlite3.Row

    def start(self, start):
        return [dict(r) for r in self.db.execute(start["sql"])]

    def hop(self, wave, hop):
        # hop: {"sql": a query with {ids}, which the wave's ids fill}: any join or aggregate, or
        #      {"to": table, "fk": column on `to` naming the wave's id} (one to many), or
        #      {"to": table, "via": column on the wave's rows naming `to`'s id} (many to one)
        if "sql" in hop:
            ids = sorted({r["id"] for r in wave})
            return [dict(r) for r in self.db.execute(hop["sql"].replace("{ids}", ",".join("?" * len(ids))), ids)]
        if "fk" in hop:
            ids = sorted({r["id"] for r in wave})
            q = f"select * from {hop['to']} where {hop['fk']} in ({','.join('?' * len(ids))})"
            if hop.get("where"):
                q += f" and ({hop['where']})"
            rows = [dict(r) for r in self.db.execute(q, ids)]
            # with: {"table", "key", "fields"}: a lookup joined in for reading, the way an analyst
            # joins merchant names before reading transactions. A foreign key alone is an opaque id.
            for w in hop.get("with", []):
                look = {r["id"]: dict(r) for r in self.db.execute(f"select * from {w['table']}")}
                for r in rows:
                    other = look.get(r.get(w["key"]), {})
                    for f in w["fields"]:
                        r[f"{w['table']}.{f}"] = other.get(f)
            return rows
        ids = sorted({r[hop["via"]] for r in wave})
        return [dict(r) for r in self.db.execute(f"select * from {hop['to']} where id in ({','.join('?' * len(ids))})", ids)]

    def join_sql(self, plan):
        """The same walk as the single declarative query an analyst would write."""
        return plan.get("sql")


class Graph:
    """A property graph, Neo4j style: labelled nodes with properties, typed relationships."""

    def __init__(self, path):
        g = json.load(open(path))
        self.nodes = {n["id"]: n for n in g["nodes"]}
        self.edges = g["edges"]

    def row(self, nid, via=()):
        n = self.nodes[nid]
        # A row is one path: its id names the whole path, so two ways to one node stay apart.
        return {"id": ">".join([*via, nid]), "node": nid, "label": n["label"], **n["props"], "via": list(via)}

    def start(self, start):
        return [self.row(i) for i in start["ids"]]

    def hop(self, wave, hop):
        # hop: {"rel": TYPE, "dir": "out"|"in"|"both", "to": Label}
        out = []
        for r in wave:
            for e in self.edges:
                if e["type"] != hop["rel"]:
                    continue
                for a, b, d in ((e["from"], e["to"], "out"), (e["to"], e["from"], "in")):
                    if a == r["node"] and hop.get("dir", "out") in (d, "both") and self.nodes[b]["label"] == hop["to"] and b not in r["via"]:
                        out.append(self.row(b, [*r["via"], r["node"]]))
        return out


def open_data(plan):
    path = os.path.join(HERE, plan["data"])
    return (Relational if path.endswith(".db") else Graph)(path), path


# --- the decider ----------------------------------------------------------------------------

CLAUDE_BUDGET = int(os.environ.get("CLAUDE_BUDGET", "0") or 0)  # no batch run uses Claude (Sirsh, 13 Nov 2026)
_claude_calls = 0


def _claude_allowed():
    """Fresh claude -p calls refuse unless the run names a budget; recorded decisions still replay."""
    global _claude_calls
    if _claude_calls >= CLAUDE_BUDGET:
        sys.exit(f"refused: Claude as decider is capped at {CLAUDE_BUDGET} fresh calls (CLAUDE_BUDGET). No batch run "
                 "uses Claude; use viewwalk.py with Jev or the stand-in, or name a small budget for a hand-picked check.")
    _claude_calls += 1


def decide(question, path, rows, hop_note, group=None, limit=SHOWN):
    """Keep the rows that bear on the question, or with group, the groups (one account's
    transactions) that do. One call per chunk; recorded, and replayed by its exact prompt."""
    shown = rows[:limit]
    if group:
        what = f"groups of rows, one group per {group}"
        body = "\n\n".join(f"{group} {k}:\n" + "\n".join(json.dumps(r, default=str) for r in shown if r[group] == k)
                            for k in sorted({r[group] for r in shown}, key=str))
        unit, reply = "group", f'{{"keep": [the {group} of every group to keep], "why": "one sentence"}}'
    else:
        what, body = "rows", "\n".join(json.dumps(r, default=str) for r in shown)
        unit, reply = "row", '{"keep": [the id of every row to keep], "why": "one sentence"}'
    prompt = (
        f"You prune a query as it runs. A walk is answering a question one join at a time. Read the "
        f"question, the path so far and the {what} the last join returned, and keep only each {unit} "
        f"that could lead to or be part of the answer. Drop each {unit} that cannot.\n\n"
        f"Question: {question}\n\nPath so far:\n" + "\n".join(f"- {p}" for p in path) +
        f"\n\nThis wave: {hop_note}. ({len(shown)} rows shown of {len(rows)}):\n" + body +
        f"\n\nReply with JSON only: {reply}"
    )
    key = hashlib.sha256(prompt.encode()).hexdigest()
    log = os.path.join(STATE, "decisions.jsonl")
    if os.path.exists(log):
        for line in open(log):
            d = json.loads(line)
            if d["key"] == key:
                return d["keep"], d["why"], True
    _claude_allowed()
    out = subprocess.run(["claude", "-p", prompt, "--model", "sonnet", "--output-format", "stream-json", "--verbose",
                          "--tools", "", "--strict-mcp-config", "--no-session-persistence"],
                         capture_output=True, text=True, stdin=subprocess.DEVNULL)
    got = None
    for line in out.stdout.splitlines():
        try:
            ev = json.loads(line)
        except ValueError:
            continue
        if ev.get("type") != "assistant" or got:
            continue
        for part in ev["message"]["content"]:
            m = re.search(r"\{.*\}", part.get("text", ""), re.S)
            if m:
                try:
                    v = json.loads(m.group(0))
                except ValueError:
                    continue
                if "keep" in v:
                    got = v
                    break
    if not got:
        sys.exit(f"the decider gave no answer: {out.stderr[-400:]}")
    with open(log, "a") as f:
        f.write(json.dumps({"key": key, "keep": got["keep"], "why": got.get("why", "")}) + "\n")
    return got["keep"], got.get("why", ""), False


# --- the walk -------------------------------------------------------------------------------

def show(rows, n=8):
    for r in rows[:n]:
        print("      " + ", ".join(f"{k}={v}" for k, v in r.items()))
    if len(rows) > n:
        print(f"      … {len(rows) - n} more")


def save(state):
    path = os.path.join(STATE, state["token"] + ".json")
    json.dump(state, open(path, "w"), indent=1, default=str)
    return path


def begin(qfile, decider=True):
    plan = json.load(open(qfile))
    data, path = open_data(plan)
    token = f"{os.path.splitext(os.path.basename(qfile))[0]}-{int(time.time())}"
    # The token reads the data as it was: keep a copy of what this walk started on.
    copy = os.path.join(STATE, token + os.path.splitext(path)[1])
    shutil.copy(path, copy)
    wave = data.start(plan["start"])
    state = {"token": token, "question": plan["question"], "plan": plan, "decider": decider, "data": copy,
             "source": path, "fingerprint": fingerprint(path), "hop": 0, "wave": wave, "trail": [], "calls": 0}
    print(f"question: {plan['question']}")
    print(f"wave 0  likeness: {plan['start']['note']} → {len(wave)} rows")
    prune(state, plan["start"])
    return state


def chunks(rows, group, shown=SHOWN):
    """Waves of at most `shown` rows, never splitting a group (one account's transactions).
    A chunk is all the decider sees, so a judgement relative to the whole wave needs one chunk."""
    if not group:
        return [rows[i:i + shown] for i in range(0, len(rows), shown)] or [[]]
    out, cur, key = [], [], None
    for r in sorted(rows, key=lambda r: str(r[group])):
        if cur and len(cur) >= shown and r[group] != key:
            out.append(cur)
            cur = []
        cur.append(r)
        key = r[group]
    return out + [cur] if cur else out or [[]]


def prune(state, step_plan):
    note = step_plan["note"]
    if not state["decider"] or step_plan.get("decide") is False:
        why = "no decider" if not state["decider"] else "not judged here"
        state["trail"].append(f"{note}: {len(state['wave'])} rows, all kept ({why})")
        return
    before, kept, whys = len(state["wave"]), set(), []
    judge = step_plan.get("group") if step_plan.get("judge") == "group" else None
    shown = step_plan.get("shown", SHOWN)
    for part in chunks(state["wave"], step_plan.get("group"), shown):
        keep, why, replayed = decide(state["question"], state["trail"] or ["(start)"], part, note, judge, shown)
        state["calls"] += 0 if replayed else 1
        kept |= set(map(str, keep))
        whys.append(why)
    field = judge or "id"
    state["wave"] = [r for r in state["wave"] if str(r[field]) in kept]
    why = whys[0] if len(whys) == 1 else f"{len(whys)} calls; " + " / ".join(w for w in whys if w)[:300]
    state["trail"].append(f"{note}: {before} rows, decider kept {len(state['wave'])}: {why}")
    print(f"        decider kept {len(state['wave'])} of {before}: {why}")
    show(state["wave"])


def step(state):
    plan = state["plan"]
    if state["hop"] >= len(plan["hops"]):
        return False
    if fingerprint(state["source"]) != state["fingerprint"]:
        print("  note: the data has changed since this walk started; it goes on reading the data as it was")
    data, _ = open_data({**plan, "data": state["data"]})
    hop = plan["hops"][state["hop"]]
    state["wave"] = data.hop(state["wave"], hop)
    state["hop"] += 1
    print(f"wave {state['hop']}  connection: {hop['note']} → {len(state['wave'])} rows")
    prune(state, hop)
    return True


def answer(state):
    # The answer is a field of the last wave's rows, or (in a graph) a node on the path to them.
    via = state["plan"].get("answer_via")
    ids = sorted({str(r["via"][via] if via is not None else r[state["plan"].get("answer_field", "id")]) for r in state["wave"]})
    gold = set(state["plan"]["gold"])
    hit = len(gold & set(ids))
    print(f"answer: {', '.join(ids) or '(none)'}")
    print(f"against the planted answer {sorted(gold)}: recall {hit / len(gold):.2f}, precision {hit / max(1, len(ids)):.2f}; "
          f"{state['calls']} decider calls")
    return ids


if __name__ == "__main__":
    cmd, arg = sys.argv[1], sys.argv[2]
    if cmd == "run":
        st = begin(arg, decider="--no-decider" not in sys.argv)
        while step(st):
            pass
        answer(st)
        save(st)
    elif cmd == "start":
        st = begin(arg)
        print(f"token {st['token']}  ({save(st)})")
    elif cmd == "step":
        st = json.load(open(os.path.join(STATE, arg + ".json")))
        print(f"resuming {arg} at wave {st['hop']}; the way here:")
        for p in st["trail"]:
            print(f"    {p}")
        if step(st):
            save(st)
            print(f"token {st['token']}" if st["hop"] < len(st["plan"]["hops"]) else "")
        if st["hop"] >= len(st["plan"]["hops"]):
            answer(st)
