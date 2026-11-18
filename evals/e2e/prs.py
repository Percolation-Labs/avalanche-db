"""The second repository question type (REGISTERED-prs.md): a merged pull request's title asked as a question; the
gold is the PR's own commits (merge^1..merge^2, no merges, no `board:` bookkeeping). No id defines the gold and none
is in the question. Mechanical, from git alone, at a pinned commit; no model writes or judges anything.

    python3 prs.py REPO REV SEED DEV_OUT TEST_OUT
"""
import json, random, re, subprocess, sys

repo, rev, seed, dev_out, test_out = sys.argv[1], sys.argv[2], int(sys.argv[3]), sys.argv[4], sys.argv[5]
git = lambda *a: subprocess.run(["git", "-C", repo, *a], capture_output=True, text=True, check=True).stdout
qs = []
for rec in git("log", rev, "--merges", "--format=%x1e%H%x1f%s%x1f%b").split("\x1e"):
    if not rec.strip():
        continue
    sha, subj, body = (rec.split("\x1f") + ["", ""])[:3]
    m = re.match(r"Merge pull request #(\d+)", subj)
    if not m:
        continue
    title = body.strip().split("\n")[0].strip()
    gold = []
    for line in git("log", "--no-merges", "--format=%H%x1f%s", f"{sha.strip()}^1..{sha.strip()}^2").splitlines():
        h, s = line.split("\x1f", 1)
        if not s.startswith("board:"):
            gold.append(f"commit/{h[:10]}")
    # an id in the title (REM-219, ADR-007) would hand search, and the id door, the answer's key
    if 2 <= len(gold) <= 8 and len(title.split()) >= 5 and not re.search(r"\b[A-Za-z]{2,}-\d+", title):
        qs.append({"qid": f"pr:{m.group(1)}", "question": f"What work went into this, and why: {title}?",
                   "merge": f"commit/{sha.strip()[:10]}", "gold": sorted(gold)})
qs.sort(key=lambda q: int(q["qid"][3:]))
random.Random(seed).shuffle(qs)
dev, test = qs[:65], qs[65:165]
for path, part in ((dev_out, dev), (test_out, test)):
    with open(path, "w") as f:
        for q in sorted(part, key=lambda q: int(q["qid"][3:])):
            f.write(json.dumps(q) + "\n")
print(f"{len(qs)} eligible PRs: {len(dev)} dev, {len(test)} test", file=sys.stderr)
