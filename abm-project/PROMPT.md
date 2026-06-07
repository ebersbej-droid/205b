# PROMPT.md — Flash-Beep Illusion ABM
# Sound-Induced Flash Illusion · Shams, Kamitani & Shimojo (2002)
# COGS 205B · Agent-Based Modeling Capstone

---

## PROJECT OVERVIEW

Build a discrete-time agent-based model of the sound-induced flash illusion
(Shams et al., 2002). A single visual flash accompanied by two rapid auditory
beeps causes observers to perceive two flashes. Specifically, a phantom visual event that was never presented. The model represents this as an emergent population-level phenomenon: auditory agents broadcast excitatory signals that stochastically recruit visual agents into firing phantom activations within a temporal binding window.

No ABM frameworks (no Mesa, no JADE). No global state. All randomness seeded
explicitly and passed via dependency injection.

---

## SCIENTIFIC HYPOTHESIS

> Agents with a wider temporal binding window will produce a significantly
> higher illusion rate in the 1-flash-2-beep condition than agents with a
> narrow temporal binding window, even when auditory and visual signal
> strengths are held equal.

H₀: IR(W_wide) = IR(W_narrow)
H₁: IR(W_wide) > IR(W_narrow)

Tested in Condition A (1 flash + 2 beeps), with coupling_strength (λ) fixed.

**Statistical evaluation:**
Bootstrap over trial outcomes within a condition. Each bootstrap sample
resamples N trials with replacement and recomputes IR. Use 100 bootstrap
replicates. Report a 95% confidence interval for:

IR(W_wide) − IR(W_narrow)

Reject H₀ if the confidence interval excludes zero.

---

## ROLE

Expert Python developer and cognitive scientist. Prioritize clarity and
correctness over complexity. Every design decision must be explainable
and verifiable.

---

## FILE STRUCTURE

abm-project/
├── PROMPT.md
├── PLAN.md
├── SKILL.md
├── agents.py
├── environment.py
├── model.py
├── verify.py
├── run_simulation.py
├── results/
├── Dockerfile
└── README.md

### Module Ownership

agents.py
  VisualAgent and AuditoryAgent definitions only.

environment.py
  Stimulus schedules, condition definitions, and event generation.

model.py
  Simulation engine, trial execution, parameter sweeps, and IR computation.

verify.py
  Verification suite and PASS/FAIL checks only.

run_simulation.py
  CLI entrypoint only.

agents.py contains no knowledge of experimental conditions.

environment.py contains no simulation statistics.

model.py is the only module allowed to compute IR,
run trials, or aggregate results.

Seed the bootstrap resampler from the same master seed
to ensure the CI is reproducible across runs.

---

## MATHEMATICAL FORMALIZATION

### Notation

T      = {0, 1, ..., T_max}      discrete timesteps (1 step = 10ms)
F      = {t : flash event at t}  flash event timesteps
B      = {t : beep event at t}   beep event timesteps
W   ∈ ℤ⁺                         temporal binding window (timesteps)
λ   ∈ [0, 1]                     coupling strength (auditory → visual)
η   ∈ [0, 1]                     baseline noise probability
F_real ∈ ℤ⁺                      visual activation threshold for a percept
N   ∈ ℤ⁺                         number of trials

### 1. Binding Indicator

An auditory signal at timestep t is eligible for cross-modal recruitment
if and only if t is itself a beep timestep whose time satisfies the window
condition relative to the most recent flash t_f*:

𝟙_bind(t, t_f*, W) = 1   if t ∈ B  AND  |t - t_f*| ≤ W
                     0   otherwise

This means binding is only evaluated at timesteps where a real beep fired.
Noise-driven auditory activations at non-beep timesteps do not contribute
to phantom recruitment. W is the primary free parameter swept in the
experiment.

### 2. AuditoryAgent State

         ⎧ 1                   if t ∈ B   (real beep)
A_k(t) = ⎨
         ⎩ Bernoulli(η)        otherwise  (spontaneous noise)

Population-level auditory signal:
S_aud(t) = 𝟙[ Σ_k A_k(t) > 0 ]

### 3. VisualAgent State

Let t_f* = most recent flash timestep ≤ t (-∞ if none yet).

         ⎧ 1                   if t ∈ F                                     (real flash)
