"""Build the browser dataset for the interaction page.

Three products, two kernel generations, kept apart on purpose:

``data/traces.bin`` + ``data/manifest.json``
    Explorer traces from the ``display`` generation: five policies x three
    product modes x five thicknesses, 55 min at 2 s steps recorded every 8 s.
    Each frame carries 31 scalars plus the 16-cell through-thickness
    temperature field, quantised to int16 with a per-channel scale and offset.

``data/surfaces.json``
    Aggregated parameter surfaces from ``results/logs/surface_xl.json``, which
    is the ``baseline`` generation (the one the paper's main tables use):
    48 seeds per cell over length x initial temperature, length x moisture,
    length x heterogeneity and length x product mode.

``dataset.json``
    The contract: what the page is, which generation wrote each part, the
    per-scenario fingerprints, and the model boundaries the page must show.

    $env:PYTHONPATH="src"
    python scripts/build_demo_dataset.py
"""

from __future__ import annotations

import hashlib
import json
import os
import sys
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
PUBLIC = ROOT / "demo" / "public"
OUT = PUBLIC / "data"
LOG = ROOT / "results" / "logs"
sys.path.insert(0, str(ROOT / "src"))

POLICIES = ("open", "pid", "mpc", "mpc_h", "dual")
COOKS = ("steam", "bake", "combi")
LENGTHS_MM = (15, 20, 30, 40, 50)
SEED = 7
T0_C = 8.0
M0 = 0.72
MINUTES = 55.0
DT = 2.0
RECORD_EVERY = 4
CELLS = 16
PROBE = (150.0, 190.0)
DESIGN_LINE = 0.85
QMAX = 32766.0

POLICY_LABEL = {
    "open": "开环菜单",
    "pid": "腔温比例",
    "mpc": "无探针点估计",
    "mpc_h": "滚动时域 MPC",
    "dual": "对偶探针",
}
POLICY_NOTE = {
    "open": "菜单时间写在厚度档上，判据只有时钟",
    "pid": "按腔温误差调加热，冷点从未被观测",
    "mpc": "用标量跟踪器的冷点估计决策，无信息动作",
    "mpc_h": "60 s 滚动时域，按预测冷点选加热档",
    "dual": "150–190 s 两段探针，窗后更新热阻再停机",
}
COOK_LABEL = {"steam": "蒸", "bake": "烤", "combi": "组合"}
MODE_LABEL = ("品质", "探针", "保持")

# (key, kernel channel, label, unit, digits). ``time`` must stay first.
CHANNELS = [
    ("time", "time", "时间", "s", 1),
    ("tSurf", "t_surf", "表面温度", "°C", 2),
    ("tCore", "t_core", "冷点温度", "°C", 2),
    ("tHat", "t_hat", "冷点估计", "°C", 2),
    ("mMean", "m_mean", "平均含水", "kg/kg", 3),
    ("mSurf", "m_surf", "表面含水", "kg/kg", 3),
    ("alpha", "alpha_m", "热力进度 α", "", 3),
    ("alphaB", "alpha_b", "褐变进度", "", 3),
    ("rHat", "r_hat", "热阻倍数 r̂", "", 2),
    ("varR", "var_r", "热阻方差", "", 3),
    ("rProxy", "r_true_proxy", "热阻参照", "", 2),
    ("rField", "r_field", "结壳热阻项", "", 2),
    ("heat", "heat", "加热指令", "", 3),
    ("heatReq", "heat_req", "加热请求", "", 3),
    ("steam", "steam", "蒸汽阀", "", 3),
    ("fan", "fan", "风机档", "", 3),
    ("exhaust", "exhaust", "排汽开度", "", 3),
    ("mode", "mode", "工作模式", "", 0),
    ("heater", "heater", "加热器温度", "°C", 1),
    ("water", "water", "水箱水位", "", 3),
    ("cavT", "cav_t", "腔温", "°C", 2),
    ("cavH", "cav_h", "腔湿", "", 3),
    ("cavP", "cav_p", "腔压", "bar", 3),
    ("door", "door", "门状态", "", 0),
    ("leak", "leak", "漏电代理", "", 4),
    ("pathA", "path_a", "路径 A 冷点潜热", "W/m²", 1),
    ("pathB", "path_b", "路径 B 表面蒸发", "W/m²", 1),
    ("pathC", "path_c", "路径 C 结壳热阻", "W/(m·K)", 4),
    ("vapor", "vapor", "水汽分数", "", 3),
    ("shell", "shell", "结壳量", "", 3),
]

COOK_CODE = {"steam": 0, "bake": 1, "combi": 2}


def key_of(policy: str, cook: str, mm: int) -> str:
    return f"{policy}_{cook}_{mm}"


