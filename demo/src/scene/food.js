import * as THREE from "three";
import { RoundedBoxGeometry } from "three/examples/jsm/geometries/RoundedBoxGeometry.js";
import { thermalColor } from "./palette.js";

const N = 16;
const WIDTH = 1.62;
const DEPTH = 1.18;

const LEAN = new THREE.Color("#a8785a");
const FAT = new THREE.Color("#cfae84");
const CRUST = new THREE.Color("#5f2f14");

function seeded(seed) {
  let x = seed >>> 0;
  return () => {
    x = (x * 1664525 + 1013904223) >>> 0;
    return x / 4294967296;
  };
}

export function buildFood() {
  const group = new THREE.Group();
  const rand = seeded(20241334);
  const slabs = [];
  const w = WIDTH / N;

  for (let i = 0; i < N; i += 1) {
    const slab = new THREE.Group();
    const jitter = 0.999 + rand() * 0.002;
    const thickness = w * 1.0;
    const bodyMat = new THREE.MeshPhysicalMaterial({
      color: LEAN.clone(), roughness: 0.6, metalness: 0.0,
      clearcoat: 0.22, clearcoatRoughness: 0.42,
    });
    const body = new THREE.Mesh(
      new RoundedBoxGeometry(thickness, 0.36 * jitter, DEPTH * jitter, 2, 0.004),
      bodyMat,
    );
    body.castShadow = true;
    body.receiveShadow = true;
    slab.add(body);

    const capMat = new THREE.MeshPhysicalMaterial({
      color: LEAN.clone(), roughness: 0.4, metalness: 0.0,
      clearcoat: 0.6, clearcoatRoughness: 0.2,
    });
    const cap = new THREE.Mesh(
      new RoundedBoxGeometry(thickness, 0.026, DEPTH * 0.995, 2, 0.003),
      capMat,
    );
    cap.position.y = 0.18 * jitter + 0.005;
    cap.receiveShadow = true;
    slab.add(cap);

    let grainMat = null;
    if (i === 0 || i === N - 1) {
      grainMat = new THREE.MeshStandardMaterial({ color: LEAN.clone(), roughness: 0.86 });
      const face = new THREE.Mesh(new THREE.PlaneGeometry(DEPTH * 0.95, 0.4 * jitter), grainMat);
      face.rotation.y = i === 0 ? -Math.PI / 2 : Math.PI / 2;
      face.position.x = (i === 0 ? -1 : 1) * thickness * 0.508;
      slab.add(face);
    }

    slab.traverse((m) => { if (m.isMesh) m.userData.part = 'food'; });
    slab.position.set(-WIDTH / 2 + (i + 0.5) * w, 0, 0);
    group.add(slab);
    slabs.push({ bodyMat, capMat, grainMat });
  }

  const coldMark = new THREE.Mesh(
    new THREE.SphereGeometry(0.032, 16, 12),
    new THREE.MeshBasicMaterial({ color: "#7eb8c9" }),
  );
  coldMark.visible = false;
  group.add(coldMark);

  const needle = new THREE.Mesh(
    new THREE.CylinderGeometry(0.011, 0.006, 0.5, 10),
    new THREE.MeshStandardMaterial({ color: "#d6e0e6", metalness: 0.92, roughness: 0.16 }),
  );
  needle.rotation.z = Math.PI / 2;
  needle.visible = false;
  group.add(needle);

  group.userData.slabs = slabs;
  group.userData.coldMark = coldMark;
  group.userData.needle = needle;
  return group;
}

const tmp = new THREE.Color();
const base = new THREE.Color();

export function updateFood(food, frame, lengthM) {
  const { slabs, coldMark, needle } = food.userData;
  if (!slabs.length) return;
  const nodes = frame?.nodes;
  const hot = frame ? Math.max(frame.tSurf, frame.tCore) : 8;
  const span = Math.max(hot - (frame?.tCore ?? 8), 1);
  const brown = Math.min(1, Math.max(0,
    (frame?.alphaB ?? 0) * 1.5 + Math.max((frame?.tSurf ?? 8) - 116, 0) / 130));

  let coldest = 0;
  for (let i = 0; i < N; i += 1) {
    const value = nodes ? nodes[i] : hot - span * (i / (N - 1)) ** 1.15;
    if (nodes && nodes[i] < nodes[coldest]) coldest = i;
    const color = thermalColor(value, 8, 175, tmp);
    const u = i / (N - 1);
    const exposure = Math.max(0.15, 1 - Math.abs(u - 0.5) * 1.3);
    const { bodyMat, capMat, grainMat } = slabs[i];
    base.copy(LEAN).lerp(FAT, i === 6 ? 0.55 : 0);

    bodyMat.color.copy(base).lerp(color, 0.82 * exposure);
    bodyMat.color.lerp(CRUST, brown * (1 - u * 0.6) * 0.36);

    capMat.color.copy(base).lerp(color, 0.46);
    capMat.color.lerp(CRUST, brown * (1 - u * 0.5) * 0.86);

    if (grainMat) {
      grainMat.color.copy(base).lerp(color, 0.72 * exposure);
    }
  }

  food.scale.x = lengthM / 0.03;

  if (nodes) {
    const z = -0.45 + (coldest / (N - 1)) * 0.9;
    coldMark.position.set(0, 0.9 + 0.0, 0.07);
    coldMark.position.x = (coldest / (N - 1) - 0.5) * 1.62;
    coldMark.visible = true;
    needle.position.set(coldMark.position.x, 0.9, DEPTH * 0.5 + 0.16);
    needle.visible = false;
  }
}
