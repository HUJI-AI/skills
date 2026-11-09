# HUJI agent skills

<div dir="rtl">

כישורי AI (סקילים) של האוניברסיטה העברית לסוכני AI. כאן נמצא המקור שלהם:
מציעים כאן כישורים חדשים ושינויים בכישורים קיימים. [פורטל ה־AI של האוניברסיטה](https://ai.huji.ac.il/skills/)
מציג את הכישורים, עם הוראות התקנה וקובצי zip להורדה, ומתעדכן מהענף `main` של המאגר.

</div>

Agent skills for the Hebrew University of Jerusalem. This repository is where
they are written, reviewed and kept. The university's AI portal publishes them
at **<https://ai.huji.ac.il/skills/>**, with install instructions, a zip of
each skill and an index for agents. The portal is built from `main`.

A skill is a folder with a `SKILL.md` file: instructions that teach an AI agent
(Claude Code, Codex, Gemini CLI and others) how to do a particular task, plus
any scripts or reference files it needs. The format is the open
[Agent Skills standard](https://agentskills.io/specification).

## Catalogue

<!-- catalogue:begin -->

| Skill | For | What it does |
| --- | --- | --- |
| [The Shnaton: courses, requirements and timetables](skills/huji-shnaton/) · [on the portal](https://ai.huji.ac.il/skills/huji-shnaton/) | Students | Search the Hebrew University course catalogue for courses, class times and exam dates, prerequisites and degree requirements by start year, and check a timetable for clashes. |
| [Doctoral studies: stages, rules and forms](skills/huji-phd/) · [on the portal](https://ai.huji.ac.il/skills/huji-phd/) | Research | Find the Authority for Research Students' rules, forms and deadlines for each stage of a PhD, from applying to submitting the dissertation, from the current pages of its website. |
| [Working with the Moriah computing cluster](skills/moriah-cluster/) · [on the portal](https://ai.huji.ac.il/skills/moriah-cluster/) | Research | Registering, connecting to and working with HURCS's Moriah cluster, including GPUs, storage and costs, and what to know before giving an AI agent access to it. |
| [Use HUJI's AI site](skills/huji-ai-guide/) · [on the portal](https://ai.huji.ac.il/skills/huji-ai-guide/) | General | Find information, tools and skills for your task, read current sources and identify the guidance that applies. |

<!-- catalogue:end -->

## Using a skill

Most people should start from the portal: each skill's page explains what it
does and links to its zip, and [the install guide](https://ai.huji.ac.il/skills/#install)
covers each agent app. Agents can find every skill through
<https://ai.huji.ac.il/llms.txt>. The portal's copies are public; this
repository requires signing in to `github.cs.huji.ac.il`.

Read a skill before installing it. A skill gives an agent instructions and may
include code it runs on your computer.

With access to this repository you can install from it directly.

### Claude Code

The repository is a Claude Code plugin marketplace with one plugin per skill:

```
/plugin install moriah-cluster --marketplace https://github.cs.huji.ac.il/hurcs-center/huji-skills.git
```

Or add the marketplace once and install by name:

```
/plugin marketplace add https://github.cs.huji.ac.il/hurcs-center/huji-skills.git
/plugin install moriah-cluster@huji-skills
```

### Codex and the ChatGPT apps

The repository is also a Codex plugin marketplace
(`.agents/plugins/marketplace.json`). Its one plugin, `huji-skills`, holds
every skill:

```
codex plugin marketplace add https://github.cs.huji.ac.il/hurcs-center/huji-skills.git
codex plugin add huji-skills@huji-skills
```

To take a single skill instead, copy its folder into `~/.agents/skills/`.
Each skill has an `agents/openai.yaml` with the name and description that
Codex and the ChatGPT apps show.

### Other agents

Copy `skills/<name>/` into the agent's skills folder, such as
`~/.claude/skills/` (Claude Code), `~/.agents/skills/` (Codex) or
`~/.gemini/skills/` (Gemini CLI). Any agent that follows the
[Agent Skills standard](https://agentskills.io/specification) can use them.

## For products that use these skills

Products and services (an agent on a cluster, a course assistant) can fetch
the skills in two ways:

- **From the portal, without signing in.** The portal publishes an
  [Agent Skills discovery index](https://github.com/cloudflare/agent-skills-discovery-rfc)
  at <https://ai.huji.ac.il/.well-known/agent-skills/index.json>: for each skill
  its `name`, `description`, the URL of its `SKILL.md` (a skill with no other
  files) or of a zip holding the skill's files at its root, and a SHA-256
  `digest` of that file. Poll it and fetch only the skills whose digest
  changed. <https://ai.huji.ac.il/skills-revision.txt> names the commit of
  this repository the portal last published. The portal follows `main` with
  each publish, so it can lag a merge.
- **From this repository, with Git.** Clone or fetch `main`, or pin a commit.
  A service needs credentials for `github.cs.huji.ac.il`, such as a read-only
  deploy key. Every skill is `skills/<name>/` with a `SKILL.md`;
  `scripts/check.py` keeps them to the standard.

A skill's folder name is its `name` and stays the same, so products can refer
to it.

## Layout

```
skills/<name>/SKILL.md             one folder per skill, named as its `name`
skills/<name>/...                  its scripts/, references/ and other files
skills/<name>/agents/openai.yaml   how Codex and ChatGPT show it (generated)
template/SKILL.md                  a starting point for a new skill
scripts/check.py                   checks every skill; writes the generated files
.claude-plugin/marketplace.json    the Claude Code marketplace (generated)
.agents/plugins/marketplace.json   the Codex marketplace (generated)
plugin.json                        the Codex plugin manifest (generated)
```

Skills stay in one flat `skills/` folder, as installers expect. Who a skill is
for is written in its `metadata.pillar`, not in the folder structure.

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md). In short: branch, add or change a
skill, run `uv run scripts/check.py --write`, and open a pull request to
`main`. Once it is merged, the next build of the portal publishes it.
