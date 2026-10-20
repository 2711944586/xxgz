# ACTS-MCDT

东北大学《信息感知》课程报告。学号 20241334，姓名庄颂，班级信息 2402。

一体机真正能改的只有加热、蒸汽、排汽和风机。报告把它当作信息感知问题：稳态观测对内部热阻的灵敏度为零，控制器必须离开平衡，用短时探针购买辨识度。设计线 \(\alpha_m=0.85\)（恒温冷点 \(F=3.794\,\mathrm{min}\)）是策略比较的零点。

交互实验台：https://2711944586.github.io/xxgz/

## 核心结果

| 问题 | 答案 | 证据 |
|---|---|---|
| 降阶的代价 | 外部膜热阻恢复到 \(2.3\) 倍内，内部热阻落到 \(23\)–\(363\) 倍；残差是结构性的（温差非单调） | `identify_reduction.py`、表 3.2 |
| 一维核丢了什么 | 一维与二维冷点只差 \(0.31\,\mathrm{K}\)；\(13.75\,\mathrm{mm}\) 是半厚距离；冷点是占全场 \(8.3\%\) 的平台 | `crosscheck_dimensions.py`、表 3.3 |
| 信息动作是否奏效 | S1 的对偶 \(4860\) 行全部把方差降到 \(0.224\)；档位研究只有三分之二，未更新全在蒸档 | 表 5.2、图 5.1 |
| 瓶颈在估计还是决策 | EKF 把偏差收窄一半、方差连续，但停机不变；MPC 最省能量却在 \(30\,\mathrm{mm}\) 提前 \(488\,\mathrm{s}\) 停机 | `run_estimators.py`、`run_mpc.py` |
| 厚度把什么平移 | 设计线沿厚度轴依次右移：腔温 \(16\)、开环 \(20\)–\(25\)、无探针 \(30\)–\(35\)、对偶 \(30\)–\(45\,\mathrm{mm}\) | `run_surfaces.py`、图 5.2 |

## 两套数值核

同一个十六条积分器带两套开关，项目都用过，日志按代际记录：

| 代际 | 用于 | 开关 |
|---|---|---|
| `baseline` | S1/S0/S2、第 5 章前五节、主表 | 腔体空气、水箱、门互锁、结壳反馈关闭；探针窗外蒸汽阀关闭 |
| `display` | 档位研究、演示页、Antoine 对照、网格表 | 腔温腔湿积分；蒸汽压差进潜热；结壳乘回导热；蒸汽回 \(0.15\) |

`src/acts_mcdt/physics.py` 顶部定义 `BASELINE` 与 `DISPLAY`，`rollout(..., generation="display")` 切换。**同一张表不混用两代核**；`results/logs/MANIFEST.json` 逐条记录代际。

## 复现

```powershell
$env:PYTHONPATH="src"
python scripts/verify_logs.py       # 15 个抽样格子，全部应复现
python -m pytest tests -q           # 契约测试
python scripts/run_surfaces.py      # 连续参数曲面，约 8.2 万次积分
python scripts/identify_reduction.py
python scripts/crosscheck_dimensions.py
python scripts/run_estimators.py
python scripts/run_mpc.py
python scripts/build_demo_dataset.py  # 演示数据：75 条轨迹 + 参数面 + 契约
```

图件重绘：`scripts/draw_results.py`、`draw_fields.py`、`draw_dist.py`、`draw_traces.py`、`draw_merge.py`、`draw_concept.py`、`draw_mechanisms_v2.py`、`draw_last.py`。共享样式在 `scripts/figstyle.py`。

## 目录

