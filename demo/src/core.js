/** Sixteen-cell slab. Same discrete step as the scoring kernel. Not a shader-side solver. */

const ALPHA = 2.0e-7;
const RHO_C = 3.4e6;
const K_BASE = ALPHA * RHO_C;

function unitNoise(seed, step) {
  const x = Math.sin(seed * 12.9898 + step * 78.233) * 43758.5453;
  return (x - Math.floor(x)) * 2 - 1;
}

function gabAw(moisture, proto) {
  const m = Math.min(0.95, Math.max(1e-3, moisture));
  const scale = proto === 1 ? 0.055 : proto === 2 ? 0.08 : 0.1;
  const k = proto === 1 ? 0.8 : proto === 2 ? 0.75 : 0.7;
  const aw = 1 - Math.exp(-m / scale) * (1 - 0.15 * k);
  return Math.min(0.99, Math.max(0.02, aw));
}

export function simulate({
  length = 0.03,
  t0 = 8,
  m0 = 0.72,
  proto = 0,
  hetero = 0,
  seed = 7,
  policy = "dual",
  minutes = 55,
}) {
  const dt = 2;
  const n = 16;
  const steps = Math.floor((minutes * 60) / dt);
  const dx = length / n;
  const policyCode = { open: 1, pid: 2, mpc: 3, dual: 4 }[policy] ?? 4;
  const kCell = Array.from({ length: n }, (_, i) => (hetero === 2 && i === 5 ? 0.45 * K_BASE : K_BASE));
  const alpha = kCell.map((k) => k / RHO_C);
  const temp = Array.from({ length: n }, (_, i) => t0 + (hetero === 1 ? -4 + (8 * i) / (n - 1) : 0));
  const moist = Array(n).fill(m0);
  let fValue = 0;
  let shell = 0;
  let heater = 40;
  let rHat = 5;
  let tcHat = t0;
  let varR = 0.64;
  let probed = false;
  let stopped = false;
  const menu = 900 + 18000 * (length - 0.015);
  const rows = [];

  for (let s = 0; s < steps; s++) {
    const now = s * dt;
    const tCore = Math.min(...temp);
    const mMean = moist.reduce((a, b) => a + b, 0) / n;
    const yT = temp[0] + 0.4 * unitNoise(seed + 17 * policyCode, s);
    const gap = Math.max(temp[0] - tCore, 0.3);
    const rProxy = Math.min(8, Math.max(0.8, gap / 8 + 1.2 + 2.5 * shell));
    const aw = gabAw(moist[0], proto);
    let steam = 0;
    let fan = 0.4;
    let heatReq = 1;
    let mode = 0;

    if (policy === "open") {
      heatReq = now < menu ? 1 : 0;
      steam = now < 0.45 * menu && proto >= 1 ? 0.8 : 0;
      fan = 0.3;
      if (now >= menu) stopped = true;
    } else if (policy === "pid") {
      const yCav = 110 + 0.4 * unitNoise(seed + 17 * policyCode, s) * 0.2;
      heatReq = Math.min(1, Math.max(0, 0.04 * (160 - yCav) + 0.6));
      steam = mMean > 0.2 ? 0.3 : 0;
      fan = 0.45;
    } else {
      const tau = Math.min(8, Math.max(0.8, rHat)) * (length / 0.03) ** 2 * 280;
      tcHat += dt * (yT - tcHat) / tau;
      tcHat = Math.min(tcHat, yT - 4 * Math.max(rHat - 1, 0.2));
      if (policy === "dual") {
        const inProbe = now >= 150 && now < 190 && varR > 0.25 && !probed;
        steam = inProbe && now < 170 ? 1 : 0;
        fan = inProbe && now >= 170 ? 1.3 : 0.4;
        mode = inProbe ? 1 : 0;
        if (now >= 190 && !probed && varR > 0.25) {
          const lag = Math.min(3, Math.max(0, (yT - tcHat) / 6));
          const rNew = Math.min(7, Math.max(0.8, 1.4 + 1.1 * lag + 1.2 * (length / 0.03)));
          if (Math.abs(rNew - rProxy) < Math.abs(rHat - rProxy)) {
            rHat = rNew;
            varR *= 0.35;
          }
          probed = true;
        }
      }
      const margin = 6 + 10 * Math.sqrt(varR) * (length / 0.03);
      heatReq = Math.min(1, Math.max(0.15, 0.35 + (75 + margin - tcHat) / 30));
      const ready = tcHat > 75 + margin && now > 240 && !(policy === "dual" && varR > 0.45 && length > 0.04);
      if (ready) stopped = true;
      if (stopped) {
        heatReq = 0.15;
        mode = 2;
      }
    }

    heater += dt * (0.015 * heatReq * (280 - heater) - 0.008 * (heater - 40));
    const over = Math.min(1, Math.max(0, (heater - 230) / 40));
    const heat = heatReq * (1 - 0.75 * over);
    const h = 12 + 55 * fan;
    const qLat = 18000 * steam * (1 - aw) - 9000 * (1 - steam) * Math.max(aw - 0.35, 0) * fan;
    const tInf = 90 + 95 * heat;
    const flux = h * (tInf - temp[0]) + qLat + 7000 * heat;
    const next = temp.slice();
    for (let i = 1; i < n - 1; i++) {
      next[i] = temp[i] + dt * alpha[i] * (temp[i + 1] - 2 * temp[i] + temp[i - 1]) / dx / dx;
    }
    next[0] = temp[0] + dt * alpha[0] * ((temp[1] - temp[0]) / dx / dx + flux / (K_BASE * dx));
    next[n - 1] = temp[n - 1] + dt * alpha[n - 1] * (temp[n - 2] - temp[n - 1]) / dx / dx;
    for (let i = 0; i < n; i++) next[i] = Math.min(220, Math.max(0, next[i]));

    const dcoef = moist.map((mv) => 2e-9 * (1 + 3 * mv));
    const nextM = moist.slice();
    for (let i = 1; i < n - 1; i++) {
      nextM[i] = moist[i] + dt * dcoef[i] * (moist[i + 1] - 2 * moist[i] + moist[i - 1]) / dx / dx;
    }
    const loss = 1.6e-4 * Math.max(aw - 0.4, 0) * (0.3 + fan) * (1 - steam);
    const gain = 1.1e-4 * steam * (1 - moist[0]);
    nextM[0] = moist[0] + dt * dcoef[0] * ((moist[1] - moist[0]) / dx / dx - loss * n + gain * n);
    nextM[n - 1] = moist[n - 1] + dt * dcoef[n - 1] * (moist[n - 2] - moist[n - 1]) / dx / dx;
    for (let i = 0; i < n; i++) nextM[i] = Math.min(0.95, Math.max(0.02, nextM[i]));

    fValue += dt * 10 ** ((tCore - 70) / 10) / 60;
    shell = Math.min(1, Math.max(0, shell + dt * 1.5e-4 * Math.max(0.45 - moist[0], 0)));
    for (let i = 0; i < n; i++) {
      temp[i] = next[i];
      moist[i] = nextM[i];
    }

    if (s % 4 === 0 || s === steps - 1) {
      rows.push({
        time: now,
        t1: temp[0],
        t2: tCore,
        hat: tcHat,
        heat,
        heatReq,
        steam,
        fan,
        varR,
        heater,
        alpha: 1 - Math.exp(-fValue / 2),
        mode,
        field: temp.slice(),
        moisture: moist.slice(),
        shell,
        aw,
      });
    }
  }
  return rows;
}

export function toCsv(rows) {
  const head = "time,t_surf,t_core,t_hat,heat,heat_req,steam,var_r,heater,alpha_m,mode";
  const body = rows.map((r) =>
    [r.time, r.t1, r.t2, r.hat, r.heat, r.heatReq, r.steam, r.varR, r.heater, r.alpha, r.mode]
      .map((v) => Number(v).toFixed(5)).join(",")
  );
  return [head, ...body].join("\n");
}
