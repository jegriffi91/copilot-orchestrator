#!/usr/bin/env python3
"""
Xcodebuild Output Distillation Pipeline

Purpose: Transform bloated xcodebuild output into token-efficient, actionable
         Markdown or JSON payloads suitable for AI agent context windows.

Subcommands:
    discover  — List workspace schemes, targets, and module topology
    compile   — Distill compiler errors/warnings from piped xcodebuild output
    test      — Extract test failures from .xcresult bundles
    tsan      — Run/parse TSan output (delegates to tsan-sanitizer.py)

Usage:
    # Discover workspace structure (always run first)
    python3 xcode-distill.py discover --workspace MyApp.xcworkspace

    # Distill compilation output
    xcodebuild build -scheme MyApp ... 2>&1 | python3 xcode-distill.py compile

    # Extract test failures from xcresult bundle
    python3 xcode-distill.py test --path ./Build/Results.xcresult

    # Run TSan with distilled output
    python3 xcode-distill.py tsan --scheme MyApp --target MyTests

Design:
    - All file paths in output are project-relative (never absolute)
    - Output capped at --max-issues (default: 20) to prevent context bloat
    - Circuit breaker: --attempt N triggers revert instructions at N >= 3
    - System framework stack frames are pruned automatically
"""

import argparse
import json
import os
import re
import subprocess
import sys
from collections import defaultdict
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple


# ---------------------------------------------------------------------------
# Shared utilities
# ---------------------------------------------------------------------------

# System framework patterns to prune from stack traces
SYSTEM_FRAME_PATTERNS = [
    r"libsystem_",
    r"libdispatch",
    r"libobjc",
    r"Foundation",
    r"UIKit",
    r"SwiftUI",
    r"CoreFoundation",
    r"CoreData",
    r"_dispatch_",
    r"objc_msgSend",
    r"swift_task_",
    r"swift_job_",
    r"__CFRunLoop",
    r"_pthread_",
    r"start_wqthread",
    r"_NSCallStack",
    r"libswiftCore",
    r"libswift_Concurrency",
    r"libsystem_pthread",
    r"AttributeGraph",
    r"GraphicsServices",
    r"RunningBoardServices",
    r"/usr/lib/",
    r"/System/Library/",
    r"Xcode\.app/Contents/",
]

SYSTEM_FRAME_RE = re.compile("|".join(SYSTEM_FRAME_PATTERNS))


def is_system_frame(frame: str) -> bool:
    """Return True if a stack frame belongs to a system/OS library."""
    return bool(SYSTEM_FRAME_RE.search(frame))


def relativize_path(abs_path: str, source_root: Optional[str] = None) -> str:
    """Strip absolute path prefix, returning project-relative path."""
    if not abs_path:
        return abs_path

    if source_root:
        try:
            return str(Path(abs_path).relative_to(source_root))
        except ValueError:
            pass

    # Heuristic: find common project indicators and strip everything before
    parts = abs_path.replace("\\", "/").split("/")
    for i, part in enumerate(parts):
        # Stop at first directory that looks like a source root
        if part.endswith((".xcworkspace", ".xcodeproj")):
            return "/".join(parts[i + 1 :])
        # Common source directories
        if part in ("Sources", "Source", "src", "App", "Modules", "Packages"):
            return "/".join(parts[i:])

    # Fallback: just use the basename
    return Path(abs_path).name


def format_circuit_breaker(attempt: int) -> str:
    """Generate circuit breaker section if attempt threshold reached."""
    if attempt < 3:
        return ""
    return (
        "\n## ⛔ CIRCUIT BREAKER — Attempt {attempt} (max 3)\n\n"
        "**You have exceeded the maximum remediation attempts for this file.**\n\n"
        "### Required Actions:\n"
        "1. `git stash` or `git checkout -- <files>` to revert your changes\n"
        "2. Open a **Draft PR** with the partially-fixed code\n"
        "3. Tag the PR with `#requires-human-architect`\n"
        "4. Include this distilled error report in the PR description\n"
        "5. **STOP** — do not attempt further automated fixes\n"
    ).format(attempt=attempt)


# ---------------------------------------------------------------------------
# Subcommand: discover
# ---------------------------------------------------------------------------


