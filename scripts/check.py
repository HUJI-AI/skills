# /// script
# requires-python = ">=3.11"
# dependencies = ["pyyaml>=6"]
# ///
"""Check the skills and connectors, and keep the generated files current.

    uv run scripts/check.py           check; exit 1 with the problems found
    uv run scripts/check.py --write   also rewrite the generated files: the
                                      README catalogues, each skill's
                                      agents/openai.yaml (Codex and ChatGPT),
                                      each connector's plugin versions, the
                                      Claude Code marketplace and the Codex
                                      plugin and marketplace

Skills are skills/<name>/. Connectors are plugins/<name>/: a remote MCP server
in .mcp.json, a manifest for Claude Code and one for Codex, a README and,
optionally, skills that teach the agent to use the server.

The AI portal (https://ai.huji.ac.il/) reads these skills from main when it is
built, and stops on the same rules, so a skill that passes here publishes.
"""

import hashlib
import json
import re
import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent.parent
SKILLS = ROOT / "skills"
PLUGINS = ROOT / "plugins"
README = ROOT / "README.md"
MARKETPLACE = ROOT / ".claude-plugin" / "marketplace.json"
CODEX_PLUGIN = ROOT / "plugin.json"
CODEX_MARKETPLACE = ROOT / ".agents" / "plugins" / "marketplace.json"
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
CONNECTORS_BEGIN, CONNECTORS_END = "<!-- connectors:begin -->", "<!-- connectors:end -->"
# The only dot-files a connector may have; everything else in it is public too.
PLUGIN_DOTFILES = {".mcp.json", ".claude-plugin", ".codex-plugin"}


def front_matter(path: Path) -> dict:
    text = path.read_text(encoding="utf-8")
    match = re.match(r"^---\n(.*?)\n---\n", text, re.S)
    if not match:
        raise ValueError("no YAML front matter between --- lines")
    data = yaml.safe_load(match[1])
    if not isinstance(data, dict):
        raise ValueError("front matter is not a mapping")
    return data


def check_standard_skill(folder: Path) -> tuple[dict | None, list[str]]:
    """What the Agent Skills standard asks of any skill: SKILL.md with a name
    that matches its folder and a description."""
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
    return data, problems


def check_skill(folder: Path) -> tuple[dict | None, list[str]]:
    rel = folder.relative_to(ROOT)
    data, problems = check_standard_skill(folder)
    if data is None:
        return None, problems
    description = data.get("description") or ""
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
        elif inner.as_posix() == "agents/openai.yaml":
            continue  # Codex's metadata, partly generated: see openai_yaml()
        elif any(part.startswith(("_", ".")) for part in inner.parts):
            # Everything here is public: maintainer notes stay out of the repository.
            problems.append(f"{rel}/{inner}: files starting with _ or . don't belong in a public skill")
    return {"name": folder.name, "description": description, **meta}, problems


def read_json(path: Path, problems: list[str]) -> dict:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        problems.append(f"{path.relative_to(ROOT)}: missing")
        return {}
    except json.JSONDecodeError as error:
        problems.append(f"{path.relative_to(ROOT)}: not valid JSON ({error})")
        return {}
    if not isinstance(data, dict):
        problems.append(f"{path.relative_to(ROOT)}: must be a JSON object")
        return {}
    return data


