# -*- coding: utf-8 -*-
"""Export Word as a page-for-page copy of the PDF using header floating backgrounds."""
from __future__ import annotations

import shutil
from pathlib import Path

import fitz
from docx import Document
from docx.enum.section import WD_ORIENT, WD_SECTION
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Mm, Pt, Twips
from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
BOOK = ROOT / "monograph"
PDF = BOOK / "ACTS-MCDT.pdf"
SUBMIT_DIR = ROOT / "submit"
SUBMIT_PDF = SUBMIT_DIR / "20241334庄颂信息2402.pdf"
SUBMIT_DOCX = SUBMIT_DIR / "20241334庄颂信息2402.docx"
LOCAL_DOCX = BOOK / "ACTS-MCDT.docx"

A4_W = Mm(210)
A4_H = Mm(297)
DPI = 250
JPEG_QUALITY = 85


def disable_auto_compress(doc: Document) -> None:
    settings = doc.settings.element
    for tag in ("w:doNotAutoCompressPictures", "w:displayBackgroundShape"):
        if settings.find(qn(tag)) is None:
            node = OxmlElement(tag)
            settings.append(node)


def configure_section(section) -> None:
    section.page_width = A4_W
    section.page_height = A4_H
    section.orientation = WD_ORIENT.PORTRAIT
    section.left_margin = Mm(0)
    section.right_margin = Mm(0)
    section.top_margin = Mm(0)
    section.bottom_margin = Mm(0)
    section.header_distance = Mm(0)
    section.footer_distance = Mm(0)
    sect = section._sectPr
    sect.set(qn("w:rsidR"), "00000000")
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
    pg_sz = sect.find(qn("w:pgSz"))
    if pg_sz is None:
        pg_sz = OxmlElement("w:pgSz")
        sect.append(pg_sz)
    pg_sz.set(qn("w:w"), str(int(Twips(A4_W.twips) if hasattr(A4_W, "twips") else 11906)))
    pg_sz.set(qn("w:w"), "11906")
    pg_sz.set(qn("w:h"), "16838")
    start = sect.find(qn("w:type"))
    if start is None:
        start = OxmlElement("w:type")
        sect.append(start)
    start.set(qn("w:val"), "nextPage")


def tight_paragraph(paragraph) -> None:
    paragraph.paragraph_format.space_before = Pt(0)
    paragraph.paragraph_format.space_after = Pt(0)
    paragraph.paragraph_format.line_spacing = 1.0
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


def _inline_to_anchor(drawing, doc_pr_id: int, name: str) -> None:
    inline = drawing.find(qn("wp:inline"))
    if inline is None:
        return
    extent = inline.find(qn("wp:extent"))
    cx = extent.get("cx")
    cy = extent.get("cy")
    docPr = inline.find(qn("wp:docPr"))
    cNv = inline.find(qn("wp:cNvGraphicFramePr"))
    graphic = inline.find(qn("a:graphic"))
    docPr.set("id", str(doc_pr_id))
    docPr.set("name", name)
    anchor = OxmlElement("wp:anchor")
    for key, val in (
        ("distT", "0"),
        ("distB", "0"),
        ("distL", "0"),
        ("distR", "0"),
        ("simplePos", "0"),
        ("relativeHeight", "0"),
        ("behindDoc", "1"),
        ("locked", "1"),
        ("layoutInCell", "1"),
        ("allowOverlap", "1"),
    ):
        anchor.set(key, val)
    simple = OxmlElement("wp:simplePos")
    simple.set("x", "0")
    simple.set("y", "0")
    pos_h = OxmlElement("wp:positionH")
    pos_h.set("relativeFrom", "page")
    off_h = OxmlElement("wp:posOffset")
    off_h.text = "0"
    pos_h.append(off_h)
    pos_v = OxmlElement("wp:positionV")
    pos_v.set("relativeFrom", "page")
    off_v = OxmlElement("wp:posOffset")
    off_v.text = "0"
    pos_v.append(off_v)
    new_extent = OxmlElement("wp:extent")
    new_extent.set("cx", cx)
    new_extent.set("cy", cy)
    effect = OxmlElement("wp:effectExtent")
    for k in ("l", "t", "r", "b"):
        effect.set(k, "0")
    wrap = OxmlElement("wp:wrapNone")
    for child in (simple, pos_h, pos_v, new_extent, effect, wrap):
        anchor.append(child)
    if docPr is not None:
        anchor.append(docPr)
    if cNv is not None:
        anchor.append(cNv)
    if graphic is not None:
        anchor.append(graphic)
    drawing.remove(inline)
    drawing.append(anchor)