def cmd_discover(args: argparse.Namespace) -> None:
    """List workspace schemes, targets, and module topology."""
    workspace = args.workspace
    if not workspace:
        # Auto-detect workspace in current directory
        candidates = list(Path(".").glob("*.xcworkspace"))
        if not candidates:
            candidates = list(Path(".").glob("*.xcodeproj"))
        if not candidates:
            print("❌ No .xcworkspace or .xcodeproj found. Use --workspace.")
            sys.exit(1)
        workspace = str(candidates[0])

    print(f"## Workspace: {Path(workspace).name}\n")

    # Get scheme list via xcodebuild -list -json
    try:
        result = subprocess.run(
            ["xcodebuild", "-list", "-workspace", workspace, "-json"],
            capture_output=True,
            text=True,
            timeout=30,
        )
        if result.returncode != 0:
            # Try as xcodeproj
            result = subprocess.run(
                ["xcodebuild", "-list", "-project", workspace, "-json"],
                capture_output=True,
                text=True,
                timeout=30,
            )
    except FileNotFoundError:
        print("❌ xcodebuild not found. Ensure Xcode Command Line Tools are installed.")
        sys.exit(1)
    except subprocess.TimeoutExpired:
        print("❌ xcodebuild -list timed out after 30 seconds.")
        sys.exit(1)

    try:
        listing = json.loads(result.stdout)
    except json.JSONDecodeError:
        print("❌ Failed to parse xcodebuild -list output.")
        print(result.stderr[:500] if result.stderr else "(no stderr)")
        sys.exit(1)

    # Extract schemes and targets
    workspace_info = listing.get("workspace", listing.get("project", {}))
    schemes = workspace_info.get("schemes", [])
    targets = workspace_info.get("targets", [])

    if args.json:
        print(
            json.dumps(
                {"workspace": Path(workspace).name, "schemes": schemes, "targets": targets},
                indent=2,
            )
        )
        return

    # Markdown table output
    print("| Scheme | Type |")
    print("|--------|------|")

    for scheme in sorted(schemes):
        # Heuristic: classify scheme type
        scheme_lower = scheme.lower()
        if "test" in scheme_lower:
            stype = "test"
        elif "ui" in scheme_lower and "test" in scheme_lower:
            stype = "ui-test"
        else:
            stype = "app"
        print(f"| {scheme} | {stype} |")

    if targets:
        print(f"\n### Targets ({len(targets)})\n")
        # Group targets by type heuristic
        test_targets = [t for t in targets if "test" in t.lower()]
        app_targets = [t for t in targets if "test" not in t.lower()]

        if app_targets:
            print("**Source targets:** " + ", ".join(sorted(app_targets)[:15]))
            if len(app_targets) > 15:
                print(f"  _(+{len(app_targets) - 15} more)_")

        if test_targets:
            print("**Test targets:** " + ", ".join(sorted(test_targets)[:15]))
            if len(test_targets) > 15:
                print(f"  _(+{len(test_targets) - 15} more)_")

    print(f"\n> **{len(schemes)} schemes, {len(targets)} targets** in `{Path(workspace).name}`")


# ---------------------------------------------------------------------------
# Subcommand: compile
# ---------------------------------------------------------------------------

# Regex for Xcode compiler diagnostics:
#   /path/to/File.swift:42:5: error: some message
#   /path/to/File.swift:42:5: warning: some message
#   /path/to/File.swift:42:5: note: some message
DIAGNOSTIC_RE = re.compile(
    r"^(.+?):(\d+):(\d+):\s+(error|warning|note):\s+(.+)$"
)


@dataclass
class CompilerDiagnostic:
    """A single compiler error, warning, or note."""

    file_path: str
    line: int
    column: int
    severity: str  # error, warning, note
    message: str


def parse_compile_output(
    raw: str, source_root: Optional[str] = None
) -> List[CompilerDiagnostic]:
    """Parse xcodebuild output into structured diagnostics."""
    diagnostics: List[CompilerDiagnostic] = []
    seen: Set[str] = set()  # For deduplication

    for line in raw.splitlines():
        m = DIAGNOSTIC_RE.match(line.strip())
        if not m:
            continue

        file_path = relativize_path(m.group(1), source_root)
        line_num = int(m.group(2))
        col = int(m.group(3))
        severity = m.group(4)
        message = m.group(5).strip()

        # Deduplicate by file:line:message
        dedup_key = f"{file_path}:{line_num}:{message}"
        if dedup_key in seen:
            continue
        seen.add(dedup_key)

        diagnostics.append(
            CompilerDiagnostic(
                file_path=file_path,
                line=line_num,
                column=col,
                severity=severity,
                message=message,
            )
        )

    return diagnostics