```
acts-mcdt/
├── submit/                 课程提交件（学号+姓名+班级）
├── monograph/              论文 LaTeX 源
│   ├── book.tex            主文件（两次 xelatex，jobname=ACTS-MCDT）
│   ├── ch1.tex–ch6.tex
│   ├── refs.tex
│   ├── app_symbols/discrete/trace/scales/tables.tex   附录 A–E
│   ├── gab_subset.tex
│   └── figures/            封面、水印、封底与三张原图
├── demo/                   浏览器实验台（Vite + React + Three.js）
│   ├── public/data/        traces.bin（75 条轨迹、31050 帧、16 层温度场）
│   │                       surfaces.json（7628 格参数面）manifest.json（通道与缩放）
│   ├── public/dataset.json 数据契约：模式、代际、指纹、模型边界
│   └── src/scene/          三维零件：外壳/门体/加热/风机/蒸汽/搁架/传感器
│                           console.js 数显面板与温控主板（屏上读数接同一帧日志）
├── src/acts_mcdt/          数值核
│   ├── physics.py          rollout()，两套代际开关
│   ├── estimator.py        两节点辨识 + 双状态 EKF
│   ├── fast.py             baseline 的 numba 快路径
│   └── propositions.py     命题核对
├── tests/                  命题测试 + 代际契约测试
├── scripts/                战役、绘图、Word 导出、日志校验
├── results/logs/           正文数字以这里为准；MANIFEST.json 记录代际
├── results/figures/paper/  正文插图（47 张，与正文引用一一对应）
└── results/figures/demo/   演示页截图与爆炸动画（capture-demo.cjs 生成）
```

## 编译与导出

在 `monograph/` 下两次 `xelatex -interaction=nonstopmode -jobname=ACTS-MCDT book.tex`。

Word 由 `scripts/build_docx.py` 从 LaTeX 导出：正文双栏（每栏 \(87.5\,\mathrm{mm}\)、页边距 \(17.5\,\mathrm{mm}\)，与 PDF 几何一致），前置单栏，附录继承正文双栏。OMML 原生公式、三线表、可编辑插图。该脚本调用本机 Word 刷新目录页码，需要 Windows + Word + `pywin32`。

## 演示

`.\start-demo.ps1` 或 `start-demo.bat`。数据由 `$env:PYTHONPATH="src"; python scripts/build_demo_dataset.py` 生成，默认种子 7、肉糜 \(30\,\mathrm{mm}\)、初温 \(8^\circ\mathrm{C}\)、含水 \(0.72\)、组合档、对偶，按 \(8\,\mathrm{s}\) 抽样，来自 `display` 代际。

页面分五栏：运行、孪生、探针、对照、响应面。回放覆盖五种策略 × 三种档位 × 五种厚度；每帧带 31 个核通道与 16 层厚度温度场，三维食物按场着色。响应面另用 `baseline` 代际的 48 种子逐格聚合，与回放不混读。

页面操作：拖拽旋转、滚轮缩放、点击零件看说明；`Space` 播放/暂停，`←/→` 步进（`Shift` 十帧），`1`–`5` 切栏，`S` 剖切。导出的 CSV 含 31 列与 16 层温度。

孪生栏的零件包含数显面板与温控主板：面板屏上只显示腔温、加热/蒸汽/风机三个指令、水位、用时与进度，**不显示冷点**；爆炸分解把它们作为两层单独拆出并标注。图案与动画由 `node scripts/capture-demo.cjs` 生成到 `results/figures/demo/`，再用 `python scripts/make_media.py` 编码成 PDF/Word 可播放的序列；两脚本需要本地已启动演示服务（默认 `http://127.0.0.1:4180`）。

## 已知边界

- `r_proxy` 使用表面与冷点的真值温差；实施到机器上要改成可安装通道。
- 演示版核的蒸汽压驱动裁在 \([-0.4,0.4]\,\mathrm{bar}\)，\(60.1\%\) 的步数贴下界。第 5.8 节那组结果是**符号结论**，不是标定过的灵敏度。
- 初始含水在家用工况下饱和，是死轴；要让含水成为有效因子，须把工况推到表面含水低于 \(0.45\) 的区域。
- 设计线 \(\alpha_m=0.85\) 不是认证阈值，微生物初始数量不进入状态。
- 公开等温线清洁子集以淀粉类为主，肉类条数为 0，测定多数不超过 \(60^\circ\mathrm{C}\)。
