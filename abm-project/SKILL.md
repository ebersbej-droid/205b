# Flash-Beep Illusion ABM — Project Context

Self-contained reference for continuing work on the sound-induced flash illusion agent-based model (Shams et al., 2002).

## How to Use This File
Paste this file into a new Cursor session to restore full project
context without re-reading the codebase. Reference specific sections
by equation number or module name when prompting.

---

## Model Assumptions and Justification

1. **Discrete time:** The simulation advances in 10 ms timesteps (T = {0, …, T_max}). Stimulus events (flash, beep) occur at specific timesteps.

2. **Population-level emergence:** Individual agents stochastically activate; a percept requires aggregate visual activation Φ(t) > F_real. The illusion rate (IR) is the fraction of trials with at least one phantom percept.

3. **Cross-modal recruitment:** Auditory activity can recruit visual agents into phantom activations, but only when:
   - The timestep is a scheduled beep (t ∈ B)
   - A recent flash falls within the binding window W of that beep
   - Population auditory signal S_aud(t) = 1

4. **No global state:** Each agent has an independent child RNG derived from a master seed via NumPy SeedSequence spawning. No module-level RNG.

5. **Flash precedence:** At coincident flash/beep timesteps (e.g., t=5 in Condition B), the real-flash rule takes priority. Phantom recruitment cannot occur at flash timesteps even if binding is satisfied.

6. **Fixed percept threshold:** F_real = 10 (= 0.5 × n_visual_agents) is held constant across all parameter sweeps. It calibrates population-level phantom detection without tuning per sweep.

7. **Conditions:**
   - **A (Illusion):** F={5}, B={5, 10} — second beep recruits phantoms
   - **B (Control):** F={5}, B={5} — coincident beep only; no second beep
   - **C (Baseline):** F={5}, B={} — no auditory events

---

## Mathematical Definitions (Equations 1–7)

### Notation

- T = {0, 1, …, T_max} — discrete timesteps
- F = {t : flash at t}, B = {t : beep at t}
- W ∈ ℤ⁺ — temporal binding window
- λ ∈ [0, 1] — coupling strength (auditory → visual)
- η ∈ [0, 1] — baseline noise probability
- F_real ∈ ℤ⁺ — visual activation threshold for a percept
- N ∈ ℤ⁺ — number of trials

### Equation 1 — Binding Indicator

```
𝟙_bind(t, t_f*, W) = 1   if t ∈ B  AND  |t - t_f*| ≤ W
                     0   otherwise
```

Binding is evaluated only at scheduled beep timesteps. Noise-driven auditory activations at non-beep times do not contribute to phantom recruitment.

### Equation 2 — Auditory Agent State

```
A_k(t) = 1              if t ∈ B   (real beep)
       = Bernoulli(η)   otherwise  (spontaneous noise)

S_aud(t) = 𝟙[ Σ_k A_k(t) > 0 ]
```

### Equation 3 — Visual Agent State

Let t_f* = most recent flash timestep ≤ t (−1 if none yet).

```
V_j(t) = 1              if t ∈ F                                    (real flash)
       = Bernoulli(λ)   if t ∉ F, S_aud(t)=1, 𝟙_bind(t, t_f*, W)=1  (phantom)
       = Bernoulli(η)   otherwise                                   (noise)
```

Phantom recruitment only occurs at timesteps t ∈ B. At t=5 in Condition B, t ∈ F takes precedence.

### Equation 4 — Per-Trial Phantom Activation

```
Φ(t, i)       = Σ_{j=1}^{n_visual} V_j(t, i)
phantom(t, i) = 𝟙[ Φ(t, i) > F_real   and   t ∉ F ]
```

### Equation 5 — Illusion Rate

```
IR = (1/N) · Σ_{i=1}^{N} 𝟙[ Σ_t phantom(t, i) ≥ 1 ]
```

H₀: IR(W_wide) = IR(W_narrow)  
H₁: IR(W_wide) > IR(W_narrow)  (λ held constant, tested on Condition A)

### Equation 6 — Expected Monotonicity

```
E[IR(W+1)] ≥ E[IR(W)]
∂IR/∂λ ≥ 0
```

Small local deviations from W-monotonicity are acceptable due to stochastic variance. Do not artificially smooth results.

### Equation 7 — Ablation Identity

When λ = 0, cross-modal recruitment is removed. Visual activations outside flash timesteps arise only from baseline noise η. IR(Cond A, λ=0) should be < 0.10.

---

## Known Failure Modes

1. **Global RNG contamination:** Using `np.random.seed()` at module scope or a shared RNG across agents breaks reproducibility. Always inject per-agent child RNGs via SeedSequence spawning.

2. **F_real too high → IR = 0:** If F_real exceeds typical Φ(t) under phantom recruitment, no trial registers an illusion. F_real is fixed at 10; do not adjust during sweeps.

3. **Large binding windows:** W large enough that nearly all beeps qualify for recruitment can inflate IR toward 1. Expected behavior, not a bug.

