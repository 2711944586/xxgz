import * as THREE from "three";

export function studioEnvironment(renderer) {
  const scene = new THREE.Scene();
  scene.background = new THREE.Color("#05080a");

  const box = (w, h, intensity, color, pos, rot) => {
    const mat = new THREE.MeshBasicMaterial({ color: new THREE.Color(color).multiplyScalar(intensity) });
    const m = new THREE.Mesh(new THREE.PlaneGeometry(w, h), mat);
    m.position.set(...pos);
    if (rot) m.rotation.set(...rot);
    scene.add(m);
    return m;
  };

  box(6, 4.2, 2.6, "#fff2df", [5.5, 5.2, 4.2], [0, -0.72, 0]);
  box(5, 3.2, 0.7, "#9fc4d4", [-6, 3.2, 3.2], [0, 0.85, 0]);
  box(7, 0.9, 1.1, "#9fd2e2", [0, 4.6, -6.4], [0, 0, 0]);
  box(8, 4, 0.22, "#3a464e", [0, -2.2, 1.5], [-Math.PI / 2, 0, 0]);

  const pmrem = new THREE.PMREMGenerator(renderer);
  pmrem.compileEquirectangularShader();
  const target = pmrem.fromScene(scene, 0.02);
  pmrem.dispose();
  scene.traverse((m) => {
    if (m.isMesh) {
      m.geometry.dispose();
      m.material.dispose();
    }
  });
  return target.texture;
}

export function floorTexture() {
  const canvas = document.createElement("canvas");
  canvas.width = canvas.height = 512;
  const ctx = canvas.getContext("2d");
  const g = ctx.createRadialGradient(256, 256, 10, 256, 256, 254);
  g.addColorStop(0, "#1b2429");
  g.addColorStop(0.42, "#131a1f");
  g.addColorStop(1, "#07090b");
  ctx.fillStyle = g;
  ctx.fillRect(0, 0, 512, 512);
  const tex = new THREE.CanvasTexture(canvas);
  tex.colorSpace = THREE.SRGBColorSpace;
  return tex;
}
