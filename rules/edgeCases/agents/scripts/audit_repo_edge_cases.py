#!/usr/bin/env python3
"""
Master Repository Edge-Case & Invariant Scanner
Executes multi-vector checks across Go, TypeScript/JavaScript, Python, and SQL files.
Usage:
    python3 audit_repo_edge_cases.py --root <path-to-repo> [--json]
"""

import os
import sys
import re
import json
import argparse
from pathlib import Path

# Directories to ignore
IGNORED_DIRS = {
    ".git", "node_modules", "dist", "build", ".next", "vendor",
    ".idea", ".vscode", "__pycache__", ".turbo", "coverage",
    "data", "brain", ".gemini", "scratch", "tmp", "bin"
}

# Scan rules dictionary
RULES = [
    {
        "id": "CONC-001",
        "category": "Concurrency",
        "severity": "CRITICAL",
        "description": "Naked sleep used for synchronization or retry waiting",
        "pattern": re.compile(r'(time\.Sleep\s*\(|sleep\s*\(\d+\)|setTimeout\s*\([^,]+,\s*\d+\))'),
        "extensions": {".go", ".ts", ".js", ".py"}
    },
    {
        "id": "SEC-001",
        "category": "Security",
        "severity": "CRITICAL",
        "description": "SQL String Interpolation (Potential SQL Injection)",
        "pattern": re.compile(r'(SELECT|INSERT|UPDATE|DELETE).*\+\s*(\w+|req\.|params\.)|\b(SELECT|INSERT|UPDATE|DELETE).*f["\']', re.IGNORECASE),
        "extensions": {".go", ".ts", ".js", ".py"}
    },
    {
        "id": "SEC-002",
        "category": "Security",
        "severity": "HIGH",
        "description": "Unsafe Deserialization (pickle.loads or yaml.load without SafeLoader)",
        "pattern": re.compile(r'(pickle\.loads?|yaml\.load\([^,)]+\))'),
        "extensions": {".py"}
    },
    {
        "id": "DB-001",
        "category": "Database",
        "severity": "HIGH",
        "description": "Deep OFFSET pagination (Use keyset/cursor pagination instead)",
        "pattern": re.compile(r'\bOFFSET\s+\d+\b', re.IGNORECASE),
        "extensions": {".sql", ".go", ".ts", ".js", ".py"}
    },
    {
        "id": "DB-002",
        "category": "Database",
        "severity": "CRITICAL",
        "description": "DDL migration missing lock_timeout",
        "pattern": re.compile(r'(ALTER\s+TABLE|DROP\s+TABLE|CREATE\s+INDEX(?!\s+CONCURRENTLY))', re.IGNORECASE),
        "extensions": {".sql"}
    },
    {
        "id": "PLAT-001",
        "category": "Platform",
        "severity": "CRITICAL",
        "description": "Redis blocking command (KEYS * or FLUSHALL)",
        "pattern": re.compile(r'(redis\.(keys|flushall|flushdb)\(|KEYS\s+["\']\*["\'])', re.IGNORECASE),
        "extensions": {".go", ".ts", ".js", ".py"}
    },
    {
        "id": "ERR-001",
        "category": "Observability",
        "severity": "MEDIUM",
        "description": "Empty catch / error swallowing",
        "pattern": re.compile(r'catch\s*\([^)]*\)\s*\{\s*\}|except:\s*pass|except\s+\w+:\s*pass'),
        "extensions": {".ts", ".js", ".py"}
    }
]

def scan_file(file_path):
    ext = file_path.suffix.lower()
    findings = []
    
    # Skip non-target extensions
    allowed_exts = {".go", ".ts", ".js", ".py", ".sql"}
    if ext not in allowed_exts:
        return findings
        
    try:
        with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
            lines = f.readlines()
            
        for line_num, line in enumerate(lines, 1):
            for rule in RULES:
                if ext in rule["extensions"]:
                    if rule["pattern"].search(line):
                        findings.append({
                            "rule_id": rule["id"],
                            "category": rule["category"],
                            "severity": rule["severity"],
                            "description": rule["description"],
                            "file": str(file_path),
                            "line": line_num,
                            "snippet": line.strip()[:140]
                        })
    except Exception:
        pass
        
    return findings

def walk_and_scan(root_dir):
    all_findings = []
    root_path = Path(root_dir)
    
    for dirpath, dirnames, filenames in os.walk(root_path):
        # Remove ignored directories in place
        dirnames[:] = [d for d in dirnames if d not in IGNORED_DIRS and not d.startswith(".")]
        
        for fname in filenames:
            fpath = Path(dirpath) / fname
            findings = scan_file(fpath)
            all_findings.extend(findings)
            
    return all_findings

def main():
    parser = argparse.ArgumentParser(description="Master Edge-Case Codebase Scanner")
    parser.add_argument("--root", default=".", help="Root directory to scan (default: current dir)")
    parser.add_argument("--json", action="store_true", help="Output findings as JSON")
    args = parser.parse_args()
    
    findings = walk_and_scan(args.root)
    
    if args.json:
        print(json.dumps(findings, indent=2))
        return
        
    print(f"\n{'='*75}")
    print(f"🔍 EDGE-CASE & INVARIANT SCAN RESULTS: {len(findings)} Total Findings")
    print(f"{'='*75}\n")
    
    if not findings:
        print("✅ No edge-case violations detected! Clean scan.")
        return
        
    by_severity = {"CRITICAL": [], "HIGH": [], "MEDIUM": [], "LOW": []}
    for f in findings:
        by_severity.get(f["severity"], by_severity["MEDIUM"]).append(f)
        
    for sev in ["CRITICAL", "HIGH", "MEDIUM", "LOW"]:
        items = by_severity[sev]
        if items:
            print(f"\n--- [{sev}] ({len(items)} issues) ---")
            for item in items:
                print(f"  [{item['rule_id']}] {item['file']}:{item['line']}")
                print(f"     Description: {item['description']}")
                print(f"     Snippet    : {item['snippet']}\n")

if __name__ == "__main__":
    main()
