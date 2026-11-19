"""Named worked examples, chosen from fixtures/<set>/index.jsonl by fixed rules (not by eye), and one SVG per example.
    python3 examples.py            writes fixtures/examples.json and fixtures/svg/<set>-<rule>.svg"""
import json, os, html

RULES = {
    "lands": "the seeds land on S: most seeds that are gold, with gold left beyond the seeds (≥2 gold); ties to the smallest Steiner cost",
    "misses": "the seeds miss S: nearest seed ≥2 doors from any gold (≥2 gold); ties to the smallest Steiner cost",
    "compact": "a compact S: ≥3 gold, none detached, the lowest Steiner cost per gold",
    "spread": "a spread S: ≥3 gold, the largest gold-to-gold distance in doors; ties to the largest cost",
    "learned-wins": "PR titles only: the largest LQ − Q recall@5; ties to the smallest Steiner cost",
}


def pick(rows, rule):
    R = [r for r in rows if r["n_gold"] >= (3 if rule in ("compact", "spread") else 2)]
    if rule == "lands": R = sorted([r for r in R if r["n_gold"] > r["seeds_on_gold"]], key=lambda r: (-r["seeds_on_gold"], r["steiner_cost"], r["qid"]))
    elif rule == "misses":
        R = sorted([r for r in R if r["nearest_seed_doors"] is None or r["nearest_seed_doors"] >= 2], key=lambda r: (r["steiner_cost"], r["qid"]))
    elif rule == "compact":
        R = sorted([r for r in R if r["detached"] == 0], key=lambda r: (r["steiner_cost"] / r["n_gold"], r["qid"]))
    elif rule == "spread":
        R = sorted([r for r in R if r["max_gold_pair_doors"]], key=lambda r: (-r["max_gold_pair_doors"], -r["steiner_cost"], r["qid"]))
    elif rule == "learned-wins":
        R = sorted([r for r in R if r["recall5"]["LQ"] is not None], key=lambda r: (-(r["recall5"]["LQ"] - r["recall5"]["Q"]), r["steiner_cost"], r["qid"]))
    return R[0] if R else None


def short(s, n=46):
    s = s or "?"
    return s if len(s) <= n else s[: n - 1] + "…"


def door(via):
    if not via: return ""
    v = via[0]
    return "Beside" if v["kind"] == "beside" else ("Near" if v["kind"] == "near" else f"“{v['key']}” ({v['width']})")


