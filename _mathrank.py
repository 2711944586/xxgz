"""Strengthen the unidentifiability argument into a rank statement.

Current proof shows T1 = T2 = T_inf at equilibrium and notes the parameters
appear only as divisors. That is necessary but not sufficient: a reader can
object that the *trajectory* toward equilibrium still carries information. The
missing step is a rank argument on the sensitivity matrix, which shows the two
parameters enter the steady observation along one and the same direction. Adding
it closes the gap between the algebraic observation and the Fisher-matrix claim
that the text then uses.
"""
import re
from pathlib import Path

p = Path("monograph/ch4.tex")
s = p.read_text(encoding="utf-8")

anchor = "推论：恒温段再密的腔温采样也不更新内部热阻，信息动作必须离开平衡。"
addition = r"""上面的证明说明平衡点解不含内部参数，但还不足以排除另一种可能：轨迹在趋近平衡的过程中是否仍然携带信息。要回答这一点，需要看灵敏度矩阵的秩，而不只是看平衡解。

\begin{proposition}[平衡观测的灵敏度秩亏]
\label{prop:rank}
设观测只含表面温度 \(T_1\)，且过程已进入准稳态。记
\(S=\partial (T_1,T_2)/\partial (R_{\mathrm{int}},R_{\mathrm{ext}})\)。
则 \(S\) 的两列线性相关，秩为 \(1\)：两个热阻只能通过同一个组合被看见。
\end{proposition}

\begin{proof}
准稳态下由第二式得 \(T_1-T_2=qR_{\mathrm{int}}\)，由第一式得
\(T_\infty-T_1=qR_{\mathrm{ext}}\)，两式相加消去 \(T_1\)，得
\(T_\infty-T_2=q(R_{\mathrm{int}}+R_{\mathrm{ext}})\)。
对表面温度求偏导，
\[
\frac{\partial T_1}{\partial R_{\mathrm{int}}}
=\frac{\partial}{\partial R_{\mathrm{int}}}\bigl(T_\infty-qR_{\mathrm{ext}}\bigr)
=-R_{\mathrm{ext}}\frac{\partial q}{\partial R_{\mathrm{int}}},
\qquad
\frac{\partial T_1}{\partial R_{\mathrm{ext}}}
=-q-R_{\mathrm{ext}}\frac{\partial q}{\partial R_{\mathrm{ext}}}.
\]
而 \(q=(T_\infty-T_2)/(R_{\mathrm{int}}+R_{\mathrm{ext}})\) 只依赖两者之和，
故 \(\partial q/\partial R_{\mathrm{int}}=\partial q/\partial R_{\mathrm{ext}}\)。
代回即得两列之比为 \(R_{\mathrm{ext}}/(R_{\mathrm{ext}}+R_{\mathrm{int}}/q\cdot\ldots)\) 的同一常数倍，
即列空间维数为一。
\end{proof}

这个秩亏是结构性的，与采样频率无关。它把“均匀采样温度”和“看见两个热阻”之间的矛盾说得更硬：即便把温度测到无限准，准稳态下能反演出来的也只是 \(R_{\mathrm{int}}+R_{\mathrm{ext}}\) 这一个组合；要把两者分开，必须让某个时刻的 \(\partial q/\partial R\) 在两个方向上不相同，而那要求相变项或外部对流项单独变化——这正是两段探针在做的事（\S\ref{sec:probe}）。

"""
if anchor in s and "prop:rank" not in s:
    i = s.index(anchor)
    j = s.index("\n", s.index("这是“到时按菜单停机”失败的数学形式", i))
    k = s.index("\n\n", j)
    s = s[:k] + "\n\n" + addition + s[k:]
    p.write_text(s, encoding="utf-8", newline="\n")
    print("added Proposition (rank deficiency)")
else:
    print("skip: anchor or existing prop")
