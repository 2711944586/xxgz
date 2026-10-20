import * as THREE from "three";
import { RoundedBoxGeometry } from "three/examples/jsm/geometries/RoundedBoxGeometry.js";
import { brass, chrome, steel } from "./palette.js";

/* Control hardware for the digital twin.
 *
 * Two assemblies carry the machine's information path, and the report's
 * argument depends on them being visible rather than implied:
 *
 *   consolePanel  printed fascia, live numeric display, three actuator dials
 *                 and two status lamps. The display shows what a real panel
 *                 knows: cavity air temperature, dial positions, water level
 *                 and the clock. It never shows the cold spot, which is the
 *                 point chapter 1 makes.
 *   consoleBoard  the board directly behind the fascia: relays, transformer,
 *                 terminal strip, microcontroller, and the capillary
 *                 thermostat whose bulb is clamped to the heating assembly.
 *
 * Both separate in the exploded view and are labelled there.
 */

const V = (x, y, z) => new THREE.Vector3(x, y, z);

/* Fascia: 4.70 m x 0.30 m at 300 px/m, so a legend lands under the part it
   names instead of near it. */
export const FASCIA = { w: 4.70, h: 0.30, depth: 0.17 };

const PPM = 300;

function box(w, h, d, r = 0.012) {
  return new RoundedBoxGeometry(w, h, d, 2, r);
}

function add(parent, geo, mat, pos, rot, part) {
  const m = new THREE.Mesh(geo, mat);
  m.position.copy(pos);
  if (rot) m.rotation.set(rot.x, rot.y, rot.z);
  m.castShadow = true;
  m.receiveShadow = true;
  m.userData.part = part;
  parent.add(m);
  return m;
}

function canvas2d(w, h) {
  const c = document.createElement("canvas");
  c.width = w;
  c.height = h;
  return [c, c.getContext("2d")];
}

function printTexture() {
  const W = Math.round(FASCIA.w * PPM);
  const H = Math.round(FASCIA.h * PPM);
  const [c, ctx] = canvas2d(W, H);
  const g = ctx.createLinearGradient(0, 0, 0, H);
  g.addColorStop(0, "#252d34");
  g.addColorStop(0.62, "#1b2227");
  g.addColorStop(1, "#151b1f");
  ctx.fillStyle = g;
  ctx.fillRect(0, 0, W, H);
  for (let y = 0; y < H; y += 2) {
    ctx.fillStyle = `rgba(255,255,255,${0.010 + (y % 8) * 0.0016})`;
    ctx.fillRect(0, y, W, 1);
  }

  const px = (x) => W / 2 + x * PPM;
  const py = (y) => H / 2 - y * PPM;

  // display well: exactly the screen mesh, with a 2 mm printed margin
  const well = { x0: px(-2.03), x1: px(-0.33), y0: py(0.112), y1: py(-0.112) };
  ctx.fillStyle = "#05090c";
  ctx.fillRect(well.x0, well.y0, well.x1 - well.x0, well.y1 - well.y0);
  ctx.strokeStyle = "rgba(120, 150, 164, 0.24)";
  ctx.lineWidth = 1;
  ctx.strokeRect(well.x0 + 0.5, well.y0 + 0.5, well.x1 - well.x0 - 1, well.y1 - well.y0 - 1);

  // dial legends
  const legend = (x, name) => {
    ctx.textAlign = "center";
    ctx.font = "500 17px 'Microsoft YaHei', 'Noto Sans SC', sans-serif";
    ctx.fillStyle = "rgba(214, 228, 236, 0.9)";
    ctx.fillText(name, px(x), py(0.083));
    ctx.fillStyle = "rgba(224, 120, 60, 0.55)";
    ctx.fillRect(px(x) - 13, py(0.062), 26, 1.5);
  };
  legend(0.97, "加热");
  legend(1.29, "蒸汽");
  legend(1.61, "风机");

  // dial range captions, below the knobs
  const caption = (x, text) => {
    ctx.textAlign = "center";
    ctx.font = "500 12px 'Microsoft YaHei', 'Noto Sans SC', sans-serif";
    ctx.fillStyle = "rgba(140, 172, 188, 0.58)";
    ctx.fillText(text, px(x), py(-0.118));
  };
  caption(0.97, "1–3 档");
  caption(1.29, "0–100 %");
  caption(1.61, "0–3 档");

  const lamp = (x, color, label) => {
    ctx.beginPath();
    ctx.arc(px(x), py(-0.042), 5, 0, Math.PI * 2);
    ctx.fillStyle = color;
    ctx.fill();
    ctx.font = "500 12px 'Microsoft YaHei', 'Noto Sans SC', sans-serif";
    ctx.fillStyle = "rgba(180, 200, 212, 0.6)";
    ctx.textAlign = "center";
    ctx.fillText(label, px(x), py(-0.105));
  };
  lamp(1.90, "#5fe0b0", "电源");
  lamp(2.08, "#e0b45f", "门锁");

  ctx.textAlign = "left";
  ctx.font = "500 11px 'Microsoft YaHei', 'Noto Sans SC', sans-serif";
  ctx.fillStyle = "rgba(122, 150, 164, 0.46)";
  ctx.fillText("ACTS-MCDT", well.x0, py(-0.128));

  const tex = new THREE.CanvasTexture(c);
  tex.colorSpace = THREE.SRGBColorSpace;
  tex.anisotropy = 8;
  return tex;
}

