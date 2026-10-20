import { useEffect, useRef, useState } from "react";

export const SURFACE_DEFS = [
  { id: "LT", title: "厚度 × 初温", third: "t0C", thirdLabel: "初温 °C" },
  { id: "LM", title: "厚度 × 含水", third: "moisture", thirdLabel: "初始含水" },
  { id: "LH", title: "厚度 × 不均匀", third: "hetero", thirdLabel: "夹层类型" },
  { id: "LC", title: "厚度 × 产品档", third: "cook", thirdLabel: "产品档" },
];

export const SURFACE_METRICS = [
  { id: 0, label: "e_α 中位数", domain: [-0.85, 0.15], fmt: (v) => v.toFixed(2), unit: "" },
  { id: 1, label: "停机 / s", domain: [600, 3300], fmt: (v) => Math.round(v), unit: "s" },
  { id: 2, label: "能耗", domain: [700, 3400], fmt: (v) => Math.round(v), unit: "" },
  { id: 3, label: "e_α 标准差", domain: [0, 0.27], fmt: (v) => v.toFixed(3), unit: "" },
];

const HETERO_LABEL = ["均匀", "厚度抖动", "脂肪夹层"];
const COOK_LABEL = { steam: "蒸", bake: "烤", combi: "组合" };

function colorOf(value, domain) {
  const x = Math.min(1, Math.max(0, (value - domain[0]) / (domain[1] - domain[0])));
  const stops = [
    [0.0, [22, 42, 74]],
    [0.24, [40, 84, 128]],
    [0.46, [66, 122, 140]],
    [0.62, [196, 148, 78]],
    [0.82, [216, 112, 62]],
    [1.0, [236, 176, 96]],
  ];
  let i = 0;
  while (i < stops.length - 2 && x > stops[i + 1][0]) i += 1;
  const [p0, c0] = stops[i];
  const [p1, c1] = stops[i + 1];
  const k = p1 === p0 ? 0 : (x - p0) / (p1 - p0);
  const c = c0.map((v, j) => Math.round(v + (c1[j] - v) * k));
  return `rgb(${c[0]},${c[1]},${c[2]})`;
}

function axisLabel(kind, value) {
  if (value == null) return "—";
  if (kind === "cook") return COOK_LABEL[value] || String(value);
  if (kind === "hetero") return HETERO_LABEL[value] ?? String(value);
  if (kind === "moisture") return Number(value).toFixed(2);
  if (kind === "t0C") return `${Math.round(value)}`;
  return String(value);
}

