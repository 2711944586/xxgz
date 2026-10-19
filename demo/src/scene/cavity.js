import * as THREE from "three";
import { RoundedBoxGeometry } from "three/examples/jsm/geometries/RoundedBoxGeometry.js";
import {
  brass, brushedMaps, chrome, dimpleMaps, enamel, glass, rubber, steel,
} from "./palette.js";

const V = (x, y, z) => new THREE.Vector3(x, y, z);

const CAVITY = { halfX: 2.2, floor: 0.1, ceil: 2.5, back: -1.3, mouth: 1.44 };

function box(w, h, d, r = 0.02) {
  return new RoundedBoxGeometry(w, h, d, 2, r);
}

function add(parent, geo, mat, pos, rot, part, explode) {
  const m = new THREE.Mesh(geo, mat);
  m.position.copy(pos);
  if (rot) m.rotation.set(rot.x, rot.y, rot.z);
  m.castShadow = true;
  m.receiveShadow = true;
  m.userData.part = part;
  if (explode) {
    m.userData.basePos = pos.clone();
    m.userData.explode = explode;
  }
  parent.add(m);
  return m;
}

function buildMaterials() {
  const brushed = brushedMaps({ streak: 0.22, repeat: 5 });
  const fine = brushedMaps({ streak: 0.12, grain: 0.03, repeat: 9 });
  const dimpled = dimpleMaps({ repeat: 18 });
  const shellGrain = brushedMaps({ streak: 0.05, grain: 0.13, repeat: 3 });

  const outer = enamel("#1d2429");
  outer.roughnessMap = shellGrain.roughnessMap;
  outer.normalMap = shellGrain.normalMap;
  outer.normalScale.set(0.02, 0.02);
  outer.envMapIntensity = 0.8;

  const liner = steel("#8c979e", { metalness: 0.72, roughness: 0.44, maps: dimpled });
  liner.envMapIntensity = 0.55;
  liner.normalScale.set(0.02, 0.02);

  const blade = new THREE.MeshPhysicalMaterial({
    color: "#242c32", metalness: 0.74, roughness: 0.3,
    clearcoat: 0.28, clearcoatRoughness: 0.38, envMapIntensity: 0.85,
  });
  blade.normalMap = fine.normalMap;
  blade.normalScale.set(0.05, 0.05);

  return {
    outer,
    insulation: new THREE.MeshStandardMaterial({ color: "#b7a487", roughness: 0.97, metalness: 0.02 }),
    liner,
    brass: brass(),
    chrome: chrome(),
    dark: steel("#1f2529", { metalness: 0.6, roughness: 0.42 }),
    motor: steel("#14181b", { metalness: 0.5, roughness: 0.5 }),
    fanPlate: steel("#242c32", { metalness: 0.55, roughness: 0.38, maps: brushed }),
    blade,
    coil: new THREE.MeshStandardMaterial({
      color: "#9d5b3b", emissive: "#bf4a1e", emissiveIntensity: 0.2,
      metalness: 0.66, roughness: 0.34,
    }),
    ceramic: new THREE.MeshStandardMaterial({ color: "#d9d0c3", roughness: 0.68, metalness: 0.05 }),
    reflector: new THREE.MeshStandardMaterial({ color: "#c7d0d6", metalness: 0.9, roughness: 0.22 }),
    rubber: rubber(),
    panel: enamel("#191f24"),
    doorFace: steel("#48535b", { metalness: 0.72, roughness: 0.3, maps: brushed }),
    display: new THREE.MeshStandardMaterial({
      color: "#081014", emissive: "#5fd0e0", emissiveIntensity: 0.45,
      metalness: 0.2, roughness: 0.22,
    }),
    led: new THREE.MeshStandardMaterial({ color: "#8fe0c8", emissive: "#5fe0b0", emissiveIntensity: 1.2 }),
    glass: glass(),
    water: new THREE.MeshPhysicalMaterial({
      color: "#2f7f92", emissive: "#1d5a68", emissiveIntensity: 0.3,
      transmission: 0.45, roughness: 0.2, metalness: 0.05, transparent: true, opacity: 0.85,
    }),
    tank: steel("#39434a", { metalness: 0.4, roughness: 0.5 }),
    nozzle: steel("#b9c4cb", { metalness: 0.9, roughness: 0.24 }),
    grille: steel("#2b333a", { metalness: 0.35, roughness: 0.62 }),
    louvre: steel("#aeb8bf", { metalness: 0.78, roughness: 0.28 }),
    rail: steel("#c3ccd2", { metalness: 0.9, roughness: 0.2 }),
    tray: new THREE.MeshPhysicalMaterial({ color: "#2b3238", metalness: 0.45, roughness: 0.34, clearcoat: 0.5 }),
    trayRim: steel("#aab4bb", { metalness: 0.85, roughness: 0.24 }),
    marker: new THREE.MeshBasicMaterial({ color: "#7eb8c9" }),
  };
}

