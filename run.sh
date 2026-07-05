#!/usr/bin/env bash
set -e
cd "$(dirname "$0")"
uv run uvicorn app.main:app --reload