def format_compile_markdown(
    diagnostics: List[CompilerDiagnostic],
    max_issues: int = 20,
    scheme: Optional[str] = None,
    attempt: int = 0,
) -> str:
    """Format compiler diagnostics as token-efficient Markdown."""
    errors = [d for d in diagnostics if d.severity == "error"]
    warnings = [d for d in diagnostics if d.severity == "warning"]
    notes = [d for d in diagnostics if d.severity == "note"]

    scheme_label = f" (scheme: {scheme})" if scheme else ""
    lines: List[str] = []
    lines.append(
        f"## Build Result: {len(errors)} errors, {len(warnings)} warnings{scheme_label}\n"
    )

    if not errors and not warnings:
        lines.append("✅ **Clean build** — no errors or warnings.\n")
        return "\n".join(lines)

    # Group errors by file
    if errors:
        lines.append("### Errors by File\n")
        by_file: Dict[str, List[CompilerDiagnostic]] = defaultdict(list)
        for d in errors:
            by_file[d.file_path].append(d)

        shown = 0
        for file_path, file_diags in sorted(
            by_file.items(), key=lambda x: -len(x[1])
        ):
            if shown >= max_issues:
                remaining = len(errors) - shown
                lines.append(f"\n_({remaining} more errors not shown — use `--max-issues` to increase)_\n")
                break

            lines.append(f"#### {Path(file_path).name} ({len(file_diags)} errors)")
            for d in sorted(file_diags, key=lambda x: x.line):
                lines.append(f"- **L{d.line}**: `{d.message}`")
                shown += 1
                if shown >= max_issues:
                    break
            lines.append("")

    # Top warnings (condensed)
    if warnings:
        show_warnings = min(5, len(warnings))
        lines.append(f"### Top {show_warnings} Warnings\n")
        for d in warnings[:show_warnings]:
            lines.append(f"- `{d.file_path}:{d.line}` — {d.message}")
        if len(warnings) > show_warnings:
            lines.append(f"- _({len(warnings) - show_warnings} more warnings)_")
        lines.append("")

    # Circuit breaker
    cb = format_circuit_breaker(attempt)
    if cb:
        lines.append(cb)

    return "\n".join(lines)


def format_compile_json(
    diagnostics: List[CompilerDiagnostic], attempt: int = 0
) -> str:
    """Format compiler diagnostics as JSON."""
    output = {
        "errors": len([d for d in diagnostics if d.severity == "error"]),
        "warnings": len([d for d in diagnostics if d.severity == "warning"]),
        "attempt": attempt,
        "circuit_breaker": attempt >= 3,
        "diagnostics": [
            {
                "file": d.file_path,
                "line": d.line,
                "severity": d.severity,
                "message": d.message,
            }
            for d in diagnostics
        ],
    }
    return json.dumps(output, indent=2)


def cmd_compile(args: argparse.Namespace) -> None:
    """Distill compiler errors/warnings from xcodebuild output."""
    # Read from stdin (piped) or file
    if args.input_file:
        with open(args.input_file, "r") as f:
            raw = f.read()
    else:
        if sys.stdin.isatty():
            print(
                "💡 Pipe xcodebuild output: xcodebuild build ... 2>&1 | python3 xcode-distill.py compile",
                file=sys.stderr,
            )
            sys.exit(1)
        raw = sys.stdin.read()

    diagnostics = parse_compile_output(raw, source_root=args.source_root)

    if args.json:
        print(format_compile_json(diagnostics, attempt=args.attempt))
    else:
        print(
            format_compile_markdown(
                diagnostics,
                max_issues=args.max_issues,
                scheme=args.scheme,
                attempt=args.attempt,
            )
        )


# ---------------------------------------------------------------------------
# Subcommand: test
# ---------------------------------------------------------------------------

@dataclass
class TestFailure:
    """A single test failure extracted from xcresult."""

    test_class: str
    test_method: str
    message: str
    file_path: str
    line: int
    duration: Optional[float] = None


