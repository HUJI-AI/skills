# Contributing a skill or a connector

Everything in this repository is public: here on GitHub and on the AI portal
(<https://ai.huji.ac.il/skills/>), as raw files, in each skill's zip and in the
portal's index for agents. Write every file as a public page.

## Add a skill

1. Fork the repository (with write access, branch from `main` instead).
2. Copy `template/skill/` to `skills/<name>/`. The name is lowercase letters, digits
   and hyphens, and `name` in `SKILL.md` must be the same.
3. Fill in the front matter:
   - `description`: in English, for the agent. It decides when the agent
     loads the skill, so say what it does and when to use it.
   - `metadata.title` and `metadata.summary`: in Hebrew, for people. The
     portal shows them on the skill's page and cards.
   - `metadata.title_en` and `metadata.summary_en`: the English page.
   - `metadata.pillar`: who it is for, which places it on the portal:
     `students`, `teaching`, `research`, `administration` or `general`.
     A skill for teaching staff is `teaching`; one for students is `students`.
   Keep `metadata` flat (no nested lists or maps), as the standard requires.
4. Write the instructions below the front matter. Link to the skill's own
   files relative to its folder, such as `[API](references/api.md)`.
5. Run `uv run scripts/check.py --write`. It checks the skill, adds it to the
   README catalogue and the Claude Code and Codex marketplaces, and writes its
   `agents/openai.yaml` from the English title and summary. You may add other
   Codex settings to that file (such as `policy` or `dependencies`); the
   check keeps them.
6. Open a pull request to `main`. GitHub runs the check on it, and a
   maintainer reviews it.

## Add a connector

A connector gives agents access to a service through its MCP server. It is a
plugin in `plugins/<name>/` that Claude Code and Codex install from the same
folder. Propose one only for a server that its owners run for the university
and agree to have listed here.

1. Fork the repository, or branch from `main`.
2. Copy `template/plugin/` to `plugins/<name>/`, and replace `connector-name`
   with the name everywhere: in both manifests and in `.mcp.json`.
3. In `.mcp.json`, set the server's `https://` address. Only remote servers
   are accepted: a connector never runs a program on the user's computer. If
   the server needs a key in a header, write a `${...}` placeholder, never the
   key itself.
4. In `.claude-plugin/plugin.json` and `.codex-plugin/plugin.json`, write the
   description in English. In the Codex one, also the name and short line
   that Codex and ChatGPT show.
5. Fill in `README.md`: what the connector reaches, who runs the server, how
   people sign in, its privacy policy and who maintains it.
6. Optionally, keep `skills/connector-name/` (renamed) to teach the agent when
   and how to use the server's tools; delete it otherwise.
7. Run `uv run scripts/check.py --write`. It checks the connector, writes the
   manifests' versions, and adds it to the README and both marketplaces.
8. Open a pull request to `main`.

Before merging, a maintainer checks that the server's owners agreed, that it
works in both Claude Code and Codex, and that it asks for no more access than
it needs.

## What does not belong here

- **Maintainer notes and TODOs.** HTML comments are published too. Keep notes
  where the maintainers keep them, outside this repository. Files and folders
  starting with `_` or `.` inside a skill are refused by the check.
- **Secrets**: keys, tokens, passwords, personal data.
- **Security details of university systems**: software versions,
  undocumented behaviour, gaps. Report those to the system's owners.
- **Dates and version numbers** in `SKILL.md`, unless the instructions need
  them: the file is published as it is.
- **ELSC-only services** (Glia, the ELSC Apps Hub, ELSC model keys). This
  repository is for the whole university.

## How a change reaches the portal

The portal fetches `main` of this repository each time it is built and stops
if a skill breaks the rules above, so run the check before you open a pull
request. A merged change appears on the portal with the next publish.

Maintainers can preview a branch on the portal before merging by building the
portal (its own repository) with this checkout:

```
HUJI_SKILLS_DIR=/path/to/huji-skills uv run build.py serve
```
