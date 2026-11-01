"""Typeset docs/PAPER.md as a self-contained HTML page and a PDF.

Equations are drawn by matplotlib so the build needs no LaTeX, and Chrome prints the PDF.
"""

import base64
import io
import os
import re
import subprocess
import tempfile
from pathlib import Path

import markdown
import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt

from metrocouncils.constants import REPO_ROOT

SOURCE = REPO_ROOT / "docs" / "PAPER.md"
OUTPUT_PDF = REPO_ROOT / "docs" / "PAPER.pdf"
CHROME_PATHS = (
    r"C:\Program Files\Google\Chrome\Application\chrome.exe",
    r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
    "/usr/bin/google-chrome",
)
SYMBOLS = {r"\lfloor": "\u230a", r"\rfloor": "\u230b", r"\log": "log"}

STYLE = """
@page {
  size: A4;
  margin: 24mm 24mm 22mm;
  @bottom-center { content: counter(page); font: 9pt Georgia, serif; color: #52514e; }
}
html { font-size: 10.5pt; }
body { font-family: Georgia, "Times New Roman", serif; line-height: 1.5; color: #111; margin: 0; }
h1 { font-size: 19pt; line-height: 1.22; font-weight: 700; margin: 0 0 10pt; text-align: center; }
h1 + p { text-align: center; font-size: 11.5pt; margin: 0 0 4pt; }
h1 + p + p { text-align: center; font-size: 9.5pt; color: #52514e; margin: 0 0 16pt; }
h1 + p + p strong { font-weight: 400; font-style: italic; }
h2 { font-size: 12.5pt; margin: 16pt 0 5pt; break-after: avoid; }
h3 { font-size: 11pt; margin: 12pt 0 4pt; break-after: avoid; }
p { margin: 0 0 7pt; text-align: justify; hyphens: auto; }
ul, ol { margin: 0 0 7pt; padding-left: 16pt; }
li { margin-bottom: 3pt; }
h2:nth-of-type(1) { text-align: center; font-size: 10.5pt; margin-top: 4pt; }
h2:nth-of-type(1) + p { font-size: 9.8pt; margin: 0 18pt 12pt; }
table {
  border-collapse: collapse; width: 100%; margin: 4pt 0 11pt; font-size: 9pt;
  font-family: Arial, sans-serif; break-inside: avoid; font-variant-numeric: tabular-nums;
}
th {
  text-align: left; padding: 3pt 6pt 3pt 0;
  border-top: 1.2pt solid #111; border-bottom: .7pt solid #111;
}
td { padding: 2.6pt 6pt 2.6pt 0; }
tr:last-child td { border-bottom: 1.2pt solid #111; }
img { display: block; width: 100%; margin: 7pt auto 2pt; }
p:has(> img) { break-after: avoid; margin: 0; }
p.caption { font-size: 9pt; text-align: left; color: #333; margin: 2pt 0 11pt; }
p.table-title { break-after: avoid; margin-bottom: 2pt; text-align: left; font-size: 9.5pt; }
img[alt="The 2021 backtest"] { width: 56%; }
.equation { text-align: center; margin: 7pt 0 9pt; break-inside: avoid; }
.equation img { display: inline-block; width: auto; margin: 0; }
sub, sup { font-size: 72%; line-height: 0; }
a { color: inherit; }
"""


def display_equation(tex: str) -> str:
    """Draw a display equation and return it as an inline PNG tag."""
    figure = plt.figure()
    text = figure.text(0, 0, f"${tex}$", fontsize=13, math_fontfamily="cm")
    figure.canvas.draw()
    box = text.get_window_extent()
    inches = (box.width / figure.dpi, box.height / figure.dpi)
    buffer = io.BytesIO()
    figure.savefig(buffer, format="png", dpi=300, bbox_inches="tight", pad_inches=0.02)
    plt.close(figure)
    encoded = base64.b64encode(buffer.getvalue()).decode("ascii")
    width = inches[0] * 0.92
    return (
        f'<div class="equation"><img style="width:{width:.2f}in" alt="Equation" '
        f'src="data:image/png;base64,{encoded}"></div>'
    )


def inline_math(tex: str) -> str:
    """Write simple inline mathematics as HTML: italic letters, subscripts and superscripts."""
    for command, symbol in SYMBOLS.items():
        tex = tex.replace(command, symbol)
    tex = re.sub(r"_(\w)", r"<sub>\1</sub>", tex)
    tex = re.sub(r"\^(\w)", r"<sup>\1</sup>", tex)
    parts = re.split(r"(<[^>]+>|log|[\d.]+)", tex)
    styled = [
        part if part.startswith("<") or part == "log" else re.sub(r"([A-Za-z])", r"<i>\1</i>", part)
        for part in parts
    ]
    return "".join(styled)


def embed_images(html: str) -> str:
    """Replace image paths with inline data, so the page stands alone."""

    def embed(match: re.Match) -> str:
        path = (SOURCE.parent / match.group(1)).resolve()
        encoded = base64.b64encode(path.read_bytes()).decode("ascii")
        return f'src="data:image/png;base64,{encoded}"'

    return re.sub(r'src="(\.\./[^"]+\.png)"', embed, html)


def to_html(text: str) -> str:
    """Turn the paper's Markdown into a complete HTML document."""
    placeholders = {}

    def hold(html: str) -> str:
        key = f"XMATHX{len(placeholders)}X"
        placeholders[key] = html
        return key

    text = re.sub(
        r"\$\$(.+?)\$\$",
        lambda m: "\n\n" + hold(display_equation(" ".join(m.group(1).split()))) + "\n\n",
        text,
        flags=re.S,
    )
    text = re.sub(r"\$([^$\n]+)\$", lambda m: hold(inline_math(m.group(1))), text)
    body = markdown.markdown(text, extensions=["tables", "sane_lists"])
    body = body.replace("<p><em>Figure", '<p class="caption"><em>Figure')
    body = body.replace("<p><strong>Table", '<p class="table-title"><strong>Table')
    for key, html in placeholders.items():
        body = body.replace(f"<p>{key}</p>", html).replace(key, html)
    title = re.search(r"^# (.+)$", text, flags=re.M).group(1)
    return (
        '<!doctype html><html lang="en"><head><meta charset="utf-8">'
        f"<title>{title}</title><style>{STYLE}</style></head><body>"
        f"{embed_images(body)}</body></html>"
    )


def find_chrome() -> str:
    for path in CHROME_PATHS:
        if Path(path).exists():
            return path
    raise FileNotFoundError("Chrome was not found, and it is needed to print the PDF")


def print_pdf(html: str, output: Path) -> None:
    with tempfile.TemporaryDirectory() as folder:
        page = Path(folder) / "paper.html"
        page.write_text(html, encoding="utf-8")
        subprocess.run(
            [
                find_chrome(),
                "--headless=new",
                "--disable-gpu",
                f"--user-data-dir={os.path.join(folder, 'profile')}",
                "--no-pdf-header-footer",
                f"--print-to-pdf={output}",
                page.as_uri(),
            ],
            check=True,
            capture_output=True,
            timeout=120,
        )


def run() -> None:
    print_pdf(to_html(SOURCE.read_text(encoding="utf-8")), OUTPUT_PDF)


if __name__ == "__main__":
    run()
