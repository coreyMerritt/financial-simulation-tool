#!/usr/bin/env bash

set -euo pipefail

# Ensure we're in the project dir
script_dir="$(dirname "$(readlink -f "$0")")"
cd "$script_dir"

# Start script
./.venv/bin/python ./src/main.py "$@"
