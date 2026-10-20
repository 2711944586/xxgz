import * as THREE from "three";

export const ANNOTATIONS = [
  { id: "console", anchor: [1.29, 2.99, 1.72], text: "数显面板", sub: "腔温 + 三枚旋钮" },
  { id: "heater", anchor: [0.55, 2.27, 0.35], text: "U 形加热管 ×6", sub: "顶置辐射 + 对流" },
  { id: "fan", anchor: [0.02, 1.35, -1.12], text: "十叶离心风机", sub: "档位 0–1.3" },
  { id: "nozzle", anchor: [-1.55, 1.62, 0.2], text: "双锥蒸汽喷嘴", sub: "左壁直喷" },
  { id: "vent", anchor: [1.62, 2.2, -1.2], text: "七片排汽百叶", sub: "后壁上部，开度随指令" },
  { id: "tray", anchor: [0.0, 0.72, 0.62], text: "搪瓷烤盘 + 烤架", sub: "四层搁架" },
  { id: "coldSpot", anchor: [0.0, 0.9, -0.42], text: "冷点", sub: "十六层最低温" },
  { id: "doorSwitch", anchor: [2.4, 0.62, 1.34], text: "门互锁", sub: "安全回路" },
  { id: "waterFloat", anchor: [-2.0, 0.36, -0.62], text: "水位浮子", sub: "干烧保护" },
  { id: "heaterProbe", anchor: [-1.9, 2.34, 0.6], text: "加热器测温", sub: "230 °C 削减" },
  { id: "bulb", anchor: [1.88, 2.36, 0.62], text: "毛细管感温包", sub: "超温断开加热" },
  { id: "humidity", anchor: [1.88, 1.62, 1.18], text: "腔体湿度探头", sub: "近排汽口" },
];

export const EXPLODE_LABELS = {
  id: "explode",
  items: [
    { id: "shellTop", text: "外壳顶板", sub: "深色钢板", side: "right" },
    { id: "insulation", text: "岩棉保温层", sub: "夹层隔热", side: "right" },
    { id: "liner", text: "拉丝不锈钢内衬", sub: "压花板", side: "right" },
    { id: "heaterAssy", text: "U 形加热管组", sub: "六根 + 反射板", side: "right" },
    { id: "fanAssy", text: "十叶风机", sub: "后壁离心", side: "right" },
    { id: "consoleAssy", text: "数显面板", sub: "腔温与三旋钮", side: "right" },
    { id: "boardAssy", text: "温控主板", sub: "继电器与毛细管", side: "right" },
    { id: "steamAssy", text: "蒸汽管路与水箱", sub: "左壁", side: "left" },
    { id: "racksAssy", text: "搁架与烤盘", sub: "四层", side: "left" },
    { id: "doorAssy", text: "门体", sub: "双层玻璃 + 钢框", side: "left" },
  ],
};

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

/* Lay callouts out in two columns ordered by projected height, so cards never
   overlap and every leader stays a straight line back to its own part. The
   stack is also clamped into the viewport: a part at the very top of the
   exploded stack would otherwise push its card off-screen. */
export function layoutCallouts(items, width, opts = {}) {
  const gap = opts.gap ?? 42;
  const edge = opts.edge ?? 10;
  const split = opts.split ?? 0.5;
  const height = opts.height ?? 0;
  const sorted = [...items].sort((a, b) => a.y - b.y);
  const lanes = { left: [], right: [] };
  return sorted.map((item) => {
    const side = item.side || (item.x < width * split ? "left" : "right");
    const lane = lanes[side];
    let y = item.y;
    const last = lane[lane.length - 1];
    if (last != null && y - last < gap) y = last + gap;
    lane.push(y);
    const cardX = side === "left" ? Math.max(edge, item.x - 14) : Math.min(width - edge, item.x + 14);
    const cardY = height > 0 ? Math.min(Math.max(y, edge + 9), height - edge - 9) : y;
    return { ...item, side, cardX, cardY };
  });
}
