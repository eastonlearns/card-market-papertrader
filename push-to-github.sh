#!/usr/bin/env bash
# One-shot: build a clean commit history for GrailBot and push it to GitHub.
# Run this from inside the app/ folder on your own machine:
#     bash push-to-github.sh
#
# Prereqs: git installed, and you're authenticated to GitHub (gh auth login,
# a credential manager, or an SSH key). Nothing here needs your password inline.
set -euo pipefail

REMOTE="https://github.com/eastonlearns/card-market-papertrader.git"

cd "$(dirname "$0")"
echo "Repo root: $(pwd)"

# Clear any partial/broken .git (e.g. one left by a sandbox), start fresh.
rm -rf .git
rm -f grailbot.db
find . -name __pycache__ -type d -prune -exec rm -rf {} + 2>/dev/null || true

git init -q
git checkout -q -b main

git add pyproject.toml requirements.txt .gitignore LICENSE .env.example
git commit -q -m "chore: scaffold project (packaging, license, env template)"

git add grailbot/__init__.py grailbot/config.py grailbot/models.py \
        grailbot/catalog.py grailbot/resolver.py grailbot/data/catalog.sample.json
git commit -q -m "feat(identity): card-identity resolver with confidence gating"

git add grailbot/sources.py grailbot/scoring.py grailbot/pipeline.py \
        grailbot/storage.py grailbot/sample_data.py grailbot/cli.py grailbot/__main__.py
git commit -q -m "feat(engine): data sources, edge scoring, pipeline, storage, CLI"

git add grailbot/ledger.py
git commit -q -m "feat(ledger): immutable hash-chained paper-trading ledger"

git add tests
git commit -q -m "test: resolver, scoring, pipeline, and ledger suites"

git add README.md ARCHITECTURE.md ROADMAP.md CONTRIBUTING.md \
        CODE_OF_CONDUCT.md AGENTS.md CHANGELOG.md docs
git commit -q -m "docs: README, architecture, roadmap, and governance"

git add .github
git commit -q -m "ci: GitHub Actions test workflow + issue/PR templates"

echo; echo "Commit history:"; git log --oneline

git remote add origin "$REMOTE" 2>/dev/null || git remote set-url origin "$REMOTE"
echo; echo "Pushing to $REMOTE ..."
git push -u origin main

echo; echo "Done. Open the repo and check the green CI badge once Actions finishes."
