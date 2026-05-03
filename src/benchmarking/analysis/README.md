# `benchmarking.analysis` — grading & comparison pipelines

Everything in this subpackage turns raw benchmark logs into graded reports. Three pipelines live here, all driven through `benchmark` subcommands:

1. **Per-run grading** (`benchmark analyze`) — score a single stack's run against the rubric, producing `analysis.json` + `analysis.md` inside the run dir.
2. **Cross-stack final analysis (LLM)** (`benchmark final`) — compare exactly two graded run dirs (baseline vs. variant) and write `final_analysis.{json,md}` under `experiments/<platform>/final/<timestamp>/`.
3. **Deterministic comparisons** (`benchmark aggregate`, `benchmark combine`) — same shape as the LLM driver but trust the per-run verdicts on disk.

All three pipelines share `precompute.py`, which converts the raw `session.log` + `token_trace.json` files in a run dir into a clean `analysis_data.json` blob the grader consumes. It is invoked automatically by the per-run and final drivers; expose it as `benchmark precompute` for ad-hoc use.

## Layout

```
src/benchmarking/analysis/
├── precompute.py        # shared: raw logs → analysis_data.json
├── per_run/             # single-stack grading
├── final/               # cross-stack & multi-variant comparison
└── notes/               # platform-specific grading guidance (package data)
```

## File map

| File | Purpose |
|---|---|
| `precompute.py` | Parses `session.log` + `token_trace.json` for every prompt subdir into `analysis_data.json`. Auto-invoked in-process by both drivers when missing. |
| `per_run/run_per_run_analysis.py` | Driver: grades one single-stack run dir via `claude --print`. Incremental — writes `per_prompt_analysis/p<id>.json` per prompt so a partial run can resume. |
| `per_run/render_md.py` | Deterministic `analysis.md` renderer from `analysis.json`. No LLM. |
| `per_run/analysis_prompt.md` | Per-run grading prompt template. Loaded by the driver and rendered with run-dir / stack / platform-notes substitutions. |
| `final/run_final_analysis.py` | Driver: cross-stack final analysis. Takes two run dirs (baseline + variant) and produces `final_analysis.{json,md}`. |
| `final/render_final_md.py` | Deterministic `final_analysis.md` renderer from `final_analysis.json`. |
| `final/aggregate_final_json.py` | Deterministic `final_analysis.json` rollup from two `analysis.json` files. Use when you trust per-run verdicts and want to skip the LLM grader. |
| `final/aggregate_combined_md.py` | N-way comparison (1 baseline + N variants) → `combined_comparison.md`. Reads each run dir's `analysis.json`. Deterministic. |
| `final/final_analysis_prompt.md` | Cross-stack grading prompt template. |
| `notes/notes_<platform>.md` | Platform-specific grading guidance (infeasible prompts, tool-name normalisation, workspace quirks). Auto-loaded by both drivers from `--platform`. |

## Step-by-step: per-run grading

You have one run dir under `experiments/<platform>/runs/<timestamp>__<stack>/` and want `analysis.md`.

1. **(Optional) Grade as part of the benchmark run.** Pass `--analyze` to `benchmark run` and the per-run analyzer fires automatically once Phase 3 finishes:
   ```bash
   uv run benchmark run --platform slack --stack slack --analyze
   ```
2. **(Or) Grade later, against existing run dirs.**
   ```bash
   uv run benchmark analyze \
       --platform slack \
       --runs experiments/slack/runs/<timestamp>__slack
   ```
   Use `--all` instead of `--runs` to grade every dir under `experiments/<platform>/runs/`.
3. **Iterate cheaply.** Re-running the command resumes from `per_prompt_analysis/`; only un-graded prompts are sent to Claude. Add `--prompt-ids 1,2,5` to focus on a subset, `--regrade` to force re-grading.
4. **Re-render the markdown only.** If you tweak `render_md.py`, regenerate without re-grading:
   ```bash
   uv run python -m benchmarking.analysis.per_run.render_md experiments/slack/runs/<timestamp>__slack
   ```

## Step-by-step: cross-stack final analysis (LLM)

You have two run dirs already graded (each has `analysis.json`) — one baseline, one variant — and want a head-to-head report.

1. **Run the driver.** Roles (baseline vs. variant) are inferred from each dir's `results.json`:
   ```bash
   uv run benchmark final \
       --platform slack \
       --runs experiments/slack/runs/<timestamp>__slack \
              experiments/slack/runs/<timestamp>__hintas__topk10_batch-off_max5_rag-off
   ```
   Or use `--all` when `experiments/<platform>/runs/` holds exactly two dirs:
   ```bash
   uv run benchmark final --platform slack --all
   ```
2. **Output lands at** `experiments/<platform>/final/<timestamp>/final_analysis.{json,md}`. The driver auto-precomputes `analysis_data.json` for any run dir missing it.
3. **Re-render only.** If `final_analysis.json` exists but the markdown is stale:
   ```bash
   uv run python -m benchmarking.analysis.final.render_final_md experiments/slack/final/<timestamp>
   ```

## Step-by-step: deterministic alternatives (no LLM)

Use these when you trust the per-run verdicts on disk and want to skip the LLM grader entirely.

- **Two-stack comparison** — same shape as the LLM driver:
  ```bash
  uv run benchmark aggregate --platform slack --all
  uv run python -m benchmarking.analysis.final.render_final_md experiments/slack/final/<timestamp>
  ```
- **N-way comparison** (1 baseline + N variants, e.g. several Hintas configs):
  ```bash
  uv run benchmark combine \
      --platform notion \
      --baseline experiments/notion/runs/<ts>__notion \
      --variants experiments/notion/runs/<ts>__hintas__<paramsA> \
                 experiments/notion/runs/<ts>__hintas__<paramsB> \
                 experiments/notion/runs/<ts>__hintas__<paramsC>
  ```
  Output: `experiments/<platform>/final/<timestamp>/combined_comparison.md`.

## Adding a new platform

`benchmark scaffold <name>` writes a placeholder grading prompt to `src/benchmarking/analysis/per_run/<name>_analysis_prompt.md` and points the platform's manifest at it. Optionally drop a `notes/notes_<name>.md` file with platform-specific grading rules — both drivers pick it up automatically based on `--platform`.

## Path conventions

- Run output (gitignored under `experiments/<platform>/runs/`, `experiments/<platform>/final/`) is rooted at the platform directory. Drivers receive that directory as `Platform.root` from the manifest loader.
- Grading prompts and platform notes are package data — `analysis_prompt.md`, `final_analysis_prompt.md`, and `notes/notes_<platform>.md` are resolved against `ANALYSIS_DIR = Path(__file__).parent`. Editing them means editing the source tree.
- The `analysis.prompt_template` field in each platform TOML is now relative to `src/benchmarking/analysis/` (e.g. `per_run/analysis_prompt.md`), not the repo root.
