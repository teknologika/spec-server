#!/bin/bash
set -euo pipefail

# Enforce rules
for arg in "$@"; do
  if [[ "$arg" == "--no-verify" ]]; then
    echo "❌ --no-verify is forbidden. Fix the hook failure instead."
    exit 1
  fi
done

# Ensure GH CLI is available
if ! command -v gh >/dev/null 2>&1; then
  echo "❌ GitHub CLI (gh) is required for CI status checking."
  exit 1
fi

case "$1" in
  commit)
    shift
    if [[ " $* " != *" -m "* ]]; then
      echo "❌ You must provide a commit message with -m."
      exit 1
    fi
    echo "✅ Committing all tracked changes..."
    git commit -a "$@"
    ;;
  push)
    shift
    echo "🚀 Pushing to remote..."
    git push "$@"
    echo "⏳ Waiting for GitHub Actions to pass..."
    gh run watch --exit-status || {
      echo "❌ CI failed. Fix before continuing."
      exit 1
    }
    ;;
  *)
    echo "🤖 Unknown safe-git command: $1"
    echo "Usage: ./scripts/safe-git.sh [commit|push] [args]"
    exit 1
    ;;
esac