function buildShell(materials, explodeTargets) {
  const g = new THREE.Group();
  const { outer, insulation, liner } = materials;
  const push = (m) => { explodeTargets.push(m); return m; };

  const panels = [
    [box(5.18, 0.2, 3.26, 0.05), outer, V(0, -0.09, 0), "shell.bottom", V(0, -0.92, 0)],
    [box(5.18, 0.2, 3.26, 0.05), outer, V(0, 2.8, 0), "shell.top", V(0, 0.95, 0)],
    [box(5.18, 3.08, 0.2, 0.05), outer, V(0, 1.36, -1.6), "shell.back", V(0, 0, -1.18)],
    [box(0.2, 3.08, 3.26, 0.05), outer, V(-2.52, 1.36, 0), "shell.left", V(-1.18, 0, 0)],
    [box(0.2, 3.08, 3.26, 0.05), outer, V(2.52, 1.36, 0), "shell.right", V(1.18, 0, 0)],
  ];
  panels.forEach(([geo, mat, pos, part, exp]) => push(add(g, geo, mat, pos, null, part, exp)));

  // Front chassis ring.
  [
    [box(5.18, 0.34, 0.14, 0.03), V(0, 2.72, 1.44), "shell.top", V(0, 0.95, 0)],
    [box(5.18, 0.32, 0.14, 0.03), V(0, 0.0, 1.44), "shell.bottom", V(0, -0.92, 0)],
    [box(0.3, 2.98, 0.14, 0.03), V(-2.44, 1.36, 1.44), "shell.left", V(-1.18, 0, 0)],
    [box(0.3, 2.98, 0.14, 0.03), V(2.44, 1.36, 1.44), "shell.right", V(1.18, 0, 0)],
  ].forEach(([geo, pos, part, exp]) => push(add(g, geo, outer, pos, null, part, exp)));

  [
    [box(0.1, 2.55, 2.7, 0.02), V(-2.33, 1.3, 0.02), "insulation.left", V(-0.52, 0, 0)],
    [box(0.1, 2.55, 2.7, 0.02), V(2.33, 1.3, 0.02), "insulation.right", V(0.52, 0, 0)],
    [box(4.7, 0.1, 2.7, 0.02), V(0, 2.62, 0.02), "insulation.top", V(0, 0.46, 0)],
    [box(4.7, 2.55, 0.1, 0.02), V(0, 1.3, -1.42), "insulation.back", V(0, 0, -0.52)],
  ].forEach(([geo, pos, part, exp]) => {
    const m = add(g, geo, insulation, pos, null, part, exp);
    m.castShadow = false;
    push(m);
  });

  [
    [box(4.5, 0.055, 2.7, 0.02), V(0, CAVITY.floor, 0.06), "liner.floor", V(0, -0.44, 0)],
    [box(4.5, 0.055, 2.7, 0.02), V(0, CAVITY.ceil, 0.06), "liner.ceiling", V(0, 0.44, 0)],
    [box(4.5, 2.48, 0.055, 0.02), V(0, 1.3, CAVITY.back), "liner.back", V(0, 0, -0.38)],
    [box(0.055, 2.48, 2.7, 0.02), V(-CAVITY.halfX, 1.3, 0.06), "liner.left", V(-0.38, 0, 0)],
    [box(0.055, 2.48, 2.7, 0.02), V(CAVITY.halfX, 1.3, 0.06), "liner.right", V(0.38, 0, 0)],
  ].forEach(([geo, pos, part, exp]) => {
    const m = add(g, geo, liner, pos, null, part, exp);
    m.castShadow = false;
    push(m);
  });

  [
    [box(4.72, 0.075, 0.075), V(0, 2.56, 1.4)],
    [box(4.72, 0.075, 0.075), V(0, 0.08, 1.4)],
    [box(0.075, 2.56, 0.075), V(-2.32, 1.32, 1.4)],
    [box(0.075, 2.56, 0.075), V(2.32, 1.32, 1.4)],
  ].forEach(([geo, pos]) => add(g, geo, materials.brass, pos, null, "frame"));

  [
    [box(4.55, 0.045, 0.06), V(0, 2.5, 1.36), "seal"],
    [box(4.55, 0.045, 0.06), V(0, 0.12, 1.36), "seal"],
    [box(0.045, 2.4, 0.06), V(-2.24, 1.31, 1.36), "seal"],
    [box(0.045, 2.4, 0.06), V(2.24, 1.31, 1.36), "seal"],
  ].forEach(([geo, pos, part]) => add(g, geo, materials.rubber, pos, null, part));

  [[-2.15, -1.2], [2.15, -1.2], [-2.15, 1.15], [2.15, 1.15]].forEach(([x, z]) => {
    add(g, new THREE.CylinderGeometry(0.075, 0.095, 0.13, 16),
      materials.dark, V(x, -0.22, z), null, "shell.bottom");
  });

  return g;
}

