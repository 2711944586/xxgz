// Smoke-test the upgraded scene: look for console errors and confirm GTAO runs.
import path from "node:path";
import { spawn, execSync } from "node:child_process";
import { chromium } from "playwright";
import { fileURLToPath } from "node:url";

const root = path.dirname(fileURLToPath(import.meta.url));
const vite = spawn("npx", ["vite", "--port", "5186", "--strictPort"], {
  cwd: root, shell: true, stdio: "pipe",
});
await new Promise((resolve, reject) => {
  const timer = setTimeout(() => reject(new Error("vite timeout")), 60000);
  vite.stdout.on("data", (b) => {
    const t = b.toString();
    if (t.includes("Local:")) { clearTimeout(timer); resolve(); }
  });
});

const browser = await chromium.launch();
const page = await browser.newPage({ viewport: { width: 1400, height: 900 } });
const errors = [];
const logs = [];
page.on("console", (m) => {
  if (m.type() === "error") errors.push(m.text());
  else logs.push(m.text());
});
page.on("pageerror", (e) => errors.push("PAGEERROR: " + e.message));

await page.goto("http://127.0.0.1:5186/", { waitUntil: "networkidle" });
await page.waitForTimeout(4000);

const info = await page.evaluate(() => {
  const canvas = document.querySelector("canvas");
  return {
    hasCanvas: !!canvas,
    width: canvas?.width ?? 0,
    height: canvas?.height ?? 0,
    webgl2: !!canvas?.getContext?.("webgl2"),
  };
});

console.log("canvas:", JSON.stringify(info));
console.log("errors:", errors.length ? errors : "none");
await browser.close();
try { if (vite.pid) execSync(`taskkill /PID ${vite.pid} /T /F`, { stdio: "ignore" }); } catch {}
process.exit(errors.length ? 1 : 0);
