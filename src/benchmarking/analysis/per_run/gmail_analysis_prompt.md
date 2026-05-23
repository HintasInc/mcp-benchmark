<!--
TODO: customize this analysis prompt for the Gmail benchmark.

Seeded by scaffold.py from analysis/per_run/analysis_prompt.md. Review
the tool-name normalisation rules, expected stack names, and any workspace-
specific grading language before running a real analysis pass.
-->

You are grading a single-stack benchmark of **{{STACK_DISPLAY_NAME}}** (`{{STACK}}`) for the {{PLATFORM_DISPLAY_NAME}} platform by reading a precomputed JSON summary of each session.

## Required outputs (read this first)

You MUST end this run by calling the **Write** tool twice to create exactly these files:

- `{{RUN_DIR}}/analysis.json`
- `{{RUN_DIR}}/analysis.md`

Both files must exist on disk when you finish. Printing their contents in chat is **not** a substitute — the orchestrating script checks the filesystem and aborts the pipeline if either file is missing. Do not summarise instead of writing. Do not skip the Write calls because the files "look like documentation" — they are pipeline outputs, explicitly requested.

## Inputs

- **Run directory:** `{{RUN_DIR}}`
- **Timestamp:** `{{TIMESTAMP}}`
- **Precomputed data:** `{{RUN_DIR}}/analysis_data.json`

The raw `session.log` and `token_trace.json` files have already been parsed by `analysis/precompute.py`. **Do not read them.** Read only `analysis_data.json` — it contains everything you need.

### Shape of `analysis_data.json`

```jsonc
{
  "run_dir": "...",
  "stacks": ["{{STACK}}"],
  "per_prompt": {
    "<id>": {
      "title": "...", "difficulty": "L2", "category": "retrieval",
      "success_criteria": [...],
      "prompt": "the literal user prompt",
      "{{STACK}}": {
        "has_result": true,                  // false ⇒ session crashed; mark ERROR
        "result_subtype": "success" | "error" | "",
        "result_is_error": true | false | null,
        "result_text": "the model's final answer to the user",
        "tool_calls": {"complete": N, "failed": N, "partial": N, "total": N},
        "tools_invoked": [...],
        "failed_details": [{"name": "...", "error": "..."}, ...],
        "initial_context": N,
        "peak_context":    N,
        "total_tokens":    N,
        "wall_clock_s":    N,
        "orchestrator_error": null | "string",
        "transcript": [
          {"role": "user",      "type": "prompt",      "text": "..."},
          {"role": "assistant", "type": "thinking",    "text": "..."},
          {"role": "assistant", "type": "text",        "text": "..."},
          {"role": "assistant", "type": "tool_use",
             "tool_use_id": "...", "tool_name": "...", "tool_name_raw": "...",
             "arguments": {...}, "arguments_truncated": false},
          {"role": "tool",      "type": "tool_result",
             "tool_use_id": "...", "is_error": false,
             "result_excerpt": "...", "result_truncated": true, "result_total_chars": N},
          {"role": "result",    "type": "final",       "text": "..."}
        ],
        "transcript_meta": {"total_turns": N, "total_chars": N,
                            "tools_truncated": N, "results_truncated": N,
                            "has_result": true, "unknown_events": []}
      }
    }
  }
}
```

The `transcript` is the cleaned working trace of the session — each turn the agent took, the arguments it passed to each MCP tool, what the tool returned (truncated head+tail with `[truncated N chars]` marker for long results), and the final answer. Use it as primary evidence.

## Your job

For every prompt in `per_prompt`, assign a verdict to **{{STACK_DISPLAY_NAME}}** and explain it briefly. All mechanical numbers (tool counts, tokens, timings) are already computed — your only judgment call is the verdict, grounded in observed agent behaviour.

### Verdict assignment

Grade each prompt by reasoning about whether the **prompt's intent** was achieved given the **tool evidence** in the transcript. Do **not** treat `success_criteria` as a literal checklist — it is reference data captured at benchmark-authoring time, and workspace state may have drifted (new users joined, channels added, pages renamed). Use it to understand the expected outcome, not as a hard gate on exact values.

Walk these steps for every prompt:

#### Step 1 — Restate the prompt's intent

What is the agent being asked to *do*? What kinds of values must appear in the final answer for it to be useful? (e.g., "a list of users with display name + ID", "channel names with member counts", "a created page returning its URL"). The intent comes from the `prompt` text — not from `success_criteria`.

#### Step 2 — Trace tool evidence

Walk the `transcript`. Did the agent call the right tools? Did those tools return real data (not errors)? Does `result_text` cite that data, or is it inferred / fabricated? Cross-check `result_text` against the actual tool returns: if the final answer asserts something not supported by any tool result, that is **fabrication**.

#### Step 3 — Classify divergences from `success_criteria`

