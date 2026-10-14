"""Draw mechanism figures M1--M28. Arrows follow the written equations."""

from pathlib import Path

import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch

plt.rcParams["font.sans-serif"] = ["Microsoft YaHei", "SimHei"]
plt.rcParams["axes.unicode_minus"] = False

OUT = Path(__file__).resolve().parents[1] / "monograph" / "figures"
OUT.mkdir(parents=True, exist_ok=True)


def box(ax, x, y, text, w=1.6, h=0.55):
    patch = FancyBboxPatch(
        (x - w / 2, y - h / 2), w, h,
        boxstyle="round,pad=0.02,rounding_size=0.08",
        facecolor="#f4efe6", edgecolor="#3c352c", lw=1.1,
    )
    ax.add_patch(patch)
    ax.text(x, y, text, ha="center", va="center", fontsize=9)


def arrow(ax, a, b):
    ax.annotate(
        "", xy=b, xytext=a,
        arrowprops=dict(arrowstyle="-|>", color="#3c352c", lw=1.1),
    )


def new():
    fig, ax = plt.subplots(figsize=(7.2, 3.6))
    ax.set_xlim(0, 10)
    ax.set_ylim(0, 5)
    ax.axis("off")
    return fig, ax


def save(fig, name):
    fig.tight_layout()
    fig.savefig(OUT / name, dpi=140)
    plt.close(fig)


SPECS = [
    ("M01", ["四个判断", "信息赤字"], [(2, 3), (7, 3)]),
    ("M02", ["真值", "带噪采样", "后验", "投影", "边界"], [(1.2, 3), (3, 3), (5, 3), (7, 3), (8.8, 3)]),
    ("M03", ["感知", "估计", "探针", "品质", "安全", "执行器"], [(1, 3), (2.6, 3), (4.2, 3), (5.8, 3), (7.4, 3), (9, 3)]),
    ("M04", ["毫秒安全", "秒级边界", "分钟食品", "批次类别"], [(1.5, 3), (3.7, 3), (6, 3), (8.4, 3)]),
    ("M05", ["模块只传分布", "不传点估计"], [(3, 3), (7.2, 3)]),
    ("M06", ["固相", "液相", "汽相", "界面"], [(1.5, 3.4), (4, 3.4), (6.5, 3.4), (8.5, 2)]),
    ("M07", ["对流", "扩散", "潜热", "反应热", "能量"], [(1.2, 3.6), (3.2, 3.6), (5.2, 3.6), (7.2, 3.6), (5, 1.6)]),
    ("M08", ["冷凝 +q", "蒸发 -q"], [(3, 3), (7, 3)]),
    ("M09", ["蛋白", "淀粉", "美拉德", "热力当量"], [(1.4, 3), (3.6, 3), (6, 3), (8.4, 3)]),
    ("M10", ["表面变干", "结壳", "热阻上升"], [(2, 3), (5, 3), (8, 3)]),
    ("M11", ["全场 X", "映射 Phi", "决策状态 z"], [(2, 3), (5, 3), (8, 3)]),
    ("M12", ["土豆陡", "面团中", "肉糜宽"], [(2, 3), (5, 3), (8, 3)]),
    ("M13", ["平行导热", "脂肪夹层", "垂直导热"], [(2, 3), (5, 3), (8, 3)]),
    ("M14", ["收缩", "厚度下降", "渗透率下降"], [(2, 3), (5, 3.6), (5, 2)]),
    ("M15", ["加热管", "腔壁", "食品"], [(2, 3.6), (5, 3.6), (8, 2.2)]),
    ("M16", ["发射", "反射", "红外亮度"], [(2, 3), (5, 3), (8, 3)]),
    ("M17", ["顶加热", "冷点下移", "底加热", "冷点上移"], [(1.5, 3.6), (4, 3.6), (6.2, 2), (8.6, 2)]),
    ("M18", ["蒸汽段", "高风段"], [(3, 3), (7, 3)]),
    ("M19", ["表面时间常数", "冷点傅里叶窗"], [(3, 3), (7.2, 3)]),
    ("M20", ["信息赤字", "信息项开", "赤字消失", "信息项关"], [(1.4, 3.6), (4, 3.6), (6.2, 2), (8.6, 2)]),
    ("M21", ["蒸汽", "冷点", "表面", "结壳"], [(2, 3.6), (5, 3.6), (5, 2.2), (8, 2.2)]),
    ("M22", ["蒸汽", "路径A", "路径B", "路径C"], [(1.6, 3), (4.4, 3.8), (4.4, 2.2), (7.6, 3)]),
    ("M23", ["预测", "干预", "反事实"], [(2, 3), (5, 3), (8, 3)]),
    ("M24", ["物理项", "有界残差", "越界回退"], [(2, 3), (5, 3), (8, 3)]),
    ("M25", ["类别先验", "精度加权", "拒绝写回"], [(2, 3), (5, 3), (8, 3)]),
    ("M26", ["品质请求", "安全集", "进入边界"], [(2, 3), (5, 3), (8, 3)]),
    ("M27", ["品质", "探针", "保持", "断电"], [(1.4, 3), (3.6, 3), (6, 3), (8.4, 3)]),
    ("M28", ["品质测量", "硬测量", "执行器"], [(2, 3.6), (2, 2), (7, 2.8)]),
]


def main():
    for name, labels, coords in SPECS:
        fig, ax = new()
        for (x, y), text in zip(coords, labels):
            box(ax, x, y, text)
        for i in range(len(coords) - 1):
            arrow(ax, coords[i], coords[i + 1])
        ax.set_title(name, loc="left", fontsize=11, color="#6b5e4e")
        save(fig, f"{name}.png")
    print(len(SPECS))


if __name__ == "__main__":
    main()
