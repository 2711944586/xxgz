import { useMemo, useState } from "react";
import Scene from "./Scene.jsx";
import { simulate, toCsv } from "./core.js";

export default function App() {
  const [policy, setPolicy] = useState("dual");
  const [length, setLength] = useState(0.03);
  const [index, setIndex] = useState(0);
  const [slice, setSlice] = useState(0.1);
  const rows = useMemo(
    () => simulate({ length, policy, seed: 7, t0: 8, m0: 0.72, minutes: 55 }),
    [length, policy],
  );
  const frame = rows[Math.min(index, rows.length - 1)];
  const cell = Math.min(15, Math.max(0, Math.round(slice * 15)));

  function download() {
    const blob = new Blob([toCsv(rows)], { type: "text/csv" });
    const a = document.createElement("a");
    a.href = URL.createObjectURL(blob);
    a.download = `trajectory_${policy}_L${Math.round(length * 1000)}.csv`;
    a.click();
  }

  return (
    <>
      <header>
        <div>
          <p className="kicker">ACTS-MCDT</p>
          <h1>热加工认知闭环</h1>
        </div>
        <p className="lede">
          十六个控制体按评分核的显式格式推进。颜色是该控制体的温度，色标固定在 5 °C 到 170 °C。切面读的是选中的那一块，不在着色器里解热方程。
        </p>
      </header>
      <main className="layout">
        <section className="panel">
          <label>策略</label>
          <select value={policy} onChange={(e) => { setPolicy(e.target.value); setIndex(0); }}>
            <option value="dual">对偶</option>
            <option value="mpc">无探针</option>
            <option value="open">开环</option>
            <option value="pid">腔温比例</option>
          </select>
          <label>厚度 {Math.round(length * 1000)} mm</label>
          <input type="range" min="0.015" max="0.05" step="0.005" value={length}
            onChange={(e) => { setLength(Number(e.target.value)); setIndex(0); }} />
          <label>时间 {Math.round(frame.time)} s</label>
          <input type="range" min="0" max={rows.length - 1} value={index}
            onChange={(e) => setIndex(Number(e.target.value))} />
          <label>控制体 {cell}，距表面 {((cell + 0.5) / 16 * length * 1000).toFixed(1)} mm</label>
          <input type="range" min="0" max="1" step="0.01" value={slice}
            onChange={(e) => setSlice(Number(e.target.value))} />
          <button type="button" onClick={download}>下载这条轨迹</button>
          <p className="note">种子固定为 7，初温 8 °C，含水 0.72，肉糜，均匀。厚度改变之后重新积分。热阻更新仍用真值温差作参照。</p>
        </section>
        <section className="panel">
          <Scene frame={frame} slice={slice} />
          <Profile field={frame.field} cell={cell} />
          <div className="row"><span>表面</span><span>{frame.t1.toFixed(1)} °C</span></div>
          <div className="row"><span>冷点</span><span>{frame.t2.toFixed(1)} °C</span></div>
          <div className="row"><span>估计</span><span>{frame.hat.toFixed(1)} °C</span></div>
          <div className="row"><span>选中控制体</span><span>{frame.field[cell].toFixed(1)} °C</span></div>
          <div className="row"><span>进度</span><span>{frame.alpha.toFixed(3)}</span></div>
        </section>
        <section className="panel">
          <h2>这一帧能读出的量</h2>
          <div className="row"><span>加热请求</span><span>{frame.heatReq.toFixed(2)}</span></div>
          <div className="row"><span>加热指令</span><span>{frame.heat.toFixed(2)}</span></div>
          <div className="row"><span>蒸汽</span><span>{frame.steam.toFixed(2)}</span></div>
          <div className="row"><span>风机</span><span>{frame.fan.toFixed(2)}</span></div>
          <div className="row"><span>热阻方差</span><span>{frame.varR.toFixed(3)}</span></div>
          <div className="row"><span>加热器</span><span>{frame.heater.toFixed(1)} °C</span></div>
          <div className="row"><span>表面活度</span><span>{frame.aw.toFixed(3)}</span></div>
          <div className="row"><span>结壳</span><span>{frame.shell.toFixed(3)}</span></div>
          <p className="note">加热请求与加热指令在加热器低于 230 °C 时重合。结壳不改变十六个控制体的导热。</p>
        </section>
      </main>
    </>
  );
}

function Profile({ field, cell }) {
  return (
    <canvas
      width={640}
      height={92}
      style={{ width: "100%", height: 92, marginTop: 8, borderRadius: 8, background: "#d9d3c7" }}
      ref={(node) => {
        if (!node || !field) return;
        const ctx = node.getContext("2d");
        const w = node.width;
        const h = node.height;
        ctx.clearRect(0, 0, w, h);
        field.forEach((value, i) => {
          const x = Math.min(1, Math.max(0, (value - 5) / 165));
          ctx.fillStyle = `hsl(${28 - 26 * x} 62% ${72 - 38 * x}%)`;
          const bx = (i * w) / 16 + 1;
          ctx.fillRect(bx, 8, w / 16 - 3, h - 16);
          if (i === cell) {
            ctx.strokeStyle = "#1c1914";
            ctx.strokeRect(bx, 8, w / 16 - 3, h - 16);
          }
        });
      }}
    />
  );
}
