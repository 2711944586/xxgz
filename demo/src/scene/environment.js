import * as THREE from "three";

/*
 * Studio environment. The reference build reads as a product shot because its
 * shell is lit from a large soft source and the floor is bright enough to pick
 * up a reflected edge; this scene was lit from a small key with a near-black
 * floor, which is why the body merged into the background. Three changes:
 * a bigger key box, a real wrap-around fill instead of one weak card, and a
 * horizon band that gives brushed metal something to reflect.
 */
export function studioEnvironment(renderer) {
  const scene = new THREE.Scene();
  scene.background = new THREE.Color("#171d22");

  const box = (w, h, intensity, color, pos, rot) => {
    const mat = new THREE.MeshBasicMaterial({ color: new THREE.Color(color).multiplyScalar(intensity) });
    const m = new THREE.Mesh(new THREE.PlaneGeometry(w, h), mat);
    m.position.set(...pos);
    if (rot) m.rotation.set(...rot);
    scene.add(m);
    return m;
  };

  // Large key, high front-right: the main source of the shell's top-face sheen.
  box(9, 6, 2.15, "#fff4e6", [6.5, 6.0, 5.0], [0, -0.72, 0]);
  // Wrap fill, front-left, wide and soft so the left panel is not pure black.
  box(7.5, 5, 1.35, "#cfe0ea", [-7.5, 3.6, 4.2], [0, 0.82, 0]);
  // Narrow rim behind, to draw the silhouette off the background.
  box(9, 1.3, 1.9, "#a8d4e4", [0, 4.8, -6.6], [0, 0, 0]);
  // Horizon band: a broad dim card at eye level that brushed metal reflects.
  box(16, 4.5, 0.55, "#5d707c", [0, 0.4, -7.6], [0, 0, 0]);
  // Bounce floor, brighter than before so the underside picks up light.
  box(14, 9, 0.5, "#4a5862", [0, -2.6, 1.2], [-Math.PI / 2, 0, 0]);

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
  g.addColorStop(0, "#2b363d");
  g.addColorStop(0.42, "#1d262c");
  g.addColorStop(1, "#101619");
  ctx.fillStyle = g;
  ctx.fillRect(0, 0, 512, 512);
  const tex = new THREE.CanvasTexture(canvas);
  tex.colorSpace = THREE.SRGBColorSpace;
  return tex;
}
