"""Extract, generate, and embed a PDF table of contents."""

import argparse
import json
import os
import subprocess
from pathlib import Path

from gen_tocjson import generate_toc_from_images


def read_descriptor(path: str | Path) -> dict:
    """Load and minimally validate a TOC descriptor."""
    descriptor_path = Path(path)
    with descriptor_path.open(encoding="utf-8") as file:
        data = json.load(file)

    required = {"toc_pages", "offset", "file_path"}
    missing = required - data.keys()
    if missing:
        raise ValueError(f"Descriptor is missing required fields: {', '.join(sorted(missing))}")
    if len(data["toc_pages"]) != 2:
        raise ValueError("toc_pages must contain exactly [first_page, last_page].")
    return data


def extract_toc_images(toc_pages: list[int], file_path: str | Path, output_prefix: str | Path) -> None:
    """Render the requested PDF pages as PNG files using pdftoppm."""
    first, last = toc_pages
    if first < 1 or last < first:
        raise ValueError("toc_pages must be positive and ordered as [first_page, last_page].")

    output_prefix = Path(output_prefix)
    output_prefix.parent.mkdir(parents=True, exist_ok=True)
    command = [
        "pdftoppm", "-f", str(first), "-l", str(last), str(file_path), str(output_prefix), "-png"
    ]
    subprocess.run(command, check=True)


def apply_toc(json_data: dict, output_path: str | Path | None = None) -> Path:
    """Embed generated TOC data in the source PDF and return the saved path."""
    try:
        import fitz
    except ImportError as error:
        raise RuntimeError("Install dependencies with: pip install -r requirements.txt") from error

    file_path = Path(os.path.expanduser(json_data["file_path"]))
    if not file_path.is_file():
        raise FileNotFoundError(f"PDF not found: {file_path}")

    output_path = Path(output_path) if output_path else file_path.with_name(f"TOC_{file_path.name}")
    if output_path.resolve() == file_path.resolve():
        raise ValueError("The output path must differ from the source PDF.")

    doc = fitz.open(file_path)
    try:
        toc = [[1, "Content", json_data["toc_pages"][0]]]
        for level, title, page in json_data["toc"]:
            adjusted_page = page + json_data["offset"]
            if 1 <= adjusted_page <= doc.page_count:
                toc.append([level, title, adjusted_page])
            else:
                print(f"Skipping out-of-range entry: {title!r} -> page {adjusted_page}")
        doc.set_toc(toc)
        doc.save(output_path)
    finally:
        doc.close()

    print(f"TOC PDF written to: {output_path}")
    return output_path


def run_pipeline(descriptor_path: str | Path, workdir: str | Path = "aux", output_path: str | Path | None = None) -> Path:
    data = read_descriptor(descriptor_path)
    file_path = Path(os.path.expanduser(data["file_path"]))
    workdir = Path(workdir)
    extract_toc_images(data["toc_pages"], file_path, workdir / "toc")
    data["toc"] = generate_toc_from_images(workdir)
    return apply_toc(data, output_path)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("descriptor", type=Path, help="Path to a TOC descriptor JSON file.")
    parser.add_argument("--workdir", type=Path, default=Path("aux"), help="Directory for generated images and JSON.")
    parser.add_argument("--output", type=Path, help="Output PDF path (default: TOC_<source name>.pdf).")
    return parser.parse_args()


if __name__ == "__main__":
    arguments = parse_args()
    run_pipeline(arguments.descriptor, arguments.workdir, arguments.output)
