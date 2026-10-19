"""Contract tests for the demo dataset.

The audit's P0 requirement is that a viewer can always tell what the page is and
what produced its numbers. That only holds if the contract cannot silently drift
away from the data, so these tests assert the linkage mechanically:

  - dataset.json exists and parses;
  - the declared frame and scenario counts match catalog.json;
  - every catalog key has an entry in the contract;
  - the declared generation is one the kernel actually defines;
  - every boundary has an id, a severity and non-empty text;
  - alpha_m = 0.85 is declared as a design line, never as a safety certificate.
"""
from __future__ import annotations

import json
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
DEMO = ROOT / "demo" / "public"


@pytest.fixture(scope="module")
def contract():
    path = DEMO / "dataset.json"
    assert path.exists(), "demo/public/dataset.json is missing"
    return json.loads(path.read_text(encoding="utf-8"))


@pytest.fixture(scope="module")
def catalog():
    path = DEMO / "catalog.json"
    assert path.exists(), "demo/public/catalog.json is missing"
    return json.loads(path.read_text(encoding="utf-8"))


def test_mode_is_declared_offline(contract):
    mode = contract["mode"]
    assert mode["is_live"] is False
    assert mode["is_measurement"] is False
    assert "回放" in mode["label_zh"]


def test_frame_count_matches_catalog(contract, catalog):
    assert contract["sampling"]["total_frames"] == len(catalog)


def test_scenario_count_matches_catalog(contract, catalog):
    actual = {row["key"] for row in catalog}
    declared = set(contract["scenarios"])
    assert declared == actual, (
        f"contract/data mismatch: only in contract {sorted(declared - actual)[:5]}, "
        f"only in data {sorted(actual - declared)[:5]}"
    )


def test_every_scenario_has_a_fingerprint(contract):
    assert set(contract["fingerprints"]) == set(contract["scenarios"])


def test_generation_is_a_real_kernel(contract):
    import sys

    sys.path.insert(0, str(ROOT / "src"))
    from acts_mcdt.physics import GENERATIONS

    gen = contract["kernel"]["generation"]
    assert gen in GENERATIONS, f"unknown generation {gen!r}"
    # the switches recorded for it must equal the kernel's own definition
    assert contract["kernel"]["switches"][gen] == dict(GENERATIONS[gen])


def test_generation_differs_from_paper_baseline(contract):
    # The page uses display while the paper's main tables use baseline; if that
    # ever stops being true the prose and the badge both need revisiting.
    assert contract["kernel"]["generation"] == "display"
    assert contract["kernel"]["differing_switches"]


def test_boundaries_are_complete(contract):
    bounds = contract["boundaries"]
    assert len(bounds) >= 5
    ids = [b["id"] for b in bounds]
    assert len(ids) == len(set(ids)), "duplicate boundary ids"
    for b in bounds:
        assert b["severity"] in ("info", "warning", "critical")
        assert b["zh"].strip()
        assert b["where"].strip()


def test_design_line_is_not_a_safety_claim(contract):
    design = next(b for b in contract["boundaries"] if b["id"] == "design_line")
    text = design["zh"]
    assert design["severity"] == "critical"
    assert "不是" in text and "食品安全" in text
    # and nothing anywhere claims certification
    whole = json.dumps(contract, ensure_ascii=False)
    for bad in ("已认证", "安全认证通过", "绝对熟"):
        assert bad not in whole


def test_sampling_interval_is_consistent(contract):
    s = contract["sampling"]
    assert s["sample_interval_s"] == s["dt_s"] * s["record_every"]


def test_provenance_points_at_real_files(contract):
    for key in ("generator", "kernel"):
        assert contract["provenance"][key]
    gen = ROOT / contract["provenance"]["generator"]
    assert gen.exists(), f"generator script missing: {gen}"


def test_expected_summary_matches_shipped_summary(contract):
    summary = json.loads((DEMO / "summary.json").read_text(encoding="utf-8"))
    exp = contract["expected_summary"]
    assert abs(summary["stop_s"] - exp["stop_s"]) < 1.0
    assert abs(summary["e_alpha"] - exp["e_alpha"]) < exp["tolerance"] + 1e-6
