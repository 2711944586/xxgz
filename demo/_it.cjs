const { chromium } = require("playwright");
(async () => {
  const b = await chromium.launch({ args: ["--use-angle=d3d11"] });
  const p = await b.newPage({ viewport: { width: 1680, height: 980 } });
  await p.goto("http://127.0.0.1:4180/", { waitUntil: "networkidle" });
  await p.waitForTimeout(2000);
  await p.keyboard.press("2"); await p.waitForTimeout(1000);
  const canvas = await p.$(".scene-host canvas");
  const bb = await canvas.boundingBox();
  await p.mouse.click(bb.x + bb.width*0.45, bb.y + bb.height*0.5);
  await p.waitForTimeout(600);
  console.log("picked:", await p.evaluate(() => document.querySelector(".part-card b")?.innerText || "none"));
  console.log("notice:", await p.evaluate(() => document.querySelector(".picked b")?.innerText || "none"));
  await p.screenshot({ path: "_v_pick.png" });
  await b.close();
})();
