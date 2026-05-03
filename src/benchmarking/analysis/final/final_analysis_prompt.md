You are producing the **FINAL numerical verdict** for a head-to-head MCP benchmark on the **{{PLATFORM_DISPLAY_NAME}}** platform. The baseline is **{{BASELINE_DISPLAY_NAME}}** (`{{BASELINE_STACK}}`); the variant under evaluation is **{{VARIANT_DISPLAY_NAME}}** (`{{VARIANT_STACK}}`).

Each stack ran in its own single-stack run directory. Your job is to score every prompt on each stack and emit one comparison report.

This prompt is intentionally light on prose. Output is dominated by tables and tallies. Narrative is allowed only where it explains a number.

## Required outputs (read this first)

You MUST end this run by calling the **Write** tool twice to create exactly:

- `{{OUTPUT_DIR}}/final_analysis.json`
- `{{OUTPUT_DIR}}/final_analysis.md`

Both files must exist on disk when you finish. Printing their contents in chat is **not** a substitute. Do not skip the Write calls because the files "look like documentation" — they are pipeline outputs, explicitly requested.

## Inputs

- **Baseline run directory** (`{{BASELINE_STACK}}`): `{{BASELINE_RUN_DIR}}`
- **Variant run directory**  (`{{VARIANT_STACK}}`): `{{VARIANT_RUN_DIR}}`
- **Output directory:** `{{OUTPUT_DIR}}`
- **Timestamp:** `{{TIMESTAMP}}`
- **Per-run precomputed data:** `<run_dir>/analysis_data.json` for each run dir
- **(Optional) prior verdicts:** each run dir may already contain a single-stack `analysis.json`. Treat it as informational only — re-grade every prompt under the rules below.

The raw `session.log` and `token_trace.json` files are off-limits. Read **only** `analysis_data.json` from each dir (and `analysis.json` if present and you want a hint).

### Shape of `<run_dir>/analysis_data.json`

Each run dir's `analysis_data.json` holds **exactly one stack**:

```jsonc
{
  "run_dir": "...",
  "run_at": "...",
  "platform": "{{PLATFORM_DISPLAY_NAME}}",
  "stacks": ["<stack>"],   // baseline dir → ["{{BASELINE_STACK}}"], variant dir → ["{{VARIANT_STACK}}"]
  "per_prompt": {
    "<id>": {
      "title": "...", "difficulty": "L2", "category": "retrieval",
      "success_criteria": [...], "prompt": "...",
      "<stack>": {
        "has_result": true|false,
        "result_subtype": "success" | "error" | "",
        "result_is_error": true | false | null,
        "result_text": "...",
        "tool_calls": {"complete": N, "failed": N, "partial": N, "total": N},
        "tools_invoked": [...],
        "failed_details": [{"name": "...", "error": "..."}, ...],
        "initial_context": N, "peak_context": N,
        "total_tokens":    N, "wall_clock_s": N,
        "orchestrator_error": null | "string",
        "transcript": [
          {"role": "user", "type": "prompt", "text": "..."},
          {"role": "assistant", "type": "thinking|text", "text": "..."},
          {"role": "assistant", "type": "tool_use",
             "tool_name": "...", "arguments": {...}},
          {"role": "tool", "type": "tool_result",
             "is_error": false, "result_excerpt": "...",
             "result_truncated": true, "result_total_chars": N},
          {"role": "result", "type": "final", "text": "..."}
        ],
        "transcript_meta": {"total_turns": N, "total_chars": N,
                            "tools_truncated": N, "results_truncated": N,
                            "has_result": true, "unknown_events": []}
      }
    }
  }
}
```

The `transcript` is the cleaned working trace of the session — what arguments the agent passed to each MCP tool, what each tool returned (truncated head+tail with a `[truncated N chars]` marker for long payloads), and the final answer. Use it as primary verdict evidence — not metadata aggregates.

To compare a prompt across stacks: read the prompt's entry under `{{BASELINE_STACK}}` from the baseline dir's file and under `{{VARIANT_STACK}}` from the variant dir's file. Use prompt id (the `<id>` key) to align rows. Always present **{{BASELINE_DISPLAY_NAME}} first, {{VARIANT_DISPLAY_NAME}} second** in tables.

## Verdict rules (apply per prompt × stack)

Grade each (prompt × stack) by reasoning about whether the **prompt's intent** was achieved given the **tool evidence** in that stack's `transcript`. Do **not** treat `success_criteria` as a literal checklist — it is reference data captured at benchmark-authoring time, and workspace state may have drifted (new users joined, channels added, pages renamed). Use it to understand the expected outcome, not as a hard gate on exact values. Two stacks may reach the same outcome via different tool sequences — judge each stack on its own transcript.