function buildDoor(materials, explodeTargets) {
  const door = new THREE.Group();
  door.position.set(-2.66, 1.32, 1.62);
  door.userData.basePos = door.position.clone();
  door.userData.explode = V(0, 0, 1.7);
  explodeTargets.push(door);

  const W = 5.06;
  const H = 2.56;
  const cx = W / 2;

  add(door, box(W, 0.13, 0.11, 0.016), materials.outer, V(cx, H / 2 - 0.065, 0), null, "door.frame");
  add(door, box(W, 0.13, 0.11, 0.016), materials.outer, V(cx, -H / 2 + 0.065, 0), null, "door.frame");
  add(door, box(0.13, H, 0.11, 0.016), materials.outer, V(0.065, 0, 0), null, "door.frame");
  add(door, box(0.13, H, 0.11, 0.016), materials.outer, V(W - 0.065, 0, 0), null, "door.frame");
  add(door, box(W - 0.3, H - 0.34, 0.05, 0.01), materials.doorFace, V(cx, 0, 0.045), null, "door.panel");

  add(door, box(W - 0.42, H - 0.46, 0.016, 0.006), materials.glass, V(cx, 0, 0.08), null, "door.glass");
  add(door, box(W - 0.5, H - 0.54, 0.012, 0.005), materials.glass, V(cx, 0, 0.02), null, "door.glass");
  add(door, box(W - 0.28, H - 0.28, 0.01, 0.006), materials.glass, V(cx, 0, -0.04), null, "door.glass");

  const gasket = (w, h, x, y) =>
    add(door, box(w, h, 0.05, 0.012), materials.rubber, V(x, y, -0.078), null, "door.seal");
  gasket(W - 0.2, 0.06, cx, H / 2 - 0.14);
  gasket(W - 0.2, 0.06, cx, -H / 2 + 0.14);
  gasket(0.06, H - 0.32, 0.14, 0);
  gasket(0.06, H - 0.32, W - 0.14, 0);

  const handle = new THREE.Group();
  handle.position.set(W - 0.34, 0.04, 0.17);
  add(handle, new THREE.CylinderGeometry(0.036, 0.036, 0.82, 24), materials.chrome, V(0, 0, 0), null, "door.handle");
  add(handle, new THREE.CylinderGeometry(0.034, 0.034, 0.15, 18), materials.chrome,
    V(0, 0.34, -0.075), { x: Math.PI / 2, y: 0, z: 0 }, "door.handle");
  add(handle, new THREE.CylinderGeometry(0.034, 0.034, 0.15, 18), materials.chrome,
    V(0, -0.34, -0.075), { x: Math.PI / 2, y: 0, z: 0 }, "door.handle");
  add(handle, new THREE.SphereGeometry(0.05, 20, 16), materials.chrome, V(0, 0.44, 0), null, "door.handle");
  add(handle, new THREE.SphereGeometry(0.05, 20, 16), materials.chrome, V(0, -0.44, 0), null, "door.handle");
  door.add(handle);

  [-0.92, 0, 0.92].forEach((hy) => {
    add(door, new THREE.CylinderGeometry(0.04, 0.04, 0.2, 20), materials.chrome, V(0, hy, 0), null, "door.hinge");
    add(door, box(0.16, 0.16, 0.05, 0.012), materials.chrome, V(0.035, hy, -0.06), null, "door.hinge");
  });
  add(door, box(0.07, 0.13, 0.05, 0.01), materials.chrome, V(W - 0.11, -0.62, -0.05), null, "door.striker");

  const panel = new THREE.Group();
  panel.position.set(cx, H / 2 + 0.02, 0.07);
  add(panel, box(W - 0.2, 0.4, 0.13, 0.02), materials.panel, V(0, 0, 0), null, "fascia");
  const display = add(panel, box(1.46, 0.23, 0.02, 0.008), materials.display,
    V(-0.55, 0, 0.072), null, "fascia.display");
  display.castShadow = false;

  const knobs = [1.34, 1.71, 2.08].map((x) => {
    const k = new THREE.Group();
    k.position.set(x, 0.01, 0.085);
    add(k, new THREE.CylinderGeometry(0.112, 0.118, 0.06, 32), materials.brass,
      V(0, 0, 0), { x: Math.PI / 2, y: 0, z: 0 }, "fascia.knob");
    add(k, new THREE.CylinderGeometry(0.072, 0.072, 0.04, 24), materials.chrome,
      V(0, 0, 0.045), { x: Math.PI / 2, y: 0, z: 0 }, "fascia.knob");
    const mark = add(k, box(0.011, 0.05, 0.012, 0.004), materials.led, V(0, 0.048, 0.062), null, "fascia.knob");
    mark.castShadow = false;
    panel.add(k);
    return k;
  });
  add(panel, new THREE.CylinderGeometry(0.032, 0.032, 0.018, 16), materials.led,
    V(2.32, 0.01, 0.075), { x: Math.PI / 2, y: 0, z: 0 }, "fascia.led");
  door.add(panel);

  door.userData.knobs = knobs;
  door.userData.display = display;
  return door;
}

