"""split.py DREAM_OUT [SPLIT_DAY] -- truth.py's rule, scored separately on sources dated before
SPLIT_DAY and on or after it, so wording tuned on one side is checked on the other. Every commit/pr -> card mention is (choice, p);
an `only mentions` answer counts as p = 0 for implements."""
import re, subprocess, sys, json, functools, os
P = os.environ.get("PERCOLATE", os.path.expanduser("~/code/percolate"))
CACHE = os.environ.get("PR_CACHE", os.path.expanduser("~/.cache/split-pr.json"))
prc = json.load(open(CACHE)) if os.path.exists(CACHE) else {}

def git(c, fmt): return subprocess.run(["git", "-C", P, "log", "-1", f"--format={fmt}", c], capture_output=True, text=True).stdout.strip()
def pr(n):
    if n not in prc:
        j = subprocess.run(["gh", "pr", "view", n, "-R", "Percolation-Labs/percolate", "--json", "title,headRefName,createdAt"], capture_output=True, text=True).stdout
        prc[n] = json.loads(j) if j else {"title": "", "headRefName": "", "createdAt": ""}
        json.dump(prc, open(CACHE, "w"))
    return prc[n]
@functools.lru_cache(None)
def subj(s): return git(s.split(":")[1], "%s")
def day(s):
    return pr(s.split("#")[1])["createdAt"][:10] if s.startswith("pr:") else git(s.split(":")[1], "%cs")
def truth(s, card):
    num = card.split("-")[1]
    if s.startswith("pr:"):
        d = pr(s.split("#")[1]); return bool(re.search(rf"(?<!\d){num}(?!\d)", d["headRefName"]) or re.search(rf"\bREM-{num}\b", d["title"]))
    t = subj(s)
    if re.match(r"Merge (remote-tracking )?branch '(origin/)?main'", t): return False
    m = re.match(r"Merge pull request #(\d+) from \S+/(\S+)", t)
    if m: return truth(f"pr:percolate#{m.group(1)}", card)
    return bool(re.search(rf"\bREM-{num}\b", t))

out = open(sys.argv[1]).read()
split = sys.argv[2] if len(sys.argv) > 2 else "2026-11-05"
rows = {}
for s, o, p in re.findall(r"^  ((?:commit|pr)\S+)\s+implements\s+(card:\S+)\s+([0-9.]+)$", out, re.M): rows[(s, o)] = float(p)
for s, o, p in re.findall(r"((?:commit|pr)\S+) implements (card:\S+) \(([0-9.]+)\)", out): rows[(s, o)] = float(p)
for x in re.search(r"only mentions: (.*)", out).group(1).split(", "):
    s, o = x.split(" → ")
    if s.startswith(("commit:", "pr:")) and o.startswith("card:"): rows.setdefault((s, o), 0.0)
halves = {"before": [], "from": []}
for (s, o), p in rows.items():
    halves["before" if day(s) < split else "from"].append((p, truth(s, o), s, o))
for h, r in halves.items():
    pos = sum(t for _, t, _, _ in r)
    line = [f"{h} (n={len(r)}, true={pos})"]
    for cut in (0.8, 0.6):
        w = [t for p, t, _, _ in r if p >= cut]
        tp = sum(w)
        line.append(f"@{cut}: P {tp/max(1,len(w)):.2f} R {tp/max(1,pos):.2f}")
    zero = sum(1 for p, t, _, _ in r if t and p == 0.0)
    line.append(f"true called only-mention {zero}")
    print("  ".join(line))
if "-v" in sys.argv:
    for p, t, s, o in sorted(halves["before"]):
        if t and p < 0.8: print("  miss", p, s, o, subj(s)[:70] if s.startswith("commit") else pr(s.split("#")[1])["title"][:70])
