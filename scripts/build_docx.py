# -*- coding: utf-8 -*-
"""Word of the same monograph. Formula source is text; PDF numbering is authority."""
import re
from pathlib import Path
from docx import Document
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml.ns import qn
from docx.shared import Cm, Pt

ROOT = Path(__file__).resolve().parents[1]
BOOK = ROOT / "monograph"
FIG = ROOT / "results" / "figures"
OUT = BOOK / "ACTS-MCDT.docx"

ORDER = [
    "c01.tex", "c02.tex", "c03.tex", "c04.tex", "c05.tex", "c06.tex",
    "c07.tex", "c08.tex", "c09.tex", "c10.tex", "c11.tex", "c12.tex",
    "c13.tex", "c14.tex", "c15.tex", "c16.tex", "c17.tex", "c18.tex",
    "app_symbols.tex", "app_discrete.tex", "app_trace.tex", "app_scales.tex",
]


def read_tree(name, seen=None):
    seen = seen or set()
    if name in seen:
        return ""
    seen.add(name)
    text = (BOOK / name).read_text(encoding="utf-8")
    def repl(m):
        return "\n" + read_tree(m.group(1), seen) + "\n"
    return re.sub(r"\\input\{([^}]+)\}", repl, text)


def strip_math(s):
    s = s.replace("\\,", " ").replace("\\ ", " ").replace("~", " ")
    s = re.sub(r"\\(?:mathrm|mathbf|text|operatorname\*?)\{([^{}]*)\}", r"\1", s)
    s = s.replace("\\vect", "").replace("\\bm", "")
    reps = {
        "\\alpha": "α", "\\beta": "β", "\\varepsilon": "ε", "\\sigma": "σ",
        "\\theta": "θ", "\\tau": "τ", "\\Delta": "Δ", "\\partial": "∂",
        "\\cdot": "·", "\\times": "×", "\\leq": "≤", "\\geq": "≥",
        "\\approx": "≈", "\\infty": "∞", "\\in": "∈", "\\subset": "⊂",
        "\\quad": " ", "\\qquad": " ", "\\\\": "\n",
        "\\left": "", "\\right": "", "\\big": "", "\\Big": "",
    }
    for a, b in reps.items():
        s = s.replace(a, b)
    s = re.sub(r"\\(?:label|ref|eqref|cite)\{([^{}]*)\}", r"[\1]", s)
    s = re.sub(r"\\[a-zA-Z]+", "", s)
    s = s.replace("{", "").replace("}", "")
    s = re.sub(r"\s+", " ", s)
    return s.strip()


def set_run_font(run, size=11, bold=False):
    run.font.size = Pt(size)
    run.bold = bold
    run.font.name = "Times New Roman"
    run._element.rPr.rFonts.set(qn("w:eastAsia"), "宋体")


def add_para(doc, text, size=11, bold=False, center=False, space_after=6):
    p = doc.add_paragraph()
    p.paragraph_format.space_after = Pt(space_after)
    p.paragraph_format.line_spacing = 1.28
    p.paragraph_format.first_line_indent = Cm(0.74) if not (bold or center) else Cm(0)
    if center:
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    run = p.add_run(text)
    set_run_font(run, size, bold)
    return p


def find_image(name):
    for base in (FIG, FIG / "paper"):
        path = base / name
        if path.exists():
            return path
    return None


