# -*- coding: utf-8 -*-
"""Update chapter/section titles so the TOC shows the paper architecture."""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1] / "monograph"

REPLACEMENTS = {
    "ch01.tex": [
        (r"\section{研究背景}", r"\section{蒸烤分体到一体：四个旋钮与内部剖面}"),
        (r"\section{问题陈述}", r"\section{信息赤字与感知—决策—执行链}"),
        (r"\section{研究目标}", r"\section{五条设计判据}"),
        (r"\section{主要工作}", r"\section{从四个边界到交叉表与演示}"),
        (r"\section{论文结构}", r"\section{全文逻辑架构}"),
    ],
    "ch02.tex": [
        (r"\chapter{文献综述与现有方案}", r"\chapter{文献基础与商品路径的信息止点}"),
        (r"\section{食品热湿传递}", r"\section{体积平均与热湿传递骨架}"),
        (r"\section{品质动力学与热力进度}", r"\section{进度阈值与热力设计线}"),
        (r"\section{逆热传导与状态估计}", r"\section{由表面恢复内部热阻的病态}"),
        (r"\section{对偶控制与安全屏障}", r"\section{辨识动作与硬测量投影}"),
        (r"\section{现有装置的信息止点}", r"\section{商品路径已经闭合的量}"),
        (r"\section{货架彩页怎样被厨房读完}", r"\section{参数表闭合边界、停机仍按时钟}"),
        (r"\section{加水口、搁架高度和冷凝托盘}", r"\section{硬切断零件与不进积分器的附件}"),
    ],
    "ch03.tex": [
        (r"\chapter{系统总体设计}", r"\chapter{感知—决策—执行总体架构}"),
        (r"\section{闭环结构}", r"\section{五层闭环与请求—指令隔离}"),
        (r"\section{五层与时间尺度}", r"\section{家用时域与薄厚 Fourier 数}"),
        (r"\section{决策状态}", r"\section{九维决策状态与四个判断}"),
        (r"\section{三档只改允许集合}", r"\section{蒸、烤、组合的通量上界}"),
    ],
    "ch04.tex": [
        (r"\chapter{多尺度物理模型}", r"\chapter{多尺度物理收缩：从全场到决策状态}"),
        (r"\section{计算域与全场}", r"\section{腔体与食品的计算域}"),
        (r"\section{能量与三相质量}", r"\section{能量、液相与蒸汽方程}"),
        (r"\section{腔体、表面与一维核}", r"\section{四个边界收为界面通量}"),
        (r"\section{反应进度}", r"\section{热力进度、褐变与结壳}"),
        (r"\section{两节点工作方程}", r"\section{表面—冷点两节点与内部热阻}"),
    ],
    "ch05.tex": [
        (r"\chapter{信息感知与状态估计}", r"\chapter{估计病态与稳态不可辨识}"),
        (r"\section{可安装观测}", r"\section{可安装通道与已经接到跟踪器的量}"),
        (r"\section{病态结构}", r"\section{内部热阻的灵敏度结构}"),
        (r"\section{稳态不可辨识}", r"\section{平衡观测灵敏度为零}"),
        (r"\section{Fisher 信息与在线跟踪器}", r"\section{短时激励的信息增益与标量跟踪器}"),
    ],
    "ch06.tex": [
        (r"\chapter{对偶控制与热信息探针}", r"\chapter{热信息探针与对偶决策}"),
        (r"\section{探针的定义}", r"\section{信息动作的三条判据}"),
        (r"\section{两段脉冲的秩}", r"\section{相变变号与对流的第二灵敏度方向}"),
        (r"\section{探针窗口内的冷点上界}", r"\section{四十秒窗内冷点几乎不动}"),
        (r"\section{四种策略}", r"\section{开环、腔温、无探针与对偶的停机几何}"),
    ],
    "ch07.tex": [
        (r"\chapter{因果路径与安全投影}", r"\chapter{因果路径与测量隔离的安全投影}"),
        (r"\section{结构方程与干预}", r"\section{干预、路径积分与可更新参数}"),
        (r"\section{三条路径}", r"\section{冷点潜热、表面蒸发与结壳热阻}"),
        (r"\section{品质参考与安全集}", r"\section{品质回路与硬测量安全集}"),
    ],
    "ch08.tex": [
        (r"\chapter{仿真结果}", r"\chapter{主对照：厚度几何、档位交叉与探针方差}"),
        (r"\section{两套格子}", r"\section{S1 主对照与档位研究两套格子}"),
        (r"\section{厚度决定能否越过设计线}", r"\section{薄件过熟、厚件不足}"),
        (r"\section{档位只改允许集合}", r"\section{蒸烤组合交叉下的允许集合}"),
        (r"\section{探针买到的是方差}", r"\section{探针降低的是热阻方差}"),
        (r"\section{Antoine 项的符号随厚度翻转}", r"\section{蒸汽潜热项的厚度符号翻转}"),
        (r"\section{分布形状与厚度--策略热图}", r"\section{停机偏差的分布与热图}"),
    ],
    "ch09.tex": [
        (r"\chapter{实现与交互演示}", r"\chapter{数值核与三维交互演示}"),
        (r"\section{数值核}", r"\section{十六条控制体与评分循环}"),
        (r"\section{三维腔体}", r"\section{状态流读回可见零件}"),
        (r"\section{面板、对照与事件}", r"\section{档位、对照策略与开门}"),
        (r"\section{交互页与导出字段}", r"\section{演示地址与日志字段}"),
    ],
    "ch10.tex": [
        (r"\section{已经成立的结论}", r"\section{交叉表上已经站住的事实}"),
        (r"\section{四个旋钮在产品上的读法}", r"\section{加热、蒸汽、排汽与风机}"),
        (r"\section{核、跟踪器与厚度几何}", r"\section{点估计偏差与 Fourier 几何}"),
        (r"\section{演示页把同一状态流摊回腔体}", r"\section{交互页与默认种子 7}"),
        (r"\section{可继续的工作}", r"\section{可安装通道、后验写回与型式试验}"),
        (r"\section{说明书三栏与厨房里的两盏灯}", r"\section{产品叙述与厨房核对}"),
    ],
    "ch11.tex": [
        (r"\chapter{离散网格与收敛诊断}", r"\chapter{网格收敛与冷点格子}"),
        (r"\section{为什么要单独做网格}", r"\section{停机偏差对格子数敏感}"),
        (r"\section{S0：十六格相对八格}", r"\section{八格到十六格：30 mm 对偶翻号}"),
        (r"\section{种子 7 上的五档加密}", r"\section{种子 7 上从 8 到 32 的加密}"),
        (r"\section{与主表的衔接}", r"\section{主对照固定在十六条}"),
    ],
    "ch12.tex": [
        (r"\section{S1 对偶子集上的边际}", r"\section{食品名、含水与非均质的边际}"),
        (r"\section{S2：探针、遮挡、质量、脂肪与开门}", r"\section{探针、遮挡、质量、脂肪与开门}"),
        (r"\section{种子 7 上的含水复核}", r"\section{种子 7 轨迹上的含水三档}"),
    ],
    "ch13.tex": [
        (r"\section{宽格子的分位}", r"\section{更宽先验下的停机分位}"),
        (r"\section{集合散布}", r"\section{集合样本的停机散布}"),
        (r"\section{50 mm 的时域延长}", r"\section{厚件走到设计线需要延长时域}"),
        (r"\section{档位研究上的初温与含水}", r"\section{档位研究中的初温与含水}"),
    ],
    "ch14.tex": [
        (r"\section{二十四乘十六的显式截面}", r"\section{显式截面上冷点偏离几何中心}"),
        (r"\section{通道关联与核里的换热}", r"\section{通道关联与核内换热}"),
        (r"\section{Fourier 数与 Biot 数}", r"\section{薄件走完尺度、厚件停在 0.12}"),
        (r"\section{加热器温度与腔温}", r"\section{管温平衡点与削减阈值}"),
        (r"\section{结壳扫描}", r"\section{干壳代理随排汽与时间}"),
    ],
    "ch15.tex": [
        (r"\section{四条策略}", r"\section{同一初值上四条策略的轨迹}"),
        (r"\section{三种厚度}", r"\section{三种厚度的过程差异}"),
        (r"\section{三种档位}", r"\section{蒸、烤、组合的执行量轨迹}"),
        (r"\section{路径代理随时间}", r"\section{三条路径的时间展开}"),
        (r"\section{表面温差、Antoine 项与算子残差}", r"\section{界面温差、潜热项与算子残差}"),
    ],
    "app_discrete.tex": [
        (r"\section{控制体}", r"\section{十六条控制体}"),
        (r"\section{四条策略的执行量}", r"\section{开环、腔温、无探针与对偶的执行量}"),
        (r"\section{加热器与界面}", r"\section{加热器温度与界面通量}"),
        (r"\section{适用范围}", r"\section{离散核的适用范围}"),
    ],
    "app_scales.tex": [
        (r"\section{加热器平衡}", r"\section{加热器平衡点}"),
        (r"\section{进度设计线}", r"\section{进度设计线与 \(F\) 值}"),
        (r"\section{适用范围}", r"\section{尺度估计的适用范围}"),
    ],
    "app_trace.tex": [
        (r"\chapter{一条轨迹的抽样}", r"\chapter{种子 7 轨迹抽样}"),
        (r"\section{探针前后}", r"\section{探针窗前后的状态}"),
        (r"\section{同一格式重放的内部场}", r"\section{同一格式重放的内部场}"),
    ],
    "app_symbols.tex": [
        (r"\section{规格场}", r"\section{规格层场量}"),
        (r"\section{估计、探针与执行}", r"\section{估计、探针与执行量}"),
        (r"\section{数值核里实际出现的量}", r"\section{数值核中实际出现的量}"),
        (r"\section{日志列}", r"\section{日志字段}"),
    ],
}

WIDTH_MAP = {
    "0.72": "0.88",
    "0.78": "0.88",
    "0.80": "0.88",
    "0.82": "0.88",
    "0.84": "0.90",
}


def bump_widths(text: str) -> str:
    for old, new in WIDTH_MAP.items():
        text = text.replace(rf"includegraphics[width={old}\textwidth]", rf"includegraphics[width={new}\textwidth]")
    return text


def main() -> None:
    for name, pairs in REPLACEMENTS.items():
        path = ROOT / name
        text = path.read_text(encoding="utf-8")
        for old, new in pairs:
            if old not in text:
                print("MISSING", name, old)
            else:
                text = text.replace(old, new, 1)
        text = bump_widths(text)
        path.write_text(text, encoding="utf-8")
        print("updated", name)
    for extra in ROOT.glob("ch*.tex"):
        if extra.name in REPLACEMENTS:
            continue
        text = extra.read_text(encoding="utf-8")
        new = bump_widths(text)
        if new != text:
            extra.write_text(new, encoding="utf-8")
            print("widths", extra.name)


if __name__ == "__main__":
    main()