def check_plugin(folder: Path) -> tuple[dict | None, list[str]]:
    """A connector: one or more remote MCP servers, packaged so Claude Code and
    Codex install the same folder."""
    rel = folder.relative_to(ROOT)
    name, problems = folder.name, []
    if not NAME.match(name) or len(name) > 64:
        problems.append(f"{rel}: the name must be 1-64 lowercase letters, digits and single hyphens")
    readme = folder / "README.md"
    if not readme.is_file() or not readme.read_text(encoding="utf-8").strip():
        problems.append(f"{rel}/README.md: missing; say what the connector reaches, who runs the server, "
                        "how people sign in and where its privacy policy is")

    servers = read_json(folder / ".mcp.json", problems).get("mcpServers")
    hosts = []
    if not isinstance(servers, dict) or not servers:
        problems.append(f'{rel}/.mcp.json: needs an "mcpServers" map with at least one server')
        servers = {}
    for key, server in servers.items():
        where = f"{rel}/.mcp.json: {key}"
        if not isinstance(server, dict):
            problems.append(f"{where}: must be an object")
            continue
        if server.get("type") not in ("http", "sse") or "command" in server:
            # A local server would run a program on everyone's computer.
            problems.append(f'{where}: only remote servers ("type": "http" or "sse") are accepted')
        url = str(server.get("url", ""))
        if not url.startswith("https://"):
            problems.append(f"{where}: url must start with https://")
        else:
            hosts.append(url.split("/")[2])
        for header, value in (server.get("headers") or {}).items():
            if "${" not in str(value):
                # The repository is public: a header holds a placeholder, never a key.
                problems.append(f"{where}: header {header} must be a ${{...}} placeholder, not a value")

    manifests = {}
    for app in ("claude", "codex"):
        path = folder / f".{app}-plugin" / "plugin.json"
        data = read_json(path, problems)
        manifests[app] = data
        if data and data.get("name") != name:
            problems.append(f'{path.relative_to(ROOT)}: name is "{data.get("name")}", expected "{name}"')
        if data and not data.get("description"):
            problems.append(f'{path.relative_to(ROOT)}: missing "description"')

    if (folder / "skills").is_dir():
        for skill in sorted(p for p in (folder / "skills").iterdir() if p.is_dir()):
            problems += check_standard_skill(skill)[1]
    for path in folder.rglob("*"):
        inner = path.relative_to(folder)
        if path.is_symlink():
            problems.append(f"{rel}/{inner}: no symbolic links; copy the file in")
        elif inner.parts[0] in PLUGIN_DOTFILES:
            continue
        elif any(part.startswith(("_", ".")) for part in inner.parts):
            problems.append(f"{rel}/{inner}: files starting with _ or . don't belong in a public connector")
    description = manifests["claude"].get("description") or manifests["codex"].get("description") or ""
    return {"name": name, "description": description, "hosts": hosts, "manifests": manifests}, problems


def plugin_version(folder: Path) -> str:
    """1.0.0+<hash of the connector>, as for the skills: Claude Code and Codex
    cache an installed plugin by its version."""
    digest = hashlib.sha256()
    for path in sorted(p for p in folder.rglob("*") if p.is_file()):
        rel = path.relative_to(folder).as_posix()
        if rel in (".claude-plugin/plugin.json", ".codex-plugin/plugin.json"):
            continue  # their version is what this computes
        digest.update(rel.encode() + b"\0" + path.read_bytes() + b"\0")
    return f"1.0.0+{digest.hexdigest()[:12]}"


def plugin_manifests(plugin: dict) -> dict[Path, str]:
    """Each manifest as written by the contributor, with the generated parts:
    the version, and for Codex where its server config and skills are."""
    folder = PLUGINS / plugin["name"]
    version = plugin_version(folder)
    claude = {**plugin["manifests"]["claude"], "version": version}
    codex = {**plugin["manifests"]["codex"], "version": version, "mcpServers": "./.mcp.json"}
    if (folder / "skills").is_dir():
        codex["skills"] = "./skills/"
    return {folder / ".claude-plugin" / "plugin.json": json.dumps(claude, ensure_ascii=False, indent=2) + "\n",
            folder / ".codex-plugin" / "plugin.json": json.dumps(codex, ensure_ascii=False, indent=2) + "\n"}


def connectors(plugins: list[dict]) -> str:
    if not plugins:
        return "\n".join([CONNECTORS_BEGIN, "", "No connectors yet.", "", CONNECTORS_END])
    rows = [CONNECTORS_BEGIN, "", "| Connector | Server | What it does |", "| --- | --- | --- |"]
    for p in plugins:
        rows.append(f"| [{p['name']}](plugins/{p['name']}/) | {', '.join(p['hosts'])} | {p['description']} |")
    return "\n".join(rows + ["", CONNECTORS_END])


def catalogue(skills: list[dict]) -> str:
    rows = [BEGIN, "", "| Skill | For | What it does |", "| --- | --- | --- |"]
    for s in sorted(skills, key=lambda s: (list(PILLARS).index(s["pillar"]), s["name"])):
        title = s.get("title_en") or s["name"]
        summary = s.get("summary_en") or s["summary"]
        rows.append(f"| [{title}](skills/{s['name']}/) · [on the portal]({SITE}skills/{s['name']}/) "
                    f"| {PILLARS[s['pillar']]} | {summary} |")
    return "\n".join(rows + ["", END])


def openai_yaml(skill: dict) -> str:
    """agents/openai.yaml, which Codex and the ChatGPT apps read for how a
    skill appears. The name and short description come from the English
    metadata; other keys a contributor adds (policy, dependencies, icons) are
    kept."""
    path = SKILLS / skill["name"] / "agents" / "openai.yaml"
    data = yaml.safe_load(path.read_text(encoding="utf-8")) if path.exists() else None
    data = data if isinstance(data, dict) else {}
    interface = data.get("interface") if isinstance(data.get("interface"), dict) else {}
    interface.update(display_name=skill.get("title_en") or skill["title"],
                     short_description=skill.get("summary_en") or skill["summary"])
    data = {"interface": interface, **{k: v for k, v in data.items() if k != "interface"}}
    return yaml.safe_dump(data, allow_unicode=True, sort_keys=False, width=1000)


