# K1 (registered before running): does any key family carry the coherence that goes with finding gold?

*19 Nov 2026, bill, for james's L3 decision (M-20261119-163410-b951). $0, dev only, nothing fitted.*

## Question

L3 would learn one coherence weight per key family. That is worth doing only if some family's share of a walk's
coherence differs between walks that find gold and walks that don't. If no family separates, L3's ceiling is L2.

## Families (fixed by the key's surface form; no thresholds)

Keys are stored lower-case. Each key belongs to the first family whose rule it matches:

1. **number:** contains a digit (years, card numbers such as `rem 505`, counts).
2. **code:** contains `_`, `.` or `/` (identifiers and paths: `upsert_agent`, `path job_dir`).
3. **phrase:** two or more words.
4. **word:** a single word.

Beside (next links) is a fifth family. Near is left out, as in L2.

## Units and measure

- Dev questions of cards, PR titles and MuSiQue, at L2's fitted θ per set (out/l2.json: LC).
- For each question, R = seeds ∪ T, where T is the top 5 beyond the seeds. Seed–seed pairs are dropped, as in L2.
- **Found:** at least one gold passage is in T.
- **Per family f:**
  - **share_f** = the observed strength among R carried by family f's keys (Σ 1/(df−1)), divided by the total
    observed strength;
  - **ratio_f** = observed over expected strength, using family f's own strength-preserving null (L2's coherence
    restricted to f).
- **Separation:** for each family and each measure, the AUC of found against not found across dev questions, with a
  95% bootstrap interval (2000 resamples, seed 0).

## What counts

- **A family separates** if its AUC interval excludes .5 on at least one set. That gives L3 a ceiling above L2. Every
  set is reported, so the number of chances is visible.
- **If no family separates on any set,** L3 isn't run.
- **Total coherence's own AUC** (L2's reward) is reported as the reference. A family has to beat it to be worth a
  weight of its own.
