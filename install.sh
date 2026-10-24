#!/bin/sh
# Install ava, one binary with no server, into ~/.local/bin:
#   curl -fsSL https://raw.githubusercontent.com/Percolation-Labs/avalanche-db/main/install.sh | sh
# AVA_BIN_DIR changes where it goes; AVA_URL where the release is read from.
set -eu
repo="Percolation-Labs/avalanche-db"
bin_dir="${AVA_BIN_DIR:-$HOME/.local/bin}"
case "$(uname -s)-$(uname -m)" in
  Darwin-arm64) target=aarch64-apple-darwin ;;
  Darwin-x86_64) target=x86_64-apple-darwin ;;
  Linux-x86_64) target=x86_64-unknown-linux-musl ;;
  Linux-aarch64 | Linux-arm64) target=aarch64-unknown-linux-musl ;;
  *)
    echo "ava: no prebuilt binary for $(uname -s) $(uname -m); build one with" >&2
    echo "  cargo install --locked --git https://github.com/$repo" >&2
    exit 1
    ;;
esac
url="${AVA_URL:-https://github.com/$repo/releases/latest/download}/ava-$target.tar.gz"
tmp=$(mktemp -d)
trap 'rm -rf "$tmp"' EXIT
curl -fsSL "$url" -o "$tmp/ava.tar.gz"
curl -fsSL "$url.sha256" -o "$tmp/ava.sha256"
want=$(cut -d' ' -f1 <"$tmp/ava.sha256")
if command -v shasum >/dev/null; then got=$(shasum -a 256 <"$tmp/ava.tar.gz"); else got=$(sha256sum <"$tmp/ava.tar.gz"); fi
if [ "$want" != "${got%% *}" ]; then
  echo "ava: $url does not match its checksum; nothing installed" >&2
  exit 1
fi
tar -xzf "$tmp/ava.tar.gz" -C "$tmp"
mkdir -p "$bin_dir"
install -m 755 "$tmp/ava" "$bin_dir/ava"
echo "installed $("$bin_dir/ava" --version) at $bin_dir/ava"
case ":$PATH:" in
  *":$bin_dir:"*) ;;
  *) echo "add $bin_dir to your PATH to run it as ava" ;;
esac
