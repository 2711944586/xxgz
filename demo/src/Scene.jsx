import { useEffect, useRef } from "react";
import * as THREE from "three";
import { OrbitControls } from "three/examples/jsm/controls/OrbitControls.js";
import { EffectComposer } from "three/examples/jsm/postprocessing/EffectComposer.js";
import { RenderPass } from "three/examples/jsm/postprocessing/RenderPass.js";
import { GTAOPass } from "three/examples/jsm/postprocessing/GTAOPass.js";
import { UnrealBloomPass } from "three/examples/jsm/postprocessing/UnrealBloomPass.js";
import { OutputPass } from "three/examples/jsm/postprocessing/OutputPass.js";
import { buildCavity } from "./scene/cavity.js";
import { buildFood, updateFood } from "./scene/food.js";
import { buildSteam, buildAirflow } from "./scene/steam.js";
import { ANNOTATIONS, anchorVector, projectionOf } from "./scene/annotations.js";
import { radialShadow } from "./scene/palette.js";
import { studioEnvironment, floorTexture } from "./scene/environment.js";

const CAM = {
  home: { yaw: 0.6, pitch: 0.3, dist: 8.6, target: [0, 1.28, 0.1] },
  front: { yaw: 0.02, pitch: 0.06, dist: 7.9, target: [0, 1.3, 0.2] },
  section: { yaw: 0.52, pitch: 0.22, dist: 7.4, target: [0, 1.25, -0.05] },
  food: { yaw: 0.92, pitch: 0.38, dist: 3.9, target: [0, 0.86, 0.1] },
};

export const VIEW_PRESETS = [
  { id: "home", label: "整机" },
  { id: "front", label: "正面" },
  { id: "section", label: "剖面" },
  { id: "food", label: "内部" },
];

