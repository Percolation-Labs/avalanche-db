"""noise.py -- bank-noisy.db: bank-large.db with the rarities real data has and which mean nothing.

On bank-large.db every planted case is a rare value, so a walk that reads rare values finds them
for free. This adds, with a fixed seed, ordinary customers who also do rare things:
  - 30 small merchants (a locksmith, a vet ...) each used 1 to 4 times
  - 40 card payments between 01:00 and 05:00 (late taxis, takeaways), ~20 to 60
  - 15 large one-off payments with ordinary memos (car purchase, wedding venue, school fees)
  - 12 single refunds of 5 to 80
  - 10 busy days: one customer making 6 to 9 card payments in an afternoon
The plants (C0017, C0029, C0005, the Northgate payments) are untouched.

    python3 noise.py        # writes bank-noisy.db
"""
import os, random, shutil, sqlite3

HERE = os.path.dirname(os.path.abspath(__file__))
src, dst = os.path.join(HERE, "bank-large.db"), os.path.join(HERE, "bank-noisy.db")
shutil.copy(src, dst)
db = sqlite3.connect(dst)
rnd = random.Random(1113)
plants = {"C0005", "C0017", "C0029", "C0002", "C0008", "C0014", "C0021", "C0033"}
accts = [a for (a, c) in db.execute("select id, customer_id from accounts where kind='current' order by id") if c not in plants]
if not accts:
    accts = [a for (a, c) in db.execute("select id, customer_id from accounts order by id") if c not in plants]
mers = [m for (m,) in db.execute("select id from merchants where category in ('grocery','food','retail','digital','marketplace','transport') order by id")]
n = db.execute("select count(*) from transactions").fetchone()[0]


def tx(acct, mer, at, amount, kind="card", memo=""):
    global n
    n += 1
    db.execute("insert into transactions values (?,?,?,?,?,?,?)", (f"N{n:05d}", acct, mer, at, round(amount, 2), kind, memo))


def day():
    return f"2026-11-{rnd.randint(1, 30):02d}"


small = ["Keyfix Locksmiths", "Hilltop Vets", "Rowan Florist", "Quayside Tailor", "Moss Dental", "Ember Kilns",
         "Ferry Bikes", "Larch Opticians", "Northside Laundry", "Orchard Piano Tuning", "Pine Framing", "Tidal Swim School",
         "Vane Clockmakers", "Willow Upholstery", "Yard Tools Hire", "Atlas Storage", "Beacon Printing", "Cobble Cobblers",
         "Dune Surf Shop", "Elm Bookbinding", "Fern Garden Centre", "Glen Car Wash", "Harbour Fishmonger", "Iris Pottery",
         "Juniper Spa", "Kestrel Driving School", "Lantern Theatre", "Meadow Riding", "Nook Escape Rooms", "Oak Tattoo"]
cats = ["services", "pets", "retail", "services", "health", "retail", "transport", "health", "services", "services",
        "retail", "leisure", "retail", "services", "services", "services", "services", "services", "leisure", "retail",
        "retail", "transport", "grocery", "retail", "leisure", "transport", "leisure", "leisure", "leisure", "services"]
for i, (name, cat) in enumerate(zip(small, cats)):
    mid = f"S{i + 1:02d}"
    db.execute("insert into merchants values (?,?,?)", (mid, name, cat))
    for _ in range(rnd.randint(1, 4)):
        tx(rnd.choice(accts), mid, f"{day()} {rnd.randint(9, 18):02d}:{rnd.choice(['00', '15', '30', '45'])}", -rnd.uniform(15, 220))
for _ in range(40):
    tx(rnd.choice(accts), rnd.choice(mers), f"{day()} 0{rnd.randint(1, 4)}:{rnd.choice(['05', '20', '40'])}", -rnd.uniform(20, 60))
memos = ["car purchase", "wedding venue deposit", "school fees", "kitchen fitting", "solar panels", "boiler replacement",
         "flight bookings", "car purchase", "dental implant", "roof repair", "tuition", "piano", "conservatory", "holiday", "loft conversion"]
for m in memos:
    tx(rnd.choice(accts), None, f"{day()} {rnd.randint(9, 16):02d}:00", -rnd.uniform(4000, 22000), "transfer", m)
for _ in range(12):
    tx(rnd.choice(accts), rnd.choice(mers), f"{day()} {rnd.randint(9, 18):02d}:30", rnd.uniform(5, 80), "refund")
for _ in range(10):
    a, d = rnd.choice(accts), day()
    for j in range(rnd.randint(6, 9)):
        tx(a, rnd.choice(mers), f"{d} {13 + j // 2:02d}:{(j % 2) * 30:02d}", -rnd.uniform(5, 90))
db.commit()
print(f"bank-noisy.db: {n} transactions, {db.execute('select count(*) from merchants').fetchone()[0]} merchants")
