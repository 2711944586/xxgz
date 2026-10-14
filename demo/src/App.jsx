import { useEffect, useMemo, useRef, useState } from "react";
import Scene from "./Scene.jsx";

const MODES = { 0: "品质", 1: "探针", 2: "保持" };

function rowsOf(catalog, policy, cook, length) {
  const key = `${policy}_${cook}_${Math.round(length * 1000)}`;
  return catalog.filter((row) => row.key === key);
}

function scoreOf(rows) {
  if (!rows.length) return null;
  const keep = rows.findIndex((row) => row.mode === 2);
  const cut = rows.findIndex((row) => row.time >= 240 && row.heat <= 0.02);
  let stopIndex = rows.length - 1;
  if (keep > 0) stopIndex = keep - 1;
  else if (keep === 0) stopIndex = 0;
  else if (cut >= 0) stopIndex = cut;
  const stop = rows[stopIndex];
  const last = rows[rows.length - 1];
  return {
    stopS: stop.time,
    eAlpha: stop.alpha - 0.85,
    varEnd: last.varR,
    probed: last.varR < 0.3,
    alphaStop: stop.alpha,
    tCoreStop: stop.t2,
  };
}

function Chart({ rows, compareRows, index }) {
  const ref = useRef(null);
  useEffect(() => {
    const canvas = ref.current;
    if (!canvas || rows.length === 0) return;
    const dpr = Math.min(window.devicePixelRatio || 1, 2);
    const w = canvas.clientWidth;
    const h = canvas.clientHeight;
    canvas.width = w * dpr;
    canvas.height = h * dpr;
    const ctx = canvas.getContext("2d");
    ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
    ctx.clearRect(0, 0, w, h);
    ctx.fillStyle = "#161b20";
    ctx.fillRect(0, 0, w, h);

    const padL = 48;
    const padR = 54;
    const padT = 22;
    const padB = 30;
    const plotW = w - padL - padR;
    const plotH = h - padT - padB;
    const t0 = rows[0].time;
    const t1 = rows[rows.length - 1].time;
    const xOf = (t) => padL + ((t - t0) / (t1 - t0 || 1)) * plotW;
    const yT = (v) => padT + (1 - v / 180) * plotH;
    const yA = (v) => padT + (1 - v) * plotH;

    const probe0 = xOf(150);
    const probe1 = xOf(190);
    ctx.fillStyle = "rgba(196, 165, 116, 0.16)";
    ctx.fillRect(probe0, padT, Math.max(probe1 - probe0, 1), plotH);
    ctx.fillStyle = "#c4a574";
    ctx.font = "10px IBM Plex Mono, monospace";
    ctx.textAlign = "center";
    ctx.textBaseline = "bottom";
    ctx.fillText("探针窗", Math.max((probe0 + probe1) / 2, padL + 28), padT - 4);
    ctx.textBaseline = "alphabetic";

    ctx.strokeStyle = "#2a333a";
    ctx.lineWidth = 1;
    ctx.font = "10px IBM Plex Mono, monospace";
    ctx.fillStyle = "#8d938b";
    ctx.textAlign = "right";
    ctx.textBaseline = "middle";
    for (let i = 0; i <= 4; i++) {
      const temp = i * 45;
      const y = yT(temp);
      ctx.beginPath();
      ctx.moveTo(padL, y);
      ctx.lineTo(padL + plotW, y);
      ctx.stroke();
      ctx.fillText(`${temp}`, padL - 6, y);
      ctx.textAlign = "left";
      ctx.fillText((i / 4).toFixed(2), padL + plotW + 6, yA(i / 4));
      ctx.textAlign = "right";
    }
    ctx.textAlign = "center";
    ctx.textBaseline = "top";
    const minutes = [0, 10, 20, 30, 40, 50];
    minutes.forEach((m) => {
      const t = m * 60;
      if (t > t1) return;
      const x = xOf(t);
      ctx.strokeStyle = "#2a333a";
      ctx.beginPath();
      ctx.moveTo(x, padT);
      ctx.lineTo(x, padT + plotH);
      ctx.stroke();
      ctx.fillStyle = "#8d938b";
      ctx.fillText(`${m}`, x, padT + plotH + 6);
    });
    ctx.fillText("时间 / min", padL + plotW / 2, h - 14);
    ctx.save();
    ctx.translate(12, padT + plotH / 2);
    ctx.rotate(-Math.PI / 2);
    ctx.fillText("温度 / °C", 0, 0);
    ctx.restore();
    ctx.save();
    ctx.translate(w - 12, padT + plotH / 2);
    ctx.rotate(Math.PI / 2);
    ctx.fillText("进度 α", 0, 0);
    ctx.restore();

    const draw = (vals, color, mapY) => {
      ctx.beginPath();
      vals.forEach((v, i) => {
        const x = xOf(rows[i].time);
        const y = mapY(v);
        if (i === 0) ctx.moveTo(x, y);
        else ctx.lineTo(x, y);
      });
      ctx.strokeStyle = color;
      ctx.lineWidth = 1.7;
      ctx.stroke();
    };
    const dash = (vals, color, mapY) => {
      ctx.save();
      ctx.setLineDash([5, 4]);
      ctx.beginPath();
      vals.forEach((v, i) => {
        const x = xOf(compareRows[i].time);
        const y = mapY(v);
        if (i === 0) ctx.moveTo(x, y);
        else ctx.lineTo(x, y);
      });
      ctx.strokeStyle = color;
      ctx.lineWidth = 1.3;
      ctx.stroke();
      ctx.restore();
    };
    const yDesign = yA(0.85);
    ctx.save();
    ctx.setLineDash([3, 5]);
    ctx.strokeStyle = "#c45c4a";
    ctx.lineWidth = 1;
    ctx.beginPath();
    ctx.moveTo(padL, yDesign);
    ctx.lineTo(padL + plotW, yDesign);
    ctx.stroke();
    ctx.restore();
    ctx.fillStyle = "#c45c4a";
    ctx.font = "10px IBM Plex Mono, monospace";
    ctx.textAlign = "left";
    ctx.fillText("α=0.85", padL + 6, yDesign - 4);

    draw(rows.map((r) => r.t1), "#e07a3d", yT);
    draw(rows.map((r) => r.t2), "#7eb8c9", yT);
    draw(rows.map((r) => r.hat), "#d8c07a", yT);
    draw(rows.map((r) => r.alpha), "#c4a574", yA);
    if (compareRows && compareRows.length > 8) {
      dash(compareRows.map((r) => r.t2), "#8aa0a8", yT);
      dash(compareRows.map((r) => r.alpha), "#9a8a68", yA);
    }

    const x = xOf(rows[Math.min(index, rows.length - 1)].time);
    ctx.strokeStyle = "#ece7dc";
    ctx.lineWidth = 1;
    ctx.beginPath();
    ctx.moveTo(x, padT);
    ctx.lineTo(x, padT + plotH);
    ctx.stroke();
  }, [rows, compareRows, index]);
  return <canvas ref={ref} className="chart" />;
}