function buildHeater(materials) {
  const g = new THREE.Group();
  const rods = [];
  for (let i = 0; i < 6; i += 1) {
    const x = -1.75 + i * 0.7;
    const rod = add(g, new THREE.CylinderGeometry(0.03, 0.03, 2.16, 20), materials.coil,
      V(x, 2.28, -0.02), { x: Math.PI / 2, y: 0, z: 0 }, "heater");
    rods.push(rod);
    [1.06, -1.1].forEach((z, k) => {
      add(g, new THREE.TorusGeometry(0.088, 0.03, 12, 22, Math.PI), materials.coil,
        V(x, 2.192, z), { x: 0, y: k === 0 ? Math.PI / 2 : -Math.PI / 2, z: Math.PI / 2 }, "heater");
      add(g, new THREE.CylinderGeometry(0.03, 0.03, 0.09, 14), materials.coil,
        V(x, 2.148, z + (k === 0 ? 0.085 : -0.085)), null, "heater");
      add(g, new THREE.CylinderGeometry(0.054, 0.05, 0.13, 18), materials.ceramic,
        V(x, 2.28, k === 0 ? 1.2 : -1.24), { x: Math.PI / 2, y: 0, z: 0 }, "heater");
      add(g, new THREE.CylinderGeometry(0.016, 0.016, 0.09, 10), materials.chrome,
        V(x, 2.28, k === 0 ? 1.28 : -1.32), { x: Math.PI / 2, y: 0, z: 0 }, "heater");
    });
  }
  add(g, new THREE.BoxGeometry(4.3, 0.02, 0.045), materials.chrome, V(0, 2.28, 1.34), null, "heater");
  add(g, new THREE.BoxGeometry(4.3, 0.02, 0.045), materials.chrome, V(0, 2.28, -1.36), null, "heater");
  const reflector = add(g, box(4.6, 0.03, 2.5, 0.01), materials.reflector, V(0, 2.46, 0.06), null, "heater");
  reflector.castShadow = false;
  for (let i = 0; i < 9; i += 1) {
    add(g, new THREE.CylinderGeometry(0.008, 0.008, 2.5, 8), materials.chrome,
      V(-1.96 + i * 0.49, 2.18, 0.06), { x: Math.PI / 2, y: 0, z: 0 }, "heater");
  }
  g.userData.rods = rods;
  return g;
}

