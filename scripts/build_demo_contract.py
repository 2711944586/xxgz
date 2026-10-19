"""P0-1: give the demo dataset a machine-checkable contract.

The audit found catalog.json carries 36 scenarios x 414 frames and not one of
them records which kernel produced it, while results/logs/MANIFEST.json
meticulously tags all 15 research artifacts. That is the single largest
credibility gap: a viewer cannot tell whether a number on screen came from the
baseline kernel (used by the paper's main tables) or the display kernel.

This script writes demo/public/dataset.json, a sidecar that states:

  - which kernel generation produced the catalog, and what its five switches are;
  - the exact initial conditions and sampling of every scenario key;
  - the data provenance chain (script -> log -> page);
  - the known model boundaries the page must surface;
  - a checksum per scenario so a stale catalog is detectable.

Nothing in the existing trajectory data is modified; the contract describes it.
"""
from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from acts_mcdt.physics import BASELINE, DISPLAY  # noqa: E402

DEMO = ROOT / "demo" / "public"
cat = json.loads((DEMO / "catalog.json").read_text(encoding="utf-8"))
params = json.loads((DEMO / "parameters.json").read_text(encoding="utf-8"))
summary = json.loads((DEMO / "summary.json").read_text(encoding="utf-8"))

# --- derive scenario table from the keys themselves ---------------------
scen = {}
for row in cat:
    key = row["key"]
    if key in scen:
        continue
    parts = key.split("_")
    # keys look like dual_combi_30 / open_steam_15 / mpc_bake_50
    scen[key] = {
        "policy": parts[0],
        "cook_mode": parts[1],
        "length_mm": int(parts[2]),
    }

# --- per-scenario fingerprint ------------------------------------------
digest = {}
for key in scen:
    rows = [r for r in cat if r["key"] == key]
    payload = json.dumps(
        [[round(r["time"], 3), round(r["t1"], 4), round(r["t2"], 4),
          round(r["alpha"], 4), round(r["hat"], 4)] for r in rows],
        sort_keys=True,
    ).encode()
    digest[key] = hashlib.sha256(payload).hexdigest()[:16]

contract = {
    "kind": "demo dataset contract",
    "schema_version": 1,
    "purpose": (
        "Declares what the browser replay is and what produced it. The page "
        "must display mode, kernel generation and provenance so that a viewer "
        "never mistakes a precomputed trajectory for a live measurement."
    ),
    "mode": {
        "id": "offline-replay",
        "label_zh": "离线轨迹回放",
        "label_en": "offline replay",
        "statement_zh": (
            "页面读取已写盘的轨迹数组，不在浏览器内重跑积分；显示的一切"
            "都是预计算仿真结果，不含任何真实设备测量。"
        ),
        "is_live": False,
        "is_measurement": False,
    },
    "kernel": {
        "generation": "display",
        "why": (
            "演示页与档位研究共用 display 代际；论文主表 s1/s0/s2 使用 "
            "baseline 代际。两者在同一名义格子上可以相差 0.2 以上，因此"
            "页面必须显式标注，不能与主表数字混读。"
        ),
        "switches": {
            "display": DISPLAY,
            "baseline": BASELINE,
        },
        "differing_switches": sorted(
            k for k in DISPLAY if DISPLAY[k] != BASELINE.get(k)
        ),
    },
    "sampling": {
        "dt_s": params["dt_s"],
        "record_every": params["record_every"],
        "sample_interval_s": params["dt_s"] * params["record_every"],
        "horizon_min": params["minutes"],
        "frames_per_scenario": 414,
        "scenarios": len(scen),
        "total_frames": len(cat),
    },
    "default_scenario": {
        "key": f"{params['policy']}_{params['cook_mode']}_{int(params['length_m']*1000)}",
        "seed": params["seed"],
        "prototype": params["proto"],
        "length_m": params["length_m"],
        "t0_c": params["t0_c"],
        "m0": params["m0"],
    },
    "scenarios": scen,
    "fingerprints": digest,
    "provenance": {
        "generator": "scripts/export_demo_trace.py",
        "kernel": "src/acts_mcdt/physics.py :: rollout(generation='display')",
        "source_log": "results/logs/demo_seed7_dual.csv",
        "research_manifest": "results/logs/MANIFEST.json",
        "paper_figures": "results/figures/paper/E_demo_*.png",
    },
    "boundaries": [
        {
            "id": "r_proxy",
            "severity": "info",
            "zh": "跟踪器里的 r 是滞后倍数代理量，由表面与冷点的真值温差反解而来，"
                  "不是可直接测量的传感器读数。",
            "where": "热阻/方差 读数、探针模式",
        },
        {
            "id": "steam_clip",
            "severity": "warning",
            "zh": "display 代际的蒸汽压驱动裁在 [-0.4, 0.4] bar，约 60.1% 的步数贴下界；"
                  "凡依赖蒸汽压差符号的结论只能按符号读，不能按标定灵敏度读。",
            "where": "路径 A/B/C、蒸汽指令",
        },
        {
            "id": "moisture_dead_axis",
            "severity": "warning",
            "zh": "家用工况下初始含水落在活度饱和段，界面潜热对它的偏导接近零，"
                  "因此含水在当前场景里是无效参数轴。",
            "where": "含水读数、参数敏感性",
        },
        {
            "id": "design_line",
            "severity": "critical",
            "zh": "alpha_m = 0.85 是模型设计判据，用于定义停机偏差 e_alpha 的零点，"
                  "不是经过认证的食品安全阈值；模型也未纳入微生物初始数量。",
            "where": "设计线、两盏判断灯、停机判据",
        },
        {
            "id": "applicability",
            "severity": "info",
            "zh": "适用工况为家用一体机、55 min 时域、厚度 10-60 mm；"
                  "超出范围的外推未经检验。",
            "where": "全页",
        },
    ],
    "expected_summary": {
        "stop_s": summary["stop_s"],
        "e_alpha": summary["e_alpha"],
        "tolerance": 1e-3,
    },
}

out = DEMO / "dataset.json"
out.write_text(json.dumps(contract, ensure_ascii=False, indent=1), encoding="utf-8")
print(f"wrote {out} ({out.stat().st_size/1024:.1f} KB)")
print(f"scenarios: {len(scen)}, frames: {len(cat)}, fingerprints: {len(digest)}")
print(f"differing switches: {contract['kernel']['differing_switches']}")
