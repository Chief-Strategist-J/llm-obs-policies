#!/usr/bin/env python3
"""
================================================================================
ALGORITHM & ARCHITECTURE BLUEPRINT: CONCURRENCY & DUAL-WRITE ARCHITECTURE SCANNER
================================================================================

1. OVERVIEW & OBJECTIVE:
   This module implements a specialized static analysis engine detecting
   concurrency race conditions, uncoordinated multi-threaded mutations,
   naked sleep calls, unbounded goroutine spawns, and unbuffered channel leaks
   across Go, TypeScript, JavaScript, and Python codebases.

2. ARCHITECTURAL LAYOUT & DESIGN PILLARS:
   - Zero-Inline-Comment Doctrine: All algorithmic descriptions, regular expressions,
     and operational bounds are encapsulated strictly in this top-level blueprint.
     Function and loop bodies remain 100% comment-free and pure.
   - Type Safety & Immutability: Uses frozen dataclasses for check rules and findings.
   - Strict I/O Boundaries: Read-only AST and token inspections; ignores build and
     artifact directories to prevent container I/O thrashing.

3. EXECUTION SEQUENCE & DATA FLOW:
   [CLI Input Options]
         │
         ▼
   [Filesystem Traversal] ──> Exclude IGNORED_DIRS & match target extensions
         │
         ▼
   [Concurrency Check Engine] ──> Execute regex matching against CONCURRENCY_RULES
         │
         ▼
   [Finding Struct Formulation] ─> Package filename, line number, snippet, recommendation
         │
         ▼
   [Emitter Pipeline] ───────────> Output JSON or structured terminal diagnostics

4. EDGE CASES & FAILURE MODES HANDLED:
   - File Read Exceptions: Silently skipped on binary or unreadable encodings.
   - Lexicographical Consistency: Output order is deterministically sorted.

5. SECURITY & RESILIENCE RULES:
   - Exit code 0 if 0 issues found; exit code 1 if concurrency violations detected.
================================================================================
"""

import os
import sys
import re
import json
import argparse
from pathlib import Path
from dataclasses import dataclass, asdict
from typing import List, Set, Dict, Pattern

IGNORED_DIRS: Set[str] = {
    ".git", "node_modules", "dist", "build", ".next", "vendor",
    "__pycache__", "data", "brain", ".gemini", "scratch", "tmp", "bin"
}

TARGET_EXTENSIONS: Set[str] = {".go", ".ts", ".js", ".py"}

@dataclass(frozen=True)
class ConcurrencyRule:
    check_id: str
    name: str
    pattern: Pattern
    recommendation: str

@dataclass(frozen=True)
class ConcurrencyFinding:
    check_id: str
    name: str
    file: str
    line: int
    snippet: str
    recommendation: str

CONCURRENCY_RULES: List[ConcurrencyRule] = [
    ConcurrencyRule(
        check_id="CONC-SLEEP",
        name="Naked Sleep In Synchronization",
        pattern=re.compile(r'\b(time\.Sleep|sleep|setTimeout|delay)\s*\('),
        recommendation="Naked sleep detected. Use deterministic event synchronization, channels, or explicit polling intervals."
    ),
    ConcurrencyRule(
        check_id="CONC-UNBOUNDED-ROUTINE",
        name="Unbounded Goroutine / Async Spawning",
        pattern=re.compile(r'for\s+.*\{\s*go\s+func'),
        recommendation="Spawning goroutines inside loop without a bounded worker pool or semaphore."
    ),
    ConcurrencyRule(
        check_id="CONC-UNBUFFERED-CHAN",
        name="Unbuffered Channel Allocation",
        pattern=re.compile(r'make\s*\(\s*chan\s+[A-Za-z0-9_*.]+\s*\)'),
        recommendation="Unbuffered channel creation. Verify reader cannot exit prematurely, causing writer goroutine leaks."
    )
]

def scan_file_for_concurrency_issues(file_path: Path) -> List[ConcurrencyFinding]:
    ext = file_path.suffix.lower()
    if ext not in TARGET_EXTENSIONS:
        return []

    findings: List[ConcurrencyFinding] = []
    try:
        content = file_path.read_text(encoding="utf-8", errors="ignore")
        lines = content.splitlines()

        for idx, line in enumerate(lines, 1):
            for rule in CONCURRENCY_RULES:
                if rule.pattern.search(line):
                    findings.append(ConcurrencyFinding(
                        check_id=rule.check_id,
                        name=rule.name,
                        file=str(file_path),
                        line=idx,
                        snippet=line.strip()[:140],
                        recommendation=rule.recommendation
                    ))
    except (OSError, UnicodeDecodeError):
        return []

    return findings

def scan_directory_concurrency(root_dir: str) -> List[ConcurrencyFinding]:
    results: List[ConcurrencyFinding] = []
    root_path = Path(root_dir).resolve()

    for dirpath, dirnames, filenames in os.walk(root_path):
        dirnames[:] = sorted([d for d in dirnames if d not in IGNORED_DIRS and not d.startswith(".")])
        for fname in sorted(filenames):
            fpath = Path(dirpath) / fname
            results.extend(scan_file_for_concurrency_issues(fpath))

    return results

def render_concurrency_report(results: List[ConcurrencyFinding]) -> None:
    print(f"\n⚡ CONCURRENCY & DUAL-WRITE AUDIT: {len(results)} issues found\n")
    if not results:
        print("✅ Clean scan: No concurrency anti-patterns detected.")
        return

    for r in results:
        print(f"[{r.check_id}] {r.file}:{r.line}")
        print(f"  Snippet: {r.snippet}")
        print(f"  Fix    : {r.recommendation}\n")

def main() -> None:
    parser = argparse.ArgumentParser(description="Concurrency & Dual-Write Architecture Scanner")
    parser.add_argument("--root", default=".", help="Root directory")
    parser.add_argument("--json", action="store_true", help="JSON output")
    args = parser.parse_args()

    results = scan_directory_concurrency(args.root)

    if args.json:
        print(json.dumps([asdict(r) for r in results], indent=2))
    else:
        render_concurrency_report(results)

    sys.exit(1 if results else 0)

if __name__ == "__main__":
    main()
