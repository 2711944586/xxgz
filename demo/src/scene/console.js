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
 *   consoleBoard  relays, transformer, terminal strip, microcontroller and the
 *                 capillary thermostat that switches the heater, mounted in
 *                 the front-top compartment directly behind the fascia.
 *
 * Both separate in the exploded view and are labelled there. A section view
 * lifts the top panels and exposes the board over the cavity ceiling.
 */

const V = (x, y, z) => new THREE.Vector3(x, y, z);

/* Fascia module: 4.86 m x 0.30 m, 0.26 m deep. It is bolted onto the cabinet
   front above the door, standing proud of the door plane by about the depth of
   a real control box, and the control board fits inside it, right behind the
   display. The print texture is produced at 300 px/m so a legend sits directly
   under the part it names. */
export const FASCIA = { w: 4.86, h: 0.30, depth: 0.26 };

const PPM = 300;
const KNOB_X = [1.34, 1.71, 2.08];
const SCREEN = { cx: -0.55, w: 1.46, h: 0.1825 };

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
  g.addColorStop(0, "#262e35");
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

  // display well, 2 mm printed margin around the screen mesh
  const x0 = px(SCREEN.cx - SCREEN.w / 2 - 0.012);
  const x1 = px(SCREEN.cx + SCREEN.w / 2 + 0.012);
  const y0 = py(SCREEN.h / 2 + 0.012);
  const y1 = py(-SCREEN.h / 2 - 0.012);
  ctx.fillStyle = "#05090c";
  ctx.fillRect(x0, y0, x1 - x0, y1 - y0);
  ctx.strokeStyle = "rgba(120, 150, 164, 0.26)";
  ctx.lineWidth = 1;
  ctx.strokeRect(x0 + 0.5, y0 + 0.5, x1 - x0 - 1, y1 - y0 - 1);

  // dial legends above each knob, and their range captions below
  const legend = (x, name, range) => {
    ctx.textAlign = "center";
    ctx.font = "500 15px 'Microsoft YaHei', 'Noto Sans SC', sans-serif";
    ctx.fillStyle = "rgba(214, 228, 236, 0.9)";
    ctx.fillText(name, px(x), py(0.104));
    ctx.font = "500 11px 'Microsoft YaHei', 'Noto Sans SC', sans-serif";
    ctx.fillStyle = "rgba(140, 172, 188, 0.6)";
    ctx.fillText(range, px(x), py(-0.112));
  };
  legend(KNOB_X[0], "加热", "1–3 档");
  legend(KNOB_X[1], "蒸汽", "0–100 %");
  legend(KNOB_X[2], "风机", "0–3 档");

  const lamp = (x, color, label) => {
    ctx.beginPath();
    ctx.arc(px(x), py(-0.075), 4, 0, Math.PI * 2);
    ctx.fillStyle = color;
    ctx.fill();
    ctx.font = "500 10px 'Microsoft YaHei', 'Noto Sans SC', sans-serif";
    ctx.fillStyle = "rgba(180, 200, 212, 0.55)";
    ctx.textAlign = "center";
    ctx.fillText(label, px(x), py(-0.118));
  };
  lamp(2.34, "#5fe0b0", "电源");

  ctx.textAlign = "left";
  ctx.font = "500 11px 'Microsoft YaHei', 'Noto Sans SC', sans-serif";
  ctx.fillStyle = "rgba(122, 150, 164, 0.44)";
  ctx.fillText("ACTS-MCDT", px(-2.30), py(-0.108));

  const tex = new THREE.CanvasTexture(c);
  tex.colorSpace = THREE.SRGBColorSpace;
  tex.anisotropy = 8;
  return tex;
}

