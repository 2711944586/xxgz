# ACTS-MCDT

面向非均质食品热加工过程的自主认知系统。正文是一篇技术专著，源文件在 `delivery/book/`。PDF 由 XeLaTeX 生成，公式编号以 PDF 为准。

## 主线

被动观测看不到内部热阻。评分核在一维十六条控制体上比较四种策略。对偶策略在 150–190 s 做一次固定探针。停机进度只在停机时刻读取。公开等温线只约束淀粉类活度，而且测定不超过 60 °C。

## 目录

- `delivery/book/` 专著源文件。编译命令见下。
- `src/acts_mcdt/` 评分核。
- `results/logs/` 已落盘的战役摘要、命题核对和种子 7 轨迹。
- `results/figures/` 由这些日志画出的图。
- `demo/` 浏览器演示。十六条控制体与种子 7 的日志对齐到写入精度。
- `external/gab-fit.xlsx` 已读入的公开等温线拟合。

## 编译

在 `delivery/book` 下执行两次：

```
xelatex -interaction=nonstopmode book.tex
xelatex -interaction=nonstopmode book.tex
```

## 演示

```
cd demo
npm install
npm run dev
```

默认条件是种子 7、肉糜、厚度 30 mm、初温 8 °C、含水 0.72。页面上的表面、冷点和估计与 `results/logs/demo_seed7_dual.csv` 一致。

## 边界

19440 行是同一数值过程的样本。集合滤波、神经算子和预测控制求解器没有在这批日志里运行。设计线 0.85 不是认证阈值。
