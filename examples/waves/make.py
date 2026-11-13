"""make.py -- build the two example databases, with fixed seeds so every run sees the same data.

bank.db (SQLite): customers -> accounts -> transactions, plus merchants. Foreign keys are the
edges. Planted, so the answers are known:
  * C17 Priya Nair: six card payments to a new payee, QuickWire Ltd, between 02:00 and 04:00 on
    18-19 Nov, together far above her usual spending.
  * C29 Tom Okafor: eleven refunds of 1.00 to 3.00 in one afternoon from merchants he never
    bought from (card testing).
  * C05 Lena Fischer (a decoy): one very large transfer, labelled as a house completion.
  * Northgate Fuel skimming reported on 12 Nov: card payments there on or after 12 Nov are at risk
    (C08, C21, C33); payments there before 12 Nov are not (C02, C14).
graph.json (property graph, Neo4j style): Person, Project, Component, Vulnerability and DataClass
nodes; WORKS_WITH, LEADS, DEPENDS_ON, AFFECTED_BY and HANDLES relationships.
"""
import json, random, sqlite3, os, sys
here = os.path.dirname(os.path.abspath(__file__))
rnd = random.Random(7)
FIRST = "Ana Ben Chloe Dev Ema Femi Gita Hugo Ines Jon Kai Lena Mo Nia Omar Pia Priya Raj Sara Tom Uma Vic Wen Yara Zed Alba Bo Cora Dan Eli Faye Gus Hana Ivo Juno Kit Leo Mira Ned Ola".split()
LAST = "Silva Okoro Brandt Mehta Rossi Adeyemi Kaur Lefevre Duarte Park Tanaka Fischer Haddad Novak Farouk Lind Nair Shah Cohen Okafor Iyer Moreau Zhou Petrov Ali Costa Berg Reyes Kim Weber Lopez Dahl Sato Kovac Ruiz Holm Bianchi Varga Quinn Eze".split()

def bank(scale=1, name="bank.db"):
    """scale 1: 40 customers (bank.db). scale 50: 2,000 customers and the same planted cases
    (bank-large.db), for walks whose first waves are far over a walker's capacity."""
    path = os.path.join(here, name)
    n_cust = 40 * scale
    w = 2 if scale == 1 else 4
    cid_of = lambda i: f"C{i:0{w}d}"
    if os.path.exists(path):
        os.remove(path)
    db = sqlite3.connect(path)
    db.executescript("""
      create table customers (id text primary key, name text, city text, since text);
      create table accounts (id text primary key, customer_id text references customers(id), kind text, opened text);
      create table merchants (id text primary key, name text, category text);
      create table transactions (id text primary key, account_id text references accounts(id),
        merchant_id text references merchants(id), at text, amount real, kind text, memo text);
    """)
    merchants = [("M01", "Fresh Market", "grocery"), ("M02", "Northgate Fuel", "fuel"), ("M03", "City Rail", "transport"),
                 ("M04", "Lumen Books", "retail"), ("M05", "Cafe Orbit", "food"), ("M06", "QuickWire Ltd", "money transfer"),
                 ("M07", "Pixel Games", "digital"), ("M08", "Brightside Energy", "utility"), ("M09", "Halden Estates", "property"),
                 ("M10", "Novaplay", "digital"), ("M11", "Sundry Online", "marketplace"), ("M12", "Payroll: Arden Ltd", "salary")]
    db.executemany("insert into merchants values (?,?,?)", merchants)
    tx = []
    n = 0
    def t(acct, merch, day, hour, amount, kind="card", memo=""):
        nonlocal n
        n += 1
        tx.append((f"T{n:04d}", acct, merch, f"2026-11-{day:02d} {hour:02d}:{rnd.randint(0,59):02d}", amount, kind, memo))
    for i in range(1, n_cust + 1):
        cid = cid_of(i)
        db.execute("insert into customers values (?,?,?,?)", (cid, f"{FIRST[(i-1) % 40]} {LAST[i-1] if scale == 1 else LAST[((i-1) * 7 + (i-1) // 40) % 40]}", rnd.choice(["Leeds", "Bristol", "York", "Hull"]), f"20{rnd.randint(12,24)}-0{rnd.randint(1,9)}-01"))
        kinds = ["checking"] + rnd.sample(["savings", "card"], rnd.randint(1, 2))
        for j, k in enumerate(kinds):
            aid = f"A{i:0{w}d}{j}"
            db.execute("insert into accounts values (?,?,?,?)", (aid, cid, k, f"20{rnd.randint(12,24)}-0{rnd.randint(1,9)}-15"))
            if k == "checking":
                t(aid, "M12", 1, 9, round(rnd.uniform(1800, 3200), 2), "credit", "salary")
                t(aid, "M08", 3, 8, -round(rnd.uniform(60, 140), 2), "direct debit", "energy")
            for _ in range(rnd.randint(5, 9)):
                m = rnd.choice(["M01", "M03", "M04", "M05", "M07", "M10", "M11"])
                t(aid, m, rnd.randint(1, 28), rnd.randint(8, 21), -round(rnd.uniform(3, 90), 2))
    acct = lambda c, k: db.execute("select id from accounts where customer_id=? and kind=?", (c, k)).fetchone()
    def card_of(c):
        a = acct(c, "card") or acct(c, "checking")
        return a[0]
    # C17: night-time transfers to a new payee.
    for d, h, amt in [(18, 2, -480.0), (18, 2, -495.0), (18, 3, -499.0), (19, 2, -470.0), (19, 3, -499.0), (19, 4, -490.0)]:
        t(card_of(cid_of(17)), "M06", d, h, amt, "card", "")
    # C29: card testing, many tiny refunds from unfamiliar merchants.
    for k in range(11):
        t(card_of(cid_of(29)), rnd.choice(["M07", "M10", "M11"]), 22, 15, round(rnd.uniform(1, 3), 2), "refund", "")
    # C05: a large but explained transfer.
    t(acct(cid_of(5), "checking")[0], "M09", 14, 11, -48500.0, "transfer", "house purchase completion")
    # Northgate Fuel: skimming reported 12 Nov.
    for c, d in [(cid_of(8), 12), (cid_of(21), 13), (cid_of(33), 15), (cid_of(2), 6), (cid_of(14), 9)]:
        t(card_of(c), "M02", d, rnd.randint(7, 20), -round(rnd.uniform(40, 80), 2), "card", "")
    # Number transactions in time order, so a planted row's id says nothing about it.
    tx.sort(key=lambda r: (r[3], r[1]))
    tx = [(f"T{k + 1:04d}",) + r[1:] for k, r in enumerate(tx)]
    db.executemany("insert into transactions values (?,?,?,?,?,?,?)", tx)
    db.commit()
    print(f"{name}: {n_cust} customers, {db.execute('select count(*) from accounts').fetchone()[0]} accounts, {len(tx)} transactions")