Walk these steps per prompt × stack:

### Step 1 — Restate the prompt's intent

What is the agent being asked to *do*? What kinds of values must appear in the final answer for it to be useful? The intent comes from the `prompt` text — not from `success_criteria`.

### Step 2 — Trace tool evidence

Walk the stack's `transcript`. Did the agent call the right tools? Did those tools return real data (not errors)? Does `result_text` cite that data, or is it inferred / fabricated? Cross-check `result_text` against tool returns: if the final answer asserts something not supported by any tool result, that is **fabrication**.

### Step 3 — Classify divergences from `success_criteria`

For each divergence between the agent's output and a criterion, classify it before letting it influence the verdict:

| Divergence type | Examples | Affects verdict? |
|---|---|---|
| **Drift** | Extra/missing items, count off by one or two, channel renames, new users joined, pages reordered — values are real and the prompt did not *explicitly* exclude them | **No** — informational only |
| **Filtering miss** | Agent included items the prompt explicitly said to exclude (e.g., bots when prompt says "human users", revoked accounts when prompt says "active") | **Yes** — PARTIAL or FAIL |
| **Required-output gap** | A value type the prompt asked for is missing (e.g., "with member counts" but no counts; "display name and user ID" but no IDs) | **Yes** — PARTIAL or FAIL |
| **Capability gap** | MCP did not expose the operation needed (visible in transcript — agent searched for / attempted a capability that wasn't available) | **FAIL** |
| **Fabrication** | Final answer cites data not present in any tool return | **FAIL** |
| **Env rejection blocking task** | "Page not shared", "missing scope", "404 / not accessible" — and the task could not be completed | **FAIL** (platform-notes rules below still apply for known-infeasible / access-boundary prompts) |

### Step 4 — Pick the verdict

- **PASS** — Prompt's intent was achieved. Agent called the right tools, tools returned usable data, and the final answer reflects that data with the required output types present. **Drift-only divergences from `success_criteria` are acceptable** and must not lower the verdict.
- **PARTIAL** — Intent partially achieved. A meaningful component is missing (one required output type omitted, one of multiple sub-tasks skipped), or a filtering miss affected part of the answer. Multi-step prompts where only part of the work landed are PARTIAL, not PASS.
- **FAIL** — Intent was not achieved. Triggers: capability gap, fabrication, no usable output, filtering miss that misrepresents the answer, missing required output type, or environmental rejection that blocked the task. Platform-notes rules (infeasible / access-boundary prompts) still mark FAIL.
- **ERROR** — Infrastructure failure: `has_result == false` OR `orchestrator_error` non-null OR `result_subtype == "error"` with no usable output. Distinct from FAIL (FAIL is a grading signal; ERROR is a harness failure).

Judge from observed behaviour, not from tool-name presence. The question is whether the transcript shows the agent achieving the prompt's intent — `success_criteria` is one signal among others, not the verdict itself.

### Reasoning per verdict

1–2 sentences. It must:

- Lead with whether the prompt's intent was achieved (yes / partially / no).
- Cite the *real* cause of any non-PASS verdict — drift in counts/names is **not** a valid cause on its own.
- When `success_criteria` and agent output diverge, name the divergence type (drift / filtering miss / required-output gap / capability gap / fabrication / env rejection).
- Cite specific tool names from `tools_invoked` or `transcript` when referenced. Quote only literal substrings of the transcript or `result_text` — never paraphrase as quotation.

### Worked examples (calibration)

- **Drift, not failure.** Prompt: "List every public channel in the Hintas workspace." `success_criteria` says "9 channels: …". Agent calls `conversations.list`, returns 12 real public channels. → **PASS**. Intent achieved with grounded tool data; the extra channels are drift, and the prompt did not pin a specific list.
- **Required-output gap, real failure.** Same domain, prompt: "List every public channel **with member counts visible**." Agent returns channel names but no counts. → **FAIL** (required-output gap / capability gap). Reasoning cites the missing member counts — not the channel-count drift.
- **Drift in user enumeration.** Prompt: "List every active human user… display name and user ID." `success_criteria` lists 8 names. Agent returns those 8 + the workspace owner (real, active, human). Bots correctly excluded. → **PASS**. Owner is a real active human; the prompt did not say "exclude owner".
- **Filtering miss.** Same prompt. Agent returns 8 humans + the Hintas Agent bot. → **FAIL** (filtering miss).
- **Env rejection on known-infeasible prompt.** Notion prompt 59 (per `notes_notion.md`, infeasible via public API). Agent reports cleanly that the operation is not exposed. → **FAIL** (platform-notes rule still applies).

### Noteworthy paths

In addition to the verdict, populate `noteworthy_paths` per stack — a list of short observations (≤120 chars each) describing **observed model behaviour worth attention**, not redundant with verdict reasoning. Examples:

- Unusual tool sequences ("Called `users.list` 4× before falling back to `users.lookupByEmail`")
- Recovery from errors ("Initial `chat.postMessage` failed with `not_in_channel`; recovered by `conversations.join` then retrying")
- Fabrication attempts ("Returned a permalink that no tool result produced")
- Tool-arg shape mistakes ("Passed `channel_id` where API expects `channel`; tool errored before retrying")
- Surprising shortcuts or divergent strategies between stacks
- Capability assumptions (acted on a resource flagged as not shared / not exposed)

Empty list (`[]`) is fine if nothing notable happened.

{{PLATFORM_NOTES}}

## Comparison rules (token / time)

A prompt's `total_tokens` and `wall_clock_s` are **only counted in cross-stack averages and totals when BOTH stacks earned PASS** for that prompt. If either side is PARTIAL, FAIL, or ERROR for a prompt, **exclude that prompt from comparison metrics** but still count it in verdict tallies and tool-call tallies.

Tool-call tallies (`tools_passed`, `tools_failed`, `tools_partial`) are **never excluded** — every tool call by every stack is counted, regardless of the prompt's verdict.

Compute the following per-stack derived numbers:

- `tools_passed`     = sum of `tool_calls.complete` across all prompts
- `tools_failed`     = sum of `tool_calls.failed` across all prompts
- `tools_partial`    = sum of `tool_calls.partial` across all prompts
- `tools_total`      = sum of `tool_calls.total` across all prompts
- `tokens_per_tool_call` (per prompt) = `total_tokens / max(1, tool_calls.total)`
- `comparable_total_tokens`     = sum of `total_tokens` over both-PASS prompts only
- `comparable_avg_wall_clock_s` = mean of `wall_clock_s` over both-PASS prompts only
- `comparable_avg_tokens_per_prompt`     = `comparable_total_tokens / |both-PASS|`
- `comparable_avg_tokens_per_tool_call`  = sum of `total_tokens` over both-PASS / sum of `tool_calls.total` over both-PASS

If a prompt id appears in only one of the two run dirs, treat the missing side as ERROR (no result) and exclude that prompt from comparable metrics. Note such gaps explicitly in the markdown.

## Outputs

Build the JSON in memory, write it once, then write the markdown from the same in-context state — do **not** re-read your own JSON file to render the markdown.

### 1. `{{OUTPUT_DIR}}/final_analysis.json`

```jsonc
{
  "timestamp": "{{TIMESTAMP}}",
  "platform": "{{PLATFORM_DISPLAY_NAME}}",
  "baseline_stack": "{{BASELINE_STACK}}",
  "variant_stack":  "{{VARIANT_STACK}}",
  "baseline_run_dir": "{{BASELINE_RUN_DIR}}",
  "variant_run_dir":  "{{VARIANT_RUN_DIR}}",
  "n_prompts": N,
  "per_prompt": {
    "<id>": {
      "title": "...", "difficulty": "...", "category": "...",
      "{{BASELINE_STACK}}": {
        "verdict": "PASS|PARTIAL|FAIL|ERROR",
        "reasoning": "...",
        "noteworthy_paths": ["...", "..."],
        "tools_passed":  N,
        "tools_failed":  N,
        "tools_partial": N,
        "tools_total":   N,
        "tokens_per_tool_call": F,
        "total_tokens":    N,
        "wall_clock_s":    N,
        "comparable":      true|false
      },
      "{{VARIANT_STACK}}": { ...same shape... }
    }
  },
  "totals": {
    "{{BASELINE_STACK}}": {
      "verdicts": {"PASS": N, "PARTIAL": N, "FAIL": N, "ERROR": N},
      "pass_rate": F,
      "tools_passed":  N, "tools_failed": N, "tools_partial": N, "tools_total": N,
      "tool_pass_rate": F,
      "comparable_n":            N,
      "comparable_total_tokens": N,
      "comparable_avg_wall_clock_s":    F,
      "comparable_avg_tokens_per_prompt":    F,
      "comparable_avg_tokens_per_tool_call": F
    },
    "{{VARIANT_STACK}}": { ...same shape... },
    "comparable_prompt_ids": [...],
    "excluded_prompt_ids":   [...]
  },
  "verdict": {
    "winner": "{{BASELINE_DISPLAY_NAME}}" | "{{VARIANT_DISPLAY_NAME}}" | "Tie",
    "speed_winner":            "...", "speed_margin_pct":   F,
    "tokens_winner":           "...", "tokens_margin_pct":  F,
    "accuracy_winner":         "...", "accuracy_margin_pp": F,
    "tool_reliability_winner": "...",
    "summary": "2–4 sentence cross-stack conclusion"
  }
}
```

`pass_rate` counts PASS only (strict). `tool_pass_rate` = `tools_passed / max(1, tools_total)`.

Margins are absolute percentages (positive numbers), with the `_winner` field naming who won. Use `"Tie"` when the two values are within 1% (or 0.5pp for accuracy / tool pass rate). The overall `winner` is whichever stack wins more of the four categories (Accuracy, Speed, Tokens, Tool reliability); fall back to `"Tie"` when the count is even.

### 2. `{{OUTPUT_DIR}}/final_analysis.md`

Numerical tables first; narrative only where it explains a number. Use pipe-delimited markdown tables with right-aligned numerics (`---:` in header) and `✓` / `◐` / `✗` / `⚠` for PASS / PARTIAL / FAIL / ERROR.

1. **Title** — `# Final Benchmark Analysis — {{PLATFORM_DISPLAY_NAME}} — <timestamp>`
2. **Scope** — one line: `<n_prompts>` prompts × 2 stacks ({{BASELINE_DISPLAY_NAME}}, {{VARIANT_DISPLAY_NAME}}). Bullet list with each run dir's path and `run_at`.
3. **Verdict legend** — one line each for PASS / PARTIAL / FAIL / ERROR. State explicitly that (a) `success_criteria` is reference data; drift-only divergences (extra users, new channels, renames) do not lower the verdict, and (b) environmental rejections that block the task are FAIL.
4. **Per-prompt results** table

   | ID | Title | Diff | {{BASELINE_DISPLAY_NAME}} | {{VARIANT_DISPLAY_NAME}} | B Tok | V Tok | B Time | V Time | ΔTok | ΔTime |

   ΔTok = V_tok − B_tok (negative ⇒ variant used fewer); ΔTime same. **Only fill ΔTok and ΔTime when both stacks earned PASS.** Otherwise write `*excl*` in both delta columns.
5. **Verdict tallies**

   | Stack | PASS | PARTIAL | FAIL | ERROR | Pass rate |

6. **Tool-call tallies (every prompt, regardless of verdict)**

   | Stack | Tools complete | Tools failed | Tools partial | Total | Tool pass rate |

7. **Comparable-only metrics (both stacks PASS)**

   - Comparable prompt IDs: `1, 4, 5, …` (count: N)
   - Excluded prompt IDs:   `7, 12, …` (count: N)

   | Metric | {{BASELINE_DISPLAY_NAME}} | {{VARIANT_DISPLAY_NAME}} | Δ (B − V) |

   Rows: Total tokens, Avg tokens / prompt, Avg tokens / tool call, Avg wall-clock (s).

8. **Final verdict**

   | Category | Winner | Margin |

   Rows: Accuracy (pass rate), Speed (avg wall-clock), Token efficiency (comparable total), Tool reliability (tool pass rate).

   One-line summary: `<Winner> wins <X>/4 categories.`

## Rules

- **Read only `analysis_data.json` per run.** Optionally peek at the run's old `analysis.json` for hints — but re-grade every prompt yourself.
- **No hallucination.** If `result_text` is empty, say so. Never quote strings that aren't in the transcript or `result_text`.
- **Ground verdicts in the transcript.** When you cite "the agent did X", X must be visible in the transcript.
- **Process prompt-by-prompt.** Build per-prompt JSON in memory, then totals, then verdict.
- **Don't re-read your own outputs.** After Write on `final_analysis.json`, render the markdown from the same in-context state.
- **Don't invoke any MCP tools.** You're grading data, not talking to {{PLATFORM_DISPLAY_NAME}}.
- **Strict verdict on env rejections.** A polite failure ("page not shared", "user doesn't exist", "integration lacks access") that blocked the task is FAIL, not PASS.
- **`success_criteria` is reference data, not a checklist.** Drift-only divergences (extra/missing items, count off by one or two, channel renames, new users joined) do not lower the verdict. Only filtering misses, required-output gaps, capability gaps, fabrication, or env rejections do.
- **Token comparison strictness.** Both-PASS only. PARTIAL excludes the row from comparison.

Now call **Write** twice — `{{OUTPUT_DIR}}/final_analysis.json` and `{{OUTPUT_DIR}}/final_analysis.md`. After writing, print a ≤10-line stdout summary: pass rates per stack, comparable-n, headline winner.

Begin.
