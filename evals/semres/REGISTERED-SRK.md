# SR-K (registered 21 Nov, before scoring): is a shared key door a gold-free stand-in for the next-hop term?

**Serves:** THEORY-SR item 1. A graph measure should price the relational step that Jev pays for, and cosine misses it.
SR-J amendment 2 found that the bridge entity e(v) ("v names the hop-1 answer") carries Jev's next-hop term: the
e-decider gets .90 top-1, against the vectors' best .62 and Jev's .97. But e uses the gold answer. The hypothesis is that
the graph's own key doors, without gold, carry the same signal.

**Data, all cached, $0.**
- SR-J's 40 MuSiQue cases (`out/srj-n40.json`): 19 options after reading hop 1, Jev's p per option and the gold hop 2.
- Key doors: the `keys` of each passage in the dream-d1 MuSiQue graph (`graph-mq.jsonl`, 21,100 passages; it covers
  every option). A key counts as a door when 2 ≤ df ≤ 100, the graph's existing door definition (j4.py's `mem`). That
  range is inherited, not chosen here.

**Features** (R = the read passage's door keys):
- `k_any(v)`: v shares any door key with R.
- `k_new(v)`: v shares a door key with R that isn't contained in the question's words. This is the gold-free analogue of
  "names the bridge entity".
- `k_str(v)` = Σ 1/(df(k) − 1) over the shared new keys. This is j4's `strength` and has no parameter.

**Gold-blind look before registering** (no gold, no Jev): `k_new` marks exactly one option in 19 of 40 cases and none in
2. `k_any` marks a median of about 5 options. One case printed: "Who is the spouse of the Green performer?" There, only
Miquette Giraudy shares `steve hillage` with the read passage.

**Outcomes:**
1. **Primary.** Top-1 hop-2 accuracy of the k-decider: argmax `k_str`, with ties broken by `cos_qr` as in SR-J's
   e-decider. Report a bootstrap 95% CI over questions.
2. Recall and precision of `k_new` for hop 2, beside e's .90 and .97.
3. Agreement of the k-decider's pick with Jev's argmax.
4. A fit of logit p_Jev = β cos_q + κ k_new + γ hop2 + c, using the SR-J fit code. Report κ, and γ with and without
   κ. SR-J amendment 2 showed that collinearity can stop the fit splitting the two terms, so this is descriptive only.

**Bar.** H1 (a gold-free stand-in) passes if the k-decider's CI lower bound is above the vectors' best, .62. It is
"close to e" if the point estimate is ≥ e's .90 minus its own CI half-width. Otherwise the result is a fail, and the
write-up says which outcome failed.

**Scope.** MuSiQue 2-hop only, 40 questions. Cards have no key-door graph here, so they are out of scope. The read
passage is the gold hop 1, as in SR-J.
