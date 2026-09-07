#!/usr/bin/env bash
# Make a fresh worktree runnable: repair the branch's tracking, pick the model
# checkout this branch builds against, allocate ports, write Claude Code's
# sandbox settings, install deps, and open its tmux dev session.
# Idempotent on purpose: wt runs it from post_create AND post_checkout (some wt
# builds fire both on create), and you can re-run it by hand to refresh.
#   scripts/wt-setup.sh          from inside a worktree
#   (wt hooks call it with WT_PATH / WT_BRANCH exported)
# WT_TCM_BRANCH, exported by wt-new.sh --model, asks for a paired worktree of
# transition-compass-model on that branch and points this one at it.
set -euo pipefail
ROOT="${WT_PATH:-$(git rev-parse --show-toplevel)}"
SCRIPTS="$(dirname "$(readlink -f "$0")")"
. "$SCRIPTS/wt-lib.sh"
MAIN="$(main_checkout)"   # not $WT_MAIN: wt points that at whichever worktree holds `dev`
BRANCH="${WT_BRANCH:-$(current_branch)}"
cd "$ROOT"
[ "$ROOT" != "$MAIN" ] || die "run from a worktree, not the main checkout"
# Prefer the branch's own copy of the tooling; fall back to the main checkout's for
# branches that predate it.
tooling() { [ -f "$ROOT/scripts/$1" ] && echo "$ROOT/scripts/$1" || echo "$MAIN/scripts/$1"; }

echo "==> worktree $ROOT ($BRANCH)"

# 0. Tracking. `wt create <branch> origin/dev` cuts the branch from a
#    remote-tracking ref, and git's default autoSetupMerge then points the new
#    branch's upstream at origin/dev. `git pull` there rebases the branch onto
#    dev instead of fetching its own commits, the next push is refused as
#    non-fast-forward, and `git pull` still answers "up to date" because it is
#    comparing against dev. `simple` only tracks a remote branch of the same
#    name, and push.autoSetupRemote sets the upstream on the first push, so a
#    new branch gets the right one or none at all. Repo-wide config, but written
#    here so every checkout of this repo gets it.
git config branch.autoSetupMerge simple || echo "note: could not set branch.autoSetupMerge"
git config push.autoSetupRemote true || echo "note: could not set push.autoSetupRemote"
if git show-ref --verify --quiet "refs/remotes/origin/$BRANCH"; then
  git branch --set-upstream-to="origin/$BRANCH" "$BRANCH" >/dev/null 2>&1 ||
    echo "note: could not track origin/$BRANCH"
elif [ "$(git config --get "branch.$BRANCH.merge" || true)" != "refs/heads/$BRANCH" ]; then
  # Not pushed yet: no upstream at all beats one pointing at another branch.
  git branch --unset-upstream "$BRANCH" >/dev/null 2>&1 || true
fi

# 1. Gitignored dev files aren't in the branch; the main checkout's copies on
#    disk are the source. Never overwrite what the worktree already has. The
#    root .env is tracked, so git brought it; backend/.env is optional (the
#    settings have defaults) and usually absent.
for f in CLAUDE.md backend/.env; do
  if [ ! -e "$f" ] && [ -e "$MAIN/$f" ]; then
    mkdir -p "$(dirname "$f")"; cp "$MAIN/$f" "$f"; echo "seeded $f"
  fi
done

# 2. The model checkout this worktree builds against. The backend imports
#    transition_compass_model; backend/pyproject.toml pins the PyPI release, and
#    a dev checkout overrides it with an editable install (step 6).
#    Default: the model's main checkout, shared read-only with every worktree.
#    `wtgo <branch> --model <model-branch>` (WT_TCM_BRANCH) instead gives this
#    worktree its own model worktree, so one agent can change both repos.
prev_tcm_path=""; prev_tcm_branch=""
if [ -f .env.worktree ]; then
  prev_tcm_path="$(sed -n 's/^TCM_PATH=//p' .env.worktree)"
  prev_tcm_branch="$(sed -n 's/^TCM_BRANCH=//p' .env.worktree)"
fi
TCM_MAIN_PATH="$(tcm_main)" || die "the backend needs a transition-compass-model checkout"
TCM_BRANCH="${WT_TCM_BRANCH:-$prev_tcm_branch}"
if [ -n "$TCM_BRANCH" ]; then
  TCM_PATH="$(ROOT="$TCM_MAIN_PATH" worktree_path_for "$TCM_BRANCH")"
  if [ -z "$TCM_PATH" ]; then
    echo "==> model worktree for $TCM_BRANCH in $TCM_MAIN_PATH"
    # Runs in the model repo, so it fires that repo's own .wt.toml hooks (its
    # session comes up too). --format json and stdout to stderr: in text mode wt
    # prints an auto-navigation marker its shell wrapper follows, and the shell
    # that called wtgo here would end up in the model worktree.
    if git -C "$TCM_MAIN_PATH" show-ref --verify --quiet "refs/heads/$TCM_BRANCH" ||
       git -C "$TCM_MAIN_PATH" show-ref --verify --quiet "refs/remotes/origin/$TCM_BRANCH"; then
      (cd "$TCM_MAIN_PATH" && wt --format json checkout "$TCM_BRANCH" >&2)
    else
      # A local ref can be stale; refresh origin/main so the new branch is cut
      # from a current base.
      ( cd "$TCM_MAIN_PATH"
        git fetch --quiet origin main || echo "warning: fetch failed, using cached origin/main" >&2
        wt --format json create "$TCM_BRANCH" origin/main >&2 )
    fi
    TCM_PATH="$(ROOT="$TCM_MAIN_PATH" worktree_path_for "$TCM_BRANCH")"
  fi
  [ -n "$TCM_PATH" ] || die "could not create a model worktree for $TCM_BRANCH"
