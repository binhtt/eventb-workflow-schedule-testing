#!/usr/bin/env bash
# Publish this reviewed artifact to the authenticated user's own GitHub account.
set -euo pipefail

repo_name="eventb-workflow-testing"
visibility="private"
while (($#)); do
    case "$1" in
        --public) visibility="public"; shift ;;
        --private) visibility="private"; shift ;;
        --name)
            if (($# < 2)); then
                echo "--name requires a repository name." >&2
                exit 2
            fi
            repo_name="$2"; shift 2 ;;
        *)
            echo "Usage: bash scripts/publish_github.sh [--private|--public] [--name REPO]" >&2
            exit 2 ;;
    esac
done
if [[ ! "$repo_name" =~ ^[A-Za-z0-9][A-Za-z0-9._-]*$ ]]; then
    echo "Use a repository name without an owner or URL." >&2
    exit 2
fi

root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
command -v gh >/dev/null || { echo "Install GitHub CLI first." >&2; exit 1; }
command -v git >/dev/null || { echo "Install Git first." >&2; exit 1; }
gh auth status
python3 "$root/scripts/verify_artifact.py"

profile="$(gh api user --jq '[.login, (.id|tostring), (.name // .login)] | @tsv')"
IFS=$'\t' read -r login account_id author_name <<< "$profile"
if [[ -z "$login" || ! "$account_id" =~ ^[0-9]+$ ]]; then
    echo "Cannot resolve the authenticated GitHub account." >&2
    exit 1
fi
target="$login/$repo_name"
if gh repo view "$target" >/dev/null 2>&1; then
    echo "Repository $target already exists. Choose a different --name." >&2
    exit 1
fi

if [[ ! -d "$root/.git" ]]; then
    git -C "$root" init -b main
fi
if ! git -C "$root" config user.name >/dev/null; then
    git -C "$root" config user.name "$author_name"
fi
if ! git -C "$root" config user.email >/dev/null; then
    git -C "$root" config user.email "$account_id+$login@users.noreply.github.com"
fi

if ! git -C "$root" rev-parse --verify HEAD >/dev/null 2>&1; then
    git -C "$root" add --all
    git -C "$root" commit -m "Add reproducible Event-B workflow verification artifact"
elif [[ -n "$(git -C "$root" status --porcelain)" ]]; then
    echo "Review and commit the local changes before publishing." >&2
    exit 1
fi

gh repo create "$target" "--$visibility" \
    --description "Research artifact for Formal Verification and Schedule-Based Testing of Multi-Agent Workflows" \
    --source "$root" --remote origin --push
gh repo edit "$target" \
    --add-topic event-b \
    --add-topic formal-verification \
    --add-topic model-based-testing \
    --add-topic multi-agent-systems \
    --add-topic reproducibility
gh repo view "$target" --json url --jq .url