/* Live display: 800 x 100 matches a 1.46 m x 0.1825 m panel at ~548 px/m. */
function displaySurface() {
  const canvas = document.createElement("canvas");
  canvas.width = 800;
  canvas.height = 100;
  const tex = new THREE.CanvasTexture(canvas);
  tex.colorSpace = THREE.SRGBColorSpace;
  tex.anisotropy = 8;
  return { canvas, ctx: canvas.getContext("2d"), tex, stamp: null, meta: null };
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

  // progress strip with the design-line tick at alpha = 0.85
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

  // Chassis: an open box bolted to the cabinet front, deep enough to hold the
  // control board. The fascia is a separate front plate, so a section view can
  // take the plate off and look straight at the board.
  const chassis = new THREE.Group();
  panel.add(chassis);
  add(chassis, box(w, h, 0.014, 0.004), materials.panel, V(0, 0, -depth / 2), null, "console.chassis");
  add(chassis, box(w, 0.014, depth, 0.004), materials.panel, V(0, h / 2, 0), null, "console.chassis");
  add(chassis, box(w, 0.014, depth, 0.004), materials.panel, V(0, -h / 2, 0), null, "console.chassis");
  add(chassis, box(0.014, h, depth, 0.004), materials.panel, V(-w / 2, 0, 0), null, "console.chassis");
  add(chassis, box(0.014, h, depth, 0.004), materials.panel, V(w / 2, 0, 0), null, "console.chassis");

  const front = new THREE.Group();
  panel.add(front);

  // fascia plate with silk-screen on its front face
  add(front, box(w - 0.02, h - 0.012, 0.020, 0.010), materials.panel, V(0, 0, depth / 2 - 0.011), null, "console.panel");
  const face = new THREE.Mesh(
    new THREE.PlaneGeometry(w - 0.04, h - 0.026),
    new THREE.MeshStandardMaterial({ map: printTexture(), roughness: 0.56, metalness: 0.24 }),
  );
  face.position.set(0, 0, depth / 2 - 0.0005);
  face.userData.part = "console.panel";
  front.add(face);

  // display well, live panel and cover glass. The well is a shallow recess and
  // its front face stays behind the screen, or it would hide the readout.
  add(front, box(SCREEN.w + 0.05, SCREEN.h + 0.05, 0.026, 0.008),
    new THREE.MeshStandardMaterial({ color: "#04080b", roughness: 0.34, metalness: 0.44 }),
    V(SCREEN.cx, 0, depth / 2 - 0.024), null, "console.bezel");
  const display = displaySurface();
  const screen = new THREE.Mesh(
    new THREE.PlaneGeometry(SCREEN.w, SCREEN.h),
    new THREE.MeshBasicMaterial({ map: display.tex, toneMapped: false }),
  );
  screen.position.set(SCREEN.cx, 0, depth / 2 + 0.003);
  screen.userData.part = "console.screen";
  front.add(screen);
  const cover = new THREE.Mesh(
    new THREE.PlaneGeometry(SCREEN.w, SCREEN.h),
    new THREE.MeshPhysicalMaterial({
      color: "#dcecf2", roughness: 0.05, metalness: 0.0, transparent: true,
      opacity: 0.07, envMapIntensity: 1.8, side: THREE.DoubleSide,
    }),
  );
  cover.position.set(SCREEN.cx, 0, depth / 2 + 0.0045);
  cover.userData.part = "console.screen";
  front.add(cover);

  // three dials: brass skirt, chrome cap, index mark, steel shaft back
  const knobs = KNOB_X.map((x) => {
    const k = new THREE.Group();
    k.position.set(x, -0.015, depth / 2 + 0.016);
    add(k, new THREE.CylinderGeometry(0.056, 0.062, 0.048, 32), brass(),
      V(0, 0, 0), { x: Math.PI / 2, y: 0, z: 0 }, "console.knob");
    add(k, new THREE.CylinderGeometry(0.036, 0.036, 0.032, 24), chrome(),
      V(0, 0, 0.036), { x: Math.PI / 2, y: 0, z: 0 }, "console.knob");
    const mark = add(k, box(0.007, 0.028, 0.008, 0.002), materials.led,
      V(0, 0.026, 0.050), null, "console.knob");
    mark.castShadow = false;
    add(k, new THREE.CylinderGeometry(0.013, 0.013, 0.19, 14), chrome(),
      V(0, 0, -0.105), { x: Math.PI / 2, y: 0, z: 0 }, "console.knob");
    front.add(k);
    return k;
  });

  const powerLed = add(front, new THREE.CylinderGeometry(0.014, 0.014, 0.015, 16), materials.led,
    V(2.34, -0.055, depth / 2 + 0.008), { x: Math.PI / 2, y: 0, z: 0 }, "console.led");
  powerLed.castShadow = false;

  const anchor = new THREE.Object3D();
  anchor.name = "anchor:console";
  anchor.position.set(KNOB_X[1], 0.02, depth / 2 + 0.05);
  panel.add(anchor);
  // A centre anchor for QA/capture framing: the group bbox also contains the
  // control board, which moves separately in the exploded view.
  const centre = new THREE.Object3D();
  centre.name = "anchor:panel";
  centre.position.set(0, 0.0, depth / 2);
  panel.add(centre);

  return {
    group: panel,
    display,
    parts: { knobs, powerLed, face, screen, front, chassis },
    anchor,
  };
}

