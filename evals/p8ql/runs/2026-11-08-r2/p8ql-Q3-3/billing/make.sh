#!/bin/sh
# Builds repo/: the billing service's history, with fixed authors and dates so that
# every commit id is the same on every machine.
set -e
cd "$(dirname "$0")"
rm -rf repo && mkdir repo && cd repo
git init -q -b main
F=../files
commit() { # date, message, then files as src:dest pairs
  d="$1T10:00:00Z"; m="$2"; shift 2
  for pair in "$@"; do mkdir -p "$(dirname "${pair#*:}")"; cp "$F/${pair%%:*}" "${pair#*:}"; git add "${pair#*:}"; done
  a="${AUTHOR:-Ana}"; e="$(echo "$a" | tr 'A-Z' 'a-z')@example.com"
  GIT_AUTHOR_NAME="$a" GIT_AUTHOR_EMAIL="$e" GIT_AUTHOR_DATE="$d" \
  GIT_COMMITTER_NAME="$a" GIT_COMMITTER_EMAIL="$e" GIT_COMMITTER_DATE="$d" \
  git -c commit.gpgsign=false commit -q -m "$m"
}
commit 2026-02-10 "invoice: compute totals" total.rs:src/invoice/total.rs
commit 2026-02-11 "invoice: round each line half-up" round-v1.rs:src/invoice/round.rs
commit 2026-03-18 "export: invoices to a spreadsheet" csv-v1.rs:src/export/csv.rs
commit 2026-03-21 "export: keep the currency symbol (BUG-3)" csv-v2.rs:src/export/csv.rs
commit 2026-04-12 "invoice: round totals half-even (ADR-007, BUG-12)" round-v2.rs:src/invoice/round.rs
printf '# Billing\n\nRounding: see ADR-007.\n' > README.md && git add README.md
GIT_AUTHOR_NAME=Ana GIT_AUTHOR_EMAIL=ana@example.com GIT_AUTHOR_DATE=2026-04-13T10:00:00Z \
GIT_COMMITTER_NAME=Ana GIT_COMMITTER_EMAIL=ana@example.com GIT_COMMITTER_DATE=2026-04-13T10:00:00Z \
git -c commit.gpgsign=false commit -q -m "docs: link ADR-007 from the README"
commit 2026-04-14 "tests: forty-line invoice totals" total.rs:tests/long_invoice.rs
# Two more people, so that "who works with Bob?" has an answer (P8QL, specs/p8ql.md).
AUTHOR=Bob commit 2026-04-20 "invoice: say why totals round half-even" round-v3.rs:src/invoice/round.rs
AUTHOR=Bob commit 2026-04-21 "export: amounts with two decimals" csv-v3.rs:src/export/csv.rs
AUTHOR=Chen commit 2026-04-22 "export: name the columns" csv-v4.rs:src/export/csv.rs
echo "built repo/: $(git rev-list --count HEAD) commits"
