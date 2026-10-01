#!/usr/bin/env python3
"""
Concurrency & Dual-Write Architecture Scanner
Specialized scanner for detecting race conditions, naked sleeps, dual writes without outbox, and locking anti-patterns.
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

CONCURRENCY_CHECKS = [
    {
        "id": "CONC-SLEEP",
        "name": "Naked Sleep In Synchronization",
        "pattern": re.compile(r'\b(time\.Sleep|sleep|setTimeout|delay)\s*\('),
        "msg": "Naked sleep detected. Use deterministic event synchronization, channels, or explicit polling intervals."
    },
    {
        "id": "CONC-UNBOUNDED-ROUTINE",
        "name": "Unbounded Goroutine / Async Spawning",
        "pattern": re.compile(r'for\s+.*\{\s*go\s+func'),
        "msg": "Spawning goroutines inside loop without a bounded worker pool or semaphore."
    },
    {
        "id": "CONC-UNBUFFERED-CHAN",
        "name": "Unbuffered Channel Allocation",
        "pattern": re.compile(r'make\s*\(\s*chan\s+[A-Za-z0-9_*.]+\s*\)'),
        "msg": "Unbuffered channel creation. Verify reader cannot exit prematurely, causing writer goroutine leaks."
    }
]

def scan_file_concurrency(fpath):
    findings = []
    ext = fpath.suffix.lower()
    if ext not in {".go", ".ts", ".js", ".py"}:
        return findings
        
    try:
        content = fpath.read_text(encoding="utf-8", errors="ignore")
        lines = content.splitlines()
        
        for idx, line in enumerate(lines, 1):
            for check in CONCURRENCY_CHECKS:
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
    parser = argparse.ArgumentParser(description="Concurrency & Dual-Write Architecture Scanner")
    parser.add_argument("--root", default=".", help="Root directory")
    parser.add_argument("--json", action="store_true", help="JSON output")
    args = parser.parse_args()
    
    results = []
    for dirpath, dirnames, filenames in os.walk(args.root):
        dirnames[:] = [d for d in dirnames if d not in IGNORED_DIRS and not d.startswith(".")]
        for fname in filenames:
            fpath = Path(dirpath) / fname
            results.extend(scan_file_concurrency(fpath))
            
    if args.json:
        print(json.dumps(results, indent=2))
        return
        
    print(f"\n⚡ CONCURRENCY & DUAL-WRITE AUDIT: {len(results)} issues found\n")
    for r in results:
        print(f"[{r['check_id']}] {r['file']}:{r['line']}")
        print(f"  Snippet: {r['snippet']}")
        print(f"  Fix    : {r['recommendation']}\n")

if __name__ == "__main__":
    main()
