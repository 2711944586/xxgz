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

function Chart({ rows, compareRows, index, stopS }) {
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

    if (stopS != null && stopS >= t0 && stopS <= t1) {
      const xs = xOf(stopS);
      ctx.save();
      ctx.setLineDash([2, 4]);
      ctx.strokeStyle = "#7a9e7e";
      ctx.lineWidth = 1;
      ctx.beginPath();
      ctx.moveTo(xs, padT);
      ctx.lineTo(xs, padT + plotH);
      ctx.stroke();
      ctx.restore();
      ctx.fillStyle = "#7a9e7e";
      ctx.font = "10px IBM Plex Mono, monospace";
      ctx.textAlign = "center";
      ctx.textBaseline = "bottom";
      ctx.fillText("停机", xs, padT - 4);
    }

    const x = xOf(rows[Math.min(index, rows.length - 1)].time);
    ctx.strokeStyle = "#ece7dc";
    ctx.lineWidth = 1;
    ctx.beginPath();
    ctx.moveTo(x, padT);
    ctx.lineTo(x, padT + plotH);
    ctx.stroke();
  }, [rows, compareRows, index, stopS]);
  return <canvas ref={ref} className="chart" />;
}

// The five stages of the experiment, in the order a reader needs them.
// Each states the question it answers, because a navigation label alone does
// not tell a viewer why they should look there.
const STAGES = [
  { id: "overview", no: "01", title: "实验总览",
    question: "这次仿真的工况、模型代际与最终判定是什么？",
    targets: ["fascia", "verdict"] },
  { id: "twin", no: "02", title: "数字孪生",
    question: "腔体内部的热场、冷点与执行器此刻在做什么？",
    targets: ["scene"] },
  { id: "identify", no: "03", title: "信息辨识",
    question: "探针窗如何把热阻从不可辨识变成可见？",
    targets: ["events", "hud"] },
  { id: "strategy", no: "04", title: "策略对照",
    question: "四条策略在同一工况下的停机与能耗差多少？",
    targets: ["controls", "fascia"] },
  { id: "report", no: "05", title: "结果与边界",
    question: "这些数字的来源、模型边界与可复现信息在哪？",
    targets: ["boundaries", "export"] },
];

/**
 * The mechanism chain: five stages of the causal argument, each showing the real
 * numbers it depends on. Pure render -- no effects, no local derived state beyond
 * the selected tab -- so it cannot interfere with data loading.
 */
