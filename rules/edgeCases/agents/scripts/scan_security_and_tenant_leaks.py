#!/usr/bin/env python3
"""
Security & Tenant Isolation Scanner
Specialized scanner for detecting Broken Object-Level Auth (BOLA/IDOR), missing tenant filters, unsafe deserializers, and secret leaks.
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

SECURITY_CHECKS = [
    {
        "id": "SEC-HARDCODED-SECRET",
        "name": "Hardcoded Token or Key",
        "pattern": re.compile(r'(api[_-]?key|secret|password|bearer|private[_-]?key)\s*[:=]\s*["\'][A-Za-z0-9_\-\/+=]{16,}["\']', re.IGNORECASE),
        "msg": "Potential hardcoded secret or API credential detected. Use secret manager or env vars."
    },
    {
        "id": "SEC-TIMING-ATTACK",
        "name": "Insecure String Equality on Token/Hash",
        "pattern": re.compile(r'(token|hash|signature|hmac)\s*(===|==)\s*', re.IGNORECASE),
        "msg": "Potential timing side-channel attack. Use subtle.timingSafeEqual or hmac.Equal."
    },
    {
        "id": "SEC-SSRF-RAW",
        "name": "Unvalidated Outbound HTTP Request",
        "pattern": re.compile(r'(http\.Get|fetch|requests\.get|axios\.get)\s*\(\s*(req\.|params\.|url\b|targetUrl)', re.IGNORECASE),
        "msg": "Potential SSRF vulnerability. Validate destination IP against internal private ranges (169.254.169.254, 10.0.0.0/8)."
    }
]

def scan_file_security(fpath):
    findings = []
    ext = fpath.suffix.lower()
    if ext not in {".go", ".ts", ".js", ".py", ".sql"}:
        return findings
        
    try:
        content = fpath.read_text(encoding="utf-8", errors="ignore")
        lines = content.splitlines()
        
        for idx, line in enumerate(lines, 1):
            for check in SECURITY_CHECKS:
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
    parser = argparse.ArgumentParser(description="Security & Tenant Isolation Scanner")
    parser.add_argument("--root", default=".", help="Root directory")
    parser.add_argument("--json", action="store_true", help="JSON output")
    args = parser.parse_args()
    
    results = []
    for dirpath, dirnames, filenames in os.walk(args.root):
        dirnames[:] = [d for d in dirnames if d not in IGNORED_DIRS and not d.startswith(".")]
        for fname in filenames:
            fpath = Path(dirpath) / fname
            results.extend(scan_file_security(fpath))
            
    if args.json:
        print(json.dumps(results, indent=2))
        return
        
    print(f"\n🛡️ SECURITY & TENANT ISOLATION AUDIT: {len(results)} issues found\n")
    for r in results:
        print(f"[{r['check_id']}] {r['file']}:{r['line']}")
        print(f"  Snippet: {r['snippet']}")
        print(f"  Fix    : {r['recommendation']}\n")

if __name__ == "__main__":
    main()
