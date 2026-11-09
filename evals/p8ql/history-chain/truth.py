"""truth.py DREAM_OUT -- score a dream's commit/pr -> card links against a rule from git and gh:
a non-merge commit carries out a card when its subject names it; a PR merge commit or a PR
when its branch carries the card number or its title names the card; a merge of main into
a branch never. The rule undercounts: an "opened after" release commit names REM-542 only in
its body, and is counted wrong. Read the wrong list before quoting precision."""
import re, subprocess, sys, json, functools
import os
P = os.environ.get("PERCOLATE", os.path.expanduser("~/code/percolate"))
@functools.lru_cache(None)
def subj(c): return subprocess.run(["git","-C",P,"log","-1","--format=%s",c.split(":")[1]],capture_output=True,text=True).stdout.strip()
@functools.lru_cache(None)
def pr(n):
    j = subprocess.run(["gh","pr","view",n,"-R","Percolation-Labs/percolate","--json","title,headRefName"],capture_output=True,text=True).stdout
    return json.loads(j) if j else {"title":"","headRefName":""}
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
impl = set(re.findall(r"^  ((?:commit|pr)\S+)\s+implements\s+(card:\S+)\s+[0-9.]+$", out, re.M))
only = {tuple(x.split(" → ")) for x in re.search(r"only mentions: (.*)", out).group(1).split(", ")}
und = set(re.findall(r"((?:commit|pr)\S+) implements (card:\S+) \(", out))
only = {x for x in only if x[0].startswith(("commit:","pr:")) and x[1].startswith("card:")}
tp = sum(truth(*x) for x in impl); fp = len(impl) - tp
fn = sum(truth(*x) for x in only | und); tn = len(only | und) - fn
print(f"implements written {len(impl)}: right {tp}, wrong {fp}; not written {len(only|und)}: missed {fn}, rightly left {tn}")
print(f"precision {tp/max(1,tp+fp):.2f}, recall {tp/max(1,tp+fn):.2f}")
for x in sorted(impl):
    if not truth(*x): print("  wrong:", x, subj(x[0])[:80] if x[0].startswith("commit") else pr(x[0].split('#')[1])["title"][:80])
