# Bayes Factor

A Python implementation of a Bayes Factor model for testing whether a 
binomial process has a fair success rate (theta ≈ 0.5).


## Project Structure
- `bayes_factor.py` — BayesFactor class implementation
- `tests/test_bayes_factor.py` — Full unittest test suite

## How to Run

Open terminal/shell

Build the image:
    docker build -t bayes-factor .

Run the tests:
    docker run --rm bayes-factor

## Tests Cover
- Input and state validation
- API behavior and return contracts
- Mathematical consistency checks
- Error behavior and exception messages
- Test Driven Development integrity
- Integration tests for Bayes Factor direction