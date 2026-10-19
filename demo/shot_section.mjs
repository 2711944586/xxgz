// Verify the section view actually hides the door.
import path from "node:path";
import { spawn, execSync } from "node:child_process";
import { chromium } from "playwright";
import { fileURLToPath } from "node:url";

const root = path.dirname(fileURLToPath(import.meta.url));
const out = path.resolve(root, "../results/figures/paper");
const vite = spawn("npx", ["vite", "--port", "5191", "--strictPort"], {
  cwd: root, shell: true, stdio: "pipe",
});
await new Promise((resolve, reject) => {
  const t = setTimeout(() => reject(new Error("vite timeout")), 60000);
  vite.stdout.on("data", (b) => { if (b.toString().includes("Local:")) { clearTimeout(t); resolve(); } });
});

const browser = await chromium.launch();
const page = await browser.newPage({ viewport: { width: 1680, height: 1080 } });
const errs = [];
page.on("pageerror", (e) => errs.push(e.message));
await page.goto("http://127.0.0.1:5191/", { waitUntil: "networkidle" });
await page.waitForTimeout(2500);

// click 剖面
await page.getByRole("button", { name: "剖面" }).click();
await page.waitForTimeout(1500);
await page.screenshot({ path: path.join(out, "E_demo_section.png"), fullPage: true });
console.log("section shot saved, errors:", errs.length ? errs : "none");

await browser.close();
try { if (vite.pid) execSync(`taskkill /PID ${vite.pid} /T /F`, { stdio: "ignore" }); } catch {}
process.exit(0);
