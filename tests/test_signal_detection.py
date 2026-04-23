from signal_detection import SignalDetection
import unittest
import matplotlib.pyplot as plt
from scipy import stats

class TestSignalDetection(unittest.TestCase):

    def setUp(self):
        self.sdtest = SignalDetection(40, 10, 20, 30)
        self.zero_hit_den = SignalDetection(0, 0, 5, 5)
        self.zero_fa_den = SignalDetection(5, 5, 0, 0)
        self.sdt_boundary = SignalDetection(10, 0, 10, 10)

    #------Core SDT Math Tests/Variables--------

    def test_signal_detection_hit_rate(self):
        expected = 40/ (40 + 10) 
        self.assertEqual(self.sdtest.hit_rate(), expected)
     
        
    def test_signal_detection_false_alarm_rate(self):
        expected =  20/ (20 + 30)  
        self.assertEqual(self.sdtest.false_alarm_rate(), expected)

    
    def test_d_prime(self):
        expected = stats.norm.ppf(self.sdtest.hit_rate()) - stats.norm.ppf(self.sdtest.false_alarm_rate())  
        self.assertEqual(self.sdtest.d_prime(), expected)
        
    def test_criterion(self):
        expected = -0.5 * (stats.norm.ppf(self.sdtest.hit_rate()) + stats.norm.ppf(self.sdtest.false_alarm_rate()))  
        self.assertEqual(self.sdtest.criterion(), expected)
    
    # -------Input value validation(s)-------

    # Denominator check

    def test_hit_rate_denominator_zero(self):
        with self.assertRaises(ValueError) as context:
            self.zero_hit_den.hit_rate()
        self.assertEqual( str(context.exception), "Hit rate is undefined: hits + misses = 0")

    def test_false_alarm_rate_denominator_zero(self):       
        with self.assertRaises(ValueError) as context:
            self.zero_fa_den.false_alarm_rate()
        self.assertEqual( str(context.exception), "False alarm rate is undefined: false_alarms + correct_rejections = 0")

    # Check for value/type error

    def test_negative_counts_raise_error(self):
        with self.assertRaises(ValueError):
            SignalDetection(-1, 10, 20, 30)

    def test_non_numeric_types_raise_error(self):
        with self.assertRaises(TypeError):
            SignalDetection("40", 10, 20, 30)

    def test_boundary_rates_raise_error(self):
        with self.assertRaises(ValueError):
            self.sdt_boundary.d_prime()
    

    # ------- operators ------
   
    def test_subtraction(self):
        #setting test variables here
        sd1 = SignalDetection(10, 5, 5, 10)
        sd2 = SignalDetection(20, 10, 10, 20)
        
        #result = sd1 - sd2 -> this was so cool to see that this raised the error for having a negative hit
        result = sd2 - sd1

        # showing elements being subtracted together correctly
        self.assertEqual(result.hits, 10.0)
        self.assertEqual(result.misses, 5.0)
        self.assertEqual(result.false_alarms, 5.0)
        self.assertEqual(result.correct_rejections, 10.0)
 
    def test_addition(self):
        #setting test variables here
        sd1 = SignalDetection(10, 5, 5, 10)
        sd2 = SignalDetection(20, 10, 10, 20)
        result = sd1 + sd2
        # showing elements being combined together correctly
        self.assertEqual(result.hits, 30.0)
        self.assertEqual(result.misses, 15.0)
        self.assertEqual(result.false_alarms, 15.0)
        self.assertEqual(result.correct_rejections, 30.0)
   
    def test_mul(self):
        sd1 = SignalDetection(10, 5, 5, 10)
        result = sd1 * 2.5
        
        self.assertEqual(result.hits, 25.0)
        self.assertEqual(result.misses, 12.5)
        self.assertEqual(result.false_alarms, 12.5)
        self.assertEqual(result.correct_rejections, 25.0)
        self.assertEqual(result.correct_rejections, 25.0)
        
    # ---check mutation----
    
    def test_operator_non_mutation(self):
        sd1 = SignalDetection(10, 5, 5, 10)
        sd2 = SignalDetection(20, 10, 10, 20)
        
        add_res = sd1 + sd2
        sub_res = sd2 - sd1
        mul_res = sd1 * 2

        # Check no overwriting of original variable
        self.assertIsNot(add_res, sd1)
        self.assertIsNot(sub_res, sd1)
        self.assertIsNot(mul_res, sd1)

        # Check that original counts were preserved safely
        self.assertEqual(sd1.hits, 10.0)
        self.assertEqual(sd2.hits, 20.0)

    # ----- Plotting Tests -------

    def test_plot_sdt_returns_objects_and_labels(self):
       
        plt.ioff() # non interactive
        
        fig, ax = self.sdtest.plot_sdt()
        
        # Verify returns are matplotlib objects
        self.assertIsInstance(fig, plt.Figure)
        self.assertIsInstance(ax, plt.Axes)
        
        #  Verify that labels and title match original class
        self.assertEqual(ax.get_xlabel(), 'Decision Variable')
        self.assertEqual(ax.get_ylabel(), 'Probability Density')
        self.assertEqual(ax.get_title(), 'Signal Detection Theory')
        
        # Verify legend keys were established, or rather the label string
        legend_texts = [text.get_text() for text in ax.get_legend().get_texts()]
        self.assertTrue(any("Noise" in label for label in legend_texts))
        
        # Close the plot to avoid memory leaks
        plt.close(fig)

    def test_plot_roc_handles_sequence_and_boundaries(self):
        
        plt.ioff() # non interactive

        # We need a list containing at least one SDT object
        sdt_list = [self.sdtest]
        fig, ax = SignalDetection.plot_roc(sdt_list)
        
        # checking x-label and title
        self.assertEqual(ax.get_xlabel(), 'Hit Rate')
        self.assertEqual(ax.get_title(), 'ROC Curve')
        
        # Verify boundary anchors (0,0) & (1,1)
        # Extract the actual drawn line data
        lines = ax.get_lines()
        self.assertTrue(len(lines) > 0)
        x_data, y_data = lines[0].get_data()
        
        # Check if the list contains the hardcoded 0.0 and 1.0 anchors
        self.assertIn(0.0, x_data)
        self.assertIn(1.0, x_data)
        self.assertIn(0.0, y_data)
        self.assertIn(1.0, y_data)
        
        plt.close(fig)

if __name__ == '__main__':
    unittest.main()