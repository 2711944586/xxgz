import * as THREE from "three";

export const ANNOTATIONS = [
  { id: "heater", anchor: [0.55, 2.27, 0.35], text: "U 形加热管 ×6", sub: "顶置辐射 + 对流" },
  { id: "fan", anchor: [0.02, 1.35, -1.12], text: "十叶离心风机", sub: "档位 0–1.3" },
  { id: "nozzle", anchor: [-1.55, 1.62, 0.2], text: "双锥蒸汽喷嘴", sub: "左壁直喷" },
  { id: "vent", anchor: [1.62, 2.2, -1.2], text: "七片排汽百叶", sub: "后壁上部，开度随指令" },
  { id: "tray", anchor: [0.0, 0.72, 0.62], text: "搪瓷烤盘 + 烤架", sub: "四层搁架" },
  { id: "coldSpot", anchor: [0.0, 0.9, -0.42], text: "冷点", sub: "十六层最低温" },
  { id: "doorSwitch", anchor: [2.4, 0.62, 1.34], text: "门互锁", sub: "安全回路" },
  { id: "waterFloat", anchor: [-2.0, 0.36, -0.62], text: "水位浮子", sub: "干烧保护" },
  { id: "heaterProbe", anchor: [-1.9, 2.34, 0.6], text: "加热器测温", sub: "230 °C 削减" },
  { id: "humidity", anchor: [1.88, 1.62, 1.18], text: "腔体湿度探头", sub: "近排汽口" },
];

export function anchorVector(anchor) {
  return new THREE.Vector3(anchor[0], anchor[1], anchor[2]);
}

export function projectionOf(camera, vector, width, height) {
  const p = vector.clone().project(camera);
  return {
    x: (p.x * 0.5 + 0.5) * width,
    y: (-p.y * 0.5 + 0.5) * height,
    behind: p.z > 1,
  };
}
