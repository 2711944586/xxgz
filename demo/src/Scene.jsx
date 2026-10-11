import { useEffect, useRef } from "react";
import * as THREE from "three";

const T_MIN = 5;
const T_MAX = 170;

function colorAt(value) {
  const x = Math.min(1, Math.max(0, (value - T_MIN) / (T_MAX - T_MIN)));
  return new THREE.Color().setHSL(0.08 - 0.07 * x, 0.55, 0.78 - 0.38 * x);
}

export default function Scene({ frame, slice }) {
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
    const heater = new THREE.Mesh(
      new THREE.BoxGeometry(1.15, 0.05, 0.08),
      new THREE.MeshStandardMaterial({ color: "#c46b3a", emissive: "#c46b3a", emissiveIntensity: 0.2 })
    );
    heater.position.set(0, 1.05, -0.55);
    scene.add(heater);
    state.current = { renderer, scene, camera, cells, cut, heater, el };
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
    s.heater.material.emissiveIntensity = 0.08 + 0.9 * frame.heat;
    s.renderer.render(s.scene, s.camera);
  }, [frame, slice]);

  return <div ref={host} style={{ minHeight: 460 }} />;
}
