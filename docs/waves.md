# Queries as waves

SQL and Cypher ask you to say exactly what you want before anything runs. A durable walk
lets you find out what you want while it runs: each likeness wave returns some nodes, each
connection wave follows some of their links, and you decide at every wave what to do next.
This page takes five traditional queries, rewrites each as a sequence of waves on the
billing example, and notes what the exercise reveals. It is an exploration, not a recipe.

In a table, the shape of an answer lives in columns. In a property graph, it lives in edge
types written into a pattern. In a walk, it lives in connectivity: which links a node has,
which of them you follow, and what you reach. All the output below is real, from `midb` on
the billing example.

## 1. A join: who works with Bob?

```sql
SELECT DISTINCT p2.name
FROM people p1
JOIN commits c1      ON c1.author = p1.id
JOIN commit_files f1 ON f1.commit = c1.id
JOIN commit_files f2 ON f2.file = f1.file
JOIN commits c2      ON c2.id = f2.commit
JOIN people p2       ON p2.id = c2.author
WHERE p1.name = 'Bob' AND p2.id <> p1.id;
```

As waves, this is one likeness wave and then four connection waves:

```text
ran
  1  like     'Bobby' → person:Bob 0.60          likeness: a wave of one
  2  hop      <-authoredBy- commit               2 rows, 2 keys
  3  hop      -touches-> file                    2 rows, 10 keys
  4  hop      <-touches- commit                  7 rows, 10 keys
  5  hop      -authoredBy-> person               7 rows, 41 keys
  6  filter   y <> x: 5 of 7 kept
y
person:Chen
person:Ana
```

The SQL needs six joins written before it runs, and it names Bob exactly. The walk began
from "Bobby", a name nobody has, and the likeness wave found Bob at 0.60. Each connection
wave reports how many rows it carried and how many keys it read, so you can see where the
work is done: the last wave, from seven commits to their authors, read 41 of the 68 keys.

**What it reveals.** The joins in the SQL are the walk's connection waves, one for one. The
difference is when you commit to them. In our agent eval, an agent that could only take one
connection at a time (`edges`) answered this question in 11 or 12 calls. An agent that could
write the whole walk down as one P8QL statement answered in 2 or 3. Once you know the shape,
writing it down is cheaper. The walk earns its place when you don't know the shape yet.

## 2. A miss: equality against likeness

```sql
SELECT * FROM people WHERE name = 'Bobby';   -- 0 rows
```

```text
$ midb query "SELECT x FROM person = 'Bobby' AS x"
midb: person:Bobby is not in the store at T2

$ midb query "SELECT x FROM person LIKE 'Ann' AS x"
  1  like     'Ann' → person:Ana 0.67
```

SQL's empty result is a fact about the question, not about the data. You learn nothing about
what was nearby. A likeness wave always returns its nearest nodes with their scores. When the
top two are within 0.1 of each other, it pauses and hands the choice back instead of guessing.

**What it reveals.** A declarative query treats "no rows" and "you asked the wrong way" as
the same thing. A walk keeps them apart, because a likeness wave is never simply empty: it
is ranked.

## 3. A Cypher pattern: issues fixed in files Chen also changed

```cypher
MATCH (:Person {name: 'Chen'})<-[:AUTHORED_BY]-(:Commit)-[:TOUCHES]->(f:File)
      <-[:TOUCHES]-(:Commit)-[:FIXES]->(i:Issue)
RETURN DISTINCT i
```

```text
ran
  1  lookup   person:Chen
  2  hop      <-authoredBy- commit               1 row, 1 keys
  3  hop      -touches-> file                    1 row, 5 keys
  4  hop      <-touches- commit                  4 rows, 4 keys
  5  hop      -fixes-> issue                     1 row, 22 keys
i
issue:BUG-3
```

Cypher's arrows and the walk's hops are nearly the same notation. Cypher states the whole
pattern and asks for every match at once. The walk takes the hops in the order written and
reports each wave's size: one commit, one file, four commits, one fix. If the four commits
had been four hundred, you would see it at wave 4 and could narrow the walk before taking
the last hop.

