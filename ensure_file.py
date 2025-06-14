#!/usr/bin/env python3
import argparse
import difflib
import re
import sys
from pathlib import Path

EXIT_OK = 0
EXIT_GENERIC_FAIL = 1
EXIT_PERMISSIONS = 2
EXIT_NO_MATCH = 3
EXIT_NO_CHANGE_NEEDED = 4
EXIT_NOT_FOUND = 5

def exit_ok_or_noop(idempotent_ok):
    sys.exit(EXIT_OK if idempotent_ok else EXIT_NO_CHANGE_NEEDED)

def show_diff_and_confirm(old, new, path, force=False, quiet=False):
    if old == new:
        if not quiet:
            print(f"No changes needed for {path}")
        return None  # signal "no change"
    if not quiet:
        diff = list(difflib.unified_diff(
            old.splitlines(keepends=True),
            new.splitlines(keepends=True),
            fromfile=f"{path}.old",
            tofile=f"{path}.new"
        ))
        print("".join(diff))
    if force:
        return True
    resp = input("Apply changes? [y/N]: ").strip().lower()
    return resp == "y"

def safe_read(path, quiet):
    try:
        return path.read_text(encoding="utf-8")
    except FileNotFoundError:
        if not quiet:
            print(f"File not found: {path}", file=sys.stderr)
        sys.exit(EXIT_NOT_FOUND)
    except PermissionError:
        if not quiet:
            print(f"Permission denied: {path}", file=sys.stderr)
        sys.exit(EXIT_PERMISSIONS)

def ensure_line(path, line, force=False, quiet=False, idempotent_ok=False):
    path = Path(path)
    old = safe_read(path, quiet) if path.exists() else ""
    lines = old.splitlines()
    if line in lines:
        if not quiet:
            print(f"Line already present in {path}")
        exit_ok_or_noop(idempotent_ok)
    lines.append(line)
    new = '\n'.join(lines) + '\n'
    confirmed = show_diff_and_confirm(old, new, path, force, quiet)
    if confirmed is None:
        exit_ok_or_noop(idempotent_ok)
    if confirmed:
        try:
            path.write_text(new, encoding="utf-8")
        except PermissionError:
            if not quiet:
                print(f"Permission denied: {path}", file=sys.stderr)
            sys.exit(EXIT_PERMISSIONS)
        if not quiet:
            print(f"Updated {path}")
        sys.exit(EXIT_OK)
    exit_ok_or_noop(idempotent_ok)

def ensure_block(path, block_lines, marker_start, marker_end,
                 force=False, quiet=False, idempotent_ok=True):
    path = Path(path)
    old = safe_read(path, quiet) if path.exists() else ""
    block = '\n'.join([marker_start] + block_lines + [marker_end])

    if marker_start in old and marker_end in old:
        start = old.index(marker_start)
        end = old.index(marker_end) + len(marker_end)
        before = old[:start].rstrip()
        after = old[end:].lstrip()
        new = before + '\n' + block + '\n' + after
    else:
        prefix = old.rstrip()
        if prefix:
            new = prefix + '\n' + block + '\n'
        else:
            new = block + '\n'

    if old == new:
        if not quiet:
            print(f"Block already correct in {path}")
        exit_ok_or_noop(idempotent_ok)

    confirmed = show_diff_and_confirm(old, new, path, force, quiet)
    if confirmed is None:
        exit_ok_or_noop(idempotent_ok)
    if confirmed:
        try:
            path.write_text(new, encoding="utf-8")
        except PermissionError:
            if not quiet:
                print(f"Permission denied: {path}", file=sys.stderr)
            sys.exit(EXIT_PERMISSIONS)
        if not quiet:
            print(f"Updated {path}")
        sys.exit(EXIT_OK)

    exit_ok_or_noop(idempotent_ok)

