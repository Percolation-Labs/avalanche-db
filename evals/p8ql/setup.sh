#!/bin/sh
# evals/p8ql/setup.sh RUN_DIR ARM -- a fresh billing store for one agent run, and an `ava`
# on PATH that allows only the arm's commands and logs every call to RUN_DIR/calls.log.
#   ARM=p8ql      ava query, ava query --explain, ava schema
#   ARM=baseline  ava search, ask, step, why, edges
set -e
run="$1"; arm="$2"; root="$(cd "$(dirname "$0")/../.." && pwd)"
real="$root/target/release/ava"
rm -rf "$run" && mkdir -p "$run/bin"
cp -R "$root/examples/billing" "$run/billing"
rm -rf "$run/billing/repo" "$run/billing/avalanche.toml" "$run/billing/.avalanche/store.redb"
(cd "$run/billing" && ./make.sh >/dev/null && "$real" init >/dev/null && "$real" ingest >/dev/null && AVALANCHE_MODEL_KEY= "$real" dream >/dev/null)
case "$arm" in
  p8ql) allow="query schema" ;;
  baseline) allow="search ask step why edges" ;;
  *) echo "arm is p8ql or baseline" >&2; exit 2 ;;
esac
cat > "$run/bin/ava" <<SHIM
#!/bin/sh
printf '%s\n' "\$*" >> "$run/calls.log"
case " $allow " in *" \$1 "*) ;; *) echo "ava \$1: not available in this arm; use one of: $allow" >&2; exit 2 ;; esac
cd "$run/billing" && exec "$real" "\$@"
SHIM
chmod +x "$run/bin/ava"
: > "$run/calls.log"
echo "$run ready: PATH=$run/bin:\$PATH, arm $arm ($allow)"
