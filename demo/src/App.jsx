import { useCallback, useEffect, useMemo, useState } from "react";
import Scene, { VIEW_PRESETS } from "./Scene.jsx";
import { TemperatureChart, ActuatorChart } from "./components/Charts.jsx";
import { SurfaceMap } from "./components/SurfaceMap.jsx";
import {
  decodeScenario, eventsOf, loadDemo, nearestFrame, scenarioOf,
} from "./lib/data.js";

const PANES = [
  { id: "run", label: "运行", hint: "腔体、时序、停机判定" },
  { id: "twin", label: "孪生", hint: "零件、剖面、标注" },
  { id: "probe", label: "探针", hint: "为什么稳态看不见热阻" },
  { id: "compare", label: "对照", hint: "五条策略的停机几何" },
  { id: "surface", label: "响应面", hint: "厚度与初温的连续曲面" },
];

function fmt(v, digits = 2) {
  if (v == null || Number.isNaN(v)) return "—";
  return Number(v).toFixed(digits);
}

function pad(v, width) {
  return String(Math.round(v)).padStart(width, "0");
}

function ColorBar() {
  return (
    <div className="colorbar">
      <div className="colorbar-track" />
      <div className="colorbar-ticks">
        <span>8 °C</span>
        <span>90</span>
        <span>175</span>
      </div>
    </div>
  );
}