function buildFan(materials) {
  const fan = new THREE.Group();
  fan.position.set(0.02, 1.4, -1.22);
  fan.userData.basePos = fan.position.clone();
  fan.userData.explode = V(0, 0, -0.55);

  const plate = new THREE.Mesh(new THREE.CylinderGeometry(0.95, 0.95, 0.05, 56), materials.fanPlate);
  plate.rotation.x = Math.PI / 2;
  plate.position.z = -0.12;
  plate.castShadow = true;
  fan.add(plate);

  const holes = new THREE.InstancedMesh(
    new THREE.CircleGeometry(0.034, 10),
    new THREE.MeshStandardMaterial({ color: "#080b0d", roughness: 0.92 }),
    140,
  );
  const dummy = new THREE.Object3D();
  let n = 0;
  for (let r = 0.28; r < 0.93 && n < 140; r += 0.108) {
    const count = Math.round((Math.PI * 2 * r) / 0.125);
    for (let k = 0; k < count && n < 140; k += 1) {
      const a = (k / count) * Math.PI * 2 + r * 3;
      dummy.position.set(Math.cos(a) * r, Math.sin(a) * r, -0.088);
      dummy.updateMatrix();
      holes.setMatrixAt(n, dummy.matrix);
      n += 1;
    }
  }
  holes.count = n;
  fan.add(holes);

  const hub = new THREE.Mesh(new THREE.CylinderGeometry(0.3, 0.36, 0.3, 28), materials.dark);
  hub.rotation.x = Math.PI / 2;
  hub.position.z = -0.05;
  fan.add(hub);
  const motor = new THREE.Mesh(new THREE.CylinderGeometry(0.19, 0.22, 0.34, 24), materials.motor);
  motor.rotation.x = Math.PI / 2;
  motor.position.z = -0.32;
  fan.add(motor);
  fan.add(new THREE.Mesh(new THREE.TorusGeometry(0.82, 0.024, 12, 64), materials.chrome));
  const ring = new THREE.Mesh(new THREE.TorusGeometry(0.95, 0.03, 12, 64), materials.chrome);
  ring.position.z = -0.06;
  fan.add(ring);
  for (let i = 0; i < 4; i += 1) {
    const bar = new THREE.Mesh(new THREE.BoxGeometry(0.007, 1.62, 0.005), materials.chrome);
    bar.rotation.z = (i * Math.PI) / 4;
    fan.add(bar);
  }

  const blades = new THREE.Group();
  blades.position.z = 0.11;
  const shape = new THREE.Shape();
  shape.moveTo(0, 0);
  shape.bezierCurveTo(0.14, 0.1, 0.2, 0.46, 0.06, 1.04);
  shape.bezierCurveTo(-0.08, 0.54, -0.086, 0.14, 0, 0);
  const foil = new THREE.ExtrudeGeometry(shape, {
    depth: 0.05, bevelEnabled: true, bevelThickness: 0.008,
    bevelSize: 0.005, bevelSegments: 3, curveSegments: 16,
  });
  for (let i = 0; i < 10; i += 1) {
    const blade = new THREE.Mesh(foil, materials.blade);
    blade.position.set(-0.02, 0.2, 0);
    blade.rotation.set(0.22, 0.66, 0.05);
    blade.castShadow = true;
    const wrap = new THREE.Group();
    wrap.rotation.z = (i * Math.PI * 2) / 10;
    wrap.add(blade);
    blades.add(wrap);
  }
  const spinner = new THREE.Mesh(new THREE.CylinderGeometry(0.12, 0.16, 0.14, 24), materials.chrome);
  spinner.rotation.x = Math.PI / 2;
  spinner.position.z = 0.16;
  blades.add(spinner);
  const nut = new THREE.Mesh(new THREE.CylinderGeometry(0.045, 0.045, 0.06, 12), materials.brass);
  nut.rotation.x = Math.PI / 2;
  nut.position.z = 0.23;
  blades.add(nut);
  fan.add(blades);
  fan.userData.blades = blades;
  return fan;
}

