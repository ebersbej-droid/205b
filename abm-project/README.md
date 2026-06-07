# Flash-Beep Illusion ABM

Discrete-time agent-based model of the sound-induced flash illusion (Shams, Kamitani & Shimojo, 2002) for COGS 205B. A single visual flash paired with two auditory beeps can produce a perceived second flash; this model represents that illusion as an emergent population-level phenomenon driven by cross-modal recruitment within a temporal binding window.

---

## Model Specification

### Agents

The model uses two agent populations with no global state. Each agent draws independently from its own child RNG (derived via NumPy `SeedSequence` spawning).

**AuditoryAgent** (K = 20 agents)

At each timestep `t`, agent `k` activates according to scheduled beeps or baseline noise:

- If `t ∈ B` (scheduled beep): `A_k(t) = 1`
- Otherwise: `A_k(t) ~ Bernoulli(η)`

**VisualAgent** (J = 20 agents)

At each timestep, agent `j` follows one of three mutually exclusive update paths:

- **Real flash:** if `t ∈ F`, then `V_j(t) = 1`
- **Phantom recruitment:** if `t ∉ F`, population auditory signal `S_aud(t) = 1`, and the binding gate is open, then `V_j(t) ~ Bernoulli(λ)`
- **Noise:** otherwise, `V_j(t) ~ Bernoulli(η)`

The simulation engine computes the binding gate and passes the resulting `auditory_signal` boolean to `VisualAgent.step()`. The agent does not implement binding logic itself.

### State Variables

| Symbol | Meaning | Scope |
|--------|---------|-------|
| `A_k(t)` | Auditory agent activation | per agent, per timestep |
| `V_j(t)` | Visual agent activation | per agent, per timestep |
| `S_aud(t)` | Population auditory signal | `1` if any `A_k(t) > 0`, else `0` |
| `Φ(t)` | Aggregate visual activation | `Σ_j V_j(t)` |
| `t_f*` (`last_flash_t`) | Most recent flash timestep | engine state; `-1` before first flash |
| `W` | Temporal binding window | config parameter |
| `λ` | Coupling strength (auditory → visual) | config parameter |
| `η` | Baseline noise probability | config parameter |
| `F_real` | Visual activation threshold for a percept | config parameter |

Discrete time: one timestep = 10 ms. Trials run from `t = 0` to `T_max = 50`.

### Update Rules

Each trial timestep proceeds in this order:

1. **Auditory step.** Each auditory agent updates; compute `S_aud(t) = 𝟙[Σ_k A_k(t) > 0]`.

2. **Flash tracking.** If `t ∈ F`, set `t_f* ← t`. This update must occur before the binding check on the same timestep to preserve flash precedence (e.g., at `t = 5` in Condition B, the real-flash rule prevents phantom recruitment even when a coincident beep is present).

3. **Binding gate** (engine only, `_binding_gate` in `model.py`):

   ```
   𝟙_bind(t, t_f*, W) = 1   if t ∈ B  AND  |t − t_f*| ≤ W
                        = 0   otherwise
   ```

   Phantom recruitment is evaluated only at scheduled beep timesteps. Noise-driven auditory activations at non-beep times do not open the binding gate.

4. **Visual step.** Each visual agent updates using the flash flag, the gated auditory signal (`S_aud(t)` AND binding open), and its own RNG.

5. **Phantom detection.** A phantom percept occurs at timestep `t` when:

   ```
   phantom(t) = 1   iff   Φ(t) > F_real   and   t ∉ F
   ```

   A trial counts as an illusion if `Σ_t phantom(t) ≥ 1`.

### Stimulus Conditions

| Condition | F (flash times) | B (beep times) | Role |
|-----------|-----------------|----------------|------|
| A | {5} | {5, 10} | Illusion: one flash, two beeps |
| B | {5} | {5} | Control: coincident flash/beep only |
| C | {5} | {} | Baseline: flash only, no beeps |

Timestep 5 = flash onset. Timestep 10 = second beep (~50 ms ISI at 10 ms/step).

### Metrics

**Illusion Rate (IR)**

```
IR = (1/N) · Σ_i 𝟙[ Σ_t phantom(t, i) ≥ 1 ]
```

The fraction of trials in which at least one phantom percept occurred. Computed separately per condition and per parameter setting.

**Hypothesis test**

