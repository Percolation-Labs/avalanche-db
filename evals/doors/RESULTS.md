# Door refactor parity (specs/doors.md)

**Result: the refactored walk reproduces the old one exactly.** All 50 of fixture-musique's recorded search
orders were walked by the pre-refactor engine (`2d29bb7`) and by the refactored one (`0fb4827`). The output files
are byte-identical: 25,000 reads and 19,367 doors opened, the same documents in the same order.

- **How:** `parity.py` drives `midb lab serve` and answers every judgement with a fixed score per door (SHA-256
  of its key), so neither run calls a model. The settings are the product's V0, `gate: 0.5` and
  `order: per_target`. In the new engine the gate is `Gated`, a filter.
- **Not compared:** `keys_read`, since the default labeller reads each term's postings, and `batches`, which
  the old engine does not have.
- **Data:** the fixture is `~/.cache/walklab/fixture-musique` (graphs.jsonl and search.jsonl, 31 Oct 2026). It
  stays local and is not committed. `tests/doors.rs` holds the same check, in CI, against a golden file from the
  old engine on a synthetic graph: 12 walks over 4 questions and the three V0 orders.

To rerun:

```console no-test
$ midb lab import ~/.cache/walklab/fixture-musique/graphs.jsonl --store mq.redb
$ python3 -I evals/doors/parity.py <old midb> mq.redb ~/.cache/walklab/fixture-musique/search.jsonl old.jsonl
$ python3 -I evals/doors/parity.py <new midb> mq.redb ~/.cache/walklab/fixture-musique/search.jsonl new.jsonl
$ cmp old.jsonl new.jsonl
```
