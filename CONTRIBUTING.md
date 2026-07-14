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
- Adding support for a new entity domain is the most common contribution — see the `resumable/` package
  for the pattern: subclass the right base, register it in the dispatch table, and add tests.
