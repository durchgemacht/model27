#!/usr/bin/env bash
# Host tests of the manager page's scripts (docs/manager/, notes/77): tools/manager/*.test.js with node.
# BACKUP_SYX=<a project backup of a Model:Cycles> and OS_SYX=<model-cycles_OS1.13.syx> add the checks against real files.
set -euo pipefail
cd "$(dirname "$0")/.."
command -v node >/dev/null || { echo "node is needed for this test"; exit 1; }

for t in tools/manager/*.test.js; do
  printf '%s: ' "$t"
  node "$t"
done
echo "OK: the manager's scripts pass their host tests"
