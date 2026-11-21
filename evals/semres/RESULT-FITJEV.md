# FITJEV result: Jev's door conductance, fitted on 64 option sets ($0)

*21 Nov 2026, james. Registration: REGISTERED-FITJEV.md. Output: out/fitjev.txt. This is least squares on logit p_Jev,
with a 95% bootstrap over option sets (32 per setting).*

| Term (nats) | SR-JW2: doors hide their links | SR-JW3: doors show their links |
|---|---|---|
| β (per cos unit) | −1.35 [−3.98, +1.13] | +2.24 [−0.57, +5.25] |
| γ_rel ([the relation is r1/r2]) | +0.12 [−0.10, +0.35] | **+0.66 [+0.43, +0.92]** |
| γ_type ([the door is of the answer's type]) | **+1.09 [+0.71, +1.54]** | **+0.70 [+0.28, +1.06]** |
| γ_read ([the door is already read]) | +0.33 [−0.27, +0.98] | **−0.85 [−1.46, −0.29]** |

## What it shows, and what it corrects

- **γ_type is the steadiest term in both settings,** at about +0.7–1.1 nats. Jev's strongest door preference here is
  "this leads to a thing of the asked type".
- **γ_rel needs the door to show its link.** It's about 0 when the door is silent and +0.66 when it names its relation.
  That's the SR-JW2/3 finding, as a coefficient.
  - It's far below bill's MuSiQue 3.7, because the indicators differ.
  - In these worlds about a quarter of all doors carry r1 or r2, so "has the relation" is common and weak.
  - In SR-J, γ was "this is *the* next hop", which is unique.
  - So the 3.7 is the *joint* relation-and-type-and-identity term. These worlds split it.
- **Correction: the read mask isn't −∞.**
  - I wrote "− ∞·[already read]" in RESULT-SRJW and SRJW3. The fit says otherwise: γ_read is −0.85 nats when doors
    show their links, and indistinguishable from 0 when they don't.
  - The low way-back share (.09 against .29) was relative to the theory, which over-credits the start (high cos, and r1
    from both ends). It was not an absolute refusal.
  - Jev discounts a read passage, and does so only when the texts make it visibly redundant.
- **β (similarity) can't be estimated here.** The intervals are wide and change sign. These worlds don't vary cos enough
  to pin it, so I'm not reporting a value.

## Postmortem

- *Predicted:*
  - γ_read well below 0 in both: **wrong** for SR-JW2.
  - γ_type above 0 in both: right.
  - γ_rel larger in JW3: right.
  - β ≈ 1: not identifiable.
- *What it cost me:* two results stated "−∞·[already read]" from shares, without a fit. I'm amending both lines to cite
  this result. Lesson: a share ratio against a theory is not a coefficient. Fit before naming a term.
- *For THEORY-SR (bill's draft):* the conductance is exp(β·cos + γ_rel·relation + γ_type·type + γ_read·read), with
  γ_read ≈ −0.85 and γ_type ≈ +0.7–1.1, all in nats. γ_rel depends on whether the door shows its link.