def graph():
    people = ["Ana", "Ben", "Chloe", "Dev", "Ema", "Femi", "Gita", "Hugo", "Ines", "Jon", "Kai", "Lena"]
    nodes = [{"id": p, "label": "Person", "props": {"name": p}} for p in people]
    projects = {"payments-api": ("Ben", ["log4j-core 2.14.1", "jackson-databind 2.15.2"], ["card data"]),
                "search": ("Ben", ["lucene 9.8.0"], []),
                "billing-batch": ("Chloe", ["log4j-core 2.17.2", "postgres-jdbc 42.6.0"], ["customer contact"]),
                "mobile-app": ("Dev", ["okhttp 4.12.0"], ["customer contact"]),
                "fraud-rules": ("Dev", ["log4j-core 2.15.0", "drools 7.74.1"], ["card data"]),
                "docs-site": ("Ema", ["hugo 0.120.0"], []),
                "warehouse": ("Femi", ["log4j-core 2.14.0"], ["sales data"]),
                "internal-wiki": ("Gita", ["xwiki 15.5"], [])}
    edges = []
    for a, b in [("Ana", "Ben"), ("Ana", "Chloe"), ("Ana", "Dev"), ("Ben", "Ema"), ("Dev", "Femi"), ("Gita", "Hugo"), ("Ana", "Ines")]:
        edges.append({"from": a, "type": "WORKS_WITH", "to": b, "props": {}})
    comps = set()
    for pj, (lead, deps, data) in projects.items():
        nodes.append({"id": pj, "label": "Project", "props": {"name": pj}})
        edges.append({"from": lead, "type": "LEADS", "to": pj, "props": {}})
        for d in deps:
            comps.add(d)
            edges.append({"from": pj, "type": "DEPENDS_ON", "to": d, "props": {}})
        for dc in data:
            edges.append({"from": pj, "type": "HANDLES", "to": dc, "props": {}})
    for c in sorted(comps):
        name, ver = c.rsplit(" ", 1)
        nodes.append({"id": c, "label": "Component", "props": {"name": name, "version": ver}})
    nodes.append({"id": "CVE-2021-44228", "label": "Vulnerability", "props": {"name": "Log4Shell", "kind": "remote code execution", "affects": "log4j-core 2.0-beta9 to 2.14.1; 2.15.0 incomplete fix (CVE-2021-45046); fixed in 2.17.1"}})
    nodes.append({"id": "CVE-2023-35116", "label": "Vulnerability", "props": {"name": "jackson-databind cyclic DoS", "kind": "denial of service, disputed", "affects": "jackson-databind up to 2.15.2"}})
    for c in sorted(comps):
        if c.startswith("log4j-core"):
            edges.append({"from": c, "type": "AFFECTED_BY", "to": "CVE-2021-44228", "props": {}})
        if c.startswith("jackson-databind"):
            edges.append({"from": c, "type": "AFFECTED_BY", "to": "CVE-2023-35116", "props": {}})
    for dc in ["card data", "customer contact", "sales data"]:
        nodes.append({"id": dc, "label": "DataClass", "props": {"name": dc, "personal": dc != "sales data"}})
    json.dump({"nodes": nodes, "edges": edges}, open(os.path.join(here, "graph.json"), "w"), indent=1)
    print(f"graph.json: {len(nodes)} nodes, {len(edges)} relationships")

if "--large" in sys.argv:
    bank(50, "bank-large.db")
else:
    bank()
    graph()
