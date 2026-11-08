# How the README and the stories are tested

`cargo test --test readme` builds `midb` and runs two stories: the README and
[stories.md](stories.md). Each runs in its own fresh copy of `examples/`. Every `console`
block runs in order, and each command's output is compared with the block, with only
durations and wall-clock times masked. Blocks marked `no-test` are skipped. `needs-key`
blocks run only when `AVALANCHE_MODEL_KEY` is set. Every other block runs with no key, so
`dream` must replay. Commands in `fails` blocks must exit non-zero.

`make.sh` builds the example repository with fixed authors and dates, so commit ids match on
every machine. `cargo test --test install` runs `install.sh --local`. It then publishes the
built binary to a folder, as a release would, and runs `install.sh` against it, including a
tarball whose checksum is wrong. If a story and the binary disagree, the build fails.
