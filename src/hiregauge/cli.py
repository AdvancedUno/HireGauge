"""HireGauge command-line interface.

``hiregauge --agent <name> [inputs] [experience] [model/output]`` runs an evaluation;
``hiregauge agents`` lists the evaluator agents and their rubrics.
"""

from __future__ import annotations

import sys
from pathlib import Path

import typer
from rich.console import Console
from rich.table import Table

from . import __version__
from .agents import all_agents, get_agent
from .config import Settings, get_settings
from .llm.factory import default_model_for
from .models import AgentName, CareerStage, ExperienceContext, Mode, OutputFormat, Provider

# Best-effort UTF-8 output so Rich glyphs render on Windows consoles.
for _stream in (sys.stdout, sys.stderr):
    try:
        _stream.reconfigure(encoding="utf-8")  # type: ignore[union-attr]
    except Exception:  # noqa: BLE001
        pass

app = typer.Typer(
    add_completion=False,
    no_args_is_help=True,
    help="HireGauge — specialized, multi-agent candidate self-assessment "
    "(quant · airesearch · bigtech · general · university).",
)
console = Console()


def _rubric_table(agent_name: str) -> Table:
    a = get_agent(agent_name)
    table = Table(
        title=f"Rubric - [bold]{a.name}[/bold] ({a.title}) - weights sum to {a.weight_total():g}",
        title_justify="left",
    )
    table.add_column("Dimension")
    table.add_column("Weight", justify="right")
    table.add_column("GT", justify="center")
    for d in a.dimensions:
        table.add_row(d.label, f"{d.weight:g}", "*" if d.is_blended else "")
    return table


@app.command("agents")
def agents_cmd() -> None:
    """List the evaluator agents and the dimensions/signals each weights."""
    for a in all_agents():
        console.print(
            f"[bold cyan]{a.name}[/bold cyan] - {a.title}   "
            f"[dim](signals: {', '.join(a.signals)})[/dim]"
        )
        console.print(_rubric_table(a.name))
        console.print()
    console.print("[dim]* = score is blended with a deterministic ground-truth signal (GitHub / Scholar).[/dim]")


def _resolve_model(model: str | None, prov: str, settings: Settings) -> str:
    """Resolve the model id. An explicit --model wins; a configured DEFAULT_MODEL applies
    only to the default provider (so switching --provider falls back to that provider's
    own default rather than sending another provider's model id)."""
    if model:
        return model
    if settings.default_model and prov == settings.default_provider:
        return settings.default_model
    return default_model_for(prov)


def _provider_or_exit(cfg, settings: Settings):
    """Resolve the LLM provider and verify it is usable *before* any collection runs.

    A missing key, missing SDK, or unimplemented provider is a hard misconfiguration:
    report it clearly and exit non-zero rather than running a full collection pass that
    can only end in a 0/100 "could not be completed" report (issue #19)."""
    from .llm.factory import build_provider

    try:
        provider = build_provider(cfg.provider, cfg.model, settings)
        provider.preflight()
    except (NotImplementedError, ValueError, RuntimeError) as exc:
        console.print(f"[bold red]Configuration error:[/bold red] {exc}")
        raise typer.Exit(code=2) from exc
    return provider


def _execute(cfg, fmt: str, out: str | None, settings: Settings) -> None:
    from rich.markdown import Markdown

    from .pipeline import run as run_pipeline
    from .report import render_html, render_markdown

    provider = _provider_or_exit(cfg, settings)

    a = get_agent(cfg.agent)
    console.print(
        f"[bold]{a.title}[/bold] · {cfg.experience.describe()} · "
        f"[dim]{cfg.provider}:{cfg.model}[/dim]"
    )
    with console.status("[bold]Collecting signals + evaluating…[/bold]", spinner="dots"):
        report = run_pipeline(cfg, provider=provider)

    md = render_markdown(report)
    if fmt == "json":
        file_content = report.model_dump_json(indent=2)
    elif fmt == "html":
        file_content = render_html(report)
    else:
        file_content = md

    if out:
        Path(out).write_text(file_content, encoding="utf-8")
        console.print(f"[green]Wrote[/green] {out}")

    if fmt == "json":
        console.print_json(file_content)
    else:
        console.print(Markdown(md))