def content_version() -> str:
    """1.0.0+<hash of the skills>: Codex caches an installed plugin by its
    version, so any change to a skill gives the plugin a new one."""
    digest = hashlib.sha256()
    for path in sorted(p for p in SKILLS.rglob("*") if p.is_file()):
        rel = path.relative_to(SKILLS).as_posix()
        if rel.endswith("/agents/openai.yaml"):
            continue  # generated from SKILL.md, which is already counted
        digest.update(rel.encode() + b"\0" + path.read_bytes() + b"\0")
    return f"1.0.0+{digest.hexdigest()[:12]}"


def codex_plugin() -> str:
    """The whole repository as one Codex plugin: Codex finds the skills in
    skills/ at the plugin root."""
    return json.dumps({
        "$schema": "https://agent-plugins.org/schemas/1.0.0/plugin.schema.json",
        "name": "huji-skills",
        "version": content_version(),
        "description": "Agent skills from the Hebrew University of Jerusalem",
    }, indent=2) + "\n"


def codex_marketplace(plugins: list[dict]) -> str:
    """One Codex plugin with every skill, then one per connector."""
    entries = [{"name": "huji-skills", "path": "./"}] + [{"name": p["name"], "path": f"./plugins/{p['name']}"} for p in plugins]
    return json.dumps({
        "name": "huji-skills",
        "interface": {"displayName": "Hebrew University skills"},
        "plugins": [{
            "name": e["name"],
            "source": {"source": "local", "path": e["path"]},
            "policy": {"installation": "AVAILABLE", "authentication": "ON_INSTALL"},
            "category": "Education",
        } for e in entries],
    }, indent=2) + "\n"


def marketplace(skills: list[dict], plugins: list[dict]) -> str:
    """One Claude Code plugin per skill, then one per connector."""
    entries = [{
        "name": s["name"],
        "description": s.get("summary_en") or s["description"],
        "source": "./",
        "strict": False,
        "skills": [f"./skills/{s['name']}"],
    } for s in sorted(skills, key=lambda s: s["name"])]
    entries += [{"name": p["name"], "description": p["description"], "source": f"./plugins/{p['name']}"} for p in plugins]
    data = {
        "name": "huji-skills",
        "owner": {"name": "HUJI AI"},
        "metadata": {"description": "Agent skills and connectors from the Hebrew University of Jerusalem"},
        "plugins": entries,
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
    plugins = []
    for folder in sorted(p for p in PLUGINS.iterdir() if p.is_dir()) if PLUGINS.is_dir() else []:
        plugin, found = check_plugin(folder)
        problems += found
        if plugin and not found:
            plugins.append(plugin)
    taken = {s["name"] for s in skills} | {"huji-skills"}
    problems += [f"plugins/{p['name']}: a skill or plugin already has this name" for p in plugins if p["name"] in taken]
    if problems:
        print("\n".join(problems), file=sys.stderr)
        return 1

    readme = README.read_text(encoding="utf-8")
    for begin, end_marker, text in ((BEGIN, END, catalogue(skills)),
                                    (CONNECTORS_BEGIN, CONNECTORS_END, connectors(plugins))):
        if begin not in readme or end_marker not in readme:
            print(f"README.md: keep the {begin} and {end_marker} markers", file=sys.stderr)
            return 1
        start, end = readme.index(begin), readme.index(end_marker) + len(end_marker)
        readme = readme[:start] + text + readme[end:]
    expected = {README: readme, MARKETPLACE: marketplace(skills, plugins),
                CODEX_PLUGIN: codex_plugin(), CODEX_MARKETPLACE: codex_marketplace(plugins)}
    expected.update({SKILLS / s["name"] / "agents" / "openai.yaml": openai_yaml(s) for s in skills})
    for plugin in plugins:
        expected.update(plugin_manifests(plugin))
    stale = [p for p, text in expected.items() if not p.exists() or p.read_text(encoding="utf-8") != text]
    if stale and write:
        for path in stale:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(expected[path], encoding="utf-8")
            print(f"updated {path.relative_to(ROOT)}")
    elif stale:
        names = ", ".join(str(p.relative_to(ROOT)) for p in stale)
        print(f"{names}: out of date; run uv run scripts/check.py --write", file=sys.stderr)
        return 1
    print(f"{len(skills)} skills and {len(plugins)} connector{'' if len(plugins) == 1 else 's'} OK")
    return 0


if __name__ == "__main__":
    sys.exit(main())
