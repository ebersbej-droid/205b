"""Verification suite for the flash-beep illusion ABM."""

import sys
from dataclasses import replace

import numpy as np

from model import SimulationConfig, compute_ir, run_condition


def _report(name: str, passed: bool) -> bool:
    """Print PASS/FAIL for a verification check."""
    status = "PASS" if passed else "FAIL"
    print(f"{name}: {status}")
    return passed


def check_deterministic_seed() -> bool:
    """Two runs with seed=42 must produce identical IR on Condition A."""
    config = SimulationConfig(random_seed=42)
    ir_one, _ = run_condition("A", config)
    ir_two, _ = run_condition("A", config)
    return _report("Deterministic seed", ir_one == ir_two)


def check_ablation() -> bool:
    """Lambda=0 must yield IR(A) below the ablation threshold."""
    config = replace(SimulationConfig(), coupling_strength=0.0)
    ir, _ = run_condition("A", config)
    return _report("Ablation (lambda=0)", ir < 0.10)


def check_baseline_silence() -> bool:
    """Condition C must remain near the noise floor."""
    config = SimulationConfig()
    ir, _ = run_condition("C", config)
    return _report("Baseline silence (Cond C)", ir < 0.10)


def check_zero_agents() -> bool:
    """Zero-agent runs must not crash and must return IR=0."""
    config = replace(
        SimulationConfig(),
        n_visual_agents=0,
        n_auditory_agents=0,
    )
    try:
        ir, _ = run_condition("A", config)
    except Exception:
        return _report("Zero agents", False)
    return _report("Zero agents", ir == 0.0)


def check_bounds() -> bool:
    """IR must remain within [0, 1] for all default conditions."""
    config = SimulationConfig()
    passed = True
    for condition in ("A", "B", "C"):
        ir, _ = run_condition(condition, config)
        if not (0.0 <= ir <= 1.0):
            passed = False
            break
    return _report("Bounds check", passed)


def check_sensitivity() -> bool:
    """IR(A) across seeds 42-46 must have std < 0.10."""
    ir_values = []
    for seed in range(42, 47):
        config = replace(SimulationConfig(), random_seed=seed)
        ir, _ = run_condition("A", config)
        ir_values.append(ir)
    passed = float(np.std(ir_values)) < 0.10
    return _report("Sensitivity (seeds 42-46)", passed)


def check_monotonicity() -> bool:
    """Mean IR(W=15) must exceed mean IR(W=1) on Condition A."""
    base = SimulationConfig()
    ir_wide, _ = run_condition("A", replace(base, binding_window=15))
    ir_narrow, _ = run_condition("A", replace(base, binding_window=1))
    return _report("Monotonicity sanity (W=15 > W=1)", ir_wide > ir_narrow)


def main() -> None:
    """Run all verification checks and exit with code 0 on full pass."""
    checks = [
        check_deterministic_seed,
        check_ablation,
        check_baseline_silence,
        check_zero_agents,
        check_bounds,
        check_sensitivity,
        check_monotonicity,
    ]
    results = [check() for check in checks]
    if all(results):
        sys.exit(0)
    sys.exit(1)


if __name__ == "__main__":
    main()
