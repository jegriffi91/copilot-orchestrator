#!/usr/bin/env python3
"""
Unified publish pipeline for copilot-orchestrator.

Subcommands:
  agents  — Compile agents from personas + standards → .copilot/agents/
  skills  — Publish skills + references to vendor dirs → .copilot/skills/
  all     — Run both agents and skills

Replaces the former stitch-brain.py (agents only) and the planned-but-never-built
publish-skills.py.

Usage:
  python3 docs/scripts/publish.py agents
  python3 docs/scripts/publish.py skills
  python3 docs/scripts/publish.py all
"""

import argparse
import os
import re
import sys
import shutil
from pathlib import Path
from datetime import datetime

# ==========================================
# 1. CONFIGURATION
# ==========================================

SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = SCRIPT_DIR.parent.parent  # docs/scripts/ → docs/ → ROOT

PATHS = {
    "personas":  PROJECT_ROOT / "docs/personas",
    "standards": PROJECT_ROOT / "docs/standards",
    "workflows": PROJECT_ROOT / "docs/workflows",
    "skills_source": PROJECT_ROOT / "docs/skills",
    "agents_output": PROJECT_ROOT / ".copilot/agents",
    "skills_output": PROJECT_ROOT / ".copilot/skills",
}

# Agent Recipes: maps output filename → persona + sources + tags + skills
AGENT_RECIPES = {
    "sdui.agent.md": {
        "persona": "sdui-dev.md",
        "sources": ["sdui"],
        "allowed_tags": ["sdui", "common", "design"],
        "skills": [],
        "description": "Specialist in Server-Driven UI (SDUI), GraphQL Schemas, and Component Mapping.",
    },
    "testing.agent.md": {
        "persona": "qa-kien.md",
        "sources": ["testing"],
        "allowed_tags": ["testing", "common", "ci"],
        "skills": [],
        "description": "Specialist in Unit Testing, Mocking Strategies, and Snapshot Tests.",
    },
    "swift6.agent.md": {
        "persona": "swift6-migration.md",
        "sources": ["common"],
        "allowed_tags": ["swift6", "common", "ci"],
        "skills": ["swift6"],
        "description": "Incremental Swift 6 Migration Specialist. Operates in small waves, stops at module boundaries.",
    },
    "ui.agent.md": {
        "persona": "ui-dev.md",
        "sources": ["common", "design"],
        "allowed_tags": ["common", "design", "swiftui"],
        "skills": ["swiftui"],
        "description": "SwiftUI UI Development Specialist. Builds modern, performant, accessible interfaces.",
    },
}

# YAML frontmatter fields that are preserved during shadow frontmatter.
# Non-standard fields are stripped for vendor compatibility.
ALLOWED_FRONTMATTER_KEYS = {"name", "description"}


# ==========================================
# 2. SHARED HELPERS
# ==========================================

def read_file(path: Path) -> str | None:
    """Safely reads a file. Returns None if missing."""
    if not path.exists():
        print(f"  ⚠️  Missing: {path.relative_to(PROJECT_ROOT)}")
        return None
    with open(path, "r", encoding="utf-8") as f:
        return f.read()


def parse_frontmatter(content: str) -> tuple[dict, str]:
    """
    Splits YAML frontmatter from Markdown body.
    Returns: (metadata_dict, body_text)
    """
    pattern = re.compile(r"^---\s*\n(.*?)\n---\s*\n", re.DOTALL)
    match = pattern.match(content)

    metadata = {}
    body = content

    if match:
        yaml_text = match.group(1)
        body = content[match.end():]

        current_key = None
        current_list = []
        in_list = False
        in_multiline = False

        for line in yaml_text.split("\n"):
            line = line.rstrip()

            if in_multiline:
                if line.startswith("  ") or line.strip() == "":
                    continue
                else:
                    in_multiline = False

            if line.startswith("  - ") and in_list:
                current_list.append(line[4:].strip().strip('"').strip("'"))
                continue

            if in_list and not line.startswith("  "):
                if current_key:
                    metadata[current_key] = current_list
                in_list = False
                current_key = None
                current_list = []

            if ":" in line:
                key, val = line.split(":", 1)
                key = key.strip()
                val = val.strip().strip('"').strip("'")

                if val.startswith("[") and val.endswith("]"):
                    metadata[key] = [x.strip() for x in val[1:-1].split(",")]
                elif val in ("|", ">"):
                    metadata[key] = _parse_multiline_scalar(yaml_text, key)
                    in_multiline = True
                elif not val:
                    current_key = key
                    current_list = []
                    in_list = True
                else:
                    metadata[key] = val

        if in_list and current_key:
            metadata[current_key] = current_list

    return metadata, body.strip()


