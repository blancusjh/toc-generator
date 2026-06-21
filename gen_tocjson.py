"""Generate structured TOC data from rendered table-of-contents pages."""

import json
import os
from pathlib import Path


MODEL_ID = "gemini-2.5-flash"


def generate_toc_from_images(folder: str | Path = "aux", api_key: str | None = None) -> list[list]:
    """Send ``toc-*.png`` files in *folder* to Gemini and write ``toc.json``."""
    try:
        from google import genai
        from google.genai import types
    except ImportError as error:
        raise RuntimeError("Install dependencies with: pip install -r requirements.txt") from error

    folder = Path(folder)
    api_key = api_key or os.environ.get("GOOGLE_API_KEY")
    if not api_key:
        raise RuntimeError("Set the GOOGLE_API_KEY environment variable before running the pipeline.")

    image_paths = sorted(
        folder.glob("toc-*.png"), key=lambda path: int(path.stem.split("-")[1])
    )
    if not image_paths:
        raise FileNotFoundError(f"No TOC images matching {folder / 'toc-*.png'} were found.")

    contents = [
        """
Extract the table of contents from the following scanned pages.

Return only structured JSON: a list of lists. Each item must follow this format:
[hierarchy_level: int, title: str, page_number: int]

Skip front matter such as prefaces and notation. Do not skip sections or subsections.
Use hierarchy level 1 for chapters, 2 for sections, and 3 for subsections.
Respect the declared data types.
"""
    ]
    for image_path in image_paths:
        contents.append(types.Part.from_bytes(data=image_path.read_bytes(), mime_type="image/png"))

    client = genai.Client(api_key=api_key)
    response = client.models.generate_content(
        model=MODEL_ID,
        contents=contents,
        config={
            "thinking_config": {"thinking_budget": 128},
            "temperature": 0.4,
            "top_p": 0.95,
            "top_k": 20,
            "response_mime_type": "application/json",
            "response_schema": list[list],
        },
    )

    toc_path = folder / "toc.json"
    toc_path.write_text(json.dumps(response.parsed, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"TOC data written to: {toc_path}")
    return response.parsed