def replace_line(path, old_line, new_line, force=False, quiet=False, idempotent_ok=False):
    path = Path(path)
    old = safe_read(path, quiet)
    lines = old.splitlines()
    match_found = False
    changed = False
    new_lines = []
    for l in lines:
        if l == old_line:
            match_found = True
            if l != new_line:
                new_lines.append(new_line)
                changed = True
            else:
                new_lines.append(l)
        else:
            new_lines.append(l)
    if not match_found:
        if not quiet:
            print(f"No exact match found for replacement in {path}")
        sys.exit(EXIT_NO_MATCH)
    if not changed:
        if not quiet:
            print(f"Line matched but already correct in {path}")
        exit_ok_or_noop(idempotent_ok)
    new = '\n'.join(new_lines) + '\n'
    confirmed = show_diff_and_confirm(old, new, path, force, quiet)
    if confirmed is None:
        exit_ok_or_noop(idempotent_ok)
    if confirmed:
        try:
            path.write_text(new, encoding="utf-8")
        except PermissionError:
            if not quiet:
                print(f"Permission denied: {path}", file=sys.stderr)
            sys.exit(EXIT_PERMISSIONS)
        if not quiet:
            print(f"Updated {path}")
        sys.exit(EXIT_OK)
    exit_ok_or_noop(idempotent_ok)

def replace_line_re(path, pattern, replacement, force=False, quiet=False, idempotent_ok=False):
    path = Path(path)
    old = safe_read(path, quiet)
    lines = old.splitlines()
    match_found = False
    changed = False
    new_lines = []
    for l in lines:
        if re.search(pattern, l):
            match_found = True
        new_l = re.sub(pattern, replacement, l)
        if new_l != l:
            changed = True
        new_lines.append(new_l)
    if not match_found:
        if not quiet:
            print(f"No regex matches found in {path}")
        sys.exit(EXIT_NO_MATCH)
    if not changed:
        if not quiet:
            print(f"Regex match found, but no changes needed in {path}")
        exit_ok_or_noop(idempotent_ok)
    new = '\n'.join(new_lines) + '\n'
    confirmed = show_diff_and_confirm(old, new, path, force, quiet)
    if confirmed is None:
        exit_ok_or_noop(idempotent_ok)
    if confirmed:
        try:
            path.write_text(new, encoding="utf-8")
        except PermissionError:
            if not quiet:
                print(f"Permission denied: {path}", file=sys.stderr)
            sys.exit(EXIT_PERMISSIONS)
        if not quiet:
            print(f"Updated {path}")
        sys.exit(EXIT_OK)
    exit_ok_or_noop(idempotent_ok)

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("filepath")
    parser.add_argument("--line", help="Line to ensure")
    parser.add_argument("--block", nargs="+", help="Block lines (requires --start and --end)")
    parser.add_argument("--start", help="Start marker for block")
    parser.add_argument("--end", help="End marker for block")
    parser.add_argument("--replace", nargs=2, metavar=("FROM", "TO"), help="Replace exact line")
    parser.add_argument("--replace-re", nargs=2, metavar=("PATTERN", "REPLACEMENT"), help="Replace lines using regex")
    parser.add_argument("-f", "--force", action="store_true", help="Apply without prompting")
    parser.add_argument("-q", "--quiet", action="store_true", help="Suppress diff and messages")
    parser.add_argument("-I", "--idempotent-fail", action="store_true", help="Treat 'already correct' as failure (exit 4)")
    args = parser.parse_args()

    try:
        if args.line:
            ensure_line(args.filepath, args.line, args.force, args.quiet, not args.idempotent_fail)
        elif args.block and args.start and args.end:
            ensure_block(args.filepath, args.block, args.start, args.end, args.force, args.quiet, not args.idempotent_fail)
        elif args.replace:
            replace_line(args.filepath, args.replace[0], args.replace[1], args.force, args.quiet, not args.idempotent_fail)
        elif args.replace_re:
            replace_line_re(args.filepath, args.replace_re[0], args.replace_re[1], args.force, args.quiet, not args.idempotent_fail)
        else:
            print("Error: Must specify --line, --block with --start/--end, --replace, or --replace-re", file=sys.stderr)
            sys.exit(EXIT_GENERIC_FAIL)
    except Exception as e:
        print(f"Unhandled error: {e}", file=sys.stderr)
        sys.exit(EXIT_GENERIC_FAIL)

if __name__ == "__main__":
    main()

