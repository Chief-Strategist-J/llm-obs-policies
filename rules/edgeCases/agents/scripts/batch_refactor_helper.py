#!/usr/bin/env python3
"""
Batch Refactoring Helper
Utility for AI agents to perform safe, structured, repo-wide search-and-replace refactorings with dry-run verification.
Usage:
    python3 batch_refactor_helper.py --find "regex_or_string" --replace "new_string" --ext .go,.ts [--dry-run]
"""

import os
import sys
import re
import argparse
from pathlib import Path

IGNORED_DIRS = {
    ".git", "node_modules", "dist", "build", ".next", "vendor",
    "__pycache__", "data", "brain", ".gemini", "scratch", "tmp", "bin"
}

def batch_replace(root_dir, find_pattern, replace_text, extensions, is_regex=False, dry_run=True):
    root_path = Path(root_dir)
    modified_files = 0
    total_occurrences = 0
    
    if is_regex:
        compiled_re = re.compile(find_pattern)
        
    for dirpath, dirnames, filenames in os.walk(root_path):
        dirnames[:] = [d for d in dirnames if d not in IGNORED_DIRS and not d.startswith(".")]
        
        for fname in filenames:
            fpath = Path(dirpath) / fname
            if fpath.suffix.lower() not in extensions:
                continue
                
            try:
                content = fpath.read_text(encoding="utf-8")
                
                if is_regex:
                    matches = compiled_re.findall(content)
                    if not matches:
                        continue
                    count = len(matches)
                    new_content = compiled_re.sub(replace_text, content)
                else:
                    if find_pattern not in content:
                        continue
                    count = content.count(find_pattern)
                    new_content = content.replace(find_pattern, replace_text)
                    
                total_occurrences += count
                modified_files += 1
                
                status = "[DRY-RUN WOULD MODIFY]" if dry_run else "[MODIFIED]"
                print(f"{status} {fpath} ({count} occurrences)")
                
                if not dry_run:
                    fpath.write_text(new_content, encoding="utf-8")
                    
            except Exception as e:
                print(f"Error processing {fpath}: {e}", file=sys.stderr)
                
    print(f"\nSummary: {total_occurrences} replacements across {modified_files} files. (Dry-run: {dry_run})")

def main():
    parser = argparse.ArgumentParser(description="Batch Code Refactoring Utility")
    parser.add_argument("--root", default=".", help="Root directory")
    parser.add_argument("--find", required=True, help="Pattern or string to find")
    parser.add_argument("--replace", required=True, help="Replacement string")
    parser.add_argument("--ext", default=".go,.ts,.js,.py,.sql", help="Comma-separated file extensions")
    parser.add_argument("--regex", action="store_true", help="Treat find pattern as regular expression")
    parser.add_argument("--apply", action="store_true", help="Apply changes (default is dry-run)")
    args = parser.parse_args()
    
    exts = set(e.strip().lower() for e in args.ext.split(","))
    batch_replace(args.root, args.find, args.replace, exts, is_regex=args.regex, dry_run=not args.apply)

if __name__ == "__main__":
    main()
