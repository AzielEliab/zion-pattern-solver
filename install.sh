#!/usr/bin/env bash
# ZionPattern Solver one-click install. Counted download via this project's Worker.
# Usage: curl -fsSL https://zsolver-download-tracker.vibelock.workers.dev/install.sh | bash
set -euo pipefail

HOST="${ZION_SOLVER_HOST:-https://zsolver-download-tracker.vibelock.workers.dev}"
ASSET="${ZION_SOLVER_ASSET:-zion-pattern-solver-0.2.0.tar.gz}"
WORKDIR="${ZION_SOLVER_HOME:-$HOME/zion-pattern-solver}"

mkdir -p "$WORKDIR"
cd "$WORKDIR"

echo "Downloading counted tarball from ${HOST}/download (User-Agent Mozilla/5.0)…"
curl -fsSL -A 'Mozilla/5.0' "${HOST}/download?asset=${ASSET}" -o "${ASSET}"

tar -xzf "${ASSET}"
DIR="$(find . -maxdepth 1 -type d \( -name 'zion-pattern-solver-*' -o -name 'zion_pattern_solver-*' \) | head -n 1)"
if [ -n "${DIR}" ]; then
  cd "${DIR}"
fi

python3 -m venv .venv
# shellcheck disable=SC1091
. .venv/bin/activate
python -m pip install -U pip
python -m pip install -e .

echo
echo "Installed ZionPattern Solver."
echo "Run:  zion-solver ui"
echo "Then open http://127.0.0.1:8790  (loopback only)"
echo "Author: Aziel Eliab."
