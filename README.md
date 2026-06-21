# TOC Generator

Generate and embed structured PDF bookmarks from scanned tables of contents using Gemini and PyMuPDF.

## Requirements

- Python 3.10+
- `pdftoppm` from Poppler (`brew install poppler` on macOS)
- A Gemini API key in the `GOOGLE_API_KEY` environment variable

Install the Python dependencies:

```bash
python -m pip install -r requirements.txt
export GOOGLE_API_KEY="your-api-key"
```

## Usage

Create a descriptor based on [`tocs/example.json`](tocs/example.json):

```json
{
  "toc_pages": [3, 6],
  "offset": 10,
  "file_path": "/absolute/path/to/book.pdf"
}
```

Then run:

```bash
python process_toc.py path/to/book.json
```

The pipeline renders the requested TOC pages into `aux/`, asks Gemini for structured bookmark data, and writes `TOC_<source name>.pdf` beside the source PDF. Use `--workdir` or `--output` to override those locations.

The source PDF is never modified.

## Descriptor fields

- `toc_pages`: inclusive `[first_page, last_page]` PDF page range containing the printed TOC.
- `offset`: number added to each printed page number before creating PDF bookmarks.
- `file_path`: absolute path to the source PDF. Keep personal paths in untracked descriptors.

## License

MIT. See [LICENSE](LICENSE).