def _parse_multiline_scalar(yaml_text: str, key: str) -> str:
    """Parse YAML multi-line scalar (| or >) syntax."""
    lines = yaml_text.split("\n")
    result = []
    capturing = False

    for line in lines:
        if capturing:
            if line.startswith("  ") and not line.lstrip().startswith("-"):
                result.append(line[2:])
            elif line.strip() == "":
                result.append("")
            else:
                break
        elif line.strip().startswith(f"{key}:") and (
            line.rstrip().endswith("|") or line.rstrip().endswith(">")
        ):
            capturing = True

    return "\n".join(result).strip()


def shadow_frontmatter(content: str) -> str:
    """
    Strip non-standard YAML fields from frontmatter for vendor compatibility.
    Preserves only ALLOWED_FRONTMATTER_KEYS. Non-standard fields are injected
    as an HTML comment (<!-- SKILL_METADATA ... -->) so LLMs can still read them.
    This follows the Shadow Frontmatter pattern from ADR-002.
    """
    meta, body = parse_frontmatter(content)
    if not meta:
        return content

    safe = {k: v for k, v in meta.items() if k in ALLOWED_FRONTMATTER_KEYS}
    unsafe = {k: v for k, v in meta.items() if k not in ALLOWED_FRONTMATTER_KEYS}

    lines = []
    if safe:
        lines.append("---")
        for k, v in safe.items():
            lines.append(f"{k}: {v}")
        lines.append("---")
        lines.append("")

    # Inject non-standard fields as HTML comment per ADR-002
    if unsafe:
        lines.append("<!-- SKILL_METADATA")
        for k, v in unsafe.items():
            if isinstance(v, list):
                lines.append(f"{k}: [{', '.join(v)}]")
            else:
                lines.append(f"{k}: {v}")
        lines.append("-->")
        lines.append("")

    lines.append(body)
    return "\n".join(lines)


# ==========================================
# 3. AGENTS SUBCOMMAND
# ==========================================

def tags_match(file_tags, allowed_tags: list) -> bool:
    """Check if file tags intersect with allowed tags."""
    if not file_tags:
        return True
    if isinstance(file_tags, str):
        file_tags = [file_tags]
    return bool(set(file_tags) & set(allowed_tags))


def parse_rule_structure(rule: str) -> str:
    """Parse a stitcher_rule and format for agent consumption."""
    fields = {}
    pattern = r"(\w+):\s*([^|]+)"
    matches = re.findall(pattern, rule)
    for field, value in matches:
        fields[field.strip().upper()] = value.strip()

    rule_type = None
    for key in ["RULE", "STEP", "CMD", "BENEFIT"]:
        if key in fields:
            rule_type = key
            break
    if not rule_type:
        return rule

    severity = fields.get("SEVERITY", "WARN")
    name = fields.get(rule_type, "")
    action = fields.get("ACTION", "")
    cmd = fields.get("CMD", "")

    parts = [f"[{severity}]"]

    if rule_type == "CMD":
        parts.append(f"CMD: {name}")
        if action:
            parts.append(f"→ {action}")
    elif rule_type == "BENEFIT":
        parts.append(f"BENEFIT: {name}")
        if action:
            parts.append(f"→ {action}")
    elif rule_type == "STEP":
        parts.append(f"STEP: {name}")
        if cmd:
            parts.append(f"CMD: {cmd}")
        elif action:
            parts.append(f"→ {action}")
    else:
        parts.append(f"{name}")
        if action:
            parts.append(f"→ {action}")
        if cmd:
            parts.append(f"CMD: {cmd}")

    return " | ".join(parts)


def get_rule_type(rule: str) -> str:
    """Extract rule type (RULE, STEP, CMD, BENEFIT) from a stitcher_rule."""
    for rt in ["RULE", "STEP", "CMD", "BENEFIT"]:
        if re.match(rf"{rt}:\s*", rule, re.IGNORECASE):
            return rt
    return "RULE"


