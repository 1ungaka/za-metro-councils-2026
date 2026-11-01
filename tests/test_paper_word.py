from docx import Document

from metrocouncils import paper_word
from metrocouncils.paper_word import MATH_NS


def test_word_paper_keeps_its_structure(tmp_path):
    output = tmp_path / "paper.docx"
    paper_word.build(output=output)
    document = Document(output)
    equations = document.element.body.findall(f".//{{{MATH_NS}}}oMathPara")
    headings = [p.text for p in document.paragraphs if p.style.name == "Heading 1"]
    assert len(equations) == len(paper_word.EQUATIONS)
    assert len(document.inline_shapes) == 4
    assert len(document.tables) == 5
    assert "6. Forecast" in headings
    assert document.core_properties.author == "Lunga Ngaka"


def test_no_markdown_is_left_in_the_text(tmp_path):
    output = tmp_path / "paper.docx"
    paper_word.build(output=output)
    text = "\n".join(p.text for p in Document(output).paragraphs)
    assert "**" not in text
    assert "$" not in text
    assert "![" not in text
