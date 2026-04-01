# Contributing Guide

## Branching Strategy

```
main (production)
  ↑
dev (staging)
  ↑
feature/*, fix/* (individual tasks)
```

### Branch Purposes

- **`main`**: Production-ready code, deployed to https://transition-compass.epfl.ch/
- **`dev`**: Integration branch for testing, deployed to https://transition-compass-dev.epfl.ch/
- **`feature/*`, `fix/*`**: Short-lived branches for specific changes

> **Note**: Model research is done in the separate [transition-compass-model](https://github.com/2050Calculators/transition-compass-model) repository. If you're working on sector calculations, data, or parameters, see that repo's contributing guide instead.

## Development Workflow

### 1. Start with Latest Code

```bash
git checkout dev
git pull origin dev

# Create a feature branch
git checkout -b feature/my-change
```

### 2. Make Your Changes

Edit frontend components, API routes, configuration, etc.

### 3. Test Locally

```bash
make install       # Install dependencies (if changed)
make lint          # Check code quality
make format        # Auto-fix formatting
make run           # Test the application at localhost:9000
```

### 4. Commit

We use [Conventional Commits](https://www.conventionalcommits.org/):

```bash
git add <files>
git commit -m "feat(transport): add new chart for emissions breakdown"
```

**Commit types**: `feat`, `fix`, `docs`, `refactor`, `perf`, `test`, `chore`

### 5. Push and Create a Pull Request

```bash
git push origin feature/my-change
```

1. Go to GitHub: https://github.com/EPFL-ENAC/leure-speed-to-zero
2. Click **"New Pull Request"**
3. Set base branch: `dev` ← compare branch: `feature/my-change`
4. Fill in the PR:
   - **Title**: Brief description (conventional commit format)
   - **Description**: What changed and why
   - **Testing**: How you tested the changes
5. Request review

### Pull Request Checklist

- [ ] `make install` completes without errors
- [ ] `make lint` passes
- [ ] `make format` has been run
- [ ] Application runs locally with `make run`
- [ ] Conventional commit messages are used
- [ ] Branch is up-to-date with `dev`

## Keeping Your Branch Updated

Periodically merge `dev` into your feature branch:

```bash
git fetch origin
git merge origin/dev
# Resolve any conflicts, then push
```

## Make Commands

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

## Getting Help

- **Git issues**: Ask Pierre or check [Git documentation](https://git-scm.com/doc)
- **Code issues**: Create an issue on [GitHub](https://github.com/EPFL-ENAC/leure-speed-to-zero/issues)
- **Linter errors**: Run `make format` first, then review remaining issues
