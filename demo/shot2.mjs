// Capture the upgraded demo at several frames to verify the visuals.
import fs from "node:fs";
import path from "node:path";
import { spawn, execSync } from "node:child_process";
import { chromium } from "playwright";
import { fileURLToPath } from "node:url";

const root = path.dirname(fileURLToPath(import.meta.url));
const outDir = path.resolve(root, "../results/figures/paper");
fs.mkdirSync(outDir, { recursive: true });

const vite = spawn("npx", ["vite", "--port", "5185", "--strictPort"], {
  cwd: root, shell: true, stdio: "pipe",
});
await new Promise((resolve, reject) => {
  const timer = setTimeout(() => reject(new Error("vite timeout")), 60000);
  vite.stdout.on("data", (buf) => {
    const text = buf.toString();
    process.stdout.write(text);
    if (text.includes("Local:")) { clearTimeout(timer); resolve(); }
  });
});

const browser = await chromium.launch();
const page = await browser.newPage({ viewport: { width: 1680, height: 1080 } });
page.setDefaultTimeout(60000);
await page.goto("http://127.0.0.1:5185/", { waitUntil: "networkidle" });
await page.waitForSelector("#time");
await page.waitForFunction(() => {
  const el = document.querySelector("#time");
  return el && Number(el.max) > 100;
});
await page.waitForTimeout(2200);
await page.evaluate(() => window.__actsCam?.set(-0.36, 0.27, 7.85));
await page.waitForTimeout(400);

async function setIndex(v) {
  await page.$eval("#time", (el, value) => {
    const proto = Object.getOwnPropertyDescriptor(HTMLInputElement.prototype, "value");
    proto.set.call(el, String(value));
    el.dispatchEvent(new Event("input", { bubbles: true }));
    el.dispatchEvent(new Event("change", { bubbles: true }));
  }, v);
}
async function shot(name) {
  await page.waitForTimeout(1600);
  await page.screenshot({ path: path.join(outDir, name), fullPage: true });
}

await page.selectOption("#cook", "combi");
await page.selectOption("#policy", "dual");
await setIndex(0);
await shot("E_demo_start.png");

const max = Number(await page.locator("#time").getAttribute("max"));
await setIndex(Math.min(max, 21));
await shot("E_demo_probe.png");

await setIndex(Math.min(max, 210));
await shot("E_demo_late.png");

await page.selectOption("#policy", "open");
await setIndex(0);
const doorBtn = page.getByRole("button", { name: /开门|关门/ });
if ((await doorBtn.innerText()) === "开门") await doorBtn.click();
await page.evaluate(() => window.__actsCam?.set(-0.28, 0.24, 8.15));
await shot("E_demo_open.png");
await page.evaluate(() => window.__actsCam?.set(-0.36, 0.27, 7.85));

await page.selectOption("#policy", "dual");
await page.selectOption("#compare", "open");
await setIndex(Math.min(max, 210));
await shot("E_demo_compare.png");

await page.selectOption("#compare", "none");
await page.getByRole("button", { name: /停机/ }).click();
await shot("E_demo_stop.png");

await page.getByRole("button", { name: "50 mm" }).click();
await page.waitForTimeout(800);
const thickMax = Number(await page.locator("#time").getAttribute("max"));
await setIndex(thickMax);
await shot("E_demo_thick.png");

await browser.close();
try { if (vite.pid) execSync(`taskkill /PID ${vite.pid} /T /F`, { stdio: "ignore" }); } catch {}
console.log("shots ok", { max, thickMax });
process.exit(0);
