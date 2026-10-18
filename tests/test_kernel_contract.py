"""Kernel contract: the two generations must stay reproducible.

These tests are the guard against the defect that motivated the split: a
campaign table silently drifting away from the kernel that produced it.
They are deliberately cheap (no campaign re-run) and they pin:

1. each named generation returns its documented trace,
2. the switch presets are the ones results/logs/MANIFEST.json records,
3. a table may not mix generations: the values ch5 quotes are reachable
   from exactly one generation, and we assert which.
"""

import unittest

import numpy as np

from acts_mcdt.physics import BASELINE, DISPLAY, GENERATIONS, rollout, switches


def one(**kwargs):
    base = dict(length=np.array([0.03]), proto=np.array([0]), t0=np.array([8.0]),
                m0=np.array([0.72]), hetero=np.array([0]), seed=np.array([7.0]),
                policy="dual", minutes=55.0, store_history=False)
    base.update(kwargs)
    return rollout(**base)


def one_traced(**kwargs):
    """Same single case but with the history kept, for trajectory claims."""
    base = dict(length=np.array([0.03]), proto=np.array([0]), t0=np.array([8.0]),
                m0=np.array([0.72]), hetero=np.array([0]), seed=np.array([7.0]),
                policy="dual", minutes=55.0, record_every=4, store_history=True)
    base.update(kwargs)
    return rollout(**base)


class GenerationTests(unittest.TestCase):
    def test_presets_are_distinct(self):
        for key in ("cavity_air", "use_antoine", "shell_k", "moisture_bc", "steam_baseline"):
            self.assertIn(key, BASELINE)
            self.assertIn(key, DISPLAY)
        self.assertNotEqual(BASELINE, DISPLAY)
        self.assertEqual(set(BASELINE), set(DISPLAY))

    def test_switches_helper(self):
        self.assertEqual(switches("baseline"), BASELINE)
        self.assertEqual(switches("display"), DISPLAY)
        mixed = switches("baseline", use_antoine=True)
        self.assertTrue(mixed["use_antoine"])
        self.assertFalse(mixed["cavity_air"])
        with self.assertRaises(ValueError):
            switches("no-such-generation")

    def test_generation_keyword_matches_explicit_switches(self):
        via_keyword = one(generation="display")
        explicit = one(**DISPLAY)
        np.testing.assert_allclose(via_keyword["e_alpha"], explicit["e_alpha"], rtol=0, atol=0)
        np.testing.assert_allclose(via_keyword["stop"], explicit["stop"], rtol=0, atol=0)

    def test_unknown_generation_rejected(self):
        with self.assertRaises(ValueError):
            one(generation="third")


class SeedSevenTests(unittest.TestCase):
    """The seed-7 case is the sharpest witness of the generation split."""

    def test_display_generation_gives_published_trace(self):
        out = one(**DISPLAY)
        self.assertAlmostEqual(float(out["stop"][0]), 1866.0, delta=0.5)
        self.assertAlmostEqual(float(out["e_alpha"][0]), 0.145, delta=5e-3)
        self.assertAlmostEqual(float(out["energy"][0]), 1864.0, delta=1.0)
        self.assertAlmostEqual(float(out["final_var"][0]), 0.224, delta=1e-9)

    def test_baseline_generation_gives_its_own_trace(self):
        out = one()
        self.assertAlmostEqual(float(out["stop"][0]), 1676.0, delta=0.5)
        self.assertAlmostEqual(float(out["e_alpha"][0]), -0.095, delta=5e-3)

    def test_generations_are_not_interchangeable(self):
        a = float(one()["stop"][0])
        b = float(one(**DISPLAY)["stop"][0])
        self.assertGreater(abs(a - b), 100.0)


