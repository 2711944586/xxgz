# ACTS-MCDT

东北大学《信息感知》课程报告。学号 20241334，姓名庄颂，班级信息 2402。

一体机真正能改的只有加热、蒸汽、排汽和风机。评分核在一维十六条控制体上比较开环、腔温比例、无探针与对偶。对偶策略在 150–190 s 做一次固定探针。停机进度只在停机时刻读取。设计线 \(\alpha_m=0.85\)（恒温冷点 \(F=3.794\,\mathrm{min}\)）是比较零点。

交互实验台：https://2711944586.github.io/xxgz/

## 目录

```
acts-mcdt/
├── submit/                 课程提交件（学号+姓名+班级）
│   ├── 20241334庄颂信息2402.pdf
│   └── 20241334庄颂信息2402.docx
├── monograph/              论文 LaTeX 源
│   ├── book.tex            主文件（两次 xelatex，jobname=ACTS-MCDT）
│   ├── ch01.tex–ch15.tex
│   ├── refs.tex
│   ├── figures/            封面 cover.png、水印 bg.png、封底 back.png
│   ├── figures/_src_*.png  提交的三张原图
│   └── ACTS-MCDT.pdf       编译产物
├── demo/                   浏览器实验台（Vite + Three.js）
│   └── public/catalog.json 已写出的状态流，页面不重跑积分
├── src/acts_mcdt/          数值核
├── tests/                  命题核对
├── scripts/                战役、绘图、封面、导出 Word
├── results/logs/           正文引用的数字以这里为准
├── results/figures/paper/  正文插图
├── results/figures/study/  档位研究附图
├── external/gab-fit.xlsx   已读入的公开等温线拟合
└── .github/workflows/pages.yml
```

仓库根目录的 `start-demo.ps1` / `start-demo.bat` 启动本地演示。

## 提交文件

课程要求未压缩 PDF 与 Word，文件名为学号+姓名+班级。两份都在 `submit/`：

- `submit/20241334庄颂信息2402.pdf`
- `submit/20241334庄颂信息2402.docx`

PDF 由 XeLaTeX 排出，是排版原件。Word 由 `scripts/build_docx.py` 从 LaTeX 导出为原生可编辑 DOCX：正文宋体 12 点两端对齐、1.5 倍行距、首行缩进 2 字；章题「第 n 章」与章名分行居中；图注楷体、三线表、OMML 公式（Cambria Math）和插图均可改，不是把 PDF 整页转成图片。目录与页眉用仿宋，点线领袖，页码由本机 Word 回填后写入文件，点击条目可跳转。封面、封底用提交的原图铺满页眉层，不留白边；正文水印用原图 `bg.png` 衬在文字后面，不影响选中和编辑。演示截图在 PDF 与 Word 里都收成两列小图。

## 编译正文

在 `monograph/` 下执行两次：

```
xelatex -interaction=nonstopmode -jobname=ACTS-MCDT book.tex
xelatex -interaction=nonstopmode -jobname=ACTS-MCDT book.tex
```

封面、封底与正文水印只用提交的三张原图（`_src_cover.png`、`_src_back.png`、`_src_bg.png`），画面不改。打印件按 A4 400 DPI 放大：

```
python scripts/draw_covers.py
```

然后在仓库根目录导出 Word，并覆盖 `submit/`：

```
python scripts/build_docx.py
```

## 演示

本地：仓库根目录执行 `.\start-demo.ps1` 或双击 `start-demo.bat`。默认条件是种子 7、肉糜、厚度 30 mm、初温 8 °C、含水 0.72、组合档、对偶策略。页面按 8 s 抽样显示停机 1864 s；核日志是 1866 s，\(e_\alpha=+0.145\)。1680 s 冷点 70.21 °C、进度 0.558。50 mm 对偶组合停在 3298 s，\(e_\alpha=-0.782\)。

`catalog.json` 必须留在 `demo/public/`。开门只改铰链，不改已经写出的温度数组。红虚线是设计线 0.85。

推送到 `main` 后，Actions 构建 `demo/` 并发布到 GitHub Pages。`vite.config.js` 使用相对基址 `./`。仓库 https://github.com/2711944586/xxgz 。

## 数字从哪里来

S1 共 19440 行，档位研究 11664 行。种子 7、肉糜、30 mm、组合、对偶：方差 192 s 由 0.64 降到 0.224；停机 1866 s，能量 1864。50 mm 对偶组合中位 \(e_\alpha=-0.782\)，55 min 时 Fourier 数 0.12。网格从 8 到 16 会把 30 mm 对偶停机偏差翻号（\(\Delta e\approx 0.227\)）。加热器平衡点 196.5 °C，削减阈值 230 °C。

命题核对（需把 `src` 加入 `PYTHONPATH`）：

```
$env:PYTHONPATH="src"
python tests/test_propositions.py
```

重跑战役调用 `scripts/run_campaign.py` 与 `scripts/run_study.py`，耗时以小时计。图件重绘：`python scripts/draw_expansion.py`。

## 边界

公开等温线的清洁子集以淀粉类为主，肉类条数为 0，测定多数不超过 60 °C。\(r_{\mathrm{proxy}}\) 使用表面与冷点的真值温差；实施到机器上要改成可安装通道。微生物初始数量不进入状态。设计线不是认证阈值。
