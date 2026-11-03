"""Build the Word version of the paper from docs/PAPER.md.

Headings use Word's built-in styles, tables are real tables and equations are editable Word
equations.
"""

import re
from datetime import UTC, datetime
from pathlib import Path

from docx import Document
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml import OxmlElement, parse_xml
from docx.oxml.ns import qn
from docx.shared import Cm, Pt, RGBColor

from metrocouncils.constants import REPO_ROOT

SOURCE = REPO_ROOT / "docs" / "PAPER.md"
OUTPUT = REPO_ROOT / "docs" / "PAPER.docx"
AUTHOR = "Lunga Ngaka"
BODY_FONT = "Georgia"
TABLE_FONT = "Arial"
TEXT_WIDTH_CM = 16.0
FIGURE_WIDTHS_CM = {"figure_4_backtest": 9.5}
INK = RGBColor(0x11, 0x11, 0x11)
MUTED = RGBColor(0x52, 0x51, 0x4E)

MATH_NS = "http://schemas.openxmlformats.org/officeDocument/2006/math"
WORD_NS = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"
MATH_FONT = '<w:rPr><w:rFonts w:ascii="Cambria Math" w:hAnsi="Cambria Math"/></w:rPr>'


def run(text: str) -> str:
    return f'<m:r>{MATH_FONT}<m:t xml:space="preserve">{text}</m:t></m:r>'


def word(text: str) -> str:
    """Set upright text, used for names in an equation."""
    return f'<m:r><m:rPr><m:sty m:val="p"/></m:rPr>{MATH_FONT}<m:t>{text}</m:t></m:r>'


def frac(top: str, bottom: str) -> str:
    return f"<m:f><m:num>{top}</m:num><m:den>{bottom}</m:den></m:f>"


def sub(base: str, script: str) -> str:
    return f"<m:sSub><m:e>{run(base)}</m:e><m:sub>{run(script)}</m:sub></m:sSub>"


def sup(base: str, script: str) -> str:
    return f"<m:sSup><m:e>{run(base)}</m:e><m:sup>{run(script)}</m:sup></m:sSup>"


def subsup(base: str, lower: str, upper: str) -> str:
    return (
        f"<m:sSubSup><m:e>{run(base)}</m:e><m:sub>{run(lower)}</m:sub>"
        f"<m:sup>{run(upper)}</m:sup></m:sSubSup>"
    )


def floor(content: str) -> str:
    return (
        f'<m:d><m:dPr><m:begChr m:val="⌊"/><m:endChr m:val="⌋"/></m:dPr><m:e>{content}</m:e></m:d>'
    )


# The paper's display equations, in order of appearance.
EQUATIONS = (
    run("Q = ") + floor(frac(run("A"), run("B − C − D"))) + run(" + 1."),
    sub("f", "j") + run(" = w ") + sub("y", "j") + run(" + (1 − w) ") + sub("z", "j") + run("."),
    subsup("b", "j", "2")
    + run(" = ")
    + frac(subsup("s", "j", "2"), sub("k", "j"))
    + run(" + ")
    + sup("c", "2")
    + run(","),
    word("precision")
    + run(" = ")
    + frac(run("1"), subsup("a", "j", "2"))
    + run(" + ")
    + frac(run("1"), subsup("b", "j", "2"))
    + run(",        ")
    + word("mean")
    + run(" = ")
    + frac(
        sub("m", "j")
        + run(" / ")
        + subsup("a", "j", "2")
        + run(" + ")
        + sub("p", "j")
        + run(" / ")
        + subsup("b", "j", "2"),
        run("1 / ") + subsup("a", "j", "2") + run(" + 1 / ") + subsup("b", "j", "2"),
    )
    + run("."),
)


def add_equation(document: Document, xml: str) -> None:
    paragraph = document.add_paragraph()
    namespaces = f'xmlns:m="{MATH_NS}" xmlns:w="{WORD_NS}"'
    element = parse_xml(f"<m:oMathPara {namespaces}><m:oMath>{xml}</m:oMath></m:oMathPara>")
    paragraph._p.append(element)
    paragraph.paragraph_format.space_before = Pt(4)
    paragraph.paragraph_format.space_after = Pt(8)


def add_math_text(paragraph, tex: str) -> None:
    """Write inline mathematics as italic letters with real subscripts and superscripts."""
    tex = tex.replace(r"\lfloor", "⌊").replace(r"\rfloor", "⌋").replace(r"\log", "log")
    for part in re.split(r"(_\w|\^\w)", tex):
        if not part:
            continue
        script = part[0] in "_^" and len(part) == 2
        text = part[1] if script else part
        for piece in re.split(r"(log|[\d.]+)", text):
            if not piece:
                continue
            item = paragraph.add_run(piece)
            item.italic = piece != "log" and not re.fullmatch(r"[\d.]+", piece)
            if script:
                item.font.subscript = part[0] == "_"
                item.font.superscript = part[0] == "^"