def extract_test_failures(xcresult_path: str, source_root: Optional[str] = None) -> List[TestFailure]:
    """Extract test failures from an .xcresult bundle using xcresulttool."""
    if not Path(xcresult_path).exists():
        print(f"❌ xcresult bundle not found: {xcresult_path}", file=sys.stderr)
        sys.exit(1)

    # Use xcrun xcresulttool to extract JSON
    try:
        result = subprocess.run(
            [
                "xcrun", "xcresulttool", "get",
                "--format", "json",
                "--path", xcresult_path,
            ],
            capture_output=True,
            text=True,
            timeout=60,
        )
    except FileNotFoundError:
        print("❌ xcrun xcresulttool not found. Ensure Xcode is installed.", file=sys.stderr)
        sys.exit(1)
    except subprocess.TimeoutExpired:
        print("❌ xcresulttool timed out after 60 seconds.", file=sys.stderr)
        sys.exit(1)

    if result.returncode != 0:
        print(f"❌ xcresulttool failed: {result.stderr[:300]}", file=sys.stderr)
        sys.exit(1)

    try:
        data = json.loads(result.stdout)
    except json.JSONDecodeError:
        print("❌ Failed to parse xcresulttool JSON output.", file=sys.stderr)
        sys.exit(1)

    failures: List[TestFailure] = []
    _walk_test_results(data, failures, source_root)
    return failures


def _walk_test_results(
    node: dict,
    failures: List[TestFailure],
    source_root: Optional[str],
    path: str = "",
) -> None:
    """Recursively walk xcresult JSON to find test failures."""
    # Handle both the new and legacy xcresult formats
    node_type = node.get("_type", {}).get("_name", "")

    # Look for action test summaries
    if node_type == "ActionTestMetadata" or node_type == "ActionTestSummary":
        status = node.get("testStatus", {}).get("_value", "")
        if status == "Failure":
            name = node.get("name", {}).get("_value", "")
            identifier = node.get("identifier", {}).get("_value", "")

            # Parse class.method from identifier
            parts = identifier.rsplit("/", 1)
            test_class = parts[0] if len(parts) > 1 else ""
            test_method = parts[-1] if parts else name

            # Extract failure message from summaries
            message = ""
            file_path = ""
            line = 0

            failure_summaries = node.get("failureSummaries", {}).get("_values", [])
            if failure_summaries:
                first = failure_summaries[0]
                message = first.get("message", {}).get("_value", "")
                loc = first.get("documentLocationInCreatingWorkspace", {})
                url = loc.get("url", {}).get("_value", "")
                if url:
                    # Parse file:///path/to/file#CharacterRangeLen=...
                    file_path = url.split("#")[0].replace("file://", "")
                    file_path = relativize_path(file_path, source_root)
                    # Extract line from URL fragment if present
                    fragment = url.split("#")[-1] if "#" in url else ""
                    line_match = re.search(r"StartingLineNumber=(\d+)", fragment)
                    if line_match:
                        line = int(line_match.group(1))

            duration_val = node.get("duration", {}).get("_value", None)
            duration = float(duration_val) if duration_val else None

            failures.append(
                TestFailure(
                    test_class=test_class,
                    test_method=test_method,
                    message=message[:200],  # Cap message length
                    file_path=file_path,
                    line=line,
                    duration=duration,
                )
            )

    # Recurse into child nodes
    for key, value in node.items():
        if isinstance(value, dict):
            _walk_test_results(value, failures, source_root, f"{path}/{key}")
        elif isinstance(value, list):
            for item in value:
                if isinstance(item, dict):
                    _walk_test_results(item, failures, source_root, f"{path}/{key}")
        # Handle xcresult's _values arrays
        if isinstance(value, dict) and "_values" in value:
            for item in value["_values"]:
                if isinstance(item, dict):
                    _walk_test_results(item, failures, source_root, f"{path}/{key}")


def format_test_markdown(
    failures: List[TestFailure],
    max_issues: int = 20,
    attempt: int = 0,
) -> str:
    """Format test failures as token-efficient Markdown."""
    lines: List[str] = []

    if not failures:
        lines.append("## Test Result: ✅ All tests passed\n")
        return "\n".join(lines)

    lines.append(f"## Test Result: {len(failures)} failures\n")

    # Group by test class
    by_class: Dict[str, List[TestFailure]] = defaultdict(list)
    for f in failures:
        by_class[f.test_class or "(unknown)"].append(f)

    shown = 0
    for test_class, class_failures in sorted(
        by_class.items(), key=lambda x: -len(x[1])
    ):
        if shown >= max_issues:
            remaining = len(failures) - shown
            lines.append(f"\n_({remaining} more failures not shown)_\n")
            break

        lines.append(f"### {test_class} ({len(class_failures)} failures)\n")
        for f in class_failures:
            loc = f""
            if f.file_path:
                loc = f" — `{f.file_path}:{f.line}`"
            duration = f" ({f.duration:.1f}s)" if f.duration else ""
            lines.append(f"- **{f.test_method}**{duration}{loc}")
            if f.message:
                # Truncate and clean the message
                msg = f.message.replace("\n", " ").strip()
                lines.append(f"  > {msg}")
            shown += 1
            if shown >= max_issues:
                break
        lines.append("")

    # Circuit breaker
    cb = format_circuit_breaker(attempt)
    if cb:
        lines.append(cb)

    return "\n".join(lines)


