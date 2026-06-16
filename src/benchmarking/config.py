"""
Platform manifest loader.

Each platform (slack, discord, …) lives under `experiments/<name>/` with its
manifest at `experiments/<name>/<name>.toml`. Adding a new platform is purely
data: no code changes in the orchestrator scripts.
"""
from __future__ import annotations

import argparse
import os
import tomli
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv

from benchmarking.paths import ANALYSIS_DIR, PLATFORMS_DIR, REPO_ROOT

RUN_TS_FORMAT = "%Y%m%d_%H%M%S"


def load_platform_env(platform_name: str) -> list[Path]:
    """
    Load environment variables for a platform.

    Reads <repo>/experiments/<platform>/.env first (platform-specific, takes
    precedence), then <repo>/.env as a fallback for shared values. Neither file
    overwrites variables already set in the process environment.

    Returns the list of files that were actually loaded.
    """
    loaded: list[Path] = []
    for path in (PLATFORMS_DIR / platform_name / ".env", REPO_ROOT / ".env"):
        if path.exists():
            load_dotenv(path, override=False)
            loaded.append(path)
    return loaded


@dataclass(frozen=True)
class Stack:
    name: str
    display_name: str
    config_dir: str
    token_env: str
    mcp_server: str
    # Some remote MCP servers (e.g. Composio) only finish registering their
    # tools when the session starts with built-in tools present; under the
    # default `--tools ""` lock the first turn fires before their handshake
    # completes and no MCP tools load. When True, keep built-in tools available
    # but deny the ones that could bypass the MCP under test (see runner.py).
    keep_builtin_tools: bool = False


@dataclass(frozen=True)
class AnalysisConfig:
    display_name: str
    config_dir: str
    prompt_template: Path
    model: str


@dataclass(frozen=True)
class Platform:
    name: str
    display_name: str
    downstream_token_env: str
    root: Path
    prompts_file: Path
    reset_script: Path
    seed_script: Path
    verify_script: Path
    output_dir: Path
    stacks: tuple[Stack, ...]
    analysis: AnalysisConfig
    state_file_template: str | None = None
    prereq_file_template: str | None = None

    @property
    def stack_names(self) -> tuple[str, ...]:
        return tuple(s.name for s in self.stacks)

    @property
    def baseline_stack(self) -> Stack:
        return self.stacks[0]

    @property
    def variant_stack(self) -> Stack:
        if len(self.stacks) < 2:
            raise ValueError(f"platform {self.name!r} declares no variant stack")
        return self.stacks[1]

    def stack(self, name: str) -> Stack:
        for s in self.stacks:
            if s.name == name:
                return s
        raise KeyError(f"stack {name!r} not declared by platform {self.name!r}")

    def state_file_for(self, stack: Stack) -> Path | None:
        """Resolve the per-stack state-file path, or None if not configured.

        The template is platform-root relative and must contain `{stack}`,
        which is substituted with the stack's name.
        """
        if not self.state_file_template:
            return None
        return self.root / self.state_file_template.format(stack=stack.name)

    def prereq_file_for(self, stack: Stack) -> Path | None:
        """Resolve the per-stack prerequisites-file path, or None if not configured."""
        if not self.prereq_file_template:
            return None
        return self.root / self.prereq_file_template.format(stack=stack.name)


def _resolve(env_var: str, default: str) -> str:
    return os.environ.get(env_var, default)


def load_platform_from_path(toml_path: Path) -> Platform:
    toml_path = Path(toml_path).resolve()
    if not toml_path.exists():
        raise FileNotFoundError(f"platform manifest not found: {toml_path}")

    with open(toml_path, "rb") as f:
        data = tomli.load(f)

    paths_data    = data["paths"]
    stacks_data   = data["stacks"]
    analysis_data = data["analysis"]

    if not stacks_data:
        raise ValueError(f"platform {toml_path.name} must declare at least one stack")

    stacks = tuple(
        Stack(
            name=s["name"],
            display_name=s["display_name"],
            config_dir=_resolve(s["config_dir_env"], s["config_dir_default"]),
            token_env=s["token_env"],
            mcp_server=s["mcp_server"],
            keep_builtin_tools=s.get("keep_builtin_tools", False),
        )
        for s in stacks_data
    )

    analysis = AnalysisConfig(
        display_name=analysis_data.get("display_name", "Analyzer Claude"),
        config_dir=_resolve(analysis_data["config_dir_env"], analysis_data["config_dir_default"]),
        prompt_template=ANALYSIS_DIR / analysis_data["prompt_template"],
        model=analysis_data["model"],
    )

    platform_root = toml_path.parent
    return Platform(
        name=data["name"],
        display_name=data["display_name"],
        downstream_token_env=data["downstream_token_env"],
        root=platform_root,
        prompts_file=platform_root / paths_data["prompts_file"],
        reset_script=platform_root / paths_data["reset_script"],
        seed_script=platform_root / paths_data["seed_script"],
        verify_script=platform_root / paths_data["verify_script"],
        output_dir=platform_root / paths_data.get("output_dir", "runs"),
        stacks=stacks,
        analysis=analysis,
        state_file_template=paths_data.get("state_file_template"),
        prereq_file_template=paths_data.get("prereq_file_template"),
    )


def load_platform(name: str) -> Platform:
    """Load experiments/<name>/<name>.toml."""
    return load_platform_from_path(PLATFORMS_DIR / name / f"{name}.toml")


def available_platforms() -> list[str]:
    if not PLATFORMS_DIR.exists():
        return []
    return sorted(
        p.parent.name
        for p in PLATFORMS_DIR.glob("*/*.toml")
        if p.stem == p.parent.name
    )


def hintas_params_dict(args) -> dict:
    """Structured Hintas server-side params; recorded in results.json."""
    return {
        "search_top_k":         args.search_top_k,
        "search_batch_enabled": bool(args.search_batch_enabled),
        "search_max_results":   args.search_max_results,
        "rag_enabled":          bool(args.rag_enabled),
    }


def hintas_param_summary(args) -> str:
    """Compact, fixed-order Hintas params encoded for run-dir names."""
    p = hintas_params_dict(args)
    return "_".join([
        f"topk{p['search_top_k']}",
        f"batch-{'on' if p['search_batch_enabled'] else 'off'}",
        f"max{p['search_max_results']}",
        f"rag-{'on' if p['rag_enabled'] else 'off'}",
    ])


def build_run_subdir(args, platform: Platform, stack: Stack, run_ts: str) -> str:
    """`<timestamp>__<stack>` plus a Hintas param summary when running the variant."""
    parts = [run_ts, stack.name]
    if stack.name == platform.variant_stack.name:
        parts.append(hintas_param_summary(args))
    return "__".join(parts)


def preload_platform(default: str | None = "slack") -> Platform | None:
    """First-pass argparse helper: scan argv for --platform, load that
    platform's .env files and manifest, and return the parsed Platform.

    Used by every CLI that registers platform-specific defaults (paths,
    stack choices) in its main argparse parser. Returns None when the
    caller passes default=None and --platform is absent.
    """
    pre = argparse.ArgumentParser(add_help=False)
    pre.add_argument("--platform", default=default)
    pre_args, _ = pre.parse_known_args()
    name = pre_args.platform
    if not name:
        return None
    load_platform_env(name)
    return load_platform(name)
