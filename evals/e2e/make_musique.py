"""Corpus A for REGISTERED.md: the walk lab's MuSiQue fixture (p8-subsystems meta/lab, ~/.cache/walklab/fixture-musique)
as a .jsonl of {id, title, text}, which the `documents` adapter reads. Refuses if the result's hash differs.

    python3 make_musique.py ~/.cache/walklab/fixture-musique/docs.jsonl musique.jsonl
"""
import hashlib, json, sys

SHA = "56d59fc70caab615"
src, out = sys.argv[1], sys.argv[2]
with open(out, "w") as f:
    for line in open(src):
        d = json.loads(line)
        _, _, body = d["said"].partition("\n\n")
        f.write(json.dumps({"id": d["uri"], "title": d["title"], "text": body}) + "\n")
got = hashlib.sha256(open(out, "rb").read()).hexdigest()[:16]
if got != SHA:
    sys.exit(f"{out}: sha256 {got}, registered {SHA}")
print(f"{out}: sha256 {got}, as registered")
