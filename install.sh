#!/bin/sh
# Install midb, one binary with no server, into ~/.local/bin:
#   curl -fsSL https://raw.githubusercontent.com/Percolation-Labs/avalanche-db/main/install.sh | sh
# MIDB_BIN_DIR changes where it goes; MIDB_URL where the release is read from.
# From a clone, with no release and no network: ./install.sh --local builds it here, packs it as a release
# would, and installs that, through the same checksum check.
set -eu
repo="Percolation-Labs/avalanche-db"
bin_dir="${MIDB_BIN_DIR:-$HOME/.local/bin}"
case "$(uname -s)-$(uname -m)" in
  Darwin-arm64) target=aarch64-apple-darwin ;;
  Darwin-x86_64) target=x86_64-apple-darwin ;;
  Linux-x86_64) target=x86_64-unknown-linux-musl ;;
  Linux-aarch64 | Linux-arm64) target=aarch64-unknown-linux-musl ;;
  *)
    echo "midb: no prebuilt binary for $(uname -s) $(uname -m); build one with" >&2
    echo "  cargo install --locked --git https://github.com/$repo" >&2
    exit 1
    ;;
esac
tmp=$(mktemp -d)
trap 'rm -rf "$tmp"' EXIT
if [ "${1:-}" = "--local" ]; then
  here=$(cd "$(dirname "$0")" && pwd)
  (cd "$here" && ${CARGO:-cargo} build --release --locked --quiet)
  mkdir -p "$tmp/release"
  cp "${MIDB_LOCAL_BIN:-$here/target/release/midb}" "$tmp/release/midb"
  (cd "$tmp/release" && tar -czf "midb-$target.tar.gz" midb && rm midb)
  if command -v shasum >/dev/null; then sum=$(shasum -a 256 <"$tmp/release/midb-$target.tar.gz"); else sum=$(sha256sum <"$tmp/release/midb-$target.tar.gz"); fi
  echo "${sum%% *}  midb-$target.tar.gz" >"$tmp/release/midb-$target.tar.gz.sha256"
  MIDB_URL="file://$tmp/release"
fi
url="${MIDB_URL:-https://github.com/$repo/releases/latest/download}/midb-$target.tar.gz"
curl -fsSL "$url" -o "$tmp/midb.tar.gz"
curl -fsSL "$url.sha256" -o "$tmp/midb.sha256"
want=$(cut -d' ' -f1 <"$tmp/midb.sha256")
if command -v shasum >/dev/null; then got=$(shasum -a 256 <"$tmp/midb.tar.gz"); else got=$(sha256sum <"$tmp/midb.tar.gz"); fi
if [ "$want" != "${got%% *}" ]; then
  echo "midb: $url does not match its checksum; nothing installed" >&2
  exit 1
fi
tar -xzf "$tmp/midb.tar.gz" -C "$tmp"
mkdir -p "$bin_dir"
install -m 755 "$tmp/midb" "$bin_dir/midb"
echo "installed $("$bin_dir/midb" --version) at $bin_dir/midb"
case ":$PATH:" in
  *":$bin_dir:"*) ;;
  *) echo "add $bin_dir to your PATH to run it as midb" ;;
esac
