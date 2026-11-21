# SR-E2 (registered 21 Nov, before scoring): confirming the ordered entry-then-door choice on fresh questions

*bill. $0, no Jev calls. Script `sre_cosdoor.py`, the same code as SR-E's unregistered check, with a start offset.*

**Why.** In SR-E's unregistered check, `cosdoor` (the entry by cosine, then the entry's key-door link) landed both hops in
.620, against `door`'s .465 and `cos`'s .200. That arm was chosen after seeing SR-E's results, so it needs fresh data.

**Data.** MuSiQue dev answerable 2-hop questions 201–700 in file order: 500 questions none of SR-K or SR-E has scored.

**Arms.** `cos`, `door`, `vec` and `cosdoor`, exactly as in SR-E with amendment 1 and its unregistered check. No
parameters.

**Bar.** Confirmed if, on `both`, `cosdoor − door` has a 95% paired bootstrap CI lower bound above 0, and so does
`cosdoor − cos`.

**Prediction.**
- cosdoor ≈ .55–.65.
- door ≈ .40–.50.
- cos ≈ .20.
- cosdoor's entry rate equals cos's, by construction.
