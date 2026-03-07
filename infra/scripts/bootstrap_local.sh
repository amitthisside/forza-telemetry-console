#!/usr/bin/env bash
set -euo pipefail

cp -n .env.example .env || true
make bootstrap
make up
