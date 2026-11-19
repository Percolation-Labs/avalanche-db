"""D3c (REGISTERED-D3c.md): remove the key memberships with the lowest learned-to-uniform vote ratio
width^(θ1+1)·(1+doors(t))^θ2; f chosen on dev under the gold-door constraint; scored on test. $0."""
exec(open(__file__.replace("d3c.py", "d3.py")).read().split("TESTF = ")[0])
TESTF = {"cards": ("../../floor/trace-cards.jsonl", "../../floor/q-cards.jsonl"), "prs": ("../../floor/trace-pr.jsonl", "../../floor/q-prs-test.jsonl")}
THETA = {"prs": (-2.0, -1.0), "cards": (-1.0, -0.5)}
rows = [json.loads(l) for l in open("graph-p8.jsonl")]
for c, (t1, t2) in THETA.items():
    g = G(rows); k0, o0 = g.keep.copy(), set(g.owned)
    dev, test = dev_waves(c), test_waves(c, *TESTF[c])
    df = g.df[g.mem[:, 1]]; nd = g.nd[g.mem[:, 0]]
    ok = (df >= 2) & (df <= 100)
    ratio = np.where(ok, df ** (t1 + 1) * (1 + nd) ** t2, np.inf)
    order = np.argsort(ratio, kind="stable")
    d0 = score(g, dev); print(f"{c} θ=({t1},{t2}): dev G0 {d0[0]:.3f} (gold door {d0[1]:.2f})", flush=True)
    best = None
    for f in (0.02, 0.05, 0.10, 0.20):
        n = int(f * ok.sum()); keep = k0.copy(); keep[order[:n]] = False
        g.build(keep, o0); d = score(g, dev)
        elig = d[1] >= d0[1] - 0.02
        print(f"  f={f}: removed {n} | dev {d[0]:.3f} (gold door {d[1]:.2f}){'' if elig else ' INELIGIBLE'}", flush=True)
        if elig and (best is None or d[0] > best[0]): best = (d[0], f, keep)
    if best is None or best[0] <= d0[0]:
        print(f"  no eligible f beats G0 on dev; scoring the best eligible anyway" if best else "  no eligible f", flush=True)
    if best is None: continue
    _, f, keep = best
    g.build(k0, o0); t0 = score(g, test)
    g.build(keep, o0); te = score(g, test)
    rk, ro = random_edit(g, keep, o0); g.build(rk, ro); tr = score(g, test)
    print(f"  chosen f={f} | TEST G0 {t0[0]:.3f} (gold door {t0[1]:.2f}) | G_edit {te[0]:.3f} ({te[1]:.2f}) | random removal {tr[0]:.3f} ({tr[1]:.2f})", flush=True)