def run_one(job):
    """Integrate one scenario and return its recorded channels."""
    policy, cook, mm = job
    from acts_mcdt.physics import rollout

    out = rollout(
        length=np.array([mm / 1000.0]),
        proto=np.array([0]),
        t0=np.array([T0_C]),
        m0=np.array([M0]),
        hetero=np.array([0]),
        seed=np.array([float(SEED)]),
        policy=policy,
        minutes=MINUTES,
        dt=DT,
        record_every=RECORD_EVERY,
        cook=cook,
        generation="display",
        n=CELLS,
        store_field=True,
    )
    channels = {name: np.asarray(out[src][:, 0], dtype=np.float64)
                for name, src, *_ in CHANNELS}
    channels["nodes"] = np.asarray(out["t_field"][:, 0, :], dtype=np.float64)
    channels["mNodes"] = np.asarray(out["m_field"][:, 0, :], dtype=np.float64)
    meta = {
        "stop": float(out["stop"][0]),
        "eAlpha": float(out["e_alpha"][0]),
        "alphaAtStop": float(out["alpha_at_stop"][0]),
        "energy": float(out["energy"][0]),
        "finalVar": float(out["final_var"][0]),
    }
    return key_of(policy, cook, mm), channels, meta


def quantise_specs(values: np.ndarray, digits: int) -> dict:
    lo = float(np.nanmin(values))
    hi = float(np.nanmax(values))
    if hi - lo < 1e-9:
        hi = lo + 1e-6
    span = hi - lo
    return {"min": round(lo, digits), "max": round(hi, digits),
            "offset": lo, "scale": span / QMAX}


def pack(values: np.ndarray, spec: dict) -> np.ndarray:
    q = np.rint((np.asarray(values, dtype=np.float64) - spec["offset"]) / spec["scale"])
    return np.clip(q, 0, QMAX).astype(np.int16)


def metrics_of(channels: dict, meta: dict) -> dict:
    t = channels["time"]
    alpha = channels["alpha"]
    var = channels["varR"]
    mode = channels["mode"]
    stop_idx = int(np.argmin(np.abs(t - meta["stop"])))
    over = np.flatnonzero(alpha >= DESIGN_LINE)
    drop = np.flatnonzero(var < 0.3)
    probe = np.flatnonzero((t >= PROBE[0]) & (t < PROBE[1]))
    hold = np.flatnonzero(mode >= 1.5)
    return {
        "stopS": round(meta["stop"], 1),
        "eAlpha": round(meta["eAlpha"], 4),
        "alphaAtStop": round(meta["alphaAtStop"], 4),
        "energy": round(meta["energy"], 1),
        "finalVar": round(meta["finalVar"], 4),
        "rHatEnd": round(float(channels["rHat"][-1]), 3),
        "rProxyEnd": round(float(channels["rProxy"][-1]), 3),
        "peakSurf": round(float(np.max(channels["tSurf"])), 1),
        "coreAtStop": round(float(channels["tCore"][stop_idx]), 1),
        "surfAtStop": round(float(channels["tSurf"][stop_idx]), 1),
        "alphaEnd": round(float(alpha[-1]), 4),
        "probed": bool(meta["finalVar"] < 0.3),
        "firstOver85": round(float(t[over[0]]), 1) if over.size else None,
        "varDropS": round(float(t[drop[0]]), 1) if drop.size else None,
        "probeS": round(float(t[probe[0]]), 1) if probe.size else None,
        "holdS": round(float(t[hold[0]]), 1) if hold.size else None,
    }


def build_surfaces() -> dict:
    src = json.loads((LOG / "surface_xl.json").read_text(encoding="utf-8"))
    policies = src["policies"]
    lengths = src["lengths_mm"]
    half = lengths[::2]
    layout = {
        "LT": ("t0C", "t0", lengths, src["temps_c"]),
        "LM": ("moisture", "m0", half, src["moistures"]),
        "LH": ("hetero", "hetero", lengths, [0, 1, 2]),
        "LC": ("cook", "cook", half, ["steam", "bake", "combi"]),
    }
    grids = {}
    for kind, (third, field, row_axis, col_axis) in layout.items():
        table = {}
        for r in src["cells"]:
            if r["kind"] == kind:
                table[(r["policy"], r["length_mm"], r[field])] = r
        series = []
        for p in policies:
            lines = []
            for x in row_axis:
                line = []
                for y in col_axis:
                    r = table.get((p, x, y))
                    line.append(None if r is None else [
                        round(r["e"]["p50"], 3),
                        round(r["stop"]["p50"], 1),
                        round(r["energy"]["p50"], 1),
                        round(r["e"]["std"], 3),
                    ])
                lines.append(line)
            series.append({"policy": p, "rows": lines})
        grids[kind] = {"second": "lengthMm", "third": third,
                       "secondAxis": row_axis, "thirdAxis": col_axis, "series": series}
    deep = [{"policy": r["policy"], "lengthMm": r["length_mm"], "hetero": r["hetero"],
             "eP05": r["e"]["p05"], "eP50": r["e"]["p50"], "eP95": r["e"]["p95"],
             "stopP50": r["stop"]["p50"], "energyP50": r["energy"]["p50"]}
            for r in src["cells"] if r["kind"] == "DEEP"]
    return {
        "generation": "baseline",
        "source": "results/logs/surface_xl.json",
        "seedsPerCell": src["seeds_per_cell"],
        "policies": policies,
        "metricOrder": ["eMedian", "stopMedian", "energyMedian", "eStd"],
        "grids": grids,
        "deep": deep,
        "note": "e 为停止时刻进度减 0.85；停机中位数 3300 s 表示被时域终点截住。",
    }


