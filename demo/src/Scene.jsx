import { useEffect, useRef } from "react";
import * as THREE from "three";

const T_MIN = 5;
const T_MAX = 170;

function colorAt(value) {
  const x = Math.min(1, Math.max(0, (value - T_MIN) / (T_MAX - T_MIN)));
  return new THREE.Color().setHSL(0.08 - 0.07 * x, 0.55, 0.78 - 0.38 * x);
}

export default function Scene({ frame, slice, length = 0.03 }) {
  const host = useRef(null);
  const state = useRef(null);

  useEffect(() => {
    const el = host.current;
    const renderer = new THREE.WebGLRenderer({ antialias: true });
    renderer.setPixelRatio(Math.min(window.devicePixelRatio || 1, 2));
    renderer.setSize(el.clientWidth || 640, 460);
    el.appendChild(renderer.domElement);
    const scene = new THREE.Scene();
    scene.background = new THREE.Color("#d9d3c7");
    const width = el.clientWidth || 640;
    const camera = new THREE.PerspectiveCamera(32, width / 460, 0.1, 40);
    camera.position.set(2.6, 1.55, 3.4);
    camera.lookAt(0, 0.42, 0);
    const ambient = new THREE.AmbientLight(0xffffff, 0.72);
    const key = new THREE.DirectionalLight(0xfff6ea, 0.9);
    key.position.set(2.2, 3.4, 1.6);
    scene.add(ambient, key);

    const food = new THREE.Group();
    const cells = [];
    for (let i = 0; i < 16; i++) {
      const mesh = new THREE.Mesh(
        new THREE.BoxGeometry(0.09, 0.62, 0.92),
        new THREE.MeshStandardMaterial({ color: "#f4efe6", roughness: 0.78 })
      );
      mesh.position.set(-0.72 + i * 0.096, 0.42, 0);
      food.add(mesh);
      cells.push(mesh);
    }
    scene.add(food);
    const cut = new THREE.Mesh(
      new THREE.PlaneGeometry(0.04, 0.66),
      new THREE.MeshStandardMaterial({ color: "#2f6f7e", side: THREE.DoubleSide, roughness: 0.4 })
    );
    scene.add(cut);
    const steam = new THREE.Mesh(
      new THREE.SphereGeometry(0.07, 18, 12),
      new THREE.MeshStandardMaterial({ color: "#d9e4ea", emissive: "#7eb8c9", emissiveIntensity: 0.05, roughness: 0.45 })
    );
    steam.position.set(-0.55, 0.98, 0.15);
    scene.add(steam);
    const fan = new THREE.Mesh(
      new THREE.BoxGeometry(0.22, 0.035, 0.22),
      new THREE.MeshStandardMaterial({ color: "#efe6d4", emissive: "#e07a3d", emissiveIntensity: 0.05, roughness: 0.6 })
    );
    fan.position.set(0.55, 0.98, 0.15);
    scene.add(fan);
    const heater = new THREE.Mesh(
      new THREE.BoxGeometry(1.15, 0.05, 0.08),
      new THREE.MeshStandardMaterial({ color: "#c46b3a", emissive: "#c46b3a", emissiveIntensity: 0.2 })
    );
    heater.position.set(0, 1.05, -0.55);
    scene.add(heater);
    const target = new THREE.Vector3(0, 0.42, 0);
    let yaw = 0.72;
    let pitch = 0.42;
    let dist = 4.55;
    let dragging = false;
    let lastX = 0;
    let lastY = 0;
    const place = () => {
      camera.position.set(
        target.x + dist * Math.cos(pitch) * Math.sin(yaw),
        target.y + dist * Math.sin(pitch),
        target.z + dist * Math.cos(pitch) * Math.cos(yaw),
      );
      camera.lookAt(target);
    };
    place();
    const onDown = (ev) => {
      dragging = true;
      lastX = ev.clientX;
      lastY = ev.clientY;
    };
    const onMove = (ev) => {
      if (!dragging) return;
      yaw -= (ev.clientX - lastX) * 0.008;
      pitch = Math.min(1.2, Math.max(-0.2, pitch + (ev.clientY - lastY) * 0.008));
      lastX = ev.clientX;
      lastY = ev.clientY;
      place();
    };
    const onUp = () => { dragging = false; };
    const onWheel = (ev) => {
      dist = Math.min(8, Math.max(2.2, dist + ev.deltaY * 0.004));
      place();
    };
    el.addEventListener("pointerdown", onDown);
    window.addEventListener("pointermove", onMove);
    window.addEventListener("pointerup", onUp);
    el.addEventListener("wheel", onWheel, { passive: true });
    state.current = { renderer, scene, camera, cells, cut, heater, steam, fan, food, el, place };
    let alive = true;
    const tick = () => {
      if (!alive) return;
      renderer.render(scene, camera);
      requestAnimationFrame(tick);
    };
    tick();
    return () => {
      alive = false;
      renderer.dispose();
      el.removeEventListener("pointerdown", onDown);
      window.removeEventListener("pointermove", onMove);
      window.removeEventListener("pointerup", onUp);
      el.removeEventListener("wheel", onWheel);
      if (renderer.domElement.parentNode === el) el.removeChild(renderer.domElement);
    };
  }, []);

  useEffect(() => {
    const s = state.current;
    if (!s || !frame?.field) return;
    frame.field.forEach((value, i) => {
      s.cells[i].material.color.copy(colorAt(value));
    });
    const index = Math.min(15, Math.max(0, Math.round(slice * 15)));
    const cell = frame.field[index];
    s.cut.position.set(-0.72 + index * 0.096, 0.42, 0.52);
    s.cut.material.color.copy(colorAt(cell));
    s.food.scale.set(length / 0.03, 1, 1);
    s.heater.material.emissiveIntensity = 0.08 + 0.9 * frame.heat;
    s.steam.material.emissiveIntensity = 0.04 + 0.85 * frame.steam;
    s.fan.material.emissiveIntensity = 0.04 + 0.7 * (frame.fan / 1.3);
    const probing = frame.time >= 150 && frame.time < 190;
    s.cells[0].material.emissive.set(probing ? "#7eb8c9" : "#000000");
    s.cells[0].material.emissiveIntensity = probing ? 0.45 : 0;
    s.renderer.render(s.scene, s.camera);
  }, [frame, slice, length]);

  return <div ref={host} style={{ minHeight: 460 }} />;
}