def add_inline(paragraph, text: str, bold: bool = False, italic: bool = False) -> None:
    """Add text holding the paper's inline Markdown: bold, italic, maths and links."""
    pattern = r"(\*\*.+?\*\*|\*[^*]+?\*|\$[^$]+\$|<https?://[^>]+>)"
    for part in re.split(pattern, text):
        if not part:
            continue
        if part.startswith("**"):
            add_inline(paragraph, part[2:-2], bold=True, italic=italic)
        elif part.startswith("*"):
            add_inline(paragraph, part[1:-1], bold=bold, italic=True)
        elif part.startswith("$"):
            add_math_text(paragraph, part[1:-1])
        elif part.startswith("<"):
            paragraph.add_run(part[1:-1])
        else:
            item = paragraph.add_run(part)
            item.bold = bold or None
            item.italic = italic or None


def set_font(style, name: str, size: float, colour=INK) -> None:
    style.font.name = name
    style.font.size = Pt(size)
    style.font.color.rgb = colour
    fonts = style.element.get_or_add_rPr().get_or_add_rFonts()
    for key in ("w:ascii", "w:hAnsi", "w:cs", "w:eastAsia"):
        fonts.set(qn(key), name)
    for key in ("w:asciiTheme", "w:hAnsiTheme", "w:cstheme", "w:eastAsiaTheme"):
        if fonts.get(qn(key)) is not None:
            del fonts.attrib[qn(key)]


def set_up_styles(document: Document) -> None:
    section = document.sections[0]
    section.page_width, section.page_height = Cm(21.0), Cm(29.7)
    section.left_margin = section.right_margin = Cm(2.5)
    section.top_margin, section.bottom_margin = Cm(2.4), Cm(2.2)

    normal = document.styles["Normal"]
    set_font(normal, BODY_FONT, 10.5)
    normal.paragraph_format.space_after = Pt(7)
    normal.paragraph_format.line_spacing = 1.2

    for name, size, before, after in (
        ("Title", 19, 0, 8),
        ("Heading 1", 13, 14, 4),
        ("Heading 2", 11.5, 10, 3),
    ):
        style = document.styles[name]
        set_font(style, BODY_FONT, size)
        style.font.bold = True
        style.font.italic = False
        style.paragraph_format.space_before = Pt(before)
        style.paragraph_format.space_after = Pt(after)
        style.paragraph_format.keep_with_next = True
    title = document.styles["Title"]
    title.paragraph_format.alignment = WD_ALIGN_PARAGRAPH.CENTER
    border = title.element.pPr.find(qn("w:pBdr"))
    if border is not None:
        title.element.pPr.remove(border)
    for name in ("List Bullet", "List Number"):
        document.styles[name].paragraph_format.space_after = Pt(3)


def set_cell_border(cell, **edges) -> None:
    properties = cell._tc.get_or_add_tcPr()
    borders = OxmlElement("w:tcBorders")
    for edge, size in edges.items():
        element = OxmlElement(f"w:{edge}")
        element.set(qn("w:val"), "single")
        element.set(qn("w:sz"), str(size))
        element.set(qn("w:color"), "111111")
        borders.append(element)
    properties.append(borders)


def add_table(document: Document, rows: list[list[str]]) -> None:
    table = document.add_table(rows=len(rows), cols=len(rows[0]))
    table.alignment = WD_TABLE_ALIGNMENT.CENTER
    table.autofit = False
    first_share = 0.3 if len(rows[0]) > 3 else 0.6
    first = Cm(TEXT_WIDTH_CM * first_share)
    others = Cm(TEXT_WIDTH_CM * (1 - first_share) / (len(rows[0]) - 1))
    for row_index, row in enumerate(rows):
        table.rows[row_index]._tr.get_or_add_trPr().append(OxmlElement("w:cantSplit"))
        for column, text in enumerate(row):
            cell = table.cell(row_index, column)
            cell.width = first if column == 0 else others
            paragraph = cell.paragraphs[0]
            paragraph.paragraph_format.space_after = Pt(1)
            paragraph.paragraph_format.space_before = Pt(1)
            paragraph.paragraph_format.line_spacing = 1.0
            paragraph.paragraph_format.keep_with_next = row_index < len(rows) - 1
            item = paragraph.add_run(text)
            item.font.name = TABLE_FONT
            item.font.size = Pt(9)
            item.bold = row_index == 0 or None
            if row_index == 0:
                set_cell_border(cell, top=10, bottom=6)
            elif row_index == len(rows) - 1:
                set_cell_border(cell, bottom=10)
    spacer = document.add_paragraph()
    spacer.paragraph_format.space_after = Pt(4)