def write_contract(manifest: dict) -> None:
    default = next(s for s in manifest["scenarios"]
                   if s["key"] == f"{manifest['defaults']['policy']}_"
                   f"{manifest['defaults']['cook']}_{manifest['defaults']['lengthMm']}")
    from acts_mcdt.physics import BASELINE, DISPLAY

    display = dict(DISPLAY)
    baseline = dict(BASELINE)
    contract = {
        "kind": "demo dataset contract",
        "schema_version": 2,
        "purpose": (
            "声明浏览器回放是什么、由哪一代数值核写出、哪些结论只能按模型判据读。"
            "页面必须显示回放模式、代际与来源，使预计算轨迹不被误读为实时测量。"
        ),
        "mode": {
            "id": "offline-replay",
            "label_zh": "离线轨迹回放",
            "label_en": "offline replay",
            "statement_zh": "页面读取已写盘的轨迹数组，不在浏览器内重跑积分；显示的一切都是预计算仿真结果，不含真实设备测量。",
            "is_live": False,
            "is_measurement": False,
        },
        "kernel": {
            "generation": "display",
            "why": manifest["generationNote"],
            "switches": {"display": display, "baseline": baseline},
            "differing_switches": sorted(k for k in display if display[k] != baseline.get(k)),
        },
        "sampling": manifest["sampling"],
        "default_scenario": {
            "key": default["key"], "seed": SEED, "prototype": "mince",
            "length_m": default["lengthMm"] / 1000.0, "t0_c": T0_C, "m0": M0,
        },
        "scenarios": {s["key"]: {"policy": s["policy"], "cook_mode": s["cook"],
                                 "length_mm": s["lengthMm"], "metrics": s["metrics"]}
                      for s in manifest["scenarios"]},
        "fingerprints": {s["key"]: s["fingerprint"] for s in manifest["scenarios"]},
        "files": {"manifest": "data/manifest.json", "traces": "data/traces.bin",
                  "surfaces": "data/surfaces.json"},
        "provenance": manifest["provenance"],
        "boundaries": manifest["boundaries"],
        "expected_summary": {
            "key": default["key"],
            "stop_s": default["metrics"]["stopS"],
            "e_alpha": default["metrics"]["eAlpha"],
            "tolerance": 1e-3,
        },
    }
    (PUBLIC / "dataset.json").write_text(
        json.dumps(contract, ensure_ascii=False, indent=1), encoding="utf-8")


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    jobs = [(p, c, mm) for p in POLICIES for c in COOKS for mm in LENGTHS_MM]
    workers = max(1, min(16, (os.cpu_count() or 4) - 2))
    print(f"scenarios={len(jobs)} workers={workers}", flush=True)
    runs: dict[str, tuple[dict, dict]] = {}
    with ProcessPoolExecutor(max_workers=workers) as pool:
        for i, (key, channels, meta) in enumerate(pool.map(run_one, jobs), 1):
            runs[key] = (channels, meta)
            if i % 15 == 0 or i == len(jobs):
                print(f"  {i}/{len(jobs)}", flush=True)

    specs = []
    for name, _src, label, unit, digits in CHANNELS:
        stacked = np.concatenate([runs[k][0][name] for k in runs])
        spec = quantise_specs(stacked, digits)
        specs.append({"key": name, "label": label, "unit": unit, "digits": digits, **spec})
    field_spec = quantise_specs(np.concatenate([runs[k][0]["nodes"].reshape(-1) for k in runs]), 2)
    field_spec.update({"key": "nodes", "label": "厚度方向温度场", "unit": "°C", "cells": CELLS})

    blocks = []
    scenarios = []
    cursor = 0
    for policy, cook, mm in jobs:
        key = key_of(policy, cook, mm)
        channels, meta = runs[key]
        block = np.empty((len(channels["time"]), len(specs) + CELLS), dtype=np.int16)
        for j, spec in enumerate(specs):
            block[:, j] = pack(channels[spec["key"]], spec)
        block[:, len(specs):] = pack(channels["nodes"].reshape(-1, CELLS), field_spec)
        blocks.append(block)
        scenarios.append({
            "key": key, "policy": policy, "policyLabel": POLICY_LABEL[policy],
            "cook": cook, "cookLabel": COOK_LABEL[cook], "lengthMm": mm,
            "frames": int(block.shape[0]), "start": cursor,
            "metrics": metrics_of(channels, meta),
            "fingerprint": hashlib.sha256(block.tobytes()).hexdigest()[:16],
        })
        cursor += block.shape[0]

    blob = np.concatenate(blocks, axis=0)
    (OUT / "traces.bin").write_bytes(blob.tobytes())
    surfaces = build_surfaces()
    (OUT / "surfaces.json").write_text(
        json.dumps(surfaces, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")

    manifest = {
        "schema": "acts-demo/2",
        "generation": "display",
        "generationNote": (
            "回放来自 display 代际：腔温腔湿积分、Antoine 蒸汽压驱动、结壳反馈开启；"
            "论文主表使用 baseline 代际，两者在同一格子上可差 0.2 以上。参数面来自 baseline，两处不可混读。"
        ),
        "product": "肉糜 · 初始 8 °C · 含水 0.72 · 种子 7",
        "field": field_spec,
        "channels": specs,
        "sampling": {
            "dtS": DT, "recordEvery": RECORD_EVERY, "frameS": DT * RECORD_EVERY,
            "minutes": MINUTES, "framesPerScenario": cursor // len(jobs),
            "scenarios": len(jobs), "frames": cursor, "cells": CELLS,
        },
        "probeWindow": list(PROBE),
        "designLine": DESIGN_LINE,
        "modeLabel": list(MODE_LABEL),
        "cooks": [{"key": c, "label": COOK_LABEL[c]} for c in COOKS],
        "lengthsMm": list(LENGTHS_MM),
        "policies": [{"key": p, "label": POLICY_LABEL[p], "note": POLICY_NOTE[p]} for p in POLICIES],
        "defaults": {"policy": "dual", "cook": "combi", "lengthMm": 30},
        "scenarios": scenarios,
        "surfaces": {"file": "data/surfaces.json", "generation": "baseline",
                     "note": surfaces["note"]},
        "provenance": {
            "generator": "scripts/build_demo_dataset.py",
            "kernel": "src/acts_mcdt/physics.py :: rollout(generation='display')",
            "surfaceSource": "results/logs/surface_xl.json (baseline, 48 seeds/cell)",
            "manifest": "results/logs/MANIFEST.json",
        },
        "boundaries": [
            {"id": "r_proxy", "severity": "info",
             "zh": "跟踪器的 r 是滞后倍数代理量，由表面与冷点的真值温差反解，不是可直接安装的传感器读数。",
             "where": "热阻读数、探针环节"},
            {"id": "steam_clip", "severity": "warning",
             "zh": "display 代际的蒸汽压驱动裁在 ±0.4 bar，约 60% 的步数贴边；依赖蒸汽压差符号的结论只按符号读。",
             "where": "路径 A/B/C、蒸汽指令"},
            {"id": "moisture_dead_axis", "severity": "warning",
             "zh": "家用工况初始含水落在活度饱和段，界面潜热对它的偏导接近零，含水在当前场景是无效参数轴。",
             "where": "含水读数、参数敏感性"},
            {"id": "design_line", "severity": "critical",
             "zh": "α = 0.85 是模型设计判据，定义停机偏差 e_α 的零点，不是认证食品安全阈值；模型不含微生物初始数量。",
             "where": "设计线、停机判据"},
            {"id": "applicability", "severity": "info",
             "zh": "适用工况为家用一体机、55 min 时域、厚度 10–60 mm；超出范围的外推未经检验。",
             "where": "全页"},
        ],
        "expected": {"dual_combi_30": {"stopS": 1866.0, "eAlpha": 0.145, "tol": 0.002}},
    }
    (OUT / "manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=1), encoding="utf-8")
    write_contract(manifest)

    default = next(s for s in scenarios if s["key"] == "dual_combi_30")
    print(f"wrote traces.bin {(OUT / 'traces.bin').stat().st_size / 1e6:.2f} MB")
    print(f"wrote surfaces.json {(OUT / 'surfaces.json').stat().st_size / 1e6:.2f} MB")
    print(f"frames {cursor} scenarios {len(jobs)} channels {len(specs)}+{CELLS}")
    print(f"dual_combi_30 stop {default['metrics']['stopS']} e_alpha {default['metrics']['eAlpha']}")


if __name__ == "__main__":
    main()