def format_test_json(failures: List[TestFailure], attempt: int = 0) -> str:
    """Format test failures as JSON."""
    output = {
        "total_failures": len(failures),
        "attempt": attempt,
        "circuit_breaker": attempt >= 3,
        "failures": [
            {
                "class": f.test_class,
                "method": f.test_method,
                "message": f.message,
                "file": f.file_path,
                "line": f.line,
            }
            for f in failures
        ],
    }
    return json.dumps(output, indent=2)


def cmd_test(args: argparse.Namespace) -> None:
    """Extract test failures from .xcresult bundle."""
    failures = extract_test_failures(args.path, source_root=args.source_root)

    if args.json:
        print(format_test_json(failures, attempt=args.attempt))
    else:
        print(format_test_markdown(failures, max_issues=args.max_issues, attempt=args.attempt))


# ---------------------------------------------------------------------------
# Subcommand: tsan
# ---------------------------------------------------------------------------

def cmd_tsan(args: argparse.Namespace) -> None:
    """Run/parse TSan output — delegates to tsan-sanitizer.py's parser."""
    # Import from sibling script
    script_dir = Path(__file__).parent
    tsan_script = script_dir / "tsan-sanitizer.py"

    if not tsan_script.exists():
        print(f"❌ tsan-sanitizer.py not found at {tsan_script}", file=sys.stderr)
        sys.exit(1)

    # Build the tsan-sanitizer.py command with forwarded args
    cmd = [sys.executable, str(tsan_script)]

    if args.raw_log:
        cmd.extend(["--raw-log", args.raw_log])
    elif args.scheme:
        cmd.extend(["--scheme", args.scheme])
        if args.device:
            cmd.extend(["--device", args.device])
        if args.workspace:
            cmd.extend(["--workspace", args.workspace])
        if args.target:
            cmd.extend(["--target", args.target])
        if args.test_class:
            cmd.extend(["--test-class", args.test_class])
        if args.test_plan:
            cmd.extend(["--test-plan", args.test_plan])
    else:
        print("❌ tsan requires --scheme or --raw-log", file=sys.stderr)
        sys.exit(1)

    if args.json:
        cmd.append("--json")
    if args.max_issues:
        cmd.extend(["--limit", str(args.max_issues)])

    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=1800)
        output = result.stdout
        if result.stderr:
            output += result.stderr

        # Post-process: prune system frames from TSan output
        pruned_lines = []
        has_timeout = False
        for line in output.splitlines():
            if line.strip().startswith("→") or line.strip().startswith("#"):
                if is_system_frame(line):
                    continue
            # Detect test timeouts (hung continuation / deadlock)
            if "exceeded time limit" in line.lower() or "test timed out" in line.lower():
                has_timeout = True
            pruned_lines.append(line)

        print("\n".join(pruned_lines))

        # Emit timeout diagnostic if detected
        if has_timeout:
            print("\n## ⚠️ TEST TIMEOUT DETECTED\n")
            print(
                "One or more tests exceeded the 30-second time limit. "
                "This typically indicates:\n"
                "- A `withCheckedContinuation` with a missing `.resume()` on some branch\n"
                "- A `DispatchSemaphore` / `DispatchGroup.wait()` deadlocking the cooperative thread pool\n"
                "- An actor method waiting on itself (reentrancy deadlock)\n\n"
                "**Action:** Audit suspension points and sync-blocking patterns in the affected test's code path.\n"
            )

        # Append circuit breaker if needed
        cb = format_circuit_breaker(args.attempt)
        if cb:
            print(cb)

    except subprocess.TimeoutExpired:
        print("❌ TSan run timed out.", file=sys.stderr)
        sys.exit(1)


# ---------------------------------------------------------------------------
# Subcommand: lint-diff
# ---------------------------------------------------------------------------

