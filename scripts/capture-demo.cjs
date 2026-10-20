/**
 * Capture the demo: a small set of representative stills plus the animations.
 *
 * The report does not need 90 screenshots. What it needs is:
 *   - one hero elevation per pane (5),
 *   - the states that carry an argument (door, section, explode, probe window),
 *   - three short animations the reader can actually watch in PDF/Word,
 *   - one live-link QR code.
 *
 * Animations are captured as frame sequences at a fixed rate and encoded to GIF
 * (and MP4 when ffmpeg exists) by scripts/make_media.py.
 *
 *   node scripts/capture-demo.cjs
 */
const path = require("path");
const fs = require("fs");
const { createRequire } = require("module");

const ROOT = path.resolve(__dirname, "..");
const demoRequire = createRequire(path.join(ROOT, "demo", "package.json"));
const { chromium } = demoRequire("playwright");

const FIG = path.join(ROOT, "results", "figures", "demo");
const SEQ = path.join(ROOT, "results", "figures", "demo", "_frames");
const URL = process.env.DEMO_URL || "http://127.0.0.1:4180/index.html";

const VIEWPORT = { width: 1600, height: 940 };
const SCALE = 2;

const stills = [];
let page;
let stage;

async function snap(name, { clip, note = "", full = false, settle = 800 } = {}) {
  await page.waitForTimeout(settle);
  const file = path.join(FIG, `${name}.png`);
  const box = full ? null : (clip ?? stage);
  await page.screenshot({ path: file, ...(box ? { clip: box } : {}) });
  const px = box
    ? [Math.round(box.width * SCALE), Math.round(box.height * SCALE)]
    : [VIEWPORT.width * SCALE, VIEWPORT.height * SCALE];
  stills.push({ name, file: path.relative(ROOT, file), note, px });
  process.stdout.write(`  ${name}.png  ${px[0]}x${px[1]}\n`);
}

const clickText = (sel, text) =>
  page.evaluate(([s, t]) => {
    const el = [...document.querySelectorAll(s)].find((e) => e.innerText.trim().includes(t));
    if (el) el.click();
    return Boolean(el);
  }, [sel, text]);

const press = async (key, wait = 500) => {
  await page.keyboard.press(key);
  await page.waitForTimeout(wait);
};

async function front() {
  await page.evaluate(() => {
    const el = [...document.querySelectorAll(".tool")].find((b) => b.innerText.trim() === "正面");
    if (el) el.click();
  });
  await page.waitForTimeout(1400);
}

/* Capture a fixed number of frames while something animates on screen. */
async function sequence(name, frames, { clip, tick = 105, before, during } = {}) {
  const dir = path.join(SEQ, name);
  fs.rmSync(dir, { recursive: true, force: true });
  fs.mkdirSync(dir, { recursive: true });
  if (before) await before();
  await page.waitForTimeout(400);
  const box = clip ?? stage;
  for (let i = 0; i < frames; i += 1) {
    if (during) await during(i, frames);
    await page.screenshot({
      path: path.join(dir, `${String(i).padStart(3, "0")}.png`),
      clip: box,
    });
    await page.waitForTimeout(tick);
  }
  process.stdout.write(`  sequence ${name}: ${frames} frames\n`);
}

async function main() {
  fs.mkdirSync(FIG, { recursive: true });
  fs.mkdirSync(SEQ, { recursive: true });
  const browser = await chromium.launch({ args: ["--use-angle=d3d11"] });
  const context = await browser.newContext({
    viewport: VIEWPORT,
    deviceScaleFactor: SCALE,
    locale: "zh-CN",
  });
  page = await context.newPage();
  const errors = [];
  page.on("pageerror", (e) => {
    if (!/setPointerCapture/.test(e.message)) errors.push(e.message);
  });

  await page.goto(`${URL}?t=${Date.now()}`, { waitUntil: "load" });
  await page.waitForSelector(".policy", { timeout: 25000 });
  await page.waitForTimeout(3000);

  const box = await (await page.$(".scene-host canvas")).boundingBox();
  stage = {
    x: Math.round(box.x),
    y: Math.round(box.y),
    width: Math.round(box.width),
    height: Math.round(box.height),
  };

  // ------------------------------------------------------------- stills
  await front();
  await snap("01_run", { note: "运行栏：正面整机、本帧读数、时间轴" });
  await snap("01_run_full", { note: "运行栏整页", full: true });

  await press("2");
  await page.waitForTimeout(800);
  await front();
  await snap("02_twin_front", { note: "孪生栏：正面、零件标注" });

  await clickText(".toggle", "腔门开合");
  await page.waitForTimeout(1500);
  await snap("03_twin_door_closed", { note: "腔门关闭：钢框黑玻璃、把手、三旋钮" });
  await clickText(".toggle", "腔门开合");
  await page.waitForTimeout(1400);

  await clickText(".toggle", "剖切视图");
  await page.waitForTimeout(1800);
  await front();
  await snap("04_twin_section", { note: "剖切视图：正面切开，内衬与风道可见" });
  await clickText(".toggle", "剖切视图");
  await page.waitForTimeout(1500);

  await clickText(".auto-row .seg", "自动分解");
  await page.waitForTimeout(3600);
  await front();
  await snap("05_twin_explode", { note: "自动分解 100%：九层沿装配轴分离并标注" });
  await clickText(".auto-row .seg", "复位");
  await page.waitForTimeout(1800);

  await press("3");
  await page.waitForTimeout(900);
  await snap("06_probe", { note: "探针栏：机制链与两段探针窗", full: true });

  await press("4");
  await page.waitForTimeout(900);
  await snap("07_compare", { note: "对照栏：五种策略同工况停机几何", full: true });

  await press("5");
  await page.waitForTimeout(900);
  await snap("08_surface", { note: "响应面：厚度 × 初温，着色 e_α 中位数", full: true });

  await press("1");
  await page.waitForTimeout(900);

  // --------------------------------------------------------- animation
  // Only the explode diagram is animated: it is the one interaction a still
  // cannot carry (nine layers separating along their assembly axes). Everything
  // else is delivered as a still.
  //
  // The explode controls live on the 孪生 pane, so the pane must be active or
  // the clicks land on nothing and the sequence records a static frame.
  await sequence("anim_explode", 42, {
    clip: stage,
    tick: 90,
    before: async () => {
      await press("2", 900);
      await front();
      await clickText(".auto-row .seg", "复位");
      await page.waitForTimeout(1400);
      await front();
    },
    during: async (i) => {
      if (i === 1) await clickText(".auto-row .seg", "自动分解");
      if (i === 28) await clickText(".auto-row .seg", "复位");
    },
  });
  await page.waitForTimeout(1500);

  const manifest = {
    generated: new Date().toISOString(),
    url: URL,
    viewport: VIEWPORT,
    deviceScaleFactor: SCALE,
    stills,
    animations: ["anim_explode"],
    errors,
  };
  fs.writeFileSync(path.join(FIG, "manifest.json"), JSON.stringify(manifest, null, 1));
  console.log(`\n${stills.length} stills + 1 animation`);
  if (errors.length) console.log("page errors:", errors);

  await browser.close();
}

main().catch((err) => {
  console.error(err);
  process.exit(1);
});
