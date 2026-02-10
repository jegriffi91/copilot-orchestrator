#!/usr/bin/env python3
"""
TSan Output Sanitizer

Purpose: Run Thread Sanitizer (TSan) and produce concise, actionable output
         instead of verbose multi-page dumps that pollute context windows.

Usage:
    python3 tsan-sanitizer.py --scheme MyScheme --device "iPhone 16"
    python3 tsan-sanitizer.py --scheme MyScheme --physical-device
    python3 tsan-sanitizer.py --raw-log path/to/tsan.log  # Parse existing log

Output:
    - Summary: Total issues, unique patterns, severity breakdown
    - Grouped Issues: Deduplicated by stack trace signature
    - Top Offenders: Files/functions with most violations
    - Actionable Fixes: Line numbers and suggested remediation
"""

import argparse
import json
import re
import subprocess
import sys
from collections import defaultdict
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional, Set


@dataclass
class TSanIssue:
    """Represents a single TSan data race detection."""
    
    issue_type: str  # e.g., "data race", "lock-order-inversion"
    location: str  # File:Line
    function: str
    thread_id: str
    stack_trace: List[str] = field(default_factory=list)
    conflicting_access: Optional[str] = None  # For data races
    
    def signature(self) -> str:
        """Generate unique signature for deduplication."""
        # Use top 3 stack frames + function name
        frames = "->".join(self.stack_trace[:3])
        return f"{self.issue_type}:{self.function}:{frames}"
    
    def short_description(self) -> str:
        """One-line summary of the issue."""
        return f"{self.issue_type.upper()} in {self.function} at {self.location}"


class TSanParser:
    """Parse TSan output into structured issues."""
    
    # Regex patterns for TSan output
    ISSUE_START = re.compile(r"WARNING: ThreadSanitizer: (.*?) \(")
    LOCATION = re.compile(r"^\s*#\d+\s+(.+?)\s+(.+?):(\d+)")
    THREAD_ID = re.compile(r"Thread T(\d+)")
    
    def __init__(self, raw_output: str):
        self.raw_output = raw_output
        self.issues: List[TSanIssue] = []
    
    def parse(self) -> List[TSanIssue]:
        """Parse raw TSan output into structured issues."""
        lines = self.raw_output.split("\n")
        current_issue = None
        in_stack_trace = False
        
        for line in lines:
            # Detect issue start
            issue_match = self.ISSUE_START.search(line)
            if issue_match:
                if current_issue:
                    self.issues.append(current_issue)
                current_issue = TSanIssue(
                    issue_type=issue_match.group(1),
                    location="",
                    function="",
                    thread_id=""
                )
                in_stack_trace = False
                continue
            
            if not current_issue:
                continue
            
            # Extract thread ID
            thread_match = self.THREAD_ID.search(line)
            if thread_match:
                current_issue.thread_id = thread_match.group(1)
            
            # Extract stack trace
            loc_match = self.LOCATION.search(line)
            if loc_match:
                function = loc_match.group(1).strip()
                file_path = loc_match.group(2)
                line_num = loc_match.group(3)
                
                # Set primary location (first frame)
                if not current_issue.location:
                    current_issue.location = f"{file_path}:{line_num}"
                    current_issue.function = function
                
                # Add to stack trace
                current_issue.stack_trace.append(f"{function} ({file_path}:{line_num})")
                in_stack_trace = True
        
        # Add last issue
        if current_issue:
            self.issues.append(current_issue)
        
        return self.issues


