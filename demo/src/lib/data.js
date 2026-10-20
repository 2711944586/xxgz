export function decodeScenario(manifest, buffer, key) {
  const meta = manifest.scenarios.find((s) => s.key === key);
  if (!meta) throw new Error(`unknown scenario ${key}`);
  const view = new DataView(buffer);
  const stride = manifest.channels.length + manifest.field.cells;
  const base = new Int16Array(buffer, meta.start * stride * 2, meta.frames * stride);
  const field = manifest.field;
  const nodes = [];
  const rows = [];
  for (let i = 0; i < meta.frames; i += 1) {
    const row = {};
    for (let c = 0; c < manifest.channels.length; c += 1) {
      const spec = manifest.channels[c];
      row[spec.key] = spec.offset + base[i * stride + c] * spec.scale;
    }
    const slice = new Float64Array(field.cells);
    for (let k = 0; k < field.cells; k += 1) {
      const q = view.getInt16((meta.start + i) * stride * 2 + (manifest.channels.length + k) * 2, true);
      slice[k] = field.offset + q * field.scale;
    }
    row.nodes = slice;
    rows.push(row);
  }
  return { meta, rows };
}

export function scenarioOf(manifest, policy, cook, lengthMm) {
  const key = `${policy}_${cook}_${lengthMm}`;
  return manifest.scenarios.find((s) => s.key === key) || null;
}

export async function loadDemo() {
  const [manifestRes, surfacesRes, contractRes] = await Promise.all([
    fetch("data/manifest.json"),
    fetch("data/surfaces.json"),
    fetch("dataset.json"),
  ]);
  if (!manifestRes.ok) throw new Error("缺少 data/manifest.json");
  const manifest = await manifestRes.json();
  const surfaces = surfacesRes.ok ? await surfacesRes.json() : null;
  const contract = contractRes.ok ? await contractRes.json() : null;
  const binRes = await fetch("data/traces.bin");
  if (!binRes.ok) throw new Error("缺少 data/traces.bin");
  const buffer = await binRes.arrayBuffer();
  const expectedBytes = manifest.sampling.frames *
    (manifest.channels.length + manifest.field.cells) * 2;
  if (buffer.byteLength !== expectedBytes) {
    throw new Error(`轨迹字节数不符：期望 ${expectedBytes}，实际 ${buffer.byteLength}`);
  }
  return { manifest, surfaces, contract, buffer };
}

export function eventsOf(manifest, scenario) {
  if (!scenario) return [];
  const m = scenario.metrics;
  const events = [];
  const probeStart = manifest.probeWindow[0];
  const probeEnd = manifest.probeWindow[1];
  if (m.probeS != null && m.probed) {
    events.push({ time: probeStart, end: probeEnd, kind: "probe", label: "信息探针窗" });
  }
  if (m.varDropS != null) events.push({ time: m.varDropS, kind: "var", label: "热阻方差下降" });
  if (m.firstOver85 != null) events.push({ time: m.firstOver85, kind: "design", label: "越过设计线 α=0.85" });
  if (m.holdS != null) events.push({ time: m.holdS, kind: "stop", label: "进入保持" });
  if (m.stopS < manifest.sampling.minutes * 60 - 1) {
    events.push({ time: m.stopS, kind: "stop", label: `停机 ${Math.round(m.stopS)} s` });
  }
  return events;
}

export function nearestFrame(rows, timeS) {
  if (!rows.length) return 0;
  let lo = 0;
  let hi = rows.length - 1;
  while (lo < hi) {
    const mid = (lo + hi) >> 1;
    if (rows[mid].time < timeS) lo = mid + 1;
    else hi = mid;
  }
  if (lo > 0 && Math.abs(rows[lo - 1].time - timeS) < Math.abs(rows[lo].time - timeS)) {
    return lo - 1;
  }
  return lo;
}
