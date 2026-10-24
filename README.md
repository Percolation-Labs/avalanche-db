# Avalanche DB (spike)

A research engine for the Percolate pattern: typed quads with valid time and transaction
time in an append-only per-tenant log, indexed on redb in four tenant-first key orders,
queried as iterative sessions whose every step lands in a usage graph. Spec: Sirsh's
Percolate piece ld-b608b2c9691f. Card: REM-1172. Single node; no distribution yet.

    cargo test
    cargo build --release && A=target/release/ava
    $A ingest git ~/code/p8-subsystems --rev origin/main      # commits, parents, files, cards named
    $A ingest cards ~/code/p8-subsystems --rev origin/main    # board cards: the decisions
    $A ingest facts data/percolate-slice.jsonl                 # one question, three packages' claims
    $A ingest facts data/extracted-links.jsonl                 # claim -informs-> card, model-written
    $A ingest facts data/rejected-links.jsonl                  # one link retracted: the rejection is a fact
    $A ask should memory be placed by the user                 # -> a session and a token
    $A step <token> --follow answers,informs,mentions,makes    # one step; prints the next token
    $A edges claim:rp-e2154adb/C4 --as-of 4                    # what the graph knew at T4
    $A usage                                                   # metrics from the usage graph
    $A log [T]                                                 # transactions, or one's facts
