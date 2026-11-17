"""The real-repo questions (REGISTERED.md, part B): a card's title asked as a question; the gold is the commits whose
message names the card's id, less the board's bookkeeping commits. Mechanical, from git alone, at a pinned commit; no model writes or judges anything.

    python3 cards.py REPO REV N SEED > cards.jsonl
"""
import collections, json, random, re, subprocess, sys

repo, rev, n, seed = sys.argv[1], sys.argv[2], int(sys.argv[3]), int(sys.argv[4])
git = lambda *a: subprocess.run(["git", "-C", repo, *a], capture_output=True, text=True, check=True).stdout
log = git("log", rev, "--format=%x1e%H%x1f%s%x1f%b")
named = collections.defaultdict(set)
for rec in log.split("\x1e"):
    if not rec.strip():
        continue
    sha, subj, body = (rec.split("\x1f") + ["", ""])[:3]
    if subj.startswith("board:"):
        continue                # bookkeeping (take, move, file): it names the card and often carries its title verbatim
    for m in set(re.findall(r"\bREM-(\d+)\b", subj + "\n" + body, re.I)):
        named[f"REM-{m}"].add(f"commit/{sha.strip()[:10]}")
cards = []
for path in git("ls-tree", "--name-only", rev, "board/cards/").split():
    text = git("show", f"{rev}:{path}")
    cid = re.search(r"^id:\s*(\S+)", text, re.M)
    title = re.search(r"^title:\s*(.+)$", text, re.M)
    if not cid or not title:
        continue
    cid, title = cid.group(1), title.group(1).strip().strip('"')
    gold = sorted(named.get(cid, ()))
    # a title that names its own id, or another id, would hand search the answer's key
    if 1 <= len(gold) <= 8 and len(title.split()) >= 5 and not re.search(r"\bREM-\d+", title, re.I):
        cards.append({"qid": f"card:{cid}", "question": f"What was done about this, and why: {title}?",
                      "card": f"{path}#1", "gold": gold})
cards.sort(key=lambda c: c["qid"])
pick = sorted(random.Random(seed).sample(cards, min(n, len(cards))), key=lambda c: c["qid"])
print(f"{len(cards)} eligible cards, {len(pick)} sampled", file=sys.stderr)
for c in pick:
    print(json.dumps(c))