/* Live display: 800 x 100, matching a 1.70 m x 0.212 m panel at ~470 px/m. */
function displaySurface() {
  const canvas = document.createElement("canvas");
  canvas.width = 800;
  canvas.height = 100;
  const tex = new THREE.CanvasTexture(canvas);
  tex.colorSpace = THREE.SRGBColorSpace;
  tex.anisotropy = 8;
  return { canvas, ctx: canvas.getContext("2d"), tex, stamp: null };
}

const CJK = "'Microsoft YaHei', 'Noto Sans SC', 'PingFang SC', sans-serif";
const MONO = "'Cascadia Mono', 'JetBrains Mono', Consolas, monospace";
const pad2 = (v) => String(Math.max(0, Math.round(v))).padStart(2, "0");

function drawDisplay(state, frame, meta) {
  const { ctx } = state;
  const w = 800;
  const h = 100;
  ctx.fillStyle = "#050e12";
  ctx.fillRect(0, 0, w, h);
  for (let y = 0; y < h; y += 3) {
    ctx.fillStyle = "rgba(70, 190, 210, 0.045)";
    ctx.fillRect(0, y, w, 1);
  }

  const cavT = frame?.cavT;
  const heat = frame?.heat ?? 0;
  const steam = frame?.steam ?? 0;
  const fan = frame?.fan ?? 0;
  const water = frame?.water ?? 0;
  const t = frame?.time ?? 0;
  const alpha = frame?.alpha ?? 0;

  ctx.textAlign = "left";
  ctx.font = `500 13px ${CJK}`;
  ctx.fillStyle = "rgba(122, 214, 226, 0.86)";
  ctx.fillText(`${meta.cookLabel || "组合"}档 · 腔温闭环`, 12, 17);

  ctx.font = `500 11px ${CJK}`;
  ctx.fillStyle = "rgba(112, 168, 180, 0.7)";
  ctx.fillText("腔温", 12, 60);
  ctx.font = `600 44px ${MONO}`;
  ctx.fillStyle = "#9ff0f4";
  ctx.fillText(cavT == null ? "--.-" : cavT.toFixed(1), 48, 88);
  ctx.font = `500 17px ${MONO}`;
  ctx.fillStyle = "rgba(140, 226, 236, 0.82)";
  ctx.fillText("°C", 182, 86);

  const gauge = (x, label, value, span, color) => {
    ctx.textAlign = "left";
    ctx.font = `500 11px ${CJK}`;
    ctx.fillStyle = "rgba(126, 190, 202, 0.8)";
    ctx.fillText(label, x, 26);
    ctx.fillStyle = "rgba(80, 190, 205, 0.16)";
    ctx.fillRect(x, 33, 70, 6);
    ctx.fillStyle = color;
    ctx.fillRect(x, 33, 70 * Math.max(0, Math.min(1, value / span)), 6);
    ctx.font = `500 11px ${MONO}`;
    ctx.fillStyle = "rgba(160, 214, 224, 0.7)";
    ctx.fillText(`${Math.round((value / span) * 100)}%`, x, 52);
  };
  gauge(226, "加热", heat, 1, "#f0913f");
  gauge(314, "蒸汽", steam, 1, "#74b6cc");
  gauge(402, "风机", fan, 1.3, "#b9cbd4");

  ctx.textAlign = "right";
  ctx.font = `500 11px ${CJK}`;
  ctx.fillStyle = "rgba(126, 190, 202, 0.72)";
  ctx.fillText("水位", 560, 22);
  ctx.fillText("用时", 560, 44);
  ctx.font = `600 13px ${MONO}`;
  ctx.fillStyle = "rgba(160, 214, 224, 0.88)";
  ctx.fillText(`${Math.round(water * 100)}%`, 620, 22);
  ctx.fillText(`${pad2(t / 60)}:${pad2(t % 60)}`, 620, 44);

  ctx.font = `500 11px ${CJK}`;
  ctx.fillStyle = "rgba(126, 190, 202, 0.72)";
  ctx.fillText(meta.modeLabel || "品质段", 786, 22);
  ctx.font = `500 10px ${MONO}`;
  ctx.fillStyle = "rgba(140, 210, 220, 0.62)";
  ctx.fillText(`α ${alpha.toFixed(3)}`, 786, 40);

  // progress strip with the design-line tick
  ctx.fillStyle = "rgba(80, 190, 205, 0.16)";
  ctx.fillRect(560, 78, 226, 6);
  ctx.fillStyle = "rgba(224, 120, 60, 0.8)";
  ctx.fillRect(560, 78, 226 * Math.max(0, Math.min(1, alpha)), 6);
  ctx.fillStyle = "rgba(242, 228, 202, 0.85)";
  ctx.fillRect(560 + 226 * 0.85, 74, 1, 14);

  state.tex.needsUpdate = true;
}