**What it reveals.** In a pattern, the middle of the path is invisible: you see the matches
at the end. A walk shows the width of every wave, which is where the cost, and often the
surprise, lies. The `fixes` link exists only because `midb dream` decided this commit fixes
that issue. A pattern that names `FIXES` assumes the edge is there. A walk asks what links a
node has before deciding which to follow.

## 4. An open question: why is the invoice a cent off?

There is no SQL or Cypher for this one unless you already know the answer's shape. The
nearest Cypher is a variable-length match:

```cypher
MATCH p = (:Issue {id: 'BUG-12'})-[*1..3]-(x) RETURN p
```

That returns every path of up to three hops, in no order, and leaves the reading to you. A
walk takes the question one wave at a time and ranks what it could do next:

```text
$ midb ask "why is the invoice a cent off"
session s1 at issue:BUG-12, pinned to T2, budget 20
$ midb step s1.0.2
step 1  issue:BUG-12 "A cent off on long invoices"
  + <-because- decision:ADR-007  "Banker's rounding for money amounts"  0.90
  + <-fixes- commit:cc746808d1  "invoice: round totals half-even (ADR-007, BUG-12)"  0.72
  + <-duplicates- issue:SUP-88  "Invoice total differs from customer spreadsheet"  0.45
  open 3 (opened 3, closed 1); next: decision:ADR-007 0.90, commit:cc746808d1 0.72, ...
  token s1.1.2
```

The likeness wave landed on BUG-12. The connection wave opened three links and ranked them.
You take ADR-007 (or tell the walk to prefer something else), and the next wave goes on from
there to P-3, the proposal ADR-007 rejected. The token is the walk's durable state: stop here,
come back tomorrow, and `step s1.1.2` resumes at the same point.

**What it reveals.** This is where a walk does something a declarative query cannot: it
decides at each wave, so you never had to know that a *decision* or a *rejected proposal*
existed before you asked. But it is not always fewer steps. In our eval, an agent using
`why` answered this question in one call, while an agent that wrote the walk as one P8QL
statement then checked three of its records again before it trusted the answer. A walk that
prints its plan and trace may read as less final than one that prints only the answer.

## 5. An aggregate: which cards share the most files with another?

On Percolate's own history (board cards, commits, files), a count is the natural question:

```sql
SELECT c2.card, COUNT(DISTINCT cf2.file) AS n
FROM card_commits c1 JOIN commit_files cf1 ON cf1.commit = c1.commit
JOIN commit_files cf2 ON cf2.file = cf1.file
JOIN card_commits c2  ON c2.commit = cf2.commit
WHERE c1.card = 'REM-1309' AND c2.card <> c1.card
GROUP BY c2.card ORDER BY n DESC LIMIT 2;
```

```text
$ midb query "SELECT y, count(DISTINCT file) AS n FROM card = 'REM-1309' AS c
    WALK c <-mentions- commit -touches-> file <-touches- commit -mentions-> card AS y
    WHERE y <> c GROUP BY y ORDER BY n DESC LIMIT 4"
y              n
card:REM-1018  7
card:REM-1266  7
card:REM-1080  2
card:REM-1313  2
4 rows; 6736 keys read in 1.7ms
```

**What it reveals.** Counting is not a wave. GROUP BY and count fold the last wave into
numbers, and they add nothing to the rhythm of likeness and connection. That is why they sit
at the end of the statement and why they are the least walk-like part of P8QL. It also shows
a limit that every query form shares. While checking these answers against git, we found the
git adapter keeps at most 40 files per commit and reads card ids only from a commit's subject
line. No query, declarative or walked, can see a link that was never written. A walk reports
the keys it read, but not the ones that were never stored.

## What the exercise suggests

- **Joins and pattern arrows are connection waves.** The translation is one to one. What
  differs is the moment of commitment: before the query, or at each wave.
- **Likeness replaces equality at the start of a query,** and a ranked miss teaches more
  than an empty one.
- **A walk shows the width of every wave.** A declarative query shows only the end.
- **Writing a walk down is cheaper once its shape is known.** A P8QL statement is a walk you
  have already discovered, and in the eval it took a fifth of the calls of walking link by
  link. The open question, where the shape is unknown, is where stepping pays.
- **Aggregation is outside the rhythm.** It summarizes a wave, and it is the one place where
  SQL's notation has no walk to translate.
