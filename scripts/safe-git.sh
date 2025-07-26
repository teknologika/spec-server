#!/bin/bash
set -euo pipefail

# Enforce rules
for arg in "$@"; do
  if [[ "$arg" == "--no-verify" ]]; then
    echo "❌ --no-verify is forbidden. Fix the hook failure instead."
    exit 1
  fi
done

# Check for spec server generated files without permission
check_spec_files() {
  local allow_spec_files=false

  for arg in "$@"; do
    if [[ "$arg" == "--allow-spec-files" ]]; then
      allow_spec_files=true
      break
    fi
  done

  if [[ "$allow_spec_files" == "false" ]]; then
    # Check for any new files in the specs directory that aren't tracked
    local untracked_spec_files=$(git ls-files --others --exclude-standard -- "specs/" ".specs/")

    # Also check for modified spec files
    local modified_spec_files=$(git diff --name-only --cached -- "specs/" ".specs/")

    if [[ -n "$untracked_spec_files" || -n "$modified_spec_files" ]]; then
      echo "❌ Detected spec server files created or modified without explicit permission:"

      if [[ -n "$untracked_spec_files" ]]; then
        echo "New untracked files:"
        echo "$untracked_spec_files"
      fi

      if [[ -n "$modified_spec_files" ]]; then
        echo "Modified files:"
        echo "$modified_spec_files"
      fi

      echo "To proceed, either:"
      echo "  1. Remove these files if they were created without permission"
      echo "  2. Add --allow-spec-files flag to explicitly allow these files"
      return 1
    fi
  fi

  return 0
}

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

    # Check for unauthorized spec files before committing
    if ! check_spec_files "$@"; then
      exit 1
    fi

    # Filter out our custom flag if present
    args=()
    for arg in "$@"; do
      if [[ "$arg" != "--allow-spec-files" ]]; then
        args+=("$arg")
      fi
    done

    echo "✅ Committing all tracked changes..."
    git commit -a "${args[@]}"
    ;;
  push)
    shift

    # Check for unauthorized spec files before pushing
    if ! check_spec_files "$@"; then
      exit 1
    fi

    # Filter out our custom flag if present
    args=()
    for arg in "$@"; do
      if [[ "$arg" != "--allow-spec-files" ]]; then
        args+=("$arg")
      fi
    done

    echo "🚀 Pushing to remote..."
    git push "${args[@]}"
    echo "⏳ Waiting for GitHub Actions to pass..."
    gh run watch --exit-status || {
      echo "❌ CI failed. Fix before continuing."
      exit 1
    }
    ;;
  *)
    echo "🤖 Unknown safe-git command: $1"
    echo "Usage: ./scripts/safe-git.sh [commit|push] [args]"
    echo "       Add --allow-spec-files flag to explicitly allow spec server files"
    exit 1
    ;;
esac
