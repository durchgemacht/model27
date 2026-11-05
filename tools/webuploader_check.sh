#!/usr/bin/env bash
# Host tests of the uploader page (docs/uploader/): tools/uploader/*.test.js with node. elektron.test.js checks the
# file protocol and the sample format, page.test.js drives app.js against a stand-in Model:Cycles.
set -euo pipefail
cd "$(dirname "$0")/.."
command -v node >/dev/null || { echo "node is needed for this test"; exit 1; }

for t in tools/uploader/*.test.js; do
  printf '%s: ' "$t"
  node "$t"
done
echo "OK: the uploader's scripts pass their host tests"