function MechanismChain({ rows, frame }) {
  const [open, setOpen] = useState("steady");

  if (!rows.length || !frame) {
    return (
      <section className="chain">
        <p className="panel-label">机制链</p>
        <p className="note">轨迹未加载，机制链不可用。</p>
      </section>
    );
  }

  const preProbe = rows.filter((r) => r.time < 150);
  const probe = rows.filter((r) => r.time >= 150 && r.time < 190);
  const postProbe = rows.filter((r) => r.time >= 190);
  const varBefore = preProbe.length ? preProbe[0].varR : null;
  const varAfter = postProbe.length ? postProbe[0].varR : null;
  const rHatAfter = postProbe.length ? postProbe[0].rHat : null;
  const firstOver = rows.find((r) => r.alpha >= 0.85);
  const rng = (xs) => (xs.length ? `${Math.min(...xs).toFixed(2)} → ${Math.max(...xs).toFixed(2)}` : "—");

  const stages = [
    {
      id: "steady", no: "1", title: "稳态观测不足",
      q: "停在平衡点时，内部热阻能被看出来吗？",
      facts: [
        ["探针前方差", varBefore != null ? varBefore.toFixed(3) : "—"],
        ["探针前 r̂", preProbe.length ? preProbe[0].rHat.toFixed(2) : "—"],
        ["结论", "方差保持先验"],
      ],
      why: "平衡点上内部热阻只以除数出现，求导为零；采样再密也只是把同一条曲线画细。",
      fail: "若这里就能看见热阻，探针窗就是多余的。",
    },
    {
      id: "probe", no: "2", title: "信息探针",
      q: "离开平衡的 40 秒里，执行器做了什么？",
      facts: [
        ["窗内帧数", String(probe.length)],
        ["蒸汽", rng(probe.map((r) => r.steam))],
        ["风机", rng(probe.map((r) => r.fan))],
        ["表面温度", probe.length
          ? `${rng(probe.map((r) => r.t1))} °C` : "—"],
      ],
      why: "先蒸汽改相变符号、后风机改外部热阻，两段各贡献一列线性无关的灵敏度。",
      fail: "若两段同向，灵敏度矩阵仍秩亏，探针等于白做。",
    },
    {
      id: "estimate", no: "3", title: "状态估计",
      q: "后验收窄了多少？",
      facts: [
        ["窗前方差", varBefore != null ? varBefore.toFixed(3) : "—"],
        ["窗后方差", varAfter != null ? varAfter.toFixed(3) : "—"],
        ["窗后 r̂", rHatAfter != null ? rHatAfter.toFixed(2) : "—"],
        ["收缩倍数", varBefore && varAfter ? `${(varBefore / varAfter).toFixed(2)}×` : "—"],
      ],
      why: "接受判据把新热阻与参照比较，通过则方差乘 0.35，后验从离散两档变成连续量。",
      fail: "若方差不动，说明表面温差不够、更新被拒（蒸档就是这样）。",
    },
    {
      id: "control", no: "4", title: "控制更新",
      q: "后验变化改写了哪些指令？",
      facts: [
        ["当前加热", frame.heat.toFixed(3)],
        ["请求 vs 指令", `${frame.heatReq.toFixed(2)} → ${frame.heat.toFixed(2)}`],
        ["模式", String(frame.mode)],
        ["路径 A/B", `${frame.pathA.toFixed(0)} / ${frame.pathB.toFixed(0)}`],
      ],
      why: "品质动作按冷点估计给加热请求；信息动作只在窗内替换时间表。",
      fail: "若后验更窄而指令不变，说明改进的估计没有进入决策。",
    },
    {
      id: "stop", no: "5", title: "停止判据",
      q: "最终是否满足模型条件？",
      facts: [
        ["当前进度 α", frame.alpha.toFixed(3)],
        ["设计线", "0.85（模型判据，非认证）"],
        ["首次越线", firstOver ? `${firstOver.time.toFixed(0)} s` : "本次未越线"],
        ["冷点", `${frame.t2.toFixed(1)} °C`],
      ],
      why: "停机偏差 e_α 定义为停止时刻进度减 0.85，衡量这条判据被满足得多准。",
      fail: "若进度到 0.85 而冷点不足，说明模型判据与真实熟度不一致。",
    },
  ];

  const active = stages.find((x) => x.id === open) || stages[0];

  return (
    <section className="chain">
      <div className="chain-head">
        <p className="panel-label">机制链</p>
        <span className="chain-hint">点每一步查看它依赖的真实数据</span>
      </div>
      <div className="chain-track">
        {stages.map((st) => (
          <button key={st.id} type="button"
            className={`chain-node ${open === st.id ? "active" : ""}`}
            onClick={() => setOpen(st.id)}>
            <span className="chain-no">{st.no}</span>
            <span className="chain-title">{st.title}</span>
          </button>
        ))}
      </div>
      <div className="chain-body">
        <p className="chain-q">{active.q}</p>
        <dl className="chain-facts">
          {active.facts.map(([k, v]) => (
            <div key={k}><dt>{k}</dt><dd>{v}</dd></div>
          ))}
        </dl>
        <p className="chain-why">{active.why}</p>
        <p className="chain-fail"><b>失效条件</b>{active.fail}</p>
      </div>
    </section>
  );
}

