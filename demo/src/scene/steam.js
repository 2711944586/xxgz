import * as THREE from "three";
import { steamSprite } from "./palette.js";

const COUNT = 2600;

export function buildSteam(tip) {
  const rand = (() => {
    let x = 987654321;
    return () => {
      x = (x * 1664525 + 1013904223) >>> 0;
      return x / 4294967296;
    };
  })();

  const geo = new THREE.BufferGeometry();
  const pos = new Float32Array(COUNT * 3);
  const seeds = new Float32Array(COUNT * 3);
  for (let i = 0; i < COUNT; i += 1) {
    const t = rand() ** 0.7;
    const theta = rand() * Math.PI * 2;
    const r = Math.sqrt(rand());
    pos[i * 3] = tip.x + 0.02 * t;
    pos[i * 3 + 1] = tip.y + Math.sin(theta) * r * 0.05;
    pos[i * 3 + 2] = tip.z + Math.cos(theta) * r * 0.05;
    seeds[i * 3] = t;
    seeds[i * 3 + 1] = rand() * 6.28;
    seeds[i * 3 + 2] = 0.55 + rand() * 1.1;
  }
  geo.setAttribute("position", new THREE.BufferAttribute(pos, 3));
  geo.setAttribute("seed", new THREE.BufferAttribute(seeds, 3));

  const sprite = steamSprite();
  const uniforms = {
    uTime: { value: 0 },
    uIntensity: { value: 0 },
    uColor: { value: new THREE.Color("#cfe3ea") },
    uSize: { value: 26 },
    uOpacity: { value: 0.5 },
    uMap: { value: sprite },
  };

  const mat = new THREE.ShaderMaterial({
    uniforms,
    transparent: true,
    depthWrite: false,
    blending: THREE.AdditiveBlending,
    vertexShader: /* glsl */ `
      attribute vec3 seed;
      uniform float uTime;
      uniform float uIntensity;
      uniform float uSize;
      varying float vFade;
      varying float vHot;
      void main() {
        float u = fract(seed.x * 0.85 + uTime * 0.16 + seed.y * 0.03);
        vec3 p = position;
        float spread = 0.05 + 0.62 * u;
        p.x += u * 2.2;
        p.y += u * 0.34 + 0.07 * sin(uTime * 1.7 + seed.y * 5.0) * u;
        p.z += spread * cos(seed.y + u * 5.0) * 0.9;
        p.y += spread * sin(seed.y * 1.7 + u * 4.0) * 0.55;
        p = clamp(p, vec3(-2.1, 0.2, -1.22), vec3(2.1, 2.44, 1.35));
        vec4 mv = modelViewMatrix * vec4(p, 1.0);
        float life = smoothstep(0.0, 0.18, u) * (1.0 - smoothstep(0.5, 1.0, u));
        vFade = life;
        vHot = 1.0 - u;
        gl_PointSize = (uSize * seed.z) * (0.8 + u * 1.1) / max(0.6, -mv.z);
        gl_PointSize *= uIntensity > 0.001 ? 1.0 : 0.0;
        gl_Position = projectionMatrix * mv;
      }
    `,
    fragmentShader: /* glsl */ `
      uniform sampler2D uMap;
      uniform vec3 uColor;
      uniform float uOpacity;
      varying float vFade;
      varying float vHot;
      void main() {
        vec4 tex = texture2D(uMap, gl_PointCoord);
        float a = tex.a * tex.a * vFade * uOpacity;
        if (a < 0.004) discard;
        vec3 col = mix(uColor, vec3(1.0, 0.94, 0.84), vHot * 0.45);
        gl_FragColor = vec4(col, a);
      }
    `,
  });

  const points = new THREE.Points(geo, mat);
  points.userData.part = 'steam.plume';
  points.frustumCulled = false;
  points.visible = false;

  return {
    points,
    uniforms,
    set(intensity, probe = false) {
      points.visible = intensity > 0.004;
      uniforms.uIntensity.value = intensity;
      uniforms.uOpacity.value = 0.16 + 0.62 * Math.min(1, intensity);
      uniforms.uSize.value = probe ? 34 : 26;
      uniforms.uColor.value.set(probe ? "#f2d79a" : "#cfe3ea");
    },
    tick(dt, intensity) {
      if (!points.visible) return;
      uniforms.uTime.value += dt * (0.8 + 0.9 * Math.min(1, intensity));
    },
  };
}

export function buildAirflow(ventPos) {
  const group = new THREE.Group();
  group.name = "airflow";
  const curves = [];
  for (let i = 0; i < 5; i += 1) {
    const y = 0.42 + i * 0.3;
    const zOff = (i % 3) * 0.3 - 0.3;
    const pts = [
      new THREE.Vector3(-0.3, y, -0.9),
      new THREE.Vector3(-1.4, y + 0.12, -0.4 + zOff * 0.2),
      new THREE.Vector3(-1.75, y + 0.05, 0.5),
      new THREE.Vector3(-0.9, y - 0.1, 1.1),
      new THREE.Vector3(0.7, y + 0.06, 1.08),
      new THREE.Vector3(1.5, y + 0.16, 0.65),
      new THREE.Vector3(1.72, y + 0.22, 0.1),
      new THREE.Vector3(ventPos.x, ventPos.y, ventPos.z),
    ];
    curves.push(new THREE.CatmullRomCurve3(pts));
  }
  const material = new THREE.MeshBasicMaterial({
    color: "#9ec9d4", transparent: true, opacity: 0.0, depthWrite: false,
    blending: THREE.AdditiveBlending,
  });
  const lines = curves.map((curve) => {
    const tube = new THREE.Mesh(new THREE.TubeGeometry(curve, 48, 0.006, 5, false), material);
    tube.frustumCulled = false;
    group.add(tube);
    return tube;
  });
  group.visible = false;
  return {
    group,
    set(level) {
      const v = Math.min(1, Math.max(0, level));
      group.visible = v > 0.3;
      material.opacity = v > 0.3 ? 0.03 + 0.09 * (v - 0.3) : 0;
    },
    tick(dt) {
      material.opacity += 0;
    },
    lines,
  };
}
