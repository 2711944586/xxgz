import { useEffect, useRef } from "react";

const FONT = "11px 'IBM Plex Mono', ui-monospace, monospace";
const COL = {
  grid: "#222a30",
  gridSoft: "#1a2126",
  axis: "#6b7a83",
  surface: "#ee8f4e",
  core: "#74b6cc",
  estimate: "#d9c183",
  alpha: "#c9a86d",
  probe: "rgba(217, 193, 131, 0.10)",
  design: "#b8604f",
  stop: "#7fa383",
  cursor: "#f2ece0",
};

function setupCanvas(canvas, height) {
  const dpr = Math.min(window.devicePixelRatio || 1, 2);
  const w = canvas.clientWidth;
  const h = height || canvas.clientHeight;
  if (!w || !h) return null;
  canvas.width = Math.round(w * dpr);
  canvas.height = Math.round(h * dpr);
  const ctx = canvas.getContext("2d");
  ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
  ctx.clearRect(0, 0, w, h);
  return { ctx, w, h };
}

function niceTicks(min, max, count) {
  const span = max - min || 1;
  const step0 = span / count;
  const mag = 10 ** Math.floor(Math.log10(step0));
  const norm = step0 / mag;
  const step = (norm >= 5 ? 5 : norm >= 2 ? 2 : 1) * mag;
  const start = Math.ceil(min / step) * step;
  const out = [];
  for (let v = start; v <= max + 1e-6; v += step) out.push(Math.round(v * 1e6) / 1e6);
  return out;
}