export default function App() {
  const [catalog, setCatalog] = useState([]);
  const [policy, setPolicy] = useState("dual");
  const [compare, setCompare] = useState("none");
  const [cook, setCook] = useState("combi");
  const [length, setLength] = useState(0.03);
  const [index, setIndex] = useState(0);
  const [playing, setPlaying] = useState(false);
  const [playSpeed, setPlaySpeed] = useState(4);
  const [sectionView, setSectionView] = useState(false);
  const [activeStage, setActiveStage] = useState("overview");
  const [rightTab, setRightTab] = useState("readout");
  // Each stage points at existing DOM regions rather than duplicating content.
  // The lookup must tolerate a target that has not mounted yet, otherwise the
  // throw inside this effect cancels the state update and navigation dies.
  const stageRefs = useRef({});
  useEffect(() => {
    const target = {
      overview: "fascia",
      twin: "scene",
      identify: "events",
      strategy: "controls",
      report: "boundaries",
    }[activeStage];
    const el = target ? stageRefs.current[target] : null;
    try {
      if (el && typeof el.scrollIntoView === "function") {
        el.scrollIntoView({ behavior: "smooth", block: "nearest" });
      }
    } catch {
      // Navigation is a convenience; never let it break the page.
    }
  }, [activeStage]);
  const [doorOpen, setDoorOpen] = useState(true);
  const [error, setError] = useState("");
  const [contract, setContract] = useState(null);
  const [contractError, setContractError] = useState("");

  useEffect(() => {
    fetch("./catalog.json")
      .then((res) => {
        if (!res.ok) throw new Error("catalog");
        return res.json();
      })
      .then(setCatalog)
      .catch(() => setError("无法读取 catalog.json，请先运行 scripts/export_demo_trace.py。"));
  }, []);

  // The contract states what this page actually is: an offline replay of a
  // specific kernel generation. It is loaded separately so that a missing or
  // stale contract degrades into a visible warning rather than a silent claim.
  useEffect(() => {
    fetch("./dataset.json")
      .then((res) => {
        if (!res.ok) throw new Error("dataset");
        return res.json();
      })
      .then(setContract)
      .catch(() => setContractError("缺少 dataset.json：无法确认模型代际与数据来源。"));
  }, []);

  // Verify the catalog against the contract fingerprints once both are loaded.
  useEffect(() => {
    if (!contract || catalog.length === 0) return;
    const expected = contract.sampling?.total_frames;
    const scens = Object.keys(contract.scenarios || {}).length;
    const actualScens = new Set(catalog.map((r) => r.key)).size;
    if (expected && expected !== catalog.length) {
      setContractError(
        `数据契约不符：契约声明 ${expected} 帧，实际 ${catalog.length} 帧。`,
      );
    } else if (scens && scens !== actualScens) {
      setContractError(
        `数据契约不符：契约声明 ${scens} 条轨迹，实际 ${actualScens} 条。`,
      );
    } else {
      setContractError("");
    }
  }, [contract, catalog]);

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
    // Base cadence 40 ms per frame; speed multiplies the step.
    const step = Math.max(1, Math.round(playSpeed / 1));
    const id = window.setInterval(() => {
      setIndex((i) => (i + step) % rows.length);
    }, 40);
    return () => window.clearInterval(id);
  }, [playing, rows.length, playSpeed]);

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
  const mm = Math.round(length * 1000);
  const stopS = score ? score.stopS : null;
  const varText = score
    ? (score.probed
      ? `方差 ${score.varEnd.toFixed(3)}`
      : `仍为先验 ${score.varEnd.toFixed(3)}`)
    : "—";

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
          <span className={`chip prov ${contract ? "ok" : contractError ? "bad" : ""}`}
                title={contract ? contract.mode.statement_zh : contractError || "正在读取数据契约"}>
            {contract ? contract.mode.label_zh : contractError ? "来源未确认" : "读取契约…"}
          </span>
          <span className={`chip prov ${contract ? "gen" : ""}`}
                title={contract ? contract.kernel.why : ""}>
            {contract ? `数值核 ${contract.kernel.generation}` : "代际未知"}
          </span>
          <span className="chip">种子 7 · 肉糜 · 8 °C · 含水 0.72</span>
          <span className={`chip ${cook === "steam" ? "steam" : "on"}`}>{cookLabel}</span>
          <span className="chip">{policyLabel}</span>
          <span className="chip">{mm} mm</span>
          {probing && <span className="chip steam">探针窗</span>}
          {frame && <span className={`chip ${frame.mode === 1 ? "steam" : frame.mode === 2 ? "hold" : ""}`}>{MODES[frame.mode] || "—"}</span>}
        </div>
      </header>

      {contractError && (
        <div className="contract-warn" role="alert">
          <b>数据契约警告</b>
          <span>{contractError}</span>
        </div>
      )}

      {contract && (
        <details className="boundary-drawer" ref={(el) => { stageRefs.current.boundaries = el; }}>
          <summary>
            <span className="bd-title">模型边界</span>
            <span className="bd-count">{contract.boundaries.length} 条</span>
            <span className="bd-hint">
              代际 {contract.kernel.generation} · 与主表差
              {contract.kernel.differing_switches.length} 个开关
            </span>
          </summary>
          <ul className="bd-list">
            {contract.boundaries.map((b) => (
              <li key={b.id} className={`bd-item sev-${b.severity}`}>
                <span className={`diag-dot ${b.severity}`} />
                <div>
                  <p className="bd-id">{b.id}<span className="bd-where">{b.where}</span></p>
                  <p className="bd-text">{b.zh}</p>
                </div>
              </li>
            ))}
          </ul>
        </details>
      )}

      <nav className="stages" aria-label="实验阶段">
        {STAGES.map((stage) => (
          <button
            key={stage.id}
            type="button"
            className={`stage ${activeStage === stage.id ? "active" : ""}`}
            onClick={() => setActiveStage(stage.id)}
            title={stage.question}
          >
            <span className="stage-no">{stage.no}</span>
            <span className="stage-title">{stage.title}</span>
            <span className="stage-q">{stage.question}</span>
          </button>
        ))}
      </nav>

      <div className="fascia" aria-live="polite" ref={(el) => { stageRefs.current.fascia = el; }}>
        <div className="fascia-cell">
          <span>本帧</span>
          <b>{frame ? `${Math.round(frame.time)} s` : "—"}</b>
        </div>
        <div className="fascia-cell">
          <span>冷点</span>
          <b>{frame ? `${frame.t2.toFixed(1)} °C` : "—"}</b>
        </div>
        <div className="fascia-cell">
          <span className="keep-case">进度 α</span>
          <b className={frame && frame.alpha >= 0.85 ? "over" : "under"}>
            <i className={`led ${frame && frame.alpha >= 0.85 ? "ok" : "off"}`} />
            {frame ? frame.alpha.toFixed(3) : "—"}
          </b>
        </div>
        <div className="fascia-cell">
          <span>停机</span>
          <b>{stopS != null ? `${Math.round(stopS)} s` : "—"}</b>
        </div>
        <div className="fascia-cell">
          <span>相对 0.85</span>
          <b className={score && score.eAlpha >= 0 ? "over" : "under"}>
            {score ? `${score.eAlpha >= 0 ? "+" : ""}${score.eAlpha.toFixed(3)}` : "—"}
          </b>
        </div>
        <div className="fascia-cell">
          <span>热阻方差</span>
          <b className={frame && frame.varR < 0.3 ? "over" : "under"}>
            <i className={`led ${frame && frame.varR < 0.3 ? "ok" : "off"}`} />
            {frame ? frame.varR.toFixed(3) : "—"}
          </b>
        </div>
      </div>

      {error && <p className="err">{error}</p>}

      <main className="workspace">
        <aside className="panel controls" ref={(el) => { stageRefs.current.controls = el; }}>
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
            <button type="button" className={`chip-btn ${length === 0.015 ? "active" : ""}`} onClick={() => { setLength(0.015); setIndex(0); }}>15 mm</button>
            <button type="button" className={`chip-btn ${length === 0.03 ? "active" : ""}`} onClick={() => { setLength(0.03); setIndex(0); }}>30 mm</button>
            <button type="button" className={`chip-btn ${length === 0.05 ? "active" : ""}`} onClick={() => { setLength(0.05); setIndex(0); }}>50 mm</button>
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
          <label>播放速度</label>
          <div className="events">
            {[1, 2, 4, 8].map((sp) => (
              <button
                key={sp}
                type="button"
                className={`chip-btn ${playSpeed === sp ? "active" : ""}`}
                onClick={() => setPlaySpeed(sp)}
              >
                {sp}×
              </button>
            ))}
          </div>
          <label>视图</label>
          <div className="events">
            <button
              type="button"
              className={`chip-btn ${!sectionView ? "active" : ""}`}
              onClick={() => setSectionView(false)}
            >
              外观
            </button>
            <button
              type="button"
              className={`chip-btn ${sectionView ? "active" : ""}`}
              onClick={() => setSectionView(true)}
            >
              剖面
            </button>
          </div>
          <div className="playrow">
            <button type="button" className="ghost" onClick={downloadAll} disabled={!frame}>
              导出 CSV
            </button>
            <button type="button" className="ghost keep-case" onClick={() => jumpTo(1680)} disabled={!frame}>
              1680 s
            </button>
          </div>
          <p className="panel-label" ref={(el) => { stageRefs.current.events = el; }}>事件</p>
          <div className="events">
            <button type="button" className="chip-btn" onClick={() => jumpTo(0)}>起始</button>
            <button type="button" className="chip-btn" onClick={() => jumpTo(160)}>探针窗</button>
            <button type="button" className="chip-btn" onClick={() => jumpTo(1680)}>1680 s</button>
            <button
              type="button"
              className="chip-btn"
              onClick={() => { if (stopS != null) jumpTo(stopS); }}
              disabled={stopS == null}
            >
              停机{stopS != null ? ` ${Math.round(stopS)} s` : ""}
            </button>
          </div>
          {score && (
            <div className="verdict">
              <div className="lamps" aria-label="两盏判断灯">
                <div className={`lamp ${frame && frame.varR < 0.3 ? "on-ok" : "on-off"}`}>
                  <i />
                  <div>
                    <small>热阻</small>
                    <span>{frame && frame.varR < 0.3 ? "已见" : "先验"}</span>
                  </div>
                </div>
                <div className={`lamp ${frame && frame.alpha >= 0.85 ? "on-ok" : "on-off"}`}>
                  <i />
                  <div>
                    <small>进度</small>
                    <span>{frame && frame.alpha >= 0.85 ? "已到" : "未到"}</span>
                  </div>
                </div>
              </div>
              <div className="row"><span>停机</span><span>{Math.round(score.stopS)} s</span></div>
              <div className="row"><span>e<sub>α</sub></span><span>{score.eAlpha >= 0 ? "+" : ""}{score.eAlpha.toFixed(3)}</span></div>
              <div className="row"><span>探针</span><span>{varText}</span></div>
              <div className="row"><span>相对 0.85</span><span>{score.eAlpha >= 0 ? "越过设计线" : "低于设计线"}</span></div>
              <div className="row"><span>停机冷点</span><span>{score.tCoreStop.toFixed(1)} °C</span></div>
              <div className="row"><span>停机进度</span><span>{score.alphaStop.toFixed(3)}</span></div>
            </div>
          )}
          <p className="note">
            页面读取数值核已经写出的状态流，不在浏览器里重跑积分。对照策略以虚线叠在底部曲线上。开门只改铰链，不改温度数组。红虚线是设计线 α=0.85。两盏灯跟本帧走：热阻是否已看见，进度是否越过 0.85。水位条只显示当前帧水箱液面。停机跳转到当前轨迹的评分时刻：30 mm 对偶组合约 1864 s，50 mm 为 3298 s。开局估计为负时 HUD 标为开局余量，来自先验热阻 5 的滞后上限。
          </p>
        </aside>

        <section className="panel viewport" ref={(el) => { stageRefs.current.scene = el; }}>
          <p className="panel-label" style={{ position: "absolute", zIndex: 2, left: 16, top: 10 }}>02 腔体</p>
          <Scene frame={frame} length={length} doorOpen={doorOpen} cook={cook} section={sectionView} />
          {frame && (
            <div className="hud">
              <p className="hud-kicker keep-case">{cookLabel} · {policyLabel} · {mm} mm</p>
              <div>表面 <b>{frame.t1.toFixed(1)} °C</b></div>
              <div>冷点 <b>{frame.t2.toFixed(1)} °C</b></div>
              <div>
                估计 <b>{frame.hat.toFixed(1)} °C</b>
                {frame.hat < 0 ? <em className="hud-hint">开局余量</em> : null}
              </div>
              <div>进度 <b className={frame.alpha >= 0.85 ? "over" : ""}>{frame.alpha.toFixed(3)}</b></div>
              <div>时间 <b>{Math.round(frame.time)} s</b></div>
              <div>模式 <b>{MODES[frame.mode] || "—"}</b></div>
              <div className="hud-lamps" aria-hidden="true">
                <span className={frame.varR < 0.3 ? "ok" : ""}>热阻{frame.varR < 0.3 ? "已见" : "先验"}</span>
                <span className={frame.alpha >= 0.85 ? "ok" : ""}>进度{frame.alpha >= 0.85 ? "已到" : "未到"}</span>
              </div>
            </div>
          )}
          <div className="legend">
            <span>冷</span>
            <span className="ramp" />
            <span>热</span>
          </div>
        </section>

        <aside className="panel">
          <div className="right-tabs" role="tablist">
            <button type="button" role="tab"
              className={`right-tab ${rightTab === "readout" ? "active" : ""}`}
              aria-selected={rightTab === "readout"}
              onClick={() => setRightTab("readout")}>本帧读数</button>
            <button type="button" role="tab"
              className={`right-tab ${rightTab === "chain" ? "active" : ""}`}
              aria-selected={rightTab === "chain"}
              onClick={() => setRightTab("chain")}>机制链</button>
          </div>

          {rightTab === "chain" ? (
            <MechanismChain rows={rows} frame={frame} />
          ) : (
          <>
          <p className="panel-label">03 本帧</p>
          {!frame && !error && <p className="note">正在读取 catalog.json …</p>}
          {frame && (
            <div className="kv">
              <div className="row"><span>含水</span><span>{frame.m.toFixed(3)}</span></div>
              <div className="row"><span>进度 α</span><span>{frame.alpha.toFixed(3)}</span></div>
              <div className="row"><span>热阻 / 方差</span><span>{frame.rHat.toFixed(2)} / {frame.varR.toFixed(3)}</span></div>
              <div className="row"><span>腔温 / 腔湿</span><span>{frame.cavT.toFixed(1)} °C / {frame.cavH.toFixed(2)}</span></div>
              <div className="row tank-row">
                <span>水位</span>
                <span className="tank-read">
                  <span className="tank" aria-hidden="true">
                    <i style={{ height: `${Math.max(0, Math.min(1, frame.water)) * 100}%` }} />
                  </span>
                  <em>{frame.water.toFixed(2)}</em>
                </span>
              </div>
              <p className="panel-label">执行器</p>
              <Meter name="加热" value={frame.heat} />
              <Meter name="蒸汽" value={frame.steam} kind="steam" />
              <Meter name="风机" value={frame.fan / 1.3} kind="fan" />
              <Meter name="排汽" value={frame.exhaust} />
              <p className="panel-label">路径与投影</p>
              <PathMeter name="A 冷点潜热" value={frame.pathA} max={220} kind="heat" />
              <PathMeter name="B 表面蒸发" value={frame.pathB} max={2200} kind="steam" />
              <PathMeter name="C 结壳热阻" value={frame.pathC} max={1} kind="fan" />
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
          </>
          )}
        </aside>
      </main>

      <footer className="chartbar">
        <Chart rows={rows} compareRows={compareRows} index={index} stopS={stopS} />
        <div className="chart-legend">
          <span><i className="dot" style={{ background: "#e07a3d" }} />表面温度</span>
          <span><i className="dot" style={{ background: "#7eb8c9" }} />冷点温度</span>
          <span><i className="dot" style={{ background: "#d8c07a" }} />估计温度</span>
          <span><i className="dot" style={{ background: "#c4a574" }} />进度 α（右轴）</span>
          {compare !== "none" && <span>虚线：对照冷点 / 进度</span>}
          <span>红虚线：设计线 0.85</span>
          <span>绿虚线：当前轨迹停机</span>
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

function formatPath(value) {
  const a = Math.abs(value);
  if (a >= 10) return value.toFixed(0);
  if (a >= 1) return value.toFixed(1);
  return value.toFixed(3);
}

function PathMeter({ name, value, max, kind }) {
  const x = Math.max(0, Math.min(1, Math.abs(value) / (max || 1)));
  return (
    <div className="row path-row">
      <span>{name}</span>
      <span className="path-read">
        <span className={`bar ${kind || ""}`}><i style={{ width: `${x * 100}%` }} /></span>
        <em>{formatPath(value)}</em>
      </span>
    </div>
  );
}