4. **Sweeping λ toward 0:** IR collapses toward the noise floor. Expected model behavior validating Equation 7.

5. **Flash/binding order bug:** If `last_flash_t` is updated *after* the binding check within the same timestep, Condition B flash-precedence at t=5 breaks silently — coincident beeps would incorrectly pass the binding gate for phantom rolls.

6. **Binding logic in agents.py:** VisualAgent must not implement binding. The engine computes `_binding_gate` and passes the resulting `auditory_signal` boolean.

7. **Non-beep phantom recruitment:** Allowing phantom rolls at non-beep timesteps (e.g., from noise-driven S_aud) violates Equation 1 and inflates IR in Conditions B and C.

8. **Bootstrap non-reproducibility:** Bootstrap resampler must be seeded deterministically from the master seed (e.g., `SeedSequence([seed, 999_999])`).

---

## Bootstrap Procedure

**Hypothesis:** H₀: IR(W=15) = IR(W=1); H₁: IR(W=15) > IR(W=1) on Condition A with λ fixed.

**Steps:**

1. Run `run_condition("A", config_with_W=15)` → `outcomes_wide` (list of N booleans)
2. Run `run_condition("A", config_with_W=1)` → `outcomes_narrow` (list of N booleans)
3. Point estimate: `IR_wide − IR_narrow`
4. For each of 100 bootstrap replicates:
   - Resample trial indices {0, …, N−1} with replacement (paired resampling)
   - Recompute `IR_wide*` and `IR_narrow*` from resampled outcomes
   - Record difference `IR_wide* − IR_narrow*`
5. 95% CI = [2.5th percentile, 97.5th percentile] of the 100 differences
6. Reject H₀ if CI excludes zero (lower bound > 0)

Bootstrap RNG is seeded from the master seed for reproducibility across runs.

---

## Implementation Priority Hierarchy

When tradeoffs arise, prioritize in this order:

1. **Scientific correctness** — equations and binding logic must match the formalization
2. **Verification checks** — all seven verify.py tests must PASS
3. **Reproducibility** — deterministic seeds, SeedSequence spawning, reproducible bootstrap
4. **Code clarity** — module boundaries, docstrings, explainable design
5. **Runtime efficiency** — optimize only after 1–3 are satisfied

Never sacrifice items 1–3 for 4–5.

---

## Module Ownership Boundaries

| Module | Owns | Must NOT contain |
|--------|------|------------------|
| `agents.py` | `VisualAgent`, `AuditoryAgent` step logic | Condition knowledge, binding gate, IR |
| `environment.py` | `StimulusSchedule`, conditions A/B/C, `get_condition()` | Simulation statistics, IR |
| `model.py` | Trial engine, `_binding_gate`, IR, sweeps, bootstrap | CLI code, verification logic |
| `verify.py` | PASS/FAIL checks, exit codes | Simulation logic |
| `run_simulation.py` | CLI parsing, `os.makedirs("results")`, output printing | Trial/IR computation |

**Critical engine ordering per timestep:**
1. Auditory agents → S_aud(t)
2. Update `last_flash_t` if flash at t
3. Binding gate at beep timesteps → `auditory_signal`
4. Visual agents → Φ(t)
5. Phantom detection if Φ > F_real and t ∉ F

---

## Verification Thresholds and Scientific Interpretation

| # | Check | Threshold | Interpretation |
|---|-------|-----------|----------------|
| 1 | Deterministic seed | seed=42 twice → identical IR | Reproducibility; results are not RNG-state artifacts |
| 2 | Ablation (λ=0) | IR(A) < 0.10 | Cross-modal coupling is necessary for illusions (Eq. 7) |
| 3 | Baseline silence (C) | IR < 0.10 | Without beeps, phantoms arise only from rare noise |
| 4 | Zero agents | no crash, IR=0 | Graceful degenerate case |
| 5 | Bounds | IR ∈ [0, 1] | IR is a valid proportion |
| 6 | Sensitivity (seeds 42–46) | std(IR) < 0.10 | Results reflect model dynamics, not seed lottery |
| 7 | Monotonicity (W=15 vs W=1) | IR(W=15) > IR(W=1) | Wider binding windows increase illusion rate (Eq. 6) |

**Untrustworthy results if:**
- Ablation fails (λ=0 still produces high IR)
- Seed check fails
- IR(C) ≈ IR(A) (coupling has no effect)
- Sensitivity std > 0.10
- IR = 0 or 1 everywhere (degenerate model)
- Bootstrap CI for IR(W=15) − IR(W=1) includes zero
- Module responsibilities entangled
- Bootstrap not reproducible from master seed

---

## Default Parameters

```
binding_window=10, coupling_strength=0.70, n_visual_agents=20,
n_auditory_agents=20, f_real=10, noise=0.01, n_timesteps=50,
n_trials=500, random_seed=42
```

## Commands

```bash
python verify.py
python run_simulation.py
python run_simulation.py --sweep
```
