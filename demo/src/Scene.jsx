import { useEffect, useRef } from "react";
import * as THREE from "three";
import { EffectComposer } from "three/examples/jsm/postprocessing/EffectComposer.js";
import { RenderPass } from "three/examples/jsm/postprocessing/RenderPass.js";
import { GTAOPass } from "three/examples/jsm/postprocessing/GTAOPass.js";
import { OutputPass } from "three/examples/jsm/postprocessing/OutputPass.js";
import { RoomEnvironment } from "three/examples/jsm/environments/RoomEnvironment.js";
import { RoundedBoxGeometry } from "three/examples/jsm/geometries/RoundedBoxGeometry.js";

const T_MIN = 8;
const T_MAX = 170;
const N_CELL = 16;
// The door hinges on the left, so the default viewpoint sits front-left:
// an open door then frames the cavity instead of crossing the sight line.
const CAM = { yaw: 0.46, pitch: 0.26, dist: 8.05, min: 3.8, max: 9.2 };

function heatColor(value) {
  const x = Math.min(1, Math.max(0, (value - T_MIN) / (T_MAX - T_MIN)));
  const color = new THREE.Color();
  if (x < 0.35) color.setHSL(0.52 - 0.18 * (x / 0.35), 0.38, 0.62);
  else if (x < 0.7) color.setHSL(0.11, 0.58, 0.58 - 0.1 * ((x - 0.35) / 0.35));
  else color.setHSL(0.045, 0.7, 0.36);
  return color;
}

function addMesh(group, geo, mat, x, y, z, rx = 0, ry = 0, rz = 0) {
  const mesh = new THREE.Mesh(geo, mat);
  mesh.position.set(x, y, z);
  mesh.rotation.set(rx, ry, rz);
  mesh.castShadow = true;
  mesh.receiveShadow = true;
  group.add(mesh);
  return mesh;
}

function steamTexture() {
  const canvas = document.createElement("canvas");
  canvas.width = 64;
  canvas.height = 64;
  const ctx = canvas.getContext("2d");
  const g = ctx.createRadialGradient(32, 32, 2, 32, 32, 30);
  g.addColorStop(0, "rgba(255,255,255,0.78)");
  g.addColorStop(0.32, "rgba(214,232,240,0.32)");
  g.addColorStop(1, "rgba(214,232,240,0)");
  ctx.fillStyle = g;
  ctx.fillRect(0, 0, 64, 64);
  const tex = new THREE.CanvasTexture(canvas);
  tex.needsUpdate = true;
  return tex;
}

function metal(color, metalness, roughness, env = 1.05) {
  // The env map is a PMREM; anisotropic sampling keeps the highlight stretched
  // along brushed grooves instead of round.
  return new THREE.MeshPhysicalMaterial({
    color,
    metalness,
    roughness,
    envMapIntensity: env,
  });
}

function fasciaMap() {
  const canvas = document.createElement("canvas");
  canvas.width = 1024;
  canvas.height = 128;
  const ctx = canvas.getContext("2d");
  const paint = (frame) => {
    const g = ctx.createLinearGradient(0, 0, 0, 128);
    g.addColorStop(0, "#2a3238");
    g.addColorStop(1, "#161b20");
    ctx.fillStyle = g;
    ctx.fillRect(0, 0, 1024, 128);
    ctx.fillStyle = "rgba(196, 165, 116, 0.18)";
    ctx.fillRect(0, 0, 1024, 1);
    ctx.fillStyle = "#c4a574";
    ctx.font = "600 22px 'IBM Plex Sans', 'Microsoft YaHei', sans-serif";
    ctx.textAlign = "center";
    ["加热", "蒸汽", "风机", "模式"].forEach((lab, i) => {
      ctx.fillText(lab, 168 + i * 148, 108);
    });
    ctx.fillStyle = "#7eb8c9";
    ctx.font = "600 26px 'IBM Plex Sans', sans-serif";
    ctx.fillText("ACTS", 860, 38);
    ctx.fillStyle = "#8d938b";
    ctx.font = "15px 'IBM Plex Mono', monospace";
    ctx.fillText("MCDT  2402", 860, 62);
    if (frame) {
      ctx.fillStyle = frame.alpha >= 0.85 ? "#7a9e7e" : "#c4a574";
      ctx.font = "600 18px 'IBM Plex Mono', monospace";
      ctx.fillText(`${Math.round(frame.time)} s  α ${frame.alpha.toFixed(3)}`, 860, 86);
      ctx.fillStyle = frame.varR < 0.3 ? "#7a9e7e" : "#c45c4a";
      ctx.font = "500 13px 'IBM Plex Mono', monospace";
      ctx.fillText(`var ${frame.varR.toFixed(3)}`, 860, 108);
      ctx.beginPath();
      ctx.fillStyle = frame.varR < 0.3 ? "#7a9e7e" : "#c45c4a";
      ctx.arc(792, 86, 6, 0, Math.PI * 2);
      ctx.fill();
      ctx.beginPath();
      ctx.fillStyle = frame.alpha >= 0.85 ? "#7a9e7e" : "#c45c4a";
      ctx.arc(792, 106, 6, 0, Math.PI * 2);
      ctx.fill();
      ctx.fillStyle = "#8d938b";
      ctx.font = "500 11px 'IBM Plex Mono', monospace";
      ctx.textAlign = "left";
      ctx.fillText("R", 804, 90);
      ctx.fillText("α", 804, 110);
      ctx.textAlign = "center";
    } else {
      ctx.fillStyle = "#8d938b";
      ctx.font = "16px 'IBM Plex Mono', monospace";
      ctx.fillText("待机", 860, 92);
    }
  };
  paint(null);
  const tex = new THREE.CanvasTexture(canvas);
  tex.colorSpace = THREE.SRGBColorSpace;
  tex.anisotropy = 8;
  tex.userData = { paint, canvas };
  return tex;
}

function airfoilGeometry() {
  const shape = new THREE.Shape();
  shape.moveTo(0, 0);
  shape.bezierCurveTo(0.12, 0.10, 0.17, 0.42, 0.058, 1.08);
  shape.bezierCurveTo(-0.07, 0.58, -0.075, 0.16, 0, 0);
  return new THREE.ExtrudeGeometry(shape, {
    depth: 0.058,
    bevelEnabled: true,
    bevelThickness: 0.009,
    bevelSize: 0.006,
    bevelSegments: 4,
    curveSegments: 18,
  });
}

