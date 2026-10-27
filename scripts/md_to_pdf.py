"""Turn every markdown file in docs/ into a print-ready PDF.

The PDFs land next to the sources with the same basename:

    python scripts/md_to_pdf.py

Markdown is first laid out as HTML (the python-markdown package adds the
fenced code and tables that the docs use), then PyMuPDF's Story engine
typesets that HTML into real pages, reusing the Windows fonts so plain
text, bold and code all keep their face, including arrow and tick marks.

Taught concepts: pathlib paths, reading text files with an encoding, the
with-free DocumentWriter loop for paged output.
"""

import markdown
import pymupdf
from pathlib import Path

DOCS = Path(__file__).resolve().parent.parent / "docs"
FONTS = Path("C:/Windows/Fonts")

# Story reads @font-face files through an archive; Segoe UI carries the
# document text and Consolas the code blocks. Sizes are in pt (points),
# like a print stylesheet.
CSS = """
@font-face { font-family: segui; src: url(segoeui.ttf); }
@font-face { font-family: segui; src: url(segoeuib.ttf); font-weight: bold; }
@font-face { font-family: segui; src: url(segoeuii.ttf); font-style: italic; }
@font-face { font-family: segui; src: url(seguisb.ttf); font-weight: 600; }
@font-face { font-family: cons; src: url(consola.ttf); }
@font-face { font-family: cons; src: url(consolab.ttf); font-weight: bold; }
body { font-family: segui; font-size: 10.5pt; color: #20242a;
       line-height: 1.4; }
h1 { font-size: 19pt; color: #17293f; margin-top: 6pt; margin-bottom: 6pt; }
h2 { font-size: 13.5pt; color: #1f3d63; margin-top: 12pt; margin-bottom: 4pt; }
h3 { font-size: 11.5pt; color: #2b5486; margin-top: 10pt; margin-bottom: 3pt; }
p { margin-top: 3pt; margin-bottom: 3pt; }
li { margin-top: 2pt; margin-bottom: 2pt; }
pre { font-family: cons; font-size: 8.5pt; line-height: 1.3;
      background-color: #f4f6f9; color: #2b3a4a; padding: 6pt;
      margin-top: 4pt; margin-bottom: 6pt; }
code { font-family: cons; font-size: 9pt; color: #34495e; }
pre code { font-size: 8.5pt; color: #2b3a4a; }
table { font-size: 9.5pt; margin-top: 4pt; margin-bottom: 6pt; }
th { font-weight: 600; background-color: #eef1f5; padding: 2pt; }
td { padding: 2pt; }
blockquote { color: #4a5563; margin-top: 4pt; margin-bottom: 4pt;
             padding-left: 8pt; }
a { color: #215da8; }
hr { margin-top: 8pt; margin-bottom: 8pt; }
"""


def md_to_html(path):
    """One markdown file becomes one HTML body string."""
    text = path.read_text(encoding="utf-8")

    return markdown.markdown(
        text, extensions=["fenced_code", "tables", "sane_lists"],
        output_format="html5")


def write_pdf(html_body, target):
    """Typeset one HTML body into a paged PDF at target."""
    writer = pymupdf.DocumentWriter(str(target))
    story = pymupdf.Story(
        html=f"<html><body>{html_body}</body></html>",
        user_css=CSS, archive=pymupdf.Archive(str(FONTS)))

    page = pymupdf.paper_rect("a4")
    where = page + (44, 42, -44, -42)
    more = 1

    while more:
        device = writer.begin_page(page)
        more, _ = story.place(where)
        story.draw(device)
        writer.end_page()

    writer.close()


def main():
    sources = sorted(DOCS.rglob("*.md"))

    for path in sources:
        target = path.with_suffix(".pdf")
        write_pdf(md_to_html(path), target)

        with pymupdf.open(str(target)) as doc:
            pages, ok = doc.page_count, doc.is_pdf

        print(f"{'ok' if ok else 'BAD '} {pages:>3} pages  {target.name}")


if __name__ == "__main__":
    main()