For each divergence between the agent's output and a criterion, classify it before letting it influence the verdict:

| Divergence type | Examples | Affects verdict? |
|---|---|---|
| **Drift** | Extra/missing items, count off by one or two, channel renames, new users joined, pages reordered — values are real and the prompt did not *explicitly* exclude them | **No** — informational only |
| **Filtering miss** | Agent included items the prompt explicitly said to exclude (e.g., bots when the prompt says "human users", revoked accounts when the prompt says "active") | **Yes** — PARTIAL or FAIL |
| **Required-output gap** | A value type the prompt asked for is missing (e.g., "with member counts" but no counts; "display name and user ID" but no IDs) | **Yes** — PARTIAL or FAIL |
| **Capability gap** | MCP did not expose the operation needed (visible in transcript — agent searched for / attempted a capability that wasn't available) | **FAIL** |
| **Fabrication** | Final answer cites data not present in any tool return | **FAIL** |
| **Env rejection blocking task** | "Page not shared", "missing scope", "404 / not accessible" — and the task could not be completed | **FAIL** (platform-notes rules below still apply for known-infeasible / access-boundary prompts) |

#### Step 4 — Pick the verdict

- **PASS** — Prompt's intent was achieved. The agent called the right tools, the tools returned usable data, and the final answer reflects that data with the required output types present. **Drift-only divergences from `success_criteria` are acceptable** and must not lower the verdict.
- **PARTIAL** — Intent partially achieved. A meaningful component is missing (one required output type omitted, one of multiple sub-tasks skipped), or a filtering miss affected part of the answer.
- **FAIL** — Intent was not achieved. Triggers: capability gap, fabrication, no usable output, filtering miss that misrepresents the answer, missing required output type, or environmental rejection that blocked the task. Platform-notes rules (infeasible prompts, access-boundary prompts) still mark FAIL.
- **ERROR** — Infrastructure failure: `has_result == false`, `orchestrator_error` non-null, or `result_subtype == "error"` with no usable output. Distinct from FAIL (which is a grading signal).

Judge from observed behaviour, not from tool-name presence. The question is whether the transcript shows the agent achieving the prompt's intent — `success_criteria` is one signal among others, not the verdict itself.

#### Reasoning requirements

Give a 1–2 sentence `reasoning` for each verdict. It must:

- Lead with whether the prompt's intent was achieved (yes / partially / no).
- Cite the *real* cause of any non-PASS verdict — drift in counts/names is **not** a valid cause on its own.
- When `success_criteria` and agent output diverge, name the divergence type (drift / filtering miss / required-output gap / capability gap / fabrication / env rejection).
- Cite specific tool names from `tools_invoked`, the actual data the tool returned (from `result_excerpt`), or short fragments of `result_text`. **Only quote text that literally appears in the transcript or `result_text`** — do not invent or paraphrase as quotation.

#### Worked examples (calibration)

- **Drift, not failure.** Prompt: "List every public channel in the Hintas workspace." `success_criteria` says "9 channels: …". Agent calls `conversations.list`, returns 12 real public channels. → **PASS**. Intent (enumerate public channels) achieved with grounded tool data; three extra channels are workspace drift since authoring; the prompt did not pin a specific list.
- **Required-output gap, real failure.** Prompt: "List every public channel **with member counts visible**." Agent returns channel names but no counts. → **FAIL** (required-output gap / capability gap). Reasoning cites the missing member counts — not the channel-count drift.
- **Drift in user enumeration.** Prompt: "List every active human user… display name and user ID." `success_criteria` lists 8 names. Agent returns those 8 + the workspace owner (real, active, human). Bots correctly excluded. → **PASS**. Owner is a real active human; the prompt did not say "exclude owner". Drift only.
- **Filtering miss.** Same prompt as above. Agent returns 8 humans + the Hintas Agent bot. → **FAIL** (filtering miss). The prompt said "human users" and a bot was included.
- **Env rejection on known-infeasible prompt.** Notion prompt 59 (per `notes_notion.md`, infeasible via public API). Agent reports cleanly that the operation is not exposed. → **FAIL** (platform-notes rule still applies).

### Noteworthy paths

In addition to the verdict, populate `noteworthy_paths` — a list of short observations (≤120 chars each) describing **observed model behaviour worth attention**, not redundant with verdict reasoning. Examples:

- Unusual tool sequences ("Called `users.list` 4× before falling back to `users.lookupByEmail`")
- Recovery from errors ("Initial `chat.postMessage` failed with `not_in_channel`; recovered by `conversations.join` then retrying")
- Fabrication attempts ("Returned a permalink that no tool result produced")
- Tool-arg shape mistakes ("Passed `channel_id` where API expects `channel`; tool errored before retrying")
- Capability assumptions (acted on a resource flagged as not shared / not exposed)

Empty list (`[]`) is fine if nothing notable happened. These are observations, not judgements — keep them concise and concrete.

{{PLATFORM_NOTES}}

## Outputs

Write two files inside the run directory using your Write tool.

### 1. `{{RUN_DIR}}/analysis.json`

```json
{
  "timestamp": "{{TIMESTAMP}}",
  "stacks": ["{{STACK}}"],
  "per_prompt": {
    "<id>": {
      "title": "...",
      "difficulty": "L2",
      "category": "retrieval",
      "{{STACK}}": {
        "verdict": "PASS|PARTIAL|FAIL|ERROR",
        "reasoning": "...",
        "noteworthy_paths": ["...", "..."],
        "tool_calls": {"complete": N, "failed": N, "partial": N},
        "tools_invoked": [...],
        "initial_context": N,
        "peak_context": N,
        "total_tokens": N,
        "wall_clock_s": N
      }
    },
    ...
  },
  "aggregates": {
    "{{STACK}}": {
      "n": N,
      "pass": N, "partial": N, "fail": N, "error": N,
      "pass_rate": 0.xx,
      "avg_initial_context": N,
      "avg_peak_context": N,
      "avg_wall_clock_s": N,
      "total_tokens": N,
      "avg_tool_calls": N,
      "total_tool_failures": N
    }
  },
  "breakdowns": {
    "by_difficulty": {
      "L1": {"n": N, "pass_rate": 0.xx, "partial": N, "fail": N, "error": N},
      ...
    },
    "by_category": {
      "retrieval": {"n": N, "pass_rate": 0.xx, "partial": N, "fail": N, "error": N},
      ...
    }
  }
}
```

`pass_rate` counts PASS only (strict). Token and timing averages cover every prompt, not just passes.

### 2. `{{RUN_DIR}}/analysis.md`

Human-readable markdown report scoped to **{{STACK_DISPLAY_NAME}}** only. Cross-stack comparison happens at the final-analysis stage; don't attempt it here.

1. **Title** — `# Benchmark Analysis — {{STACK_DISPLAY_NAME}} — Run <timestamp>`
2. **Scope** — one line: N prompts × {{STACK_DISPLAY_NAME}}, graded against precomputed session summaries.
3. **Verdict legend** — explain PASS / PARTIAL / FAIL / ERROR briefly. State explicitly that (a) `success_criteria` is reference data; drift-only divergences (extra users, new channels, renames) do not lower the verdict, and (b) environmental rejections that block the task are FAIL.
4. **Per-prompt results** table, columns: `ID | Title | Diff | Verdict | Time | Tokens | Tool calls | Tool fails`.
5. **Initial vs peak context** table: `ID | Title | Initial | Peak`.
6. **Aggregates** — Prompts run, Pass rate, Passes, Partial, Fails, Errors, Avg tokens, Total tokens, Avg tool calls, Total tool failures, Avg wall clock.
7. **Breakdown by difficulty** table (L1..L5): `Difficulty | n | Pass rate | P/F/E counts`.
8. **Breakdown by category** table.
9. **Notable failures** — up to 8 bullets describing the most instructive PARTIAL/FAIL/ERROR rows. Lead with prompt ID, then the cause (missing tool, permission error, partial tool call, wrong result, env rejection, etc.).

Use pipe-delimited markdown tables with right-aligned numerics (`---:` in the header), ✓ for PASS, ✗ for FAIL, ◐ for PARTIAL, ⚠ for ERROR.

## Rules

- **Read only `analysis_data.json`.** The raw session logs are off-limits — the cleaned `transcript` field already contains the relevant trace.
- **No hallucination.** If `result_text` is empty, say so. Never quote strings that aren't in the transcript or `result_text`.
- **Ground verdicts in the transcript.** When you cite "the agent did X", X must be visible in the transcript (a tool_use, a tool_result excerpt, a thinking/text block, or `result_text`).
- **`success_criteria` is reference data, not a checklist.** Drift-only divergences (extra/missing items, count off by one or two, channel renames, new users joined) do not lower the verdict. Only filtering misses, required-output gaps, capability gaps, fabrication, or env rejections do.
- **Work prompt-by-prompt while building `analysis.json`.** This keeps your own context bounded.
- **Do not re-read files you've already written.** Once you call Write on `analysis.json`, do not Read it back to verify or compose `analysis.md` — write `analysis.md` from the same in-context data.
- **Write both files using the Write tool.** After writing, print a short (≤10 line) summary to stdout — pass rate, total tokens, one headline finding.
- **Do not invoke any MCP tools.** You're grading data, not talking to the platform.

Now call the **Write** tool twice — once for `{{RUN_DIR}}/analysis.json` and once for `{{RUN_DIR}}/analysis.md`. Do not skip this step. Do not paste the content into chat instead.

Begin.