class BaselineCampaignTests(unittest.TestCase):
    """Spot values the main tables quote, pinned to the baseline."""

    def test_s1_30mm_dual_median(self):
        cases = []
        for t0 in (5.0, 20.0):
            for m0 in (0.64, 0.72, 0.80):
                for hetero in (0, 1, 2):
                    for seed in range(30):
                        cases.append((t0, m0, hetero, seed))
        arr = np.array(cases)
        out = rollout(length=np.full(len(arr), 0.03), proto=np.zeros(len(arr)),
                      t0=arr[:, 0], m0=arr[:, 1], hetero=arr[:, 2],
                      seed=1000.0 + arr[:, 3], policy="dual", minutes=55.0,
                      store_history=False)
        # tab:s1L, 30 mm dual, e50 = -0.080
        self.assertAlmostEqual(float(np.median(out["e_alpha"])), -0.080, delta=2e-3)

    def test_s0_grid_pairing_flips_sign(self):
        args = dict(length=np.array([0.030]), proto=np.array([0]), t0=np.array([5.0]),
                    m0=np.array([0.72]), hetero=np.array([0]), seed=np.array([1000.0]),
                    policy="dual", minutes=55.0, store_history=False)
        fine = float(rollout(n=16, **args)["e_alpha"][0])
        coarse = float(rollout(n=8, **args)["e_alpha"][0])
        self.assertLess(fine, 0.0)
        self.assertGreater(coarse, 0.0)
        self.assertAlmostEqual(coarse - fine, 0.227, delta=5e-3)

    def test_dual_variance_collapses_on_every_s1_row(self):
        """S1 dual ends at 0.224 for 4860/4860 rows, not two thirds."""
        out = rollout(length=np.full(64, 0.03), proto=np.zeros(64),
                      t0=np.full(64, 5.0), m0=np.full(64, 0.72),
                      hetero=np.zeros(64), seed=1000.0 + np.arange(64, dtype=float),
                      policy="dual", minutes=55.0, store_history=False)
        self.assertTrue(np.allclose(out["final_var"], 0.224))

    def test_open_loop_menu_times(self):
        args = dict(proto=np.array([0]), t0=np.array([8.0]), m0=np.array([0.72]),
                    hetero=np.array([0]), seed=np.array([7.0]),
                    policy="open", minutes=55.0, store_history=False)
        for length, want in ((0.015, 900.0), (0.030, 1170.0), (0.050, 1530.0)):
            out = rollout(length=np.array([length]), **args)
            self.assertAlmostEqual(float(out["stop"][0]), want, delta=0.5)


class SwitchIsolationTests(unittest.TestCase):
    """Each switch must either move the trajectory or be provably inert.

    Two switches are inert on their own, and that is a property of the
    mechanism, not a bug: ``cavity_air`` only reaches the food through the
    Antoine drive, and ``shell_k`` only bites once crust has accumulated
    past the surface-moisture threshold. The tests pin the coupling structure
    so that a future edit cannot silently decouple it.
    """

    def test_antoine_drives_the_trajectory(self):
        base = float(one(**BASELINE)["e_alpha"][0])
        moved = float(one(**switches("baseline", use_antoine=True))["e_alpha"][0])
        self.assertGreater(abs(moved - base), 1e-2)

    def test_steam_baseline_drives_the_trajectory(self):
        base = float(one(**BASELINE)["e_alpha"][0])
        moved = float(one(**switches("baseline", steam_baseline=0.15))["e_alpha"][0])
        self.assertGreater(abs(moved - base), 1e-2)

    def test_cavity_air_alone_is_inert(self):
        """cavity_air has no path into the food except through the drive."""
        base = float(one(**BASELINE)["stop"][0])
        alone = float(one(**switches("baseline", cavity_air=True))["stop"][0])
        self.assertAlmostEqual(alone, base, delta=1e-9)

    def test_drive_needs_cavity_state(self):
        """With the cavity node frozen, the drive degenerates to a fixed sink.

        ``cavity_air=False`` freezes cav_h at 0.4 and cav_t at 25 C, so
        ``p_cav`` becomes a constant and the drive collapses to
        ``clip(const - a_w p_food)``. It still moves the trajectory and it
        still flips sign with thickness, but it no longer carries any cavity
        information. Turning the cavity node on restores the exchange.
        """
        frozen = float(one(**switches("baseline", use_antoine=True))["stop"][0])
        live = float(one(**DISPLAY)["stop"][0])
        self.assertGreater(abs(live - frozen), 100.0)

        args = dict(proto=np.array([0]), t0=np.array([8.0]), m0=np.array([0.72]),
                    hetero=np.array([0]), seed=np.array([7.0]), policy="dual",
                    minutes=55.0, store_history=False)
        deltas = []
        for length in (0.015, 0.050):
            on = rollout(length=np.array([length]), **args,
                         **switches("baseline", use_antoine=True))
            off = rollout(length=np.array([length]), **args, **switches("baseline"))
            deltas.append(float(on["e_alpha"][0] - off["e_alpha"][0]))
        # The paper's ch5.8 result: the same vapour term helps a thin piece and
        # hurts a thick one. It must survive with the cavity frozen.
        self.assertGreater(deltas[0], 0.0)
        self.assertLess(deltas[1], 0.0)

    def test_invalid_moisture_bc_rejected(self):
        with self.assertRaises(ValueError):
            one(**switches("baseline", moisture_bc="nonsense"))