function electronics() {
  return {
    pcb: new THREE.MeshStandardMaterial({ color: "#1b4736", roughness: 0.6, metalness: 0.24 }),
    plastic: new THREE.MeshStandardMaterial({ color: "#181d21", roughness: 0.68, metalness: 0.14 }),
    relay: new THREE.MeshStandardMaterial({ color: "#25406c", roughness: 0.46, metalness: 0.24 }),
    copper: new THREE.MeshStandardMaterial({ color: "#b87333", roughness: 0.34, metalness: 0.9 }),
    ceramic: new THREE.MeshStandardMaterial({ color: "#cabda2", roughness: 0.82, metalness: 0.04 }),
    tray: steel("#39424a", { metalness: 0.5, roughness: 0.55 }),
    sink: steel("#8e9aa2", { metalness: 0.85, roughness: 0.3 }),
  };
}

/* ------------------------------------------------------------------ panel */

export function buildConsolePanel(materials) {
  const { w, h, depth } = FASCIA;
  const panel = new THREE.Group();
  panel.name = "consolePanel";

  add(panel, box(w, h, depth, 0.016), materials.panel, V(0, 0, 0), null, "console.panel");
  const face = new THREE.Mesh(
    new THREE.PlaneGeometry(w - 0.04, h - 0.015),
    new THREE.MeshStandardMaterial({ map: printTexture(), roughness: 0.56, metalness: 0.24 }),
  );
  face.position.set(0, 0, depth / 2 + 0.0015);
  face.userData.part = "console.panel";
  panel.add(face);

  // display well, live panel, cover glass
  add(panel, box(1.80, 0.235, 0.04, 0.008),
    new THREE.MeshStandardMaterial({ color: "#04080b", roughness: 0.34, metalness: 0.44 }),
    V(-1.18, 0.0, depth / 2 - 0.005), null, "console.bezel");
  const display = displaySurface();
  const screen = new THREE.Mesh(
    new THREE.PlaneGeometry(1.70, 0.212),
    new THREE.MeshBasicMaterial({ map: display.tex, toneMapped: false }),
  );
  screen.position.set(-1.18, 0.0, depth / 2 + 0.014);
  screen.userData.part = "console.screen";
  panel.add(screen);
  const cover = new THREE.Mesh(
    new THREE.PlaneGeometry(1.70, 0.212),
    new THREE.MeshPhysicalMaterial({
      color: "#dcecf2", roughness: 0.05, metalness: 0.0, transparent: true,
      opacity: 0.07, envMapIntensity: 1.8, side: THREE.DoubleSide,
    }),
  );
  cover.position.set(-1.18, 0.0, depth / 2 + 0.0155);
  cover.userData.part = "console.screen";
  panel.add(cover);

  // three dials: brass skirt, chrome cap, index mark, steel shaft back
  const knobs = [0.97, 1.29, 1.61].map((x) => {
    const k = new THREE.Group();
    k.position.set(x, -0.045, depth / 2 + 0.032);
    add(k, new THREE.CylinderGeometry(0.062, 0.068, 0.050, 32), brass(),
      V(0, 0, 0), { x: Math.PI / 2, y: 0, z: 0 }, "console.knob");
    add(k, new THREE.CylinderGeometry(0.040, 0.040, 0.034, 24), chrome(),
      V(0, 0, 0.038), { x: Math.PI / 2, y: 0, z: 0 }, "console.knob");
    const mark = add(k, box(0.008, 0.030, 0.009, 0.002), materials.led,
      V(0, 0.028, 0.052), null, "console.knob");
    mark.castShadow = false;
    add(k, new THREE.CylinderGeometry(0.014, 0.014, 0.18, 14), chrome(),
      V(0, 0, -0.10), { x: Math.PI / 2, y: 0, z: 0 }, "console.knob");
    panel.add(k);
    return k;
  });

  // status lamps
  const lamp = (x, mat) => {
    const m = add(panel, new THREE.CylinderGeometry(0.016, 0.016, 0.016, 16), mat,
      V(x, -0.045, depth / 2 + 0.005), { x: Math.PI / 2, y: 0, z: 0 }, "console.led");
    m.castShadow = false;
    return m;
  };
  const powerLed = lamp(1.90, materials.led);
  const lockLed = lamp(2.08, new THREE.MeshStandardMaterial({
    color: "#8a5a2a", emissive: "#c07a2a", emissiveIntensity: 0.8,
  }));

  // ribbon from the display down to the board
  const ribbon = new THREE.Mesh(
    new THREE.TubeGeometry(new THREE.CatmullRomCurve3([
      V(-1.58, -0.10, -0.02),
      V(-1.24, -0.13, -0.05),
      V(-0.86, -0.12, -0.06),
      V(-0.48, -0.08, -0.06),
    ]), 40, 0.020, 6, false),
    new THREE.MeshStandardMaterial({ color: "#6f5335", roughness: 0.74, metalness: 0.05 }),
  );
  ribbon.scale.set(1, 0.5, 1);
  ribbon.userData.part = "console.ribbon";
  panel.add(ribbon);

  const anchor = new THREE.Object3D();
  anchor.name = "anchor:console";
  anchor.position.set(1.30, 0.0, depth / 2 + 0.05);
  panel.add(anchor);

  return { group: panel, display, parts: { knobs, powerLed, lockLed, face, screen }, anchor };
}