# Forbidden patterns — hard reject
FORBIDDEN_PATTERNS: List[Tuple[re.Pattern, str, str]] = [
    (
        re.compile(r"@unchecked\s+Sendable"),
        "@unchecked Sendable",
        "Unsafe concurrency bypass. Use `actor`, `Sendable` value types, or `nonisolated(unsafe)` with justification.",
    ),
    (
        re.compile(r"\.assumeIsolated"),
        ".assumeIsolated",
        "Bypasses compiler isolation checks. Crashes at runtime if assumption is wrong.",
    ),
    (
        re.compile(r"DispatchSemaphore\s*\("),
        "DispatchSemaphore",
        "Blocks the cooperative thread pool, causing deadlock. Propagate `async` up the call stack instead.",
    ),
    (
        re.compile(r"DispatchGroup\(\)\.wait\(\)|dispatchGroup\.wait\(\)", re.IGNORECASE),
        "DispatchGroup.wait()",
        "Blocks the cooperative thread pool, causing deadlock. Use `async let` or `TaskGroup` instead.",
    ),
    (
        re.compile(r"Task\.detached"),
        "Task.detached",
        "Breaks structured concurrency. Use `Task {}`, `async let`, or `TaskGroup`. "
        "Task.detached is only permitted for root-level background processes with explicit justification.",
    ),
]

# Conditional patterns — reject without justification
CONDITIONAL_PATTERNS: List[Tuple[re.Pattern, str, str]] = [
    (
        re.compile(r"nonisolated\s*\(\s*unsafe\s*\)"),
        "nonisolated(unsafe)",
        "Requires a justification comment on the preceding line. "
        "Allowed for `static let` singletons with thread-safe initialization.",
    ),
]

# Warning patterns — warn only
WARN_PATTERNS: List[Tuple[re.Pattern, str, str]] = [
    (
        re.compile(r"@preconcurrency\s+import"),
        "@preconcurrency import",
        "Verify this is a 3rd-party/system framework. "
        "@preconcurrency is strictly forbidden on 1st-party internal modules.",
    ),
]


@dataclass
class LintViolation:
    """A concurrency lint violation found in a diff."""

    file_path: str
    line_num: int  # Line number in the diff hunk (approximate)
    pattern_name: str
    severity: str  # "error", "warning"
    message: str
    diff_line: str


def parse_diff_for_violations(
    diff_text: str, max_files: int = 15
) -> Tuple[List[LintViolation], Optional[str]]:
    """Parse unified diff text for concurrency violations.

    Returns:
        Tuple of (violations list, blast_radius_message or None)
    """
    violations: List[LintViolation] = []
    current_file = ""
    current_line = 0
    changed_files: Set[str] = set()

    # Track files touched in the diff
    file_header_re = re.compile(r"^\+\+\+\s+b/(.+)$")
    hunk_header_re = re.compile(r"^@@\s+-\d+(?:,\d+)?\s+\+(\d+)(?:,\d+)?\s+@@")

    lines = diff_text.splitlines()
    prev_line = ""

    for line in lines:
        # Track current file
        file_match = file_header_re.match(line)
        if file_match:
            current_file = file_match.group(1)
            changed_files.add(current_file)
            current_line = 0
            prev_line = ""
            continue

        # Track current line number
        hunk_match = hunk_header_re.match(line)
        if hunk_match:
            current_line = int(hunk_match.group(1))
            prev_line = ""
            continue

        # Only check added lines (lines starting with +)
        if not line.startswith("+") or line.startswith("+++"):
            if not line.startswith("-"):
                current_line += 1
            prev_line = line
            continue

        added_content = line[1:]  # Strip leading +
        current_line += 1

        # Skip comment-only lines (they're justification comments, not code)
        stripped_content = added_content.strip()
        if stripped_content.startswith("//") or stripped_content.startswith("/*") or stripped_content.startswith("*"):
            prev_line = line
            continue

        # Check forbidden patterns
        for pattern, name, message in FORBIDDEN_PATTERNS:
            if pattern.search(added_content):
                violations.append(
                    LintViolation(
                        file_path=current_file,
                        line_num=current_line,
                        pattern_name=name,
                        severity="error",
                        message=message,
                        diff_line=added_content.strip(),
                    )
                )

        # Check conditional patterns (need justification comment on preceding line)
        for pattern, name, message in CONDITIONAL_PATTERNS:
            if pattern.search(added_content):
                # Check if preceding line in the diff is a justification comment
                has_justification = False
                prev_stripped = prev_line.lstrip("+").strip()
                if prev_stripped.startswith("//") and any(
                    kw in prev_stripped.lower()
                    for kw in ["justification", "safety", "thread-safe", "rationale"]
                ):
                    has_justification = True

                if not has_justification:
                    violations.append(
                        LintViolation(
                            file_path=current_file,
                            line_num=current_line,
                            pattern_name=name,
                            severity="error",
                            message=f"Missing justification comment. {message}",
                            diff_line=added_content.strip(),
                        )
                    )

        # Check warning patterns
        for pattern, name, message in WARN_PATTERNS:
            if pattern.search(added_content):
                violations.append(
                    LintViolation(
                        file_path=current_file,
                        line_num=current_line,
                        pattern_name=name,
                        severity="warning",
                        message=message,
                        diff_line=added_content.strip(),
                    )
                )

        prev_line = line

    # Blast radius check
    blast_msg = None
    if len(changed_files) > max_files:
        blast_msg = (
            f"Scope Violation: Your concurrency changes modified {len(changed_files)} files "
            f"(max: {max_files}). This suggests a viral cascade from a protocol or global actor change. "
            f"Revert and handle isolation at the local conformance site to contain the blast radius."
        )

    return violations, blast_msg


