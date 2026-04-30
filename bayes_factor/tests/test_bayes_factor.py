import unittest
from bayes_factor import BayesFactor

class TestBayesFactor(unittest.TestCase):

    def setUp(self):
        #Fixture for shared setup pattern
        self.n = 10
        self.k = 5
        self.bf = BayesFactor(self.n, self.k)

    # --------input and state validation-------------

    def test_reject_non_integer_n(self):
        with self.assertRaises(TypeError) as context:
            BayesFactor(10.5, 5)
        self.assertEqual(str(context.exception), "n and k must be integers")
    
    def test_reject_non_integer_string_n(self):
        with self.assertRaises(TypeError) as context:
            BayesFactor('10.5', 5)
        self.assertEqual(str(context.exception), "n and k must be integers")

    def test_reject_non_integer_k(self):
        with self.assertRaises(TypeError) as context:
            BayesFactor(10, 5.5)
        self.assertEqual(str(context.exception), "n and k must be integers")
    
    def test_reject_bool_n(self):
        with self.assertRaises(TypeError) as context:
            BayesFactor(True, 1)
        self.assertEqual(str(context.exception), "n and k must be integers")

    def test_reject_bool_k(self):
        with self.assertRaises(TypeError) as context:
            BayesFactor(1, False)
        self.assertEqual(str(context.exception), "n and k must be integers")

    def test_reject_negative_counts_n(self):
        with self.assertRaises(ValueError) as context:
            BayesFactor(-10, 5)
        self.assertEqual(str(context.exception), "n and k cannot be negative")
    
    def test_reject_negative_counts_k(self):
        with self.assertRaises(ValueError) as context:
            BayesFactor(5, -10)
        self.assertEqual(str(context.exception), "n and k cannot be negative")

    def test_invalid_theta_raises_value_error(self):
        # Checks that the right exception type is raised
        with self.assertRaises(ValueError) as context:
            self.bf.likelihood(1.5)
        self.assertEqual(str(context.exception), "theta must be between 0 and 1")

    def test_invalid_theta_type_error(self):
        with self.assertRaises(TypeError) as context:
            self.bf.likelihood("RawrXD")
        self.assertEqual(str(context.exception), "theta must be a number")

    # k > n impossible test
    def test_reject_impossible_binomial_state(self):
        with self.assertRaises(ValueError) as context:
            BayesFactor(5, 10)
        self.assertEqual(str(context.exception), "k cannot be greater than n (impossible binomial state)")
    
    # a > b
    def test_invalid_priors_bound_handled(self):
        with self.assertRaises(ValueError) as context:
            BayesFactor(10, 5, a=0.6, b=0.4)
        self.assertEqual(str(context.exception), "Parameter 'a' must be strictly less than 'b'")

    def test_object_state_consistent(self):
        self.assertEqual(self.bf.n, 10)
        self.assertEqual(self.bf.k, 5)

    # ------------API behavior and return contracts-------------

    def test_api_methods_exist_and_callable(self):
        methods = ['likelihood', 'evidence_slab', 'evidence_spike', 'bayes_factor']
        for m in methods:
          is_callable = callable(getattr(self.bf, m, None))
          self.assertTrue(
              is_callable, 
              f"Required method '{m}' is missing or is not callable!")

    def test_default_prior_bounds(self):
        self.assertAlmostEqual(self.bf.a, 0.4999)
        self.assertAlmostEqual(self.bf.b, 0.5001)

    # ---------- unit tests  ----------------

    def test_likelihood_returns_float(self):
        self.assertIsInstance(self.bf.likelihood(0.5), float)
    
    def test_evidence_slab_returns_float(self):
        self.assertIsInstance(self.bf.evidence_slab(), float)
    
    def test_evidence_spike_returns_float(self):
        self.assertIsInstance(self.bf.evidence_spike(), float)

    def test_bayes_factor_returns_float(self):
        self.assertIsInstance(self.bf.bayes_factor(), float)

    # ----------Math consistency checks ----------------

    def test_likelihood_at_extreme_points(self):
        # using extreme params n=10, k=5, likelihood should evaluate to exactly 0
        self.assertEqual(self.bf.likelihood(0.0), 0.0)
        self.assertEqual(self.bf.likelihood(1.0), 0.0)

    def test_bayes_factor_equal_priors_smoke_test(self):
        # BF = 1 test
        bf_equal = BayesFactor(10, 5, a=0.0, b=1.0)
        self.assertAlmostEqual(bf_equal.bayes_factor(), 1.0, places=5)

    def test_evidence_non_negative(self):
        self.assertGreaterEqual(self.bf.evidence_slab(), 0.0)
        self.assertGreaterEqual(self.bf.evidence_spike(), 0.0)

    def test_likelihood_at_zero_data(self):
        # n=0, k=0 aka no data, likelihood should be 1.0 for any theta
        bf_empty = BayesFactor(0, 0)
        self.assertEqual(bf_empty.likelihood(0.0), 1.0)
        self.assertEqual(bf_empty.likelihood(0.5), 1.0)
        self.assertEqual(bf_empty.likelihood(1.0), 1.0)

    # ---------TDD quality -----------------
    
    # intentional since BayesFactor can't be negative
    @unittest.expectedFailure
    def test_intentionally_failing_test(self):
        bf = BayesFactor(10, 5, a=0.4, b=0.6)
        self.assertLess(bf.bayes_factor(), 0, "intentionally failing: Bayes factor cannot be negative :P")
   
    # ---------- integration tests ----------

    # test Spike is favored when success rate is exactly 0.5
    def test_bayes_factor_favors_spike_at_perfect_half(self):
        # Using the fixture setup (n=10, k=5)
        bf_value = self.bf.bayes_factor()
        # The Bayes Factor should strongly favor H1 (Spike)
        self.assertGreater(bf_value, 1.0)
        
    
    #Slab is favored when k=0 because Spike expects ~50%
    # BF < 1 means the Slab (H0) is more likely than the Spike (H1)
    def test_bayes_factor_favors_slab_at_zero_successes(self):
        bf_zero = BayesFactor(n=10, k=0)
        self.assertLess(bf_zero.bayes_factor(), 1.0)

# run test
if __name__ == '__main__':
    unittest.main()