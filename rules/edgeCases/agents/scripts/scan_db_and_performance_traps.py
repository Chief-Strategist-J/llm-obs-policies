#!/usr/bin/env python3
"""
================================================================================
ALGORITHM & ARCHITECTURE BLUEPRINT: DATABASE & PERFORMANCE TRAP SCANNER
================================================================================

1. OVERVIEW & OBJECTIVE:
   This module implements an automated database, query performance, and platform
   antipattern analyzer scanning SQL migrations, Prisma schemas, Go, TypeScript,
   JavaScript, and Python services for blocking Redis operations, unindexed deep
   OFFSET queries, and floating-point currency calculations.

2. ARCHITECTURAL LAYOUT & DESIGN PILLARS:
   - Zero-Inline-Comment Doctrine: All algorithmic requirements, regular expression
     matrices, and operational bounds are encapsulated in this top-side blueprint.
     Function bodies remain 100% comment-free, self-describing, and pure.
   - Frozen Dataclass Rule Architecture: Immutable rule and finding definitions.
   - High Precision Target Filtering: Specific file extensions scanned per rule.

3. EXECUTION SEQUENCE & DATA FLOW:
   [CLI Flags Input]
         │
         ▼
   [Filesystem Discovery] ──> Exclude non-target directories & filter extensions
         │
         ▼
   [Database Rule Matrix] ──> Match line patterns across DB_RULES
         │
         ▼
   [Finding Formulation] ───> Populate typed DatabaseFinding records
         │
         ▼
   [Report Generation] ─────> Format JSON or ANSI-colorized terminal output

4. EDGE CASES & FAILURE MODES HANDLED:
   - File Access Invariants: Graceful handling of file read permissions.
   - Lexicographical Consistency: Alphabetical file and finding order.

5. SECURITY & RESILIENCE RULES:
   - Read-only execution with non-zero exit codes when violations are detected.
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

ALLOWED_EXTENSIONS: Set[str] = {".go", ".ts", ".js", ".py", ".sql", ".prisma"}

@dataclass(frozen=True)
class DatabaseRule:
    check_id: str
    name: str
    pattern: Pattern
    recommendation: str

@dataclass(frozen=True)
class DatabaseFinding:
    check_id: str
    name: str
    file: str
    line: int
    snippet: str
    recommendation: str

DB_RULES: List[DatabaseRule] = [
    DatabaseRule(
        check_id="DB-OFFSET",
        name="Deep OFFSET Pagination",
        pattern=re.compile(r'\bOFFSET\s+[0-9]+\b', re.IGNORECASE),
        recommendation="OFFSET causes linear table scan overhead at scale. Migrate to keyset/cursor pagination (WHERE id > last_seen_id)."
    ),
    DatabaseRule(
        check_id="DB-FLOAT-MONEY",
        name="Float Used for Monetary Values",
        pattern=re.compile(r'\b(amount|price|balance|cost|fee)\s*:\s*(float|number|f64|float64)\b', re.IGNORECASE),
        recommendation="Floating point used for money. Use integer cents/satoshis or arbitrary-precision NUMERIC/Decimal."
    ),
    DatabaseRule(
        check_id="PLAT-REDIS-KEYS",
        name="Redis KEYS Command in Production",
        pattern=re.compile(r'redis\.(keys|KEYS)\s*\(', re.IGNORECASE),
        recommendation="KEYS * blocks the Redis single-threaded event loop. Use SCAN with cursor."
    )
]

def scan_file_for_db_traps(file_path: Path) -> List[DatabaseFinding]:
    ext = file_path.suffix.lower()
    if ext not in ALLOWED_EXTENSIONS:
        return []

    findings: List[DatabaseFinding] = []
    try:
        content = file_path.read_text(encoding="utf-8", errors="ignore")
        lines = content.splitlines()

        for idx, line in enumerate(lines, 1):
            for rule in DB_RULES:
                if rule.pattern.search(line):
                    findings.append(DatabaseFinding(
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

def scan_directory_database(root_dir: str) -> List[DatabaseFinding]:
    results: List[DatabaseFinding] = []
    root_path = Path(root_dir).resolve()

    for dirpath, dirnames, filenames in os.walk(root_path):
        dirnames[:] = sorted([d for d in dirnames if d not in IGNORED_DIRS and not d.startswith(".")])
        for fname in sorted(filenames):
            fpath = Path(dirpath) / fname
            results.extend(scan_file_for_db_traps(fpath))

    return results

def render_database_report(results: List[DatabaseFinding]) -> None:
    print(f"\n🗄️ DATABASE & PERFORMANCE AUDIT: {len(results)} issues found\n")
    if not results:
        print("✅ Clean scan: No database or performance traps detected.")
        return

    for r in results:
        print(f"[{r.check_id}] {r.file}:{r.line}")
        print(f"  Snippet: {r.snippet}")
        print(f"  Fix    : {r.recommendation}\n")

def main() -> None:
    parser = argparse.ArgumentParser(description="Database & Performance Trap Scanner")
    parser.add_argument("--root", default=".", help="Root directory")
    parser.add_argument("--json", action="store_true", help="JSON output")
    args = parser.parse_args()

    results = scan_directory_database(args.root)

    if args.json:
        print(json.dumps([asdict(r) for r in results], indent=2))
    else:
        render_database_report(results)

    sys.exit(1 if results else 0)

if __name__ == "__main__":
    main()
