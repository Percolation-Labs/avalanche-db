import json, statistics as st
FIX = ("second", "last", "longest")
verdicts = []
for s in ("cards", "prs", "mq"):
    try: rows = [json.loads(l) for l in open(f"d0-{s}.jsonl")]
    except FileNotFoundError: continue
    rows = [r for r in rows if "error" not in r["doors"].get("gold", {}) and "error" not in r["doors"].get("control", {})]
    g = [r["doors"]["gold"] for r in rows]; c = [r["doors"]["control"] for r in rows]
    top = sum(min(d["rank"][v] for v in FIX) == 0 for d in g) / len(g)
    qtop = sum(d["rank"]["q-best"] == 0 for d in g) / len(g)
    disp = sum(max(d["rank"][v] for v in FIX) > 0 for d in c) / len(c)
    dr = st.median(min(d["rank"][v] for v in FIX) - d["rank0"] for d in g)
    dp = lambda ds, v: st.mean(d["v"][v] - d["p"] for d in ds)
    alt = sum(d["alt"] for d in g) / max(1, sum(d["leads"] for d in g))
    print(f"{s}: n={len(rows)}  gold door to top by best fixed variant {top:.2f} (q-best {qtop:.2f})  control displaced {disp:.2f}  median gold rank change {dr:+}  leads with an alternative {alt:.2f}")
    print("   mean P change, gold: " + "  ".join(f"{v} {dp(g, v):+.3f}" for v in FIX + ('q-best',)) + "   control: " + "  ".join(f"{v} {dp(c, v):+.3f}" for v in FIX + ('q-best',)))
    print(f"   cost ${sum(r['cost'] for r in rows):.3f}")
    verdicts.append(top - disp >= .10)
print("text headroom (>= 2 of 3 sets):", sum(verdicts) >= 2, verdicts)