export function TemperatureChart({
  rows, compareRows, manifest, frameIndex, stopS, probed, onSeek, accentGlow,
}) {
  const ref = useRef(null);
  const dragRef = useRef(false);

  useEffect(() => {
    const canvas = ref.current;
    if (!canvas || !rows?.length) return undefined;
    const paint = () => {
      const s = setupCanvas(canvas);
      if (!s) return;
      const { ctx, w, h } = s;
      const padL = 46;
      const padR = 44;
      const padT = 16;
      const padB = 26;
      const pw = w - padL - padR;
      const ph = h - padT - padB;

      const t0 = rows[0].time;
      const t1 = rows[rows.length - 1].time;
      const xOf = (t) => padL + ((t - t0) / (t1 - t0 || 1)) * pw;
      let peak = 0;
      for (const r of rows) peak = Math.max(peak, r.tSurf, r.tCore);
      for (const r of compareRows || []) peak = Math.max(peak, r.tCore);
      const tempMax = Math.ceil((peak + 10) / 40) * 40;
      const yT = (v) => padT + (1 - Math.min(v, tempMax) / tempMax) * ph;
      const yA = (v) => padT + (1 - Math.min(1, Math.max(0, v))) * ph;

      ctx.fillStyle = "#0e1418";
      ctx.fillRect(0, 0, w, h);

      if (probed) {
        const [p0, p1] = manifest.probeWindow;
        ctx.fillStyle = COL.probe;
        ctx.fillRect(xOf(p0), padT, Math.max(xOf(p1) - xOf(p0), 1), ph);
        ctx.fillStyle = "#a8905f";
        ctx.font = FONT;
        ctx.textAlign = "left";
        ctx.textBaseline = "top";
        ctx.fillText("探针窗", xOf(p0) + 4, padT + 3);
      }

      ctx.strokeStyle = COL.gridSoft;
      ctx.lineWidth = 1;
      niceTicks(0, tempMax, 4).forEach((v) => {
        const y = yT(v);
        ctx.beginPath();
        ctx.moveTo(padL, y);
        ctx.lineTo(padL + pw, y);
        ctx.stroke();
        ctx.fillStyle = COL.axis;
        ctx.textAlign = "right";
        ctx.textBaseline = "middle";
        ctx.fillText(String(Math.round(v)), padL - 7, y);
      });
      const minutes = niceTicks(0, t1 / 60, 6);
      minutes.forEach((m) => {
        const x = xOf(m * 60);
        if (x < padL - 1 || x > padL + pw + 1) return;
        ctx.strokeStyle = COL.gridSoft;
        ctx.beginPath();
        ctx.moveTo(x, padT);
        ctx.lineTo(x, padT + ph);
        ctx.stroke();
        ctx.fillStyle = COL.axis;
        ctx.textAlign = "center";
        ctx.textBaseline = "top";
        ctx.fillText(String(Math.round(m)), x, padT + ph + 6);
      });

      ctx.fillStyle = COL.axis;
      ctx.textAlign = "left";
      ctx.textBaseline = "top";
      ctx.fillText("°C", 6, padT - 2);
      ctx.textAlign = "right";
      ctx.fillText("α", w - 8, padT - 2);
      ctx.textAlign = "center";
      ctx.fillText("min", padL + pw / 2, h - 12);

      ctx.save();
      ctx.setLineDash([4, 4]);
      ctx.strokeStyle = COL.design;
      ctx.beginPath();
      ctx.moveTo(padL, yA(manifest.designLine));
      ctx.lineTo(padL + pw, yA(manifest.designLine));
      ctx.stroke();
      ctx.restore();
      ctx.fillStyle = COL.design;
      ctx.textAlign = "left";
      ctx.textBaseline = "bottom";
      ctx.fillText("α 0.85", padL + 4, yA(manifest.designLine) - 2);

      if (stopS != null && stopS < t1 - 1) {
        ctx.save();
        ctx.setLineDash([2, 3]);
        ctx.strokeStyle = COL.stop;
        ctx.beginPath();
        ctx.moveTo(xOf(stopS), padT);
        ctx.lineTo(xOf(stopS), padT + ph);
        ctx.stroke();
        ctx.restore();
      }

      const line = (xs, ys, color, width = 1.8, dash = null, glow = 0) => {
        ctx.save();
        if (dash) ctx.setLineDash(dash);
        ctx.strokeStyle = color;
        ctx.lineWidth = width;
        ctx.lineJoin = "round";
        if (glow) {
          ctx.shadowColor = color;
          ctx.shadowBlur = glow;
        }
        ctx.beginPath();
        for (let i = 0; i < xs.length; i += 1) {
          const x = xOf(xs[i]);
          const y = ys[i];
          if (i === 0) ctx.moveTo(x, y);
          else ctx.lineTo(x, y);
        }
        ctx.stroke();
        ctx.restore();
      };

      const times = rows.map((r) => r.time);
      if (compareRows?.length) {
        line(compareRows.map((r) => r.time), compareRows.map((r) => yT(r.tCore)), "#7b9099", 1.2, [5, 4]);
        line(compareRows.map((r) => r.time), compareRows.map((r) => yA(r.alpha)), "#8a7b5c", 1.1, [5, 4]);
      }
      line(times, rows.map((r) => yT(r.tSurf)), COL.surface, 1.9, null, accentGlow ? 6 : 0);
      line(times, rows.map((r) => yT(r.tCore)), COL.core, 1.9);
      line(times, rows.map((r) => yT(r.tHat)), COL.estimate, 1.3, [3, 3]);
      line(times, rows.map((r) => yA(r.alpha)), COL.alpha, 1.5);

      const idx = Math.min(frameIndex, rows.length - 1);
      const row = rows[idx];
      const cx = xOf(row.time);
      ctx.strokeStyle = "rgba(242, 236, 224, 0.35)";
      ctx.lineWidth = 1;
      ctx.beginPath();
      ctx.moveTo(cx, padT);
      ctx.lineTo(cx, padT + ph);
      ctx.stroke();
      [
        [row.tSurf, COL.surface, yT],
        [row.tCore, COL.core, yT],
        [row.alpha, COL.alpha, yA],
      ].forEach(([v, color, mapY]) => {
        ctx.fillStyle = color;
        ctx.beginPath();
        ctx.arc(cx, mapY(v), 3, 0, Math.PI * 2);
        ctx.fill();
        ctx.strokeStyle = "#0e1418";
        ctx.lineWidth = 1.2;
        ctx.stroke();
      });
      return { xOf, padL, pw, t0, t1 };
    };

    paint();
    const ro = new ResizeObserver(() => paint());
    ro.observe(canvas);
    return () => ro.disconnect();
  }, [rows, compareRows, manifest, frameIndex, stopS, probed, accentGlow]);

  const seek = (ev) => {
    const canvas = ref.current;
    if (!canvas || !rows?.length) return;
    const rect = canvas.getBoundingClientRect();
    const padL = 46;
    const padR = 44;
    const pw = rect.width - padL - padR;
    const ratio = Math.min(1, Math.max(0, (ev.clientX - rect.left - padL) / pw));
    const t = rows[0].time + ratio * (rows[rows.length - 1].time - rows[0].time);
    const index = Math.round((t - rows[0].time) / (rows[1].time - rows[0].time));
    onSeek?.(Math.min(rows.length - 1, Math.max(0, index)));
  };

  return (
    <canvas
      ref={ref}
      className="chart chart-temp"
      onPointerDown={(ev) => {
        dragRef.current = true;
        ev.currentTarget.setPointerCapture?.(ev.pointerId);
        seek(ev);
      }}
      onPointerMove={(ev) => {
        if (dragRef.current) seek(ev);
      }}
      onPointerUp={(ev) => {
        dragRef.current = false;
        ev.currentTarget.releasePointerCapture?.(ev.pointerId);
      }}
      onPointerCancel={() => { dragRef.current = false; }}
    />
  );
}

