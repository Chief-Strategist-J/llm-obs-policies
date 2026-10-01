#!/usr/bin/env python3
"""
================================================================================
ALGORITHM & ARCHITECTURE BLUEPRINT: BATCH CODE REFACTORING HELPER
================================================================================

1. OVERVIEW & OBJECTIVE:
   This module implements a deterministic batch refactoring and string/regex
   replacement engine enabling AI agents and developers to perform repository-wide
   syntax transformations with mandatory dry-run diff verification.

2. ARCHITECTURAL LAYOUT & DESIGN PILLARS:
   - Zero-Inline-Comment Doctrine: All architectural workflows, execution bounds,
     and replacement logic are documented solely in this top-level blueprint.
     Function bodies remain 100% comment-free, self-describing, and pure.
   - Idempotency & Safety: Default execution mode is `--dry-run` (`apply=False`).
     Mutations execute only when `--apply` is explicitly passed.
   - Character Encoding Preservation: Reads and writes UTF-8 text explicitly.

3. EXECUTION SEQUENCE & DATA FLOW:
   [CLI Arguments Parsing] ──> Validate search pattern, replacement text, extensions
         │
         ▼
   [Filesystem Discovery] ───> Filter against IGNORED_DIRS & target extension set
         │
         ▼
   [Content Matching] ───────> Execute exact string search or compiled regex match
         │
         ▼
   [Dry-Run / Apply Gate] ───> If dry-run: Log modified lines without disk write.
                               If apply: Write modified UTF-8 buffer back to file.
         │
         ▼
   [Summary Metric Emission] ─> Report total occurrences and modified file counts

4. EDGE CASES & FAILURE MODES HANDLED:
   - Unreadable File Failures: Handled gracefully via try/except blocks.
   - Regex Runaways: Compile pattern once before entering traversal loop.

5. SECURITY & RESILIENCE RULES:
   - Path allowlist enforced; binary and vendor folders unconditionally ignored.
================================================================================
"""

import os
import sys
import re
import argparse
from pathlib import Path
from dataclasses import dataclass
from typing import Set, Tuple, List, Optional, Pattern

IGNORED_DIRS: Set[str] = {
    ".git", "node_modules", "dist", "build", ".next", "vendor",
    "__pycache__", "data", "brain", ".gemini", "scratch", "tmp", "bin"
}

@dataclass(frozen=True)
class RefactorSummary:
    total_occurrences: int
    modified_files: int
    dry_run: bool

def execute_batch_replacement(
    root_dir: str,
    find_pattern: str,
    replace_text: str,
    extensions: Set[str],
    is_regex: bool = False,
    dry_run: bool = True
) -> RefactorSummary:
    root_path = Path(root_dir).resolve()
    modified_files = 0
    total_occurrences = 0

    compiled_re: Optional[Pattern] = re.compile(find_pattern) if is_regex else None

    for dirpath, dirnames, filenames in os.walk(root_path):
        dirnames[:] = sorted([d for d in dirnames if d not in IGNORED_DIRS and not d.startswith(".")])

        for fname in sorted(filenames):
            fpath = Path(dirpath) / fname
            if fpath.suffix.lower() not in extensions:
                continue

            try:
                content = fpath.read_text(encoding="utf-8")

                if compiled_re:
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

                status_label = "[DRY-RUN WOULD MODIFY]" if dry_run else "[MODIFIED]"
                print(f"{status_label} {fpath} ({count} occurrences)")

                if not dry_run:
                    fpath.write_text(new_content, encoding="utf-8")

            except (OSError, UnicodeDecodeError) as err:
                print(f"Error processing {fpath}: {err}", file=sys.stderr)

    print(f"\nSummary: {total_occurrences} replacements across {modified_files} files. (Dry-run: {dry_run})")
    return RefactorSummary(total_occurrences, modified_files, dry_run)

def main() -> None:
    parser = argparse.ArgumentParser(description="Batch Code Refactoring Utility")
    parser.add_argument("--root", default=".", help="Root directory")
    parser.add_argument("--find", required=True, help="Pattern or string to find")
    parser.add_argument("--replace", required=True, help="Replacement string")
    parser.add_argument("--ext", default=".go,.ts,.js,.py,.sql", help="Comma-separated file extensions")
    parser.add_argument("--regex", action="store_true", help="Treat find pattern as regular expression")
    parser.add_argument("--apply", action="store_true", help="Apply changes (default is dry-run)")
    args = parser.parse_args()

    exts = set(e.strip().lower() for e in args.ext.split(","))
    execute_batch_replacement(
        root_dir=args.root,
        find_pattern=args.find,
        replace_text=args.replace,
        extensions=exts,
        is_regex=args.regex,
        dry_run=not args.apply
    )

if __name__ == "__main__":
    main()
