# ACTS-MCDT

东北大学《信息感知》课程报告配套仓库。学号 20241334，姓名庄颂，班级信息2402。

一体机真正能改的只有加热、蒸汽、排汽和风机。评分核在一维十六条控制体上比较开环、腔温比例、无探针与对偶。对偶策略在 150–190 s 做一次固定探针。停机进度只在停机时刻读取。设计线 \(\alpha_m=0.85\)（恒温冷点 \(F=3.794\,\mathrm{min}\)）是比较零点，不是认证阈值。

## 目录

- `src/acts_mcdt/` 评分核。一维十六个控制体，时间步 2 s，时域 55 min。
- `tests/` 命题核对。
- `scripts/` 战役、图件、Word 导出与演示轨迹导出。
- `results/logs/` 已落盘的战役摘要与种子 7 轨迹。正文数字以这里为准。
- `results/figures/paper/` 正文引用的图；`results/figures/study/` 档位研究附图。
- `monograph/` 正文。源文件 `book.tex` 与 `ch01.tex`–`ch15.tex`。PDF 用 `xelatex -jobname=ACTS-MCDT` 生成 `ACTS-MCDT.pdf`。Word 由该 PDF 逐页嵌入，版式与 PDF 相同。
- `demo/` 浏览器演示。读取 `demo/public/catalog.json`，不在浏览器里重跑积分。`catalog.json` 必须留在 `demo/public/`。
- `outline/` 规划稿，不进入提交 PDF。
- `external/gab-fit.xlsx` 已读入的公开等温线拟合。
- `.github/workflows/pages.yml` 把 `demo/` 构建并发布到 GitHub Pages。
- 提交副本：仓库根目录 `20241334庄颂信息2402.pdf` 与 `.docx`。课程中文文件名副本同时写在仓库根目录与 `monograph/`。

## 编译正文

在 `monograph` 下执行两次：

```
xelatex -interaction=nonstopmode -jobname=ACTS-MCDT book.tex
xelatex -interaction=nonstopmode -jobname=ACTS-MCDT book.tex
```

Word 必须在 PDF 之后生成，按页嵌入该 PDF：

```
python scripts/build_docx.py
```

提交文件名：`20241334庄颂信息2402.pdf` 与 `.docx`（由脚本同时写出课程中文文件名副本）。

## 演示

本地：仓库根目录执行 `.\start-demo.ps1` 或双击 `start-demo.bat`。默认条件是种子 7、肉糜、厚度 30 mm、初温 8 °C、含水 0.72、组合档、对偶策略。1680 s 冷点 70.21 °C、进度 0.558；停机约 1866 s，\(e_\alpha=+0.145\)。

页面上可以切换蒸/烤/组合与四种策略，叠一条对照策略（虚线冷点与进度），把门打开或关上，并跳到起始、探针窗、1680 s 品质段和停机。15/30/50 mm 三档芯片只切换已经写出的数组。左栏给出本条轨迹的 \(e_\alpha\) 与探针是否把方差降到 0.224；页面按 8 s 抽样显示停机 1864 s，核日志是 1866 s。红虚线是设计线 0.85。开门只改铰链，不改已经写出的温度数组。

静态部署：推送到 `main` 后，Actions 工作流构建 `demo/` 并发布。仓库 Settings → Pages 选择 GitHub Actions 作为源。公开地址

https://2711944586.github.io/xxgz/

仓库 https://github.com/2711944586/xxgz 。`vite.config.js` 使用相对基址 `./`。

## 数字从哪里来

S1 共 19440 行，档位研究 11664 行。种子 7、肉糜、30 mm、组合、对偶：方差 192 s 由 0.64 降到 0.224；停机 1866 s，能量 1864。50 mm 对偶组合中位 \(e_\alpha=-0.782\)，55 min 时 Fourier 数 0.12。网格从 8 到 16 会把 30 mm 对偶停机偏差翻号（\(\Delta e\approx 0.227\)）。加热器平衡点 196.5 °C，削减阈值 230 °C。

重跑战役调用 `scripts/run_campaign.py` 与 `scripts/run_study.py`，耗时以小时计。图件重绘：`python scripts/draw_expansion.py`；只重绘截面、S2 横条与 Fo/Bi 时加 `--fast`。

## 边界

公开等温线的清洁子集以淀粉类为主，肉类条数为 0，测定多数不超过 60 °C。\(r_{\mathrm{proxy}}\) 使用表面与冷点的真值温差；实施到机器上要改成可安装通道。微生物初始数量不进入状态。设计线不是认证阈值。