else
  # An earlier run may have recorded a path; keep it only if it still exists.
  TCM_PATH="$prev_tcm_path"
  [ -n "$TCM_PATH" ] && [ -d "$TCM_PATH" ] || TCM_PATH="$TCM_MAIN_PATH"
fi
echo "model: $TCM_PATH${TCM_BRANCH:+ ($TCM_BRANCH)}"

# 3. Ports and names. A previous run may have picked ports (the servers in the
#    session listen on them): keep them. A fresh worktree gets the hashed pair,
#    or the next free one (branch_ports in wt-lib.sh).
prev_backend=""; prev_frontend=""
if [ -f .env.worktree ]; then
  prev_backend="$(sed -n 's/^BACKEND_PORT=//p' .env.worktree)"
  prev_frontend="$(sed -n 's/^FRONTEND_PORT=//p' .env.worktree)"
fi
if [ -n "$prev_backend" ] && [ -n "$prev_frontend" ]; then
  BACKEND_PORT="$prev_backend"; FRONTEND_PORT="$prev_frontend"
else
  branch_ports "$BRANCH"
fi
SLUG="$(slug "$BRANCH")"
cat > .env.worktree <<ENV
# Generated by scripts/wt-setup.sh — this worktree's private settings (gitignored).
# tmux-dev.sh exports these in every pane; re-run wt-setup.sh to refresh.
WT_BRANCH=$BRANCH
WT_SLUG=$SLUG
BACKEND_PORT=$BACKEND_PORT
FRONTEND_PORT=$FRONTEND_PORT
# The transition-compass-model checkout installed editable in backend/.venv.
# TCM_BRANCH is set only when this worktree has a model worktree of its own.
TCM_PATH=$TCM_PATH
TCM_BRANCH=$TCM_BRANCH
# uv re-syncs the venv from the lockfile before every \`uv run\`, which puts the
# PyPI transition-compass-model back over the editable one. Off in a worktree.
UV_NO_SYNC=1
ENV
echo "ports: backend $BACKEND_PORT, frontend $FRONTEND_PORT"

# 4. Nothing else to wire: quasar.config.ts runs in Node and reads
#    FRONTEND_PORT (and BACKEND_PORT for its /api proxy) from the environment,
#    and the Makefiles read BACKEND_PORT / TCM_PATH. No env file to write.

# 5. Claude Code runs sandboxed here with the ask/deny rules from the template.
#    .claude/settings.local.json is gitignored, so it never reaches a commit.
#    Always read the template from the main checkout, not the branch: a branch
#    forked before a template fix would otherwise write the old rules back, and
#    a feature branch should not be able to change Claude's permissions.
#    additionalDirectories is added only for a paired model worktree: with the
#    shared model main checkout, the agent may read it (the sandbox allows
#    reads) but must not write in a checkout other worktrees build against.
#    Not fatal: a re-run from inside a sandboxed agent cannot write this file
#    (Claude blocks an agent editing its own permissions), and in that case the
#    file is already there.
mkdir -p .claude
render_settings() {
  local tpl="$MAIN/scripts/claude-worktree-settings.json"
  if [ -n "$TCM_BRANCH" ] && command -v jq >/dev/null 2>&1; then
    jq --arg d "$TCM_PATH" '.permissions.additionalDirectories = [$d]' "$tpl"
  else
    cat "$tpl"
  fi
}
if render_settings > .claude/settings.local.json.tmp 2>/dev/null &&
   mv .claude/settings.local.json.tmp .claude/settings.local.json 2>/dev/null; then
  echo "wrote .claude/settings.local.json"
else
  rm -f .claude/settings.local.json.tmp
  echo "note: could not write .claude/settings.local.json (kept the existing one; re-run wt-setup.sh from a terminal to refresh it)"
fi

# 6. Dependencies. The root install is what puts lefthook in this worktree:
#    the shared pre-commit hook looks for node_modules/lefthook at the root of
#    the checkout that commits, and exits without running anything when it is
#    missing. The editable model install runs every time, not just on a fresh
#    venv: it is quick, and it re-points the venv after --model changed TCM_PATH.
#    The interpreter is pinned on purpose. uv, run from backend/, does not look
#    up the tree for the repo's root .python-version, so a fresh sync takes the
#    newest python on the machine (3.14 today). orjson ships no wheel for that
#    one and falls back to building it from source, which downloads a Rust
#    toolchain. 3.12.7 is what .python-version and the Docker image already say.
PYVER="$(cat "$ROOT/.python-version" 2>/dev/null || echo 3.12)"
[ -d node_modules ] || npm ci
[ -d frontend/node_modules ] || (cd frontend && npm ci)
[ -d backend/.venv ] || (cd backend && uv sync --frozen --python "$PYVER")
(cd backend && uv pip install --quiet --editable "$TCM_PATH") &&
  echo "model installed editable from $TCM_PATH"
npx --no-install lefthook install >/dev/null 2>&1 || echo "note: lefthook install failed, commits will run no hooks here"

# 7. Detached tmux session "<repo>/<branch>"; switch to it with prefix+s.
ROOT="$ROOT" "$(tooling tmux-dev.sh)" --no-attach   # ROOT: the script may be the main checkout's copy
