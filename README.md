# 基于信息感知的智能蒸烤一体机（ACTS-MCDT）

东北大学《信息感知》课程报告。学号 **20241334**，姓名 **庄颂**，班级 **信息 2402**。

仓库根目录为本目录（`acts-mcdt/`）；远程地址：<https://github.com/2711944586/xxgz>。

报告把家用蒸烤一体机写成信息感知问题：机器真正能改的只有**加热、蒸汽、排汽、风机**四个执行量，而决定熟度的冷点温度、内部含水与反应进度都不在这四个量上。稳态观测对内部热阻的灵敏度为零，控制器必须离开平衡，用短时探针购买辨识度。设计线 \(\alpha_m=0.85\)（恒温冷点 \(F=3.794\,\mathrm{min}\)）是全部策略比较的零点。

- **交付物**：`submit/20241334庄颂信息2402.pdf`（81 页）与 `submit/20241334庄颂信息2402.docx`（可编辑，含原生 OMML 公式与可编辑插图）
- **交互实验台**：<https://2711944586.github.io/xxgz/>

---

## 目录结构

```
acts-mcdt/
├── submit/                  课程交付物（唯一出口，只放这两份成品）
│   ├── 20241334庄颂信息2402.pdf
│   └── 20241334庄颂信息2402.docx
├── monograph/               LaTeX 源（只有 .tex 与 figures/，不放编译产物）
│   ├── book.tex             主文件：贯穿全书，两次 xelatex，jobname=ACTS-MCDT
│   ├── preamble.tex         版式、字体、宏包
│   ├── ch1.tex – ch6.tex    正文六章
│   ├── app_symbols.tex      附录 A 符号、单位与日志字段
│   ├── app_discrete.tex     附录 B 一维工程核的离散格式
│   ├── app_trace.tex        附录 C 种子 7 轨迹抽样
│   ├── app_scales.tex       附录 D 用已定常数算出的尺度
│   ├── app_tables.tex       附录 E 交叉表全文（入口）
│   ├── s1_tables.tex        附录 E 主对照 S1 明细表
│   ├── s1_extra.tex         附录 E 补充表
│   ├── gab_tables.tex       附录 E 公开等温线拟合记录
│   ├── gab_subset.tex       附录 E 等温线子集
│   ├── refs.tex             参考文献（22 条）
│   └── figures/             封面、封底、水印底图
│       └── src/             上述三张图的原始大图（draw_covers.py 的输入）
├── build/                   本地 LaTeX 编译产物（忽略，不提交，可随时重建）
├── src/acts_mcdt/           数值核
│   ├── physics.py           rollout()，baseline / display 两套代际开关
│   ├── cavity.py            腔体边界与执行量
│   ├── estimator.py         两节点辨识 + 双状态 EKF
│   ├── fast.py              baseline 的 numba 快路径（可选依赖）
│   └── propositions.py      命题核对
├── tests/                   51 个命题与契约测试
├── scripts/                 战役、绘图、导出、校验（见下表）
│   └── word_qa/             Word 目录、标题页码检查
├── results/
│   ├── logs/                正文数字以这里为准；MANIFEST.json 记录代际
│   └── figures/
│       ├── paper/           正文插图（PNG；部分图另有同名 PDF 矢量版）
│       └── demo/            演示页截图与爆炸分解动画帧
├── demo/                    浏览器实验台（Vite + React + Three.js）
│   ├── public/data/         traces.bin、surfaces.json、manifest.json
│   ├── public/dataset.json  数据契约：模式、代际、指纹、模型边界
│   └── src/scene/           三维零件：外壳/门体/加热/风机/蒸汽/搁架/传感器
├── external/                外部数据（gab-fit.xlsx）
├── .github/workflows/       GitHub Pages 部署（交互实验台）
├── requirements.txt         Python 依赖与工具链说明
├── requirements-optional.txt 可选的 Numba / PyTorch 依赖
└── .gitignore
```

**目录职责**：`monograph/` 保存 LaTeX 源码及封面原图，`build/` 保存本地可重建的编译产物（已忽略），`submit/` 是对外交付的 PDF 与 DOCX，`results/` 保存可复现日志和图件。临时 Word 分页报告写入已忽略的 `results/word_qa/`。

---

## 构建

### 只出 PDF

```powershell
powershell -ExecutionPolicy Bypass -File scripts/build_pdf.ps1
```

需要 XeLaTeX（MiKTeX 或 TeX Live）在 PATH 上。脚本跑两遍 xelatex（第一遍填 `.toc`/`.aux`，第二遍解出目录与全部 `\ref`），产物写到 `build/ACTS-MCDT.pdf`，并在结束时检查日志中是否还有重复标签、未定义引用或缺字。

### 出 PDF + Word

```powershell
powershell -ExecutionPolicy Bypass -File scripts/build_pdf.ps1   # 先有 PDF
python scripts/build_docx.py                                     # 再把 PDF 一起归位
```

