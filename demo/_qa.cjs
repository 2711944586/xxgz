const { chromium } = require("playwright");
(async () => {
  const b = await chromium.launch({ args: ["--use-angle=d3d11"] });
  const p = await b.newPage({ viewport: { width: 1680, height: 980 } });
  const errs = [];
  p.on("pageerror", e => errs.push("PAGEERROR " + e.message));
  p.on("console", m => { if (m.type() === "error") errs.push("CERR " + m.text().slice(0,180)); });
  await p.goto("http://127.0.0.1:4180/", { waitUntil: "networkidle" });
  await p.waitForTimeout(2000);
  await p.screenshot({ path: "_q_run.png" });
  await p.click(".play");
  await p.waitForTimeout(1500);
  await p.click(".play");
  await p.waitForTimeout(300);
  console.log("clock:", await p.evaluate(() => document.querySelector(".clock b")?.innerText));
  const chips = await p.$$eval(".event-chip", els => els.map(e => e.innerText));
  console.log("chips:", JSON.stringify(chips));
  await p.evaluate(() => { const b = [...document.querySelectorAll(".event-chip")].find(e => e.innerText.includes("探针")); if (b) b.click(); });
  await p.waitForTimeout(1000);
  console.log("hud:", await p.evaluate(() => document.querySelector(".hud")?.innerText.replace(/\n/g," ")));
  await p.screenshot({ path: "_q_probe.png" });
  for (const [k, n] of [["2","twin"],["3","chain"],["4","compare"],["5","surface"]]) {
    await p.keyboard.press(k);
    await p.waitForTimeout(1100);
    await p.screenshot({ path: `_q_${n}.png` });
  }
  console.log("errors:", JSON.stringify(errs.slice(0,5)));
  await b.close();
})();