class TSanSanitizer:
    """Sanitize TSan output into actionable summary."""
    
    def __init__(self, issues: List[TSanIssue]):
        self.issues = issues
        self.grouped: Dict[str, List[TSanIssue]] = defaultdict(list)
        self.file_counts: Dict[str, int] = defaultdict(int)
        self.function_counts: Dict[str, int] = defaultdict(int)
    
    def analyze(self):
        """Group and analyze issues."""
        for issue in self.issues:
            # Group by signature
            sig = issue.signature()
            self.grouped[sig].append(issue)
            
            # Count by file
            file_name = issue.location.split(":")[0] if ":" in issue.location else "unknown"
            self.file_counts[file_name] += 1
            
            # Count by function
            self.function_counts[issue.function] += 1
    
    def print_summary(self):
        """Print concise summary."""
        print("\n" + "=" * 80)
        print("TSAN SUMMARY")
        print("=" * 80)
        print(f"Total Issues: {len(self.issues)}")
        print(f"Unique Patterns: {len(self.grouped)}")
        
        # Issue type breakdown
        issue_types = defaultdict(int)
        for issue in self.issues:
            issue_types[issue.issue_type] += 1
        
        print("\nIssue Types:")
        for issue_type, count in sorted(issue_types.items(), key=lambda x: -x[1]):
            print(f"  - {issue_type}: {count}")
        
        print("\nTop 5 Files:")
        for file_name, count in sorted(self.file_counts.items(), key=lambda x: -x[1])[:5]:
            short_name = Path(file_name).name
            print(f"  - {short_name}: {count} issues")
        
        print("\nTop 5 Functions:")
        for func, count in sorted(self.function_counts.items(), key=lambda x: -x[1])[:5]:
            print(f"  - {func}(): {count} issues")
    
    def print_grouped_issues(self, limit: int = 10):
        """Print deduplicated issues with occurrence counts."""
        print("\n" + "=" * 80)
        print(f"UNIQUE ISSUES (Top {limit})")
        print("=" * 80)
        
        sorted_groups = sorted(
            self.grouped.items(),
            key=lambda x: len(x[1]),
            reverse=True
        )[:limit]
        
        for idx, (sig, group) in enumerate(sorted_groups, 1):
            representative = group[0]
            print(f"\n{idx}. {representative.short_description()}")
            print(f"   Occurrences: {len(group)}")
            print(f"   Thread: T{representative.thread_id}")
            
            # Print condensed stack trace (top 3 frames)
            if representative.stack_trace:
                print("   Stack:")
                for frame in representative.stack_trace[:3]:
                    print(f"     → {frame}")
            
            # Suggested fix
            print(f"   Fix: Review {representative.location}")
    
    def print_actionable_fixes(self):
        """Print actionable fix suggestions."""
        print("\n" + "=" * 80)
        print("ACTIONABLE FIXES")
        print("=" * 80)
        
        # Group by file for easier batch fixing
        file_issues: Dict[str, List[TSanIssue]] = defaultdict(list)
        for issue in self.issues:
            file_name = issue.location.split(":")[0] if ":" in issue.location else "unknown"
            file_issues[file_name].append(issue)
        
        for file_name, issues in sorted(file_issues.items(), key=lambda x: -len(x[1]))[:5]:
            short_name = Path(file_name).name
            print(f"\n📄 {short_name} ({len(issues)} issues)")
            
            # Get unique line numbers
            lines: Set[str] = set()
            for issue in issues:
                if ":" in issue.location:
                    lines.add(issue.location.split(":")[1])
            
            print(f"   Lines: {', '.join(sorted(lines, key=int)[:10])}")
            
            # Common fix patterns
            issue_types = set(issue.issue_type for issue in issues)
            if "data race" in issue_types:
                print("   → Wrap shared mutable state in `actor`")
                print("   → Mark UI properties `@MainActor`")
            if "lock-order-inversion" in issue_types:
                print("   → Avoid nested locks; use single actor")


def run_tsan(
    scheme: str, 
    device: str, 
    workspace: str = "CreditWorks.xcworkspace",
    target: Optional[str] = None,
    test_class: Optional[str] = None,
    test_plan: Optional[str] = None
) -> str:
    """Run xcodebuild with TSan enabled.
    
    Args:
        scheme: Xcode scheme to test
        device: Simulator device name (use 'generic' for generic/platform=iOS Simulator)
        workspace: Xcode workspace path
        target: Specific test target (e.g., CMSCoreUnitTests) - Tier 3
        test_class: Specific test class (e.g., SDUISheetContainerViewModelTests) - Tier 2
        test_plan: Test plan to use (e.g., sdui)
    
    Tiers:
        - No target/test_class: Full scheme (CI only) - 10-30 min
        - target only: Module TSan - 5-10 min
        - target + test_class: Scoped TSan - 1-2 min
    """
    scope_desc = "full scheme"
    if test_class and target:
        scope_desc = f"test class: {test_class}"
    elif target:
        scope_desc = f"test target: {target}"
    
    print(f"Running TSan on scheme: {scheme} ({scope_desc})...")
    if test_class:
        print("⚡ Scoped TSan (Tier 2) - ~2 minutes")
    elif target:
        print("📦 Module TSan (Tier 3) - ~5-10 minutes")
    else:
        print("🌐 Full TSan (CI only) - ~10-30 minutes")
    print()
    
    # Build destination
    if device == "generic":
        destination = "generic/platform=iOS Simulator"
    else:
        destination = f"platform=iOS Simulator,name={device}"
    
    cmd = [
        "xcodebuild", "test",
        "-workspace", workspace,
        "-scheme", scheme,
        "-destination", destination,
        "-enableThreadSanitizer", "YES",
        "-quiet"
    ]
    
    # Add test plan if specified
    if test_plan:
        cmd.extend(["-testPlan", test_plan])
    
    # Add scoping if specified
    if test_class and target:
        cmd.extend(["-only-testing", f"{target}/{test_class}"])
    elif target:
        cmd.extend(["-only-testing", target])
    
    # Adjust timeout based on scope
    if test_class:
        timeout = 180  # 3 minutes for scoped
    elif target:
        timeout = 600  # 10 minutes for module
    else:
        timeout = 1800  # 30 minutes for full scheme
    
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=timeout
        )
        return result.stdout + result.stderr
    except subprocess.TimeoutExpired:
        print(f"⚠️ TSan timed out after {timeout // 60} minutes")
        return ""
    except FileNotFoundError:
        print("❌ xcodebuild not found. Ensure Xcode Command Line Tools are installed.")
        sys.exit(1)