def add_page_number(document: Document) -> None:
    paragraph = document.sections[0].footer.paragraphs[0]
    paragraph.alignment = WD_ALIGN_PARAGRAPH.CENTER
    item = paragraph.add_run()
    item.font.size = Pt(9)
    item.font.color.rgb = MUTED
    for kind, text in (("begin", None), (None, "PAGE"), ("end", None)):
        if kind:
            element = OxmlElement("w:fldChar")
            element.set(qn("w:fldCharType"), kind)
        else:
            element = OxmlElement("w:instrText")
            element.text = text
        item._r.append(element)


def add_figure(document: Document, relative_path: str) -> None:
    path = (SOURCE.parent / relative_path).resolve()
    paragraph = document.add_paragraph()
    paragraph.alignment = WD_ALIGN_PARAGRAPH.CENTER
    paragraph.paragraph_format.keep_with_next = True
    paragraph.paragraph_format.space_after = Pt(2)
    width = FIGURE_WIDTHS_CM.get(path.stem, TEXT_WIDTH_CM)
    paragraph.add_run().add_picture(str(path), width=Cm(width))


def split_blocks(text: str) -> list[str]:
    """Split the source into blocks, keeping display equations whole."""
    return [block.strip() for block in re.split(r"\n\s*\n", text) if block.strip()]


def build(source: Path = SOURCE, output: Path = OUTPUT) -> None:
    document = Document()
    set_up_styles(document)
    add_page_number(document)
    equations = iter(EQUATIONS)
    blocks = split_blocks(source.read_text(encoding="utf-8"))
    for position, block in enumerate(blocks):
        block_text = " ".join(line.strip() for line in block.splitlines())
        if block.startswith("# "):
            document.add_paragraph(block[2:], style="Title")
            document.core_properties.title = block[2:]
        elif block.startswith("## "):
            heading = document.add_heading(block[3:], level=1)
            if block[3:] == "Abstract":
                heading.alignment = WD_ALIGN_PARAGRAPH.CENTER
        elif block.startswith("### "):
            document.add_heading(block[4:], level=2)
        elif block.startswith("$$"):
            add_equation(document, next(equations))
        elif block.startswith("!["):
            add_figure(document, re.search(r"\(([^)]+)\)", block).group(1))
        elif block.startswith("|"):
            rows = [
                [cell.strip() for cell in line.strip().strip("|").split("|")]
                for line in block.splitlines()
                if not re.fullmatch(r"\|[\s\-|]+\|", line.strip())
            ]
            add_table(document, rows)
        elif re.match(r"(- |\d+\. )", block):
            items = re.split(r"\n(?=- |\d+\. )", block)
            for item in items:
                numbered = bool(re.match(r"\d+\. ", item))
                text = re.sub(r"^(- |\d+\. )", "", " ".join(item.split()))
                style = "List Number" if numbered else "List Bullet"
                add_inline(document.add_paragraph(style=style), text)
        else:
            paragraph = document.add_paragraph()
            add_inline(paragraph, block_text)
            is_caption = block_text.startswith("*Figure")
            is_table_title = block_text.startswith("**Table")
            if position == 1:
                paragraph.alignment = WD_ALIGN_PARAGRAPH.CENTER
            elif position == 2:
                paragraph.alignment = WD_ALIGN_PARAGRAPH.CENTER
                for item in paragraph.runs:
                    item.bold = None
                    item.italic = True
                    item.font.size = Pt(9.5)
                    item.font.color.rgb = MUTED
            elif is_caption:
                for item in paragraph.runs:
                    item.font.size = Pt(9)
            elif is_table_title:
                paragraph.paragraph_format.keep_with_next = True
                paragraph.paragraph_format.space_after = Pt(3)
                for item in paragraph.runs:
                    item.font.size = Pt(9.5)
            else:
                paragraph.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
    if next(equations, None) is not None:
        raise ValueError("The paper has fewer display equations than EQUATIONS")
    properties = document.core_properties
    properties.author = AUTHOR
    properties.last_modified_by = AUTHOR
    properties.comments = ""
    properties.created = properties.modified = datetime.now(UTC).replace(tzinfo=None)
    set_compatibility_mode(document)
    document.save(output)


def set_compatibility_mode(document, mode: int = 15) -> None:
    """Mark the file as current Word format so it does not open in Compatibility Mode."""
    settings = document.settings.element
    compat = settings.find(qn("w:compat"))
    if compat is None:
        compat = OxmlElement("w:compat")
        settings.append(compat)
    for setting in compat.findall(qn("w:compatSetting")):
        if setting.get(qn("w:name")) == "compatibilityMode":
            compat.remove(setting)
    setting = OxmlElement("w:compatSetting")
    setting.set(qn("w:name"), "compatibilityMode")
    setting.set(qn("w:uri"), "http://schemas.microsoft.com/office/word")
    setting.set(qn("w:val"), str(mode))
    compat.append(setting)


if __name__ == "__main__":
    build()
