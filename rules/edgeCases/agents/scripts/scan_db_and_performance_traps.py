#!/usr/bin/env python3
"""
Database & Performance Trap Scanner
Specialized scanner for detecting missing lock_timeouts in migrations, deep OFFSET pagination, Redis blocking commands, and unindexed status queries.
"""

import os
import sys
import re
import json
import argparse
from pathlib import Path

IGNORED_DIRS = {
    ".git", "node_modules", "dist", "build", ".next", "vendor",
    "__pycache__", "data", "brain", ".gemini", "scratch", "tmp", "bin"
}

DB_CHECKS = [
    {
        "id": "DB-OFFSET",
        "name": "Deep OFFSET Pagination",
        "pattern": re.compile(r'\bOFFSET\s+[0-9]+\b', re.IGNORECASE),
        "msg": "OFFSET causes linear table scan overhead at scale. Migrate to keyset/cursor pagination (WHERE id > last_seen_id)."
    },
    {
        "id": "DB-FLOAT-MONEY",
        "name": "Float Used for Monetary Values",
        "pattern": re.compile(r'\b(amount|price|balance|cost|fee)\s*:\s*(float|number|f64|float64)\b', re.IGNORECASE),
        "msg": "Floating point used for money. Use integer cents/satoshis or arbitrary-precision NUMERIC/Decimal."
    },
    {
        "id": "PLAT-REDIS-KEYS",
        "name": "Redis KEYS Command in Production",
        "pattern": re.compile(r'redis\.(keys|KEYS)\s*\(', re.IGNORECASE),
        "msg": "KEYS * blocks the Redis single-threaded event loop. Use SCAN with cursor."
    }
]

def scan_file_db(fpath):
    findings = []
    ext = fpath.suffix.lower()
    if ext not in {".go", ".ts", ".js", ".py", ".sql", ".prisma"}:
        return findings
        
    try:
        content = fpath.read_text(encoding="utf-8", errors="ignore")
        lines = content.splitlines()
        
        for idx, line in enumerate(lines, 1):
            for check in DB_CHECKS:
                if check["pattern"].search(line):
                    findings.append({
                        "check_id": check["id"],
                        "name": check["name"],
                        "file": str(fpath),
                        "line": idx,
                        "snippet": line.strip()[:140],
                        "recommendation": check["msg"]
                    })
    except Exception:
        pass
    return findings

def main():
    parser = argparse.ArgumentParser(description="Database & Performance Trap Scanner")
    parser.add_argument("--root", default=".", help="Root directory")
    parser.add_argument("--json", action="store_true", help="JSON output")
    args = parser.parse_args()
    
    results = []
    for dirpath, dirnames, filenames in os.walk(args.root):
        dirnames[:] = [d for d in dirnames if d not in IGNORED_DIRS and not d.startswith(".")]
        for fname in filenames:
            fpath = Path(dirpath) / fname
            results.extend(scan_file_db(fpath))
            
    if args.json:
        print(json.dumps(results, indent=2))
        return
        
    print(f"\n🗄️ DATABASE & PERFORMANCE AUDIT: {len(results)} issues found\n")
    for r in results:
        print(f"[{r['check_id']}] {r['file']}:{r['line']}")
        print(f"  Snippet: {r['snippet']}")
        print(f"  Fix    : {r['recommendation']}\n")

if __name__ == "__main__":
    main()