function buildSteam(materials) {
  const g = new THREE.Group();
  add(g, box(0.5, 0.34, 0.72, 0.04), materials.tank, V(-2.02, 0.3, -0.92), null, "steam.tank", V(-0.42, 0, -0.32));
  add(g, box(0.34, 0.2, 0.06, 0.01), materials.glass, V(-2.02, 0.32, -0.53), null, "steam.tank");
  const water = add(g, box(0.3, 0.16, 0.024, 0.004), materials.water, V(-2.02, 0.27, -0.52), null, "steam.tank");
  water.castShadow = false;

  add(g, new THREE.CylinderGeometry(0.046, 0.046, 0.74, 18), materials.liner,
    V(-1.96, 1.66, 0.16), { x: 0, y: 0, z: Math.PI / 2 }, "steam.pipe");
  add(g, new THREE.TorusGeometry(0.08, 0.046, 12, 20, Math.PI / 2), materials.liner,
    V(-2.3, 1.58, 0.16), { x: 0, y: 0, z: Math.PI / 2 }, "steam.pipe");
  add(g, new THREE.CylinderGeometry(0.08, 0.08, 0.15, 20), materials.brass,
    V(-2.29, 1.7, 0.16), { x: 0, y: 0, z: Math.PI / 2 }, "steam.valve");
  add(g, new THREE.CylinderGeometry(0.032, 0.032, 0.16, 12), materials.chrome,
    V(-2.29, 1.82, 0.16), null, "steam.valve");

  const nozzle = new THREE.Group();
  nozzle.position.set(-1.6, 1.62, 0.18);
  const cone = new THREE.Mesh(new THREE.ConeGeometry(0.085, 0.22, 20, 1, true), materials.nozzle);
  cone.rotation.z = -Math.PI / 2;
  cone.position.x = 0.08;
  cone.castShadow = true;
  cone.userData.part = "steam.nozzle";
  nozzle.add(cone);
  const collar = new THREE.Mesh(new THREE.CylinderGeometry(0.07, 0.07, 0.12, 20), materials.brass);
  collar.rotation.z = Math.PI / 2;
  collar.userData.part = "steam.nozzle";
  nozzle.add(collar);
  g.add(nozzle);

  const tip = new THREE.Object3D();
  tip.position.set(-1.47, 1.62, 0.18);
  g.add(tip);
  g.userData.water = water;
  g.userData.nozzle = nozzle;
  g.userData.tip = tip;
  return g;
}

// Exhaust louvres sit high on the back wall beside the fan: a recessed pocket,
// seven slats that pivot with the exhaust command, and a brass surround.
function buildVent(materials) {
  const g = new THREE.Group();
  const Z = -1.245;
  const recess = add(g, box(0.58, 0.56, 0.05, 0.008), materials.grille, V(1.62, 2.16, Z), null, "vent");
  recess.castShadow = false;
  const louvres = [];
  for (let i = 0; i < 7; i += 1) {
    louvres.push(add(g, box(0.52, 0.022, 0.07, 0.005), materials.louvre,
      V(1.62, 2.38 - i * 0.062, Z + 0.04), { x: 0.55, y: 0, z: 0 }, "vent"));
  }
  for (let i = 0; i < 2; i += 1) {
    add(g, box(0.016, 0.6, 0.03, 0.004), materials.brass,
      V(1.62 + (i ? 0.3 : -0.3), 2.16, Z + 0.03), null, "vent");
  }
  g.userData.louvres = louvres;
  return g;
}