const LANES = [
  { key: "heat", label: "加热", color: "#e0783c" },
  { key: "steam", label: "蒸汽", color: "#74b6cc" },
  { key: "fan", label: "风机", color: "#8fa3ad", max: 1.3 },
  { key: "exhaust", label: "排汽", color: "#8a7b5c" },
];

export function ActuatorChart({ rows, manifest, frameIndex, probed, onSeek }) {
  const ref = useRef(null);
  useEffect(() => {
    const canvas = ref.current;
    if (!canvas || !rows?.length) return undefined;
    const paint = () => {
      const s = setupCanvas(canvas, 118);
      if (!s) return;
      const { ctx, w, h } = s;
      const padL = 46;
      const padR = 12;
      const padT = 8;
      const padB = 16;
      const pw = w - padL - padR;
      const laneH = (h - padT - padB) / LANES.length;
      const t0 = rows[0].time;
      const t1 = rows[rows.length - 1].time;
      const xOf = (t) => padL + ((t - t0) / (t1 - t0 || 1)) * pw;

      ctx.fillStyle = "#0e1418";
      ctx.fillRect(0, 0, w, h);

      if (probed) {
        const [p0, p1] = manifest.probeWindow;
        ctx.fillStyle = COL.probe;
        ctx.fillRect(xOf(p0), padT, Math.max(xOf(p1) - xOf(p0), 1), laneH * LANES.length);
      }

      LANES.forEach((lane, i) => {
        const top = padT + i * laneH;
        const base = top + laneH - 2;
        const max = lane.max || 1;
        ctx.strokeStyle = COL.gridSoft;
        ctx.beginPath();
        ctx.moveTo(padL, top + laneH - 0.5);
        ctx.lineTo(padL + pw, top + laneH - 0.5);
        ctx.stroke();

        ctx.beginPath();
        ctx.moveTo(xOf(rows[0].time), base);
        rows.forEach((r) => {
          ctx.lineTo(xOf(r.time), base - (Math.min(max, r[lane.key]) / max) * (laneH - 6));
        });
        ctx.lineTo(xOf(rows[rows.length - 1].time), base);
        ctx.closePath();
        ctx.fillStyle = `${lane.color}33`;
        ctx.fill();
        ctx.strokeStyle = lane.color;
        ctx.lineWidth = 1;
        ctx.stroke();

        ctx.fillStyle = COL.axis;
        ctx.font = FONT;
        ctx.textAlign = "right";
        ctx.textBaseline = "middle";
        ctx.fillText(lane.label, padL - 7, top + laneH / 2);
      });

      const idx = Math.min(frameIndex, rows.length - 1);
      const cx = xOf(rows[idx].time);
      ctx.strokeStyle = "rgba(242, 236, 224, 0.4)";
      ctx.beginPath();
      ctx.moveTo(cx, padT);
      ctx.lineTo(cx, padT + laneH * LANES.length);
      ctx.stroke();
    };
    paint();
    const ro = new ResizeObserver(() => paint());
    ro.observe(canvas);
    return () => ro.disconnect();
  }, [rows, manifest, frameIndex, probed]);

  return (
    <canvas
      ref={ref}
      className="chart chart-act"
      onPointerDown={(ev) => {
        const rect = ev.currentTarget.getBoundingClientRect();
        const ratio = Math.min(1, Math.max(0, (ev.clientX - rect.left - 46) / (rect.width - 58)));
        onSeek?.(Math.round(ratio * (rows.length - 1)));
      }}
    />
  );
}
