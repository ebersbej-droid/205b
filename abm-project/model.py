"""Simulation engine, trial execution, parameter sweeps, and IR computation."""

from dataclasses import dataclass, replace
from typing import List, Tuple

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from agents import AuditoryAgent, VisualAgent
from environment import StimulusSchedule, get_condition


@dataclass(frozen=True)
class SimulationConfig:
    """Configuration parameters for a simulation run."""

    binding_window: int = 10
    coupling_strength: float = 0.70
    n_visual_agents: int = 20
    n_auditory_agents: int = 20
    f_real: int = 10
    noise: float = 0.01
    n_timesteps: int = 50
    n_trials: int = 500
    random_seed: int = 42


def _make_agents(
    seed: int,
    trial_index: int,
    n_visual: int,
    n_auditory: int,
) -> Tuple[List[VisualAgent], List[np.random.Generator], List[AuditoryAgent], List[np.random.Generator]]:
    """
    Create agents with independent child RNGs for a single trial.

    Args:
        seed: Master random seed.
        trial_index: Trial index used to derive independent trial streams.
        n_visual: Number of visual agents.
        n_auditory: Number of auditory agents.

    Returns:
        Tuple of (visual_agents, visual_rngs, auditory_agents, auditory_rngs).
    """
    n_total = n_visual + n_auditory
    ss = np.random.SeedSequence([seed, trial_index])
    children = ss.spawn(n_total)

    visual_agents = [VisualAgent() for _ in range(n_visual)]
    visual_rngs = [np.random.default_rng(child) for child in children[:n_visual]]

    auditory_agents = [AuditoryAgent() for _ in range(n_auditory)]
    auditory_rngs = [np.random.default_rng(child) for child in children[n_visual:]]

    return visual_agents, visual_rngs, auditory_agents, auditory_rngs


def _binding_gate(t: int, beep: bool, last_flash_t: int, binding_window: int) -> bool:
    """
    Evaluate the cross-modal binding indicator.

    Args:
        t: Current timestep.
        beep: True if t is a scheduled beep timestep.
        last_flash_t: Most recent flash timestep t_f*; -1 if none yet.
        binding_window: Temporal binding window W.

    Returns:
        True if auditory recruitment is eligible at timestep t.
    """
    if not beep or last_flash_t < 0:
        return False
    return abs(t - last_flash_t) <= binding_window


def run_trial(
    schedule: StimulusSchedule,
    config: SimulationConfig,
    trial_index: int,
) -> bool:
    """
    Run a single trial and return whether an illusion occurred.

    Args:
        schedule: Stimulus schedule for the trial.
        config: Simulation configuration.
        trial_index: Index of the current trial.

    Returns:
        True if at least one phantom percept occurred during the trial.
    """
    visual_agents, visual_rngs, auditory_agents, auditory_rngs = _make_agents(
        config.random_seed,
        trial_index,
        config.n_visual_agents,
        config.n_auditory_agents,
    )

    last_flash_t = -1
    trial_has_phantom = False

    for t in range(config.n_timesteps + 1):
        auditory_activations = [
            agent.step(t, schedule.is_beep(t), config.noise, rng)
            for agent, rng in zip(auditory_agents, auditory_rngs)
        ]
        s_aud = any(auditory_activations)

        # REQUIRED ORDER: flash update MUST precede binding check within the same
        # timestep. If this order changes, Condition B flash-precedence at t=5
        # breaks silently (coincident beep would incorrectly qualify for phantom).
        if schedule.is_flash(t):
            last_flash_t = t

        if schedule.is_beep(t) and last_flash_t >= 0:
            bind = _binding_gate(t, True, last_flash_t, config.binding_window)
            aud_signal = s_aud and bind
        else:
            aud_signal = False

        flash = schedule.is_flash(t)
        visual_activations = [
            agent.step(
                t,
                flash,
                aud_signal,
                last_flash_t,
                config.binding_window,
                config.coupling_strength,
                config.noise,
                rng,
            )
            for agent, rng in zip(visual_agents, visual_rngs)
        ]
        phi = sum(visual_activations)
        if not flash and phi > config.f_real:
            trial_has_phantom = True

    return trial_has_phantom