export default function App() {
  const [data, setData] = useState({ manifest: null, surfaces: null, contract: null, buffer: null });
  const [error, setError] = useState("");
  const [policy, setPolicy] = useState("dual");
  const [compare, setCompare] = useState("mpc");
  const [cook, setCook] = useState("combi");
  const [lengthMm, setLengthMm] = useState(30);
  const [index, setIndex] = useState(0);
  const [playing, setPlaying] = useState(false);
  const [speed, setSpeed] = useState(3);
  const [pane, setPane] = useState("run");
  const [view, setView] = useState("home");
  const [section, setSection] = useState(false);
  const [explode, setExplode] = useState(0);
  const [annotations, setAnnotations] = useState(true);
  const [orphan, setOrphan] = useState(null);
  const [doorOpen, setDoorOpen] = useState(true);
  const [showSteam, setShowSteam] = useState(true);
  const [showAirflow, setShowAirflow] = useState(true);
  const [surface, setSurface] = useState("LT");
  const [metric, setMetric] = useState(0);
  const [chainStep, setChainStep] = useState(0);
  const [pickedPart, setPickedPart] = useState(null);
  const [exportOpen, setExportOpen] = useState(false);
  const [toast, setToast] = useState("");

  useEffect(() => {
    loadDemo().then(setData).catch((err) => setError(err.message));
  }, []);

  const { manifest, surfaces, contract, buffer } = data;

  useEffect(() => {
    if (!manifest) return;
    const d = manifest.defaults;
    setPolicy(d.policy);
    setCook(d.cook);
    setLengthMm(d.lengthMm);
  }, [manifest]);

  const scenario = useMemo(
    () => (manifest ? scenarioOf(manifest, policy, cook, lengthMm) : null),
    [manifest, policy, cook, lengthMm],
  );
  const compareScenario = useMemo(
    () => (manifest && compare !== "none" ? scenarioOf(manifest, compare, cook, lengthMm) : null),
    [manifest, compare, cook, lengthMm],
  );

  const trace = useMemo(() => {
    if (!manifest || !buffer || !scenario) return null;
    return decodeScenario(manifest, buffer, scenario.key);
  }, [manifest, buffer, scenario]);

  const compareTrace = useMemo(() => {
    if (!manifest || !buffer || !compareScenario) return null;
    return decodeScenario(manifest, buffer, compareScenario.key);
  }, [manifest, buffer, compareScenario]);

  const rows = trace?.rows || [];
  const compareRows = compareTrace?.rows || [];
  const safeIndex = Math.min(index, Math.max(rows.length - 1, 0));
  const frame = rows[safeIndex] || null;
  const compareFrame = compareRows[Math.min(safeIndex, Math.max(compareRows.length - 1, 0))] || null;
  const events = useMemo(
    () => (manifest && scenario ? eventsOf(manifest, scenario) : []),
    [manifest, scenario],
  );

  useEffect(() => { setIndex(0); setPlaying(false); }, [scenario?.key]);

  useEffect(() => {
    if (!playing || !rows.length) return undefined;
    const frameMs = 1000 / 60;
    const stepPerFrame = Math.max(1, Math.round(speed / 2));
    const id = window.setInterval(() => {
      setIndex((i) => {
        const next = i + stepPerFrame;
        if (next >= rows.length - 1) {
          setPlaying(false);
          return rows.length - 1;
        }
        return next;
      });
    }, frameMs);
    return () => window.clearInterval(id);
  }, [playing, rows.length, speed]);

  const seekTime = useCallback((seconds) => {
    if (!rows.length) return;
    setPlaying(false);
    setIndex(nearestFrame(rows, seconds));
  }, [rows]);

  const jumpEvent = (ev) => seekTime(ev.time);

  useEffect(() => {
    const onKey = (ev) => {
      const el = ev.target;
      const typing = el instanceof HTMLInputElement
        && !["range", "checkbox", "radio", "button"].includes(el.type);
      if (typing || el instanceof HTMLSelectElement) return;
      // A focused slider keeps the arrow keys (its own stepping) and space
      // (page scroll guard); every other shortcut still applies, so the page
      // does not go dead after a drag.
      const onRange = el instanceof HTMLInputElement;
      if (ev.code === "Space" && !onRange) {
        ev.preventDefault();
        setPlaying((p) => !p);
      } else if (ev.code === "ArrowRight" && !onRange) {
        setIndex((i) => Math.min(rows.length - 1, i + (ev.shiftKey ? 10 : 1)));
      } else if (ev.code === "ArrowLeft" && !onRange) {
        setIndex((i) => Math.max(0, i - (ev.shiftKey ? 10 : 1)));
      } else if (ev.key === "1") setPane("run");
      else if (ev.key === "2") setPane("twin");
      else if (ev.key === "3") setPane("probe");
      else if (ev.key === "4") setPane("compare");
      else if (ev.key === "5") setPane("surface");
      else if (ev.key.toLowerCase() === "s") setSection((s) => !s);
      else if (ev.key.toLowerCase() === "d") setOrphan((d) => !d);
    };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [rows.length]);

  const download = () => {
    if (!rows.length) return;
    const keys = manifest.channels.map((c) => c.key);
    const head = [...keys, ...Array.from({ length: manifest.field.cells }, (_, i) => `T${i}`)];
    const lines = [head.join(",")];
    rows.forEach((r) => {
      const vals = keys.map((k) => Number(r[k].toFixed(5)));
      const field = Array.from(r.nodes, (v) => Number(v.toFixed(3)));
      lines.push([...vals, ...field].join(","));
    });
    const blob = new Blob([`${lines.join("\n")}\n`], { type: "text/csv" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `acts_${scenario.key}.csv`;
    a.click();
    URL.revokeObjectURL(url);
  };

  const copyLink = () => {
    const params = new URLSearchParams({ p: policy, c: cook, l: String(lengthMm), i: String(safeIndex) });
    navigator.clipboard?.writeText(`${window.location.origin}${window.location.pathname}?${params}`);
    setToast("链接已复制");
    window.setTimeout(() => setToast(""), 1600);
  };

  if (error) {
    return (
      <div className="fatal">
        <h1>数据未就绪</h1>
        <p>{error}</p>
        <code>python scripts/build_demo_dataset.py</code>
      </div>
    );
  }

  const ready = Boolean(manifest && frame);
  const probing = frame && frame.mode === 1;
  const policyMeta = manifest?.policies.find((p) => p.key === policy);
  const compareMeta = manifest?.policies.find((p) => p.key === compare);
  const progress = rows.length > 1 ? safeIndex / (rows.length - 1) : 0;
  const stopS = scenario?.metrics.stopS;
  const doorShown = doorOpen && !section && pane !== "surface";
  const isDoorClosed = !doorShown;

  return (
    <div className="shell">
      <header className="top">
        <div className="brand">
          <div className="brand-mark">
            <span />
            <span />
            <span />
          </div>
          <div>
            <p className="brand-kicker">信息感知 · 课程设计 · 20241334 庄颂 · 信息2402</p>
            <h1>智能蒸烤一体机 · 数字孪生实验台</h1>
          </div>
        </div>
        <div className="top-status">
          {manifest && (
            <>
              <span className="status-chip">{manifest.product}</span>
              <span className="status-chip mono">显示代际</span>
              <span className="status-chip mono">{manifest.sampling.frames.toLocaleString()} 帧 · {manifest.sampling.scenarios} 条</span>
            </>
          )}
          <a className="status-link" href="https://2711944586.github.io/xxgz/" target="_blank" rel="noreferrer">
            公开页
          </a>
        </div>
      </header>

      <nav className="panes">
        {PANES.map((p, i) => (
          <button key={p.id} type="button"
            className={`pane ${pane === p.id ? "on" : ""}`}
            onClick={() => setPane(p.id)}>
            <span className="pane-idx">{pad(i + 1, 2)}</span>
            <span className="pane-body">
              <b>{p.label}</b>
              <i>{p.hint}</i>
            </span>
          </button>
        ))}
        <div className="pane-spacer" />
        <div className="status-strip">
          <div className="status-cell">
            <span>t</span>
            <b>{frame ? frame.time.toFixed(0) : "—"}<i>s</i></b>
          </div>
          <div className="status-cell">
            <span>冷点</span>
            <b>{frame ? fmt(frame.tCore, 1) : "—"}<i>°C</i></b>
          </div>
          <div className={`status-cell ${frame && frame.alpha >= 0.85 ? "ok" : ""}`}>
            <span>α</span>
            <b>{frame ? fmt(frame.alpha, 3) : "—"}</b>
          </div>
          <div className={`status-cell ${scenario?.metrics.eAlpha >= 0 ? "ok" : "warn"}`}>
            <span>e<sub>α</sub></span>
            <b>{(scenario?.metrics.eAlpha ?? 0) >= 0 ? "+" : ""}{scenario ? fmt(scenario.metrics.eAlpha, 3) : "—"}</b>
          </div>
          <div className="status-cell">
            <span>停机</span>
            <b>{stopS ? Math.round(stopS) : "—"}<i>s</i></b>
          </div>
          <div className={`status-cell ${frame && frame.varR < 0.3 ? "ok" : ""}`}>
            <span>σ²</span>
            <b>{frame ? fmt(frame.varR, 3) : "—"}</b>
          </div>
        </div>
      </nav>

      <main className={`stage pane-${pane}`}>
        <aside className="rail rail-left">
          {pane === "run" && (
            <RunControls
              manifest={manifest}
              policy={policy} setPolicy={setPolicy}
              cook={cook} setCook={setCook}
              lengthMm={lengthMm} setLengthMm={setLengthMm}
              policyMeta={policyMeta}
              doorOpen={doorOpen} setDoorOpen={setDoorOpen}
            />
          )}
          {pane === "twin" && (
            <TwinControls
              view={view} setView={setView}
              section={section} setSection={setSection}
              explode={explode} setExplode={setExplode}
              annotations={annotations} setAnnotations={setAnnotations}
              showSteam={showSteam} setShowSteam={setShowSteam}
              showAirflow={showAirflow} setShowAirflow={setShowAirflow}
              orphan={orphan} setOrphan={setOrphan}
              doorOpen={doorOpen} setDoorOpen={setDoorOpen}
              pickedPart={pickedPart}
            />
          )}
          {pane === "probe" && (
            <ProbeControls chainStep={chainStep} setChainStep={setChainStep} frame={frame} rows={rows} />
          )}
          {pane === "compare" && (
            <CompareControls
              manifest={manifest}
              policy={policy} setPolicy={setPolicy}
              compare={compare} setCompare={setCompare}
              lengthMm={lengthMm} setLengthMm={setLengthMm}
              cook={cook} setCook={setCook}
            />
          )}
          {pane === "surface" && (
            <SurfaceControls
              surface={surface} setSurface={setSurface}
              metric={metric} setMetric={setMetric}
              policy={policy} setPolicy={setPolicy}
              surfaces={surfaces}
            />
          )}

          <div className="rail-foot">
            <button type="button" className="ghost-btn" onClick={download} disabled={!rows.length}>
              导出当前轨迹 CSV
            </button>
            <button type="button" className="ghost-btn" onClick={copyLink}>
              复制本帧链接
            </button>
            <button type="button" className="ghost-btn" onClick={() => setExportOpen((v) => !v)}>
              {exportOpen ? "收起数据说明" : "数据说明"}
            </button>
            {exportOpen && manifest && (
              <div className="data-note">
                <p>{manifest.generationNote}</p>
                <dl>
                  <div><dt>生成</dt><dd>{manifest.provenance.generator}</dd></div>
                  <div><dt>核</dt><dd>{manifest.provenance.kernel}</dd></div>
                  <div><dt>响应面</dt><dd>{manifest.provenance.surfaceSource}</dd></div>
                  <div><dt>抽样</dt><dd>{manifest.sampling.frameS} s / 帧，共 {manifest.sampling.framesPerScenario} 帧</dd></div>
                </dl>
              </div>
            )}
          </div>
        </aside>

        <section className="canvas-area">
          <Scene
            frame={frame}
            lengthM={lengthMm / 1000}
            doorOpen={doorShown}
            view={view}
            section={section || pane === "compare"}
            explode={explode}
            annotations={annotations && (pane === "twin" || pane === "run") && !isDoorClosed}
            showSteam={showSteam}
            showAirflow={showAirflow}
            cavityLightOn={orphan}
            onPickPart={(part) => setPickedPart(part)}
          />
          {pane !== "surface" && (
            <div className="canvas-top">
              <div className="mode-tag">
                {probing ? "探针窗" : frame?.mode === 2 ? "保持" : "品质段"}
                <span>{policyMeta?.label || "—"} · {cook === "steam" ? "蒸" : cook === "bake" ? "烤" : "组合"} · {lengthMm} mm</span>
              </div>
              <div className="view-tools">
                {VIEW_PRESETS.map((v) => (
                  <button key={v.id} type="button"
                    className={`tool ${view === v.id && !section ? "on" : ""}`}
                    onClick={() => { setSection(false); setView(v.id); }}>
                    {v.label}
                  </button>
                ))}
                <button type="button" className={`tool ${section ? "on" : ""}`}
                  onClick={() => setSection((s) => !s)}>
                  剖切
                </button>
              </div>
            </div>
          )}
          {pane !== "surface" && (
            <div className="canvas-bottom">
              <div className="hud">
                <div className="hud-row"><span>表面</span><b>{fmt(frame?.tSurf, 1)}</b><i>°C</i></div>
                <div className="hud-row"><span>冷点</span><b>{fmt(frame?.tCore, 1)}</b><i>°C</i></div>
                <div className="hud-row"><span>估计</span><b>{fmt(frame?.tHat, 1)}</b><i>°C</i></div>
                <div className="hud-row"><span>腔温</span><b>{fmt(frame?.cavT, 1)}</b><i>°C</i></div>
              </div>
              <ColorBar />
            </div>
          )}
          {pane === "surface" && (
            <div className="surface-overlay">
              <SurfaceMap
                surfaces={surfaces}
                policy={policy}
                metric={metric}
                surface={surface}
                onSurface={setSurface}
                onMetric={setMetric}
              />
            </div>
          )}
        </section>

        <aside className="rail rail-right">
          {pane === "run" && (
            <RunInspector
              manifest={manifest}
              scenario={scenario}
              frame={frame}
              compareFrame={compareFrame}
              compare={compare}
              compareMeta={compareMeta}
              events={events}
              onJump={jumpEvent}
            />
          )}
          {pane === "twin" && (
            <TwinInspector
              manifest={manifest}
              frame={frame}
              scenario={scenario}
              pickedPart={pickedPart}
              onPickPart={setPickedPart}
            />
          )}
          {pane === "probe" && (
            <ProbeInspector chainStep={chainStep} setChainStep={setChainStep} rows={rows} frame={frame} scenario={scenario} onJump={seekTime} />
          )}
          {pane === "compare" && (
            <CompareInspector
              manifest={manifest}
              cook={cook}
              lengthMm={lengthMm}
              policy={policy}
              compare={compare}
            />
          )}
          {pane === "surface" && (
            <SurfaceInspector
              surfaces={surfaces}
              policy={policy}
              metric={metric}
              surface={surface}
              onPickPolicy={setPolicy}
            />
          )}
        </aside>
      </main>

      <footer className="timeline">
        <div className="transport">
          <button type="button" className="play" onClick={() => setPlaying((p) => !p)}>
            {playing ? "暂停" : "播放"}
          </button>
          <div className="speed">
            {[1, 3, 6, 12].map((s) => (
              <button key={s} type="button" className={`sp ${speed === s ? "on" : ""}`}
                onClick={() => setSpeed(s)}>{s}×</button>
            ))}
          </div>
          <div className="clock">
            <b>{frame ? frame.time.toFixed(0) : "0"}</b>
            <i>/ {rows.length ? rows[rows.length - 1].time.toFixed(0) : "0"} s</i>
          </div>
          <div className="event-chips">
            {events.map((ev) => (
              <button key={`${ev.kind}${ev.time}`} type="button" className={`event-chip ${ev.kind}`}
                onClick={() => jumpEvent(ev)}>
                {ev.label}
              </button>
            ))}
          </div>
        </div>
        <div className="scrub-wrap">
          <input
            className="scrub"
            type="range"
            min={0}
            max={Math.max(rows.length - 1, 0)}
            value={safeIndex}
            onChange={(e) => { setPlaying(false); setIndex(Number(e.target.value)); }}
          />
          <div className="scrub-marks">
            {events.map((ev) => (
              <span key={`m${ev.kind}${ev.time}`} className={`mark ${ev.kind}`}
                style={{ left: `${((ev.time - rows[0]?.time) / (rows[rows.length - 1]?.time - rows[0]?.time || 1)) * 100}%` }} />
            ))}
          </div>
        </div>
        <div className="charts">
          <div className="chart-block">
            {manifest && rows.length > 0 && (
              <TemperatureChart
                rows={rows}
                compareRows={compareRows}
                manifest={manifest}
                frameIndex={safeIndex}
                onSeek={(i) => { setPlaying(false); setIndex(i); }}
                accentGlow={probing}
              />
            )}
            <div className="chart-legend">
              <span><i style={{ background: "#ee8f4e" }} />表面</span>
              <span><i style={{ background: "#74b6cc" }} />冷点</span>
              <span><i style={{ background: "#d9c183" }} />估计</span>
              <span><i style={{ background: "#c9a86d" }} />进度 α</span>
              {compare !== "none" && <span className="dash">虚线：对照</span>}
              <span className="dim">红虚线 α=0.85</span>
            </div>
          </div>
          <div className="chart-block narrow">
            {manifest && rows.length > 0 && (
              <ActuatorChart rows={rows} manifest={manifest} frameIndex={safeIndex}
                onSeek={(i) => { setPlaying(false); setIndex(i); }} />
            )}
            <div className="chart-legend">
              <span><i style={{ background: "#e0783c" }} />加热</span>
              <span><i style={{ background: "#74b6cc" }} />蒸汽</span>
              <span><i style={{ background: "#8fa3ad" }} />风机</span>
              <span><i style={{ background: "#8a7b5c" }} />排汽</span>
            </div>
          </div>
        </div>
      </footer>

      {toast && <div className="toast">{toast}</div>}
      {!ready && !error && (
        <div className="loading">
          <div className="spinner" />
          <span>载入轨迹…</span>
        </div>
      )}
    </div>
  );
}



function RunControls({ manifest, policy, setPolicy, cook, setCook, lengthMm, setLengthMm, policyMeta, doorOpen, setDoorOpen }) {
  return (
    <>
      <section className="group">
        <h2>产品档</h2>
        <div className="seg-row">
          {manifest?.cooks.map((c) => (
            <button key={c.key} type="button" className={`seg ${cook === c.key ? "on" : ""}`}
              onClick={() => setCook(c.key)}>{c.label}</button>
          ))}
        </div>
        <h2>策略</h2>
        <div className="policy-list">
          {(manifest?.policies || []).map((p) => (
            <button key={p.key} type="button" className={`policy ${policy === p.key ? "on" : ""}`}
              onClick={() => setPolicy(p.key)}>
              <b>{p.label}</b>
              <i>{p.note}</i>
            </button>
          ))}
        </div>
        <h2>厚度</h2>
        <div className="seg-row">
          {manifest?.lengthsMm.map((mm) => (
            <button key={mm} type="button" className={`seg ${lengthMm === mm ? "on" : ""}`}
              onClick={() => setLengthMm(mm)}>{mm}</button>
          ))}
        </div>
        <h2>腔门</h2>
        <div className="seg-row">
          <button type="button" className={`seg ${doorOpen ? "on" : ""}`} onClick={() => setDoorOpen(true)}>开</button>
          <button type="button" className={`seg ${doorOpen ? "" : "on"}`} onClick={() => setDoorOpen(false)}>关</button>
        </div>
        <p className="rail-note">肉糜 · 初始 8 °C · 含水 0.72 · 种子 7。厚度改变切片的层数与几何，不改已经写出的数组。门开合只改铰链与门互锁的显示，不改已经写出的数组。</p>
      </section>
    </>
  );
}

function TwinControls({
  view, setView, section, setSection, explode, setExplode, annotations, setAnnotations,
  showSteam, setShowSteam, showAirflow, setShowAirflow, orphan, setOrphan, pickedPart,
  doorOpen, setDoorOpen,
}) {
  return (
    <>
      <section className="group">
        <h2>视角</h2>
        <div className="seg-row">
          {VIEW_PRESETS.map((v) => (
            <button key={v.id} type="button" className={`seg ${view === v.id && !section ? "on" : ""}`}
              onClick={() => { setSection(false); setView(v.id); }}>{v.label}</button>
          ))}
        </div>
        <button type="button" className={`toggle ${section ? "on" : ""}`} onClick={() => setSection((s) => !s)}>
          <span>剖切视图</span>
          <i>{section ? "开" : "关"}</i>
        </button>
        <button type="button" className={`toggle ${doorOpen ? "on" : ""}`} onClick={() => setDoorOpen((v) => !v)}>
          <span>腔门开合</span>
          <i>{doorOpen ? "开" : "关"}</i>
        </button>
        <label className="slider-row">
          <span>爆炸分解</span>
          <input type="range" min={0} max={1} step={0.01} value={explode}
            onChange={(e) => setExplode(Number(e.target.value))} />
          <b>{Math.round(explode * 100)}%</b>
        </label>
        <button type="button" className={`toggle ${annotations ? "on" : ""}`} onClick={() => setAnnotations((v) => !v)}>
          <span>零件标注</span>
          <i>{annotations ? "开" : "关"}</i>
        </button>
        <button type="button" className={`toggle ${showSteam ? "on" : ""}`} onClick={() => setShowSteam((v) => !v)}>
          <span>蒸汽粒子</span>
          <i>{showSteam ? "开" : "关"}</i>
        </button>
        <button type="button" className={`toggle ${showAirflow ? "on" : ""}`} onClick={() => setShowAirflow((v) => !v)}>
          <span>气流线</span>
          <i>{showAirflow ? "开" : "关"}</i>
        </button>
        <button type="button" className={`toggle ${orphan ? "" : "on"}`} onClick={() => setOrphan((v) => !v)}>
          <span>腔体照明</span>
          <i>{orphan ? "关" : "开"}</i>
        </button>
        <p className="rail-note">
          建模按家用蒸烤箱可见零件：外壳钢板、岩棉夹层、拉丝内衬、黄铜门框、双层门玻璃、六根 U 形加热管、十叶风机、蒸汽喷嘴、七片排汽百叶、四层搁架。
        </p>
        {pickedPart && <p className="picked">已选部件 <b>{PART_LABEL[pickedPart] || pickedPart}</b></p>}
      </section>
    </>
  );
}

function ProbeControls({ chainStep, setChainStep, frame, rows }) {
  const steps = ["稳态观测", "两段探针", "状态估计", "控制更新", "停止判据"];
  return (
    <>
      <section className="group">
        <h2>机制链</h2>
        <ol className="chain-list">
          {steps.map((label, i) => (
            <li key={label}>
              <button type="button" className={`chain-item ${chainStep === i ? "on" : ""}`}
                onClick={() => setChainStep(i)}>
                <span className="chain-num">{i + 1}</span>
                <span>{label}</span>
              </button>
            </li>
          ))}
        </ol>
        <p className="rail-note">
          五步构成一条链：平衡点上内部热阻不可辨识 → 两段探针买第二个灵敏度方向 → 后验收窄 → 指令更新 → 停机判据被满足多少。
        </p>
      </section>
    </>
  );
}

function CompareControls({ manifest, policy, setPolicy, compare, setCompare, lengthMm, setLengthMm, cook, setCook }) {
  return (
    <>
      <section className="group">
        <h2>主策略</h2>
        <select value={policy} onChange={(e) => setPolicy(e.target.value)}>
          {(manifest?.policies || []).map((p) => <option key={p.key} value={p.key}>{p.label}</option>)}
        </select>
        <h2>对照</h2>
        <select value={compare} onChange={(e) => setCompare(e.target.value)}>
          <option value="none">关闭</option>
          {(manifest?.policies || []).map((p) => <option key={p.key} value={p.key}>{p.label}</option>)}
        </select>
        <h2>产品档</h2>
        <div className="seg-row">
          {(manifest?.cooks || []).map((c) => (
            <button key={c.key} type="button" className={`seg ${cook === c.key ? "on" : ""}`}
              onClick={() => setCook(c.key)}>{c.label}</button>
          ))}
        </div>
        <h2>厚度</h2>
        <div className="seg-row">
          {(manifest?.lengthsMm || []).map((mm) => (
            <button key={mm} type="button" className={`seg ${lengthMm === mm ? "on" : ""}`}
              onClick={() => setLengthMm(mm)}>{mm}</button>
          ))}
        </div>
      </section>
    </>
  );
}

function SurfaceControls({ surface, setSurface, metric, setMetric, policy, setPolicy, surfaces }) {
  return (
    <>
      <section className="group">
        <h2>截面</h2>
        <div className="surface-choices">
          {["LT", "LM", "LH", "LC"].map((k) => (
            <button key={k} type="button" className={`seg ${surface === k ? "on" : ""}`}
              onClick={() => setSurface(k)}>
              {{ LT: "厚度×初温", LM: "厚度×含水", LH: "厚度×夹层", LC: "厚度×档位" }[k]}
            </button>
          ))}
        </div>
        <h2>着色</h2>
        <select value={metric} onChange={(e) => setMetric(Number(e.target.value))}>
          <option value={0}>e_α 中位数</option>
          <option value={1}>停机时刻</option>
          <option value={2}>能耗</option>
          <option value={3}>e_α 标准差</option>
        </select>
        <h2>策略</h2>
        <div className="seg-row wrap">
          {(surfaces?.policies || []).map((p) => (
            <button key={p} type="button" className={`seg ${policy === p ? "on" : ""}`}
              onClick={() => setPolicy(p)}>{p}</button>
          ))}
        </div>
        <p className="rail-note">
          响应面来自主表代际，48 个种子逐格聚合，覆盖 41 个厚度档与 31 个初温档。冷色表示停机偏早，暖色表示已越过设计线。
        </p>
      </section>
    </>
  );
}

function RunInspector({ manifest, scenario, frame, compareFrame, compare, compareMeta, events, onJump }) {
  if (!frame) return <p className="note">载入中…</p>;
  const m = scenario.metrics;
  return (
    <>
      <section className="group">
        <h2>本帧</h2>
        <dl className="readout">
          <div><dt>表面温度</dt><dd>{fmt(frame.tSurf, 2)} °C</dd></div>
          <div><dt>冷点温度</dt><dd>{fmt(frame.tCore, 2)} °C</dd></div>
          <div><dt>冷点估计</dt><dd>{fmt(frame.tHat, 2)} °C</dd></div>
          <div><dt>热力进度 α</dt><dd className={frame.alpha >= 0.85 ? "ok" : ""}>{fmt(frame.alpha, 3)}</dd></div>
          <div><dt>褐变进度</dt><dd>{fmt(frame.alphaB, 3)}</dd></div>
          <div><dt>热阻 / 方差</dt><dd>{fmt(frame.rHat, 2)} / {fmt(frame.varR, 3)}</dd></div>
          <div><dt>平均含水</dt><dd>{fmt(frame.mMean, 3)}</dd></div>
          <div><dt>结壳量</dt><dd>{fmt(frame.shell, 3)}</dd></div>
          <div><dt>腔温 / 腔湿</dt><dd>{fmt(frame.cavT, 1)} °C / {fmt(frame.cavH, 2)}</dd></div>
        </dl>
        <h2>执行器</h2>
        <Meter label="加热" value={frame.heat} />
        <Meter label="蒸汽" value={frame.steam} tone="steam" />
        <Meter label="风机" value={frame.fan / 1.3} tone="fan" />
        <Meter label="排汽" value={frame.exhaust} tone="vent" />
        <Meter label="水位" value={frame.water} tone="water" />
        <div className="tiny-row">
          <span>请求 → 指令</span>
          <b>{fmt(frame.heatReq, 2)} → {fmt(frame.heat, 2)}</b>
        </div>
        <div className="tiny-row">
          <span>加热器</span>
          <b>{fmt(frame.heater, 1)} °C</b>
        </div>
      </section>

      <section className="group">
        <h2>停机判定</h2>
        <dl className="readout tight">
          <div><dt>停机时刻</dt><dd>{Math.round(m.stopS)} s</dd></div>
          <div><dt>停机进度</dt><dd>{fmt(m.alphaAtStop, 3)}</dd></div>
          <div><dt>e<sub>α</sub></dt><dd className={m.eAlpha >= 0 ? "ok" : "warn"}>{m.eAlpha >= 0 ? "+" : ""}{fmt(m.eAlpha, 3)}</dd></div>
          <div><dt>停机冷点</dt><dd>{fmt(m.coreAtStop, 1)} °C</dd></div>
          <div><dt>能量</dt><dd>{Math.round(m.energy)}</dd></div>
          <div><dt>终值方差</dt><dd>{fmt(m.finalVar, 3)}</dd></div>
          <div><dt>首次越线</dt><dd>{m.firstOver85 ? `${Math.round(m.firstOver85)} s` : "未越过"}</dd></div>
        </dl>
        <div className="lamp-row">
          <div className={`lamp ${m.probed ? "ok" : ""}`}>
            <i />
            <span>热阻</span>
            <b>{m.probed ? "已辨识" : "仍先验"}</b>
          </div>
          <div className={`lamp ${m.eAlpha >= 0 ? "ok" : "warn"}`}>
            <i />
            <span>设计线</span>
            <b>{m.eAlpha >= 0 ? "已越过" : "未达"}</b>
          </div>
        </div>
      </section>

      <section className="group">
        <h2>事件</h2>
        <ul className="event-list">
          {events.map((ev) => (
            <li key={`${ev.kind}-${ev.time}`}>
              <button type="button" onClick={() => onJump(ev)}>
                <span className={`dot ${ev.kind}`} />
                <span>{ev.label}</span>
                <b>{Math.round(ev.time)} s</b>
              </button>
            </li>
          ))}
          {!events.length && <li className="muted">本条策略无探针窗。</li>}
        </ul>
        {compare !== "none" && compareFrame && (
          <>
            <h2>对照 · {compareMeta?.label}</h2>
            <dl className="readout tight">
              <div><dt>冷点</dt><dd>{fmt(compareFrame.tCore, 1)} °C</dd></div>
              <div><dt>进度</dt><dd>{fmt(compareFrame.alpha, 3)}</dd></div>
              <div><dt>方差</dt><dd>{fmt(compareFrame.varR, 3)}</dd></div>
            </dl>
          </>
        )}
      </section>
    </>
  );
}

function Meter({ label, value, tone = "" }) {
  const v = Math.max(0, Math.min(1, value ?? 0));
  return (
    <div className="meter">
      <span>{label}</span>
      <div className={`meter-track ${tone}`}><i style={{ width: `${v * 100}%` }} /></div>
      <b>{v.toFixed(2)}</b>
    </div>
  );
}

const PART_LABEL = {
  "food": "食品切片",
  "steam.plume": "蒸汽羽流",
  "steam.tank": "水箱",
  "steam.pipe": "蒸汽管路",
  "steam.valve": "蒸汽阀",
  "steam.nozzle": "蒸汽喷嘴",
  "heater": "加热管组",
  "fan": "离心风机",
  "vent": "排汽百叶",
  "tray": "烤盘",
  "rack": "烤架",
  "frame": "腔口门框",
  "seal": "密封条",
  "bay": "电控舱",
  "fascia": "控制面板",
  "fascia.knob": "旋钮",
  "fascia.led": "指示灯",
  "fascia.display": "显示屏",
  "door.frame": "门外框",
  "door.panel": "门板",
  "door.glass": "门玻璃",
  "door.seal": "门封条",
  "door.handle": "门把手",
  "door.hinge": "铰链",
  "door.striker": "门锁扣",
  "shell.top": "外壳顶板",
  "shell.bottom": "外壳底板",
  "shell.back": "外壳背板",
  "shell.left": "外壳左侧板",
  "shell.right": "外壳右侧板",
  "insulation.top": "顶部保温层",
  "insulation.back": "背部保温层",
  "insulation.left": "左侧保温层",
  "insulation.right": "右侧保温层",
  "liner.floor": "内衬底板",
  "liner.ceiling": "内衬顶板",
  "liner.back": "内衬背板",
  "liner.left": "内衬左侧板",
  "liner.right": "内衬右侧板",
  "sensor.cavityTemp": "腔温热电偶",
  "sensor.humidity": "湿度探头",
  "sensor.heaterProbe": "加热器测温",
  "sensor.doorSwitch": "门互锁",
  "sensor.waterFloat": "水位浮子",
  "sensor.coldSpot": "冷点标记",
  "sensor.estimate": "冷点估计标记",
};

const PART_INFO = {
  "food": ["食品切片", "沿厚度分成十六层，每层颜色取该控制体的温度；第 6 层是脂肪夹层。"],
  "steam.plume": ["蒸汽羽流", "喷嘴喷出的蒸汽粒子，浓度跟蒸汽阀；探针窗内全开并染成暖色。"],
  "heater": ["U 形加热管", "六根串并联加热管，指令 0–1 决定管壁温度上限 250 °C。"],
  "fan": ["十叶离心风机", "后壁风机，档位 0–1.3。档位越高，表面换热系数 h = 12 + 55·fan 越大。"],
  "steam.nozzle": ["双锥蒸汽喷嘴", "左壁直喷。窗内蒸汽升到 1.0，窗外回到基线 0.15。"],
  "vent": ["排汽百叶", "七片百叶，开度跟排汽指令走，改变腔体湿度。"],
  "tray": ["烤盘与烤架", "搪瓷烤盘接住冷凝水，四层搁架改变辐射份额。"],
  "sensor.coldSpot": ["冷点标记", "十六层温度场里最低的那一层。"],
  "sensor.doorSwitch": ["门互锁", "门开即把加热和蒸汽固定在零，属于安全回路。"],
  "sensor.waterFloat": ["水位浮子", "水位低于 0.05 触发干烧保护。"],
  "sensor.heaterProbe": ["加热器测温", "管温超过 230 °C 时按比例削减加热请求。"],
  "sensor.humidity": ["湿度探头", "近排汽口，读腔体相对湿度。"],
  "door.frame": ["门框与密封条", "黄铜勾边，橡胶密封条在关门时压住腔口。"],
  "shell.top": ["外壳顶板", "深色钢板外壳，剖面视图里移开以露出内衬。"],
  "liner.right": ["内衬侧板", "拉丝不锈钢，压花纹理。"],
};

function TwinInspector({ manifest, frame, scenario, pickedPart, onPickPart }) {
  const info = pickedPart ? PART_INFO[pickedPart] : null;
  const label = pickedPart ? (PART_LABEL[pickedPart] || pickedPart) : null;
  return (
    <>
      <section className="group">
        <h2>部件</h2>
        {pickedPart ? (
          <div className="part-card">
            <b>{info ? info[0] : label}</b>
            <p>{info ? info[1] : "该部件属于腔体建模的固定结构，数据通道不单独记录它的状态。"}</p>
            <button type="button" className="ghost-btn" onClick={() => onPickPart(null)}>取消选择</button>
          </div>
        ) : (
          <p className="rail-note">在三维视图里点击任意零件查看它的作用。剖面视图会移开近侧壁板。</p>
        )}
        <dl className="readout">
          <div><dt>加热指令</dt><dd>{fmt(frame?.heat, 2)}</dd></div>
          <div><dt>蒸汽阀</dt><dd>{fmt(frame?.steam, 2)}</dd></div>
          <div><dt>风机档</dt><dd>{fmt(frame?.fan, 2)}</dd></div>
          <div><dt>排汽开度</dt><dd>{fmt(frame?.exhaust, 2)}</dd></div>
          <div><dt>水位</dt><dd>{fmt(frame?.water, 2)}</dd></div>
          <div><dt>腔压</dt><dd>{fmt(frame?.cavP, 3)} bar</dd></div>
        </dl>
      </section>
      <section className="group">
        <h2>厚度场</h2>
        <FieldStack nodes={frame?.nodes} />
      </section>
      <section className="group">
        <h2>建模清单</h2>
        <ul className="spec-list">
          <li>外壳深色钢板，岩棉夹层，拉丝不锈钢内衬</li>
          <li>黄铜门框、橡胶密封条、双层门玻璃</li>
          <li>六根 U 形加热管带陶瓷端帽与反射板</li>
          <li>十叶扭曲翼型风机与穿孔后壁</li>
          <li>左侧管路、水量阀、双锥喷嘴</li>
          <li>七片排汽百叶，随排汽指令转动</li>
          <li>四层搁架与搪瓷烤盘</li>
          <li>五处传感器、门互锁、水位浮子</li>
        </ul>
      </section>
    </>
  );
}

function FieldStack({ nodes }) {
  if (!nodes) return <p className="note">无场数据</p>;
  const min = Math.min(...nodes);
  const max = Math.max(...nodes);
  return (
    <div className="field-stack">
      {Array.from(nodes).reverse().map((v, i) => {
        const t = max > min ? (v - min) / (max - min) : 0.5;
        return (
          <div key={i} className="field-row">
            <span>{15 - i}</span>
            <div className="field-bar"><i style={{ width: `${30 + t * 70}%` }} /></div>
            <b>{v.toFixed(1)}</b>
          </div>
        );
      })}
    </div>
  );
}

function ProbeInspector({ chainStep, setChainStep, rows, frame, scenario, onJump }) {
  if (!rows.length || !frame) return <p className="note">载入中…</p>;
  const pre = rows.filter((r) => r.time < 150);
  const win = rows.filter((r) => r.time >= 150 && r.time < 190);
  const post = rows.filter((r) => r.time >= 190);
  const var0 = pre.length ? pre[0].varR : null;
  const var1 = post.length ? post[0].varR : null;
  const r0 = pre.length ? pre[0].rHat : null;
  const r1 = post.length ? post[0].rHat : null;
  const over = rows.find((r) => r.alpha >= 0.85);
  const probeFrame = frame.time >= 150 && frame.time < 190;

  const steps = [
    {
      title: "稳态观测看不见内部热阻",
      body: "平衡点上内部热阻只以除数出现，对表面温度的偏导为零。采样再密也只是把同一条曲线画细。",
      facts: [
        ["探针前方差", var0 != null ? var0.toFixed(3) : "—"],
        ["探针前 r̂", r0 != null ? r0.toFixed(2) : "—"],
        ["结论", "保持先验"],
      ],
    },
    {
      title: "两段探针打开秩",
      body: "前 20 s 蒸汽全开、排汽关小；后 20 s 风机升到 1.3。先冷凝后对流，两段各贡献一列线性无关的灵敏度。",
      facts: [
        ["窗内帧数", String(win.length)],
        ["蒸汽", win.length ? `${Math.min(...win.map((r) => r.steam)).toFixed(2)} → ${Math.max(...win.map((r) => r.steam)).toFixed(2)}` : "—"],
        ["风机", win.length ? `${Math.min(...win.map((r) => r.fan)).toFixed(2)} → ${Math.max(...win.map((r) => r.fan)).toFixed(2)}` : "—"],
        ["表面温度", win.length ? `${Math.min(...win.map((r) => r.tSurf)).toFixed(1)} → ${Math.max(...win.map((r) => r.tSurf)).toFixed(1)} °C` : "—"],
      ],
    },
    {
      title: "后验在窗后收窄",
      body: "窗结束时若新热阻更接近参照，方差乘 0.35。后验从离散两档变成连续量，25 mm 以上才有第二次判据。",
      facts: [
        ["窗前方差", var0 != null ? var0.toFixed(3) : "—"],
        ["窗后方差", var1 != null ? var1.toFixed(3) : "—"],
        ["收缩倍数", var0 && var1 ? `${(var0 / var1).toFixed(2)}×` : "—"],
        ["窗后 r̂", r1 != null ? r1.toFixed(2) : "—"],
      ],
    },
    {
      title: "控制指令因此改写",
      body: "品质动作按冷点估计给加热请求，信息动作只在窗内替换时间表。停机门槛随方差一起下降。",
      facts: [
        ["当前加热", frame.heat.toFixed(3)],
        ["请求 → 指令", `${frame.heatReq.toFixed(2)} → ${frame.heat.toFixed(2)}`],
        ["模式", ["品质", "探针", "保持"][frame.mode] || "—"],
        ["路径 A/B", `${frame.pathA.toFixed(0)} / ${frame.pathB.toFixed(0)}`],
      ],
    },
    {
      title: "停机判据被满足多少",
      body: "进度越过 0.85 的那一刻记为首次越线；停机偏差 e_α 是停止时刻进度减 0.85。",
      facts: [
        ["当前 α", frame.alpha.toFixed(3)],
        ["首次越线", over ? `${over.time.toFixed(0)} s` : "本次未越线"],
        ["停机", `${Math.round(scenario.metrics.stopS)} s`],
        ["e<sub>α</sub>", `${scenario.metrics.eAlpha >= 0 ? "+" : ""}${scenario.metrics.eAlpha.toFixed(3)}`],
      ],
    },
  ];

  return (
    <>
      <section className="group">
        <h2>{`0${chainStep + 1} · ${steps[chainStep].title}`}</h2>
        <p className="chain-body">{steps[chainStep].body}</p>
        <dl className="readout">
          {steps[chainStep].facts.map(([k, v]) => (
            <div key={k}><dt>{k}</dt><dd>{v}</dd></div>
          ))}
        </dl>
        <div className="chain-actions">
          <button type="button" className="ghost-btn" onClick={() => onJump(160)}>跳到探针窗</button>
          {chainStep < 4 && (
            <button type="button" className="primary-btn" onClick={() => setChainStep(chainStep + 1)}>
              下一步
            </button>
          )}
        </div>
        {probeFrame && <p className="probe-badge">当前帧在探针窗内</p>}
      </section>
    </>
  );
}

function CompareInspector({ manifest, cook, lengthMm, policy, compare }) {
  const pick = (key) => scenarioOf(manifest, key, cook, lengthMm);
  const list = manifest.policies.map((p) => ({ meta: p, row: pick(p.key) })).filter((x) => x.row);
  const best = [...list].sort((a, b) => Math.abs(a.row.metrics.eAlpha) - Math.abs(b.row.metrics.eAlpha))[0];
  return (
    <>
      <section className="group">
        <h2>同一工况 · 五种策略</h2>
        <table className="cmp-table">
          <thead>
            <tr><th>策略</th><th>停机 s</th><th>e<sub>α</sub></th><th>能耗</th></tr>
          </thead>
          <tbody>
            {list.map(({ meta, row }) => (
              <tr key={meta.key} className={meta.key === policy ? "on" : meta.key === compare ? "cmp" : ""}>
                <td>{meta.label}</td>
                <td>{Math.round(row.metrics.stopS)}</td>
                <td className={row.metrics.eAlpha >= 0 ? "ok" : "warn"}>
                  {row.metrics.eAlpha >= 0 ? "+" : ""}{row.metrics.eAlpha.toFixed(3)}
                </td>
                <td>{Math.round(row.metrics.energy)}</td>
              </tr>
            ))}
          </tbody>
        </table>
        <p className="rail-note">
          最接近设计线的是 {best?.meta.label}：e_α = {best?.row.metrics.eAlpha.toFixed(3)}。停机 3300 s 表示被时域终点截住。
        </p>
      </section>
      <section className="group">
        <h2>停机几何</h2>
        <ul className="geo-list">
          <li><b>时钟</b>开环把停止时刻写成厚度的函数，不看冷点。</li>
          <li><b>腔温</b>比例控制停在时域终点，冷点可能已经越过。</li>
          <li><b>点估计</b>按估计冷点停机，无信息动作时方差停在 0.64。</li>
          <li><b>短窗</b>对偶在 150–190 s 离开平衡，窗后方差落到 0.224。</li>
          <li><b>滚动</b>MPC 提前卸热省能量，代价是厚件少走一段。</li>
        </ul>
      </section>
    </>
  );
}

function SurfaceInspector({ surfaces, policy, metric, surface, onPickPolicy }) {
  if (!surfaces) return <p className="note">无响应面数据</p>;
  const grid = surfaces.grids[surface];
  const deep = surfaces.deep.filter((d) => d.policy === policy);
  return (
    <>
      <section className="group">
        <h2>读数</h2>
        <p className="rail-note">{surfaces.note}</p>
        <dl className="readout">
          <div><dt>代际</dt><dd>{surfaces.generation === "baseline" ? "主表代际" : surfaces.generation}</dd></div>
          <div><dt>种子/格</dt><dd>{surfaces.seedsPerCell}</dd></div>
          <div><dt>厚度档</dt><dd>{grid.secondAxis.length}</dd></div>
          <div><dt>第三轴</dt><dd>{grid.thirdAxis.length}</dd></div>
        </dl>
      </section>
      <section className="group">
        <h2>深种子 · {policy}</h2>
        <table className="cmp-table">
          <thead>
            <tr><th>mm</th><th>夹层</th><th>e_α</th><th>停机</th></tr>
          </thead>
          <tbody>
            {deep.map((d) => (
              <tr key={`${d.lengthMm}-${d.hetero}`}>
                <td>{d.lengthMm}</td>
                <td>{["均匀", "抖动", "夹层"][d.hetero]}</td>
                <td>{d.eP50.toFixed(2)}</td>
                <td>{Math.round(d.stopP50)}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </section>
      <section className="group">
        <h2>切换策略</h2>
        <div className="seg-row wrap">
          {surfaces.policies.map((p) => (
            <button key={p} type="button" className={`seg ${policy === p ? "on" : ""}`}
              onClick={() => onPickPolicy(p)}>{p}</button>
          ))}
        </div>
      </section>
    </>
  );
}
