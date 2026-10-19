const { chromium } = require("playwright");
(async () => {
  const b = await chromium.launch({ args: ["--use-angle=d3d11"] });
  const p = await b.newPage({ viewport: { width: 1680, height: 980 } });
  await p.goto("http://127.0.0.1:4180/", { waitUntil: "networkidle" });
  await p.waitForTimeout(2000);
  await p.click(".event-chip");
  await p.waitForTimeout(1200);
  await p.screenshot({ path: "_q_probe.png" });
  await b.close();
})();
