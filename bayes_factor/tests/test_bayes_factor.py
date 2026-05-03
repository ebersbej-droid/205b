import unittest
from bayes_factor import BayesFactor

class TestBayesFactor(unittest.TestCase):

    def setUp(self):
        #Fixture for shared setup pattern
        self.a = 0.4999 
        self.b = 0.5001
        self.n = 10
        self.k = 5
        self.bf = BayesFactor(self.n, self.k)

    # --------input and state validation-------------
    
    # Verify TypeError and specific message for non-integer n & k

    def test_reject_non_integer_n(self):
        # float error for n
        with self.assertRaises(TypeError) as context:
            BayesFactor(10.5, 5)
        self.assertEqual(str(context.exception), "n must be an integer")
    
    def test_reject_non_integer_string_n(self):
        # string error for n
        with self.assertRaises(TypeError) as context:
            BayesFactor('10.5', 5)
        self.assertEqual(str(context.exception), "n must be an integer")
    
    def test_reject_bool_n(self):
        # boolean error for n (added bool checks since python treats them as ints)
        with self.assertRaises(TypeError) as context:
            BayesFactor(True, 1)
        self.assertEqual(str(context.exception), "n must be an integer")
    
    def test_reject_non_integer_k(self):
        # float error for k
        with self.assertRaises(TypeError) as context:
            BayesFactor(10, 5.5)
        self.assertEqual(str(context.exception), "k must be an integer")

    def test_reject_bool_k(self):
        # boolean error for k
        with self.assertRaises(TypeError) as context:
            BayesFactor(1, False)
        self.assertEqual(str(context.exception), "k must be an integer")

    # Verify TypeError and specific message for negative n & k values

    def test_reject_negative_counts_n(self):
        # negative value error for n
        with self.assertRaises(ValueError) as context:
            BayesFactor(-10, 5)
        self.assertEqual(str(context.exception), "n cannot be negative")
    
    def test_reject_negative_counts_k(self):
        # negative value error for k
        with self.assertRaises(ValueError) as context:
            BayesFactor(5, -10)
        self.assertEqual(str(context.exception), "k cannot be negative")

    # checking theta now for input errors and error messages

    def test_invalid_theta_raises_value_error(self):
        # Checks that the right exception type is raised for theta
        with self.assertRaises(ValueError) as context:
            self.bf.likelihood(1.5)
        self.assertEqual(str(context.exception), "theta must be between 0 and 1")

    def test_invalid_theta_type_error(self):
        # string error for theta
        with self.assertRaises(TypeError) as context:
            self.bf.likelihood("RawrXD")
        self.assertEqual(str(context.exception), "theta must be a number")

    # Parameter checks

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
    
    # If we instead raise an error for edge cases rather than setting to 'inf'

    # def test_bayes_factor_undefined_when_slab_is_zero(self):
    #     # edge case test: if slab evidence is 0, Bayes Factor is undefined
    #     bf = BayesFactor(0, 0, a=0.0, b=0.0) 
    #     with self.assertRaises(ValueError) as context:
    #         bf.bayes_factor()
    #     self.assertEqual(str(context.exception), "Slab evidence is zero; Bayes Factor is undefined")
        
    # value(s) consistency test

    def test_object_state_consistent(self):
        # making sure n & k weren't altered
        self.assertEqual(self.bf.n, 10)
        self.assertEqual(self.bf.k, 5)

    # ------------API behavior and return contracts-------------

    def test_api_methods_exist_and_callable(self):
        # make sure that all required API methods are present
        methods = ['likelihood', 'evidence_slab', 'evidence_spike', 'bayes_factor']
        for m in methods:
            is_callable = callable(getattr(self.bf, m, None))
            self.assertTrue(is_callable, f"Required method '{m}' is missing or is not callable!")

    def test_default_prior_bounds(self):
        # checking prior boundaries
        self.assertAlmostEqual(self.bf.a, 0.4999)
        self.assertAlmostEqual(self.bf.b, 0.5001)

    # ---------- unit tests  ----------------

    def test_likelihood_returns_float(self):
        # check likelihood is a float
        self.assertIsInstance(self.bf.likelihood(0.5), float)
    
    def test_evidence_slab_returns_float(self):
        # check slab evidence is a float
        self.assertIsInstance(self.bf.evidence_slab(), float)
    
    def test_evidence_spike_returns_float(self):
        # check spike evidence is a float
        self.assertIsInstance(self.bf.evidence_spike(), float)

    def test_bayes_factor_returns_float(self):
        # check Bayes factor is a float
        self.assertIsInstance(self.bf.bayes_factor(), float)

    # ----------Math consistency checks ----------------

    def test_likelihood_at_extreme_points(self):
        # if theta=0 you can't have any successes, and if theta=1 you can't have any failures
        # soooo likelihood has to be 0, for k not equal to 0 or n, 
        # likelihood is 0 at θ=0 and θ=1 (specifically for our n=10, k=5 fixture)
        
        self.assertAlmostEqual(self.bf.likelihood(0.0), 0.0, places=10)
        self.assertAlmostEqual(self.bf.likelihood(1.0), 0.0, places = 10)

        # since I switched from math.comb to binom.pmf
        # I know at larger n's that I can get a extremely small value
        # so I changed to AlmostEqual fo small float comparisons
        # self.assertEqual(self.bf.likelihood(0.0), 0.0)
        # self.assertEqual(self.bf.likelihood(1.0), 0.0)

    def test_bayes_factor_equals_one_when_priors_identical(self):
        # testing when priors are identical
        bf = BayesFactor(10, 5, a=0.0, b=1.0)
        result = bf.bayes_factor()
        self.assertAlmostEqual(result, 1.0, places=6)
        self.assertNotEqual(result, float('inf')) #edge case check

    def test_bayes_factor_changes_with_data(self):
        # Making sure class even works
        bf1 = BayesFactor(10, 5)
        bf2 = BayesFactor(10, 2)
        self.assertNotEqual(bf1.bayes_factor(), bf2.bayes_factor())

    def test_evidence_non_negative(self):
        # check for negative evidence
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
        bf = BayesFactor(10, 5)
        self.assertLess(bf.bayes_factor(), 0)
   
    # ---------- integration tests ----------
    
    # Test that slab is favored when k=0 because Spike expects ~50%
    # BF < 1 means the Slab (H0) is more likely than the Spike (H1)
    def test_bayes_factor_favors_slab_at_zero_successes(self):
        bf_zero = BayesFactor(n=10, k=0)
        self.assertLess(bf_zero.bayes_factor(), 1.0)

# run test
if __name__ == '__main__':
    unittest.main()