def format_lint_markdown(
    violations: List[LintViolation], blast_msg: Optional[str] = None
) -> str:
    """Format lint violations as Markdown."""
    lines: List[str] = []

    errors = [v for v in violations if v.severity == "error"]
    warnings = [v for v in violations if v.severity == "warning"]

    if not violations and not blast_msg:
        lines.append("## Diff Lint: ✅ No concurrency violations\n")
        return "\n".join(lines)

    lines.append(f"## Diff Lint: {len(errors)} errors, {len(warnings)} warnings\n")

    if blast_msg:
        lines.append(f"> [!CAUTION]")
        lines.append(f"> {blast_msg}\n")

    if errors:
        lines.append("### ❌ Forbidden Patterns\n")
        by_file: Dict[str, List[LintViolation]] = defaultdict(list)
        for v in errors:
            by_file[v.file_path].append(v)

        for file_path, file_violations in sorted(by_file.items()):
            lines.append(f"#### {Path(file_path).name}")
            for v in file_violations:
                lines.append(f"- **L{v.line_num}** `{v.pattern_name}`: {v.message}")
                lines.append(f"  ```\n  {v.diff_line}\n  ```")
            lines.append("")

    if warnings:
        lines.append("### ⚠️ Warnings\n")
        for v in warnings:
            lines.append(
                f"- `{Path(v.file_path).name}:{v.line_num}` `{v.pattern_name}`: {v.message}"
            )
        lines.append("")

    return "\n".join(lines)


def format_lint_json(
    violations: List[LintViolation], blast_msg: Optional[str] = None
) -> str:
    """Format lint violations as JSON."""
    output = {
        "errors": len([v for v in violations if v.severity == "error"]),
        "warnings": len([v for v in violations if v.severity == "warning"]),
        "blast_radius_violation": blast_msg,
        "violations": [
            {
                "file": v.file_path,
                "line": v.line_num,
                "pattern": v.pattern_name,
                "severity": v.severity,
                "message": v.message,
            }
            for v in violations
        ],
    }
    return json.dumps(output, indent=2)


def cmd_lint_diff(args: argparse.Namespace) -> None:
    """Lint a git diff for forbidden concurrency patterns."""
    if args.diff_file:
        with open(args.diff_file, "r") as f:
            diff_text = f.read()
    else:
        # Read diff from stdin or run git diff
        if sys.stdin.isatty():
            # Auto-run git diff for staged changes
            try:
                result = subprocess.run(
                    ["git", "diff", "--cached", "--unified=3"],
                    capture_output=True,
                    text=True,
                    timeout=30,
                )
                diff_text = result.stdout
                if not diff_text:
                    # Fall back to unstaged diff
                    result = subprocess.run(
                        ["git", "diff", "--unified=3"],
                        capture_output=True,
                        text=True,
                        timeout=30,
                    )
                    diff_text = result.stdout
            except (FileNotFoundError, subprocess.TimeoutExpired):
                print("❌ git not found or timed out. Use --diff to provide a diff file.", file=sys.stderr)
                sys.exit(1)
        else:
            diff_text = sys.stdin.read()

    if not diff_text.strip():
        print("## Diff Lint: ✅ No changes to lint\n")
        return

    violations, blast_msg = parse_diff_for_violations(
        diff_text, max_files=args.max_files
    )

    if args.json:
        print(format_lint_json(violations, blast_msg))
    else:
        print(format_lint_markdown(violations, blast_msg))

    # Exit with non-zero if errors found
    errors = [v for v in violations if v.severity == "error"]
    if errors or blast_msg:
        sys.exit(1)


# ---------------------------------------------------------------------------
# Main CLI
# ---------------------------------------------------------------------------