class EstimatorTests(unittest.TestCase):
    """The two estimators share channels, seeds and stopping rule."""

    def test_scalar_is_the_default_and_unchanged(self):
        default = one(**DISPLAY)
        explicit = one(**DISPLAY, estimator="scalar")
        np.testing.assert_allclose(default["e_alpha"], explicit["e_alpha"])
        np.testing.assert_allclose(default["stop"], explicit["stop"])

    def test_unknown_estimator_rejected(self):
        with self.assertRaises(ValueError):
            one(**DISPLAY, estimator="kalman")

    def test_ekf_produces_continuous_variance(self):
        """The scalar tracker yields two variance values; the EKF yields many."""
        scalar = one_traced(**DISPLAY)
        ekf = one_traced(**DISPLAY, estimator="ekf")
        n_scalar = len(np.unique(np.round(scalar["var_r"][:, 0], 5)))
        n_ekf = len(np.unique(np.round(ekf["var_r"][:, 0], 5)))
        self.assertEqual(n_scalar, 2)
        self.assertGreater(n_ekf, 10)

    def test_ekf_recovers_thickness_ordering(self):
        """r(15) < r(30) < r(50) must hold for the EKF estimate."""
        finals = []
        for length in (0.015, 0.030, 0.050):
            out = one_traced(**DISPLAY, length=np.array([length]), estimator="ekf")
            finals.append(float(out["r_hat"][-1, 0]))
        self.assertLess(finals[0], finals[1])
        self.assertLess(finals[1], finals[2])

    def test_ekf_stays_inside_the_box(self):
        from acts_mcdt.physics import R_MAX, R_MIN
        for length in (0.015, 0.030, 0.050):
            out = one_traced(**DISPLAY, length=np.array([length]), estimator="ekf")
            r = out["r_hat"][:, 0]
            self.assertTrue(np.all(r >= R_MIN - 1e-9))
            self.assertTrue(np.all(r <= R_MAX + 1e-9))

    def test_ekf_does_not_drag_down_in_the_hold_phase(self):
        """The resistance must not collapse after the probe closes."""
        out = one_traced(**DISPLAY, estimator="ekf")
        r = out["r_hat"][:, 0]
        peak = float(np.max(r))
        self.assertGreater(peak, 5.0)
        self.assertGreater(float(r[-1]), peak * 0.5,
                           "the hold phase dragged r down")


class ProxyCeilingTests(unittest.TestCase):
    """The resistance reference must not be pinned at its ceiling.

    ``r`` is a lag multiplier; fits of the single-lag relation on the field put
    its truth at 8.19 (15 mm) to 10.70 (50 mm) for the dual policy, and up to
    13.79 for the open loop at 50 mm. The old R_MAX = 8.0 therefore saturated
    the reference, and the probe acceptance test compared an update against a
    constant for most of the run.
    """

    def test_box_covers_the_fitted_truth(self):
        from acts_mcdt.physics import R_MAX, R_MIN
        self.assertLess(R_MIN, 8.0)
        self.assertGreater(R_MAX, 14.0)

    def test_reference_is_not_saturated(self):
        from acts_mcdt.physics import R_MAX, R_MIN
        for length in (0.015, 0.030, 0.050):
            out = one_traced(**DISPLAY, length=np.array([length]))
            raw = out["r_true_proxy"][:, 0]
            self.assertLess(float(np.mean(raw >= R_MAX - 1e-9)), 1e-9,
                            f"{length*1000:.0f} mm reference saturates at R_MAX")
            self.assertLess(float(np.mean(raw <= R_MIN + 1e-9)), 1e-9,
                            f"{length*1000:.0f} mm reference saturates at R_MIN")

    def test_fitted_lag_multiplier_matches_the_box(self):
        """Re-derive the truth from the field and check the box contains it."""
        from acts_mcdt.physics import R_MAX, R_MIN

        def fit_tau(surf, core, dt=2.0):
            taus = np.geomspace(20.0, 20000.0, 240)
            prev = core[:-1]
            drv = surf[:-1] - prev
            targets = core[1:]
            best_tau, best = None, np.inf
            for tau in taus:
                err = float(np.mean((prev + dt * drv / tau - targets) ** 2))
                if err < best:
                    best, best_tau = err, tau
            return float(best_tau)

        for length, lo, hi in ((0.015, 7.5, 9.0), (0.030, 8.0, 10.0),
                               (0.050, 9.5, 12.0)):
            out = one_traced(**DISPLAY, length=np.array([length]))
            # one_traced records every 4 steps of 2 s, so the sample spacing is 8 s.
            tau = fit_tau(out["t_surf"][:, 0], out["t_core"][:, 0], dt=8.0)
            r_true = tau / ((length / 0.03) ** 2 * 280.0)
            self.assertGreater(r_true, lo)
            self.assertLess(r_true, hi)
            self.assertGreater(R_MIN, 0.0)
            self.assertLess(r_true, R_MAX)


if __name__ == "__main__":
    unittest.main()