V_j(t) = ⎨ Bernoulli(λ)        if t ∉ F, S_aud(t)=1, 𝟙_bind(t, t_f*, W)=1  (phantom)
         ⎩ Bernoulli(η)        otherwise                                    (noise)

Each agent draws independently from its own child RNG.

Note: phantom recruitment only occurs at timesteps t ∈ B. At t=5 in
Condition B, t ∈ F takes precedence and the real flash rule applies,
meaning a single coincident beep cannot trigger a phantom roll.

### 4. Per-Trial Phantom Activation

Φ(t, i)       = Σ_{j=1}^{n_visual} V_j(t, i)
phantom(t, i) = 𝟙[ Φ(t, i) > F_real   and   t ∉ F ]

### 5. Illusion Rate

IR = (1/N) · Σ_{i=1}^{N} 𝟙[ Σ_t phantom(t, i) ≥ 1 ]

Computed separately per condition and per parameter setting.

H₀: IR(W_wide) = IR(W_narrow)
H₁: IR(W_wide) > IR(W_narrow)    (λ held constant)

### 6. Expected Monotonicity

IR is expected to be non-decreasing in W on average:

E[IR(W+1)] ≥ E[IR(W)]

IR is expected to be non-decreasing in λ:

∂IR/∂λ ≥ 0

Note: small local deviations from W-monotonicity are acceptable due to
stochastic sampling variance. Do not smooth or adjust results to enforce
monotonicity artificially. The trend should be visible across the full
sweep range, not at every individual step.

### 7. Ablation Identity

λ = 0 removes cross-modal recruitment.

Visual activations outside flash timesteps then arise only from baseline
noise η. Phantom percepts should therefore become rare and IR should
approach zero for sufficiently small η.

Verification operationalizes this as:

IR(Cond A, λ = 0) < 0.10

This test validates that cross-modal coupling is necessary for producing
substantial illusion rates.

---

## AGENT SPECIFICATIONS

### VisualAgent.step()

VisualAgent.step(
    t,                        # current timestep
    flash: bool,              # True if t ∈ F
    auditory_signal: bool,    # True if S_aud(t)=1 AND 𝟙_bind(t, t_f*, W)=1
                              # binding gate applied by engine before this call
    last_flash_t: int,        # t_f*; -1 if no flash yet
    binding_window: int,      # W
    coupling_strength: float, # λ
    noise: float,             # η
    rng: np.random.Generator
) -> bool                     # V_j(t)

The simulation engine is responsible for determining whether
𝟙_bind(t, t_f*, W)=1 and passing the resulting auditory_signal state
to VisualAgent.step(). 

### AuditoryAgent.step()

AuditoryAgent.step(
    t,
    beep: bool,
    noise: float,             # η
    rng: np.random.Generator
) -> bool                     # A_k(t)

### Per-Agent RNG

Each agent must receive an independent child RNG derived reproducibly
from the master seed.

Use a NumPy SeedSequence-based approach:

ss = np.random.SeedSequence(seed)
children = ss.spawn(n)

Construct agent RNGs from the spawned child sequences.

Never use a shared global RNG object.
Never call np.random.seed(...) at module scope.

---

## STIMULUS CONDITIONS

Condition A — Illusion:   F = {5},  B = {5, 10}   →  IR substantially above B and C
Condition B — Control:    F = {5},  B = {5}        →  IR near noise floor
Condition C — Baseline:   F = {5},  B = {}         →  IR near noise floor

Condition A should produce a meaningfully higher IR than Conditions B and C.
Pilot calibration at default parameters suggests IR(A) ≈ 0.60–0.75, but
exact values are not required. Do not tune implementation details to hit
these numbers. The qualitative ordering IR(A) >> IR(B) ≈ IR(C) is what
matters.

Timestep 5 = flash onset. Timestep 10 = second beep (~50ms ISI at 10ms/step).

---

## DEFAULT PARAMETERS

binding_window    = 10      # W
coupling_strength = 0.70    # λ
n_visual_agents   = 20
n_auditory_agents = 20
F_real             = 10     # F_real = 0.5 * n_visual_agents
noise             = 0.01    # η
n_timesteps       = 50      # T_max
n_trials          = 500     # N
random_seed       = 42