function makeCavity() {
  const group = new THREE.Group();

  // Two procedural fills: a fine anisotropic streak for the brushed shell, and
  // a finer grain for the bright liner. Generated at load time so the repo
  // carries no binary texture assets.
  const shellMaps = proceduralSurfaceMaps({ streak: 0.26, grain: 0.05 });
  const linerMaps = proceduralSurfaceMaps({ streak: 0.14, grain: 0.04 });

  const outer = metal("#2a3136", 0.58, 0.46);
  outer.normalMap = shellMaps.normalMap;
  outer.normalScale = new THREE.Vector2(0.06, 0.06);
  outer.roughnessMap = shellMaps.roughnessMap;

  const liner = metal("#d8e0e6", 0.92, 0.16, 1.25);
  liner.normalMap = linerMaps.normalMap;
  liner.normalScale = new THREE.Vector2(0.025, 0.025);
  liner.roughnessMap = linerMaps.roughnessMap;

  const floor = metal("#8f989f", 0.72, 0.34);
  const dark = metal("#3a434a", 0.62, 0.4);
  const brass = metal("#c4a574", 0.84, 0.26, 1.2);
  const ceramic = new THREE.MeshStandardMaterial({
    color: "#d8d0c4",
    metalness: 0.08,
    roughness: 0.72,
  });
  const rubber = new THREE.MeshStandardMaterial({
    color: "#1b1e21",
    metalness: 0.12,
    roughness: 0.8,
  });
  const foam = new THREE.MeshStandardMaterial({
    color: "#c9b89a",
    roughness: 0.92,
    metalness: 0.02,
  });
  // Oven glass: a dark, strongly reflective pane. Transmission stays high
  // enough to see the cavity, opacity and tint give the sheet a visible
  // presence so the door does not vanish against the lit interior.
  const glass = new THREE.MeshPhysicalMaterial({
    color: "#5d7078",
    metalness: 0.12,
    roughness: 0.045,
    transmission: 0.45,
    thickness: 0.03,
    ior: 1.52,
    transparent: true,
    opacity: 0.78,
    envMapIntensity: 2.4,
    clearcoat: 1.0,
    clearcoatRoughness: 0.03,
    reflectivity: 0.9,
  });
  const chrome = metal("#cfd8de", 0.95, 0.12, 1.3);
  const enamel = new THREE.MeshStandardMaterial({
    color: "#1e2428",
    metalness: 0.35,
    roughness: 0.55,
  });

  addMesh(group, new RoundedBoxGeometry(5.18, 0.2, 3.26, 3, 0.04), outer, 0, -0.09, 0);
  addMesh(group, new RoundedBoxGeometry(5.18, 0.2, 3.26, 3, 0.04), outer, 0, 2.8, 0);
  addMesh(group, new RoundedBoxGeometry(5.18, 3.08, 0.2, 3, 0.04), outer, 0, 1.36, -1.6);
  addMesh(group, new RoundedBoxGeometry(0.2, 3.08, 3.26, 3, 0.04), outer, -2.52, 1.36, 0);
  addMesh(group, new RoundedBoxGeometry(0.2, 3.08, 3.26, 3, 0.04), outer, 2.52, 1.36, 0);

  addMesh(group, new THREE.BoxGeometry(0.1, 2.55, 2.7), foam, -2.33, 1.3, 0.02);
  addMesh(group, new THREE.BoxGeometry(0.1, 2.55, 2.7), foam, 2.33, 1.3, 0.02);
  addMesh(group, new THREE.BoxGeometry(4.7, 0.1, 2.7), foam, 0, 2.62, 0.02);
  addMesh(group, new THREE.BoxGeometry(4.7, 2.55, 0.1), foam, 0, 1.3, -1.42);

  addMesh(group, new RoundedBoxGeometry(4.5, 0.055, 2.7, 2, 0.018), floor, 0, 0.1, 0.06);
  addMesh(group, new RoundedBoxGeometry(4.5, 0.055, 2.7, 2, 0.018), liner, 0, 2.5, 0.06);
  addMesh(group, new RoundedBoxGeometry(4.5, 2.48, 0.055, 2, 0.018), liner, 0, 1.3, -1.3);
  addMesh(group, new RoundedBoxGeometry(0.055, 2.48, 2.7, 2, 0.018), liner, -2.2, 1.3, 0.06);
  addMesh(group, new RoundedBoxGeometry(0.055, 2.48, 2.7, 2, 0.018), liner, 2.2, 1.3, 0.06);

  [
    [new THREE.BoxGeometry(4.72, 0.075, 0.075), [0, 2.56, 1.4]],
    [new THREE.BoxGeometry(4.72, 0.075, 0.075), [0, 0.08, 1.4]],
    [new THREE.BoxGeometry(0.075, 2.56, 0.075), [-2.32, 1.32, 1.4]],
    [new THREE.BoxGeometry(0.075, 2.56, 0.075), [2.32, 1.32, 1.4]],
  ].forEach(([geo, pos]) => addMesh(group, geo, brass, ...pos));
  addMesh(group, new THREE.BoxGeometry(4.55, 0.04, 0.05), rubber, 0, 2.5, 1.36);
  addMesh(group, new THREE.BoxGeometry(4.55, 0.04, 0.05), rubber, 0, 0.12, 1.36);
  addMesh(group, new THREE.BoxGeometry(0.04, 2.4, 0.05), rubber, -2.24, 1.31, 1.36);
  addMesh(group, new THREE.BoxGeometry(0.04, 2.4, 0.05), rubber, 2.24, 1.31, 1.36);

  // ------------------------------------------------------------------
  // Front door. The opening spans x in [-2.62, 2.62] at z = 1.44, and the
  // body front face is z = 1.52. The hinge is a vertical axis at the LEFT
  // edge of the opening, so the panel must be built with its own origin at
  // that axis and extend to +x.
  // ------------------------------------------------------------------
  const door = new THREE.Group();
  // Hinge sits just OUTSIDE the front face so the panel clears the brass frame
  // as it swings. z = 1.62 is in front of both the frame (1.40) and the body
  // face (1.52), which removes the interpenetration on opening.
  door.position.set(-2.66, 1.32, 1.62);
  const DOOR_W = 5.06;
  const DOOR_H = 2.56;
  const doorCenterX = DOOR_W / 2;

  // Outer enamel frame (four rails), thin in z so the face points at +z.
  addMesh(door, new RoundedBoxGeometry(DOOR_W, 0.10, 0.10, 2, 0.012), enamel,
          doorCenterX, DOOR_H / 2 - 0.05, 0, 0, 0, 0);
  addMesh(door, new RoundedBoxGeometry(DOOR_W, 0.10, 0.10, 2, 0.012), enamel,
          doorCenterX, -DOOR_H / 2 + 0.05, 0, 0, 0, 0);
  addMesh(door, new RoundedBoxGeometry(0.10, DOOR_H, 0.10, 2, 0.012), enamel,
          0.05, 0, 0, 0, 0, 0);
  addMesh(door, new RoundedBoxGeometry(0.10, DOOR_H, 0.10, 2, 0.012), enamel,
          DOOR_W - 0.05, 0, 0, 0, 0, 0);

  // Two glass panes with a narrow air gap, as on a real appliance door.
  addMesh(door, new RoundedBoxGeometry(DOOR_W - 0.22, DOOR_H - 0.22, 0.016, 2, 0.008),
          glass, doorCenterX, 0, 0.018);
  addMesh(door, new RoundedBoxGeometry(DOOR_W - 0.22, DOOR_H - 0.22, 0.016, 2, 0.008),
          glass, doorCenterX, 0, -0.018);

  // Gasket around the glass, pressed against the cavity when closed.
  addMesh(door, new RoundedBoxGeometry(DOOR_W - 0.16, 0.05, 0.05, 2, 0.01), rubber,
          doorCenterX, DOOR_H / 2 - 0.16, -0.02, 0, 0, 0);
  addMesh(door, new RoundedBoxGeometry(DOOR_W - 0.16, 0.05, 0.05, 2, 0.01), rubber,
          doorCenterX, -DOOR_H / 2 + 0.16, -0.02, 0, 0, 0);

  // Handle on the free (right) edge, standing off the face.
  addMesh(door, new THREE.CylinderGeometry(0.032, 0.032, 0.62, 16), chrome,
          DOOR_W - 0.30, 0.10, 0.14, 0, 0, 0);
  addMesh(door, new THREE.CylinderGeometry(0.030, 0.030, 0.16, 12), chrome,
          DOOR_W - 0.30, 0.10, 0.08, Math.PI / 2, 0, 0);
  addMesh(door, new THREE.SphereGeometry(0.046, 16, 16), chrome,
          DOOR_W - 0.30, 0.41, 0.14);
  addMesh(door, new THREE.SphereGeometry(0.046, 16, 16), chrome,
          DOOR_W - 0.30, -0.21, 0.14);

  // Hinge barrels, visible at the left edge when the door is open.
  for (const hy of [-0.85, 0.0, 0.85]) {
    addMesh(door, new THREE.CylinderGeometry(0.035, 0.035, 0.16, 14), chrome,
            0.0, hy, 0.0, 0, 0, 0);
  }

  door.userData.closedZ = 1.62;
  door.userData.openAngle = -1.15;
  group.add(door);

  const fasciaTex = fasciaMap();
  const fasciaMat = enamel.clone();
  fasciaMat.map = fasciaTex;
  fasciaMat.roughness = 0.48;
  addMesh(group, new RoundedBoxGeometry(5.18, 0.44, 0.56, 2, 0.03), fasciaMat, 0, 2.99, 1.22);
  const knobs = [];
  for (let i = 0; i < 4; i++) {
    const x = -1.55 + i * 0.74;
    const knob = new THREE.Group();
    knob.position.set(x, 3.22, 1.4);
    addMesh(knob, new THREE.CylinderGeometry(0.075, 0.075, 0.055, 24), chrome, 0, -0.02, 0);
    addMesh(knob, new THREE.CylinderGeometry(0.048, 0.048, 0.042, 18), brass, 0, 0.02, 0);
    addMesh(knob, new THREE.CylinderGeometry(0.012, 0.012, 0.038, 10), dark, 0, 0.04, 0.018, 0.55, 0, 0);
    group.add(knob);
    knobs.push(knob);
  }
  addMesh(group, new THREE.BoxGeometry(1.22, 0.18, 0.045), metal("#12181c", 0.18, 0.32), 1.62, 3.01, 1.5);
  const screen = addMesh(group, new THREE.BoxGeometry(0.92, 0.09, 0.02), metal("#7eb8c4", 0.2, 0.28, 0.6), 1.62, 3.01, 1.53);
  const led = addMesh(
    group,
    new THREE.CylinderGeometry(0.018, 0.018, 0.012, 12),
    new THREE.MeshStandardMaterial({ color: "#7a9e7e", emissive: "#7a9e7e", emissiveIntensity: 0.8 }),
    2.18,
    3.12,
    1.48,
    Math.PI / 2,
    0,
    0,
  );

  const heatMat = new THREE.MeshStandardMaterial({
    color: "#b85a32",
    emissive: "#c45c26",
    emissiveIntensity: 0.22,
    metalness: 0.48,
    roughness: 0.28,
  });
  const coil = new THREE.Group();
  for (let i = 0; i < 6; i++) {
    const x = -1.75 + i * 0.7;
    const rod = new THREE.Mesh(new THREE.CylinderGeometry(0.028, 0.028, 2.12, 20), heatMat);
    rod.rotation.x = Math.PI / 2;
    rod.position.set(x, 2.28, -0.02);
    rod.castShadow = true;
    coil.add(rod);
    const uFront = new THREE.Mesh(new THREE.TorusGeometry(0.085, 0.028, 14, 24, Math.PI), heatMat);
    uFront.rotation.set(0, Math.PI / 2, Math.PI / 2);
    uFront.position.set(x, 2.195, 1.06);
    coil.add(uFront);
    const uBack = new THREE.Mesh(new THREE.TorusGeometry(0.085, 0.028, 14, 24, Math.PI), heatMat);
    uBack.rotation.set(0, -Math.PI / 2, Math.PI / 2);
    uBack.position.set(x, 2.195, -1.1);
    coil.add(uBack);
    const dropF = new THREE.Mesh(new THREE.CylinderGeometry(0.028, 0.028, 0.09, 14), heatMat);
    dropF.position.set(x, 2.15, 1.145);
    coil.add(dropF);
    const dropB = new THREE.Mesh(new THREE.CylinderGeometry(0.028, 0.028, 0.09, 14), heatMat);
    dropB.position.set(x, 2.15, -1.185);
    coil.add(dropB);
    addMesh(coil, new THREE.CylinderGeometry(0.052, 0.048, 0.12, 16), ceramic, x, 2.28, 1.18, Math.PI / 2, 0, 0);
    addMesh(coil, new THREE.CylinderGeometry(0.052, 0.048, 0.12, 16), ceramic, x, 2.28, -1.22, Math.PI / 2, 0, 0);
    addMesh(coil, new THREE.CylinderGeometry(0.018, 0.018, 0.08, 10), chrome, x, 2.28, 1.26, Math.PI / 2, 0, 0);
    addMesh(coil, new THREE.CylinderGeometry(0.018, 0.018, 0.08, 10), chrome, x, 2.28, -1.30, Math.PI / 2, 0, 0);
  }
  const bus = new THREE.Mesh(new THREE.BoxGeometry(4.3, 0.018, 0.04), chrome);
  bus.position.set(0, 2.28, 1.32);
  coil.add(bus);
  const busB = new THREE.Mesh(new THREE.BoxGeometry(4.3, 0.018, 0.04), chrome);
  busB.position.set(0, 2.28, -1.34);
  coil.add(busB);
  group.add(coil);

  const lamp = addMesh(
    group,
    new THREE.SphereGeometry(0.078, 20, 20),
    new THREE.MeshStandardMaterial({
      color: "#fff4d6",
      emissive: "#ffe7b0",
      emissiveIntensity: 1.45,
    }),
    1.78,
    2.22,
    0.58,
  );
  addMesh(group, new THREE.CylinderGeometry(0.095, 0.095, 0.04, 18), chrome, 1.78, 2.29, 0.58);
  addMesh(group, new THREE.CylinderGeometry(0.11, 0.09, 0.03, 16), dark, 1.78, 2.32, 0.58);

  const fanHub = new THREE.Group();
  fanHub.position.set(0.02, 1.4, -1.24);
  addMesh(fanHub, new THREE.CylinderGeometry(0.92, 0.92, 0.06, 48), metal("#1a1f24", 0.35, 0.55), 0, 0, -0.16, Math.PI / 2, 0, 0);
  addMesh(fanHub, new THREE.CylinderGeometry(0.30, 0.36, 0.32, 22), metal("#161b20", 0.42, 0.5), 0, 0, -0.28, Math.PI / 2, 0, 0);
  addMesh(fanHub, new THREE.BoxGeometry(0.22, 0.22, 0.16), dark, 0, -0.5, -0.28);
  addMesh(fanHub, new THREE.TorusGeometry(0.80, 0.022, 10, 56), chrome, 0, 0, -0.01, Math.PI / 2, 0, 0);
  addMesh(fanHub, new THREE.CylinderGeometry(0.84, 0.84, 0.028, 48), metal("#14181c", 0.28, 0.62), 0, 0, -0.11, Math.PI / 2, 0, 0);
  for (let i = 0; i < 4; i++) {
    const bar = new THREE.Mesh(new THREE.BoxGeometry(0.008, 1.52, 0.006), chrome);
    bar.rotation.z = (i * Math.PI) / 4;
    bar.position.z = -0.02;
    fanHub.add(bar);
  }
  const blades = new THREE.Group();
  const bladeMat = new THREE.MeshPhysicalMaterial({
    color: "#2a3238",
    metalness: 0.72,
    roughness: 0.34,
    envMapIntensity: 0.85,
    clearcoat: 0.18,
    clearcoatRoughness: 0.42,
  });
  const foil = airfoilGeometry();
  for (let i = 0; i < 10; i++) {
    const blade = new THREE.Mesh(foil, bladeMat);
    blade.position.set(-0.02, 0.22, 0.22);
    blade.rotation.set(0.18, 0.68, 0.06);
    blade.castShadow = true;
    blade.receiveShadow = true;
    const wrap = new THREE.Group();
    wrap.rotation.z = (i * Math.PI * 2) / 10;
    wrap.add(blade);
    blades.add(wrap);
  }
  fanHub.add(blades);
  addMesh(fanHub, new THREE.CylinderGeometry(0.19, 0.19, 0.13, 28), chrome, 0, 0, 0.22, Math.PI / 2, 0, 0);
  addMesh(fanHub, new THREE.CylinderGeometry(0.058, 0.058, 0.16, 16), chrome, 0, 0, 0.21, Math.PI / 2, 0, 0);
  addMesh(fanHub, new THREE.TorusGeometry(0.16, 0.014, 8, 28), brass, 0, 0, 0.20, Math.PI / 2, 0, 0);
  group.add(fanHub);

  for (let ix = -6; ix <= 6; ix++) {
    for (let iy = -5; iy <= 5; iy++) {
      if (ix * ix + iy * iy < 28) continue;
      addMesh(
        group,
        new THREE.CircleGeometry(0.024, 10),
        dark,
        ix * 0.17,
        1.4 + iy * 0.155,
        -1.295,
      );
    }
  }

  const pipe = new THREE.Mesh(new THREE.CylinderGeometry(0.044, 0.044, 0.68, 16), liner);
  pipe.rotation.z = Math.PI / 2;
  pipe.position.set(-2.0, 1.62, 0.18);
  group.add(pipe);
  addMesh(group, new THREE.SphereGeometry(0.06, 16, 16), liner, -1.68, 1.62, 0.18);
  addMesh(group, new THREE.CylinderGeometry(0.072, 0.072, 0.13, 14), dark, -2.28, 1.62, 0.18, 0, 0, Math.PI / 2);
  const jetMat = new THREE.MeshStandardMaterial({
    color: "#d9e7ee",
    transparent: true,
    opacity: 0.32,
    roughness: 1,
    depthWrite: false,
  });
  const jet = addMesh(group, new THREE.ConeGeometry(0.08, 0.2, 16, 1, true), jetMat, -1.54, 1.62, 0.18, 0, 0, -Math.PI / 2);
  addMesh(group, new THREE.ConeGeometry(0.055, 0.14, 14, 1, true), jetMat, -1.5, 1.48, 0.32, 0.18, 0, -Math.PI / 2);

  const vent = new THREE.Group();
  for (let i = 0; i < 7; i++) {
    addMesh(vent, new THREE.BoxGeometry(0.5, 0.032, 0.055), dark, 1.86, 2.2 - i * 0.068, 1.26);
  }
  group.add(vent);

  const railMat = metal("#bcc5cb", 0.82, 0.24);
  for (let i = 0; i < 5; i++) {
    const z = -0.9 + i * 0.46;
    addMesh(group, new THREE.BoxGeometry(3.62, 0.018, 0.018), railMat, 0, 0.5, z);
    addMesh(group, new THREE.BoxGeometry(3.62, 0.018, 0.018), railMat, 0, 1.12, z);
    addMesh(group, new THREE.BoxGeometry(0.028, 0.64, 0.018), railMat, -1.78, 0.81, z);
    addMesh(group, new THREE.BoxGeometry(0.028, 0.64, 0.018), railMat, 1.78, 0.81, z);
  }

  addMesh(group, new RoundedBoxGeometry(2.24, 0.034, 1.48, 2, 0.012), liner, 0, 0.64, 0.08);
  addMesh(group, new RoundedBoxGeometry(2.3, 0.05, 1.52, 2, 0.014), liner, 0, 0.67, 0.08);
  addMesh(group, new THREE.BoxGeometry(0.04, 0.04, 1.5), dark, -1.1, 0.7, 0.08);
  addMesh(group, new THREE.BoxGeometry(0.04, 0.04, 1.5), dark, 1.1, 0.7, 0.08);
  for (let i = 0; i < 6; i++) {
    addMesh(group, new THREE.BoxGeometry(2.0, 0.01, 0.028), dark, 0, 0.7, -0.55 + i * 0.22);
  }
  for (let ix = -4; ix <= 4; ix++) {
    for (let iz = -3; iz <= 3; iz++) {
      addMesh(group, new THREE.CircleGeometry(0.028, 8), dark, ix * 0.22, 0.705, 0.08 + iz * 0.18);
    }
  }
  addMesh(group, new RoundedBoxGeometry(5.4, 0.16, 3.6, 2, 0.04), metal("#1a1f24", 0.22, 0.72), 0, -0.22, 0.08);

  addMesh(group, new RoundedBoxGeometry(0.64, 0.4, 0.8, 2, 0.03), dark, -2.08, 0.34, -0.88);
  addMesh(group, new THREE.BoxGeometry(0.52, 0.24, 0.08), glass, -2.08, 0.36, -0.48);
  const water = addMesh(group, new THREE.BoxGeometry(0.46, 0.18, 0.02), STEAM_LEVEL(), -2.08, 0.3, -0.47);
  water.userData.baseY = 0.3;

  addMesh(group, new THREE.BoxGeometry(2.4, 0.04, 0.18), dark, 0, 0.12, 1.18);
  addMesh(group, new RoundedBoxGeometry(2.2, 0.03, 1.1, 2, 0.01), metal("#6a7378", 0.55, 0.42), 0, 0.14, 0.22);

  for (const x of [-2.15, 2.15]) {
    for (const z of [-1.2, 1.15]) {
      addMesh(group, new THREE.CylinderGeometry(0.07, 0.09, 0.12, 14), enamel, x, -0.2, z);
    }
  }

  addMesh(group, new THREE.BoxGeometry(0.08, 0.08, 0.55), chrome, 1.55, 1.05, 0.55);
  addMesh(group, new THREE.CylinderGeometry(0.012, 0.012, 0.58, 12), chrome, 0.55, 0.95, 0.2, 0, 0, Math.PI / 2);
  addMesh(group, new THREE.SphereGeometry(0.02, 12, 12), metal("#c45c26", 0.4, 0.35), 0.26, 0.95, 0.2);

  addMesh(group, new THREE.BoxGeometry(0.22, 0.08, 0.08), dark, -2.08, 2.22, 0.18);
  addMesh(group, new THREE.CylinderGeometry(0.035, 0.035, 0.16, 12), chrome, -1.92, 2.22, 0.18, 0, 0, Math.PI / 2);
  addMesh(group, new RoundedBoxGeometry(0.34, 0.06, 1.6, 2, 0.01), dark, 0, 2.46, 0.08);
  for (let i = 0; i < 3; i++) {
    addMesh(group, new THREE.BoxGeometry(0.04, 0.22, 0.04), brass, -1.92 + i * 1.92, 0.22, 1.22);
  }
  addMesh(group, new THREE.CylinderGeometry(0.018, 0.018, 0.42, 10), chrome, 1.92, 2.18, -0.22, 0, 0, Math.PI / 2);
  addMesh(group, new THREE.SphereGeometry(0.028, 12, 12), metal("#c45c26", 0.35, 0.4), 1.72, 2.18, -0.22);
  addMesh(group, new THREE.BoxGeometry(0.12, 0.04, 0.22), dark, 2.08, 0.42, 1.18);
  addMesh(group, new THREE.CylinderGeometry(0.03, 0.03, 0.18, 12), chrome, 2.08, 0.52, 1.18);
  for (let i = 0; i < 4; i++) {
    addMesh(group, new THREE.BoxGeometry(0.06, 0.03, 0.08), brass, -1.78, 0.52 + i * 0.42, 0.92);
    addMesh(group, new THREE.BoxGeometry(0.06, 0.03, 0.08), brass, 1.78, 0.52 + i * 0.42, 0.92);
  }

  return { group, coilMat: heatMat, blades, vent, jet, lamp, door, water, knobs, screen, led, fasciaMap: fasciaTex };
}