def add_header_background(section, image_path: Path, page_index: int) -> None:
    header = section.header
    header.is_linked_to_previous = False
    paragraph = header.paragraphs[0] if header.paragraphs else header.add_paragraph()
    tight_paragraph(paragraph)
    run = paragraph.add_run()
    run.add_picture(str(image_path), width=A4_W, height=A4_H)
    drawing = run._r.find(qn("w:drawing"))
    if drawing is not None:
        _inline_to_anchor(drawing, page_index + 1, f"page-{page_index + 1:03d}")
    footer = section.footer
    footer.is_linked_to_previous = False
    for p in footer.paragraphs:
        p.clear()
        tight_paragraph(p)


def page_jpeg(page, dest: Path) -> None:
    zoom = DPI / 72.0
    pix = page.get_pixmap(matrix=fitz.Matrix(zoom, zoom), alpha=False, annots=True)
    img = Image.frombytes("RGB", (pix.width, pix.height), pix.samples)
    pix = None
    dest.parent.mkdir(parents=True, exist_ok=True)
    img.save(
        dest,
        "JPEG",
        quality=JPEG_QUALITY,
        optimize=True,
        subsampling=0,
        dpi=(DPI, DPI),
    )
    img.close()


def build() -> None:
    if not PDF.exists():
        raise SystemExit(f"missing {PDF}; compile XeLaTeX first")

    tmp = BOOK / "_page_images"
    if tmp.exists():
        shutil.rmtree(tmp)
    tmp.mkdir(parents=True)

    doc = Document()
    disable_auto_compress(doc)
    normal = doc.styles["Normal"]
    normal.paragraph_format.space_before = Pt(0)
    normal.paragraph_format.space_after = Pt(0)
    normal.paragraph_format.line_spacing = 1.0
    normal.font.size = Pt(1)

    pdf = fitz.open(PDF)
    n_pages = pdf.page_count
    for i, page in enumerate(pdf):
        img_path = tmp / f"page-{i + 1:03d}.jpg"
        page_jpeg(page, img_path)
        if i == 0:
            section = doc.sections[0]
            configure_section(section)
            add_header_background(section, img_path, i)
            p = doc.paragraphs[0] if doc.paragraphs else doc.add_paragraph()
            tight_paragraph(p)
            run = p.add_run(" ")
            run.font.size = Pt(1)
        else:
            section = doc.add_section(WD_SECTION.NEW_PAGE)
            configure_section(section)
            add_header_background(section, img_path, i)
            p = doc.paragraphs[-1]
            tight_paragraph(p)
            if not p.runs:
                run = p.add_run(" ")
                run.font.size = Pt(1)
        print(f"page {i + 1}/{n_pages}", flush=True)

    pdf.close()
    SUBMIT_DIR.mkdir(exist_ok=True)
    SUBMIT_PDF.write_bytes(PDF.read_bytes())
    doc.save(SUBMIT_DOCX)
    doc.save(LOCAL_DOCX)
    shutil.rmtree(tmp, ignore_errors=True)
    print("wrote", SUBMIT_DOCX, "pages", n_pages)
    print("wrote", SUBMIT_PDF)


if __name__ == "__main__":
    build()