/* ------------------------------------------------------------------ board */

export function buildConsoleBoard() {
  const m = electronics();
  const board = new THREE.Group();
  board.name = "consoleBoard";

  // open chassis that mounts inside the fascia shell, open toward the front
  add(board, box(1.70, 0.012, 0.20, 0.003), m.tray, V(0, -0.100, 0.01), null, "ctrl.tray");
  add(board, box(1.70, 0.20, 0.012, 0.003), m.tray, V(0, 0.0, -0.100), null, "ctrl.tray");
  add(board, box(0.012, 0.20, 0.20, 0.003), m.tray, V(-0.85, 0.0, 0.01), null, "ctrl.tray");
  add(board, box(0.012, 0.20, 0.20, 0.003), m.tray, V(0.85, 0.0, 0.01), null, "ctrl.tray");

  const pcb = new THREE.Group();
  board.add(pcb);
  add(pcb, box(1.52, 0.22, 0.012, 0.003), m.pcb, V(0, 0.005, -0.01), null, "ctrl.board");

  // power relays with their driver pads
  [-0.56, -0.40].forEach((x) => {
    add(pcb, box(0.115, 0.085, 0.085, 0.008), m.relay, V(x, 0.022, 0.052), null, "ctrl.relay");
    add(pcb, box(0.024, 0.013, 0.024, 0.003), m.ceramic, V(x, -0.055, 0.038), null, "ctrl.relay");
  });
  // mains transformer
  add(pcb, box(0.165, 0.145, 0.095, 0.008), steel("#3a434a", { metalness: 0.5, roughness: 0.55 }),
    V(-0.14, 0.0, 0.058), null, "ctrl.transformer");
  add(pcb, box(0.125, 0.028, 0.075, 0.004), brass(), V(-0.14, 0.086, 0.058), null, "ctrl.transformer");
  // terminal strip
  add(pcb, box(0.60, 0.05, 0.058, 0.005), m.plastic, V(0.02, -0.100, 0.036), null, "ctrl.terminal");
  for (let i = 0; i < 8; i += 1) {
    add(pcb, new THREE.CylinderGeometry(0.0085, 0.0085, 0.015, 10), brass(),
      V(-0.23 + i * 0.072, -0.100, 0.068), { x: Math.PI / 2, y: 0, z: 0 }, "ctrl.terminal");
  }
  // capacitors, microcontroller, heat sink, fuse holder
  [-0.35, -0.31].forEach((x) => {
    add(pcb, new THREE.CylinderGeometry(0.021, 0.021, 0.075, 16), m.plastic,
      V(x, 0.032, 0.046), { x: Math.PI / 2, y: 0, z: 0 }, "ctrl.capacitor");
  });
  add(pcb, box(0.105, 0.026, 0.072, 0.003), m.plastic, V(0.06, 0.062, 0.044), null, "ctrl.mcu");
  add(pcb, box(0.058, 0.010, 0.044, 0.002), m.ceramic, V(0.06, 0.080, 0.044), null, "ctrl.mcu");
  add(pcb, box(0.07, 0.135, 0.048, 0.004), m.sink, V(0.245, 0.0, 0.048), null, "ctrl.heatsink");
  add(pcb, box(0.075, 0.048, 0.038, 0.005), m.plastic, V(0.63, 0.0, 0.046), null, "ctrl.fuse");

  // thermostat: body on the board, spindle forward, bulb on a pigtail below
  const stat = new THREE.Group();
  stat.position.set(0.47, 0.028, -0.050);
  pcb.add(stat);
  add(stat, box(0.125, 0.125, 0.095, 0.012), steel("#c9d2d7", { metalness: 0.7, roughness: 0.34 }),
    V(0, 0, 0), null, "ctrl.thermostat");
  add(stat, box(0.082, 0.082, 0.028, 0.006), brass(), V(0, 0, 0.062), null, "ctrl.thermostat");
  add(stat, new THREE.CylinderGeometry(0.015, 0.015, 0.07, 16), chrome(),
    V(0, 0, 0.108), { x: Math.PI / 2, y: 0, z: 0 }, "ctrl.thermostat");

  const pigtail = [];
  for (let i = 0; i <= 74; i += 1) {
    const k = i / 74;
    const a = k * Math.PI * 5.0;
    pigtail.push(new THREE.Vector3(
      0.30 + Math.cos(a) * 0.048,
      -0.055 - k * 0.012,
      0.035 + Math.sin(a) * 0.048,
    ));
  }
  const coil = new THREE.Mesh(
    new THREE.TubeGeometry(new THREE.CatmullRomCurve3(pigtail), 160, 0.0055, 7, false),
    m.copper,
  );
  coil.userData.part = "ctrl.capillary";
  coil.castShadow = true;
  pcb.add(coil);

  const anchor = new THREE.Object3D();
  anchor.name = "anchor:controller";
  anchor.position.set(0.10, 0.08, 0.02);
  board.add(anchor);

  return { group: board, anchor, parts: { pcb, stat, coil } };
}

