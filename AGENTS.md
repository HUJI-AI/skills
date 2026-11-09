# AGENTS.md

Agent skills for the Hebrew University of Jerusalem. Each `skills/<name>/` is a
public skill that the AI portal (https://ai.huji.ac.il/skills/) publishes from
`main`. Follow [CONTRIBUTING.md](CONTRIBUTING.md); it holds the rules.

- Every file in a skill folder is public: no secrets, notes, TODOs or security
  details of university systems, including in HTML comments.
- Don't write names, services, prices, dates or policies the maintainer hasn't
  provided or that you haven't checked at their source.
- Run `uv run scripts/check.py --write` after changing a skill and commit what
  it updates (the README catalogue, each skill's `agents/openai.yaml`, both
  marketplaces and `plugin.json`). Skills must work in Claude Code, Codex and
  other Agent Skills apps: keep to the standard's fields.
- Work on a branch and open a pull request to `main`; don't push to `main`.
