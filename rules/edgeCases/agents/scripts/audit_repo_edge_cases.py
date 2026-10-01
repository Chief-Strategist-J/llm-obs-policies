#!/usr/bin/env python3
"""
================================================================================
ALGORITHM & ARCHITECTURE BLUEPRINT: MASTER REPOSITORY EDGE-CASE AUDITOR
================================================================================

1. OVERVIEW & OBJECTIVE:
   This module implements an automated, high-throughput static analysis scanner
   designed to detect edge cases, safety invariant violations, anti-patterns,
   and operational risks across polyglot source repositories (Go, TypeScript,
   JavaScript, Python, and SQL).

2. ARCHITECTURAL LAYOUT & DESIGN PILLARS:
   - Zero-Inline-Comment Doctrine: All algorithmic documentation, control flow
     specifications, and operational invariants are centralized strictly in this
     top-side blueprint header. Function bodies remain 100% comment-free.
   - Strict Type Safety: All domain models, rule definitions, and scanner results
     are strongly typed using standard dataclasses and typing primitives.
   - Deterministic Execution: File traversal paths and rule evaluations are
     lexicographically sorted to ensure reproducible findings across runs.
   - Bounded Resource Invariants: Traversal skips binary, cache, and vendor
     directories to prevent I/O thrashing and memory exhaustion.

3. EXECUTION SEQUENCE & DATA FLOW:
   [CLI Invocation] 
         │
         ▼
   [Path Resolution & Validation] ──> Filter against IGNORED_DIRS set
         │
         ▼
   [File Stream Pipeline] ───────────> Inspect file extension allowlist
         │
         ▼
   [Regex Rule Engine Matching] ─────> Match line-by-line across compiled rules
         │
         ▼
   [Finding Aggregation & Triage] ───> Group by severity (CRITICAL, HIGH, MEDIUM, LOW)
         │
         ▼
   [Structured Output Emission] ─────> Format as JSON or ANSI-formatted terminal report

4. EDGE CASES & FAILURE MODES HANDLED:
   - Unreadable/Locked Files: Gracefully caught via OSError/UnicodeDecodeError,
     preventing scanner crashes on corrupt or binary buffers.
   - Permission Denied Directories: Skipped during filesystem traversal.
   - Large Monorepo Traversals: Streamed iteratively without buffering full trees.

5. SECURITY & RESILIENCE RULES:
   - Read-only filesystem operations; zero mutation side-effects.
   - Exit code 0 on clean repository scan; exit code 1 if CRITICAL/HIGH findings exist.
================================================================================
"""

import os
import sys
import re
import json
import argparse
from pathlib import Path
from dataclasses import dataclass, asdict
from typing import List, Set, Dict, Pattern, Optional

IGNORED_DIRS: Set[str] = {
    ".git", "node_modules", "dist", "build", ".next", "vendor",
    ".idea", ".vscode", "__pycache__", ".turbo", "coverage",
    "data", "brain", ".gemini", "scratch", "tmp", "bin"
}

ALLOWED_EXTENSIONS: Set[str] = {".go", ".ts", ".js", ".py", ".sql"}

@dataclass(frozen=True)
class AuditRule:
    rule_id: str
    category: str
    severity: str
    description: str
    pattern: Pattern
    extensions: Set[str]

@dataclass(frozen=True)
class Finding:
    rule_id: str
    category: str
    severity: str
    description: str
    file: str
    line: int
    snippet: str