function buildRacks(materials) {
  const g = new THREE.Group();
  [0.34, 0.82, 1.3, 1.78, 2.26].forEach((y) => {
    [-1.78, 1.78].forEach((x) => {
      add(g, box(0.026, 0.5, 0.018, 0.004), materials.rail, V(x, y, 0.06), null, "rack");
    });
  });

  const shelf = new THREE.Group();
  shelf.position.set(0, 0.66, 0.08);
  for (let i = 0; i < 9; i += 1) {
    add(shelf, box(2.26, 0.012, 0.012, 0.003), materials.rail, V(0, 0, -0.66 + i * 0.165), null, "rack");
  }
  for (let i = 0; i < 5; i += 1) {
    add(shelf, box(0.012, 0.012, 1.4, 0.003), materials.rail, V(-0.94 + i * 0.47, 0, 0), null, "rack");
  }
  g.add(shelf);

  const tray = new THREE.Group();
  tray.position.set(0, 0.7, 0.06);
  tray.userData.basePos = tray.position.clone();
  tray.userData.explode = V(0, 0.36, 0.12);
  add(tray, box(2.24, 0.036, 1.46, 0.012), materials.tray, V(0, 0, 0), null, "tray");
  add(tray, box(2.3, 0.05, 1.52, 0.02), materials.trayRim, V(0, 0.02, 0), null, "tray");
  g.add(tray);
  g.userData.tray = tray;
  return g;
}

function buildSensors(materials) {
  const g = new THREE.Group();
  const mark = (pos, color, part, size = 0.028) => {
    const mat = new THREE.MeshStandardMaterial({
      color, emissive: color, emissiveIntensity: 1.6, roughness: 0.3,
    });
    const m = new THREE.Mesh(new THREE.SphereGeometry(size, 14, 12), mat);
    m.position.copy(pos);
    m.userData.part = part;
    m.castShadow = false;
    g.add(m);
    return m;
  };
  const marks = {
    cavityTemp: mark(V(1.9, 2.1, -1.18), "#7eb8c9", "sensor.cavityTemp"),
    humidity: mark(V(1.88, 1.62, 1.18), "#9fd0c4", "sensor.humidity"),
    heaterProbe: mark(V(-1.9, 2.34, 0.6), "#ff9a5c", "sensor.heaterProbe"),
    doorSwitch: mark(V(2.4, 0.62, 1.34), "#d8c07a", "sensor.doorSwitch"),
    waterFloat: mark(V(-2.0, 0.36, -0.62), "#6fb3c9", "sensor.waterFloat"),
    coldSpot: mark(V(0, 0.9, -0.4), "#7eb8c9", "sensor.coldSpot", 0.034),
    estimate: mark(V(0, 0.96, -0.4), "#f4bc41", "sensor.estimate", 0.03),
  };
  g.userData.marks = marks;
  return g;
}

export function buildCavity() {
  const materials = buildMaterials();
  const group = new THREE.Group();
  const explodeTargets = [];

  const shell = buildShell(materials, explodeTargets);
  group.add(shell);
  const door = buildDoor(materials, explodeTargets);
  group.add(door);
  const heater = buildHeater(materials);
  group.add(heater);
  const fan = buildFan(materials);
  group.add(fan);
  const steamLine = buildSteam(materials);
  group.add(steamLine);
  const vent = buildVent(materials);
  group.add(vent);
  const racks = buildRacks(materials);
  group.add(racks);
  const sensors = buildSensors(materials);
  group.add(sensors);
  explodeTargets.push(fan, racks.userData.tray);

  const bay = new THREE.Group();
  add(bay, box(0.8, 0.42, 0.9, 0.03), materials.dark, V(-1.96, 0.4, -1.05), null, "bay", V(-0.48, 0, -0.6));
  add(bay, box(0.72, 0.06, 0.8, 0.01), materials.chrome, V(-1.96, 0.62, -1.05), null, "bay");
  group.add(bay);
  explodeTargets.push(bay);

  // Panels hidden in section view: the near wall and its liner/insulation.
  const sectionPanels = [];
  const topPanels = [];
  shell.traverse((m) => {
    if (!m.isMesh) return;
    const part = m.userData.part || "";
    if (part.endsWith(".right") || part === "shell.right" || part === "liner.right"
      || part === "insulation.right" || part === "frame.right") {
      sectionPanels.push(m);
    }
    if (part === "shell.top" || part === "liner.ceiling" || part === "insulation.top") {
      topPanels.push(m);
    }
  });

  return {
    group, materials,
    parts: { shell, door, heater, fan, steamLine, vent, racks, sensors, bay },
    explodeTargets, sectionPanels, topPanels,
  };
}
