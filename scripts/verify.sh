#!/usr/bin/env bash
# Release gate: run before every push that claims "done".
# Stdlib only, no install step, no network. Three checks: the package imports,
# the unittest suite passes, and the CLI does real work offline.
set -uo pipefail
cd "$(dirname "$0")/.."

fail() { echo "GATE FAILED: $*"; exit 1; }

out=$(mktemp)
trap 'rm -f "$out"' EXIT

echo "== check 1/3: import"
python3 -c "import reportforge" || fail "import"

echo "== check 2/3: unittest suite"
python3 -m unittest discover -s tests -q || fail "tests"

echo "== check 3/3: CLI smoke: parse the sample Burp export into PDF + markdown"
workdir=$(mktemp -d)
python3 -m reportforge --burp sample-issues.xml --out "$workdir/report.pdf" --md "$workdir/report.md" > "$out" 2>&1 || { cat "$out"; rm -r "$workdir"; fail "cli exit"; }
[ -s "$workdir/report.pdf" ] || fail "no PDF written"
[ -s "$workdir/report.md" ] || fail "no markdown written"
grep -q "finding" "$out" || { cat "$out"; fail "cli output: expected a finding count"; }
echo "smoke ok: $(grep -m1 finding "$out") | pdf $(wc -c < "$workdir/report.pdf") bytes"
rm -r "$workdir"
echo "ALL CHECKS PASSED"
