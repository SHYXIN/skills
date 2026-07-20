#!/usr/bin/env python3
"""Convert a PDF to text and split it into chapter files.

The script intentionally depends on the external `pdftotext` command because it
is reliable for layout-preserving extraction and was the proven route for this
workflow. It has no Python package dependencies.
"""

from __future__ import annotations

import argparse
import re
import shutil
import subprocess
import sys
from pathlib import Path


SPECIAL_TITLES = ["Preamble", "About the Author", "Conclusion", "Annexes"]
SPECIAL_FILENAMES = {
    "Preamble": "00-Preamble.txt",
    "About the Author": "00-About-the-Author.txt",
    "Conclusion": "98-Conclusion.txt",
    "Annexes": "99-Annexes.txt",
}


def slugify(value: str, fallback: str) -> str:
    value = re.sub(r"[^\w\s.-]+", "", value, flags=re.UNICODE)
    value = re.sub(r"\s+", "-", value.strip())
    value = value.strip(".-")
    return value or fallback


def find_pdftotext(explicit: str | None) -> str:
    if explicit:
        path = shutil.which(explicit) or explicit
        if Path(path).exists() or shutil.which(path):
            return path
        raise SystemExit(f"pdftotext not found: {explicit}")

    found = shutil.which("pdftotext")
    if found:
        return found

    common_windows_path = Path(r"C:\Program Files\Git\mingw64\bin\pdftotext.exe")
    if common_windows_path.exists():
        return str(common_windows_path)

    raise SystemExit(
        "pdftotext was not found. Install Poppler, or use Git for Windows' "
        "pdftotext.exe, then retry with --pdftotext <path>."
    )


def convert_pdf(pdftotext: str, pdf: Path, full_txt: Path) -> None:
    full_txt.parent.mkdir(parents=True, exist_ok=True)
    cmd = [pdftotext, "-layout", str(pdf), str(full_txt)]
    subprocess.run(cmd, check=True)


def next_nonblank(lines: list[str], start: int) -> int | None:
    idx = start
    while idx < len(lines):
        if lines[idx].strip():
            return idx
        idx += 1
    return None


def looks_like_title(line: str) -> bool:
    stripped = line.strip()
    if len(stripped) < 3:
        return False
    if re.search(r"[A-Za-z]", stripped) is None:
        return False
    if len(stripped.split()) > 12:
        return False
    return True


def discover_sections(lines: list[str], include_special: bool) -> list[tuple[str, int]]:
    starts: list[tuple[str, int]] = []

    if include_special:
        for title in SPECIAL_TITLES:
            for idx, line in enumerate(lines):
                if line.strip() == title:
                    starts.append((title, idx))
                    break

    for idx, line in enumerate(lines):
        stripped = line.strip()
        if not re.fullmatch(r"\d{1,2}", stripped):
            continue

        title_idx = next_nonblank(lines, idx + 1)
        if title_idx is None:
            continue

        title = lines[title_idx].strip()
        if looks_like_title(title):
            starts.append((f"{stripped} {title}", idx))

    starts.sort(key=lambda item: item[1])

    deduped: list[tuple[str, int]] = []
    seen_positions: set[int] = set()
    for title, idx in starts:
        if idx in seen_positions:
            continue
        seen_positions.add(idx)
        deduped.append((title, idx))
    return deduped


def write_sections(lines: list[str], sections: list[tuple[str, int]], out_dir: Path) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)
    notes_dir = out_dir / "notes"
    notes_dir.mkdir(exist_ok=True)

    manifest: list[str] = []
    width = max(2, len(str(len(sections))))

    for section_index, (title, start) in enumerate(sections):
        end = sections[section_index + 1][1] if section_index + 1 < len(sections) else len(lines)
        prefix = f"{section_index:0{width}d}"
        if title in SPECIAL_FILENAMES:
            filename = SPECIAL_FILENAMES[title]
        elif re.match(r"^\d+\s+", title):
            chapter_num, chapter_title = title.split(" ", 1)
            prefix = chapter_num.zfill(2)
            filename = f"{prefix}-{slugify(chapter_title, 'chapter')}.txt"
        else:
            filename = f"{prefix}-{slugify(title, 'section')}.txt"

        content = "\n".join(lines[start:end]).rstrip() + "\n"
        target = out_dir / filename
        target.write_text(content, encoding="utf-8")
        manifest.append(f"{filename}\tlines {start + 1}-{end}\t{title}")

    (out_dir / "MANIFEST.txt").write_text("\n".join(manifest) + "\n", encoding="utf-8")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Convert a PDF to text and split it by chapter headings.")
    parser.add_argument("pdf", type=Path, help="Path to the source PDF.")
    parser.add_argument("--out-dir", type=Path, help="Output directory. Defaults to a sibling folder named after the PDF.")
    parser.add_argument("--pdftotext", help="Path or command name for pdftotext.")
    parser.add_argument("--no-special", action="store_true", help="Do not include Preamble/About/Conclusion/Annexes sections.")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    pdf = args.pdf.resolve()
    if not pdf.exists():
        print(f"PDF not found: {pdf}", file=sys.stderr)
        return 2

    out_dir = args.out_dir.resolve() if args.out_dir else pdf.with_suffix("")
    full_txt = out_dir / "full.txt"

    pdftotext = find_pdftotext(args.pdftotext)
    convert_pdf(pdftotext, pdf, full_txt)

    lines = full_txt.read_text(encoding="utf-8", errors="replace").splitlines()
    sections = discover_sections(lines, include_special=not args.no_special)

    if len([title for title, _ in sections if re.match(r"^\d+\s+", title)]) < 2:
        print(f"Converted PDF to {full_txt}")
        print("Could not confidently discover multiple chapters. Keep full.txt and ask the user for chapter boundaries.")
        return 1

    write_sections(lines, sections, out_dir)
    print(f"Output directory: {out_dir}")
    print(f"Full text: {full_txt}")
    print(f"Manifest: {out_dir / 'MANIFEST.txt'}")
    print(f"Sections: {len(sections)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
