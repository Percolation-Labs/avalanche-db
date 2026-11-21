# SR-E result: a key-door pair lands the two-hop chain 2.3× as often as cosine, but the entry should still come from cosine

*21 Nov 2026, bill. Registered at 15aa825, with amendment 1 (james's review) at e90d8c1, before scoring. $0, with no Jev
calls. Output is in `out/sre.txt`; the unregistered check is in `out/sre-cosdoor.txt`.*

**Serves.** THEORY-SR item 2, the entry hop. Can the graph's own key doors pick the entry together with its link, so
that a walk lands on a 2-hop chain rather than on one passage?

**Result: the bar passes on the primary.** The measure is the pair landing {hop 1, hop 2}, on 200 MuSiQue 2-hop pools of
20 passages, with 95% paired bootstrap CIs.

| arm | both hops (primary) | entry is hop 1 | hop 1 in the pair |
|---|---|---|---|
| `cos`: top 2 by cosine | .200 | .780 | .870 |
| `vec`: best pair (v, nearest vector) | .165 | .770 | .815 |
| `door`: best pair (v, its key-door link) | **.465** | .725 | .790 |
| door − cos | **+.265 [+.195, +.335]** | −.055 [−.100, −.015] | −.080 [−.130, −.030] |
| door − vec | **+.300 [+.230, +.370]** | −.045 [−.090, .000] | −.025 [−.080, +.030] |

On questions 41–200 alone (not seen in SR-K), `both` is .425 against .200 and .150. door − cos is +.225 [+.156, +.300]
and door − vec is +.275 [+.200, +.350].

**Predictions.**
- door > vec held.
- vec > cos failed: a nearest-vector link is *worse* than taking the second-best cosine passage.
- The entry effect was within ±.10 as predicted, but negative.
- 'has1 ≥ cos − .05' failed (−.08). Choosing a pair for its joint fit to the question sometimes leaves hop 1 out.

**Worked case.** "Who is the spouse of the Green performer?" `door` picks {Green (Steve Hillage album), Miquette
Giraudy}, linked by `steve hillage`. That's the chain. `cos` picks {The Odd Life of Timothy Green, Green (Steve Hillage
album)}: two passages about "Green", and no spouse.

**Unregistered check (descriptive).** In `cosdoor`, the entry is the top passage by cosine, and the pair is the entry
plus its key-door link.
- It lands both hops in .620, above `door` by +.155 [+.090, +.220], and by +.125 [+.056, +.194] on 41–200.
- It keeps cosine's entry rate (.780).

Choosing in the question's order, first the entry by fit to the question and then the link by the door, beats choosing the
pair jointly. This agrees with james's SR-TW reading: separation lives in the ordered per-step choice, not in one joint
number. It has to be confirmed on fresh questions before it's claimed. SR-E2 is registered for that.

**What this changes.**
- Item 2 sharpens. The entry hop is still cosine's to find; the door doesn't improve it, and the joint pair hurts it
  slightly.
- What the door adds is that, once landed, the walk's second step is found without gold (SR-K's .95 given the true entry,
  and .62 end to end with a cosine entry).
- For repair, the target is a door from a well-landed entry to its link. Pairing the entry choice with the link costs
  entries.

**Caveats.**
- These are in-pool candidates: 20 per question, from MuSiQue's own retrieval set, not the 21,100-passage graph.
- No walker was run. This says which pair the graph and the vectors pick, not whether Jev takes the door when it's
  presented.
- MuSiQue 2-hop only. The df range 2–100 is the graph's own.

**Postmortem.**
- **What went right.** The gold-blind look caught a pair-symmetry bug: the first design named hop 2 as the entry. James's
  review caught a second: linkless passages were linked to pool index 0 by argmax. Both were fixed before scoring.
  Without the second fix, `door` could have won on junk pairs.
- **What I got wrong.** I predicted vec > cos, and the entry effect as neutral. Both missed in the same way: a joint
  pair score optimises fit to the whole question and gives up the best single entry. I didn't think through what the
  pair argmax trades away. The ordered variant should have been an arm from the start. It's the natural reading of
  THEORY-SR, where landing decides and then the next-hop term prices the step.
