# Contributing to semhound

Thank you for your interest in contributing! This guide explains everything you need to know to submit changes — from branching to commit messages to getting your code released on PyPI automatically.

---

## Who Can Merge?

Only **[@salecharohit](https://github.com/salecharohit)** can approve and merge pull requests into `main`. Direct pushes to `main` are restricted. All contributions must go through a PR.

---

## Workflow

```
1. Fork or branch  →  2. Make changes  →  3. Open PR  →  4. Review & merge  →  5. Automated release
```

### Step-by-step

```bash
# 1. Clone the repo
git clone git@github.com:salecharohit/semhound.git
cd semhound

# 2. Create a feature branch — never commit directly to main
git checkout -b feat/my-feature        # for new features
git checkout -b fix/my-bugfix          # for bug fixes
git checkout -b docs/update-readme     # for documentation

# 3. Make your changes and commit (see commit format below)
git add .
git commit -m "feat: add support for GitLab targets"

# 4. Push your branch
git push origin feat/my-feature

# 5. Open a Pull Request on GitHub against main
#    CI will run automatically — PR cannot be merged until it passes
```

---

## Commit Message Format

semhound uses **[Conventional Commits](https://www.conventionalcommits.org/)** — a strict commit message format that drives automated versioning and changelog generation via [release-please](https://github.com/googleapis/release-please).

### Structure

```
<type>(<optional scope>): <short description>

[optional body]

[optional footer — e.g. BREAKING CHANGE: ...]
```

### Commit Types

| Type | When to use | Version bump | Appears in CHANGELOG |
|---|---|---|---|
| `feat` | New feature for the end user | **Minor** `1.0.0 → 1.1.0` | ✅ Yes |
| `fix` | Bug fix for the end user | **Patch** `1.0.0 → 1.0.1` | ✅ Yes |
| `docs` | Documentation only changes | None | ❌ No |
| `refactor` | Code change with no behaviour change | None | ❌ No |
| `perf` | Performance improvement | None | ❌ No |
| `test` | Adding or fixing tests | None | ❌ No |
| `chore` | Build process, dependency updates, tooling | None | ❌ No |
| `ci` | CI/CD configuration changes | None | ❌ No |
| `style` | Formatting, whitespace (no logic change) | None | ❌ No |

### Breaking Changes → Major version bump

Add `!` after the type, **or** add a `BREAKING CHANGE:` footer:

```bash
# Option A — exclamation mark
git commit -m "feat!: drop support for Python 3.8"

# Option B — footer in body
git commit -m "feat: redesign CLI flags

BREAKING CHANGE: --rules-dir is now --rules, --orgs-file is now --targets"
```

Both produce a **Major** bump: `1.2.3 → 2.0.0`.

---

## Real Examples

```bash
# New feature
git commit -m "feat: add --exclude flag to skip repos by pattern"

# Bug fix
git commit -m "fix: handle empty org gracefully instead of crashing"

# Scoped fix (optional scope in parentheses)
git commit -m "fix(scanner): prevent duplicate findings when using multiple rule sources"

# Performance improvement
git commit -m "perf: switch from ThreadPoolExecutor to asyncio for clone phase"

# Documentation update (no release triggered)
git commit -m "docs: add bedrock authentication example to README"

# Dependency bump (no release triggered)
git commit -m "chore: bump anthropic to 0.30"

# Breaking change
git commit -m "feat!: replace --ai-config file with --ai-provider flags"
```

---

## What Happens After Your PR is Merged

```
Your PR merged into main
        │
        ▼
release-please reads new commits on main
        │
        ├── Only docs:/chore:/refactor: ?
        │         → No action taken
        │
        └── feat: or fix: present?
                  → Opens a "Release PR" automatically
                        │
                        ▼
            @salecharohit merges the Release PR
                        │
                        ▼
            Git tag vX.Y.Z created automatically
                        │
                        ▼
            Package built and published to PyPI ✅
            GitHub Release created with changelog ✅
```

You do **not** need to manually tag, build, or publish anything.

---

## CI Checks

Every PR runs the following checks. All must pass before merging:

| Check | What it does |
|---|---|
| `ci / syntax-check` | Compiles all Python files (`python -m compileall`) |
| `ci / Check imports` | Verifies the package imports cleanly |

---

## Code Style

- Python **3.9+** compatible syntax only
- No new external dependencies without discussion — keep the install footprint small
- Follow the existing code style (no linter is enforced yet, but keep it consistent)
- Preserve all existing docstrings and comments unless directly relevant to your change

---

## Reporting Issues

Open an issue at [github.com/salecharohit/semhound/issues](https://github.com/salecharohit/semhound/issues).

Please include:
- semhound version (`pip show semhound`)
- Python version (`python --version`)
- OS
- Full command you ran
- Full error output
