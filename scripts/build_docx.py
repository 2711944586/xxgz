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


def build():
    if not PDF.exists():
        raise SystemExit(f"missing {PDF}; compile XeLaTeX first")

    doc = Document()
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

    for i, page in enumerate(pdf):
        pix = page.get_pixmap(matrix=matrix, alpha=False)
        img_path = tmp / f"page-{i + 1:03d}.png"
        pix.save(img_path)
        p = doc.add_paragraph()
        p.paragraph_format.space_before = Pt(0)
        p.paragraph_format.space_after = Pt(0)
        p.paragraph_format.line_spacing = 1.0
        run = p.add_run()
        set_run_font(run)
        run.add_picture(str(img_path), width=Mm(210), height=Mm(297))
        if i < pdf.page_count - 1:
            doc.add_page_break()

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