def resolve_verification_link(link: str) -> Path | None:
    """Resolve verification link to filesystem path."""
    if not link or not isinstance(link, str) or link.strip().lower() == "null":
        return None
    link = link.strip()
    if link.startswith("docs/"):
        return PROJECT_ROOT / link
    return PATHS["workflows"] / link


def stitch_agent(filename: str, recipe: dict, dry_run: bool = False) -> dict:
    """Compile a single agent from persona + standards + skills.
    Returns a validation report dict for summary output.
    """
    print(f"\n🧵 Compiling Agent: {filename}...")

    report = {"agent": filename, "warnings": [], "rules": 0, "skills": 0}
    buf = []
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    agent_name = filename.replace(".agent.md", "").replace("-", " ").title()
    agent_id = filename.replace(".agent.md", "")

    # --- Frontmatter ---
    buf.append("---")
    buf.append(f"agent: {agent_id}")
    buf.append(f"name: {agent_name}")
    buf.append(f"description: {recipe['description']}")
    buf.append("version: 1.0.0")
    buf.append(f"generated: {timestamp}")
    buf.append(f"tags: {', '.join(recipe['allowed_tags'])}")
    buf.append("---")
    buf.append("")

    # --- IDENTITY (Persona) ---
    persona_path = PATHS["personas"] / recipe["persona"]
    persona_content = read_file(persona_path)
    if persona_content:
        _, p_body = parse_frontmatter(persona_content)
        buf.append(p_body)
    else:
        report["warnings"].append(f"Missing persona: {recipe['persona']}")
        buf.append(f"# IDENTITY\nYou are the {recipe['description']}")
    buf.append("\n---\n")

    # --- Collect Rules ---
    allowed_tags = recipe.get("allowed_tags", [])
    collected_verification_paths = set()
    law_rules = []
    loop_rules = []

    for source_dir_name in recipe["sources"]:
        source_path = PATHS["standards"] / source_dir_name
        if not source_path.exists():
            report["warnings"].append(f"Missing standards dir: {source_dir_name}/")
            print(f"  ⚠️  Skipping missing standards dir: {source_dir_name}")
            continue
        md_files = list(source_path.glob("*.md"))
        non_readme = [f for f in md_files if f.name.lower() != "readme.md"]
        if not non_readme:
            report["warnings"].append(f"Empty standards dir: {source_dir_name}/ (no .md files)")

        for file_path in sorted(source_path.glob("*.md")):
            if file_path.name.lower() == "readme.md":
                continue

            raw_content = read_file(file_path)
            if not raw_content:
                continue

            meta, body = parse_frontmatter(raw_content)
            file_tags = meta.get("tags", [])
            if not tags_match(file_tags, allowed_tags):
                continue

            stitcher_rules = meta.get("stitcher_rules", [])
            if stitcher_rules:
                relative_path = file_path.relative_to(PROJECT_ROOT)
                file_law = []
                file_loop = []
                for rule in stitcher_rules:
                    formatted = parse_rule_structure(rule)
                    if get_rule_type(rule) == "RULE":
                        file_law.append(formatted)
                    else:
                        file_loop.append(formatted)
                if file_law:
                    law_rules.append((relative_path, file_law))
                if file_loop:
                    loop_rules.append((relative_path, file_loop))

            if "related_verification" in meta:
                links = meta["related_verification"]
                if isinstance(links, str):
                    links = [links]
                for link in links:
                    v_path = resolve_verification_link(link)
                    if v_path and v_path.exists():
                        collected_verification_paths.add(v_path)

    total_rules = sum(len(r) for _, r in law_rules) + sum(
        len(r) for _, r in loop_rules
    )
    report["rules"] = total_rules
    print(
        f"  📋 Extracted {total_rules} rules ({len(law_rules)} law + {len(loop_rules)} loop files)"
    )

    # --- THE LAW ---
    if law_rules:
        buf.append("# 🏛️ THE LAW (Stitcher Rules)\n")
        buf.append(f"> **Role Context:** {recipe['description']}")
        buf.append("> **Strictness:** Adhere without deviation.\n")
        for source_path, rules in law_rules:
            buf.append(f"\n## From: {source_path.as_posix()}\n")
            for rule in rules:
                buf.append(f"- {rule}")
    buf.append("\n---\n")

    # --- THE LOOP ---
    buf.append("# 🔄 THE LOOP (Verification Process)\n")
    buf.append("> Before finishing any task, run these verification steps.\n")

    if loop_rules:
        buf.append("\n## Quick Commands & Steps\n")
        for source_path, rules in loop_rules:
            buf.append(f"\n### From: {source_path.as_posix()}\n")
            for rule in rules:
                buf.append(f"- {rule}")

    if collected_verification_paths:
        buf.append("\n## Detailed Workflows\n")
        for v_path in sorted(list(collected_verification_paths)):
            v_raw = read_file(v_path)
            if not v_raw:
                continue
            v_meta, v_body = parse_frontmatter(v_raw)
            buf.append(f"\n### Verify: {v_path.stem}")
            summary = v_meta.get("summary", "")
            if summary:
                buf.append(f"\n**Quick Reference:**\n{summary.strip()}")
            else:
                lines = v_body.split("\n")[:15]
                buf.append("\n".join(lines))
                if len(v_body.split("\n")) > 15:
                    buf.append("\n...(truncated)")
            rel_path = v_path.relative_to(PROJECT_ROOT)
            buf.append(
                f"\n\n⚠️ **For troubleshooting:** Read `{rel_path}` before improvising.\n"
            )

    # --- SKILLS Section ---
    skills = recipe.get("skills", [])
    report["skills"] = len(skills)
    if skills:
        buf.append("\n---\n")
        buf.append("# 🛠️ SKILLS (Runtime Loading)\n")
        buf.append(
            "> You can load these skills on-demand for domain-specific guidance.\n"
        )
        for skill_name in skills:
            skill_path = PATHS["skills_source"] / skill_name / "SKILL.md"
            if skill_path.exists():
                meta, _ = parse_frontmatter(read_file(skill_path))
                desc = meta.get("description", "No description.")
                buf.append(f"- **{skill_name}** — {desc}")
            else:
                report["warnings"].append(f"Missing skill: {skill_name}/SKILL.md")
                buf.append(f"- **{skill_name}** — _(skill not found)_")
        buf.append(
            "\n> To load a skill, read `docs/skills/<name>/SKILL.md`.\n"
        )

    # --- Write ---
    if dry_run:
        print(f"  🔍 [DRY RUN] Would write {filename} ({len(buf)} lines)")
    else:
        PATHS["agents_output"].mkdir(parents=True, exist_ok=True)
        output_file = PATHS["agents_output"] / filename
        with open(output_file, "w", encoding="utf-8") as f:
            f.write("\n".join(buf))

    print(
        f"  ✅ {filename} ({len(buf)} lines, {len(collected_verification_paths)} workflows, {len(skills)} skills)"
    )
    return report


