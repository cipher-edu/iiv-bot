"""Markdown -> styled HTML -> PDF.

Uses Python markdown for HTML rendering and WeasyPrint for the final PDF.
Designed for formal Uzbek-language documentation (tables, signatures, page numbers).
"""
import sys
from pathlib import Path

import markdown
from weasyprint import HTML, CSS

CSS_TEMPLATE = """
@page {
    size: A4;
    margin: 2.5cm 2cm 2cm 3cm;
    @bottom-center {
        content: counter(page) " / " counter(pages);
        font-size: 9pt;
        color: #555;
    }
}

body {
    font-family: 'DejaVu Serif', 'Liberation Serif', 'Times New Roman', serif;
    font-size: 11pt;
    line-height: 1.45;
    color: #111;
    text-align: justify;
}

h1 {
    font-size: 16pt;
    font-weight: bold;
    text-align: center;
    margin: 0 0 0.6em 0;
    page-break-after: avoid;
}

h2 {
    font-size: 13pt;
    font-weight: bold;
    margin: 1.2em 0 0.4em 0;
    border-bottom: 1px solid #ccc;
    padding-bottom: 2pt;
    page-break-after: avoid;
}

h3 {
    font-size: 12pt;
    font-weight: bold;
    margin: 1em 0 0.3em 0;
    page-break-after: avoid;
}

h4 {
    font-size: 11pt;
    font-weight: bold;
    margin: 0.8em 0 0.3em 0;
    page-break-after: avoid;
}

p { margin: 0 0 0.5em 0; }

table {
    border-collapse: collapse;
    width: 100%;
    margin: 0.5em 0 1em 0;
    font-size: 10pt;
    page-break-inside: avoid;
}

th, td {
    border: 1px solid #888;
    padding: 4pt 6pt;
    vertical-align: top;
    text-align: left;
}

th {
    background: #eee;
    font-weight: bold;
}

ul, ol { margin: 0.3em 0 0.6em 1.2em; padding: 0; }
li { margin: 0.2em 0; }

code {
    font-family: 'DejaVu Sans Mono', monospace;
    background: #f4f4f4;
    padding: 1pt 3pt;
    font-size: 10pt;
}

pre {
    background: #f4f4f4;
    padding: 6pt;
    overflow: auto;
    font-size: 9pt;
}

hr {
    border: none;
    border-top: 1px solid #aaa;
    margin: 1em 0;
}

strong { font-weight: bold; }
em { font-style: italic; }

/* Signature blocks: keep underline-and-text together */
p:has(> strong:only-child) { page-break-after: avoid; }
"""


def convert(md_path: Path, pdf_path: Path) -> None:
    text = md_path.read_text(encoding="utf-8")

    html_body = markdown.markdown(
        text,
        extensions=["tables", "fenced_code", "sane_lists", "toc"],
    )

    html = f"""<!DOCTYPE html>
<html lang="uz">
<head>
<meta charset="utf-8">
<title>{md_path.stem}</title>
</head>
<body>
{html_body}
</body>
</html>"""

    HTML(string=html, base_url=str(md_path.parent)).write_pdf(
        str(pdf_path), stylesheets=[CSS(string=CSS_TEMPLATE)]
    )
    print(f"  ✓ {md_path.name} -> {pdf_path.name}")


def main() -> int:
    if len(sys.argv) < 2:
        print("Foydalanish: md_to_pdf.py <fayl1.md> [fayl2.md ...]")
        return 1

    for src in sys.argv[1:]:
        src_path = Path(src)
        if not src_path.exists():
            print(f"  ! Fayl topilmadi: {src}")
            continue
        pdf_path = src_path.with_suffix(".pdf")
        try:
            convert(src_path, pdf_path)
        except Exception as e:
            print(f"  ! {src_path.name} ERROR: {e}")
            return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
