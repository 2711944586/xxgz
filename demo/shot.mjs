import { chromium } from "playwright";
import { spawn } from "node:child_process";
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
  const timer = setTimeout(() => reject(new Error("vite timeout")), 40000);
  vite.stdout.on("data", (buf) => {
    const text = buf.toString();
    if (text.includes("Local:")) {
      clearTimeout(timer);
      resolve();
    }
  });
  vite.stderr.on("data", (buf) => process.stderr.write(buf));
});

const browser = await chromium.launch();
const page = await browser.newPage({ viewport: { width: 1440, height: 900 } });
await page.goto("http://127.0.0.1:5183/", { waitUntil: "networkidle" });
await page.waitForTimeout(600);
await page.screenshot({ path: path.join(outDir, "E_demo_start.png") });

const time = page.locator("label", { hasText: "时间" }).locator("xpath=following-sibling::input[1]");
await time.fill("200");
await page.waitForTimeout(300);
await page.screenshot({ path: path.join(outDir, "E_demo_late.png") });

await page.selectOption("select", "open");
await page.waitForTimeout(400);
await page.screenshot({ path: path.join(outDir, "E_demo_open.png") });

const body = await page.locator("body").innerText();
fs.writeFileSync(path.join(outDir, "E_demo_text.txt"), body, "utf8");
await browser.close();
vite.kill();
console.log("shots ok");
