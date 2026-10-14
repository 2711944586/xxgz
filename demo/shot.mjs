import { chromium } from "playwright";
import { spawn, execSync } from "node:child_process";
import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";

const root = path.dirname(fileURLToPath(import.meta.url));
const outDir = path.resolve(root, "../results/figures/paper");
fs.mkdirSync(outDir, { recursive: true });

const vite = spawn("npx", ["vite", "--port", "5183", "--strictPort"], {
  cwd: root,
  shell: true,
  stdio: "pipe",
});
await new Promise((resolve, reject) => {
  const timer = setTimeout(() => reject(new Error("vite timeout")), 60000);
  const onData = (buf) => {
    const text = buf.toString();
    process.stdout.write(text);
    if (text.includes("Local:")) {
      clearTimeout(timer);
      resolve();
    }
  };
  vite.stdout.on("data", onData);
  vite.stderr.on("data", (buf) => process.stderr.write(buf));
});

const browser = await chromium.launch();
const page = await browser.newPage({ viewport: { width: 1440, height: 900 } });
page.setDefaultTimeout(60000);
await page.goto("http://127.0.0.1:5183/", { waitUntil: "networkidle" });
await page.waitForSelector("#time");
await page.waitForFunction(() => {
  const el = document.querySelector("#time");
  return el && Number(el.max) > 100;
});
await page.waitForSelector("canvas");
await page.waitForTimeout(1800);

async function setIndex(value) {
  await page.$eval("#time", (el, v) => {
    const proto = Object.getOwnPropertyDescriptor(HTMLInputElement.prototype, "value");
    proto.set.call(el, String(v));
    el.dispatchEvent(new Event("input", { bubbles: true }));
    el.dispatchEvent(new Event("change", { bubbles: true }));
  }, value);
}

async function shot(name) {
  await page.waitForTimeout(1800);
  await page.screenshot({ path: path.join(outDir, name), fullPage: true });
}

await page.selectOption("#cook", "combi");
await page.selectOption("#policy", "dual");
await page.waitForTimeout(500);
await setIndex(0);
await shot("E_demo_start.png");

const max = Number(await page.locator("#time").getAttribute("max"));
const probeIndex = Math.min(max, 20);
await setIndex(probeIndex);
await shot("E_demo_probe.png");

const lateIndex = Math.min(max, 210);
await setIndex(lateIndex);
await shot("E_demo_late.png");

await page.selectOption("#policy", "open");
await setIndex(0);
const doorBtn = page.getByRole("button", { name: /开门|关门/ });
if ((await doorBtn.innerText()) === "开门") await doorBtn.click();
await shot("E_demo_open.png");

await page.selectOption("#policy", "dual");
await page.selectOption("#compare", "open");
await setIndex(lateIndex);
await shot("E_demo_compare.png");

const stopIndex = Math.min(max, 233);
await page.selectOption("#compare", "none");
await setIndex(stopIndex);
await shot("E_demo_stop.png");

await page.getByRole("button", { name: "50 mm" }).click();
await page.waitForTimeout(800);
const thickMax = Number(await page.locator("#time").getAttribute("max"));
await setIndex(thickMax);
await shot("E_demo_thick.png");

const body = await page.locator("body").innerText();
fs.writeFileSync(path.join(outDir, "E_demo_text.txt"), body, "utf8");
await browser.close();
try {
  if (vite.pid) execSync(`taskkill /PID ${vite.pid} /T /F`, { stdio: "ignore" });
} catch {
  /* already gone */
}
console.log("shots ok", { max, probeIndex, lateIndex });
process.exit(0);
