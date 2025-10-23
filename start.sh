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
venv_existed=1
if [[ ! -d .venv ]]; then
  python3 -m venv .venv
  venv_existed=0
fi
if [[ -f .venv/bin/activate ]]; then
  source .venv/bin/activate
  pip install --upgrade pip setuptools wheel
fi
if [[ ! $venv_existed -eq 1 ]]; then
  pip install .
fi

# Start script -- pass args
python3 ./src/main.py $@

