#!/usr/bin/env python3
import os
import re
import sys
from pathlib import Path
from datetime import datetime

# ==========================================
# 1. CONFIGURATION (The Recipes)
# ==========================================
# Maps Output Filename -> Persona & Input Standard Directories
# Note: 'common' is added to most to ensure base Swift rules are present.

AGENT_RECIPES = {
    "sdui.agent.md": {
        "persona": "sdui-dev.md", # Fallback for SDUI Architect
        "sources": ["sdui"], # SDUI needs Design Tokens + Schema rules
        "allowed_tags": ["sdui", "common", "design"], # Filter standards by these tags
        "description": "Specialist in Server-Driven UI (SDUI), GraphQL Schemas, and Component Mapping."
    },
    "testing.agent.md": {
        "persona": "qa-kien.md",
        "sources": ["testing", "workflows"],  # Include workflows for CI/TSan commands
        "allowed_tags": ["testing", "common", "ci"], # Test engineer doesn't need design tokens
        "description": "Specialist in Unit Testing, Mocking Strategies, and Snapshot Tests."
    },
    "swift6.agent.md": {
        "persona": "swift6-migration.md",
        "sources": ["common", "workflows"],  # Swift 6 concurrency + verification workflows
        "allowed_tags": ["swift6", "common", "ci"],  # Focus on Swift 6 and concurrency
        "description": "Incremental Swift 6 Migration Specialist. Operates in small waves, stops at module boundaries."
    }
}

# ==========================================
# 2. PATH SETUP
# ==========================================
# robustly find the project root regardless of where script is run
SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = SCRIPT_DIR.parent.parent # docs/scripts/ -> docs/ -> ROOT

PATHS = {
    "personas": PROJECT_ROOT / "docs/personas",
    "standards": PROJECT_ROOT / "docs/standards",
    "workflows": PROJECT_ROOT / "docs/standards/workflows",
    "output": PROJECT_ROOT / ".github/agents"
}

# ==========================================
# 3. HELPER FUNCTIONS
# ==========================================

def read_file(path: Path) -> str:
    """Safely reads a file. Returns None if missing."""
    if not path.exists():
        print(f"⚠️  Warning: Missing file {path.relative_to(PROJECT_ROOT)}")
        return None
    with open(path, 'r', encoding='utf-8') as f:
        return f.read()

def parse_multiline_scalar(yaml_text: str, key: str) -> str:
    """
    Parse YAML multi-line scalar (| or >) syntax.
    Returns the multiline string value, or empty string if not found.
    """
    lines = yaml_text.split('\n')
    result = []
    capturing = False
    
    for line in lines:
        if capturing:
            # Still part of multiline value if indented with 2 spaces
            if line.startswith('  ') and not line.lstrip().startswith('-'):
                result.append(line[2:])  # Remove 2-space indent
            elif line.strip() == '':
                result.append('')  # Preserve blank lines in block
            else:
                break  # End of multiline block (non-indented line)
        elif line.strip().startswith(f'{key}:') and (line.rstrip().endswith('|') or line.rstrip().endswith('>')):
            capturing = True
    
    return '\n'.join(result).strip()


