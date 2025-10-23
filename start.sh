#!/usr/bin/env bash

set -e
set -E
set -x

# Ensure we're in the project dir
script_dir="$(dirname "$(readlink -f "$0")")"
cd "$script_dir"

# Handle configs if necessary
if [[ -d "./config" && -d "./config/model" ]]; then
  if [[ ! -d "./config/prod" ]]; then
    mkdir "./config/prod"
  fi
  if [[ ! -d "./config/backup" ]]; then
    mkdir "./config/backup"
  fi

  if ! find "config/prod" -mindepth 1 | grep -q .; then
    cp -r ./config/model/* ./config/prod/
  fi
fi

# Ensure we're in venv
if [[ -f .venv/bin/activate ]]; then
  source .venv/bin/activate
fi

# Start script -- pass args
python3 ./src/main.py $@