/* ------------------------------------------------------------------ board */

export function buildConsoleBoard() {
  const m = electronics();
  const board = new THREE.Group();
  board.name = "consoleBoard";

  // shallow tray fixed to the cabinet roof, open toward the fascia
  add(board, box(1.66, 0.016, 0.36, 0.004), m.tray, V(0, -0.10, -0.02), null, "ctrl.tray");
  add(board, box(1.66, 0.20, 0.012, 0.004), m.tray, V(0, 0.0, -0.19), null, "ctrl.tray");

  const pcb = new THREE.Group();
  pcb.position.set(0, 0.0, 0.0);
  board.add(pcb);
  add(pcb, box(1.46, 0.24, 0.012, 0.003), m.pcb, V(0, 0, 0), null, "ctrl.board");

  // power relays with drivers
  [-0.54, -0.38].forEach((x) => {
    add(pcb, box(0.12, 0.09, 0.09, 0.008), m.relay, V(x, 0.02, 0.055), null, "ctrl.relay");
    add(pcb, box(0.025, 0.014, 0.025, 0.003), m.ceramic, V(x, -0.055, 0.042), null, "ctrl.relay");
  });
  // mains transformer
  add(pcb, box(0.17, 0.15, 0.10, 0.008), steel("#3a434a", { metalness: 0.5, roughness: 0.55 }),
    V(-0.13, 0.0, 0.062), null, "ctrl.transformer");
  add(pcb, box(0.13, 0.03, 0.08, 0.004), brass(), V(-0.13, 0.09, 0.062), null, "ctrl.transformer");
  // terminal strip
  add(pcb, box(0.62, 0.055, 0.06, 0.005), m.plastic, V(0.02, -0.105, 0.04), null, "ctrl.terminal");
  for (let i = 0; i < 8; i += 1) {
    add(pcb, new THREE.CylinderGeometry(0.009, 0.009, 0.016, 10), brass(),
      V(-0.24 + i * 0.075, -0.105, 0.074), { x: Math.PI / 2, y: 0, z: 0 }, "ctrl.terminal");
  }
  // capacitors, microcontroller, heat sink, fuse
  [-0.34, -0.30].forEach((x) => {
    add(pcb, new THREE.CylinderGeometry(0.022, 0.022, 0.08, 16), m.plastic,
      V(x, 0.03, 0.048), { x: Math.PI / 2, y: 0, z: 0 }, "ctrl.capacitor");
  });
  add(pcb, box(0.11, 0.028, 0.075, 0.003), m.plastic, V(0.06, 0.062, 0.046), null, "ctrl.mcu");
  add(pcb, box(0.06, 0.011, 0.046, 0.002), m.ceramic, V(0.06, 0.081, 0.046), null, "ctrl.mcu");
  add(pcb, box(0.075, 0.14, 0.05, 0.004), m.sink, V(0.24, 0.0, 0.05), null, "ctrl.heatsink");
  add(pcb, box(0.08, 0.05, 0.04, 0.005), m.plastic, V(0.62, 0.0, 0.05), null, "ctrl.fuse");

  // thermostat body on the board
  const stat = new THREE.Group();
  stat.position.set(0.48, 0.02, 0.0);
  pcb.add(stat);
  add(stat, box(0.13, 0.13, 0.10, 0.012), steel("#c9d2d7", { metalness: 0.7, roughness: 0.34 }),
    V(0, 0, 0), null, "ctrl.thermostat");
  add(stat, box(0.085, 0.085, 0.035, 0.006), brass(), V(0, 0, 0.068), null, "ctrl.thermostat");
  add(stat, new THREE.CylinderGeometry(0.016, 0.016, 0.14, 16), chrome(),
    V(0, 0, 0.145), { x: Math.PI / 2, y: 0, z: 0 }, "ctrl.thermostat");

  // capillary coil beside the thermostat
  const coil = [];
  for (let i = 0; i <= 90; i += 1) {
    const k = i / 90;
    const a = k * Math.PI * 6.0;
    coil.push(new THREE.Vector3(
      0.20 + Math.cos(a) * 0.055,
      -0.03 + Math.sin(a) * 0.010,
      0.055 + Math.sin(a) * 0.055,
    ));
  }
  const coilMesh = new THREE.Mesh(
    new THREE.TubeGeometry(new THREE.CatmullRomCurve3(coil), 200, 0.006, 7, false),
    m.copper,
  );
  coilMesh.userData.part = "ctrl.capillary";
  coilMesh.castShadow = true;
  pcb.add(coilMesh);

  const anchor = new THREE.Object3D();
  anchor.name = "anchor:controller";
  anchor.position.set(0.10, 0.06, 0.06);
  board.add(anchor);

  return { group: board, anchor, parts: { pcb, stat, coil: coilMesh } };
}