def parse_frontmatter(content: str):
    """
    Splits YAML frontmatter from Markdown body.
    Returns: (metadata_dict, body_text)
    """
    # Regex to capture content between the first two --- blocks
    pattern = re.compile(r"^---\s*\n(.*?)\n---\s*\n", re.DOTALL)
    match = pattern.match(content)

    metadata = {}
    body = content

    if match:
        yaml_text = match.group(1)
        body = content[match.end():] # Everything after the second ---

        # lightweight YAML parser (avoids 'pip install pyyaml')
        current_key = None
        current_list = []
        in_list = False
        in_multiline = False
        
        for line in yaml_text.split('\n'):
            line = line.rstrip()
            
            # Skip lines while in multiline mode (handled separately)
            if in_multiline:
                if line.startswith('  ') or line.strip() == '':
                    continue  # Still in multiline block
                else:
                    in_multiline = False  # Exit multiline mode
            
            # Handle list items (starts with '  - ')
            if line.startswith('  - ') and in_list:
                current_list.append(line[4:].strip().strip('"').strip("'"))
                continue
            
            # End of list, store it
            if in_list and not line.startswith('  '):
                if current_key:
                    metadata[current_key] = current_list
                in_list = False
                current_key = None
                current_list = []
            
            if ':' in line:
                key, val = line.split(':', 1)
                key = key.strip()
                val = val.strip().strip('"').strip("'")

                # Handle inline list syntax: tags: [swift6, uikit]
                if val.startswith('[') and val.endswith(']'):
                    metadata[key] = [x.strip() for x in val[1:-1].split(',')]
                # Handle multi-line scalar syntax: summary: |
                elif val == '|' or val == '>':
                    multiline_content = parse_multiline_scalar(yaml_text, key)
                    metadata[key] = multiline_content
                    in_multiline = True
                # Handle multi-line list syntax
                elif not val or val == '':
                    current_key = key
                    current_list = []
                    in_list = True
                else:
                    metadata[key] = val
        
        # Handle case where list is at end of frontmatter
        if in_list and current_key:
            metadata[current_key] = current_list

    return metadata, body.strip()

def resolve_verification_link(link: str) -> Path:
    """
    Resolves 'related_verification' links.
    Can handle relative paths ('verify_tests.md') or full paths ('docs/standards/workflows/...')
    """
    if not link or not isinstance(link, str) or link.strip().lower() == 'null':
        return None
    link = link.strip()

    # If it looks like a full path
    if link.startswith("docs/"):
        return PROJECT_ROOT / link

    # Otherwise assume it's in the default workflows dir
    return PATHS["workflows"] / link

def tags_match(file_tags, allowed_tags):
    """
    Check if any file tags match the allowed tags list.
    Returns True if there's at least one match or if file has no tags (include by default).
    """
    if not file_tags:
        return True  # Include files without tags
    
    if isinstance(file_tags, str):
        file_tags = [file_tags]
    
    # Check for intersection between file tags and allowed tags
    return bool(set(file_tags) & set(allowed_tags))

def parse_rule_structure(rule: str) -> str:
    """
    Parse a stitcher_rule string and extract structured fields.
    
    Expected formats:
      "RULE: Name | ACTION: Do X | SEVERITY: CRITICAL"
      "STEP: Name | CMD: command here | SEVERITY: CRITICAL"
      "CMD: Description | ACTION: command here | SEVERITY: WARN"
      "BENEFIT: Description | ACTION: benefit text | SEVERITY: WARN"
    
    Returns formatted string optimized for agent consumption.
    """
    import re
    
    # Extract all field: value pairs
    fields = {}
    pattern = r'(\w+):\s*([^|]+)'
    matches = re.findall(pattern, rule)
    
    for field, value in matches:
        fields[field.strip().upper()] = value.strip()
    
    # Determine primary type
    rule_type = None
    for key in ['RULE', 'STEP', 'CMD', 'BENEFIT']:
        if key in fields:
            rule_type = key
            break
    
    if not rule_type:
        return rule  # Fallback: return original if unparsable
    
    # Build formatted output
    severity = fields.get('SEVERITY', 'WARN')
    name = fields.get(rule_type, '')
    action = fields.get('ACTION', '')
    cmd = fields.get('CMD', '')
    benefit = fields.get('BENEFIT', '')
    
    # Format based on type
    parts = [f"[{severity}]"]
    
    if rule_type == 'CMD':
        parts.append(f"CMD: {name}")
        if action:
            parts.append(f"→ {action}")
    elif rule_type == 'BENEFIT':
        parts.append(f"BENEFIT: {name}")
        if action:
            parts.append(f"→ {action}")
    elif rule_type == 'STEP':
        parts.append(f"STEP: {name}")
        if cmd:
            parts.append(f"CMD: {cmd}")
        elif action:
            parts.append(f"→ {action}")
    else:  # RULE
        parts.append(f"{name}")
        if action:
            parts.append(f"→ {action}")
        if cmd:
            parts.append(f"CMD: {cmd}")
    
    return " | ".join(parts)