export default function Scene({
  frame,
  lengthM = 0.03,
  doorOpen = true,
  view = "home",
  section = false,
  explode = 0,
  annotations = false,
  showSteam = true,
  showAirflow = true,
  cavityLightOn = true,
  onPickPart,
}) {
  const host = useRef(null);
  const overlay = useRef(null);
  const state = useRef(null);
  const pickRef = useRef(onPickPart);
  pickRef.current = onPickPart;
  const live = useRef({});
  live.current = { frame, lengthM, doorOpen, view, section, explode, annotations, showSteam, showAirflow, cavityLightOn };

  useEffect(() => {
    const el = host.current;
    const renderer = new THREE.WebGLRenderer({ antialias: true, powerPreference: "high-performance" });
    renderer.setPixelRatio(Math.min(window.devicePixelRatio || 1, 1.8));
    const w0 = el.clientWidth || 900;
    const h0 = el.clientHeight || 620;
    renderer.setSize(w0, h0);
    renderer.toneMapping = THREE.ACESFilmicToneMapping;
    renderer.toneMappingExposure = 1.22;
    renderer.outputColorSpace = THREE.SRGBColorSpace;
    renderer.shadowMap.enabled = true;
    renderer.shadowMap.type = THREE.PCFSoftShadowMap;
    el.appendChild(renderer.domElement);

    const scene = new THREE.Scene();
    scene.background = new THREE.Color("#0e1419");
    scene.fog = new THREE.FogExp2("#0e1419", 0.022);
    scene.environment = studioEnvironment(renderer);

    const camera = new THREE.PerspectiveCamera(32, w0 / h0, 0.1, 60);
    const controls = new OrbitControls(camera, renderer.domElement);
    controls.enableDamping = true;
    controls.dampingFactor = 0.08;
    controls.minDistance = 2.4;
    controls.maxDistance = 13;
    controls.maxPolarAngle = Math.PI * 0.53;
    controls.minPolarAngle = Math.PI * 0.05;
    controls.enablePan = false;
    controls.rotateSpeed = 0.7;
    controls.zoomSpeed = 0.85;
    controls.target.set(...CAM.home.target);
    controls.addEventListener("start", () => { state.current.camGoal = null; });

    const composer = new EffectComposer(renderer);
    composer.setPixelRatio(Math.min(window.devicePixelRatio || 1, 1.8));
    composer.setSize(w0, h0);
    const gtao = new GTAOPass(scene, camera, w0, h0);
    gtao.updateGtaoMaterial({
      radius: 0.2, distanceExponent: 1.2, thickness: 0.9, scale: 1.0,
      samples: 16, distanceFallOff: 1.0, screenSpaceRadius: false,
    });
    gtao.blendIntensity = 0.95;
    const bloom = new UnrealBloomPass(new THREE.Vector2(w0, h0), 0.3, 0.68, 0.85);
    composer.addPass(new RenderPass(scene, camera));
    composer.addPass(gtao);
    composer.addPass(bloom);
    composer.addPass(new OutputPass());

    const hemi = new THREE.HemisphereLight(0xe8f0f5, 0x2a343b, 0.72);
    const key = new THREE.DirectionalLight(0xfff4e6, 1.55);
    key.position.set(4.6, 6.8, 5.2);
    key.castShadow = true;
    key.shadow.mapSize.set(2048, 2048);
    key.shadow.bias = -0.00035;
    key.shadow.normalBias = 0.022;
    key.shadow.camera.near = 1;
    key.shadow.camera.far = 22;
    key.shadow.camera.left = -4.8;
    key.shadow.camera.right = 4.8;
    key.shadow.camera.top = 5.2;
    key.shadow.camera.bottom = -3.4;
    const fill = new THREE.DirectionalLight(0xa9c9da, 0.95);
    fill.position.set(-5.4, 2.6, 3.8);
    const rim = new THREE.DirectionalLight(0x86bcd4, 0.72);
    rim.position.set(-1.8, 2.0, -5.4);
    const cavityLight = new THREE.PointLight(0xffe8cc, 0.85, 4.6, 1.9);
    cavityLight.position.set(0, 1.55, 0.45);
    const cavityLight2 = new THREE.PointLight(0xfff4e2, 0.4, 3.0, 2.0);
    cavityLight2.position.set(-1.2, 2.1, 0.65);
    const cavityLight3 = new THREE.PointLight(0xfff0d8, 0.35, 2.9, 2.0);
    cavityLight3.position.set(1.2, 2.05, 0.6);
    const heaterGlow = new THREE.PointLight(0xff6a24, 0.0, 3.4, 1.9);
    heaterGlow.position.set(0, 2.14, 0.2);
    const nozzleLight = new THREE.PointLight(0xbfe4f2, 0.0, 2.6, 1.9);
    nozzleLight.position.set(-1.5, 1.6, 0.2);
    const bounce = new THREE.DirectionalLight(0x9fb4c0, 0.42);
    bounce.position.set(0.6, -2.4, 5.4);
    scene.add(hemi, key, fill, rim, bounce, cavityLight, cavityLight2, cavityLight3, heaterGlow, nozzleLight);

    const floor = new THREE.Mesh(
      new THREE.CircleGeometry(11, 64),
      new THREE.MeshStandardMaterial({ map: floorTexture(), roughness: 0.72, metalness: 0.2 }),
    );
    floor.rotation.x = -Math.PI / 2;
    floor.position.y = -0.3;
    floor.receiveShadow = true;
    scene.add(floor);

    const contact = new THREE.Mesh(
      new THREE.PlaneGeometry(7.8, 5.4),
      new THREE.MeshBasicMaterial({ map: radialShadow(), transparent: true, depthWrite: false }),
    );
    contact.rotation.x = -Math.PI / 2;
    contact.position.y = -0.295;
    scene.add(contact);

    const cavity = buildCavity();
    scene.add(cavity.group);
    const food = buildFood();
    food.position.set(0, 0.9, 0.07);
    scene.add(food);
    const steam = buildSteam(cavity.parts.steamLine.userData.tip.position);
    scene.add(steam.points);
    const airflow = buildAirflow(new THREE.Vector3(1.62, 2.16, -1.2));
    scene.add(airflow.group);

    const raycaster = new THREE.Raycaster();
    const pointer = new THREE.Vector2();
    let downAt = null;
    const onDown = (ev) => { downAt = { x: ev.clientX, y: ev.clientY }; };
    const onUp = (ev) => {
      if (!downAt) return;
      const moved = Math.hypot(ev.clientX - downAt.x, ev.clientY - downAt.y);
      downAt = null;
      if (moved > 5) return;
      const rect = el.getBoundingClientRect();
      pointer.x = ((ev.clientX - rect.left) / rect.width) * 2 - 1;
      pointer.y = -((ev.clientY - rect.top) / rect.height) * 2 + 1;
      raycaster.setFromCamera(pointer, camera);
      const hits = raycaster.intersectObjects([cavity.group, food, steam.points], true);
      const hit = hits.find((h) => h.object.userData.part);
      pickRef.current?.(hit ? hit.object.userData.part : null);
    };
    el.addEventListener("pointerdown", onDown);
    el.addEventListener("pointerup", onUp);

    const goalFor = (name) => {
      const p = CAM[name] || CAM.home;
      const target = new THREE.Vector3(...p.target);
      const pos = new THREE.Vector3(
        target.x + p.dist * Math.cos(p.pitch) * Math.sin(p.yaw),
        target.y + p.dist * Math.sin(p.pitch),
        target.z + p.dist * Math.cos(p.pitch) * Math.cos(p.yaw),
      );
      return { pos, target };
    };
    const setPreset = (name, instant = false) => {
      const goal = goalFor(name);
      if (instant) {
        camera.position.copy(goal.pos);
        controls.target.copy(goal.target);
        controls.update();
      } else {
        state.current.camGoal = goal;
      }
    };

    if (typeof window !== "undefined") {
      window.__scenePick = (cx, cy) => {
        const rect = el.getBoundingClientRect();
        const pt = new THREE.Vector2(((cx - rect.left) / rect.width) * 2 - 1, -((cy - rect.top) / rect.height) * 2 + 1);
        raycaster.setFromCamera(pt, camera);
        const hits = raycaster.intersectObjects(scene.children, true);
        return hits.slice(0, 4).map((h) => ({ part: h.object.userData.part || h.object.name || h.object.type, d: +h.distance.toFixed(2) }));
      };
    }
    state.current = {
      renderer, composer, scene, camera, controls, gtao, bloom, cavity, food,
      steam, airflow, hemi, key, fill, cavityLight, cavityLight2, cavityLight3, heaterGlow, nozzleLight,
      camGoal: null, setPreset, picked: null, sectionAmt: 0, explodeAmt: 0,
      lastT: performance.now(),
    };
    setPreset("home", true);

    const onResize = () => {
      const w = el.clientWidth || 900;
      const h = el.clientHeight || 620;
      if (w < 4 || h < 4) return;
      camera.aspect = w / h;
      camera.updateProjectionMatrix();
      renderer.setSize(w, h);
      composer.setSize(w, h);
      gtao.setSize?.(w, h);
      bloom.setSize?.(w, h);
    };
    const ro = new ResizeObserver(onResize);
    ro.observe(el);
    onResize();

    let alive = true;
    const tick = () => {
      if (!alive) return;
      const s = state.current;
      const now = performance.now();
      const dt = Math.min(0.05, (now - s.lastT) / 1000);
      s.lastT = now;
      const L = live.current;
      const f = L.frame;

      if (s.camGoal) {
        const k = 1 - Math.exp(-7.5 * dt);
        camera.position.lerp(s.camGoal.pos, k);
        controls.target.lerp(s.camGoal.target, k);
        if (camera.position.distanceTo(s.camGoal.pos) < 0.012) s.camGoal = null;
      }

      const door = s.cavity.parts.door;
      door.rotation.y += ((L.doorOpen ? -1.42 : 0) - door.rotation.y) * (1 - Math.exp(-8.5 * dt));

      s.sectionAmt += ((L.section ? 1 : 0) - s.sectionAmt) * (1 - Math.exp(-6 * dt));
      const sec = s.sectionAmt;
      door.visible = sec < 0.55;
      s.cavity.sectionPanels.forEach((m) => {
        m.visible = sec < 0.6;
      });
      s.cavity.topPanels.forEach((m) => {
        m.visible = sec < 0.9;
      });

      s.explodeAmt += ((L.explode ?? 0) - s.explodeAmt) * (1 - Math.exp(-6 * dt));
      const ex = s.explodeAmt;
      s.cavity.explodeTargets.forEach((m) => {
        if (!m.userData.basePos || !m.userData.explode) return;
        m.position.copy(m.userData.basePos).addScaledVector(m.userData.explode, ex);
      });

      const heat = f?.heat ?? 0;
      const steamCmd = f?.steam ?? 0;
      const fanCmd = f?.fan ?? 0.4;
      const exhaust = f?.exhaust ?? 0.4;
      s.cavity.materials.coil.emissiveIntensity = 0.16 + 2.2 * heat;
      s.heaterGlow.intensity = 0.1 + 1.5 * heat;
      const lampScale = L.cavityLightOn === false ? 0.06 : 1;
      s.cavityLight.intensity = (0.78 + 0.55 * heat) * lampScale;
      s.cavityLight2.intensity = 0.4 * lampScale;
      s.cavityLight3.intensity = 0.35 * lampScale;
      s.key.intensity = 1.42 + 0.22 * heat;
      s.cavity.parts.fan.userData.blades.rotation.z += dt * (0.35 + 5.0 * Math.min(1, fanCmd / 1.3));

      s.cavity.parts.vent.userData.louvres.forEach((m) => {
        m.rotation.x = m.userData.baseRotX + 0.5 * exhaust;
      });

      s.nozzleLight.intensity = 0.18 + 1.5 * steamCmd;
      if (L.showSteam) steam.set(Math.max(steamCmd, f?.mode === 1 ? 0.85 : 0), f?.mode === 1);
      else steam.set(0);
      steam.tick(dt, steamCmd);
      airflow.set(L.showAirflow && !L.section ? Math.min(1, Math.max(0, (fanCmd - 0.45) / 0.85)) : 0);

      const water = s.cavity.parts.steamLine.userData.water;
      const level = Math.min(1, Math.max(0.05, f?.water ?? 0.72));
      water.scale.y = 0.35 + 0.9 * level;
      water.position.y = 0.27 - 0.075 * (1 - level);

      const knobs = door.userData.knobs;
      knobs[0].rotation.z = -heat * 2.5;
      knobs[1].rotation.z = -steamCmd * 2.5;
      knobs[2].rotation.z = -(fanCmd / 1.3) * 2.5;

      updateFood(s.food, f, L.lengthM);

      const marks = s.cavity.parts.sensors.userData.marks;
      const cold = f?.nodes ? f.nodes.reduce((a, v, i) => (v < f.nodes[a] ? i : a), 0) : 0;
      const zPos = -0.46 + (cold / 15) * 0.92;
      marks.coldSpot.position.set(zPos, 0.9 + 0.02, 0.07);
      marks.estimate.position.set(zPos, 0.96, 0.07);
      marks.coldSpot.visible = L.annotations || L.section;
      marks.estimate.visible = L.annotations || L.section;

      controls.update();
      s.composer.render();

      const layer = overlay.current;
      if (layer) {
        const rect = el.getBoundingClientRect();
        const on = L.annotations && rect.width > 0;
        layer.style.opacity = on ? "1" : "0";
        if (on) {
          const list = ANNOTATIONS.map((a) => ({
            a,
            p: projectionOf(camera, anchorVector(a.anchor), rect.width, rect.height),
          })).filter(({ p }) => !p.behind);
          list.sort((u, v) => u.p.y - v.p.y);
          const lanes = { left: [], right: [] };
          list.forEach(({ a, p }) => {
            const side = p.x < rect.width * 0.48 ? "left" : "right";
            const lane = lanes[side];
            let y = p.y;
            if (lane.length && y - lane[lane.length - 1] < 46) y = lane[lane.length - 1] + 46;
            lane.push(y);
            const node = layer.querySelector(`[data-ann="${a.id}"]`);
            if (!node) return;
            const x = side === "left" ? Math.max(10, p.x - 12) : Math.min(rect.width - 10, p.x + 12);
            node.style.transform = `translate(${x.toFixed(1)}px, ${y.toFixed(1)}px)`;
            node.style.visibility = "visible";
            node.dataset.side = side;
            const lead = node.querySelector(".ann-lead");
            if (lead) {
              const dx = p.x - x;
              const dy = p.y - y;
              lead.style.width = `${Math.hypot(dx, dy).toFixed(1)}px`;
              lead.style.transform = `rotate(${Math.atan2(dy, dx)}rad)`;
            }
          });
        }
      }
      requestAnimationFrame(tick);
    };
    tick();

    return () => {
      alive = false;
      el.removeEventListener("pointerdown", onDown);
      el.removeEventListener("pointerup", onUp);
      ro.disconnect();
      controls.dispose();
      renderer.dispose();
      if (renderer.domElement.parentNode === el) el.removeChild(renderer.domElement);
    };
  }, []);

  useEffect(() => {
    const s = state.current;
    if (!s) return;
    s.setPreset(section ? "section" : view);
  }, [view, section]);

  return (
    <div className="scene">
      <div className="scene-host" ref={host} />
      <div className="ann-layer" ref={overlay}>
        {ANNOTATIONS.map((a) => (
          <div className="ann" data-ann={a.id} key={a.id}>
            <span className="ann-lead" />
            <span className="ann-card">
              <b>{a.text}</b>
              <i>{a.sub}</i>
            </span>
          </div>
        ))}
      </div>
    </div>
  );
}
