# Contributing

## Branches

- `develop` — active development. Open PRs here.
- `main` — release-track. `develop` is merged into `main` (no-ff) when a
  release is ready.

## Commits — Conventional Commits

Every commit message must follow [Conventional Commits](https://www.conventionalcommits.org).
The prefix tells `release-please` what kind of change it is and what
SemVer bump to derive.

```
<type>(<optional scope>): <imperative summary>

<optional body>

<optional BREAKING CHANGE: footer>
```

### Types

| Type | Effect on next version | Goes in CHANGELOG? |
|---|---|---|
| `feat` | MINOR (`0.1.0 → 0.2.0`) | yes — *Features* |
| `fix` | PATCH (`0.1.0 → 0.1.1`) | yes — *Bug Fixes* |
| `perf` | PATCH | yes — *Performance* |
| `refactor` | PATCH | yes — *Refactoring* |
| `docs` | PATCH | yes — *Documentation* |
| `revert` | PATCH | yes — *Reverts* |
| `build` | none | no |
| `ci` | none | no |
| `chore` | none | no |
| `style` | none | no |
| `test` | none | no |

### Breaking changes

Add `!` after the type, or include a `BREAKING CHANGE:` footer in the
body. Either form bumps the **MAJOR** version (`0.x → 1.0` pre-1.0
behaviour is governed by `bump-minor-pre-major` in
`release-please-config.json` — currently, pre-1.0 we treat breaking
changes as MINOR bumps).

```
feat(client)!: rename recognize_image to ocr_image

BREAKING CHANGE: Client.recognize_image is now Client.ocr_image.
The old name is removed without an alias.
```

### Examples

```
feat(client): add recognize_pixels for raw RGB(A) buffers
fix(grpc): close channel cleanly on AsyncGrpcClient shutdown
docs: add Diátaxis tutorials and how-tos
refactor(http): lift lazy reportlab imports to module top
ci: add release-please workflow
```

## Release flow

You never edit the version in `pyproject.toml` by hand. `release-please`
does it for you.

1. **Merge feature PRs into `develop`** — each with Conventional Commit
   messages.
2. **When ready to ship**, merge `develop` → `main`:
   ```
   git checkout main
   git merge --no-ff develop
   git push origin main
   ```
3. **`release-please` opens a PR** titled `release: vX.Y.Z` against
   `main`, containing:
   - bumped `version` in `pyproject.toml`
   - bumped version in `.release-please-manifest.json`
   - regenerated `CHANGELOG.md` from the Conventional Commits since the
     last tag
4. **Review the PR**. Edit the CHANGELOG if you want to reword
   anything. When happy, **merge it**.
5. **Merging the release PR** causes `release-please` to:
   - tag `vX.Y.Z` on `main`
   - publish a GitHub Release with the CHANGELOG entry
6. **The tag push triggers `release.yml`**, which builds + tests + publishes
   to PyPI via the OIDC Trusted Publisher.
7. **The tag push also triggers `docs.yml`**, which deploys versioned docs
   to GitHub Pages (`vX.Y.Z` + alias `latest`).

No manual `git tag` step. No hand-edited CHANGELOG. No version-bump
commit by you.

## Local checks before pushing

```bash
ruff check .
mypy .
uv run pytest tests -q --ignore=tests/integration
```

CI runs the same on every PR via `.github/workflows/ci.yml`.

## Docs

Preview the docs site locally:

```bash
uv run --extra docs mkdocs serve -f docs/mkdocs.yml
```

Lives at http://127.0.0.1:8000 with live reload.
