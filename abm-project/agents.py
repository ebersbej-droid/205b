"""Agent definitions for the flash-beep illusion ABM."""

import numpy as np


class AuditoryAgent:
    """Auditory agent that fires on real beeps or spontaneous noise."""

    def step(
        self,
        t: int,
        beep: bool,
        noise: float,
        rng: np.random.Generator,
    ) -> bool:
        """
        Compute auditory activation A_k(t).

        Args:
            t: Current timestep.
            beep: True if t is a scheduled beep timestep.
            noise: Baseline noise probability eta.
            rng: Per-agent random number generator.

        Returns:
            True if the agent activates at timestep t.
        """
        if beep:
            return True
        return rng.random() < noise


class VisualAgent:
    """Visual agent that fires on real flashes, phantoms, or noise."""

    def step(
        self,
        t: int,
        flash: bool,
        auditory_signal: bool,
        last_flash_t: int,
        binding_window: int,
        coupling_strength: float,
        noise: float,
        rng: np.random.Generator,
    ) -> bool:
        """
        Compute visual activation V_j(t).

        Args:
            t: Current timestep.
            flash: True if t is a scheduled flash timestep.
            auditory_signal: True if S_aud(t)=1 and binding gate is open
                (computed by the simulation engine before this call).
            last_flash_t: Most recent flash timestep t_f*; -1 if none yet.
            binding_window: Temporal binding window W (spec API only).
            coupling_strength: Cross-modal coupling strength lambda.
            noise: Baseline noise probability eta.
            rng: Per-agent random number generator.

        Returns:
            True if the agent activates at timestep t.
        """
        # binding gate applied by engine; params kept for spec API only
        _ = (last_flash_t, binding_window)

        if flash:
            return True
        if auditory_signal:
            return rng.random() < coupling_strength
        return rng.random() < noise
