#!/usr/bin/env python3
"""Validate dandiset metadata and structure for all registered dandisets.

This script checks that each dandiset listed in .gitmodules has valid
metadata and that the submodule paths are consistent.
"""

import configparser
import re
import sys
from pathlib import Path


GITMODULES_PATH = Path(__file__).parent.parent / ".gitmodules"
DANDISET_ID_PATTERN = re.compile(r"^\d{6}$")


def parse_gitmodules(path: Path) -> list[dict]:
    """Parse .gitmodules and return a list of submodule entries."""
    config = configparser.ConfigParser()
    # configparser requires section headers; gitmodules uses quoted section names
    content = path.read_text(encoding="utf-8")
    config.read_string(content)

    modules = []
    for section in config.sections():
        entry = dict(config[section])
        entry["name"] = section.split('"')[1] if '"' in section else section
        modules.append(entry)
    return modules


def validate_dandiset_id(dandiset_id: str) -> bool:
    """Check that a dandiset ID is a zero-padded 6-digit string."""
    return bool(DANDISET_ID_PATTERN.match(dandiset_id))


def validate_module(module: dict) -> list[str]:
    """Validate a single submodule entry, returning a list of error messages."""
    errors = []

    name = module.get("name", "")
    path = module.get("path", "")
    url = module.get("url", "")

    if not name:
        errors.append("Missing submodule name")

    if not path:
        errors.append(f"[{name}] Missing 'path' field")
    else:
        dandiset_id = Path(path).name
        if not validate_dandiset_id(dandiset_id):
            errors.append(
                f"[{name}] Path '{path}' does not end with a valid 6-digit dandiset ID"
            )

    if not url:
        errors.append(f"[{name}] Missing 'url' field")
    elif "dandiarchive" not in url and "github.com" not in url:
        errors.append(
            f"[{name}] URL '{url}' does not appear to be a valid dandiset URL"
        )

    # Ensure path and name are consistent
    if path and name and Path(path).name != name.split("/")[-1]:
        errors.append(
            f"[{name}] Submodule name '{name}' does not match path '{path}'"
        )

    return errors


def main() -> int:
    """Run validation and report results."""
    if not GITMODULES_PATH.exists():
        print(f"ERROR: {GITMODULES_PATH} not found", file=sys.stderr)
        return 1

    print(f"Parsing {GITMODULES_PATH} ...")
    try:
        modules = parse_gitmodules(GITMODULES_PATH)
    except Exception as exc:
        print(f"ERROR: Failed to parse .gitmodules: {exc}", file=sys.stderr)
        return 1

    print(f"Found {len(modules)} submodule(s). Validating...")

    all_errors: list[str] = []
    for module in modules:
        errors = validate_module(module)
        all_errors.extend(errors)

    if all_errors:
        print(f"\nValidation FAILED with {len(all_errors)} error(s):")
        for err in all_errors:
            print(f"  - {err}")
        return 1
    else:
        print(f"\nValidation PASSED. All {len(modules)} submodule(s) look good.")
        return 0


if __name__ == "__main__":
    sys.exit(main())