/* The capillary bulb clamped to the heater support. Built as its own group so
   it can ride with the heating assembly in the exploded view, with the copper
   run climbing from the heater up behind the fascia where the thermostat is. */
export function buildThermostatBulb() {
  const m = electronics();
  const g = new THREE.Group();
  g.name = "thermostatBulb";
  add(g, new THREE.CylinderGeometry(0.014, 0.014, 0.17, 12), m.copper,
    V(0, 0, 0), { x: 0, y: 0, z: Math.PI / 2 }, "ctrl.bulb");
  add(g, box(0.048, 0.085, 0.048, 0.008), steel("#9aa6ad", { metalness: 0.8, roughness: 0.3 }),
    V(0, 0, 0), null, "ctrl.bulb");
  add(g, box(0.036, 0.026, 0.036, 0.004), m.ceramic, V(-0.098, 0.0, 0.0), null, "ctrl.bulb");
  // run from the bulb back over the ceiling to the control fascia
  const run = [
    V(-0.14, 0.0, 0.0),
    V(-0.30, 0.06, 0.10),
    V(-0.58, 0.16, 0.30),
    V(-0.84, 0.26, 0.56),
    V(-0.98, 0.33, 0.86),
  ];
  const tube = new THREE.Mesh(
    new THREE.TubeGeometry(new THREE.CatmullRomCurve3(run), 80, 0.0048, 6, false),
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