def main() -> None:
    parser = argparse.ArgumentParser(
        prog="xcode-distill",
        description="Xcodebuild Output Distillation Pipeline — transforms raw Xcode output into token-efficient agent payloads",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""\
Examples:
  # Step 1: Discover workspace structure
  python3 xcode-distill.py discover --workspace MyApp.xcworkspace

  # Step 2: Distill compilation errors
  xcodebuild build -scheme MyApp 2>&1 | python3 xcode-distill.py compile

  # Step 3: Extract test failures
  python3 xcode-distill.py test --path ./Build/Results.xcresult

  # Step 4: Run TSan with distilled output
  python3 xcode-distill.py tsan --scheme MyApp --target MyTests

  # With circuit breaker (attempt tracking)
  xcodebuild build 2>&1 | python3 xcode-distill.py compile --attempt 2
""",
    )

    subparsers = parser.add_subparsers(dest="command", help="Available subcommands")

    # --- discover ---
    p_discover = subparsers.add_parser(
        "discover",
        help="List workspace schemes, targets, and module topology",
    )
    p_discover.add_argument("--workspace", help="Path to .xcworkspace or .xcodeproj")
    p_discover.add_argument("--json", action="store_true", help="Output JSON format")

    # --- compile ---
    p_compile = subparsers.add_parser(
        "compile",
        help="Distill compiler errors/warnings from piped xcodebuild output",
    )
    p_compile.add_argument(
        "--input-file", "-i", help="Read from file instead of stdin"
    )
    p_compile.add_argument("--scheme", help="Scheme name (for report header)")
    p_compile.add_argument(
        "--source-root", help="Project root for relativizing paths"
    )
    p_compile.add_argument(
        "--max-issues",
        type=int,
        default=20,
        help="Max issues to display (default: 20)",
    )
    p_compile.add_argument(
        "--attempt",
        type=int,
        default=0,
        help="Remediation attempt number (circuit breaker at 3)",
    )
    p_compile.add_argument("--json", action="store_true", help="Output JSON format")

    # --- test ---
    p_test = subparsers.add_parser(
        "test",
        help="Extract test failures from .xcresult bundles",
    )
    p_test.add_argument(
        "--path", required=True, help="Path to .xcresult bundle"
    )
    p_test.add_argument(
        "--source-root", help="Project root for relativizing paths"
    )
    p_test.add_argument(
        "--max-issues",
        type=int,
        default=20,
        help="Max failures to display (default: 20)",
    )
    p_test.add_argument(
        "--attempt",
        type=int,
        default=0,
        help="Remediation attempt number (circuit breaker at 3)",
    )
    p_test.add_argument("--json", action="store_true", help="Output JSON format")

    # --- tsan ---
    p_tsan = subparsers.add_parser(
        "tsan",
        help="Run/parse TSan output (delegates to tsan-sanitizer.py)",
    )
    p_tsan.add_argument("--scheme", help="Xcode scheme to test")
    p_tsan.add_argument(
        "--device", default="generic", help="Simulator device (default: generic)"
    )
    p_tsan.add_argument("--workspace", help="Xcode workspace path")
    p_tsan.add_argument("--raw-log", help="Parse existing TSan log file")
    p_tsan.add_argument("--target", help="Test target to scope TSan")
    p_tsan.add_argument("--test-class", help="Test class to scope TSan")
    p_tsan.add_argument("--test-plan", help="Test plan to use")
    p_tsan.add_argument(
        "--max-issues",
        type=int,
        default=10,
        help="Max unique issues to display (default: 10)",
    )
    p_tsan.add_argument(
        "--attempt",
        type=int,
        default=0,
        help="Remediation attempt number (circuit breaker at 3)",
    )
    p_tsan.add_argument("--json", action="store_true", help="Output JSON format")

    # --- lint-diff ---
    p_lint = subparsers.add_parser(
        "lint-diff",
        help="Lint git diff for forbidden concurrency patterns",
    )
    p_lint.add_argument(
        "--diff", dest="diff_file", help="Path to a unified diff file (default: auto-run git diff)"
    )
    p_lint.add_argument(
        "--max-files",
        type=int,
        default=15,
        help="Max files allowed in diff before blast radius rejection (default: 15)",
    )
    p_lint.add_argument("--json", action="store_true", help="Output JSON format")

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        sys.exit(1)

    if args.command == "discover":
        cmd_discover(args)
    elif args.command == "compile":
        cmd_compile(args)
    elif args.command == "test":
        cmd_test(args)
    elif args.command == "tsan":
        cmd_tsan(args)
    elif args.command == "lint-diff":
        cmd_lint_diff(args)


if __name__ == "__main__":
    main()
