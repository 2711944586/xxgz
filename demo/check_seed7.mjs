import { simulate } from "./src/core.js";
import fs from "fs";
import path from "node:path";
import { fileURLToPath } from "node:url";

const here = path.dirname(fileURLToPath(import.meta.url));
const csvPath = path.resolve(here, "../results/logs/demo_seed7_dual.csv");
const rows = simulate({ length: 0.03, policy: "dual", seed: 7, t0: 8, m0: 0.72, minutes: 55 });
const csv = fs.readFileSync(csvPath, "utf8")
  .trim().split(/\r?\n/).slice(1).map((line) => line.split(",").map(Number));
let surf = 0, core = 0, hat = 0;
const n = Math.min(rows.length, csv.length);
for (let i = 0; i < n; i++) {
  surf = Math.max(surf, Math.abs(rows[i].t1 - csv[i][1]));
  core = Math.max(core, Math.abs(rows[i].t2 - csv[i][2]));
  hat = Math.max(hat, Math.abs(rows[i].hat - csv[i][3]));
}
console.log(JSON.stringify({ n, csv: csv.length, surf, core, hat, t0: rows[0].t1, alphaEnd: rows.at(-1).alpha }));