def publish_agents(dry_run: bool = False) -> None:
    """Compile all agents from recipes."""
    print("═" * 50)
    print(f"📦 PUBLISHING AGENTS{' [DRY RUN]' if dry_run else ''}")
    print("═" * 50)
    reports = []
    for agent_file, recipe in AGENT_RECIPES.items():
        report = stitch_agent(agent_file, recipe, dry_run=dry_run)
        reports.append(report)

    # --- Validation Summary ---
    all_warnings = [(r["agent"], w) for r in reports for w in r["warnings"]]
    if all_warnings:
        print(f"\n{'─' * 50}")
        print(f"⚠️  VALIDATION SUMMARY ({len(all_warnings)} issues)")
        print(f"{'─' * 50}")
        for agent, warning in all_warnings:
            print(f"  {agent}: {warning}")
        print()

    print(f"✨ {len(AGENT_RECIPES)} agents compiled → {PATHS['agents_output']}")


# ==========================================
# 4. SKILLS SUBCOMMAND
# ==========================================

def publish_skills(dry_run: bool = False) -> None:
    """Publish skills + references to vendor output directories."""
    print("═" * 50)
    print(f"📦 PUBLISHING SKILLS{' [DRY RUN]' if dry_run else ''}")
    print("═" * 50)

    skills_source = PATHS["skills_source"]
    skills_output = PATHS["skills_output"]
    catalog_entries = []

    for skill_dir in sorted(skills_source.iterdir()):
        if not skill_dir.is_dir():
            continue

        skill_file = skill_dir / "SKILL.md"
        if not skill_file.exists():
            continue

        content = read_file(skill_file)
        if not content:
            continue

        meta, _ = parse_frontmatter(content)
        skill_name = meta.get("name", skill_dir.name)
        skill_desc = meta.get("description", "No description.")

        if not meta.get("name"):
            print(f"  ⚠️  {skill_dir.name}/SKILL.md missing 'name' in frontmatter")
        if not meta.get("description"):
            print(
                f"  ⚠️  {skill_dir.name}/SKILL.md missing 'description' in frontmatter"
            )

        # Apply shadow frontmatter
        published_content = shadow_frontmatter(content)

        if dry_run:
            print(f"  🔍 [DRY RUN] Would publish {skill_dir.name}")
        else:
            # Copy SKILL.md
            target_dir = skills_output / skill_dir.name
            target_dir.mkdir(parents=True, exist_ok=True)
            (target_dir / "SKILL.md").write_text(published_content, encoding="utf-8")

            # Copy subdirectories (references/, templates/, etc.)
            copied_subdirs = []
            for subdir in sorted(skill_dir.iterdir()):
                if subdir.is_dir() and not subdir.name.startswith("."):
                    target_subdir = target_dir / subdir.name
                    if target_subdir.exists():
                        shutil.rmtree(target_subdir)
                    shutil.copytree(subdir, target_subdir)
                    file_count = sum(1 for _ in subdir.rglob("*") if _.is_file())
                    copied_subdirs.append(f"{subdir.name}({file_count})")

            subdirs_str = ", ".join(copied_subdirs) if copied_subdirs else "no subdirs"
            print(f"  ✅ {skill_dir.name} → {subdirs_str}")

        catalog_entries.append(
            {"name": skill_name, "description": skill_desc, "dir": skill_dir.name}
        )

    # Generate catalog
    if not dry_run:
        _generate_catalog(catalog_entries, skills_output)
    print(
        f"\n✨ {len(catalog_entries)} skills {'would be ' if dry_run else ''}published → {skills_output}"
    )