function STEAM_LEVEL() {
  return new THREE.MeshStandardMaterial({
    color: "#2a6f7f",
    emissive: "#1a4a55",
    emissiveIntensity: 0.35,
    roughness: 0.4,
  });
}

function makeFood() {
  const group = new THREE.Group();
  const slabs = [];
  const w = 1.68 / N_CELL;
  // Deterministic pseudo-random so the stack looks hand-cut but rebuilds the
  // same way on every load.
  let seed = 20241334;
  const rnd = () => {
    seed = (seed * 1664525 + 1013904223) >>> 0;
    return seed / 4294967296;
  };

  for (let i = 0; i < N_CELL; i++) {
    const fat = i === 5;
    const slice = new THREE.Group();

    // --- body ---------------------------------------------------------
    const mat = new THREE.MeshPhysicalMaterial({
      color: fat ? "#8a5a32" : "#c9a078",
      roughness: fat ? 0.44 : 0.60,
      metalness: 0.02,
      clearcoat: fat ? 0.34 : 0.18,
      clearcoatRoughness: fat ? 0.30 : 0.46,
    });
    // 1-1.5% variation: enough that the stack is not machine-perfect,
    // small enough that it still reads as one piece cut into portions.
    const bw = w * (fat ? 0.985 : 0.995) * (0.993 + rnd() * 0.014);
    const bh = (fat ? 0.48 : 0.40) * (0.994 + rnd() * 0.012);
    const bd = (fat ? 1.26 : 1.16) * (0.994 + rnd() * 0.012);
    const body = new THREE.Mesh(
      new RoundedBoxGeometry(bw, bh, bd, 4, 0.012),
      mat,
    );
    body.userData.baseColor = mat.color.clone();
    body.castShadow = true;
    body.receiveShadow = true;
    body.userData.fat = fat;
    body.userData.tintable = true;
    slice.add(body);

    // --- surface cap --------------------------------------------------
    // The +y face is what the heater sees; give it its own material so the
    // browning tint can act on the crust rather than the whole block.
    const capMat = new THREE.MeshPhysicalMaterial({
      color: fat ? "#a87243" : "#dcb489",
      roughness: fat ? 0.32 : 0.40,
      metalness: 0.0,
      clearcoat: 0.55,
      clearcoatRoughness: 0.22,
    });
    const cap = new THREE.Mesh(
      new RoundedBoxGeometry(bw * 0.995, 0.030, bd * 0.995, 3, 0.008),
      capMat,
    );
    cap.position.y = bh / 2 + 0.004;
    cap.castShadow = false;
    cap.receiveShadow = true;
    cap.userData.baseColor = capMat.color.clone();
    cap.userData.tintable = true;
    cap.userData.isCap = true;
    slice.add(cap);

    // --- interior grain ------------------------------------------------
    // Two small darker inserts; visible through the section view and at the
    // open cut faces, which is where a real slice shows its structure.
    for (let g = 0; g < 2; g++) {
      const gMat = new THREE.MeshStandardMaterial({
        color: fat ? "#7d5130" : "#b8916b",
        roughness: 0.78,
        metalness: 0.01,
      });
      const gm = new THREE.Mesh(
        new THREE.BoxGeometry(bw * (0.12 + rnd() * 0.14), bh * 0.42, bd * (0.06 + rnd() * 0.10)),
        gMat,
      );
      gm.position.set(
        (rnd() - 0.5) * bw * 0.5,
        (rnd() - 0.5) * bh * 0.15,
        (rnd() - 0.5) * bd * 0.55,
      );
      gm.userData.tintable = true;
      gm.userData.baseColor = gMat.color.clone();
      slice.add(gm);
    }

    slice.position.set(-0.84 + (i + 0.5) * w, 0.93, 0.08);
    slice.userData.body = body;
    group.add(slice);
    slabs.push(slice);
  }
  group.userData.slabs = slabs;
  return group;
}