def get_rule_type(rule: str) -> str:
    """
    Extract the rule type (RULE, STEP, CMD, BENEFIT) from a stitcher_rule string.
    Returns 'RULE' by default.
    """
    import re
    
    # Check for explicit type markers
    for rule_type in ['RULE', 'STEP', 'CMD', 'BENEFIT']:
        if re.match(rf'{rule_type}:\s*', rule, re.IGNORECASE):
            return rule_type
    
    return 'RULE'  # Default

# ==========================================
# 4. MAIN STITCHER LOGIC
# ==========================================

def stitch_agent(filename, recipe):
    print(f"\n🧵 Stitching Brain: {filename}...")

    # --- A. PREPARE BUFFER WITH FRONTMATTER ---
    output_buffer = []
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    # Generate agent name from filename (remove .agent.md extension)
    agent_name = filename.replace('.agent.md', '').replace('-', ' ').title()
    agent_id = filename.replace('.agent.md', '')
    
    # Add GitHub Copilot agent frontmatter
    output_buffer.append("---")
    output_buffer.append(f"agent: {agent_id}")
    output_buffer.append(f"name: {agent_name}")
    output_buffer.append(f"description: {recipe['description']}")
    output_buffer.append(f"version: 1.0.0")
    output_buffer.append(f"generated: {timestamp}")
    output_buffer.append(f"tags: {', '.join(recipe['allowed_tags'])}")
    output_buffer.append("---")
    output_buffer.append("")

    # --- B. INJECT IDENTITY (Persona) ---
    persona_path = PATHS["personas"] / recipe["persona"]
    persona_content = read_file(persona_path)

    if persona_content:
        # Strip frontmatter from persona (we don't need its metadata)
        _, p_body = parse_frontmatter(persona_content)
        output_buffer.append(p_body)
    else:
        output_buffer.append(f"# IDENTITY\nYou are the {recipe['description']}")

    output_buffer.append("\n---\n")

    # --- C. COLLECT ALL RULES (First Pass) ---
    allowed_tags = recipe.get("allowed_tags", [])
    collected_verification_paths = set()
    
    # Separate buckets for different rule types
    law_rules = []  # RULE types
    loop_rules = []  # STEP, CMD, BENEFIT types
    
    for source_dir_name in recipe["sources"]:
        source_path = PATHS["standards"] / source_dir_name

        if not source_path.exists():
            print(f"⚠️  Skipping missing directory: {source_dir_name}")
            continue

        # Sort files to ensure deterministic output
        files = sorted(source_path.glob("*.md"))

        for file_path in files:
            # Skip readme files
            if file_path.name.lower() == "readme.md": continue

            raw_content = read_file(file_path)
            if not raw_content:
                continue
                
            meta, body = parse_frontmatter(raw_content)

            # FILTER BY TAGS: Skip if tags don't match allowed list
            file_tags = meta.get('tags', [])
            if not tags_match(file_tags, allowed_tags):
                print(f"⏭️  Skipping {file_path.name} - tags {file_tags} don't match {allowed_tags}")
                continue

            # EXTRACT STITCHER RULES AND CATEGORIZE
            stitcher_rules = meta.get('stitcher_rules', [])
            if stitcher_rules:
                relative_path = file_path.relative_to(PROJECT_ROOT)
                
                # Separate rules by type
                file_law_rules = []
                file_loop_rules = []
                
                for rule in stitcher_rules:
                    formatted_rule = parse_rule_structure(rule)
                    rule_type = get_rule_type(rule)
                    
                    if rule_type == 'RULE':
                        file_law_rules.append(formatted_rule)
                    else:  # STEP, CMD, BENEFIT
                        file_loop_rules.append(formatted_rule)
                
                # Store with source path
                if file_law_rules:
                    law_rules.append((relative_path, file_law_rules))
                if file_loop_rules:
                    loop_rules.append((relative_path, file_loop_rules))

            # COLLECT VERIFICATION LINKS
            if 'related_verification' in meta:
                links = meta['related_verification']
                if isinstance(links, str): links = [links]

                for link in links:
                    v_path = resolve_verification_link(link)
                    if v_path and v_path.exists():
                        collected_verification_paths.add(v_path)
                    elif v_path:
                        print(f"❌ Broken Link in {file_path.name}: {link}")
    
    total_rules = sum(len(rules) for _, rules in law_rules) + sum(len(rules) for _, rules in loop_rules)
    print(f"📋 Extracted {total_rules} stitcher rules ({len(law_rules)} law files, {len(loop_rules)} loop files)")
    
    # --- D. INJECT THE LAW (Practices & Constraints) ---
    if law_rules:
        output_buffer.append("# 🏛️ THE LAW (Stitcher Rules)\n")
        output_buffer.append(f"> **Role Context:** {recipe['description']}")
        output_buffer.append("> **Strictness:** You must adhere to the following standards without deviation.\n")
        output_buffer.append("> **Format:** RULE types define constraints during development.\n")
        
        for source_path, rules in law_rules:
            output_buffer.append(f"\n## From: {source_path.as_posix()}\n")
            for rule in rules:
                output_buffer.append(f"- {rule}")
            output_buffer.append(f"\n*(Source: {source_path.as_posix()})*\n")
    
    output_buffer.append("\n---\n")

    # --- E. INJECT THE LOOP (Verification Process) ---
    output_buffer.append("# 🔄 THE LOOP (Verification Process)\n")
    output_buffer.append("> **Constraint:** Before finishing any task, you must run these verification steps.\n")
    
    # E1. Quick Commands (STEP, CMD, BENEFIT)
    if loop_rules:
        output_buffer.append("\n## Quick Commands & Steps\n")
        output_buffer.append("> **Format:** Executable commands and verification steps.\n")
        
        for source_path, rules in loop_rules:
            output_buffer.append(f"\n### From: {source_path.as_posix()}\n")
            for rule in rules:
                output_buffer.append(f"- {rule}")
            output_buffer.append(f"\n*(Source: {source_path.as_posix()})*\n")
    
    # E2. Detailed Workflows (from related_verification)
    if collected_verification_paths:
        output_buffer.append("\n## Detailed Workflows\n")
        output_buffer.append("> **Format:** Full verification procedures extracted from related_verification links.\n")

        for v_path in sorted(list(collected_verification_paths)):
            v_raw = read_file(v_path)
            v_meta, v_body = parse_frontmatter(v_raw)

            output_buffer.append(f"\n### Verify: {v_path.stem}")
            
            # Use summary if available, otherwise first 15 lines of body
            summary = v_meta.get('summary', '')
            if summary:
                output_buffer.append(f"\n**Quick Reference:**\n{summary.strip()}")
            else:
                # Fallback: first 15 lines + truncation notice
                lines = v_body.split('\n')[:15]
                output_buffer.append('\n'.join(lines))
                if len(v_body.split('\n')) > 15:
                    output_buffer.append('\n...(truncated)')
            
            # Add reference link with explicit guidance to reduce hallucination
            rel_path = v_path.relative_to(PROJECT_ROOT)
            output_buffer.append(f"\n\n⚠️ **For troubleshooting or edge cases:** Use `view` tool to read `{rel_path}` before improvising commands.\n")

    # --- E. WRITE TO DISK ---
    if not PATHS["output"].exists():
        os.makedirs(PATHS["output"])

    output_file = PATHS["output"] / filename
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write("\n".join(output_buffer))

    file_line_count = len(output_buffer)
    print(f"✅ Created {filename} ({file_line_count} lines, {len(collected_verification_paths)} workflows)")

# ==========================================
# 5. ENTRY POINT
# ==========================================
if __name__ == "__main__":
    print(f"🧠 Stitcher Initialized at: {PROJECT_ROOT}")
    for agent_file, recipe in AGENT_RECIPES.items():
        stitch_agent(agent_file, recipe)
    print("✨ All Agents Compiled Successfully.")
