# ACTS-MCDT

智能蒸烤一体机的自主认知系统。仓库按规划、正文、数值核、结果、演示分开。腔体里的四个执行量是加热、蒸汽、排汽和气流。

## 主线

被动观测看不到内部热阻。评分核在一维十六条控制体上比较四种策略。对偶策略在 150–190 s 做一次固定探针。停机进度只在停机时刻读取。公开等温线只约束淀粉类活度，而且测定不超过 60 °C。

## 目录

- `outline/` 规划稿。源文件 `main.tex`，已编译的 PDF 是 `outline.pdf`。
- `monograph/` 正文。源文件 `book.tex`，PDF 是 `book.pdf`，同一正文的 Word 是 `ACTS-MCDT.docx`。公式编号以 PDF 为准。
- `refs.tex` 规划稿和正文共用的文献入口。
- `src/acts_mcdt/` 评分核。一维十六个控制体，不改物理后再跑战役。
- `tests/` 命题核对。
- `scripts/run_campaign.py` 写出 S1 的 `results/logs/` 和由该日志画出的图。这 19440 行已经落盘。
- `scripts/run_s0_s2.py` 写出网格减半的 18 条配对和边界扫描的 480 行，以及 `S0_grid.png`、`D15_occlusion.png`、`S2_factors.png`。
- `scripts/build_docx.py` 由正文源文件生成 `monograph/ACTS-MCDT.docx`。
- `results/logs/` 战役摘要、命题核对和种子 7 轨迹。
- `results/figures/` 由这些日志画出的图，以及演示截屏。
- `demo/` 浏览器演示。十六条控制体与种子 7 的日志对齐到写入精度。
- `external/gab-fit.xlsx` 已读入的公开等温线拟合。
- `requirements.txt` 评分核、作图和 Word 生成用的 Python 依赖。

## 编译正文

在 `monograph` 下执行两次：

```
xelatex -interaction=nonstopmode book.tex
xelatex -interaction=nonstopmode book.tex
```

Word 在仓库根目录生成：

```
python scripts/build_docx.py
```

规划稿在 `outline` 下对 `main.tex` 执行两次 XeLaTeX。它引用上一级的 `refs.tex`。

## 演示

```
cd demo
npm install
npm run dev
```

默认条件是种子 7、肉糜、厚度 30 mm、初温 8 °C、含水 0.72。页面上的表面、冷点和估计与 `results/logs/demo_seed7_dual.csv` 一致。`node check_seed7.mjs` 用相对路径读这张表。

## 边界

19440 行是同一数值过程的样本。另有六份日志：`s1_wide.jsonl` 是 648 个格子各 30000 个种子的分位；`ensemble.json` 是同一核的成员散布，没有分析步；`t2_section.json` 是 24 乘 16 的显式截面；`t3_boundary.json` 是通道关联，没有接进核；`mpc_horizon.json` 是一个状态下 60 秒、18 个加热点的搜索，不是 CasADi；`operators.json` 是两节点教师上的主干加分支，留出均方误差没有收紧，不是 Fourier 算子或 DeepONet。设计线 0.85 不是认证阈值。