function makeSteam() {
  const n = 1100;
  const geo = new THREE.BufferGeometry();
  const pos = new Float32Array(n * 3);
  const sizes = new Float32Array(n);
  const seeds = [];
  const rng = (() => {
    let x = 987654321;
    return () => {
      x = (x * 1664525 + 1013904223) >>> 0;
      return x / 4294967296;
    };
  })();
  for (let i = 0; i < n; i++) {
    // Cone from the nozzle mouth: axial distance t, radial spread grows with t
    // so the plume widens as it travels, which is what makes it look like gas.
    const t = Math.pow(rng(), 0.75);
    const spread = 0.05 + 0.42 * t;
    const theta = rng() * Math.PI * 2;
    const r = spread * Math.sqrt(rng());
    seeds.push({
      x: -1.70 + 2.35 * t,
      y: 1.44 + 0.30 * t + Math.sin(theta) * r * 0.6,
      z: 0.20 + Math.cos(theta) * r,
      s: 0.55 + rng() * 1.15,
      spin: rng() * Math.PI * 2,
    });
    pos[i * 3] = seeds[i].x;
    pos[i * 3 + 1] = seeds[i].y;
    pos[i * 3 + 2] = seeds[i].z;
    sizes[i] = 0.16 + 0.22 * rng() + 0.14 * t;
  }
  geo.setAttribute("size", new THREE.BufferAttribute(sizes, 1));
  geo.setAttribute("position", new THREE.BufferAttribute(pos, 3));
  const mat = new THREE.PointsMaterial({
    map: steamTexture(),
    transparent: true,
    depthWrite: false,
    blending: THREE.NormalBlending,
    size: 0.30,
    opacity: 0.36,
    sizeAttenuation: true,
    color: 0xd7e6ee,
  });
  // Drift runs in the vertex shader from one time uniform, so the CPU never
  // touches the position buffer after the cloud is built.
  mat.userData.clock = { value: 0 };
  mat.onBeforeCompile = (shader) => {
    shader.uniforms.uSteamTime = mat.userData.clock;
    shader.vertexShader = shader.vertexShader
      .replace(
        "#include <common>",
        "#include <common>\nuniform float uSteamTime;",
      )
      .replace(
        "#include <begin_vertex>",
        `#include <begin_vertex>
         // Bounded plume. u is a per-particle phase so the cloud does not move
         // as a rigid block; the offsets stay inside the cavity box
         // (x in [-2.2, 2.2], y in [0.15, 2.5], z in [-1.3, 1.4]).
         float u = fract(uSteamTime * 0.22 + position.y * 0.37 + position.z * 0.21);
         float life = smoothstep(0.0, 0.25, u) * (1.0 - smoothstep(0.55, 1.0, u));
         transformed.x += u * 2.34 * life;
         transformed.y += u * 0.72 * life + 0.05 * sin(uSteamTime * 1.4 + position.x * 5.0) * life;
         transformed.z += 0.10 * sin(uSteamTime * 0.9 + position.y * 4.0) * life;
         transformed.x = clamp(transformed.x, -2.15, 2.15);
         transformed.y = clamp(transformed.y, 0.18, 2.46);
         transformed.z = clamp(transformed.z, -1.26, 1.36);`,
      );
  };
  const points = new THREE.Points(geo, mat);
  points.visible = false;
  return { points, seeds, pos };
}

