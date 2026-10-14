# -*- coding: utf-8 -*-
"""Word that is a page-for-page image copy of the compiled PDF."""
from pathlib import Path

import fitz
from docx import Document
from docx.enum.section import WD_ORIENT
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Mm, Pt

ROOT = Path(__file__).resolve().parents[1]
BOOK = ROOT / "monograph"
PDF = BOOK / "ACTS-MCDT.pdf"
OUT = BOOK / "ACTS-MCDT.docx"
CN = BOOK / "基于信息感知的智能蒸烤一体机.docx"
SUBMIT = ROOT / "20241334庄颂信息2402.docx"


def set_run_font(run):
    run.font.name = "Times New Roman"
    run._element.rPr.rFonts.set(qn("w:eastAsia"), "宋体")


def suppress_header_distance(section):
    sect = section._sectPr
    for tag, val in (("w:headerDistance", "0"), ("w:footerDistance", "0")):
        node = sect.find(qn(tag))
        if node is None:
            node = OxmlElement(tag)
            sect.append(node)
        node.set(qn("w:w"), val)
    pg_mar = sect.find(qn("w:pgMar"))
    if pg_mar is None:
        pg_mar = OxmlElement("w:pgMar")
        sect.append(pg_mar)
    for attr in ("w:top", "w:right", "w:bottom", "w:left", "w:header", "w:footer", "w:gutter"):
        pg_mar.set(qn(attr), "0")
    doc_grid = sect.find(qn("w:docGrid"))
    if doc_grid is None:
        doc_grid = OxmlElement("w:docGrid")
        sect.append(doc_grid)
    doc_grid.set(qn("w:type"), "default")
    doc_grid.set(qn("w:linePitch"), "0")


def tight_paragraph(paragraph, page_break_before=False):
    paragraph.paragraph_format.space_before = Pt(0)
    paragraph.paragraph_format.space_after = Pt(0)
    paragraph.paragraph_format.line_spacing = 1.0
    paragraph.paragraph_format.page_break_before = page_break_before
    pPr = paragraph._p.get_or_add_pPr()
    spacing = pPr.find(qn("w:spacing"))
    if spacing is None:
        spacing = OxmlElement("w:spacing")
        pPr.append(spacing)
    spacing.set(qn("w:before"), "0")
    spacing.set(qn("w:after"), "0")
    spacing.set(qn("w:line"), "0")
    spacing.set(qn("w:lineRule"), "auto")
    for tag, val in (
        ("w:autoSpaceDE", "0"),
        ("w:autoSpaceDN", "0"),
        ("w:adjustRightInd", "0"),
        ("w:widowControl", "0"),
        ("w:kinsoku", "0"),
        ("w:overflowPunct", "0"),
        ("w:contextualSpacing", "1"),
    ):
        node = pPr.find(qn(tag))
        if node is None:
            node = OxmlElement(tag)
            pPr.append(node)
        node.set(qn("w:val"), val)


def build():
    if not PDF.exists():
        raise SystemExit(f"missing {PDF}; compile XeLaTeX first")

    doc = Document()
    normal = doc.styles["Normal"]
    normal.paragraph_format.space_before = Pt(0)
    normal.paragraph_format.space_after = Pt(0)
    normal.paragraph_format.line_spacing = 1.0
    normal.font.size = Pt(1)

    section = doc.sections[0]
    section.page_width = Mm(210)
    section.page_height = Mm(297)
    section.orientation = WD_ORIENT.PORTRAIT
    section.left_margin = Mm(0)
    section.right_margin = Mm(0)
    section.top_margin = Mm(0)
    section.bottom_margin = Mm(0)
    section.header_distance = Mm(0)
    section.footer_distance = Mm(0)
    suppress_header_distance(section)

    zoom = 2.0
    matrix = fitz.Matrix(zoom, zoom)
    pdf = fitz.open(PDF)
    tmp = BOOK / "_page_images"
    tmp.mkdir(exist_ok=True)

    # A full A4 bitmap plus the paragraph mark overflows one page and
    # a separate page-break paragraph then becomes a blank sheet.
    page_w = Mm(210)
    page_h = Mm(296.2)

    for i, page in enumerate(pdf):
        pix = page.get_pixmap(matrix=matrix, alpha=False)
        img_path = tmp / f"page-{i + 1:03d}.png"
        pix.save(img_path)
        p = doc.add_paragraph()
        tight_paragraph(p, page_break_before=(i > 0))
        run = p.add_run()
        set_run_font(run)
        run.font.size = Pt(1)
        run.add_picture(str(img_path), width=page_w, height=page_h)

    pdf.close()
    pdf_bytes = PDF.read_bytes()
    submit_pdf = ROOT / "20241334庄颂信息2402.pdf"
    named_pdf = BOOK / "基于信息感知的智能蒸烤一体机.pdf"
    root_cn_pdf = ROOT / "基于信息感知的智能蒸烤一体机.pdf"
    submit_pdf.write_bytes(pdf_bytes)
    named_pdf.write_bytes(pdf_bytes)
    root_cn_pdf.write_bytes(pdf_bytes)
    doc.save(OUT)
    doc.save(CN)
    doc.save(SUBMIT)
    doc.save(ROOT / "基于信息感知的智能蒸烤一体机.docx")
    print("wrote", OUT, "pages", i + 1)
    print("wrote", submit_pdf)
    print("wrote", named_pdf)


if __name__ == "__main__":
    build()
