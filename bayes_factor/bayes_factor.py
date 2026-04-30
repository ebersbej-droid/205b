import math
import scipy.integrate

class BayesFactor:
    def __init__(self, n, k, a=0.4999, b=0.5001):
        #Input and state validation
        if not isinstance(n, int) or isinstance(n, bool) or not isinstance(k, int) or isinstance(k, bool):
            raise TypeError("n and k must be integers")
        if n < 0 or k < 0:
            raise ValueError("n and k cannot be negative")
        if k > n:
            raise ValueError("k cannot be greater than n (impossible binomial state)")
        if a >= b:
            raise ValueError("Parameter 'a' must be strictly less than 'b'")
        # making sure validated values are stored   
        self.n = n
        self.k = k
        self.a = a
        self.b = b

    def likelihood(self, theta):
        # checking theta
        if not isinstance(theta, (int, float)):
            raise TypeError("theta must be a number")
        if not (0 <= theta <= 1):
            raise ValueError("theta must be between 0 and 1")

        # P(x | theta) = (n choose k) * theta^k * (1 - theta)^(n - k) 
        combination = math.comb(self.n, self.k)
        return float(combination * (theta ** self.k) * ((1 - theta) ** (self.n - self.k)))
    
    # likelihood under slab prior: U(0, 1).
    def evidence_slab(self):
        result, _ = scipy.integrate.quad(self.likelihood, 0, 1)
        return result
    
    # Computes marginal likelihood under spike prior: U(a, b)
    # Prior is 1 / (b - a) on [a, b]
    def evidence_spike(self):
        c = self.b - self.a
        integral, _ = scipy.integrate.quad(self.likelihood, self.a, self.b)
        return integral / c
    
    # Computes Bayes Factor B_1:0 (spike over slab).
    def bayes_factor(self):
        ev_slab = self.evidence_slab()
        ev_spike = self.evidence_spike()
        if ev_slab == 0:
            return float('inf')  # edge case handling( slab evidence is 0, spike wins infinitely) 
        return ev_spike / ev_slab