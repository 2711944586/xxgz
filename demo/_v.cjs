const { chromium } = require("playwright");
(async () => {
  const b = await chromium.launch({ args: ["--use-angle=d3d11"] });
  const p = await b.newPage({ viewport: { width: 1366, height: 768 } });
  p.on("pageerror", e => console.log("PAGEERROR", e.message));
  await p.goto("http://127.0.0.1:4180/", { waitUntil: "networkidle" });
  await p.waitForTimeout(3000);
  const st = await p.evaluate(() => ({
    timeline: !!document.querySelector(".timeline"),
    chart: document.querySelectorAll(".chart").length,
    fatal: document.querySelector(".fatal")?.innerText.slice(0,200),
    loading: !!document.querySelector(".loading"),
    html: document.getElementById("root").innerHTML.length,
  }));
  console.log(JSON.stringify(st));
  await p.screenshot({ path: "_v_dbg.png" });
  await b.close();
})();
