# -*- coding: utf-8 -*-
"""Rewrite chapter/section titles into summarizing headings."""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1] / "monograph"

# Exact LaTeX commands currently on disk -> summarizing titles.
REPLACEMENTS = {
    "ch01.tex": [
        (r"\section{蒸烤分体到一体：四个旋钮与内部剖面}", r"\section{蒸烤一体后的执行边界}"),
        (r"\section{信息赤字与感知—决策—执行链}", r"\section{内部热阻缺席下的决策困难}"),
        (r"\section{五条设计判据}", r"\section{系统设计的五条约束}"),
        (r"\section{从四个边界到交叉表与演示}", r"\section{模型收缩、交叉对照与演示}"),
        (r"\section{全文逻辑架构}", r"\section{论证线索与章节安排}"),
    ],
    "ch02.tex": [
        (r"\chapter{文献基础与商品路径的信息止点}", r"\chapter{文献基础与商品方案的信息边界}"),
        (r"\section{体积平均与热湿传递骨架}", r"\section{食品热湿传递的描述框架}"),
        (r"\section{进度阈值与热力设计线}", r"\section{热力进度作为停机依据}"),
        (r"\section{由表面恢复内部热阻的病态}", r"\section{内部热阻估计的病态性质}"),
        (r"\section{辨识动作与硬测量投影}", r"\section{对偶控制与安全屏障}"),
        (r"\section{商品路径已经闭合的量}", r"\section{现有商品方案的信息边界}"),
        (r"\section{参数表闭合边界、停机仍按时钟}", r"\section{菜单时钟对内部状态的替代}"),
        (r"\section{硬切断零件与不进积分器的附件}", r"\section{安全切断与模型外附件}"),
    ],
    "gab_tables.tex": [
        (r"\subsection{清洁拟合的记录}", r"\subsection{公开等温线的拟合记录}"),
    ],
    "ch03.tex": [
        (r"\chapter{感知—决策—执行总体架构}", r"\chapter{感知、决策与执行的分层}"),
        (r"\section{五层闭环与请求—指令隔离}", r"\section{五层闭环及其隔离关系}"),
        (r"\section{家用时域与薄厚 Fourier 数}", r"\section{家用时域下的厚度尺度}"),
        (r"\section{九维决策状态与四个判断}", r"\section{决策状态的构成}"),
        (r"\section{蒸、烤、组合的通量上界}", r"\section{三档模式对执行范围的限制}"),
    ],
    "ch04.tex": [
        (r"\chapter{多尺度物理收缩：从全场到决策状态}", r"\chapter{从全场物理到决策状态}"),
        (r"\section{腔体与食品的计算域}", r"\section{计算域的划分}"),
        (r"\section{能量、液相与蒸汽方程}", r"\section{能量与水分方程}"),
        (r"\section{四个边界收为界面通量}", r"\section{边界作用的界面化}"),
        (r"\section{热力进度、褐变与结壳}", r"\section{进度与表面品质的演化}"),
        (r"\section{表面—冷点两节点与内部热阻}", r"\section{两节点模型与内部热阻}"),
    ],
    "ch05.tex": [
        (r"\chapter{估计病态与稳态不可辨识}", r"\chapter{内部热阻的不可辨识性}"),
        (r"\section{可安装通道与已经接到跟踪器的量}", r"\section{可安装观测的范围}"),
        (r"\section{内部热阻的灵敏度结构}", r"\section{热阻估计的灵敏度结构}"),
        (r"\section{平衡观测灵敏度为零}", r"\section{稳态观测下的不可辨识}"),
        (r"\section{短时激励的信息增益与标量跟踪器}", r"\section{短时激励与在线跟踪}"),
    ],
    "ch06.tex": [
        (r"\section{信息动作的三条判据}", r"\section{信息动作的定义}"),
        (r"\section{相变变号与对流的第二灵敏度方向}", r"\section{第二灵敏度方向的构造}"),
        (r"\section{四十秒窗内冷点几乎不动}", r"\section{探针窗口对冷点的约束}"),
        (r"\section{开环、腔温、无探针与对偶的停机几何}", r"\section{四种策略的停机方式}"),
    ],
    "ch07.tex": [
        (r"\chapter{因果路径与测量隔离的安全投影}", r"\chapter{因果路径与安全隔离}"),
        (r"\section{干预、路径积分与可更新参数}", r"\section{干预分析与参数更新范围}"),
        (r"\section{冷点潜热、表面蒸发与结壳热阻}", r"\section{蒸汽作用的三条路径}"),
        (r"\section{品质回路与硬测量安全集}", r"\section{品质回路与硬测量的分离}"),
    ],
    "ch08.tex": [
        (r"\chapter{主对照：厚度几何、档位交叉与探针方差}", r"\chapter{厚度、档位与探针的对照结果}"),
        (r"\section{S1 主对照与档位研究两套格子}", r"\section{对照试验的格子设计}"),
        (r"\section{薄件过熟、厚件不足}", r"\section{厚度对停机结果的主导作用}"),
        (r"\section{蒸烤组合交叉下的允许集合}", r"\section{档位变化的作用范围}"),
        (r"\section{探针降低的是热阻方差}", r"\section{探针的信息收益}"),
        (r"\section{蒸汽潜热项的厚度符号翻转}", r"\section{潜热项随厚度的符号变化}"),
        (r"\section{停机偏差的分布与热图}", r"\section{停机偏差的总体形态}"),
    ],
    "s1_tables.tex": [
        (r"\subsection{日志交叉表}", r"\subsection{交叉表的读法}"),
    ],
    "s1_extra.tex": [
        (r"\subsection{能量、方差与褐变}", r"\subsection{能量、方差与褐变的伴随量}"),
    ],
    "ch11.tex": [
        (r"\chapter{网格收敛与冷点格子}", r"\chapter{网格收敛与冷点取法}"),
        (r"\section{停机偏差对格子数敏感}", r"\section{网格密度对停机偏差的影响}"),
        (r"\section{八格到十六格：30 mm 对偶翻号}", r"\section{加密引起的策略符号变化}"),
        (r"\section{种子 7 上从 8 到 32 的加密}", r"\section{单条轨迹的逐级加密}"),
        (r"\section{主对照固定在十六条}", r"\section{主对照的网格选取}"),
    ],
    "ch12.tex": [
        (r"\section{食品名、含水与非均质的边际}", r"\section{食品属性的边际贡献}"),
        (r"\section{探针、遮挡、质量、脂肪与开门}", r"\section{边界与结构扰动的影响}"),
        (r"\section{种子 7 轨迹上的含水三档}", r"\section{含水变化的轨迹复核}"),
    ],
    "ch13.tex": [
        (r"\chapter{宽格子、集合散布与时域延长}", r"\chapter{先验宽度、集合散布与时域}"),
        (r"\section{更宽先验下的停机分位}", r"\section{多种子下的停机分位}"),
        (r"\section{集合样本的停机散布}", r"\section{集合积分中的停机散布}"),
        (r"\section{厚件走到设计线需要延长时域}", r"\section{厚件到达设计线的时域需求}"),
        (r"\section{档位研究中的初温与含水}", r"\section{初温与含水的补充对照}"),
    ],
    "ch14.tex": [
        (r"\chapter{二维截面、边界关联与尺度诊断}", r"\chapter{冷点位置与过程尺度}"),
        (r"\section{显式截面上冷点偏离几何中心}", r"\section{冷点对几何中心的偏离}"),
        (r"\section{通道关联与核内换热}", r"\section{对流通道与内部换热}"),
        (r"\section{薄件走完尺度、厚件停在 0.12}", r"\section{薄件与厚件的尺度完成程度}"),
        (r"\section{管温平衡点与削减阈值}", r"\section{加热器工作点与安全阈值}"),
        (r"\section{干壳代理随排汽与时间}", r"\section{干壳形成的条件}"),
    ],
    "ch15.tex": [
        (r"\chapter{轨迹族、界面通量与机理图谱}", r"\chapter{典型轨迹与作用机理}"),
        (r"\section{同一初值上四条策略的轨迹}", r"\section{四种策略的过程对比}"),
        (r"\section{三种厚度的过程差异}", r"\section{厚度变化下的过程差异}"),
        (r"\section{蒸、烤、组合的执行量轨迹}", r"\section{三档模式的执行过程}"),
        (r"\section{厚度--时间场与插值色带}", r"\section{温度场随时间的演化}"),
        (r"\section{三条路径的时间展开}", r"\section{因果路径随时间的展开}"),
        (r"\section{界面温差、潜热项与算子残差}", r"\section{界面通量与残差诊断}"),
    ],
    "ch09.tex": [
        (r"\chapter{数值核与三维交互演示}", r"\chapter{数值实现与交互演示}"),
        (r"\section{十六条控制体与评分循环}", r"\section{评分核的离散实现}"),
        (r"\section{状态流读回可见零件}", r"\section{腔体可视化}"),
        (r"\section{档位、对照策略与开门}", r"\section{交互对照的读法}"),
        (r"\section{演示地址与日志字段}", r"\section{公开演示与日志导出}"),
    ],
    "ch10.tex": [
        (r"\section{交叉表上已经站住的事实}", r"\section{主要结论}"),
        (r"\section{加热、蒸汽、排汽与风机}", r"\section{执行器在产品上的对应}"),
        (r"\section{点估计偏差与 Fourier 几何}", r"\section{估计偏差与厚度限制}"),
        (r"\section{交互页与默认种子 7}", r"\section{演示条件的读法}"),
        (r"\section{可安装通道、后验写回与型式试验}", r"\section{局限与后续工作}"),
        (r"\section{产品叙述与厨房核对}", r"\section{对产品使用的启示}"),
    ],
}


def main() -> None:
    missing = 0
    for name, pairs in REPLACEMENTS.items():
        path = ROOT / name
        text = path.read_text(encoding="utf-8")
        for old, new in pairs:
            if old not in text:
                print("MISSING", name, old)
                missing += 1
            else:
                text = text.replace(old, new, 1)
        path.write_text(text, encoding="utf-8")
        print("updated", name)
    if missing:
        raise SystemExit(f"{missing} titles not found")


if __name__ == "__main__":
    main()