def main():
    parser = argparse.ArgumentParser(
        description="TSan Output Sanitizer - Tiered Verification for Swift 6 Migration",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Verification Tiers:
  Tier 1 (Compile)  - Static analysis only, no TSan needed
  Tier 2 (Scoped)   - Use --target + --test-class for single test class (~2 min)
  Tier 3 (Module)   - Use --target for entire test module (~5-10 min)
  Tier 4 (Full)     - Use --scheme only for CI/CD (~10-30 min)

Examples:
  # Tier 2: Scoped TSan on single test class (RECOMMENDED for incremental)
  python3 tsan-sanitizer.py --scheme ECW --target CMSCoreUnitTests --test-class SDUISheetContainerViewModelTests --test-plan sdui

  # Tier 3: Module TSan
  python3 tsan-sanitizer.py --scheme ECW --target CMSCoreUnitTests --test-plan sdui

  # Tier 4: Full scheme (CI only)
  python3 tsan-sanitizer.py --scheme ECW

  # Parse existing log
  python3 tsan-sanitizer.py --raw-log tsan.log
        """
    )
    parser.add_argument("--scheme", help="Xcode scheme to test")
    parser.add_argument("--device", default="generic", help="Simulator device name (default: generic)")
    parser.add_argument("--physical-device", action="store_true", help="Run on physical device")
    parser.add_argument("--raw-log", help="Parse existing TSan log file")
    parser.add_argument("--workspace", default="CreditWorks.xcworkspace", help="Xcode workspace")
    parser.add_argument("--json", action="store_true", help="Output JSON format")
    parser.add_argument("--limit", type=int, default=10, help="Max unique issues to display")
    
    # New scoping arguments for tiered verification
    parser.add_argument("--target", help="Test target to scope TSan (e.g., CMSCoreUnitTests) - Tier 3")
    parser.add_argument("--test-class", help="Test class to scope TSan (e.g., MyViewModelTests) - Tier 2")
    parser.add_argument("--test-plan", help="Test plan to use (e.g., sdui)")
    
    args = parser.parse_args()
    
    # Get raw TSan output
    if args.raw_log:
        with open(args.raw_log, "r") as f:
            raw_output = f.read()
    elif args.scheme:
        if args.physical_device:
            print("⚠️ Physical device testing requires manual setup. Use --raw-log to parse results.")
            sys.exit(1)
        
        # Validate scoping args
        if args.test_class and not args.target:
            print("❌ --test-class requires --target to be specified")
            sys.exit(1)
        
        raw_output = run_tsan(
            args.scheme, 
            args.device, 
            args.workspace,
            target=args.target,
            test_class=args.test_class,
            test_plan=args.test_plan
        )
    else:
        parser.print_help()
        sys.exit(1)
    
    # Parse issues
    tsan_parser = TSanParser(raw_output)
    issues = tsan_parser.parse()
    
    if not issues:
        print("✅ No TSan issues detected!")
        return
    
    # Sanitize and display
    sanitizer = TSanSanitizer(issues)
    sanitizer.analyze()
    
    if args.json:
        # JSON output for CI/CD
        output = {
            "total_issues": len(issues),
            "unique_patterns": len(sanitizer.grouped),
            "scope": {
                "target": args.target,
                "test_class": args.test_class,
                "tier": "2-scoped" if args.test_class else ("3-module" if args.target else "4-full")
            },
            "issues": [
                {
                    "type": issue.issue_type,
                    "location": issue.location,
                    "function": issue.function,
                    "thread": issue.thread_id
                }
                for issue in issues
            ]
        }
        print(json.dumps(output, indent=2))
    else:
        # Human-readable output
        sanitizer.print_summary()
        sanitizer.print_grouped_issues(limit=args.limit)
        sanitizer.print_actionable_fixes()
        print("\n" + "=" * 80)
        print(f"📊 Found {len(issues)} total issues ({len(sanitizer.grouped)} unique patterns)")
        print("=" * 80)


if __name__ == "__main__":
    main()
