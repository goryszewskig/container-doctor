# Git Tips & Tricks for DevOps / Data Engineers

## Git Notation Glossary

Before the commands — here's what the cryptic symbols mean:

| Notation | Meaning | Example |
|---|---|---|
| `HEAD` | Pointer to your current commit (usually the tip of the checked-out branch) | `git show HEAD` |
| `HEAD~N` | N commits *before* HEAD, following first parents | `HEAD~5` = 5 commits back |
| `HEAD^` | First parent of HEAD (`HEAD^2` = second parent of a merge commit) | `git revert -m 1 <sha>` uses parent #1 as the "mainline" |
| `<sha>` | A commit's hash ID (full 40 chars or short prefix like `a1b2c3d`) — every commit has one | `git cherry-pick a1b2c3d` |
| `main` | Branch name — a movable pointer to a commit | `git diff main...HEAD` |
| `origin/main` | Your local *copy* of where the remote's main was at last fetch | `git fetch` updates it |
| `HEAD@{N}` | Reflog entry — where HEAD was N moves ago (NOT the same as `HEAD~N`) | `HEAD@{2}` = two operations ago (commits, checkouts, rebases all count) |
| `stash@{N}` | Entry on the stash stack, 0 = most recent | `git stash apply stash@{1}` |
| `A..B` | Commits reachable from B but not A (linear range) | `git log main..feature` |
| `A...B` | Commits on either side since their common ancestor (symmetric difference); in `diff`, shows changes on B since the fork point | `git diff main...HEAD` |
| `<name>` in docs | Placeholder — replace with your real value | `git checkout -b <branch>` → `git checkout -b fix/typo` |
| `@{u}` / `@{upstream}` | The upstream branch your current branch tracks | `git diff @{u}..HEAD` |
| `@` alone | Shortcut for `HEAD` | `git rebase -i @~3` |

Common confusion — `~` vs `^` vs `@{}`:
- `HEAD~5` walks **history back** 5 commits ( ancestry )
- `HEAD^2` picks a **parent** (only matters for merge commits)
- `HEAD@{5}` walks the **reflog** — what *you did locally* 5 operations ago, including discarded work

## Branching & History

- `git rebase -i HEAD~5` — squash/reword/reorder commits before pushing
  ```bash
  git rebase -i HEAD~3
  # mark commits 2 and 3 as "squash" to fold them into the first
  ```
- `git commit --fixup <sha>` + `git rebase -i --autosquash main` — auto-fold fixes into the right commit
  ```bash
  git commit --fixup a1b2c3d        # small fix for commit a1b2c3d
  git rebase -i --autosquash main   # git places it automatically
  ```
- `git cherry-pick <sha>` — port a single commit to another branch
  ```bash
  git checkout release/1.4
  git cherry-pick a1b2c3d           # hotfix commit from master
  ```
- `git reflog` — recover lost commits, bad rebases, deleted branches
  ```bash
  git reflog
  git reset --hard HEAD@{5}         # jump back to a known-good state
  ```
- `git log --oneline --graph --all` — visual branch map
  ```bash
  git log --oneline --graph --all --since="2 weeks ago" --author=me
  ```
- `git bisect` — binary-search history to find the commit that introduced a bug
  ```bash
  git bisect start
  git bisect bad                    # current version is broken
  git bisect good v1.2.0            # this tag was fine
  # git checks out middle commits; mark each as good/bad until culprit is found
  git bisect reset
  ```

## Daily Efficiency

- `git switch -c` / `git restore` — modern replacements for overloaded `checkout`
  ```bash
  git switch -c feature/new-thing   # create + switch branch
  git restore src/app.py            # discard local changes in file
  ```
- `git worktree` — two branches in two folders at once
  ```bash
  git worktree add ../proj-hotfix -b hotfix/urgent
  cd ../proj-hotfix && make fix && git push
  git worktree remove ../proj-hotfix
  ```
- `git diff main...HEAD` — three dots = changes on my branch since divergence
  ```bash
  git fetch origin
  git diff origin/main...HEAD --stat
  ```