def svg(fx, title):
    st = fx["steiner"]
    seeds = {s["id"]: s for s in fx["seeds"]}
    reads = {d["id"]: d for d in fx["walk_reads"] if d["wave"] >= 1}
    lq = {t["id"] for t in fx["top5"]["LQ"]}
    nodes = {n["id"]: n for n in st["nodes"]}
    for s in fx["seeds"]: nodes.setdefault(s["id"], {"id": s["id"], "label": s["label"], "role": "seed"})
    for d in reads.values(): nodes.setdefault(d["id"], {"id": d["id"], "label": d["label"], "role": "read"})
    for g in fx["gold"]:
        if g.get("not_in_graph"): nodes.setdefault(g["id"], {"id": g["id"], "label": "(not in graph)", "role": "gold"})
    gold = {g["id"] for g in fx["gold"]}
    col = lambda n: 0 if n["id"] in seeds else (2 if n["id"] in gold else 1)
    cols = {0: [], 1: [], 2: []}
    for n in nodes.values(): cols[col(n)].append(n)
    for c in cols: cols[c].sort(key=lambda n: (n["id"] not in st and n["role"] == "read", n["label"] or ""))
    W, rowh, top = 1180, 46, 96
    H = top + rowh * max(len(v) for v in cols.values()) + 70
    X = {0: 40, 1: 430, 2: 820}; pos = {}
    for c, ns in cols.items():
        for i, n in enumerate(ns): pos[n["id"]] = (X[c], top + i * rowh)
    o = [f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" font-family="system-ui, sans-serif" font-size="12">',
         '<style>.t{fill:#1d1d1f}.m{fill:#6e6e73}.e{stroke:#0a7d5a;stroke-width:2;fill:none}.k{fill:#0a7d5a;font-size:10px}</style>',
         f'<rect width="{W}" height="{H}" fill="#fff"/>',
         f'<text x="20" y="28" font-size="15" font-weight="600" class="t">{html.escape(short(title, 150))}</text>',
         f'<text x="20" y="50" class="m">{html.escape(short(fx["question"], 170))}</text>',
         f'<text x="{X[0]}" y="78" font-weight="600" class="m">search’s seeds</text><text x="{X[1]}" y="78" font-weight="600" class="m">connectors and walk reads</text><text x="{X[2]}" y="78" font-weight="600" class="m">gold</text>']
    for l in st["links"]:
        if l["a"] in pos and l["b"] in pos:
            (x1, y1), (x2, y2) = pos[l["a"]], pos[l["b"]]
            x1 += 150; x2 += 0 if x2 > x1 else 150
            o.append(f'<path class="e" d="M{x1},{y1} C{(x1 + x2) / 2},{y1} {(x1 + x2) / 2},{y2} {x2},{y2}"/>')
            lab = html.escape(short(door(l["via"]), 34)); lx, ly = (x1 + x2) / 2 - 40, (y1 + y2) / 2 - 4
            o.append(f'<rect x="{lx - 3}" y="{ly - 11}" width="{6.2 * len(lab) + 6}" height="15" rx="3" fill="#fff" opacity=".9"/>')
            o.append(f'<text class="k" x="{lx}" y="{ly}">{lab}</text>')
    for nid, n in nodes.items():
        x, y = pos[nid]
        isg, iss, isr, inS = nid in gold, nid in seeds, nid in reads, nid in {m["id"] for m in st["nodes"]}
        fill = "#f5c400" if isg else ("#dbe9ff" if iss else "#f2f2f4")
        stroke = "#0a7d5a" if inS else "#c7c7cc"
        o.append(f'<rect x="{x}" y="{y - 15}" width="340" height="28" rx="6" fill="{fill}" stroke="{stroke}" stroke-width="{2 if inS else 1}"/>')
        tag = []
        if isr: tag.append(f"walk w{reads[nid]['wave']}")
        if nid in lq: tag.append("LQ top 5")
        o.append(f'<text x="{x + 8}" y="{y + 4}" class="t">{html.escape(short(n["label"], 44))}</text>')
        if tag: o.append(f'<text x="{x + 338}" y="{y + 4}" text-anchor="end" class="m" font-size="10">{" · ".join(tag)}</text>')
    r = fx["recall5"]
    p = fx["potential"]
    o.append(f'<text x="20" y="{H - 34}" class="m">Steiner cost {st["cost"]} links; nearest seed {st["entry"]["doors"] if st["entry"] else "—"} doors from gold; '
             f'graph within 1 door of the seeds: {p["within_1_door"]:,} passages, within 2: {p["within_2_doors"]:,}</text>')
    fmt = lambda v: "—" if v is None else f"{v:.2f}"
    o.append(f'<text x="20" y="{H - 14}" class="m">recall@5 beyond the seeds: search {fmt(r["S"])}, U {fmt(r["U"])}, Q {fmt(r["Q"])}, LQ {fmt(r["LQ"])}. '
             f'Yellow gold, blue seeds, green-edged nodes and links form the Steiner graph.</text>')
    o.append("</svg>")
    return "\n".join(o)


def main():
    out = []
    os.makedirs("fixtures/svg", exist_ok=True)
    for c in ("cards", "prs", "mq"):
        rows = [json.loads(l) for l in open(f"fixtures/{c}/index.jsonl")]
        for rule in RULES:
            if rule == "learned-wins" and c != "prs": continue
            r = pick(rows, rule)
            if not r:
                out.append({"name": f"{c}-{rule}", "set": c, "rule": RULES[rule], "qid": None, "note": "no test question meets the rule"})
                print(f"{c}-{rule}: none meets the rule"); continue
            fx = json.load(open(f"fixtures/{c}/{r['file']}"))
            name = f"{c}-{rule}"
            open(f"fixtures/svg/{name}.svg", "w").write(svg(fx, f"{ {'cards': 'Cards', 'prs': 'PR titles', 'mq': 'MuSiQue'}[c]} · {rule}: {fx['qid']}"))
            out.append({"name": name, "set": c, "rule": RULES[rule], "qid": r["qid"], "fixture": f"{c}/{r['file']}", "svg": f"svg/{name}.svg", "summary": r})
            print(f"{name}: {r['qid']} gold {r['n_gold']} seeds-on-gold {r['seeds_on_gold']} cost {r['steiner_cost']} recall5 {r['recall5']}")
    json.dump({"rules": RULES, "examples": out}, open("fixtures/examples.json", "w"), indent=1)


if __name__ == "__main__":
    main()