export function SurfaceMap({ surfaces, policy, metric, surface, onSurface, onMetric }) {
  const canvasRef = useRef(null);
  const stripRef = useRef(null);
  const [hover, setHover] = useState(null);

  const grid = surfaces?.grids?.[surface];
  const metricDef = SURFACE_METRICS.find((m) => m.id === metric) || SURFACE_METRICS[0];
  const series = grid?.series?.find((s) => s.policy === policy) || grid?.series?.[0];

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas || !grid || !series) return undefined;
    const paint = () => {
      const dpr = Math.min(window.devicePixelRatio || 1, 2);
      const w = canvas.clientWidth;
      const h = canvas.clientHeight;
      if (!w || !h) return;
      canvas.width = w * dpr;
      canvas.height = h * dpr;
      const ctx = canvas.getContext("2d");
      ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
      ctx.fillStyle = "#0e1418";
      ctx.fillRect(0, 0, w, h);
      const padL = 40;
      const padB = 30;
      const padT = 22;
      const padR = 10;
      const cols = grid.thirdAxis.length;
      const rows = grid.secondAxis.length;
      const cw = (w - padL - padR) / cols;
      const ch = (h - padT - padB) / rows;
      series.rows.forEach((row, ri) => {
        row.forEach((cell, ci) => {
          if (!cell) return;
          const v = cell[metricDef.id];
          ctx.fillStyle = colorOf(v, metricDef.domain);
          ctx.fillRect(padL + ci * cw, padT + ri * ch, Math.ceil(cw) + 0.5, Math.ceil(ch) + 0.5);
        });
      });
      ctx.fillStyle = "#7d8b93";
      ctx.font = "10px 'IBM Plex Mono', monospace";
      ctx.textAlign = "center";
      ctx.textBaseline = "top";
      grid.thirdAxis.forEach((v, i) => {
        if (cols > 12 && i % 2 !== 0) return;
        ctx.fillText(axisLabel(grid.third, v), padL + (i + 0.5) * cw, padT + rows * ch + 6);
      });
      ctx.textAlign = "right";
      ctx.textBaseline = "middle";
      grid.secondAxis.forEach((v, i) => {
        if (rows > 12 && i % 2 !== 0) return;
        ctx.fillText(String(Math.round(v)), padL - 6, padT + (i + 0.5) * ch);
      });
      ctx.textAlign = "left";
      ctx.textBaseline = "top";
      ctx.fillText(SURFACE_DEFS.find((d) => d.id === surface)?.thirdLabel || "", padL, 4);
      ctx.textAlign = "right";
      ctx.fillText("厚度 mm ↓", w - padR, 4);
      return { padL, padT, cw, ch, cols, rows };
    };
    paint();
    const ro = new ResizeObserver(() => paint());
    ro.observe(canvas);
    return () => ro.disconnect();
  }, [grid, series, metricDef, surface]);

  useEffect(() => {
    const canvas = stripRef.current;
    if (!canvas || !grid) return undefined;
    const paint = () => {
      const dpr = Math.min(window.devicePixelRatio || 1, 2);
      const w = canvas.clientWidth;
      const h = canvas.clientHeight;
      if (!w || !h) return;
      canvas.width = w * dpr;
      canvas.height = h * dpr;
      const ctx = canvas.getContext("2d");
      ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
      ctx.fillStyle = "#0e1418";
      ctx.fillRect(0, 0, w, h);
      const pad = 8;
      const gap = 6;
      const rows = grid.secondAxis.length;
      const cols = grid.thirdAxis.length;
      const cellW = (w - pad * 2 - gap * (grid.series.length - 1)) / grid.series.length;
      const rowH = Math.max(1, (h - pad * 2) / rows);
      grid.series.forEach((s, si) => {
        const x0 = pad + si * (cellW + gap);
        s.rows.forEach((row, ri) => {
          row.forEach((cell, ci) => {
            if (!cell) return;
            ctx.fillStyle = colorOf(cell[metricDef.id], metricDef.domain);
            ctx.fillRect(x0 + (ci / cols) * cellW, pad + ri * rowH, cellW / cols + 0.5, rowH + 0.5);
          });
        });
        ctx.fillStyle = s.policy === policy ? "#e7dcc4" : "#6f7d85";
        ctx.font = "9px 'IBM Plex Mono', monospace";
        ctx.textAlign = "center";
        ctx.textBaseline = "top";
        ctx.fillText(s.policy, x0 + cellW / 2, pad + rows * rowH + 2);
      });
    };
    paint();
    const ro = new ResizeObserver(() => paint());
    ro.observe(canvas);
    return () => ro.disconnect();
  }, [grid, metricDef, policy]);

  const onMove = (ev) => {
    const canvas = canvasRef.current;
    if (!canvas || !grid || !series) return;
    const rect = canvas.getBoundingClientRect();
    const padL = 40;
    const padB = 30;
    const padT = 22;
    const cols = grid.thirdAxis.length;
    const rows = grid.secondAxis.length;
    const cw = (rect.width - padL - 10) / cols;
    const ch = (rect.height - padT - padB) / rows;
    const ci = Math.floor((ev.clientX - rect.left - padL) / cw);
    const ri = Math.floor((ev.clientY - rect.top - padT) / ch);
    if (ci < 0 || ri < 0 || ci >= cols || ri >= rows) {
      setHover(null);
      return;
    }
    const cell = series.rows[ri]?.[ci];
    if (!cell) {
      setHover(null);
      return;
    }
    setHover({
      x: ev.clientX - rect.left,
      y: ev.clientY - rect.top,
      length: grid.secondAxis[ri],
      third: axisLabel(grid.third, grid.thirdAxis[ci]),
      cell,
    });
  };

  return (
    <div className="surface-wrap">
      <div className="surface-head">
        <div className="surface-tabs">
          {SURFACE_DEFS.map((d) => (
            <button key={d.id} type="button"
              className={`seg ${surface === d.id ? "on" : ""}`}
              onClick={() => onSurface(d.id)}>
              {d.title}
            </button>
          ))}
        </div>
        <select className="mini-select" value={metric} onChange={(e) => onMetric(Number(e.target.value))}>
          {SURFACE_METRICS.map((m) => (
            <option key={m.id} value={m.id}>{m.label}</option>
          ))}
        </select>
      </div>
      <div className="surface-canvas-wrap">
        <canvas ref={canvasRef} className="surface-canvas" onMouseMove={onMove} onMouseLeave={() => setHover(null)} />
        {hover && (
          <div className="surface-tip" style={{ left: hover.x + 12, top: hover.y + 12 }}>
            <b>{hover.length} mm · {hover.third}</b>
            <span>e_α {hover.cell[0].toFixed(3)}</span>
            <span>停机 {Math.round(hover.cell[1])} s</span>
            <span>能耗 {Math.round(hover.cell[2])}</span>
            <span>σ {hover.cell[3].toFixed(3)}</span>
          </div>
        )}
      </div>
      <canvas ref={stripRef} className="surface-strip" />
      <div className="surface-foot">
        <span className="surface-scale">
          {metricDef.fmt(metricDef.domain[0])}
          <i style={{
            background: `linear-gradient(90deg, ${[0, 0.25, 0.5, 0.75, 1]
              .map((t) => colorOf(metricDef.domain[0] + t * (metricDef.domain[1] - metricDef.domain[0]), metricDef.domain))
              .join(", ")})`,
          }} />
          {metricDef.fmt(metricDef.domain[1])}{metricDef.unit}
        </span>
        <span>着色：{metricDef.label}</span>
        <span>每格 48 个种子 · 主表代际</span>
      </div>
    </div>
  );
}
