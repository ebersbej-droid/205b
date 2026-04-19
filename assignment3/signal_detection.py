# import packages

import numpy as np
import matplotlib.pyplot as plt
from scipy import stats 
import pandas as pd
import math


# create class

class SignalDetection:
    def __init__(self, hits, misses, false_alarms, correct_rejections):
        self.hits                = self._validate("hits", hits)
        self.misses              = self._validate("misses", misses)
        self.false_alarms        = self._validate("false_alarms", false_alarms)
        self.correct_rejections  = self._validate("correct_rejections", correct_rejections)

    # Validation to reject non-numeric, boolean, negative, and non-finite values
    @staticmethod
    def _validate(name, value):
        if isinstance(value, bool):
            raise TypeError(f"'{name}' must be a non-negative number, not a boolean.")
        if not isinstance(value, (int, float)):
            raise TypeError(f"'{name}' must be a non-negative number, got {type(value).__name__!r}.")
        if math.isnan(value) or math.isinf(value):
            raise ValueError(f"'{name}' must be finite, got {value}.")
        if value < 0:
            raise ValueError(f"'{name}' must be >= 0, got {value}.")
        return float(value)

    def hit_rate(self):
        denominator = self.hits + self.misses
        if denominator == 0:
            raw = 0.0
        else:
            raw = self.hits / denominator
        # Dealing with edge cases
        return float(np.clip(raw, 1e-10, 1.0 - 1e-10))

    def false_alarm_rate(self):
        denominator = self.false_alarms + self.correct_rejections
        if denominator == 0:
            raw = 0.0
        else:
            raw = self.false_alarms / denominator
        # dealing with edge cases again
        return float(np.clip(raw, 1e-10, 1.0 - 1e-10))

    def d_prime(self):
        return stats.norm.ppf(self.hit_rate()) - stats.norm.ppf(self.false_alarm_rate())

    def criterion(self):
        return -0.5 * (stats.norm.ppf(self.hit_rate()) + stats.norm.ppf(self.false_alarm_rate()))

    # overload operators

    # addition
    def __add__(self, other):   
        if not isinstance(other, SignalDetection):
            return NotImplemented
        return SignalDetection(
            self.hits + other.hits,
            self.misses + other.misses,
            self.false_alarms + other.false_alarms,
            self.correct_rejections + other.correct_rejections )
    
    # subtraction
    def __sub__(self, other):  
        if not isinstance(other, SignalDetection):
            return NotImplemented
        return SignalDetection(
            self.hits - other.hits,
            self.misses - other.misses,
            self.false_alarms - other.false_alarms,
            self.correct_rejections - other.correct_rejections)
       
    # multiplication
    def __mul__(self, factor):  
        factor = self._validate("factor", factor)
        return SignalDetection(
            self.hits * factor,
            self.misses * factor,
            self.false_alarms * factor,
            self.correct_rejections * factor)

    # right multiply just in case
    def __rmul__(self, factor):
        return self.__mul__(factor)

    def __str__(self):
        return (
            f"SignalDetection(hits={self.hits}, misses={self.misses}, "
            f"false_alarms={self.false_alarms}, correct_rejections={self.correct_rejections}) | "
            f"H={self.hit_rate():.4f}  FA={self.false_alarm_rate():.4f}  "
            f"d'={self.d_prime():.4f}  C={self.criterion():.4f}")

    # plotting

    def plot_sdt(self):
        d = self.d_prime()
        c = self.criterion()

        # The actual threshold location on the x-axis
        criterion_x = c + d / 2

        # x range wide enough to show both distributions
        x = np.linspace(-4, d + 4, 1000)

        # distributions: nois centered at 0 and signal center at d'
        noise  = stats.norm.pdf(x, 0, 1)  
        signal = stats.norm.pdf(x, d, 1) 

        # starting to call plots
        fig, ax = plt.subplots()
        ax.plot(x, noise,  color='blue', label='Noise  N(0, 1)')
        ax.plot(x, signal, color='red',  label="Signal N(d', 1)")
        ax.axvline(x=criterion_x, color='black', linestyle='--',
                   label=f'Criterion (C = {c:.2f})')

        # Horizontal arrow showing d' between the two means
        y_arrow = max(noise.max(), signal.max()) * 0.6
        ax.annotate('', xy=(d, y_arrow), xytext=(0, y_arrow),
                    arrowprops=dict(arrowstyle='<->', color='green', lw=2))
        ax.text(d / 2, y_arrow * 1.08, f"d' = {d:.2f}",
                ha='center', color='green')

        ax.set_xlabel('Decision Variable')
        ax.set_ylabel('Probability Density')
        ax.set_title('Signal Detection Theory')
        ax.legend()
        plt.tight_layout()
        plt.savefig('sdt_plot.png')
        plt.close()
        return fig, ax 

    @staticmethod
    def plot_roc(sdt_list):
        # Collect hit and FA rates, anchoring with (0,0) and (1,1) for the ROC curve
        hit_rates = [0.0] + [sd.hit_rate() for sd in sdt_list] + [1.0]
        fa_rates  = [0.0] + [sd.false_alarm_rate() for sd in sdt_list] + [1.0]
        
        # glad I found the zip function to easily pair data into coorinates 
        # sort by hit rate (x-axis) so the curve draws cleanly
        pairs = sorted(zip(hit_rates, fa_rates))
        hit_rates_sorted, fa_rates_sorted = zip(*pairs)

        fig, ax = plt.subplots()
        ax.plot(hit_rates_sorted, fa_rates_sorted, marker='o', color='blue')
        # labeling ze chart
        ax.set_xlabel('Hit Rate')
        ax.set_ylabel('False Alarm Rate')
        ax.set_title('ROC Curve')
        # setting chart axis limits
        ax.set_xlim([0, 1])
        ax.set_ylim([0, 1])
        # prevent axis labels being clipped
        plt.tight_layout()
        # save figure in current directory
        plt.savefig('roc_plot.png')
        plt.close()
        return fig, ax 

# test data (included values that would raise errors for show)
sd1 = SignalDetection(40, 10, 20, 30)
sd2 = SignalDetection(30, 20, 10, 40)
sd3 = SignalDetection(50,  5, 15, 35)

print("\n --- Test Data ---")
print(sd1)
print(sd2)
print(sd3)

print("\n--- Operators ---")
print("sd1 + sd2 :", sd1 + sd2)
try: # using try so we can push through the error(s) to the plotting section
    print("sd1 - sd2 :", sd1 - sd2)
except ValueError as exc:
    print(f"sd1 - sd2 : caught ValueError: {exc}")
print("sd1 * 2   :", sd1 * 2)
print("3 * sd2   :", 3 * sd2)

print("\n--- Validation ---")
for bad, label in [
    (lambda: SignalDetection(-1, 10, 5, 5), "negative count"),
    (lambda: SignalDetection("a", 10, 5, 5), "string count"),
    (lambda: SignalDetection(True, 10, 5, 5), "boolean count"),
    (lambda: sd1 * -1, "negative factor"),
    (lambda: sd1 + 5, "add non-SDT"),]:
    try:
        result = bad()
        print(f"  {label}: (no errors found)") # obvously I will have bad data, but ya know
    except (TypeError, ValueError) as exc:
        print(f"  {label}: caught {type(exc).__name__}: {exc}")

SignalDetection.plot_roc([sd1, sd2, sd3])
sd1.plot_sdt()