H₀: IR(W=15) = IR(W=1)  
H₁: IR(W=15) > IR(W=1)

Tested on Condition A with λ held constant. Bootstrap over trial outcomes: 100 replicates, paired resampling with replacement, 95% CI for `IR(W=15) − IR(W=1)`. H₀ is rejected if the CI excludes zero.

**Parameter sweeps** (Condition A, all other defaults held fixed)

- Binding window W: 1 to 15 (step 1)
- Coupling strength λ: 0.0 to 1.0 (step 0.1)

### Default Parameters

| Parameter | Symbol | Default | Description |
|-----------|--------|---------|-------------|
| `binding_window` | W | 10 | Temporal binding window (timesteps) |
| `coupling_strength` | λ | 0.70 | Auditory → visual coupling probability |
| `n_visual_agents` | J | 20 | Number of visual agents |
| `n_auditory_agents` | K | 20 | Number of auditory agents |
| `f_real` | F_real | 10 | Activation threshold for a percept (= 0.5 × J) |
| `noise` | η | 0.01 | Baseline spontaneous activation rate |
| `n_timesteps` | T_max | 50 | Trial duration |
| `n_trials` | N | 500 | Trials per condition |
| `random_seed` | — | 42 | Master reproducibility seed |

`F_real` is fixed at 10 across all sweeps and is not retuned.

---

## Results

All values below are from runs with `random_seed = 42`, `N = 500`, and default parameters unless noted. Outputs are saved in `results/`.

### Condition Comparison

| Condition | IR | Interpretation |
|-----------|-----|----------------|
| A | 0.956 | Strong illusion: second beep at t = 10 recruits phantoms within W = 10 |
| B | 0.000 | No second beep; coincident flash/beep at t = 5 produces no phantom |
| C | 0.000 | No auditory events; IR at noise floor |

**Conclusion:** Cross-modal coupling produces the illusion selectively in Condition A. The qualitative ordering IR(A) >> IR(B) ≈ IR(C) matches the Shams et al. (2002) pattern: the extra beep in Condition A drives phantom percepts that are absent in the control and baseline conditions.

### Binding Window Sweep (Condition A)

| W range | IR |
|---------|-----|
| 1–4 | 0.000 |
| 5–15 | 0.956 |

The second beep at t = 10 is 5 timesteps from the flash at t = 5. IR remains zero until W ≥ 5, then jumps to 0.956 and stays flat through W = 15.

**Conclusion:** The illusion requires the second beep to fall within W of the most recent flash. Wider binding windows increase IR once the window encompasses the inter-stimulus interval (threshold at |10 − 5| = 5). This is a direct consequence of fixed stimulus timing |t_beep2 - t_flash| = |10 - 5| = 5 exactly, so any W ≥ 5 always captures the second beep and any W < 5 never does. This supports H₁ that wider W yields higher IR, though the effect appears as a step function rather than a gradual rise at every increment. 

### Coupling Strength Sweep (Condition A)

| λ | IR |
|---|-----|
| 0.0–0.2 | 0.000 |
| 0.3 | 0.012 |
| 0.4 | 0.120 |
| 0.5 | 0.410 |
| 0.6 | 0.770 |
| 0.7 | 0.956 |
| 0.8 | 0.998 |
| 0.9–1.0 | 1.000 |

**Conclusion:** Cross-modal coupling is necessary for substantial illusion rates (λ = 0 → IR = 0, consistent with the ablation check). IR increases monotonically with λ across the sweep range.

### Bootstrap Hypothesis Test (Condition A)

| Statistic | Value |
|-----------|-------|
| IR(W = 15) − IR(W = 1) (point estimate) | 0.956 |
| 95% bootstrap CI | [0.9368, 0.9730] |
| H₀ rejected (CI excludes 0) | Yes |

**Conclusion:** A wider temporal binding window produces a significantly higher illusion rate than a narrow window on Condition A. H₀ is rejected.

**Caveat:** IR(A) = 0.956 at default parameters exceeds the PROMPT pilot range (~0.60–0.75). The implementation was not tuned to match that range; qualitative ordering and hypothesis support remain valid, but exact magnitudes should not be treated as empirical predictions.

---

### How Accuracy Was Ensured

**Mathematical fidelity.** Equations 1–7 from the project specification are implemented in `model.py`. The binding indicator is computed exclusively in the engine (`_binding_gate`), not in agent code. Phantom detection uses the population threshold Φ(t) > F_real with the flash exclusion t ∉ F.

