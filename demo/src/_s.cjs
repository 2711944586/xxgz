const { chromium } = require("playwright");
(async () => {
  const b = await chromium.launch({ args: ["--use-angle=d3d11"] });
  const p = await b.newPage({ viewport: { width: 1680, height: 980 } });
  await p.goto("http://127.0.0.1:4180/", { waitUntil: "networkidle" });
  await p.waitForTimeout(2400);
  await p.evaluate(() => { const b = [...document.querySelectorAll(".seg")].find(e => e.innerText.trim() === "关"); b.click(); });
  await p.waitForTimeout(1600);
  await p.screenshot({ path: "_door_closed.png" });
  await b.close();
})();