### Calibration Note

F_real must remain fixed at 10 across all parameter sweeps. It is chosen
such that default parameters (λ=0.70, W=10) produce non-degenerate illusion
rates. Do not adjust F_real during sweeps. Be aware that sweeping λ downward
toward 0 will cause IR to collapse, this is expected model behavior, not
a bug.

### Parameter Sweeps

Sweep W from 1 to 15 (step 1), all else default.
Sweep λ from 0.0 to 1.0 (step 0.1), all else default.
Save: results/sweep_binding_window.csv, results/sweep_coupling_strength.csv
Save corresponding IR vs. parameter plots as PNG.

---

## VERIFICATION CHECKS (verify.py)

All six must print PASS/FAIL and exit with code 0 on full pass.

1. Deterministic seed:   seed=42 twice → identical IR
2. Ablation:             λ=0.0 → IR(Cond A) < 0.10 (validates eq. 7)
3. Baseline silence:     B=∅ (Cond C) → IR < 0.10
4. Zero agents:          n_visual=0, n_auditory=0 → no crash, IR=0
5. Bounds check:         IR ∈ [0.0, 1.0] for all conditions
6. Sensitivity:          seeds 42–46, Cond A → std(IR) < 0.10
7. Monotonicity sanity check: Mean IR(W=15) > Mean IR(W=1)

Run with: python verify.py

---

## run_simulation.py CLI

python run_simulation.py [--seed INT] [--binding_window INT]
                         [--coupling_strength FLOAT] [--n_trials INT]
                         [--sweep]

No flags: run all three conditions at defaults, print IR table,
          save results/results_default.csv
--sweep:  run both parameter sweeps, save CSVs and plots
Always print the active seed.

---

## CONSTRAINTS

DO:
- PEP 8 + docstrings on all public functions and classes
- if __name__ == "__main__": guards on all runnable scripts
- Pass rng explicitly everywhere
- numpy, pandas, matplotlib only
- plt.savefig(...) before any plt.show()
- Store stimulus schedules and condition definitions inside environment or
  model instances rather than module-level mutable globals
- Use NumPy SeedSequence spawning for reproducible independent RNG streams

DO NOT:
- Hardcode results or short-circuit simulation logic
- Tune thresholds or implementation details to match expected IR ranges
- Use Mesa, JADE, or any ABM framework
- Use np.random.seed(...) at module level
- Create circular imports between simulation files

---

## CONTEXT MANAGEMENT (SKILL.md)

Encode the following for use across Cursor sessions:
- Model assumptions and justification
- Full mathematical definitions (equations 1–7)
- Known failure modes: global RNG contamination, F_real too high → IR=0,
  large binding windows causing nearly all beeps to qualify for recruitment,
  sweeping λ low causing IR degeneracy
- Bootstrap procedure: resample trials with replacement, recompute IR,
  100 replicates, 95% CI
- Implementation priority hierarchy
- Module ownership boundaries
- Verification thresholds and their scientific interpretation

---

## IMPLEMENTATION PRIORITY

If tradeoffs arise:

1. Scientific correctness
2. Verification checks
3. Reproducibility
4. Code clarity
5. Runtime efficiency

NEVER sacrifice items 1–3 to improve items 4–5.

---

## WHAT WOULD MAKE THE RESULT UNTRUSTWORTHY

- Ablation fails — IR does not drop when λ=0; equation 7 violated
- Seed check fails — two runs with seed=42 differ
- IR(Cond C) ≈ IR(Cond A) — cross-modal coupling has no measurable effect
- Sensitivity std > 0.10 — results are seed-dominated noise
- IR = 0 or 1 everywhere — model is degenerate
- Bootstrap CI for IR(W_wide) − IR(W_narrow) includes zero — hypothesis
  not supported
- Module responsibilities become entangled (e.g., simulation logic inside
  verify.py or CLI code inside model.py)
- Results depend on global RNG state
- Bootstrap procedure is not reproducible from the specified seed

---

## REFERENCES

Shams, L., Kamitani, Y., & Shimojo, S. (2002). Visual illusion induced by
sound. Cognitive Brain Research, 14(1), 147–152.