- `git blame` + pickaxe search `-S` — who wrote this / when did this string change
  ```bash
  git blame -L 40,60 -- docker-compose.yml
  git log -S "POOL_SIZE" --oneline  # commits that added/removed this text
  ```
- Aliases in `~/.gitconfig`
  ```bash
  git config --global alias.lg "log --oneline --graph --all"
  git config --global alias.st "status -sb"
  git lg
  ```

## Safer Pushing & Syncing

- `git push --force-with-lease` — force-push that refuses if the remote moved
  ```bash
  git rebase main
  git push --force-with-lease       # safe on your own feature branch
  ```
- `git pull --rebase` — linear history, no merge-commit noise
  ```bash
  git config --global pull.rebase true
  git pull                          # now always rebases
  ```
- `git fetch --prune` — drop stale remote-tracking branches
  ```bash
  git config --global fetch.prune true
  ```
- Push options (GitLab)
  ```bash
  git push -o merge_request.create -o merge_request.target=main
  ```

## Partial & Precise Staging

- `git add -p` — stage selected hunks interactively
  ```bash
  git add -p container_doctor.py    # y/n/s/e per hunk
  ```
- `git restore -p` — discard selected hunks
- `git commit -v` — see the diff in the commit message editor
- `git restore --staged <file>` — unstage without losing changes
  ```bash
  git add .
  git restore --staged secrets.yaml # oops, unstage that one
  git commit -m "feat: add monitoring"
  ```

## DevOps-Specific Patterns

- **Sparse checkout** for monorepos
  ```bash
  git clone --filter=blob:none --sparse https://github.com/org/monorepo
  cd monorepo
  git sparse-checkout set infra/terraform services/api
  ```
- **Shallow clones in CI** — faster pipelines
  ```bash
  git clone --depth 1 https://github.com/org/repo
  ```
- `.gitattributes` — end CRLF/LF wars (important on Windows)
  ```
  * text=auto
  *.sh text eol=lf
  *.py text eol=lf
  *.png binary
  ```
- **pre-commit hooks** — lint/format/scan before commit
  ```bash
  pip install pre-commit gitleaks
  pre-commit install                # runs on every git commit
  ```
- **Signed tags** for releases
  ```bash
  git tag -s v1.2.0 -m "release 1.2.0"
  git push origin v1.2.0
  ```
- **Conventional Commits** — enables automated changelogs/versioning
  ```bash
  git commit -m "feat(api): add /history endpoint"
  git commit -m "fix(db): prevent restart loop on disk-full"
  ```

## Data Engineering Angle

- **Purging secrets/data from history** — use `git filter-repo`, then rotate the secret anyway
  ```bash
  pip install git-filter-repo
  git filter-repo --path credentials.json --invert-paths
  git push --force-with-lease
  ```
- **Large files** — DVC or git-lfs instead of plain git
  ```bash
  git lfs install
  git lfs track "*.parquet"
  git add .gitattributes data/sample.parquet
  git commit -m "chore: track sample dataset with LFS"
  ```
- Debug `.gitignore`
  ```bash
  git check-ignore -v data/raw/export.csv
  ```

## Recovery Toolkit

```bash
git reflog                      # find lost state
git reset --hard HEAD@{2}       # jump back to it
git revert <sha>                # undo a pushed commit safely (no history rewrite)
git clean -ndx                  # PREVIEW untracked junk that would be deleted
git clean -fdx                  # actually delete it
```

Example — undo a bad merge that is already pushed:
```bash
git revert -m 1 <merge-commit-sha>
git push
```

## Rules of Thumb

1. Rebase your own branches; merge shared branches (main)
2. Small, atomic commits — one logical change each
3. `git status` + `git diff --staged` before every commit
4. Rewrite history only before it's pushed/shared
5. When lost: `git reflog` first, panic never

Good practice path: master `rebase -i`, `reflog`, and `--force-with-lease` first — those three alone put you ahead of most engineers.
