"""Round one is search: for each cached viewwalk run, the answer after the first view read vs the final answer."""
import json, os, re, subprocess, sys
W = os.path.dirname(os.path.abspath(__file__))
QS = ["noisy-unusual-activity", "unusual-activity", "noisy-card-testing", "noisy-money-transfer", "noisy-one-off", "noisy-busy-afternoon", "noisy-night"]
def pr(s, g): h = len(s & g); return (h / len(g), h / len(s) if s else 0)
for dec in sys.argv[1:]:
    print(f"== decider {dec}, --sample 3, capacity 20")
    for q in QS:
        f = f"{W}/questions/{q}.json"
        if not os.path.exists(f): continue
        g = set(json.load(open(f))["gold"])
        out = subprocess.run([sys.executable, "viewwalk.py", f, "--decider", dec, "--sample", "3"], cwd=W, capture_output=True, text=True,
                             env={**os.environ, "JEV_OFFLINE": "1"}).stdout
        if "result set:" not in out: print(f"  {q}: not cached"); continue
        first, final, steps, kept = None, set(), 0, set()
        for l in out.splitlines():
            m = re.match(r"step (\d+): (.*?): \d+ keys read, kept (.*?)(?:,? nothing new)?  \(", l) or re.match(r"step (\d+): (.*?): .*kept (.*?)  \(", l)
            if l.startswith("step ") and "keys read" in l:
                steps += 1
                k = re.search(r"kept (.*?)(?:, nothing new)?  \(", l)
                ks = set() if not k or k.group(1).startswith("none") else set(re.findall(r"C\d{4}", k.group(1)))
                kept |= ks
                if first is None: first = set(kept)
        final = set(re.findall(r"C\d{4}", out.split("result set:")[1].splitlines()[0]))
        first = first or set()
        r1, p1 = pr(first, g); rf, pf = pr(final, g)
        print(f"  {q:24s} round one (1 view): R {r1:.2f} P {p1:.2f} | final ({steps} views read): R {rf:.2f} P {pf:.2f}"
              f"  gold added after round one: {len((final - first) & g)}  non-gold added: {len((final - first) - g)}")
