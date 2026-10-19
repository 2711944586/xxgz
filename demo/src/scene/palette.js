import * as THREE from "three";

/* Thermal palette used by every field reading on the page: the food slices,
   the legend and the two canvases. Stops are a low-light ironbow so a 60 K
   gradient still separates at the dark end. */
const STOPS = [
  [0.0, "#101c30"],
  [0.16, "#233a6e"],
  [0.32, "#4a3f92"],
  [0.48, "#8d3a80"],
  [0.62, "#c1462f"],
  [0.76, "#e37c2e"],
  [0.89, "#f4bc41"],
  [1.0, "#fff3d2"],
];

const STOPS_RGB = STOPS.map(([pos, hex]) => {
  const c = new THREE.Color(hex);
  return [pos, c.r, c.g, c.b];
});

export function thermalColor(value, min = 8, max = 175, target = new THREE.Color()) {
  const x = Math.min(1, Math.max(0, (value - min) / (max - min)));
  let i = 0;
  while (i < STOPS_RGB.length - 2 && x > STOPS_RGB[i + 1][0]) i += 1;
  const [p0, r0, g0, b0] = STOPS_RGB[i];
  const [p1, r1, g1, b1] = STOPS_RGB[i + 1];
  const t = p1 === p0 ? 0 : (x - p0) / (p1 - p0);
  return target.setRGB(r0 + (r1 - r0) * t, g0 + (g1 - g0) * t, b0 + (b1 - b0) * t);
}

export function thermalCss(value, min = 8, max = 175) {
  const c = thermalColor(value, min, max);
  return `rgb(${Math.round(c.r * 255)}, ${Math.round(c.g * 255)}, ${Math.round(c.b * 255)})`;
}

export function cssStops(count = 8) {
  return Array.from({ length: count }, (_, i) => {
    const t = i / (count - 1);
    return `${thermalCss(8 + t * 167)} ${(t * 100).toFixed(1)}%`;
  }).join(", ");
}

/* ---------------------------------------------------------------- textures */

function canvas2d(w, h) {
  const canvas = document.createElement("canvas");
  canvas.width = w;
  canvas.height = h;
  return [canvas, canvas.getContext("2d")];
}

function rng(seed) {
  let x = seed >>> 0;
  return () => {
    x = (x * 1664525 + 1013904223) >>> 0;
    return x / 4294967296;
  };
}

function toTexture(canvas, repeat = 1) {
  const tex = new THREE.CanvasTexture(canvas);
  tex.wrapS = THREE.RepeatWrapping;
  tex.wrapT = THREE.RepeatWrapping;
  tex.repeat.set(repeat, repeat);
  tex.anisotropy = 8;
  return tex;
}

/* Brushed metal: a height field of long horizontal streaks becomes a normal
   map and a correlated roughness map, so highlights stretch along the grain
   instead of sitting on it as a round blob. */
export function brushedMaps({ size = 512, streak = 0.24, grain = 0.05, repeat = 6 } = {}) {
  const rand = rng(20241334);
  const height = new Float32Array(size * size);
  for (let y = 0; y < size; y += 1) {
    let row = 0.5;
    for (let x = 0; x < size; x += 1) {
      row += (rand() - 0.5) * streak * 0.3;
      row = Math.min(1, Math.max(0, row * 0.995 + 0.0025));
      height[y * size + x] = row + (rand() - 0.5) * grain;
    }
  }
  const nrm = new Uint8ClampedArray(size * size * 4);
  const rough = new Uint8ClampedArray(size * size * 4);
  for (let y = 0; y < size; y += 1) {
    for (let x = 0; x < size; x += 1) {
      const i = y * size + x;
      const xl = height[y * size + ((x - 1 + size) % size)];
      const xr = height[y * size + ((x + 1) % size)];
      const yt = height[((y - 1 + size) % size) * size + x];
      const yb = height[((y + 1) % size) * size + x];
      const dx = (xr - xl) * 2.4;
      const dy = (yb - yt) * 2.4;
      const len = Math.hypot(dx, dy, 1);
      nrm[i * 4] = ((dx / len) * 0.5 + 0.5) * 255;
      nrm[i * 4 + 1] = ((dy / len) * 0.5 + 0.5) * 255;
      nrm[i * 4 + 2] = ((1 / len) * 0.5 + 0.5) * 255;
      nrm[i * 4 + 3] = 255;
      const r = 168 + height[i] * 52;
      rough[i * 4] = r;
      rough[i * 4 + 1] = r;
      rough[i * 4 + 2] = r;
      rough[i * 4 + 3] = 255;
    }
  }
  const build = (arr) => {
    const [canvas, ctx] = canvas2d(size, size);
    ctx.putImageData(new ImageData(arr, size, size), 0, 0);
    return toTexture(canvas, repeat);
  };
  return { normalMap: build(nrm), roughnessMap: build(rough) };
}

