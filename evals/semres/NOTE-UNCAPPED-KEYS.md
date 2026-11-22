# Uncapped keys look (22 Nov, $0, no Jev): without the df ceiling, later chain steps become reachable and the candidate set stays small

*james, at bill's framing (17:03Z): the df ≤ 100 cap is a constant, while the step already weights a key by
1/(df − 1). So the knob-free graph keeps every key with df ≥ 2 and lets common places be weak rather than absent.
Scripts `build_keys_uncapped.py` and `keys_look.py`. Output `out/keys-look.txt`. The key files are in
~/.cache/walklab/mq-train/ (`graph-train-pc-cap508.jsonl`, `graph-train-pc-nocap.jsonl`). The look uses the gold
decomposition over all train chains, so it's a look, not a result.*

**Three graphs, the same frequency strategy:**
- **today's**: the strategy's keys, then the dump's df ≤ 100 cap. Built in #75.
- **cap508**: no dump cap. The strategy's own declared cap is max(df_floor, df_share · N) = 508.
- **nocap**: df_share = 1, so there's no ceiling. Its top keys are "united" 4,562, "states", "located"…

**Per chain step:**
- **keyed**: hop i and hop i + 1 share a key.
- **bridge**: the previous hop's answer is itself that shared key.
- **|S|**: for the shared key with the lowest df, the number of other passages in the question's pool of 20 that hold
  it. This is the name step's candidate set.

| graph | step | keyed | bridge is a key | name options \|R\| (median) | \|S\| = 1 | \|S\| ≥ 5 |
|---|---|---|---|---|---|---|
| today's | 2-hop | .78 | .67 | 18 | .68 | .06 |
| today's | 3–4 hop, first | .70 | .57 | 17 | .86 | .02 |
| today's | 3–4 hop, later | **.47** | **.33** | 22 | .78 | .02 |
| cap508 | 2-hop | .96 | .85 | 27 | .63 | .08 |
| cap508 | 3–4 hop, later | .85 | .69 | 34 | .67 | .04 |
| nocap | 2-hop | .98 | .85 | 34 | .63 | .08 |
| nocap | 3–4 hop, first | .97 | .76 | 32 | .70 | .06 |
| nocap | 3–4 hop, later | **.96** | **.76** | 43 | .64 | .05 |

## What it says

- **The ceiling is what cut the later steps.** Without it, the answer that bridges to the next hop is a shared key
  on .76 of later steps, against .33 today. On 2-hop it's .85, against .67.
- **Inside a pool, a common key is still specific.** A place key in about 100–500 passages corpus-wide is usually held
  by one other passage of the question's 20 (|S| = 1 in about two thirds), and rarely by 5 or more. bill's concern,
  that uncapped keys would blow up |S|, doesn't hold within a pool. It would hold in an open corpus, where the walk's
  options aren't a pool of 20.
- **The cost moves to the name request.** The read's keys go from a median of 22 to 43 on later steps, so Jev names
  the bridge among about twice the options, at about twice the naming input. Naming has been cheap (about 8% of a
  passage request, SR-BN), so this should still leave the cheap step well under the full step.
- **One limit.** |S| uses the shared key with the lowest df, the best case for the step. Jev must name it among more
  options, so the real |S| depends on naming accuracy, which only a Jev run measures.

## Proposed next (to register after bill's review)

- **SR-BU:** SR-BH's 200 chains, the cheap walk on the nocap graph (key filter df ≥ 2, not in the question, no upper
  bound), against SR-BH's cached cheap (today's graph) and pass arms.
- **Primary:** all hops, cheap(nocap) − cheap(today), plus cheap(nocap) − pass, with input beside both.
- **Secondary:** the rescue rate per step, against SR-BH's .44 / .62 / .65.
- The questions are SR-BH's seen ones, to pair with its cached arms. No Jev quantity was tuned on them, and the graph
  choice is the knob-free one, not one picked from this look. A fresh draw would follow before any claim.
- Cost: about $0.08 (new name and rescue requests only). Cap $0.20.