`build_docx.py` 的链路是 **LaTeX → 预处理 → pandoc → DOCX → 原生 OOXML 后处理**：

1. 展平 `book.tex`（展开 `\input`、替换 `\ref`/`\cite`、公式转 `\[...\]`）
2. 预处理掉 pandoc 不认的宏：`\resizebox` 剥壳、`\animategraphics` 换静态帧、自定义列类型 `Y` 换 `p{6.2cm}`、`^\circ\mathrm{C}` 换 `\text{°C}`
3. pandoc 转 docx（公式落成原生 OMML，不是图片）
4. python-docx 后处理：双栏版式、三线表、图注编号、页眉页脚、水印、目录
5. 用 Word COM 刷新目录页码并回写

需要 `pandoc` 在 PATH 上（实测 2.12 可用），以及 Windows + Word（`pywin32`）。

> Word 由 LaTeX 导出，**内容与 PDF 同源**。两份文件的图号、表号、章节号完全一致；分页不同是双栏几何与 Word 排版引擎差异所致，属正常现象。

---

## 复现

安装常用 Python 依赖：

```powershell
python -m pip install -r requirements.txt
```

Numba 快核和 PyTorch 代理训练为可选依赖，按需安装 `requirements-optional.txt`。测试共 51 项；未安装 Numba 时，47 项通过，4 个快核交叉校验会跳过。

```powershell
$env:PYTHONPATH="src"

python -m pytest tests -q              # 命题与代际契约测试
python scripts/verify_logs.py          # 抽样格子按代际复算
python scripts/run_surfaces.py         # 连续参数曲面
python scripts/identify_reduction.py   # 两节点降阶的代价
python scripts/crosscheck_dimensions.py # 一维/二维冷点交叉验证
python scripts/run_estimators.py       # 标量跟踪器 vs EKF
python scripts/run_mpc.py              # 滚动时域决策
python scripts/build_demo_dataset.py   # 演示数据（75 条轨迹 + 参数面 + 契约）
```

重绘图件：`scripts/draw_*.py`，共享样式在 `scripts/figstyle.py`。

Word 目录核对脚本位于 `scripts/word_qa/`。`read_toc.py` 读取当前 DOCX 的目录文字，`get_actual_pages.py` 与 `get_heading_pages.py` 通过 Windows Word COM 读取实际页码，`update_toc.py` 刷新目录页码；结果写入本地忽略目录 `results/word_qa/`。运行 COM 脚本需要 Windows、Word 和 `pywin32`。

---

## 脚本分工

| 分组 | 脚本 | 做什么 |
|---|---|---|
| **构建** | `build_pdf.ps1` | 两次 xelatex → `build/ACTS-MCDT.pdf`，并检查 LaTeX 日志 |
| | `build_docx.py` | LaTeX → pandoc → DOCX，含全部 OOXML 后处理与目录页码回写 |
| | `draw_covers.py` | 封面／封底／水印按 400 dpi 印刷尺寸出图 |
| **战役** | `run_campaign.py` | 主对照 S1 主战役 |
| | `run_study.py` | 档位研究 |
| | `run_s0_s2.py` | S0 网格配对、S2 边界扫描 |
| | `run_surfaces.py` / `run_surfaces_xl.py` | 连续参数曲面（含宽格子版） |
| | `run_pairs.py` | Antoine 压差成对积分 |
| | `run_shell.py` | 壳体散热扫描 |
| | `run_extensions.py` | 集合积分与扩展实验 |
| **辨识与对照** | `identify_reduction.py` | 两节点降阶辨识 |
| | `crosscheck_dimensions.py` | 一维／二维冷点 |
| | `run_coldspot_position.py` | 冷点位置病态性 |
| | `run_estimators.py` | 标量跟踪器与 EKF 对比 |
| | `run_mpc.py` | 滚动时域决策 |
| | `calibrate_ekf.py` | EKF 标定 |
| | `stats_bootstrap.py` | 中位数 bootstrap 区间 |
| | `audit_fast.py` / `verify_logs.py` | 数值核一致性审计、抽样格子复算 |
| | `robust_drive.py` / `robust_proxy.py` | 蒸汽压差裁剪与热阻代理的稳健性 |
| **绘图** | `draw_*.py`（19 个） | 每个脚本产出正文某一组图，见文件头 docstring |
| | `restyle_figures.py` | 战役图重排版 |
| | `make_media.py` | 爆炸分解动画帧编码成 PDF 可播放序列 |
| **演示** | `build_demo_dataset.py` | 写 `demo/public/data/` |
| | `capture-demo.cjs` | 无头浏览器截图（需先启动演示服务） |
| **AI 声明** | `_apply_polish.py` + `_polish_ch*.json` | 逐条复核摘要里声明的 36 处 AI 润色 |

---

## 两套数值核

同一个十六条积分器带两套开关，项目都用过，日志按代际记录：