/**
 * Tileable procedural surface maps.
 *
 * Returns { normalMap, roughnessMap } built from one canvas pass so the two
 * stay correlated: where the grain is high the surface catches less light and
 * is slightly rougher, which is how real brushed metal behaves.
 */
function proceduralSurfaceMaps({ size = 256, streak = 0.22, grain = 0.08 } = {}) {
  const h = document.createElement("canvas");
  h.width = h.height = size;
  const hc = h.getContext("2d");
  const img = hc.createImageData(size, size);
  // Height field: fine horizontal streaks plus a little isotropic noise.
  const rnd = (() => {
    let seed = 20241334;
    return () => {
      seed = (seed * 1664525 + 1013904223) >>> 0;
      return seed / 4294967296;
    };
  })();
  const height = new Float32Array(size * size);
  for (let y = 0; y < size; y++) {
    let row = 0.5;
    for (let x = 0; x < size; x++) {
      row += (rnd() - 0.5) * streak * 0.35;
      row = Math.min(1, Math.max(0, row * 0.994 + 0.003));
      height[y * size + x] = row + (rnd() - 0.5) * grain;
    }
  }
  // Normal map from the height field (Sobel-free central differences).
  const nrm = new Uint8ClampedArray(size * size * 4);
  const rough = new Uint8ClampedArray(size * size * 4);
  for (let y = 0; y < size; y++) {
    for (let x = 0; x < size; x++) {
      const i = y * size + x;
      const xl = height[y * size + ((x - 1 + size) % size)];
      const xr = height[y * size + ((x + 1) % size)];
      const yt = height[((y - 1 + size) % size) * size + x];
      const yb = height[((y + 1) % size) * size + x];
      const dx = (xr - xl) * 2.2;
      const dy = (yb - yt) * 2.2;
      const len = Math.hypot(dx, dy, 1);
      nrm[i * 4] = ((dx / len) * 0.5 + 0.5) * 255;
      nrm[i * 4 + 1] = ((dy / len) * 0.5 + 0.5) * 255;
      nrm[i * 4 + 2] = ((1 / len) * 0.5 + 0.5) * 255;
      nrm[i * 4 + 3] = 255;
      const r = 186 + height[i] * 34;
      rough[i * 4] = r;
      rough[i * 4 + 1] = r;
      rough[i * 4 + 2] = r;
      rough[i * 4 + 3] = 255;
    }
  }
  const mk = (arr, repeat) => {
    const c = document.createElement("canvas");
    c.width = c.height = size;
    c.getContext("2d").putImageData(new ImageData(arr, size, size), 0, 0);
    const t = new THREE.CanvasTexture(c);
    t.wrapS = t.wrapT = THREE.RepeatWrapping;
    t.repeat.set(repeat, repeat);
    t.anisotropy = 8;
    return t;
  };
  hc.putImageData(img, 0, 0);
  return {
    normalMap: mk(nrm, 14),
    roughnessMap: mk(rough, 14),
  };
}