def emit(doc, src):
    src = re.sub(r"(?<!\\)%.*", "", src)
    parts = re.split(r"(\\chapter\*?\{.*?\}|\\section\*?\{.*?\}|\\subsection\*?\{.*?\}|\\paragraph\{.*?\}|\\begin\{(?:equation|align|figure|table|longtable)\}.*?\\end\{(?:equation|align|figure|table|longtable)\}|\\includegraphics(?:\[[^\]]*\])?\{.*?\})", src, flags=re.S)
    for part in parts:
        part = part.strip()
        if not part:
            continue
        if part.startswith("\\chapter"):
            title = strip_math(re.search(r"\{(.*)\}", part, re.S).group(1))
            add_para(doc, title, 16, True, space_after=10)
        elif part.startswith("\\section"):
            title = strip_math(re.search(r"\{(.*)\}", part, re.S).group(1))
            add_para(doc, title, 14, True, space_after=8)
        elif part.startswith("\\subsection"):
            title = strip_math(re.search(r"\{(.*)\}", part, re.S).group(1))
            add_para(doc, title, 12, True, space_after=6)
        elif part.startswith("\\paragraph"):
            title = strip_math(re.search(r"\{(.*)\}", part, re.S).group(1))
            add_para(doc, title, 11, True, space_after=4)
        elif part.startswith("\\begin{equation") or part.startswith("\\begin{align"):
            body = re.sub(r"\\begin\{(?:equation|align)\*?\}|\\end\{(?:equation|align)\*?\}", "", part)
            add_para(doc, strip_math(body), 11, center=True, space_after=6)
        elif "includegraphics" in part and part.startswith("\\begin{figure"):
            for name in re.findall(r"\\includegraphics(?:\[[^\]]*\])?\{([^}]+)\}", part):
                img = find_image(Path(name).name)
                if img:
                    p = doc.add_paragraph()
                    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
                    p.add_run().add_picture(str(img), width=Cm(14.5))
            cap = re.search(r"\\caption\{(.*)\}", part, re.S)
            if cap:
                add_para(doc, strip_math(cap.group(1)), 10, center=True)
        elif part.startswith("\\begin{table") or part.startswith("\\begin{longtable"):
            cap = re.search(r"\\caption\{(.*?)\}", part, re.S)
            if cap:
                add_para(doc, strip_math(cap.group(1)), 10, True, center=True, space_after=2)
            rows = []
            for line in part.splitlines():
                if "&" not in line:
                    continue
                if line.strip().startswith("\\"):
                    continue
                cells = [strip_math(c) for c in line.split("&")]
                cells[-1] = cells[-1].replace("\\\\", "").strip()
                if any(cells):
                    rows.append(cells)
            if not rows:
                continue
            width = max(len(r) for r in rows)
            table = doc.add_table(rows=0, cols=width)
            table.style = "Table Grid"
            for row in rows[:80]:
                cells = table.add_row().cells
                for i in range(width):
                    cells[i].text = row[i] if i < len(row) else ""
            if len(rows) > 80:
                add_para(doc, f"（表在 PDF 中有 {len(rows)} 行，此处保留前 80 行。完整行以 PDF 为准。）", 10)
        else:
            text = strip_math(part)
            if len(text) < 2:
                continue
            for para in re.split(r"\n\s*\n", text):
                para = para.strip()
                if para:
                    add_para(doc, para)


def main():
    doc = Document()
    sec = doc.sections[0]
    sec.page_width = Cm(21.0)
    sec.page_height = Cm(29.7)
    sec.left_margin = Cm(2.5)
    sec.right_margin = Cm(2.5)
    sec.top_margin = Cm(2.6)
    sec.bottom_margin = Cm(2.6)
    add_para(doc, "智能蒸烤一体机的自主认知系统", 18, True, center=True, space_after=4)
    add_para(doc, "ACTS-MCDT", 14, True, center=True, space_after=8)
    add_para(doc, "公式编号以同名 PDF 为准。本文 Word 保留公式的源文本，便于批注。图与表来自同一批日志。", 11, center=True)
    for name in ORDER:
        emit(doc, read_tree(name))
    add_para(doc, "参考文献与标准入口", 16, True, space_after=10)
    emit(doc, (ROOT / "refs.tex").read_text(encoding="utf-8"))
    add_para(doc, "文稿中的计算与起草", 16, True, space_after=10)
    add_para(doc, "日志、分位表和命题核对由数值核生成，种子与时间步长写在附录的离散格式中。叙述、公式整理和章节展开在起草时使用了语言模型；数字不由语言模型给出。未运行的规格保持为规格，不写成结果。")
    doc.save(OUT)
    print("wrote", OUT, "paragraphs", len(doc.paragraphs))


if __name__ == "__main__":
    main()