def compute_ir(trial_outcomes: List[bool]) -> float:
    """
    Compute illusion rate from binary trial outcomes.

    Args:
        trial_outcomes: List of per-trial illusion indicators.

    Returns:
        Fraction of trials with at least one phantom percept.
    """
    if not trial_outcomes:
        return 0.0
    return float(np.mean(trial_outcomes))


def run_condition(
    condition: str,
    config: SimulationConfig,
) -> Tuple[float, List[bool]]:
    """
    Run all trials for a condition and compute illusion rate.

    Args:
        condition: Experimental condition identifier ('A', 'B', or 'C').
        config: Simulation configuration.

    Returns:
        Tuple of (illusion_rate, list of per-trial outcomes).
    """
    schedule = get_condition(condition)
    outcomes = [
        run_trial(schedule, config, trial_index)
        for trial_index in range(config.n_trials)
    ]
    return compute_ir(outcomes), outcomes


def bootstrap_ci(
    outcomes_wide: List[bool],
    outcomes_narrow: List[bool],
    seed: int,
    n_boot: int = 100,
) -> Tuple[float, float, float]:
    """
    Compute a bootstrap 95% CI for IR(W_wide) - IR(W_narrow).

    Args:
        outcomes_wide: Trial outcomes for the wide binding window condition.
        outcomes_narrow: Trial outcomes for the narrow binding window condition.
        seed: Master seed for reproducible bootstrap resampling.
        n_boot: Number of bootstrap replicates.

    Returns:
        Tuple of (lower bound, point estimate, upper bound) for the IR difference.
    """
    n_trials = len(outcomes_wide)
    if n_trials != len(outcomes_narrow):
        raise ValueError("Wide and narrow outcome lists must have equal length")

    wide = np.asarray(outcomes_wide, dtype=float)
    narrow = np.asarray(outcomes_narrow, dtype=float)
    point_estimate = compute_ir(outcomes_wide) - compute_ir(outcomes_narrow)

    boot_rng = np.random.default_rng(np.random.SeedSequence([seed, 999_999]))
    diffs = np.empty(n_boot, dtype=float)
    for replicate in range(n_boot):
        indices = boot_rng.integers(0, n_trials, size=n_trials)
        diffs[replicate] = wide[indices].mean() - narrow[indices].mean()

    lower, upper = np.percentile(diffs, [2.5, 97.5])
    return float(lower), float(point_estimate), float(upper)


def sweep_binding_window(config: SimulationConfig) -> pd.DataFrame:
    """
    Sweep binding window W from 1 to 15 on Condition A.

    Args:
        config: Base simulation configuration.

    Returns:
        DataFrame with columns binding_window and ir.
    """
    rows = []
    for binding_window in range(1, 16):
        sweep_config = replace(config, binding_window=binding_window)
        ir, _ = run_condition("A", sweep_config)
        rows.append({"binding_window": binding_window, "ir": ir})
    return pd.DataFrame(rows)


def sweep_coupling_strength(config: SimulationConfig) -> pd.DataFrame:
    """
    Sweep coupling strength lambda from 0.0 to 1.0 on Condition A.

    Args:
        config: Base simulation configuration.

    Returns:
        DataFrame with columns coupling_strength and ir.
    """
    rows = []
    for step in range(11):
        coupling_strength = round(step * 0.1, 1)
        sweep_config = replace(config, coupling_strength=coupling_strength)
        ir, _ = run_condition("A", sweep_config)
        rows.append({"coupling_strength": coupling_strength, "ir": ir})
    return pd.DataFrame(rows)


def plot_sweep(
    df: pd.DataFrame,
    x_col: str,
    y_col: str,
    path: str,
    title: str,
    xlabel: str,
) -> None:
    """
    Plot and save a parameter sweep result.

    Args:
        df: Sweep results DataFrame.
        x_col: Column name for the x-axis.
        y_col: Column name for the y-axis.
        path: Output PNG path.
        title: Plot title.
        xlabel: X-axis label.
    """
    plt.figure(figsize=(8, 5))
    plt.plot(df[x_col], df[y_col], marker="o")
    plt.title(title)
    plt.xlabel(xlabel)
    plt.ylabel("Illusion Rate (IR)")
    plt.ylim(0.0, 1.0)
    plt.grid(True, alpha=0.3)
    plt.tight_layout()
    plt.savefig(path)
    plt.show()
    plt.close()
