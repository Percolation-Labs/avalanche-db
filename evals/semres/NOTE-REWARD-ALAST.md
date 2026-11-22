# Look (22 Nov, $0, post hoc): the bridge reward on A-last, the answer-passage measure

*bill. Script `srba.py`, output `out/srba.txt`, `out/srba.json`. Sirsh at 17:07Z: optimise the dreaming reward toward
the answer being in what the walk returns. A-last (james, #98): the returned set contains the gold last-hop passage
(on 2-hop, h2), which holds the answer in every cached question. SR-BC's data, split, walk and fixed-point update,
unchanged. A look on SR-BC's test half, which was already scored on both hops, so it isn't a registered result.*

| reward the update learns from | learn-half rate (its own measure) | test A-last | test both hops | gained / lost on A-last |
|---|---|---|---|---|
| none | .463 / .534 | .534 | .401 | |
| gold pair (SR-BC's T*) | .471 | .551 | .418 | 8 / 0 |
| **A-last** | .581 | **.556** | .423 | 10 / 0 |

- **On A-last, SR-BC's reward helps exactly as it did on both hops**: +.017 [+.007, +.031], the same 8 questions
  gained, none lost. The questions it fixes are ones where the step was missing the answer passage.
- **Rewarding A-last directly is a little better**: +.022 [+.009, +.037] over none, and +.004 [+.000, +.011] over the
  gold-pair reward. It converges the same way (a fixed point after two passes), and loses nothing.
- **Rewarding the answer passage doesn't cost the chain**: both hops also rises (.423). On 2-hop the step's only job is
  to reach h2 from h1, so the two rewards mostly agree; they can diverge only on longer chains, where a walk can skip.

**What it means for dreaming.** The reward can be switched to Sirsh's target at no cost on 2-hop. The live question is
longer chains: a reward on A-last will also reward the skips that SR-BH found reach the answer passage without the
bridge. Whether that's good is the reader question (#99's AC): does a reader still pick the right answer when the
bridge is missing?

**Scope.** MuSiQue train 2-hop, the structural walk, gold labels as the stand-in for a confirmed answer.
