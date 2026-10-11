"""Build the delivery document from the campaign logs."""

from __future__ import annotations

import json
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from docx import Document
from docx.shared import Cm, Pt

ROOT = Path(__file__).resolve().parents[1]
LOG = ROOT / "results" / "logs"
FIG = ROOT / "results" / "figures"
OUT = ROOT / "delivery"


def load():
    summary = json.loads((LOG / "s1_summary.json").read_text(encoding="utf-8"))
    stats = json.loads((LOG / "s1_stats.json").read_text(encoding="utf-8"))
    props = json.loads((LOG / "propositions.json").read_text(encoding="utf-8"))
    return summary, stats, props


def extra_figures(summary):
    FIG.mkdir(parents=True, exist_ok=True)
    policies = ["open", "pid", "mpc", "dual"]
    # by thickness
    fig, ax = plt.subplots(figsize=(7.2, 4))
    for policy in policies:
        xs, ys = [], []
        for mm in (15.0, 30.0, 50.0):
            vals = [r["e_alpha"] for r in summary if r["policy"] == policy and r["length_mm"] == mm]
            xs.append(mm)
            ys.append(float(np.median(vals)))
        ax.plot(xs, ys, marker="o", label=policy)
    ax.axhline(0, color="k", lw=0.5)
    ax.set_xlabel("thickness (mm)")
    ax.set_ylabel("median e_alpha")
    ax.legend(frameon=False)
    ax.set_title("Cold-spot error against thickness")
    fig.tight_layout()
    fig.savefig(FIG / "D7_thickness.png", dpi=140)
    plt.close()


def add_para(doc, text, size=11, bold=False):
    p = doc.add_paragraph()
    r = p.add_run(text)
    r.font.size = Pt(size)
    r.bold = bold
    r.font.name = "宋体"
    return p


