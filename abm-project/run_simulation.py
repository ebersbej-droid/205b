"""CLI entrypoint for the flash-beep illusion ABM."""

import argparse
import os
from dataclasses import replace

import pandas as pd

from model import (
    SimulationConfig,
    bootstrap_ci,
    plot_sweep,
    run_condition,
    sweep_binding_window,
    sweep_coupling_strength,
)


def _build_config(args: argparse.Namespace) -> SimulationConfig:
    """Construct a simulation config from CLI arguments."""
    return SimulationConfig(
        binding_window=args.binding_window,
        coupling_strength=args.coupling_strength,
        n_trials=args.n_trials,
        random_seed=args.seed,
    )


def _run_default(config: SimulationConfig) -> None:
    """Run default three-condition simulation and hypothesis test."""
    rows = []
    for condition in ("A", "B", "C"):
        ir, _ = run_condition(condition, config)
        rows.append({"condition": condition, "ir": ir})

    df = pd.DataFrame(rows)
    print(f"Active seed: {config.random_seed}")
    print("\nIllusion Rate by Condition")
    print(df.to_string(index=False))

    output_path = os.path.join("results", "results_default.csv")
    df.to_csv(output_path, index=False)
    print(f"\nSaved default results to {output_path}")

    config_wide = replace(config, binding_window=15)
    config_narrow = replace(config, binding_window=1)
    _, outcomes_wide = run_condition("A", config_wide)
    _, outcomes_narrow = run_condition("A", config_narrow)
    lower, point, upper = bootstrap_ci(
        outcomes_wide,
        outcomes_narrow,
        config.random_seed,
    )
    rejects_h0 = lower > 0.0
    print("\nBootstrap 95% CI for IR(W=15) - IR(W=1) on Condition A")
    print(f"Point estimate: {point:.4f}")
    print(f"95% CI: [{lower:.4f}, {upper:.4f}]")
    print(f"H0 rejected (CI excludes 0): {rejects_h0}")


def _run_sweeps(config: SimulationConfig) -> None:
    """Run binding-window and coupling-strength sweeps."""
    print(f"Active seed: {config.random_seed}")

    binding_df = sweep_binding_window(config)
    binding_csv = os.path.join("results", "sweep_binding_window.csv")
    binding_df.to_csv(binding_csv, index=False)
    plot_sweep(
        binding_df,
        "binding_window",
        "ir",
        os.path.join("results", "sweep_binding_window.png"),
        "Illusion Rate vs Binding Window (Condition A)",
        "Binding Window (W)",
    )
    print(f"Saved binding-window sweep to {binding_csv}")

    coupling_df = sweep_coupling_strength(config)
    coupling_csv = os.path.join("results", "sweep_coupling_strength.csv")
    coupling_df.to_csv(coupling_csv, index=False)
    plot_sweep(
        coupling_df,
        "coupling_strength",
        "ir",
        os.path.join("results", "sweep_coupling_strength.png"),
        "Illusion Rate vs Coupling Strength (Condition A)",
        "Coupling Strength (lambda)",
    )
    print(f"Saved coupling-strength sweep to {coupling_csv}")


def main() -> None:
    """Parse CLI arguments and run the requested simulation mode."""
    os.makedirs("results", exist_ok=True)

    parser = argparse.ArgumentParser(
        description="Run the flash-beep illusion agent-based model."
    )
    parser.add_argument("--seed", type=int, default=42, help="Master random seed")
    parser.add_argument(
        "--binding_window",
        type=int,
        default=10,
        help="Temporal binding window W",
    )
    parser.add_argument(
        "--coupling_strength",
        type=float,
        default=0.70,
        help="Cross-modal coupling strength lambda",
    )
    parser.add_argument(
        "--n_trials",
        type=int,
        default=500,
        help="Number of trials per condition",
    )
    parser.add_argument(
        "--sweep",
        action="store_true",
        help="Run parameter sweeps and save CSV/PNG outputs",
    )
    args = parser.parse_args()
    config = _build_config(args)

    if args.sweep:
        _run_sweeps(config)
    else:
        _run_default(config)


if __name__ == "__main__":
    main()
