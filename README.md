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
<https://ai.huji.ac.il/llms.txt>; the portal's copies are public, while this
repository requires signing in to `github.cs.huji.ac.il`.

With access to this repository you can also install from it directly:

- **Copy a folder.** Copy `skills/<name>/` into your agent's skills folder:
  `~/.claude/skills/` (Claude Code), `~/.agents/skills/` (Codex) or
  `~/.gemini/skills/` (Gemini CLI).
- **Claude Code plugin marketplace.** The repository is a marketplace with one
  plugin per skill:

  ```
  /plugin marketplace add https://github.cs.huji.ac.il/hurcs-center/huji-skills.git
  /plugin install moriah-cluster@huji-skills
  ```

Read a skill before installing it. A skill gives an agent instructions and may
include code it runs on your computer.

## Layout

```
skills/<name>/SKILL.md    one folder per skill, named as its `name`
skills/<name>/...         its scripts/, references/ and other files
template/SKILL.md         a starting point for a new skill
scripts/check.py          checks every skill; updates the catalogue above
.claude-plugin/           the Claude Code marketplace (generated)
```

Skills stay in one flat `skills/` folder, as installers expect. Who a skill is
for is written in its `metadata.pillar`, not in the folder structure.

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md). In short: branch, add or change a
skill, run `uv run scripts/check.py --write`, and open a pull request to
`main`. Once it is merged, the next build of the portal publishes it.
