import unittest

from acts_mcdt.propositions import cold_spot_bound, pulse_rank, shield_domain, steady_sensitivity


class PropositionTests(unittest.TestCase):
    def test_steady(self):
        self.assertTrue(steady_sensitivity()["passed"])

    def test_pulse(self):
        self.assertTrue(pulse_rank()["passed"])

    def test_budget(self):
        self.assertTrue(cold_spot_bound()["passed"])

    def test_shield(self):
        self.assertTrue(shield_domain()["passed"])


if __name__ == "__main__":
    unittest.main()