export default function App() {
  const [catalog, setCatalog] = useState([]);
  const [policy, setPolicy] = useState("dual");
  const [compare, setCompare] = useState("none");
  const [cook, setCook] = useState("combi");
  const [length, setLength] = useState(0.03);
  const [index, setIndex] = useState(0);
  const [playing, setPlaying] = useState(false);
  const [doorOpen, setDoorOpen] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    fetch("./catalog.json")
      .then((res) => {
        if (!res.ok) throw new Error("catalog");
        return res.json();
      })
      .then(setCatalog)
      .catch(() => setError("无法读取 catalog.json，请先运行 scripts/export_demo_trace.py。"));
  }, []);

  const rows = useMemo(
    () => rowsOf(catalog, policy, cook, length),
    [catalog, policy, cook, length],
  );
  const compareRows = useMemo(
    () => (compare === "none" ? [] : rowsOf(catalog, compare, cook, length)),
    [catalog, compare, cook, length],
  );
  const score = useMemo(() => scoreOf(rows), [rows]);
  const compareScore = useMemo(() => scoreOf(compareRows), [compareRows]);
  const frame = rows[Math.min(index, Math.max(rows.length - 1, 0))] || null;
  const compareFrame = compareRows[Math.min(index, Math.max(compareRows.length - 1, 0))] || null;

  function jumpTo(timeS) {
    if (!rows.length) return;
    let best = 0;
    let dist = Infinity;
    rows.forEach((row, i) => {
      const d = Math.abs(row.time - timeS);
      if (d < dist) {
        dist = d;
        best = i;
      }
    });
    setIndex(best);
    setPlaying(false);
  }

  useEffect(() => {
    if (!playing || rows.length === 0) return undefined;
    const id = window.setInterval(() => {
      setIndex((i) => (i + 1) % rows.length);
    }, 40);
    return () => window.clearInterval(id);
  }, [playing, rows.length]);

  function snapLength(value) {
    return [0.015, 0.03, 0.05].reduce((a, b) => (Math.abs(b - value) < Math.abs(a - value) ? b : a));
  }

  function downloadAll() {
    if (!rows.length) return;
    const header = Object.keys(rows[0]).join(",");
    const body = rows.map((row) => Object.values(row).join(",")).join("\n");
    const blob = new Blob([`${header}\n${body}\n`], { type: "text/csv" });
    const a = document.createElement("a");
    a.href = URL.createObjectURL(blob);
    a.download = `acts_${policy}_${cook}_${Math.round(length * 1000)}mm.csv`;
    a.click();
    ["summary.json", "parameters.json"].forEach((name) => {
      const link = document.createElement("a");
      link.href = `./${name}`;
      link.download = name;
      link.click();
    });
  }

  const probing = frame && frame.time >= 150 && frame.time < 190;
  const cookLabel = { steam: "蒸", bake: "烤", combi: "组合" }[cook];
  const policyLabel = { dual: "对偶", mpc: "无探针", open: "开环", pid: "腔温比例" }[policy];

  return (
    <div className="app">
      <header className="topbar">
        <div>
          <p className="kicker">ACTS-MCDT · 东北大学信息感知 · 庄颂 20241334 信息2402</p>
          <h1>智能蒸烤一体机实验台</h1>
          <p className="pages-url">
            静态页{" "}
            <a href="https://2711944586.github.io/xxgz/">https://2711944586.github.io/xxgz/</a>
          </p>
        </div>
        <div className="chips">
          <span className="chip">种子 7 · 肉糜 · 8 °C · 含水 0.72</span>
          <span className={`chip ${cook === "steam" ? "steam" : "on"}`}>{cookLabel}</span>
          <span className="chip">{policyLabel}</span>
          {probing && <span className="chip steam">探针窗</span>}
          {frame && <span className="chip">{MODES[frame.mode] || "—"}</span>}
        </div>
      </header>

      {error && <p className="err">{error}</p>}

      <main className="workspace">
        <aside className="panel controls">
          <p className="panel-label">01 工况</p>
          <label htmlFor="cook">产品模式</label>
          <select id="cook" value={cook} onChange={(e) => { setCook(e.target.value); setIndex(0); }}>
            <option value="steam">蒸</option>
            <option value="bake">烤</option>
            <option value="combi">组合</option>
          </select>
          <label htmlFor="policy">控制策略</label>
          <select id="policy" value={policy} onChange={(e) => { setPolicy(e.target.value); setIndex(0); }}>
            <option value="dual">对偶（探针 + 停机）</option>
            <option value="mpc">无探针反馈</option>
            <option value="open">开环菜单</option>
            <option value="pid">腔温比例</option>
          </select>
          <label htmlFor="compare">对照策略</label>
          <select id="compare" value={compare} onChange={(e) => setCompare(e.target.value)}>
            <option value="none">关闭</option>
            <option value="open">开环菜单</option>
            <option value="pid">腔温比例</option>
            <option value="mpc">无探针反馈</option>
            <option value="dual">对偶</option>
          </select>
          <label htmlFor="thick">厚度 {Math.round(length * 1000)} mm</label>
          <div className="events">
            <button type="button" className="chip-btn" onClick={() => { setLength(0.015); setIndex(0); }}>15 mm</button>
            <button type="button" className="chip-btn" onClick={() => { setLength(0.03); setIndex(0); }}>30 mm</button>
            <button type="button" className="chip-btn" onClick={() => { setLength(0.05); setIndex(0); }}>50 mm</button>
          </div>
          <input
            id="thick"
            type="range" min="0.015" max="0.05" step="0.005" value={length}
            onChange={(e) => { setLength(snapLength(Number(e.target.value))); setIndex(0); }}
          />
          <label htmlFor="time">时间 {frame ? Math.round(frame.time) : 0} s</label>
          <input
            id="time"
            type="range"
            min="0"
            max={Math.max(rows.length - 1, 0)}
            step="1"
            value={Math.min(index, Math.max(rows.length - 1, 0))}
            onChange={(e) => setIndex(Number(e.target.value))}
          />
          <div className="playrow">
            <button type="button" onClick={() => setPlaying((p) => !p)} disabled={!frame}>
              {playing ? "暂停" : "回放"}
            </button>
            <button type="button" className="ghost" onClick={() => setDoorOpen((d) => !d)}>
              {doorOpen ? "关门" : "开门"}
            </button>
          </div>
          <div className="playrow">
            <button type="button" className="ghost" onClick={downloadAll} disabled={!frame}>
              导出 CSV
            </button>
            <button type="button" className="ghost" onClick={() => jumpTo(1680)} disabled={!frame}>
              1680 s
            </button>
          </div>
          <p className="panel-label">事件</p>
          <div className="events">
            <button type="button" className="chip-btn" onClick={() => jumpTo(0)}>起始</button>
            <button type="button" className="chip-btn" onClick={() => jumpTo(160)}>探针窗</button>
            <button type="button" className="chip-btn" onClick={() => jumpTo(1680)}>品质段</button>
            <button type="button" className="chip-btn" onClick={() => jumpTo(1866)}>停机</button>
          </div>
          {score && (
            <div className="verdict">
              <div className="row"><span>停机</span><span>{Math.round(score.stopS)} s</span></div>
              <div className="row"><span>e<sub>α</sub></span><span>{score.eAlpha >= 0 ? "+" : ""}{score.eAlpha.toFixed(3)}</span></div>
              <div className="row"><span>探针</span><span>{score.probed ? "方差 0.224" : "仍为先验 0.64"}</span></div>
              <div className="row"><span>相对 0.85</span><span>{score.eAlpha >= 0 ? "越过设计线" : "低于设计线"}</span></div>
            </div>
          )}
          <p className="note">
            页面读取数值核已经写出的状态流，不在浏览器里重跑积分。对照策略以虚线叠在底部曲线上。开门只改铰链，不改温度数组。红虚线是设计线 α=0.85。
          </p>
        </aside>

        <section className="panel viewport">
          <p className="panel-label" style={{ position: "absolute", zIndex: 2, left: 16, top: 10 }}>02 腔体</p>
          <Scene frame={frame} length={length} doorOpen={doorOpen} />
          {frame && (
            <div className="hud">
              <div>表面 <b>{frame.t1.toFixed(1)} °C</b></div>
              <div>冷点 <b>{frame.t2.toFixed(1)} °C</b></div>
              <div>估计 <b>{frame.hat.toFixed(1)} °C</b></div>
              <div>进度 <b>{frame.alpha.toFixed(3)}</b></div>
              <div>时间 <b>{Math.round(frame.time)} s</b></div>
            </div>
          )}
          <div className="legend">
            <span>冷</span>
            <span className="ramp" />
            <span>热</span>
          </div>
        </section>

        <aside className="panel">
          <p className="panel-label">03 本帧</p>
          {frame && (
            <div className="kv">
              <div className="row"><span>含水</span><span>{frame.m.toFixed(3)}</span></div>
              <div className="row"><span>进度 α</span><span>{frame.alpha.toFixed(3)}</span></div>
              <div className="row"><span>热阻 / 方差</span><span>{frame.rHat.toFixed(2)} / {frame.varR.toFixed(3)}</span></div>
              <div className="row"><span>腔温 / 腔湿</span><span>{frame.cavT.toFixed(1)} °C / {frame.cavH.toFixed(2)}</span></div>
              <div className="row"><span>水位</span><span>{frame.water.toFixed(2)}</span></div>
              <p className="panel-label">执行器</p>
              <Meter name="加热" value={frame.heat} />
              <Meter name="蒸汽" value={frame.steam} kind="steam" />
              <Meter name="风机" value={frame.fan / 1.3} kind="fan" />
              <Meter name="排汽" value={frame.exhaust} />
              <p className="panel-label">路径与投影</p>
              <div className="row"><span>A 冷点潜热</span><span>{frame.pathA.toFixed(0)}</span></div>
              <div className="row"><span>B 表面蒸发</span><span>{frame.pathB.toFixed(0)}</span></div>
              <div className="row"><span>C 结壳热阻</span><span>{frame.pathC.toFixed(0)}</span></div>
              <div className="row"><span>请求 → 指令</span><span>{frame.heatReq.toFixed(2)} → {frame.heat.toFixed(2)}</span></div>
              <div className="row"><span>加热器</span><span>{frame.heater.toFixed(1)} °C</span></div>
              {compareFrame && (
                <>
                  <p className="panel-label">对照本帧</p>
                  <div className="row"><span>对照冷点</span><span>{compareFrame.t2.toFixed(1)} °C</span></div>
                  <div className="row"><span>对照进度</span><span>{compareFrame.alpha.toFixed(3)}</span></div>
                  <div className="row"><span>对照方差</span><span>{compareFrame.varR.toFixed(3)}</span></div>
                  {compareScore && (
                    <div className="row">
                      <span>对照 e<sub>α</sub></span>
                      <span>{compareScore.eAlpha >= 0 ? "+" : ""}{compareScore.eAlpha.toFixed(3)}</span>
                    </div>
                  )}
                </>
              )}
            </div>
          )}
        </aside>
      </main>

      <footer className="chartbar">
        <Chart rows={rows} compareRows={compareRows} index={index} />
        <div className="chart-legend">
          <span><i className="dot" style={{ background: "#e07a3d" }} />表面温度</span>
          <span><i className="dot" style={{ background: "#7eb8c9" }} />冷点温度</span>
          <span><i className="dot" style={{ background: "#d8c07a" }} />估计温度</span>
          <span><i className="dot" style={{ background: "#c4a574" }} />进度 α（右轴）</span>
          {compare !== "none" && <span>虚线：对照冷点 / 进度</span>}
          <span>红虚线：设计线 0.85</span>
        </div>
      </footer>
    </div>
  );
}

function Meter({ name, value, kind }) {
  const x = Math.max(0, Math.min(1, value));
  return (
    <div className="row">
      <span>{name}</span>
      <span className={`bar ${kind || ""}`}><i style={{ width: `${x * 100}%` }} /></span>
    </div>
  );
}