/* Embossed liner: the dimpled stainless pattern inside real ovens. */
export function dimpleMaps({ size = 512, repeat = 16 } = {}) {
  const [hCanvas, hCtx] = canvas2d(size, size);
  const [rCanvas, rCtx] = canvas2d(size, size);
  hCtx.fillStyle = "#8d8d8d";
  hCtx.fillRect(0, 0, size, size);
  rCtx.fillStyle = "#c0c0c0";
  rCtx.fillRect(0, 0, size, size);
  const step = size / 8;
  for (let row = 0; row < 8; row += 1) {
    for (let col = 0; col < 8; col += 1) {
      const x = col * step + step / 2 + (row % 2 ? step / 2 : 0);
      const y = row * step + step / 2;
      const g = hCtx.createRadialGradient(x, y, 1, x, y, step * 0.42);
      g.addColorStop(0, "#808080");
      g.addColorStop(0.55, "#8a8a8a");
      g.addColorStop(1, "#8e8e8e");
      hCtx.fillStyle = g;
      hCtx.beginPath();
      hCtx.arc(x % size, y, step * 0.36, 0, Math.PI * 2);
      hCtx.fill();
      const rg = rCtx.createRadialGradient(x, y, 1, x, y, step * 0.4);
      rg.addColorStop(0, "#d0d0d0");
      rg.addColorStop(1, "#b0b0b0");
      rCtx.fillStyle = rg;
      rCtx.beginPath();
      rCtx.arc(x % size, y, step * 0.36, 0, Math.PI * 2);
      rCtx.fill();
    }
  }
  return {
    normalMap: toTexture(hCanvas, repeat),
    roughnessMap: toTexture(rCanvas, repeat),
  };
}

/* Cast-iron / enamel speckle for the cooktop-style fascia. */
export function enamelMaps({ size = 256, repeat = 2 } = {}) {
  const rand = rng(778821);
  const [canvas, ctx] = canvas2d(size, size);
  const img = ctx.createImageData(size, size);
  for (let i = 0; i < size * size; i += 1) {
    const v = 120 + rand() * 22;
    img.data[i * 4] = v;
    img.data[i * 4 + 1] = v;
    img.data[i * 4 + 2] = v;
    img.data[i * 4 + 3] = 255;
  }
  ctx.putImageData(img, 0, 0);
  return { roughnessMap: toTexture(canvas, repeat) };
}

export function steamSprite() {
  const [canvas, ctx] = canvas2d(128, 128);
  const g = ctx.createRadialGradient(64, 64, 4, 64, 64, 62);
  g.addColorStop(0, "rgba(255,255,255,0.9)");
  g.addColorStop(0.28, "rgba(226,240,246,0.5)");
  g.addColorStop(0.62, "rgba(210,230,240,0.16)");
  g.addColorStop(1, "rgba(210,230,240,0)");
  ctx.fillStyle = g;
  ctx.fillRect(0, 0, 128, 128);
  const tex = new THREE.CanvasTexture(canvas);
  tex.colorSpace = THREE.SRGBColorSpace;
  return tex;
}

export function radialShadow() {
  const [canvas, ctx] = canvas2d(256, 256);
  const g = ctx.createRadialGradient(128, 128, 8, 128, 128, 126);
  g.addColorStop(0, "rgba(0,0,0,0.62)");
  g.addColorStop(0.45, "rgba(0,0,0,0.26)");
  g.addColorStop(1, "rgba(0,0,0,0)");
  ctx.fillStyle = g;
  ctx.fillRect(0, 0, 256, 256);
  return new THREE.CanvasTexture(canvas);
}

/* ---------------------------------------------------------------- materials */

export function steel(color, { metalness = 0.85, roughness = 0.3, maps = null } = {}) {
  const mat = new THREE.MeshPhysicalMaterial({
    color,
    metalness,
    roughness,
    envMapIntensity: 1.15,
  });
  if (maps) {
    mat.normalMap = maps.normalMap;
    mat.normalScale = new THREE.Vector2(0.12, 0.12);
    mat.roughnessMap = maps.roughnessMap;
  }
  return mat;
}

export function enamel(color) {
  return new THREE.MeshPhysicalMaterial({
    color,
    metalness: 0.32,
    roughness: 0.52,
    clearcoat: 0.55,
    clearcoatRoughness: 0.34,
    envMapIntensity: 0.9,
  });
}

export function rubber(color = "#171b1e") {
  return new THREE.MeshStandardMaterial({ color, metalness: 0.06, roughness: 0.9 });
}

export function glass() {
  return new THREE.MeshPhysicalMaterial({
    color: "#aebbc2",
    metalness: 0.0,
    roughness: 0.04,
    transmission: 0.85,
    thickness: 0.06,
    ior: 1.52,
    transparent: true,
    opacity: 0.3,
    envMapIntensity: 2.2,
    clearcoat: 1.0,
    clearcoatRoughness: 0.02,
    reflectivity: 0.85,
    side: THREE.DoubleSide,
  });
}

export function chrome() {
  return new THREE.MeshPhysicalMaterial({
    color: "#e4ebef",
    metalness: 1.0,
    roughness: 0.1,
    envMapIntensity: 1.5,
  });
}

export function brass() {
  return new THREE.MeshPhysicalMaterial({
    color: "#c9a86d",
    metalness: 0.92,
    roughness: 0.28,
    envMapIntensity: 1.25,
  });
}

export function emissive(color, intensity = 1) {
  return new THREE.MeshStandardMaterial({
    color,
    emissive: color,
    emissiveIntensity: intensity,
    roughness: 0.4,
    metalness: 0.1,
  });
}
