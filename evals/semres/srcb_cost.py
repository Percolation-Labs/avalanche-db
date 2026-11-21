"""SR-CB cost: encode the dream-d1 MuSiQue graph's 21,100 passages (graph order) with each ColBERT model and with
bge-small, on this Mac's CPU. Reports wall time, tokens kept per passage, and index size at fp16 (raw vectors, no
compression). Vectors are not saved.
    uv run --with pylate python srcb_cost.py GRAPH_MQ"""
import hashlib, json, os, sys, time
import numpy as np
text = {}
for l in open(os.path.expanduser("~/.cache/walklab/musique-src/musique_ans_v1.0_dev.jsonl")):
    for p in json.loads(l)["paragraphs"]:
        text["mq:" + hashlib.sha256((p["title"] + "\n" + p["paragraph_text"]).encode()).hexdigest()[:16]] = p["title"] + ". " + p["paragraph_text"]
docs = [text[json.loads(l)["d"]] for l in open(sys.argv[1])]
from sentence_transformers import SentenceTransformer
from pylate import models
t = time.time(); E = SentenceTransformer("BAAI/bge-small-en-v1.5", device="cpu").encode(docs, batch_size=64); tb = time.time() - t
print(f"bge-small: {len(docs)} passages, {tb:.0f} s, 1 vector x 384, fp16 index {len(docs) * 384 * 2 / 1e6:.1f} MB", flush=True)
for name in ("answerdotai/answerai-colbert-small-v1", "mixedbread-ai/mxbai-edge-colbert-v0-17m"):
    m = models.ColBERT(name, device="cpu"); t = time.time(); D = m.encode(docs, is_query=False, batch_size=64); tc = time.time() - t
    n = np.array([len(x) for x in D]); dim = D[0].shape[1]
    print(f"{name}: {tc:.0f} s ({tc / tb:.1f}x bge), tokens per passage mean {n.mean():.0f} (median {int(np.median(n))}), "
          f"dim {dim}, fp16 index {n.sum() * dim * 2 / 1e6:.0f} MB ({n.sum() * dim * 2 / (len(docs) * 384 * 2):.0f}x bge)", flush=True)
