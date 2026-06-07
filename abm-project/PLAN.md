# Flash-Beep Illusion ABM — Implementation Plan

## Overview

Discrete-time agent-based model of the sound-induced flash illusion (Shams et al., 2002). Auditory agents broadcast excitatory signals that stochastically recruit visual agents into phantom activations within a temporal binding window.

## Module Order

1. **`agents.py`** — `VisualAgent`, `AuditoryAgent` (no condition knowledge)
2. **`environment.py`** — `StimulusSchedule`, conditions A/B/C
3. **`model.py`** — trial engine, IR, bootstrap CI, parameter sweeps (sole owner of simulation statistics)
4. **`verify.py`** — seven PASS/FAIL checks; exit code 0 on full pass
5. **`run_simulation.py`** — CLI entrypoint; creates `results/` at startup
6. **`SKILL.md`**, **`README.md`**, **`Dockerfile`**

## Verification Gates

Run `python verify.py` before considering the build complete:

| Check | Criterion |
|-------|-----------|
| Deterministic seed | seed=42 twice → identical IR |
| Ablation | λ=0 → IR(A) < 0.10 |
| Baseline silence | Cond C → IR < 0.10 |
| Zero agents | no crash, IR=0 |
| Bounds | IR ∈ [0, 1] |
| Sensitivity | seeds 42–46, std(IR) < 0.10 |
| Monotonicity | IR(W=15) > IR(W=1) |

## Success Criteria

```bash
python verify.py                 # exit 0
python run_simulation.py         # IR table + bootstrap CI
python run_simulation.py --sweep # CSVs + PNGs in results/
```

## Key Correctness Constraints

- Binding gate computed exclusively in `model.py` (`_binding_gate`)
- Flash update to `last_flash_t` must precede binding check each timestep
- Bootstrap hypothesis test uses W=15 vs W=1 via two separate `run_condition("A")` calls
- `F_real=10` fixed across all sweeps
- Per-agent RNG via `SeedSequence.spawn`; no global RNG
