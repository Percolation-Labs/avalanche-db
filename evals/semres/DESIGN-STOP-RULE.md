# Design (22 Nov): a stop rule without a chosen constant

*bill. Follows SR-BH and SR-BH2 (#94): every chain walk so far was told its hop count H. A spare read was worth
+.16 to +.21 all-hops and paid for itself per character, so the walk's value is in when it stops. Design for james's
review; nothing is registered or run.*

**The question.** With H hidden, can the walk decide when it has read enough? The readout that matters, from james's
note: per-hop recall is above .72 while all-hops is .28–.51, so the gap is whole chains left one read short, or ended
on a wrong turn.

**Constraints.** No threshold on a probability, no read budget, no count. Jev's p values are scored per option, so the
knob-free decision is an argmax over options that include stopping, not "stop if p > x". The only bound on reads is
the pool itself (20 passages), which is physical, not chosen.

**Two stop rules.**
- **S-in (inside the step).** Add one option to the step request the walk already makes: the name request (cheap walk)
  or the pass request (full step) gets "Nothing more: what has been read already answers `question`". The walk stops
  when that option wins the argmax. No extra request; but the request's context is the last read only, so it judges
  completeness without seeing the earlier reads.
- **S-check (a separate check).** After each step, one two-option request with every read passage in context:
  "`question` can be answered from `reads`" against "`question` needs a passage not yet read". Stop on the argmax.
  It sees everything, at the price of one request per step that grows with the reads.

Both are applied to the cheap walk and to the full-step walk, so each step rule is compared under the same stop rule.

**Data.** A fresh draw where the walk can't guess H from the type: MuSiQue train answerable chains, 2-hop, 3hop1 and
4hop1, 80 of each (240), a new seed, disjoint from SR-BX, SR-BE and SR-BH. Fresh-sub-question types stay out, as in
SR-BH.

**Arms** (all from Jev's entry request): cheap and pass, each with S-in, S-check, the oracle H, and the oracle H+1.

**Primary.** All hops, **cheap × S-check − cheap × oracle(H)**, paired bootstrap 95% CI, with input characters per
question beside it. Non-inferiority: lower bound above −.05 (the margin carried from SR-BH).

**Secondary.**
- The same for S-in, and for the pass walk.
- Reads used against H: stopped early, exact, late. Plus all-hops within each.
- All hops per 10k input characters for every arm (james's SR-BH2 measure).
- By hop type, so a rule that only works on 2-hop is visible.

**Predictions.**
- S-in stops too early. It can't see the earlier reads, so on the last read of a 2-hop walk it can't tell that hop 1
  is already in hand, and from a mid-chain read it often believes the answer is near. All-hops well below oracle(H).
- S-check is close to oracle(H): it stops late more than early, since "can be answered" is a high bar. Lower bound
  around −.05, a coin flip on non-inferiority. Input about 1.5× the oracle walk's.
- Stopping late costs less than stopping early, as SR-BH2's spare read showed, so S-check × cheap may beat oracle(H)
  on all-hops while losing per character.

**Risks.**
- S-check's context grows with every read; 4-hop walks that run long could cost several times a 2-hop walk. The
  dry run will price it; if over the cap, the draw shrinks, not the rule.
- "Can be answered" may be judged on surface overlap with the question. Report S-check's decision against the gold
  (did the read set contain every hop when it stopped?) as a confusion table.

**Cost.** To be priced by a dry run with random scores, as SR-BH's. Expect $0.15–0.30 for 240 questions; cap $0.50.