RULES: List[AuditRule] = [
    AuditRule(
        rule_id="CONC-001",
        category="Concurrency",
        severity="CRITICAL",
        description="Naked sleep used for synchronization or retry waiting",
        pattern=re.compile(r'(time\.Sleep\s*\(|sleep\s*\(\d+\)|setTimeout\s*\([^,]+,\s*\d+\))'),
        extensions={".go", ".ts", ".js", ".py"}
    ),
    AuditRule(
        rule_id="SEC-001",
        category="Security",
        severity="CRITICAL",
        description="SQL String Interpolation (Potential SQL Injection)",
        pattern=re.compile(r'(SELECT|INSERT|UPDATE|DELETE).*\+\s*(\w+|req\.|params\.)|\b(SELECT|INSERT|UPDATE|DELETE).*f["\']', re.IGNORECASE),
        extensions={".go", ".ts", ".js", ".py"}
    ),
    AuditRule(
        rule_id="SEC-002",
        category="Security",
        severity="HIGH",
        description="Unsafe Deserialization (pickle.loads or yaml.load without SafeLoader)",
        pattern=re.compile(r'(pickle\.loads?|yaml\.load\([^,)]+\))'),
        extensions={".py"}
    ),
    AuditRule(
        rule_id="DB-001",
        category="Database",
        severity="HIGH",
        description="Deep OFFSET pagination (Use keyset/cursor pagination instead)",
        pattern=re.compile(r'\bOFFSET\s+\d+\b', re.IGNORECASE),
        extensions={".sql", ".go", ".ts", ".js", ".py"}
    ),
    AuditRule(
        rule_id="DB-002",
        category="Database",
        severity="CRITICAL",
        description="DDL migration missing lock_timeout",
        pattern=re.compile(r'(ALTER\s+TABLE|DROP\s+TABLE|CREATE\s+INDEX(?!\s+CONCURRENTLY))', re.IGNORECASE),
        extensions={".sql"}
    ),
    AuditRule(
        rule_id="PLAT-001",
        category="Platform",
        severity="CRITICAL",
        description="Redis blocking command (KEYS * or FLUSHALL)",
        pattern=re.compile(r'(redis\.(keys|flushall|flushdb)\(|KEYS\s+["\']\*["\'])', re.IGNORECASE),
        extensions={".go", ".ts", ".js", ".py"}
    ),
    AuditRule(
        rule_id="ERR-001",
        category="Observability",
        severity="MEDIUM",
        description="Empty catch / error swallowing",
        pattern=re.compile(r'catch\s*\([^)]*\)\s*\{\s*\}|except:\s*pass|except\s+\w+:\s*pass'),
        extensions={".ts", ".js", ".py"}
    )
]

def scan_file_contents(file_path: Path) -> List[Finding]:
    ext = file_path.suffix.lower()
    if ext not in ALLOWED_EXTENSIONS:
        return []

    findings: List[Finding] = []
    try:
        with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
            lines = f.readlines()

        for line_num, line in enumerate(lines, 1):
            for rule in RULES:
                if ext in rule.extensions and rule.pattern.search(line):
                    findings.append(Finding(
                        rule_id=rule.rule_id,
                        category=rule.category,
                        severity=rule.severity,
                        description=rule.description,
                        file=str(file_path),
                        line=line_num,
                        snippet=line.strip()[:140]
                    ))
    except (OSError, UnicodeDecodeError):
        return []

    return findings

def execute_repository_scan(root_directory: str) -> List[Finding]:
    all_findings: List[Finding] = []
    root_path = Path(root_directory).resolve()

    for dirpath, dirnames, filenames in os.walk(root_path):
        dirnames[:] = sorted([d for d in dirnames if d not in IGNORED_DIRS and not d.startswith(".")])
        
        for fname in sorted(filenames):
            fpath = Path(dirpath) / fname
            all_findings.extend(scan_file_contents(fpath))

    return all_findings

def render_terminal_report(findings: List[Finding]) -> None:
    print(f"\n{'='*75}")
    print(f"🔍 EDGE-CASE & INVARIANT SCAN RESULTS: {len(findings)} Total Findings")
    print(f"{'='*75}\n")

    if not findings:
        print("✅ No edge-case violations detected! Clean repository scan.")
        return

    by_severity: Dict[str, List[Finding]] = {"CRITICAL": [], "HIGH": [], "MEDIUM": [], "LOW": []}
    for f in findings:
        by_severity.get(f.severity, by_severity["MEDIUM"]).append(f)

    for sev in ["CRITICAL", "HIGH", "MEDIUM", "LOW"]:
        items = by_severity[sev]
        if items:
            print(f"\n--- [{sev}] ({len(items)} issues) ---")
            for item in items:
                print(f"  [{item.rule_id}] {item.file}:{item.line}")
                print(f"     Description: {item.description}")
                print(f"     Snippet    : {item.snippet}\n")

def main() -> None:
    parser = argparse.ArgumentParser(description="Master Edge-Case Codebase Scanner")
    parser.add_argument("--root", default=".", help="Root directory to scan (default: current dir)")
    parser.add_argument("--json", action="store_true", help="Output findings as JSON")
    args = parser.parse_args()

    findings = execute_repository_scan(args.root)

    if args.json:
        print(json.dumps([asdict(f) for f in findings], indent=2))
    else:
        render_terminal_report(findings)

    has_critical = any(f.severity in {"CRITICAL", "HIGH"} for f in findings)
    sys.exit(1 if has_critical else 0)

if __name__ == "__main__":
    main()