@app.callback(invoke_without_command=True)
def main(
    ctx: typer.Context,
    agent: AgentName | None = typer.Option(None, "--agent", "-a", help="Evaluator agent (default: general)."),
    # --- inputs ---
    resume: str | None = typer.Option(None, "--resume", help="Path to resume PDF/text."),
    github: str | None = typer.Option(None, "--github", help="GitHub username or profile URL."),
    scholar: str | None = typer.Option(None, "--scholar", help="Google Scholar profile URL."),
    orcid: str | None = typer.Option(None, "--orcid", help="ORCID id."),
    arxiv: str | None = typer.Option(None, "--arxiv", help="arXiv author id or URL."),
    codeforces: str | None = typer.Option(None, "--codeforces", help="Codeforces handle."),
    leetcode: str | None = typer.Option(None, "--leetcode", help="LeetCode handle (best-effort)."),
    kaggle: str | None = typer.Option(None, "--kaggle", help="Kaggle handle."),
    site: str | None = typer.Option(None, "--site", help="Portfolio/blog URL."),
    linkedin: str | None = typer.Option(None, "--linkedin", help="LinkedIn export PDF (manual)."),
    # --- experience / level ---
    yoe: float | None = typer.Option(None, "--yoe", help="Years of professional experience."),
    level: CareerStage | None = typer.Option(None, "--level", help="Career stage / seniority."),
    target_level: CareerStage | None = typer.Option(
        None, "--target-level", help="Aspirational stage/role to aim for."
    ),
    title: str | None = typer.Option(None, "--title", help="Current title."),
    # --- target ---
    role: str | None = typer.Option(None, "--role", help="Target role to match against."),
    jd: str | None = typer.Option(None, "--jd", help="Job-description file to match against."),
    # --- model / output ---
    provider: Provider | None = typer.Option(
        None, "--provider", help="LLM backend (default: DEFAULT_PROVIDER, else gemini)."
    ),
    model: str | None = typer.Option(None, "--model", help="Model id (default: per-provider)."),
    mode: Mode = typer.Option(Mode.candidate, "--mode", help="Report mode."),
    fmt: OutputFormat = typer.Option(OutputFormat.md, "--format", help="Report format."),
    out: str | None = typer.Option(None, "--out", help="Write the report to this path."),
    no_cache: bool = typer.Option(False, "--no-cache", help="Bypass the API response cache."),
    verbose: bool = typer.Option(False, "--verbose", "-v", help="Verbose output."),
    version: bool = typer.Option(False, "--version", help="Show version and exit."),
) -> None:
    if version:
        console.print(f"hiregauge {__version__}")
        raise typer.Exit()
    if ctx.invoked_subcommand is not None:
        return
    has_input = any(
        [resume, github, scholar, orcid, arxiv, codeforces, leetcode, kaggle, site, linkedin]
    )
    if agent is None and not has_input:
        console.print(ctx.get_help())
        raise typer.Exit()
    agent_value = agent.value if agent is not None else "general"

    settings = get_settings()
    prov = provider.value if provider is not None else settings.default_provider
    mdl = _resolve_model(model, prov, settings)
    exp = ExperienceContext(yoe=yoe, stage=level, target_stage=target_level, current_title=title)

    from .pipeline import RunConfig

    cfg = RunConfig(
        agent=agent_value,
        resume=resume, github=github, scholar=scholar, orcid=orcid, arxiv=arxiv,
        codeforces=codeforces, leetcode=leetcode, kaggle=kaggle, site=site, linkedin=linkedin,
        role=role, jd=jd, experience=exp,
        provider=prov, model=mdl, mode=mode.value, no_cache=no_cache,
    )
    _execute(cfg, fmt.value, out, settings)


if __name__ == "__main__":  # pragma: no cover
    app()
