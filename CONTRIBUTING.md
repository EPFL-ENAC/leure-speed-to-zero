# Contributing Guide

## 🌳 Branching Strategy

This project uses a structured branching workflow:

```
main (production)
  ↑
dev (staging)
  ↑
model (research/development)
  ↑
feature/*, fix/* (individual tasks)
```

### Branch Purposes

- **`main`**: Production-ready code, deployed to https://speed-to-zero.epfl.ch/
- **`dev`**: Integration branch for testing, deployed to https://speed-to-zero-dev.epfl.ch/
- **`model`**: Research and model development branch (long-lived)
- **`feature/*`, `fix/*`**: Short-lived branches for specific changes

## 🔄 Development Workflow

### For Researchers Working on the Model

#### 1. Start with Latest Code

Always start by syncing your `model` branch with the latest from `dev`:

```bash
# Switch to model branch
git checkout model

# Get latest changes from remote
git fetch origin

# Merge latest dev changes into model
git merge origin/dev

# If there are conflicts, resolve them and commit
```

#### 2. Make Your Changes

```bash
# Create a feature branch (optional but recommended)
git checkout -b feature/my-new-feature

# Make your changes to the code
# Edit files, add modules, update calculations, etc.
```

#### 3. Test Your Changes Locally

```bash
# Install dependencies (if changed)
make install

# Run linter to check code quality
make lint

# Fix formatting issues automatically
make format

# Test the application
make run
```

Visit http://localhost:9000 to verify your changes work correctly.

#### 4. Commit Your Changes

We use [Conventional Commits](https://www.conventionalcommits.org/):

```bash
# Stage your changes
git add .

# Commit with a descriptive message
git commit -m "feat(agriculture): add new crop yield calculation"
# or
git commit -m "fix(buildings): correct heating demand formula"
# or
git commit -m "docs(model): update carbon sequestration documentation"
```

**Commit types:**

- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation only
- `refactor`: Code restructuring without behavior change
- `perf`: Performance improvement
- `test`: Adding tests
- `chore`: Maintenance tasks

#### 5. Push to Remote

```bash
# If you created a feature branch
git push origin feature/my-new-feature

# If working directly on model branch
git push origin model
```

#### 6. Create a Pull Request

1. Go to GitHub: https://github.com/EPFL-ENAC/leure-speed-to-zero
2. Click **"New Pull Request"**
3. Set base branch: `dev` ← compare branch: `model` (or your feature branch)
4. Fill in the PR template:
   - **Title**: Brief description (follows conventional commit format)
   - **Description**: Explain what changed and why
   - **Testing**: How you tested the changes
   - **Screenshots**: If UI changed
5. Request review from Pierre (@pguilbert)
6. Wait for approval before merging

### Pull Request Checklist

Before creating a PR, ensure:

- [ ] `make install` completes without errors
- [ ] `make lint` passes without errors
- [ ] `make format` has been run
- [ ] Application runs locally with `make run`
- [ ] All calculations produce expected results
- [ ] Conventional commit messages are used
- [ ] Branch is up-to-date with `dev`

## 🔀 Keeping Your Branch Updated

### Option 1: Regular Merges (Recommended)

Periodically merge `dev` into your `model` branch to stay current:

```bash
git checkout model
git fetch origin
git merge origin/dev

# Resolve any conflicts
# Test that everything still works
git push origin model
```

**When to merge:**

- Before starting new work
- When major features land on `dev`
- At least weekly to avoid large conflicts

### Option 2: Rebase (Advanced)

For a cleaner history, rebase your changes on top of `dev`:

```bash
git checkout model
git fetch origin
git rebase origin/dev

# Resolve conflicts if any
# Force push (use with caution!)
git push origin model --force-with-lease
```

⚠️ **Warning**: Only use rebase if you're the only one working on the branch!

## 🐛 Handling Merge Conflicts

When conflicts occur during merge:

```bash
# After git merge origin/dev shows conflicts

# 1. Check which files have conflicts
git status

# 2. Open conflicted files and look for:
<<<<<<< HEAD
your changes
=======
incoming changes from dev
>>>>>>> origin/dev

# 3. Edit files to resolve conflicts
# Keep both, keep yours, or keep theirs - depends on the situation

# 4. Stage resolved files
git add path/to/resolved/file

# 5. Complete the merge
git commit

# 6. Test everything works
make install
make run

# 7. Push
git push origin model
```

## 📋 Quick Reference

### Common Commands

```bash
# Daily workflow
git checkout model
git pull origin model
git merge origin/dev              # Get latest from dev
# ... make changes ...
make lint && make format          # Check code quality
git add .
git commit -m "feat: description"
git push origin model

# Create PR: model → dev on GitHub
```

### Make Commands

```bash
make help              # Show all available commands
make install           # Install all dependencies
make lint              # Check code quality
make format            # Auto-fix formatting issues
make run               # Start dev servers (backend + frontend)
make run-backend       # Backend only
make run-frontend      # Frontend only
make clean             # Clean dependencies
```

### Git Workflow Diagram

```
┌─────────────────────────────────────────────────────┐
│ 1. Start: Sync with dev                            │
│    git checkout model                               │
│    git merge origin/dev                             │
└────────────────┬────────────────────────────────────┘
                 │
┌────────────────▼────────────────────────────────────┐
│ 2. Develop: Make changes                           │
│    Edit code, add features, fix bugs               │
└────────────────┬────────────────────────────────────┘
                 │
┌────────────────▼────────────────────────────────────┐
│ 3. Quality: Test and lint                          │
│    make lint && make format                         │
│    make run                                         │
└────────────────┬────────────────────────────────────┘
                 │
┌────────────────▼────────────────────────────────────┐
│ 4. Commit: Save changes                            │
│    git add .                                        │
│    git commit -m "feat: description"                │
└────────────────┬────────────────────────────────────┘
                 │
┌────────────────▼────────────────────────────────────┐
│ 5. Push: Upload to remote                          │
│    git push origin model                            │
└────────────────┬────────────────────────────────────┘
                 │
┌────────────────▼────────────────────────────────────┐
│ 6. PR: Create Pull Request                         │
│    model → dev on GitHub                            │
│    Wait for review and approval                     │
└─────────────────────────────────────────────────────┘
```

## 🆘 Getting Help

- **Git issues**: Ask Pierre or check [Git documentation](https://git-scm.com/doc)
- **Code issues**: Create an issue on GitHub
- **Merge conflicts**: Don't force push - ask for help!
- **Linter errors**: Run `make format` first, then review remaining issues

## 🎯 Best Practices

### Do's ✅

- Merge `dev` into `model` regularly
- Run `make lint` before committing
- Use conventional commit messages
- Test locally before pushing
- Create descriptive PR descriptions
- Ask for code review

### Don'ts ❌

- Don't push directly to `dev` or `main`
- Don't force push without consulting the team
- Don't commit generated files (node_modules, .venv, **pycache**)
- Don't merge without testing
- Don't skip the linter
- Don't work on outdated code (merge dev first!)

## 📚 Additional Resources

- [Conventional Commits](https://www.conventionalcommits.org/)
- [GitHub Pull Requests](https://docs.github.com/en/pull-requests)
- [Git Basics](https://git-scm.com/book/en/v2/Getting-Started-Git-Basics)
- [Project README](README.md)
- [New Sector Tutorial](TUTORIAL_NEW_SECTOR.md)
- [New Lever Tutorial](TUTORIAL_NEW_LEVER.md)
