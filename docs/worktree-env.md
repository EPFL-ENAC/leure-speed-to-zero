# Per-worktree dev environment

One branch = one git worktree = one tmux session = one Claude Code agent, with its own
backend and frontend ports and its own model checkout. Nothing is shared between
worktrees except the git object store, so several agents (or several of your own
branches) run side by side without touching each other's servers or branches.

Ported from [resslab-hub](https://github.com/RESSLab-Team/resslab-hub) and
[bluecity-viz](https://github.com/EPFL-ENAC/bluecity-viz), which carry the same tooling.
The long version, with the reasoning behind every odd line, is
`docs/worktree-env/` in bluecity-viz.

```
wtgo feat/x                        (or: make go BRANCH=feat/x, or: wt create feat/x origin/dev)
  └─ scripts/wt-new.sh             fetches origin/dev, `wt create` (or `wt checkout` if the branch exists)
       └─ .wt.toml post_create → scripts/wt-setup.sh          (idempotent)
            ├─ 0. branch tracking: upstream = origin/<branch>, or none
            ├─ 1. seeds gitignored dev files from the main checkout
            ├─ 2. picks the transition-compass-model checkout (--model pairs a model worktree)
            ├─ 3. hashes the branch name → .env.worktree (ports, TCM_PATH, UV_NO_SYNC)
            ├─ 5. writes .claude/settings.local.json from the MAIN checkout's template
            ├─ 6. npm ci (root + frontend), uv sync, editable model install, lefthook
            └─ 7. scripts/tmux-dev.sh --no-attach → tmux session "leure-speed-to-zero/feat/x"
       └─ attach (or switch-client when already inside tmux)
wtdone feat/x                      session killed, worktree removed, branch kept
make wt-land BRANCH=feat/x         from the main checkout: rebase, PR, squash-merge into dev, clean up
```

## Machine setup, once

```bash
go install github.com/timvw/wt@latest          # ~/go/bin/wt
wt init                                        # shell function so `wt create` cd's for you
git config --global push.default current
git config --global push.autoSetupRemote true
git config --global branch.autoSetupMerge simple
printf '**/.claude/worktrees/\n' >> ~/.config/git/ignore
printf 'bind s choose-tree -wZ -O name\n' >> ~/.tmux.conf
echo 'source ~/dev/speed-to-zero/scripts/wt-go.bash' >> ~/.bashrc   # wtgo / wtdone, with completion
```

`~/.config/wt/config.toml`, so worktrees land where Claude Code expects them:

```toml
strategy = "custom"
pattern  = "{.repo.Main}/.claude/worktrees/{.branch}"
separator = "-"                                         # feat/foo -> feat-foo
```

One source line of `wt-go.bash` serves every repo with this tooling: the functions act
on the repo you are standing in.

The model repo must sit next to this one (`transition-compass-model`, the same place
`backend/Makefile` has always looked for it). `TCM_MAIN` overrides that.

## Daily commands

```bash
wtgo all                          # after a reboot: every set-up worktree's session, then the picker
wtgo feat/<TAB>                   # go to a branch's session; creates branch, worktree and session as needed
wtgo feat/x --no-attach           # spin it up without entering it (chain several in one shell)
wtgo feat/x --model feat/y        # ... and give it its own transition-compass-model worktree on feat/y
wtgo feat/x --prompt brief.md     # brief the branch's agent (see below)
make wt-open BRANCH=feat/x        # frontend in the browser; TARGET=backend for /docs
make wt-land BRANCH=feat/x        # from the main checkout: rebase → PR → squash-merge → cleanup
wtdone feat/x                     # kill the session and remove the worktree, keep the branch
```

`prefix+s` lists the sessions sorted by name, `prefix+d` detaches, `prefix+X` opens a
close menu on the current session. `make new` / `make go` / `make wt-done` do the same
as the `wtgo` functions, without tab completion.

## Ports and the model

Everything per-worktree lives in `.env.worktree` at the checkout root, gitignored, and
the tmux panes export it. Nothing reads the file directly: the Makefiles read
`BACKEND_PORT` and `TCM_PATH`, `quasar.config.ts` reads `FRONTEND_PORT` and
`BACKEND_PORT` for its `/api` proxy, uv reads `UV_NO_SYNC`.

```
WT_BRANCH=feat/x
WT_SLUG=feat_x
BACKEND_PORT=18246          # 18xxx / 19xxx, hashed from <repo>/<branch>
FRONTEND_PORT=19246
TCM_PATH=/mnt/data/Documents/Code/transition-compass-model
TCM_BRANCH=                 # set only when the worktree is paired with a model worktree
UV_NO_SYNC=1
```

The main checkout has no such file and keeps 8000 / 9000.

**`UV_NO_SYNC=1` is not optional.** `uv run` and `uv sync` restore the environment to
the lockfile, which pins the PyPI `transition-compass-model` and so throws away the
editable install of the local checkout. Use `uv run --no-sync` in any shell that has not
sourced `.env.worktree`. `make -C backend check-model` prints which model is actually
imported.

With `--model`, the paired model worktree is created in the model repo, with its own
tmux session, and this worktree's backend reloads on its `.py` changes. Closing the app
worktree never removes the model one: it may hold unpushed model work. Close it from the
model repo with `wtdone <model-branch>`.

## Briefing an agent

A `PROMPT.md` at a checkout root is a one-shot brief. `wtgo <branch> --prompt <file>`
writes it and the session's `claude` pane starts on it, in plan mode, so the agent comes
back with a plan to review instead of editing straight away. The file is renamed to
`PROMPT.sent.md` before the run, so a session recreated later resumes that conversation
instead of firing the brief twice. Drafts go in `.wt-prompts/` (gitignored).

Several streams at once, one per line, never with `&` (`git worktree add` races on its
locks):

```bash
wtgo feat/a --no-attach --prompt .wt-prompts/a.md
wtgo feat/b --no-attach --prompt .wt-prompts/b.md
wtgo all
```

Give each brief an explicit "you own / do not touch" file list when the streams share a
directory, and tell the running sessions to `git merge origin/dev` after each landing.

## What an agent may do in a worktree

The session runs in auto mode with the OS sandbox on. On top of that,
`scripts/wt-setup.sh` writes `.claude/settings.local.json` from
`scripts/claude-worktree-settings.json` in the **main checkout** (a feature branch must
not be able to change the agent's own permissions):

| Layer     | Content                                                                                                                                                                                                |
| --------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| `allow`   | this repo's lint, format and test commands, and read-only `curl` to `localhost` / `127.0.0.1`                                                                                                          |
| `ask`     | write forms of `curl`/`wget`/`gh api`, `gh pr create/merge`, `gh release`, running downloaded code (`bash <(...)`, `npx -y`, `uvx`, `pip install git+`), `chmod +x`. Always prompts, even in auto mode |
| `deny`    | pushes to `dev`/`main` in every spelling, force push, tags, `git remote set-url/add`, `claude *`, every mutating connector tool                                                                        |
| `sandbox` | writes confined to the worktree (plus the paired model worktree); network to github, pypi and npm without a check. `curl` and `docker` run outside the sandbox, which cannot reach loopback            |

Outside Claude, and not negotiable by it: `scripts/git-push-guard.sh` runs as the shared
`.git/hooks/pre-push`, installed by `wt-setup.sh`. Inside a worktree it refuses any push
whose target is not the worktree's own branch, and any push to `dev` or `main`. The main
checkout is exempt, which is why `wt-land.sh` runs from there.

It is deliberately **not** a lefthook job. lefthook builds a file list for `pre-push` and
skips the job when that list is empty, which is what `git push origin HEAD:dev` produces:
it printed `push-guard (skip) no matching push files` and let the push through. There is
no config option to force it (see `buildCommand` in lefthook's source), so `lefthook.yml`
carries no `pre-push` section at all. That also stops `lefthook install` from replacing
the hook. Check yours with:

```bash
grep -c 'wt push guard' "$(git rev-parse --git-common-dir)/hooks/pre-push"   # 1
```

## Smoke test

Run it from a terminal, not from an agent: the sandbox cannot install git hooks or reach
the tmux socket.

```bash
wtgo test/smoke --no-attach
tmux ls                                                 # leure-speed-to-zero/test/smoke
cd .claude/worktrees/test-smoke && cat .env.worktree
make -C backend check-model                             # the TCM_PATH checkout
curl -sI "http://localhost:$FRONTEND_PORT/"             # 200
curl -sf "http://127.0.0.1:$BACKEND_PORT/health"        # ok
grep -c 'wt push guard' "$(git rev-parse --git-common-dir)/hooks/pre-push"   # 1
git commit --allow-empty -m "test: smoke" && git push   # must work
git push --dry-run origin HEAD:dev                      # must be REFUSED
git branch -vv                                          # upstream is origin/test/smoke, not origin/dev
wtdone test/smoke                                       # session gone, ports free
```

If the guard does not refuse, stop and fix it before real work: it is the one piece
protecting the shared branches from an agent.

## Traps already paid for

- **`$WT_MAIN` lies**: wt points it at whichever worktree has the default branch checked
  out. Everything here resolves the main checkout through `git rev-parse
--git-common-dir`. Never check out `dev` in a worktree.
- **A branch must not track its base.** Cutting from `origin/dev` makes git track
  `origin/dev`, `git pull` then rebases onto dev and the next push is refused. Step 0 of
  `wt-setup.sh` repairs it.
- **A local ref makes a stale base**: pass `origin/<base>`, fetched first.
- **`post_checkout` may run on create too**, so setup is idempotent and can be re-run by
  hand at any time to refresh a worktree.
- **The sandbox cannot reach loopback or the tmux socket**: an agent reads `.wt-logs/`
  instead of running `tmux`, and `curl` is excluded from the sandbox so it can hit its
  own servers.
- **The sandbox cannot finish `wt-setup.sh`**: an agent cannot write `.git/hooks`, nor
  `~/.npm/_cacache`, so `npm ci` fails there too. Create worktrees from a terminal. A
  sandboxed re-run is still fine for the env file and the session-less parts.
- **An ask rule beats everything**, in auto mode too, and no allow rule overrides it.
  Never put a bare interpreter (`python3 -`, `node -`) in `ask`: auto mode edits files
  through heredocs and it prompts on every edit.
- **uv does not look up the tree for `.python-version`.** Run from `backend/`, a fresh
  `uv sync` takes the newest interpreter on the machine instead of the 3.12 the repo and
  the Docker image name, and `orjson` then has no wheel and wants a Rust toolchain.
  `wt-setup.sh` passes `--python` explicitly.
- **Until this lands in `dev`**, a worktree cut from `origin/dev` carries neither the
  scripts nor the new `.gitignore`, so it shows `.env.worktree` and `.wt-logs/` as
  untracked and `wtdone` asks for `--force`. The hooks still work: they always run the
  main checkout's copy of the scripts.
- **tmux session names** cannot contain `.` or `:`; `session_name()` maps them to `-`.
- **`wt-land.sh` squash-merges**, so a branch lands as one commit on `dev`.
