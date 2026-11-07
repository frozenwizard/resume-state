# Contribution guidelines

Contributions are welcome! Bug reports, feature requests, and pull requests are all appreciated — for
larger changes, consider opening an issue first so we can talk it through.

## Developing

- Run the tests with `python3 -m pytest tests/`.
- Run `scripts/lint` before pushing — CI runs the same checks (ruff, mypy, markdownlint, JSON formatting)
  in check-only mode.

## Pull requests

- Target the `main` branch. Every PR needs the checks green and will be reviewed by the maintainer
  before merging.
- New code is expected to be fully typed and docstringed; tests for new behavior are expected too.
- Add a line for each user-visible change under `## Unreleased` in `CHANGELOG.md` (add the heading if it's
  missing). Release notes come from there.
- Adding support for a new entity domain is the most common contribution — see the `resumable/` package
  for the pattern: subclass the right base, register it in the dispatch table, and add tests.

## Releasing

1. In a pull request, set the manifest version to `X.Y.Z` and rename `## Unreleased` in `CHANGELOG.md` to
   `## vX.Y.Z (DD-MM-YYYY)`.
2. Once it's merged, tag the release PR's merge commit and push the tag, e.g.
   `git tag vX.Y.Z <merge commit> && git push origin vX.Y.Z`. Tag that commit rather than the tip of `main`: any later
   merge, such as an auto-merged Dependabot PR, bumps the manifest version, and the release requires it to match the
   tag. The release workflow checks the tag and the changelog, runs the checks, and publishes the GitHub release with
   that section as its notes. HACS offers it to users from there.
