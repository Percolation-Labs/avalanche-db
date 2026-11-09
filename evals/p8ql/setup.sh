#!/bin/sh
# evals/p8ql/setup.sh RUN_DIR ARM -- a fresh billing store for one agent run, and an `midb`
# on PATH that allows only the arm's commands and logs every call to RUN_DIR/calls.log.
# With STORE set to a folder holding avalanche.toml and .avalanche/, the run gets a copy of
# that store instead (history/build.sh makes one from Percolate's history). TRACE=after
# prints a walk's answer before its plan and trace (the trace-placement variant).
#   ARM=p8ql      midb query, midb query --explain, midb schema
#   ARM=baseline  midb search, ask, step, why, edges
set -e
run="$1"; arm="$2"; root="$(cd "$(dirname "$0")/../.." && pwd)"
real="${MIDB:-$root/target/release/midb}"   # MIDB= another build, for an A/B of two versions
rm -rf "$run" && mkdir -p "$run/bin"
if [ -n "$STORE" ]; then
  mkdir -p "$run/store" && cp -R "$STORE/avalanche.toml" "$STORE/.avalanche" "$run/store/"
else
  cp -R "$root/examples/billing" "$run/store"
  rm -rf "$run/store/repo" "$run/store/avalanche.toml" "$run/store/.avalanche/store.redb"
  (cd "$run/store" && ./make.sh >/dev/null && "$real" init >/dev/null && "$real" ingest >/dev/null && AVALANCHE_MODEL_KEY= "$real" dream >/dev/null)
fi
case "$arm" in
  p8ql) allow="query schema" ;;
  baseline) allow="search ask step why edges" ;;
  *) echo "arm is p8ql or baseline" >&2; exit 2 ;;
esac
cat > "$run/bin/midb" <<SHIM
#!/bin/sh
printf '%s\n' "\$*" >> "$run/calls.log"
case " $allow " in *" \$1 "*) ;; *) echo "midb \$1: not available in this arm; use one of: $allow" >&2; exit 2 ;; esac
cd "$run/store" && AVALANCHE_TRACE="${TRACE:-}" exec "$real" "\$@"
SHIM
chmod +x "$run/bin/midb"
: > "$run/calls.log"
echo "$run ready: PATH=$run/bin:\$PATH, arm $arm ($allow)"
