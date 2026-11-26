"""Focused regressions for the reviewed resampler and mathematical errata."""

import json
from pathlib import Path
import re
import unittest
import warnings

import numpy as np
from scipy.integrate import quad
from scipy.stats import chi2, norm

ROOT = Path(__file__).resolve().parents[1]


def load_resampler(random=None):
    notebook = json.loads((ROOT / "12-Particle-Filters.ipynb").read_text(encoding="utf-8"))
    namespace = {
        "np": np,
        "random": np.random.default_rng(7).random if random is None else random,
    }
    # Deliberately supply no global w: the function must use its argument.
    exec("".join(notebook["cells"][65]["source"]), namespace)
    return namespace["residual_resample"]


class ReviewedNumerics(unittest.TestCase):
    def test_resampling_uses_argument_without_global_weights(self):
        weights = np.array([0.2, 0.3, 0.5])
        before = weights.copy()
        indexes = load_resampler()(weights)
        self.assertEqual(indexes.shape, (3,))
        self.assertTrue(np.issubdtype(indexes.dtype, np.integer))
        self.assertTrue(np.all((indexes >= 0) & (indexes < 3)))
        np.testing.assert_array_equal(weights, before)

    def test_exact_copies_need_no_random_draw_or_normalization(self):
        def no_draw(_):
            raise AssertionError("deterministic copies need no random draw")

        resample = load_resampler(no_draw)
        with warnings.catch_warnings():
            warnings.simplefilter("error", RuntimeWarning)
            np.testing.assert_array_equal(resample([0.25] * 4), [0, 1, 2, 3])
            np.testing.assert_array_equal(resample([0.0, 0.0, 1.0]), [2, 2, 2])
            np.testing.assert_array_equal(resample([1.0]), [0])
            self.assertEqual(len(resample([])), 0)

    def test_residual_draws_reproduce_expected_offspring_counts(self):
        # One remaining draw has probabilities .3, .3, .4; two copies of
        # particle 2 are deterministic. The former source code always chose 2.
        resample = load_resampler()
        counts = np.zeros(3)
        for _ in range(12000):
            counts += np.bincount(resample([0.1, 0.1, 0.8]), minlength=3)
        np.testing.assert_allclose(counts / 12000, [0.3, 0.3, 2.4], atol=0.025, rtol=0)

    def test_zero_random_draw_skips_zero_probability_particle(self):
        indexes = load_resampler(lambda n: np.zeros(n))([0.0, 0.5, 0.5])
        self.assertNotIn(0, indexes)
        np.testing.assert_array_equal(indexes, [1, 2, 1])

    def test_documented_filterpy_import_executes(self):
        notebook = json.loads((ROOT / "12-Particle-Filters.ipynb").read_text(encoding="utf-8"))
        snippet = re.search(r"```python\n(.*?)```", "".join(notebook["cells"][63]["source"]), re.S).group(1)
        namespace = {}
        exec(snippet, namespace)
        self.assertTrue(callable(namespace["multinomial_resample"]))

    def test_gaussian_sum_convolution_matches_stated_distribution(self):
        for mu_p, var_p, mu_z, var_z in [(1.2, 2.3, -0.7, 0.4), (-3, 0.5, 4, 6)]:
            for x in (-2, 0, 3):
                integrated, _ = quad(
                    lambda z: norm.pdf(x - z, mu_p, np.sqrt(var_p))
                    * norm.pdf(z, mu_z, np.sqrt(var_z)),
                    -np.inf,
                    np.inf,
                )
                expected = norm.pdf(x, mu_p + mu_z, np.sqrt(var_p + var_z))
                self.assertAlmostEqual(integrated, expected, places=10)
                total = var_p + var_z
                v = var_p * var_z / total
                mean_z = (var_z * (x - mu_p) + var_p * mu_z) / total
                for z in (-1, 0, 2):
                    product = norm.pdf(x-z, mu_p, np.sqrt(var_p)) * norm.pdf(z, mu_z, np.sqrt(var_z))
                    factored = expected * norm.pdf(z, mean_z, np.sqrt(v))
                    self.assertAlmostEqual(product, factored, places=12)

    def test_covariance_population_and_sample_denominators(self):
        data = np.array([[1.8, 2.0, 1.7, 1.9, 1.6], [70.1, 91.2, 59.5, 93.2, 53.5]])
        population = np.cov(data, bias=True)
        sample = np.cov(data)
        self.assertAlmostEqual(population[0, 0], 0.02)
        self.assertAlmostEqual(population[1, 1], 261.788)
        np.testing.assert_allclose(sample, population * 5 / 4)

    def test_multidimensional_standard_deviation_coverage(self):
        self.assertAlmostEqual(chi2.cdf(4, df=2), 0.8646647168)
        self.assertAlmostEqual(chi2.cdf(9, df=3), 0.9707091135)
        self.assertGreater(norm.cdf(3) - norm.cdf(-3), 0.997)

    def test_bayes_evidence_uses_likelihood_times_prior(self):
        prior = np.array([0.2, 0.8])
        likelihood = np.array([0.75, 0.25])
        evidence = np.dot(prior, likelihood)
        self.assertAlmostEqual(evidence, 0.35)
        np.testing.assert_allclose(prior * likelihood / evidence, [3/7, 4/7])


if __name__ == "__main__":
    unittest.main(verbosity=2)