**Module boundaries.** `agents.py` defines agent step logic only and has no knowledge of experimental conditions. `environment.py` defines stimulus schedules only and computes no statistics. `model.py` is the sole owner of trial execution, IR computation, sweeps, and bootstrap. `verify.py` and `run_simulation.py` contain no simulation logic.

**Reproducibility.** Each agent receives an independent child RNG via `SeedSequence([seed, trial_index]).spawn(n)`. No module calls `np.random.seed()` at import time, and no global RNG is shared across agents. The bootstrap resampler is seeded deterministically from the master seed.

**Automated verification.** `python verify.py` runs seven checks; all pass:

1. Deterministic seed — identical IR on repeated runs with seed = 42
2. Ablation — λ = 0 yields IR(A) < 0.10
3. Baseline silence — Condition C IR < 0.10
4. Zero agents — no crash, IR = 0
5. Bounds — IR ∈ [0, 1] for all conditions
6. Sensitivity — std(IR) < 0.10 across seeds 42–46
7. Monotonicity — IR(W = 15) > IR(W = 1)

**Critical ordering invariant.** Within each timestep, `last_flash_t` is updated before the binding gate is evaluated. An inline comment in `model.py` documents that reversing this order would silently break flash precedence in Condition B.

### Trust Assessment

**What I trust**

- The qualitative conclusions: Condition A produces illusions that Conditions B and C do not; λ and W modulate IR in the expected directions; removing coupling (λ = 0) collapses IR to the noise floor.
- Reproducibility and internal consistency: the verification suite passes, and reruns with the same seed produce identical results.
- The hypothesis test result: the difference IR(W = 15) − IR(W = 1) is large and stable, with a bootstrap CI that clearly excludes zero.

**Caveats and limits**

- IR(A) = 0.956 is VERY high relative to human psychophysics and the PROMPT pilot range. The model is sensitive at default parameters and was not calibrated to match empirical illusion rates.
- The W sweep shows a step function (threshold at 5 timesteps) rather than smooth monotonicity at every step. This is acceptable per the specification but reflects the discrete stimulus schedule rather than graded neural binding.
- Detailed results are reported for seed = 42; the sensitivity check covers seeds 42–46 but is not exhaustive.
- The model is a simplified ABM: no observer heterogeneity, no neural dynamics, and no spatial structure.

**Reflection**

Accuracy was ensured through four mechanisms. First, equations 1–7 from the specification are implemented directly in model.py. The binding gate lives exclusively in the engine, not in agent code, and phantom detection applies the population threshold with the flash exclusion. Second, module boundaries are enforced: agents know no conditions, environment computes no statistics, and all IR logic lives in model.py. Third, reproducibility is guaranteed via SeedSequence spawning each agent has an independent child RNG, no global RNG state exists, and the bootstrap resampler is seeded from the master seed. Fourth, python verify.py runs seven simulation-specific checks (deterministic seed, ablation, baseline silence, zero agents, bounds, sensitivity, monotonicity); all pass.

I trust the qualitative conclusions that Condition A produces illusions that B and C do not, λ and W modulate IR in the expected directions, and removing coupling collapses IR to the noise floor. The bootstrap CI clearly excludes zero, supporting H₁. What I do not trust is the exact magnitudes: IR(A) = 0.956 exceeds typical human illusion rates and the pilot range, reflecting that the model was not calibrated to empirical data (Normally around ~.6-.7).

The clearest limitation is the single-threshold binding window. Empirical literature shows an inverted-U shape relationship. Signals too close fuse rather than produce a phantom, but this model only captures the upper bound. This likely inflates IR at short asynchronies. Adding a minimum threshold would be the most natural step toward a more realistic implementation.

---

## How to Run

Requires Python 3.10+ with numpy, pandas, and matplotlib:

```bash
python verify.py
python run_simulation.py
python run_simulation.py --sweep
```

Docker:

```bash
docker build -t flash-beep-abm .
docker run flash-beep-abm
```

Outputs are written to `results/` (`results_default.csv`, sweep CSVs and PNGs).

---

## References

Shams, L., Kamitani, Y., & Shimojo, S. (2002). Visual illusion induced by sound. *Cognitive Brain Research*, 14(1), 147–152.