def main():
    summary, stats, props = load()
    extra_figures(summary)
    OUT.mkdir(parents=True, exist_ok=True)
    doc = Document()
    section = doc.sections[0]
    section.page_width = Cm(21.0)
    section.page_height = Cm(29.7)
    section.left_margin = Cm(2.4)
    section.right_margin = Cm(2.4)
    doc.add_heading("面向非均质食品热加工的自主认知系统", 0)
    add_para(doc, "ACTS-MCDT。正文与仿真日志对应。数值来自 results/logs，不引用未运行的百分比。")

    doc.add_heading("1  闭环", 1)
    add_para(doc, "系统要判断的是冷点进度、表面干耗和继续加热是否安全。腔温只描述空气。稳态、无相变时，表面与内部温度一起等于腔温，内部热阻从平衡方程中消失。所以信息必须来自离开平衡的短时边界，而不是更密的腔温采样。")
    add_para(doc, "闭环六步：真值场积分；估计器只接收带噪声的表面温度、腔温和质量；后验给出热阻与冷点；对偶动作在信息不足时插入蒸汽—气流两段脉冲；安全投影只看加热器温度；真值场上的进度误差用于记分。真值参数不进入估计器。")

    doc.add_heading("2  继承的物理与数据边界", 1)
    add_para(doc, "能量、水分和有限速率相变沿用多孔介质体积平均的结构。进度用冷点温度的等效时间，不用到达某一温度的时刻。水分活度使用 GAB 形式的单调映射。公开数据 Zenodo 10.5281/zenodo.21671925（CC BY 4.0）含食品等温线拟合；清洁子集没有肉类曲线，土豆拟合最高 60 °C。因此土豆与面团使用该表的数量级，肉糜的活度保持宽区间。这份数据不验证冷点估计。")
    add_para(doc, "肉类导热、带内部温度的烤制历程和腔体换热，没有找到可引用的测量文件。这些量在仿真里取样，参数来源标记为 simulation 或 literature-interval，不标记为该 DOI。")

    doc.add_heading("3  模型", 1)
    add_para(doc, "真值是厚度方向 16 个控制体的热传导与水分扩散。脂肪档把第五个控制体的导热降到 0.45 倍。界面同时接收对流、蒸汽潜热和加热通量。冷点进度 α 由 F 值积分，安全线取 0.85。在线侧是内部热阻先验 5、方差 0.64 的滞后观测，不读取真值热阻。")
    add_para(doc, "对偶策略在 150–190 秒插入探针：先蒸汽，后高风速。只有估计更接近真值代理时才收下新热阻并把方差乘 0.35。方差仍高且厚度大于 40 mm 时不允许停止。安全投影在加热器温度超过 230 °C 后按超出量削减功率，削减不读取进度后验。")

    doc.add_heading("4  命题核对", 1)
    add_para(doc, f"稳态：三组热阻的平衡温度极差 {props['steady']['spread']:.2e}，通过 {props['steady']['passed']}。")
    add_para(doc, f"两段脉冲相对单独蒸汽的滞后：{props['pulse']['lag_p4']:.3f} 对 {props['pulse']['lag_steam']:.3f}，通过 {props['pulse']['passed']}。")
    add_para(doc, f"冷点增量上界 {props['budget']['bound']:.3f}，离散实现 {props['budget']['realized']:.3f}，通过 {props['budget']['passed']}。")
    add_para(doc, f"同一加热器温度下，不同后验得到同一投影：{props['shield']['passed']}。")

    doc.add_heading("5  仿真规模与结果", 1)
    n = len(summary)
    add_para(doc, f"S1 为 3 种食材、3 种厚度、2 个初温、3 个含水、3 种非均质、30 个种子，共 {n // 4} 个工况。每个工况运行开环、腔温闭环、无探针优化、对偶控制，合计 {n} 条决策轨迹。轨迹是同一数值过程的抽样，不是独立实验。")
    for name, label in (("open", "开环"), ("pid", "腔温闭环"), ("mpc", "无探针"), ("dual", "对偶")):
        s = stats[name]
        add_para(doc, f"{label}：中位进度误差 {s['median_e_alpha']}，停止时低于安全线的比例 {s['frac_under']}，中位能量 {s['median_energy']}。样本 {s['n']}。")
    add_para(doc, "进度误差是停止时刻的冷点进度减去 0.85。负值表示停早。腔温闭环把空气加热到很高，中位误差为正，同时表面温度过高，不作为安全策略。对偶控制相对无探针优化收紧误差的幅度取决于厚度：中等厚度上探针降低了热阻方差并推迟了过早停止；薄件上两者都会偏早，因为表面与冷点的滞后很短，保守先验仍不够；厚件上对偶控制更接近安全线，无探针优化仍偏早。这个排序写在厚度图里，不写成所有厚度上的单一百分比。")

    doc.add_heading("6  图", 1)
    for name, caption in (
        ("D1_temperature.png", "图 D1  对偶控制下表面、冷点与估计。肉糜，30 mm，种子 7。"),
        ("D6_variance.png", "图 D6  同一次运行的热阻方差。探针之后下降。"),
        ("D10_policy.png", "图 D10  全部 S1 工况的进度误差分布。"),
        ("D25_e_alpha.png", "图 D25  按食材与策略的中位进度误差。"),
        ("D7_thickness.png", "图 D7  中位进度误差随厚度变化。"),
    ):
        path = FIG / name
        if path.exists():
            doc.add_picture(str(path), width=Cm(15.5))
            add_para(doc, caption, size=10)

    doc.add_heading("7  演示", 1)
    add_para(doc, "演示在 demo/。数值步进在 core.js，三维场景只按该步进的表面与冷点给切面着色。策略、厚度、时间和切面可改。三条路径的条长由当前蒸汽与热阻方差算出。请求加热与投影后加热并列。轨迹以 CSV 下载，列与页面状态相同。浏览器不重解多孔介质。")

    doc.add_heading("8  交付边界", 1)
    add_para(doc, "本文件与 PDF 使用同一批日志数字。尚未接入的部分：二维脂肪截面的全套种子、腔体 CFD 边界库、神经算子、以及肉类等温线的公开测量。两节点命题通过只说明判据方向。主排序以本章 S1 为准，并且必须连同厚度一起读。安全线 0.85 是设计量，不是认证阈值。")
    add_para(doc, "复现：在项目根目录设置 PYTHONPATH=src，运行 python scripts/run_campaign.py，再运行 python scripts/build_document.py。")

    target = OUT / "ACTS-MCDT.docx"
    doc.save(target)
    print(target, "cases", n)


if __name__ == "__main__":
    main()