| 代际 | 用于 | 开关 |
|---|---|---|
| `baseline` | S1/S0/S2、第 5 章前五节、主表 | 腔体空气、水箱、门互锁、结壳反馈关闭；探针窗外蒸汽阀关闭 |
| `display` | 档位研究、演示页、Antoine 对照、网格表 | 腔温腔湿积分；蒸汽压差进潜热；结壳乘回导热；蒸汽回 `0.15` |

`src/acts_mcdt/physics.py` 顶部定义 `BASELINE` 与 `DISPLAY`，`rollout(..., generation="display")` 切换。**同一张表不混用两代核**；`results/logs/MANIFEST.json` 逐条记录代际。

---

## 核心结果

| 问题 | 答案 | 证据 |
|---|---|---|
| 降阶的代价 | 外部膜热阻恢复到 \(2.3\) 倍内，内部热阻落到 \(23\)–\(363\) 倍；残差是结构性的（温差非单调） | `identify_reduction.py`、表 3.2 |
| 一维核丢了什么 | 一维与二维冷点只差 \(0.31\,\mathrm{K}\)；\(13.75\,\mathrm{mm}\) 是半厚距离；冷点是占全场 \(8.3\%\) 的平台 | `crosscheck_dimensions.py`、表 3.3 |
| 信息动作是否奏效 | S1 的对偶 \(4860\) 行全部把方差降到 \(0.224\)；档位研究只有三分之二，未更新全在蒸档 | 表 5.2、图 5.1 |
| 瓶颈在估计还是决策 | EKF 把偏差收窄一半、方差连续，但停机不变；MPC 最省能量却在 \(30\,\mathrm{mm}\) 提前 \(488\,\mathrm{s}\) 停机 | `run_estimators.py`、`run_mpc.py` |
| 厚度把什么平移 | 设计线沿厚度轴依次右移：腔温 \(16\)、开环 \(20\)–\(25\)、无探针 \(30\)–\(35\)、对偶 \(30\)–\(45\,\mathrm{mm}\) | `run_surfaces.py`、图 5.2 |

---

## AI 辅助说明

作业要求“AI 生成内容须标注位置与用途”，摘要页已按下列口径逐项声明，正文不得与之一致性冲突：

1. **文字润色**——第 1–6 章共 36 处句级修改（每章 6 处），只调句式与过渡，不改数字、结论与引用。原句与理据存在 `scripts/_polish_ch123.json` 与 `scripts/_polish_ch456.json`，可用 `scripts/_apply_polish.py` 逐条复核。
2. **绘图辅助**——腔体示意、六环架构图与封面的矢量草图。
3. **前端框架**——第 6 章 WebGL 交互页的脚手架（Vite + React + Three.js）。

数值核、日志与正文引用的每个数字均由本地脚本积分产生，AI 未参与计算；参考文献均来自 `monograph/refs.tex` 的公开条目。

---

## 演示

```powershell
.\start-demo.bat          # 或 .\start-demo.ps1
```

数据由 `$env:PYTHONPATH="src"; python scripts/build_demo_dataset.py` 生成，默认种子 7、肉糜 \(30\,\mathrm{mm}\)、初温 \(8^\circ\mathrm{C}\)、含水 \(0.72\)、组合档、对偶，按 \(8\,\mathrm{s}\) 抽样，来自 `display` 代际。

页面分五栏：运行、孪生、探针、对照、响应面。回放覆盖五种策略 × 三种档位 × 五种厚度；每帧带 31 个核通道与 16 层厚度温度场，三维食物按场着色。响应面另用 `baseline` 代际的 48 种子逐格聚合，与回放不混读。

双栏图件中的演示截图集合（`01_run.png` … `10_board.png`）由 `node scripts/capture-demo.cjs` 生成到 `results/figures/demo/`，再用 `python scripts/make_media.py` 编码成 PDF/Word 可播放的序列；两脚本需要本地已启动演示服务（默认 `http://127.0.0.1:4180`）。

---

## 已知边界

- `r_proxy` 使用表面与冷点的真值温差；实施到机器上要改成可安装通道。
- 演示版核的蒸汽压驱动裁在 \([-0.4,0.4]\,\mathrm{bar}\)，\(60.1\%\) 的步数贴下界。第 5.10 节那组结果是**符号结论**，不是标定过的灵敏度。
- 初始含水在家用工况下饱和，是死轴；要让含水成为有效因子，须把工况推到表面含水低于 \(0.45\) 的区域。
- 设计线 \(\alpha_m=0.85\) 不是认证阈值，微生物初始数量不进入状态。
- 公开等温线清洁子集以淀粉类为主，肉类条数为 0，测定多数不超过 \(60^\circ\mathrm{C}\)。
- `tests/test_kernel_contract.py` 中有 4 个快核交叉校验需要安装可选依赖 `numba`；基础环境不包含它们，其余 47 项测试无需 Numba。
