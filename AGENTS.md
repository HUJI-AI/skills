# AGENTS.md

Agent skills and connectors for the Hebrew University of Jerusalem. Each
`skills/<name>/` is a public skill that the AI portal
(https://ai.huji.ac.il/skills/) publishes from `main`. Each `plugins/<name>/`
is a connector: a remote MCP server packaged for Claude Code and Codex.
Follow [CONTRIBUTING.md](CONTRIBUTING.md); it holds the rules.

- Every file is public: no secrets, notes, TODOs or security details of
  university systems, including in HTML comments.
- Don't write names, services, addresses, prices, dates or policies the
  maintainer hasn't provided or that you haven't checked at their source.
  Never add a connector for a server whose owners haven't agreed.
- Run `uv run scripts/check.py --write` after a change and commit what it
  updates (the README catalogues, each skill's `agents/openai.yaml`, each
  connector's manifest versions, both marketplaces and `plugin.json`).
  Everything must work in Claude Code, Codex and other Agent Skills apps:
  keep to the standard's fields.
- Work on a branch and open a pull request to `main`; don't push to `main`.
  GitHub Actions runs `scripts/check.py` on each pull request.
