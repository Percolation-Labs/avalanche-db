"""setwalk.py -- a walk through sets, with semantic exceptions.

On a relational database the walk moves through sets, not rows. At each step the decider reads
the question, the schema (tables, columns, foreign keys and how many rows each table holds) and
every step so far, and writes one SQL query: a description of a set. The database counts it
first. A set over the walker's capacity raises a semantic exception: the decider gets the count
and never the rows, and refines. A set within capacity comes back whole, and the next step can
start from it. The walk ends when the decider answers. The aim is not a set that contains the
answer, which the whole table does, but the smallest set that still holds what the question needs.

Two things are kept apart (Sirsh, 13 Nov). The *result set* is the keys rated for return to the
caller: every step adds keys to it or removes them, explicitly, and the answer is that set, even
for keys the walker never looks at again. *Kappa* is the walker's short-term memory, the limited
information the decider uses to choose its next step: here, the schema and the steps so far.
Some of the result set may sit in kappa, but they are different stacks. With --no-result-set the
walk answers from kappa alone, as it did before.

    python3 setwalk.py questions/<q>.json [--capacity 100] [--steps 8]

The decider is claude -p (a stand-in for Jev). Every decision is recorded in
.waves/decisions.jsonl against its exact prompt, so a rerun replays and calls nothing.
"""
import hashlib, json, os, re, sqlite3, subprocess, sys

HERE = os.path.dirname(os.path.abspath(__file__))
STATE = os.path.join(HERE, ".waves")
os.makedirs(STATE, exist_ok=True)


def schema(db):
    out = []
    for (t,) in db.execute("select name from sqlite_master where type='table' order by name"):
        cols = [f"{c[1]} {c[2]}" for c in db.execute(f"pragma table_info({t})")]
        fks = [f"{f[3]} -> {f[2]}.{f[4]}" for f in db.execute(f"pragma foreign_key_list({t})")]
        n = db.execute(f"select count(*) from {t}").fetchone()[0]
        out.append(f"{t} ({n} rows): {', '.join(cols)}" + (f"; foreign keys {', '.join(fks)}" if fks else ""))
    return "\n".join(out)


def ask(prompt):
    key = hashlib.sha256(prompt.encode()).hexdigest()
    log = os.path.join(STATE, "decisions.jsonl")
    if os.path.exists(log):
        for line in open(log):
            d = json.loads(line)
            if d["key"] == key:
                return d["reply"], True
    out = subprocess.run(["claude", "-p", prompt, "--model", "sonnet", "--output-format", "stream-json", "--verbose",
                          "--tools", "", "--strict-mcp-config", "--no-session-persistence"],
                         capture_output=True, text=True, stdin=subprocess.DEVNULL)
    for line in out.stdout.splitlines():
        try:
            ev = json.loads(line)
        except ValueError:
            continue
        if ev.get("type") != "assistant":
            continue
        for part in ev["message"]["content"]:
            m = re.search(r"\{.*\}", part.get("text", ""), re.S)
            if m:
                try:
                    reply = json.loads(m.group(0))
                except ValueError:
                    continue
                if "sql" in reply or "answer" in reply or "stop" in reply:
                    with open(log, "a") as f:
                        f.write(json.dumps({"key": key, "reply": reply}) + "\n")
                    return reply, False
    sys.exit(f"the decider gave no answer: {out.stderr[-400:]}")


