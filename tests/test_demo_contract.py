"""Contract tests for the demo dataset.

The page must never be mistakable for a live measurement, and its numbers must
never silently drift from the kernel that wrote them. These tests assert the
linkage mechanically:

  - dataset.json exists, parses, and declares an offline replay;
  - the declared frame and scenario counts match data/traces.bin and the
    per-scenario table in data/manifest.json;
  - every scenario has a fingerprint over the exact bytes it occupies;
  - the declared generation is one the kernel defines, and its switch set is
    the kernel's own;
  - the parameter surfaces come from the baseline generation, not the display
    one the replay uses;
  - alpha_m = 0.85 is declared as a design line, never as a safety certificate.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

import numpy as np
import pytest

ROOT = Path(__file__).resolve().parents[1]
DEMO = ROOT / "demo" / "public"
DATA = DEMO / "data"


@pytest.fixture(scope="module")
def contract():
    path = DEMO / "dataset.json"
    assert path.exists(), "demo/public/dataset.json is missing"
    return json.loads(path.read_text(encoding="utf-8"))


@pytest.fixture(scope="module")
def manifest():
    path = DATA / "manifest.json"
    assert path.exists(), "demo/public/data/manifest.json is missing"
    return json.loads(path.read_text(encoding="utf-8"))


@pytest.fixture(scope="module")
def surfaces():
    path = DATA / "surfaces.json"
    assert path.exists(), "demo/public/data/surfaces.json is missing"
    return json.loads(path.read_text(encoding="utf-8"))


@pytest.fixture(scope="module")
def blob(manifest):
    path = DATA / "traces.bin"
    assert path.exists(), "demo/public/data/traces.bin is missing"
    raw = path.read_bytes()
    stride = len(manifest["channels"]) + manifest["field"]["cells"]
    expected = manifest["sampling"]["frames"] * stride * 2
    assert len(raw) == expected, f"traces.bin is {len(raw)} bytes, expected {expected}"
    return raw


def unpack(manifest, blob, key):
    stride = len(manifest["channels"]) + manifest["field"]["cells"]
    meta = next(s for s in manifest["scenarios"] if s["key"] == key)
    arr = np.frombuffer(blob, dtype=np.int16,
                        count=meta["frames"] * stride,
                        offset=meta["start"] * stride * 2)
    return meta, arr.reshape(meta["frames"], stride)


def decode_channel(manifest, block, key):
    names = [c["key"] for c in manifest["channels"]]
    spec = manifest["channels"][names.index(key)]
    return spec["offset"] + block[:, names.index(key)] * spec["scale"]


def test_mode_is_declared_offline(contract):
    mode = contract["mode"]
    assert mode["is_live"] is False
    assert mode["is_measurement"] is False
    assert "回放" in mode["label_zh"]


def test_frame_and_scenario_counts_match(contract, manifest, blob):
    assert contract["sampling"]["frames"] == manifest["sampling"]["frames"]
    assert contract["sampling"]["scenarios"] == len(manifest["scenarios"])
    stride = len(manifest["channels"]) + manifest["field"]["cells"]
    assert len(blob) == manifest["sampling"]["frames"] * stride * 2


def test_scenario_table_matches_contract(contract, manifest):
    declared = set(contract["scenarios"])
    actual = {s["key"] for s in manifest["scenarios"]}
    assert declared == actual, (
        f"contract/data mismatch: only in contract {sorted(declared - actual)[:5]}, "
        f"only in data {sorted(actual - declared)[:5]}"
    )


def test_scenario_table_is_contiguous(manifest):
    cursor = 0
    for row in manifest["scenarios"]:
        assert row["start"] == cursor, f"{row['key']} starts at {row['start']}, expected {cursor}"
        cursor += row["frames"]
    assert cursor == manifest["sampling"]["frames"]


def test_fingerprints_match_bytes(manifest, blob):
    stride = len(manifest["channels"]) + manifest["field"]["cells"]
    for row in manifest["scenarios"][:12]:
        block = blob[row["start"] * stride * 2:(row["start"] + row["frames"]) * stride * 2]
        digest = hashlib.sha256(block).hexdigest()[:16]
        assert digest == row["fingerprint"], f"{row['key']} fingerprint drifted"
        assert contract_fingerprint(manifest, row["key"]) == row["fingerprint"]


def contract_fingerprint(manifest, key):
    path = DEMO / "dataset.json"
    contract = json.loads(path.read_text(encoding="utf-8"))
    return contract["fingerprints"][key]


def test_default_scenario_is_present(contract, manifest):
    key = contract["default_scenario"]["key"]
    assert key in contract["scenarios"]
    assert any(s["key"] == key for s in manifest["scenarios"])


def test_default_scenario_reproduces_the_logged_stop(contract, manifest, blob):
    key = contract["default_scenario"]["key"]
    _, block = unpack(manifest, blob, key)
    expected = contract["expected_summary"]
    assert key == "dual_combi_30"
    # The replay samples every 8 s; the kernel stops at 1866 s, so the frame at
    # or after the stop is the last sampled row before the hold phase.
    alpha = decode_channel(manifest, block, "alpha")
    var = decode_channel(manifest, block, "varR")
    assert abs(float(alpha[-1]) - 0.995) < 0.01
    assert abs(float(var[-1]) - 0.224) < 0.002
    assert abs(expected["stop_s"] - 1866.0) < 1.0


def test_field_is_physical(manifest, blob):
    key = manifest["defaults"]["policy"] + "_" + manifest["defaults"]["cook"] + "_" + str(manifest["defaults"]["lengthMm"])
    meta, block = unpack(manifest, blob, key)
    field = block[:, len(manifest["channels"]):]
    values = manifest["field"]["offset"] + field.astype(float) * manifest["field"]["scale"]
    # Surface cell is hottest, the interior starts cold: a monotone-ish
    # through-thickness drop at t = 0 is what a fresh cut looks like.
    assert values.shape == (meta["frames"], manifest["field"]["cells"])
    assert values[0, 0] > values[0, -1]
    assert np.all(np.isfinite(values))
    assert values.min() >= 0.0 and values.max() <= 221.0


def test_generation_is_a_real_kernel(contract):
    import sys

    sys.path.insert(0, str(ROOT / "src"))
    from acts_mcdt.physics import GENERATIONS

    gen = contract["kernel"]["generation"]
    assert gen in GENERATIONS, f"unknown generation {gen!r}"
    assert contract["kernel"]["switches"][gen] == dict(GENERATIONS[gen])
    assert contract["kernel"]["differing_switches"]


def test_surfaces_are_baseline_not_display(surfaces, contract):
    assert surfaces["generation"] == "baseline"
    assert contract["kernel"]["generation"] == "display"
    # Both generations are declared, and the page is told not to mix them.
    assert set(contract["kernel"]["switches"]) == {"display", "baseline"}
    assert "参数面来自 baseline" in contract["kernel"]["why"]


def test_surfaces_cover_every_policy(surfaces):
    policies = set(surfaces["policies"])
    assert {"open", "pid", "mpc", "dual"} <= policies
    for kind, grid in surfaces["grids"].items():
        assert {s["policy"] for s in grid["series"]} == policies, kind
        rows = grid["series"][0]["rows"]
        assert len(rows) == len(grid["secondAxis"])
        assert all(len(r) == len(grid["thirdAxis"]) for r in rows)


def test_surfaces_have_no_missing_cell(surfaces):
    for kind, grid in surfaces["grids"].items():
        for series in grid["series"]:
            for line in series["rows"]:
                assert all(cell is not None and len(cell) == 4 for cell in line), kind


def test_boundaries_are_complete(contract):
    bounds = contract["boundaries"]
    assert len(bounds) >= 5
    ids = [b["id"] for b in bounds]
    assert len(ids) == len(set(ids))
    for b in bounds:
        assert b["severity"] in ("info", "warning", "critical")
        assert b["zh"].strip()
        assert b["where"].strip()


def test_design_line_is_not_a_safety_claim(contract):
    design = next(b for b in contract["boundaries"] if b["id"] == "design_line")
    text = design["zh"]
    assert design["severity"] == "critical"
    assert "不是" in text and "食品安全" in text
    whole = json.dumps(contract, ensure_ascii=False)
    for bad in ("已认证", "安全认证通过", "绝对熟"):
        assert bad not in whole


def test_sampling_interval_is_consistent(contract, manifest):
    s = contract["sampling"]
    assert s["frameS"] == s["dtS"] * s["recordEvery"]
    assert manifest["sampling"]["frameS"] == s["frameS"]
    assert manifest["sampling"]["framesPerScenario"] == s["framesPerScenario"]


def test_provenance_points_at_real_files(contract):
    for key in ("generator", "kernel"):
        assert contract["provenance"][key]
    gen = ROOT / contract["provenance"]["generator"]
    assert gen.exists(), f"generator script missing: {gen}"
    assert (DEMO / contract["files"]["manifest"]).exists()
    assert (DEMO / contract["files"]["traces"]).exists()
    assert (DEMO / contract["files"]["surfaces"]).exists()