def _generate_catalog(entries: list[dict], output_dir: Path) -> None:
    """Generate _skill_catalog.md discovery index."""
    lines = [
        "# Skill Catalog",
        "",
        f"> Auto-generated by `publish.py` on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        "> Do not edit manually — changes will be overwritten.",
        "",
        "| Skill | Directory | Description |",
        "|-------|-----------|-------------|",
    ]
    for entry in entries:
        lines.append(
            f"| {entry['name']} | `{entry['dir']}/` | {entry['description']} |"
        )
    lines.append("")

    output_dir.mkdir(parents=True, exist_ok=True)
    catalog_path = output_dir / "_skill_catalog.md"
    catalog_path.write_text("\n".join(lines), encoding="utf-8")
    print(f"  📋 Catalog: {catalog_path.relative_to(PROJECT_ROOT)}")


# ==========================================
# 5. ENTRY POINT
# ==========================================

def main():
    parser = argparse.ArgumentParser(
        description="Unified publish pipeline for copilot-orchestrator.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python3 publish.py agents          Compile agents from personas + standards
  python3 publish.py skills          Publish skills + references to vendor dirs
  python3 publish.py all             Run both agents and skills
  python3 publish.py agents --dry-run  Preview agent compilation without writing
""",
    )
    parser.add_argument(
        "command",
        choices=["agents", "skills", "all"],
        help="Subcommand to run",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Preview what would be generated without writing files",
    )
    args = parser.parse_args()

    print(f"🧠 Publish Pipeline — {PROJECT_ROOT}")
    if args.dry_run:
        print("🔍 DRY RUN MODE — no files will be written")
    print()

    if args.command == "agents":
        publish_agents(dry_run=args.dry_run)
    elif args.command == "skills":
        publish_skills(dry_run=args.dry_run)
    elif args.command == "all":
        publish_agents(dry_run=args.dry_run)
        print()
        publish_skills(dry_run=args.dry_run)


if __name__ == "__main__":
    main()
