# /// script
# requires-python = ">=3.11"
# dependencies = ["pyyaml>=6"]
# ///
"""Check the skills and keep the generated parts of the repository current.

    uv run scripts/check.py           check; exit 1 with the problems found
    uv run scripts/check.py --write   also rewrite the README catalogue and
                                      .claude-plugin/marketplace.json

The AI portal (https://ai.huji.ac.il/) reads these skills from main when it is
built, and stops on the same rules, so a skill that passes here publishes.
"""

import json
import re
import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent.parent
SKILLS = ROOT / "skills"
README = ROOT / "README.md"
MARKETPLACE = ROOT / ".claude-plugin" / "marketplace.json"
SITE = "https://ai.huji.ac.il/"

PILLARS = {
    "students": "Students",
    "teaching": "Teaching",
    "research": "Research",
    "administration": "Administration",
    "general": "General",
}
NAME = re.compile(r"^[a-z0-9]+(-[a-z0-9]+)*$")
BEGIN, END = "<!-- catalogue:begin -->", "<!-- catalogue:end -->"


def front_matter(path: Path) -> dict:
    text = path.read_text(encoding="utf-8")
    match = re.match(r"^---\n(.*?)\n---\n", text, re.S)
    if not match:
        raise ValueError("no YAML front matter between --- lines")
    data = yaml.safe_load(match[1])
    if not isinstance(data, dict):
        raise ValueError("front matter is not a mapping")
    return data


def check_skill(folder: Path) -> tuple[dict | None, list[str]]:
    rel = folder.relative_to(ROOT)
    problems = []
    skill_md = folder / "SKILL.md"
    if not skill_md.is_file():
        return None, [f"{rel}: no SKILL.md"]
    try:
        data = front_matter(skill_md)
    except (ValueError, yaml.YAMLError) as error:
        return None, [f"{rel}/SKILL.md: {error}"]
    name = data.get("name")
    if name != folder.name:
        problems.append(f'{rel}/SKILL.md: name is "{name}", expected the folder name "{folder.name}"')
    if not NAME.match(folder.name) or len(folder.name) > 64:
        problems.append(f"{rel}: the name must be 1-64 lowercase letters, digits and single hyphens")
    description = data.get("description") or ""
    if not description:
        problems.append(f'{rel}/SKILL.md: missing "description"')
    elif len(description) > 1024:
        problems.append(f"{rel}/SKILL.md: description is {len(description)} characters, at most 1024")
    meta = data.get("metadata") or {}
    if not isinstance(meta, dict):
        meta = {}
        problems.append(f"{rel}/SKILL.md: metadata must be a mapping")
    for key in ("title", "summary", "pillar"):
        if not meta.get(key):
            problems.append(f'{rel}/SKILL.md: missing "metadata.{key}"')
    if meta.get("pillar") and meta["pillar"] not in PILLARS:
        problems.append(f'{rel}/SKILL.md: pillar is "{meta["pillar"]}", expected one of: {", ".join(PILLARS)}')
    for key, value in meta.items():
        if isinstance(value, (dict, list)):
            problems.append(f'{rel}/SKILL.md: metadata.{key} must be a plain value (the standard keeps metadata flat)')
    for path in folder.rglob("*"):
        inner = path.relative_to(folder)
        if path.is_symlink():
            problems.append(f"{rel}/{inner}: no symbolic links; copy the file in")
        elif any(part.startswith(("_", ".")) for part in inner.parts):
            # Everything here is public: maintainer notes stay out of the repository.
            problems.append(f"{rel}/{inner}: files starting with _ or . don't belong in a public skill")
    return {"name": folder.name, "description": description, **meta}, problems


def catalogue(skills: list[dict]) -> str:
    rows = [BEGIN, "", "| Skill | For | What it does |", "| --- | --- | --- |"]
    for s in sorted(skills, key=lambda s: (list(PILLARS).index(s["pillar"]), s["name"])):
        title = s.get("title_en") or s["name"]
        summary = s.get("summary_en") or s["summary"]
        rows.append(f"| [{title}](skills/{s['name']}/) · [on the portal]({SITE}skills/{s['name']}/) "
                    f"| {PILLARS[s['pillar']]} | {summary} |")
    return "\n".join(rows + ["", END])


def marketplace(skills: list[dict]) -> str:
    plugins = [{
        "name": s["name"],
        "description": s.get("summary_en") or s["description"],
        "source": "./",
        "strict": False,
        "skills": [f"./skills/{s['name']}"],
    } for s in sorted(skills, key=lambda s: s["name"])]
    data = {
        "name": "huji-skills",
        "owner": {"name": "Hebrew University AI portal"},
        "metadata": {"description": "Agent skills from the Hebrew University of Jerusalem"},
        "plugins": plugins,
    }
    return json.dumps(data, ensure_ascii=False, indent=2) + "\n"


def main() -> int:
    write = "--write" in sys.argv[1:]
    skills, problems = [], []
    for folder in sorted(p for p in SKILLS.iterdir() if p.is_dir()):
        skill, found = check_skill(folder)
        problems += found
        if skill and not found:
            skills.append(skill)
    stray = [p.name for p in SKILLS.iterdir() if p.is_file()]
    problems += [f"skills/{name}: only skill folders belong in skills/" for name in stray]
    if problems:
        print("\n".join(problems), file=sys.stderr)
        return 1

    readme = README.read_text(encoding="utf-8")
    if BEGIN not in readme or END not in readme:
        print(f"README.md: keep the {BEGIN} and {END} markers", file=sys.stderr)
        return 1
    start, end = readme.index(BEGIN), readme.index(END) + len(END)
    expected = {README: readme[:start] + catalogue(skills) + readme[end:], MARKETPLACE: marketplace(skills)}
    stale = [p for p, text in expected.items() if not p.exists() or p.read_text(encoding="utf-8") != text]
    if stale and write:
        for path in stale:
            path.parent.mkdir(exist_ok=True)
            path.write_text(expected[path], encoding="utf-8")
            print(f"updated {path.relative_to(ROOT)}")
    elif stale:
        names = ", ".join(str(p.relative_to(ROOT)) for p in stale)
        print(f"{names}: out of date; run uv run scripts/check.py --write", file=sys.stderr)
        return 1
    print(f"{len(skills)} skills OK")
    return 0


if __name__ == "__main__":
    sys.exit(main())