const PROBE_GOLD = new THREE.Color("#c4a574");
const STEAM_COOL = new THREE.Color("#cfe3ea");
const TOASTED = new THREE.Color("#6b3a18");

export default function Scene({ frame, length = 0.03, doorOpen = true, cook = "combi", section = false }) {
  const host = useRef(null);
  const state = useRef(null);

  useEffect(() => {
    const el = host.current;
    const renderer = new THREE.WebGLRenderer({ antialias: true, alpha: false });
    renderer.setPixelRatio(Math.min(window.devicePixelRatio || 1, 1.75));
    renderer.setSize(el.clientWidth || 760, el.clientHeight || 520);
    renderer.toneMapping = THREE.ACESFilmicToneMapping;
    renderer.toneMappingExposure = 1.12;
    renderer.outputColorSpace = THREE.SRGBColorSpace;
    renderer.shadowMap.enabled = true;
    renderer.shadowMap.type = THREE.PCFSoftShadowMap;
    el.appendChild(renderer.domElement);

    const scene = new THREE.Scene();
    scene.background = new THREE.Color("#101418");
    scene.fog = new THREE.Fog("#101418", 12.5, 22);
    const pmrem = new THREE.PMREMGenerator(renderer);
    scene.environment = pmrem.fromScene(new RoomEnvironment(), 0.035).texture;

    const viewW = el.clientWidth || 760;
    const viewH = el.clientHeight || 520;
    const camera = new THREE.PerspectiveCamera(34, viewW / viewH, 0.1, 40);

    // Post-processing chain. GTAO supplies the contact darkening the cavity
    // needs: panel seams, the shadow line under the coil bank and the crease
    // where the food meets the rack. Panels otherwise read as separate boxes.
    const composer = new EffectComposer(renderer);
    composer.setPixelRatio(Math.min(window.devicePixelRatio || 1, 1.75));
    composer.setSize(viewW, viewH);
    const gtao = new GTAOPass(scene, camera, viewW, viewH);
    gtao.updateGtaoMaterial({
      radius: 0.22,
      distanceExponent: 1.4,
      thickness: 1.0,
      scale: 1.05,
      samples: 16,
      distanceFallOff: 1.0,
      screenSpaceRadius: false,
    });
    gtao.blendIntensity = 1.0;
    composer.addPass(new RenderPass(scene, camera));
    composer.addPass(gtao);
    composer.addPass(new OutputPass());

    const hemi = new THREE.HemisphereLight(0xf4efe6, 0x2c3338, 0.5);
    const key = new THREE.DirectionalLight(0xfff3e4, 1.12);
    key.position.set(3.6, 5.2, 4.6);
    key.castShadow = true;
    key.shadow.mapSize.set(2048, 2048);
    key.shadow.bias = -0.0004;
    key.shadow.normalBias = 0.02;
    key.shadow.camera.near = 1;
    key.shadow.camera.far = 18;
    key.shadow.camera.left = -4.2;
    key.shadow.camera.right = 4.2;
    key.shadow.camera.top = 4.6;
    key.shadow.camera.bottom = -3.2;
    const fill = new THREE.DirectionalLight(0xb7d3dc, 0.36);
    fill.position.set(-3.8, 1.7, 2.5);
    const rim = new THREE.PointLight(0xe07a3d, 0.55, 10);
    rim.position.set(0, 2.2, 0.15);
    const interior = new THREE.PointLight(0xfff1dc, 1.08, 8);
    interior.position.set(0, 1.5, 0.4);
    const lampLight = new THREE.PointLight(0xffe7b0, 0.72, 5);
    lampLight.position.set(1.78, 2.22, 0.58);
    const fanLight = new THREE.PointLight(0xe8f0f4, 1.35, 3.6);
    fanLight.position.set(0.02, 1.4, -0.28);
    scene.add(hemi, key, fill, rim, interior, lampLight, fanLight);

    const ground = new THREE.Mesh(
      new THREE.CircleGeometry(7.5, 48),
      new THREE.MeshStandardMaterial({ color: "#161b20", roughness: 0.92, metalness: 0.08 }),
    );
    ground.rotation.x = -Math.PI / 2;
    ground.position.y = -0.28;
    ground.receiveShadow = true;

    // Contact shadow: a soft radial darkening under the body so it reads as
    // resting on the floor rather than hovering above it.
    const contactCanvas = document.createElement("canvas");
    contactCanvas.width = contactCanvas.height = 256;
    const cctx = contactCanvas.getContext("2d");
    const grad = cctx.createRadialGradient(128, 128, 10, 128, 128, 126);
    grad.addColorStop(0, "rgba(0,0,0,0.55)");
    grad.addColorStop(0.55, "rgba(0,0,0,0.22)");
    grad.addColorStop(1, "rgba(0,0,0,0)");
    cctx.fillStyle = grad;
    cctx.fillRect(0, 0, 256, 256);
    const contact = new THREE.Mesh(
      new THREE.PlaneGeometry(7.4, 5.2),
      new THREE.MeshBasicMaterial({
        map: new THREE.CanvasTexture(contactCanvas),
        transparent: true,
        depthWrite: false,
      }),
    );
    contact.rotation.x = -Math.PI / 2;
    contact.position.y = -0.275;
    scene.add(contact);
    scene.add(ground);

    const cavity = makeCavity();
    scene.add(cavity.group);
    const food = makeFood();
    scene.add(food);
    const steam = makeSteam();
    scene.add(steam.points);

    const target = new THREE.Vector3(0.04, 1.36, 0.22);
    let yaw = CAM.yaw;
    let pitch = CAM.pitch;
    let dist = CAM.dist;
    let dragging = false;
    let lastX = 0;
    let lastY = 0;
    const canvas = renderer.domElement;
    canvas.style.position = "absolute";
    canvas.style.inset = "0";
    canvas.style.width = "100%";
    canvas.style.height = "100%";
    canvas.style.touchAction = "none";
    canvas.style.cursor = "grab";
    const place = () => {
      camera.position.set(
        target.x + dist * Math.cos(pitch) * Math.sin(yaw),
        target.y + dist * Math.sin(pitch),
        target.z + dist * Math.cos(pitch) * Math.cos(yaw),
      );
      camera.lookAt(target);
    };
    place();
    const clampDist = (value) => Math.min(CAM.max, Math.max(CAM.min, value));
    // Read-only hook so automated checks can sample the animation state.
    window.__actsDebug = () => {
      const d = state.current?.cavity?.door;
      return { doorAngle: d ? d.rotation.y : 0 };
    };
    window.__actsCam = {
      set(nextYaw, nextPitch, nextDist) {
        if (Number.isFinite(nextYaw)) yaw = nextYaw;
        if (Number.isFinite(nextPitch)) pitch = nextPitch;
        if (Number.isFinite(nextDist)) dist = clampDist(nextDist);
        place();
      },
      get() {
        return { yaw, pitch, dist };
      },
      reset() {
        yaw = CAM.yaw;
        pitch = CAM.pitch;
        dist = CAM.dist;
        place();
      },
    };

    const onDown = (ev) => {
      if (ev.pointerType === "mouse" && ev.button !== 0) return;
      dragging = true;
      lastX = ev.clientX;
      lastY = ev.clientY;
      canvas.style.cursor = "grabbing";
      canvas.setPointerCapture?.(ev.pointerId);
    };
    const onMove = (ev) => {
      if (!dragging) return;
      if (ev.cancelable) ev.preventDefault();
      yaw -= (ev.clientX - lastX) * 0.007;
      pitch = Math.min(0.82, Math.max(-0.04, pitch + (ev.clientY - lastY) * 0.007));
      lastX = ev.clientX;
      lastY = ev.clientY;
      place();
    };
    const onUp = (ev) => {
      dragging = false;
      canvas.style.cursor = "grab";
      if (ev?.pointerId != null) canvas.releasePointerCapture?.(ev.pointerId);
    };
    const onWheel = (ev) => {
      ev.preventDefault();
      ev.stopPropagation();
      const pixels = ev.deltaMode === 1 ? ev.deltaY * 16 : ev.deltaMode === 2 ? ev.deltaY * el.clientHeight : ev.deltaY;
      dist = clampDist(dist + pixels * 0.003);
      place();
    };
    const onResize = () => {
      const w = el.clientWidth || 760;
      const h = el.clientHeight || 520;
      camera.aspect = w / h;
      camera.updateProjectionMatrix();
      renderer.setSize(w, h);
    };
    canvas.addEventListener("pointerdown", onDown);
    canvas.addEventListener("pointermove", onMove, { passive: false });
    canvas.addEventListener("pointerup", onUp);
    canvas.addEventListener("pointercancel", onUp);
    canvas.addEventListener("wheel", onWheel, { passive: false });
    const onMenu = (ev) => ev.preventDefault();
    canvas.addEventListener("contextmenu", onMenu);
    window.addEventListener("resize", onResize);
    const ro = new ResizeObserver(onResize);
    ro.observe(el);
    onResize();

    state.current = {
      renderer, composer, scene, camera, food, cavity, steam, rim, interior, lampLight, el, place,
    };
    let alive = true;
    const tick = () => {
      if (!alive) return;
      const s = state.current;
      if (s) {
        // Time-based door motion, independent of frame rate and of whether
        // the trace is playing. Critically damped approach: each step moves a
        // fraction determined by elapsed time, so 60 fps and 144 fps look alike.
        if (s.cavity.door) {
          const d = s.cavity.door;
          const wantSection = s.sectionWanted ?? section;
          d.visible = !wantSection;
          if (!wantSection) {
            const now = performance.now();
            const dt = Math.min(0.05, (now - (s.lastDoorT || now)) / 1000);
            s.lastDoorT = now;
            const wantOpen = (s.doorWanted ?? (doorOpen ? "open" : "closed")) === "open";
            const target = wantOpen ? d.userData.openAngle : 0;
            const k = 1 - Math.exp(-9.5 * dt);
            d.rotation.y += (target - d.rotation.y) * k;
            // settle
            if (Math.abs(target - d.rotation.y) < 1e-4) d.rotation.y = target;
          }
        }
        const fan = s.frame?.fan ?? 0.4;
        s.cavity.blades.rotation.z += 0.035 + 0.18 * Math.min(fan / 1.3, 1);
        const f = s.frame;
        const steamOn = f?.steam ?? 0;
        const showSteam = steamOn > 1e-3;
        const pts = s.steam.points;
        pts.visible = showSteam;
        s.cavity.jet.visible = showSteam;
        const inProbe = f ? (f.time >= 150 && f.time < 190) : false;
        if (showSteam) {
          pts.material.color.copy(inProbe ? PROBE_GOLD : STEAM_COOL);
          pts.material.opacity = inProbe
            ? 0.50 + 0.30 * steamOn
            : 0.20 + 0.32 * steamOn;
          s.cavity.jet.scale.setScalar(inProbe ? 1.35 : 1.0);
          pts.material.userData.clock.value += inProbe ? 0.045 : 0.022;
        }
        if (showSteam) {
          s.steam.points.material.opacity = 0.22 + 0.42 * steamOn;
          s.steam.points.material.size = 0.14 + 0.14 * steamOn;
          const { seeds, pos } = s.steam;
          seeds.forEach((p, i) => {
            p.x += 0.008 + 0.014 * steamOn;
            p.y += 0.004 + 0.011 * steamOn;
            p.z += 0.0022 * Math.sin(p.x * 4.2 + i);
            if (p.x > 1.62 || p.y > 2.38) {
              p.x = -1.74 + Math.random() * 0.22;
              p.y = 1.40 + Math.random() * 0.38;
              p.z = 0.18 + (Math.random() - 0.5) * 0.86;
            }
            pos[i * 3] = p.x;
            pos[i * 3 + 1] = p.y + 0.018 * Math.sin(p.x * 6 + i);
            pos[i * 3 + 2] = p.z;
          });
          s.steam.points.geometry.attributes.position.needsUpdate = true;
        }
        if (s.cavity.water) {
          const water = s.frame?.water ?? 0.72;
          const sy = 0.45 + 0.7 * Math.min(Math.max(water, 0), 1);
          s.cavity.water.scale.y = sy;
          s.cavity.water.position.y = s.cavity.water.userData.baseY - 0.09 * (1 - sy);
        }
        composer.render();
      }
      requestAnimationFrame(tick);
    };
    tick();
    return () => {
      alive = false;
      renderer.dispose();
      pmrem.dispose();
      canvas.removeEventListener("pointerdown", onDown);
      canvas.removeEventListener("pointermove", onMove);
      canvas.removeEventListener("pointerup", onUp);
      canvas.removeEventListener("pointercancel", onUp);
      canvas.removeEventListener("wheel", onWheel);
      canvas.removeEventListener("contextmenu", onMenu);
      window.removeEventListener("resize", onResize);
      ro.disconnect();
      if (canvas.parentNode === el) el.removeChild(canvas);
    };
  }, []);

  // Publish the desired door state so the animation loop (which lives in the
  // setup effect and is never re-created) can read the current value each frame
  // instead of seeing the one captured when the context was built.
  useEffect(() => {
    if (state.current) state.current.doorWanted = doorOpen ? "open" : "closed";
    if (state.current) state.current.sectionWanted = section;
  }, [doorOpen, section]);

  useEffect(() => {
    const s = state.current;
    if (!s || !frame) return;
    s.frame = frame;
    const slabs = s.food.userData.slabs || [];
    const span = Math.max(frame.t1 - frame.t2, 1);
    // Surface browning proxy in [0, 1]; the log carries shell and the panel
    // carries no alpha_b, so shell is used as the visible browning proxy.
    const brown = Math.min(1, Math.max(0, (frame.shell ?? 0) * 14 + Math.max(frame.t1 - 120, 0) / 90));
    slabs.forEach((slice, i) => {
      const u = i / Math.max(N_CELL - 1, 1);
      const value = frame.t1 - span * u ** 1.15;
      const color = heatColor(value);
      // Only the outer slices are exposed to the heater, so browning falls off
      // quickly with index; the cap takes more of the tint than the body.
      const outer = Math.max(0, 1 - u * 6);
      slice.traverse((mesh) => {
        if (!mesh.isMesh || !mesh.userData.tintable) return;
        const base = mesh.userData.baseColor;
        mesh.material.color.copy(base);
        // Blend the temperature colour into the body, but keep the cap and
        // grain closer to their own material so the surface still reads as
        // crust rather than as a heat map.
        const bodyMix = mesh.userData.isCap ? 0.35 : 0.85;
        mesh.material.color.lerp(color, bodyMix);
        const mix = brown * outer * (mesh.userData.isCap ? 0.75 : 0.45);
        if (mix > 0.001) mesh.material.color.lerp(TOASTED, mix);
      });
    });
    s.food.scale.set(length / 0.03, 1, 1);
    s.cavity.coilMat.emissiveIntensity = 0.16 + 1.55 * frame.heat;
    s.rim.intensity = 0.22 + 1.45 * frame.heat;
    s.interior.intensity = 0.72 + 0.7 * frame.heat;
    s.lampLight.intensity = 0.45 + 0.55 * frame.heat;
    s.cavity.vent.scale.set(1, 1, 0.55 + 1.2 * frame.exhaust);
    if (s.cavity.knobs) {
      const cookAngle = { steam: 0.4, bake: 2.2, combi: 4.1 }[cook] || 4.1;
      s.cavity.knobs[0].rotation.y = frame.heat * 4.4;
      s.cavity.knobs[1].rotation.y = frame.steam * 4.4;
      s.cavity.knobs[2].rotation.y = (frame.fan / 1.3) * 4.4;
      s.cavity.knobs[3].rotation.y = cookAngle;
    }
    if (s.cavity.led?.material) {
      const probingNow = frame.time >= 150 && frame.time < 190;
      const color = probingNow ? "#7eb8c9" : frame.mode === 2 ? "#7a9e7e" : "#e07a3d";
      s.cavity.led.material.color.set(color);
      s.cavity.led.material.emissive.set(color);
      s.cavity.led.material.emissiveIntensity = 0.55 + 0.7 * Math.max(frame.heat, frame.steam);
    }
    if (s.cavity.screen?.material) {
      s.cavity.screen.material.emissive = s.cavity.screen.material.emissive || new THREE.Color("#7eb8c4");
      s.cavity.screen.material.emissive.set(frame.mode === 1 ? "#7eb8c9" : "#c4a574");
      s.cavity.screen.material.emissiveIntensity = 0.25 + 0.35 * (frame.mode === 1 ? 1 : frame.heat);
    }
    const fasciaTex = s.cavity.fasciaMap;
    if (fasciaTex?.userData?.paint) {
      fasciaTex.userData.paint(frame);
      fasciaTex.needsUpdate = true;
    }
    s.renderer.render(s.scene, s.camera);
  }, [frame, length, doorOpen, cook, section]);

  function zoomBy(step) {
    const cam = window.__actsCam;
    if (!cam) return;
    const now = cam.get();
    cam.set(now.yaw, now.pitch, now.dist + step);
  }

  return (
    <div className="scene-host" ref={host}>
      <div className="cam-tools" onPointerDown={(ev) => ev.stopPropagation()}>
        <button type="button" aria-label="拉近" onClick={() => zoomBy(-0.55)}>+</button>
        <button type="button" aria-label="拉远" onClick={() => zoomBy(0.55)}>−</button>
        <button type="button" className="cam-reset" aria-label="复位视角" onClick={() => window.__actsCam?.reset()}>复位</button>
      </div>
      <p className="cam-hint">拖拽旋转 · 滚轮缩放</p>
    </div>
  );
}