/* The capillary bulb, clamped to the heater support; parented to the heater so
   it travels with it in the exploded view. */
export function buildThermostatBulb() {
  const m = electronics();
  const g = new THREE.Group();
  g.name = "thermostatBulb";
  add(g, new THREE.CylinderGeometry(0.015, 0.015, 0.18, 12), m.copper,
    V(0, 0, 0), { x: 0, y: 0, z: Math.PI / 2 }, "ctrl.bulb");
  add(g, box(0.05, 0.09, 0.05, 0.008), steel("#9aa6ad", { metalness: 0.8, roughness: 0.3 }),
    V(0, 0, 0), null, "ctrl.bulb");
  add(g, box(0.04, 0.028, 0.04, 0.004), m.ceramic, V(0.11, 0.0, 0.0), null, "ctrl.bulb");

  // the run from the bulb back over the ceiling to the control tray
  const run = [
    V(0.11, 0.0, 0.0),
    V(0.26, 0.06, -0.18),
    V(0.30, 0.13, -0.52),
    V(0.24, 0.16, -0.92),
    V(0.20, 0.17, -1.22),
  ];
  const tube = new THREE.Mesh(
    new THREE.TubeGeometry(new THREE.CatmullRomCurve3(run), 64, 0.0055, 6, false),
    m.copper,
  );
  tube.userData.part = "ctrl.capillary";
  tube.castShadow = true;
  g.add(tube);
  return g;
}

/* Push one frame of the kernel log into the panel. Only the quantities a real
   machine closes are drawn: cavity temperature, dial positions, water, clock. */
export function updateConsole(display, frame, meta) {
  if (!display) return;
  // 4 Hz is enough for a numeric readout, and the canvas is 800x100: redrawing
  // it every animation frame would cost more than the rest of the scene.
  const stamp = frame ? Math.round(frame.time * 4) : -1;
  if (display.stamp === stamp && display.meta === meta?.modeLabel) return;
  display.stamp = stamp;
  display.meta = meta?.modeLabel;
  drawDisplay(display, frame, meta || {});
}
