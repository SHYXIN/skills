# -*- coding: utf-8 -*-
"""Synchronize an agent result package before platform upload.

This script intentionally does not run git add, commit, push, reset, or checkout.
"""

from __future__ import annotations

import argparse
import os
import subprocess
import sys
import zipfile
from pathlib import Path


def run_git(repo: Path, args: list[str]) -> str:
    try:
        result = subprocess.run(
            ["git", "-C", str(repo), *args],
            check=False,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
        )
    except FileNotFoundError:
        return "git not found"
    return (result.stdout + result.stderr).strip()


def latest_mtime(root: Path) -> float:
    latest = root.stat().st_mtime
    for path in root.rglob("*"):
        if "__pycache__" in path.parts or path.suffix == ".pyc":
            continue
        if path.is_file():
            latest = max(latest, path.stat().st_mtime)
    return latest


def zip_skill(skill_dir: Path, zip_path: Path) -> None:
    base = skill_dir.parent
    with zipfile.ZipFile(zip_path, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        for path in skill_dir.rglob("*"):
            if "__pycache__" in path.parts or path.suffix == ".pyc":
                continue
            if not path.is_file():
                continue
            archive.write(path, path.relative_to(base).as_posix())


def sync_agents_name(package_root: Path) -> list[str]:
    notes: list[str] = []
    instructions = package_root / "Instructions.md"
    agents = package_root / "AGENTS.md"
    lower_agents = package_root / "agents.md"

    if instructions.exists() and not agents.exists():
        instructions.rename(agents)
        notes.append("renamed Instructions.md -> AGENTS.md")
    elif instructions.exists() and agents.exists():
        notes.append("both Instructions.md and AGENTS.md exist; no overwrite")

    if lower_agents.exists() and lower_agents.name != "AGENTS.md":
        notes.append("agents.md exists; normalize to AGENTS.md manually if required")
    return notes


def candidate_skill_dirs(skills_root: Path) -> list[Path]:
    if not skills_root.exists():
        return []
    ignored = {"__pycache__", "_disabled-skills"}
    return sorted(
        path for path in skills_root.iterdir()
        if path.is_dir() and path.name not in ignored and not path.name.startswith(".")
    )


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo", type=Path, default=Path.cwd(), help="repository root; default is cwd")
    parser.add_argument("--package", type=Path, help="agent package root; default is <repo>/result")
    parser.add_argument("--all", action="store_true", help="rebuild all skill zips")
    parser.add_argument("--dry-run", action="store_true", help="print actions without writing zips or renaming files")
    args = parser.parse_args()

    repo = args.repo.resolve()
    package_root = (args.package or repo / "result").resolve()
    skills_root = package_root / "skills"

    print("== Git status ==")
    print(run_git(repo, ["status", "--short"]) or "clean")
    print()

    print("== Package ==")
    print(package_root)
    if not package_root.exists():
        print("package root not found", file=sys.stderr)
        return 2

    if args.dry_run:
        notes = ["dry-run: AGENTS.md sync skipped"]
    else:
        notes = sync_agents_name(package_root)
    for note in notes:
        print(f"- {note}")
    print()

    rebuilt: list[Path] = []
    skipped: list[Path] = []

    print("== Skills ==")
    for skill_dir in candidate_skill_dirs(skills_root):
        zip_path = skills_root / f"{skill_dir.name}.zip"
        needs_rebuild = args.all or not zip_path.exists()
        if zip_path.exists() and not needs_rebuild:
            needs_rebuild = latest_mtime(skill_dir) > zip_path.stat().st_mtime
        if needs_rebuild:
            print(f"rebuild {zip_path.name}")
            if not args.dry_run:
                zip_skill(skill_dir, zip_path)
            rebuilt.append(zip_path)
        else:
            print(f"current {zip_path.name}")
            skipped.append(zip_path)
    print()

    upload_files = []
    for name in ("AGENTS.md", "soul.md", "README.md"):
        path = package_root / name
        if path.exists():
            upload_files.append(path)
    upload_files.extend(sorted(skills_root.glob("*.zip")) if skills_root.exists() else [])

    print("== Upload checklist ==")
    for path in upload_files:
        print(f"- {path}")
    print()

    print("== Summary ==")
    print(f"rebuilt: {len(rebuilt)}")
    print(f"current: {len(skipped)}")
    print("git commit/push: not performed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