def walk(qfile, capacity=100, steps=8, result_set=True):
    plan = json.load(open(qfile))
    db = sqlite3.connect(os.path.join(HERE, plan["set_data"]))
    db.row_factory = sqlite3.Row
    sch = schema(db)
    history, calls, rows_read = [], 0, 0
    result = {}  # key -> why it is in the result set
    print(f"question: {plan['question']}\ncapacity: {capacity} rows; result set {'on' if result_set else 'off'}")
    for n in range(1, steps + 1):
        if result_set:
            ask_tail = (
                f"\n\nResult set (the {plan['answer_hint']} that will be returned to the caller, with why each is in it):\n" +
                ("\n".join(f"- {k}: {w}" for k, w in result.items()) if result else "(empty)") +
                "\n\nEvery reply may change the result set: add the keys your latest step established as part of "
                "the answer, and remove any it ruled out. Keys stay in it until you remove them, and the caller gets "
                "exactly this set. Reply with JSON only: {\"sql\": \"<one select>\", \"add\": {\"<key>\": \"why\"}, "
                "\"remove\": [\"<key>\"], \"why\": \"one sentence\"} to take a step, or {\"stop\": true, \"add\": {...}, "
                "\"remove\": [...], \"why\": \"one sentence\"} when the result set is complete."
            )
        else:
            ask_tail = ('\n\nReply with JSON only: {"sql": "<one select>", "why": "one sentence"} to take a step, or '
                        f'{{"answer": [{plan["answer_hint"]}], "why": "one sentence"}} to answer.')
        prompt = (
            "You answer a question about a SQLite database by walking through sets. Each step, write ONE SQL "
            "select describing a set that moves you toward the answer: a filter, a join, or an aggregate or "
            "ranking (a set of keys with a weight). The database first counts the set. If the count is over your "
            f"capacity of {capacity} rows, you get a semantic exception: the count and no rows, and you must "
            "refine the predicate. Otherwise you get the rows, and later steps can build on them. Aim for the "
            "smallest set that still holds what the question needs; a set that merely contains the answer is "
            "too big. When you know the answer, give it.\n\n"
            f"Question: {plan['question']}\n\nSchema:\n{sch}\n\nSteps so far:\n" +
            ("\n".join(history) if history else "(none)") + ask_tail
        )
        reply, replayed = ask(prompt)
        calls += 0 if replayed else 1
        if result_set:
            for k, w in (reply.get("add") or {}).items():
                result[str(k)] = w
            for k in reply.get("remove") or []:
                result.pop(str(k), None)
            if reply.get("add") or reply.get("remove"):
                print(f"  result set now: {', '.join(sorted(result)) or '(empty)'}")
        if "answer" in reply or reply.get("stop"):
            ids = sorted(result) if result_set else sorted(map(str, reply["answer"]))
            gold = set(plan["gold"])
            hit = len(gold & set(ids))
            print(f"answer after {n - 1} steps: {', '.join(ids)}  ({reply.get('why', '')})")
            print(f"against the planted answer {sorted(gold)}: recall {hit / len(gold):.2f}, precision {hit / max(1, len(ids)):.2f}; "
                  f"{rows_read} rows read; {calls} decider calls this run")
            return
        if not reply.get("sql"):
            history.append(f"{n}. (no query; the result set was updated)")
            continue
        sql = reply["sql"].strip().rstrip(";")
        try:
            count = db.execute(f"select count(*) from ({sql})").fetchone()[0]
        except sqlite3.Error as e:
            history.append(f"{n}. {sql}\n   error: {e}")
            print(f"step {n}: error {e}")
            continue
        if count > capacity:
            history.append(f"{n}. {sql}\n   semantic exception: {count} rows, over capacity {capacity}; not read")
            print(f"step {n}: {count} rows: semantic exception, not read  ({reply.get('why', '')})\n    {sql[:200]}")
            continue
        got = [dict(r) for r in db.execute(sql)]
        rows_read += len(got)
        history.append(f"{n}. {sql}\n   {count} rows:\n" + "\n".join("   " + json.dumps(r, default=str) for r in got))
        print(f"step {n}: {count} rows, read  ({reply.get('why', '')})\n    {sql[:200]}")
    print(f"no answer within {steps} steps; {rows_read} rows read; {calls} decider calls")


if __name__ == "__main__":
    a = sys.argv
    cap = int(a[a.index("--capacity") + 1]) if "--capacity" in a else 100
    st = int(a[a.index("--steps") + 1]) if "--steps" in a else 8
    walk(a[1], cap, st, "--no-result-set" not in a)
