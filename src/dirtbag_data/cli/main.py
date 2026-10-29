"""``dirtbag`` command line interface.

Commands (spec §36):
    dirtbag crawl <scope> [--source ...] [--incremental]
    dirtbag status
    dirtbag validate
    dirtbag reconcile
"""

from __future__ import annotations

from pathlib import Path

import typer
from rich.console import Console

from dirtbag_data import __version__
from dirtbag_data.config import Settings, load_settings

app = typer.Typer(name="dirtbag", help="DirtBag Data Acquisition CLI", no_args_is_help=True)
console = Console()


def _settings(config: Path | None) -> Settings:
    try:
        return load_settings(config)
    except FileNotFoundError:
        console.print(f"[red]Config file not found:[/red] {config or 'configs/development.yaml'}")
        raise typer.Exit(code=1) from None


def _mask_url(url: str) -> str:
    """Hide credentials of a database URL for display."""
    if "@" not in url or "://" not in url:
        return url
    scheme, rest = url.split("://", 1)
    creds, host = rest.rsplit("@", 1)
    user = creds.split(":", 1)[0]
    return f"{scheme}://{user}:***@{host}"


@app.command()
def status(config: Path | None = typer.Option(None, "--config", help="Path to YAML config")) -> None:
    """Show configuration and module status."""
    settings = _settings(config)
    console.print(f"[bold]dirtbag-data[/bold] v{__version__}")
    console.print(f"database:  {_mask_url(settings.database.url)}")
    console.print(f"raw store: {settings.storage.raw_path}")
    enabled = settings.crawlers.enabled_sources()
    console.print(f"sources:   {', '.join(enabled) if enabled else '(none enabled)'}")


@app.command()
def crawl(
    scope: str = typer.Argument(
        ..., help="Seed key from config (e.g. el-salto) or a full https:// URL"
    ),
    source: str = typer.Option("thecrag", "--source", help="Source adapter name"),
    limit: int | None = typer.Option(
        None, "--limit", help="Max route pages to fetch in this run"
    ),
    dry_run: bool = typer.Option(
        False, "--dry-run", help="Fetch + parse but write nothing to the database"
    ),
    config: Path | None = typer.Option(None, "--config", help="Path to YAML config"),
) -> None:
    """Crawl an area tree from a seed and store source observations."""
    import asyncio

    settings = _settings(config)
    if source != "thecrag":
        console.print(f"[red]Adapter not available:[/red] {source} (only 'thecrag')")
        raise typer.Exit(code=1)
    src_cfg = settings.crawlers.sources.get(source)
    if src_cfg is None:
        console.print(f"[red]Source not in config:[/red] {source}")
        raise typer.Exit(code=1)

    if scope.startswith(("http://", "https://")):
        seed_url = scope
    else:
        seed_url = src_cfg.seeds.get(scope)
        if seed_url is None:
            available = ", ".join(sorted(src_cfg.seeds)) or "(none)"
            console.print(
                f"[red]Unknown scope[/red] {scope!r} for {source}. "
                f"Seeds: {available} — or pass a full URL."
            )
            raise typer.Exit(code=1)

    from dirtbag_data.crawlers.thecrag.crawler import crawl_area_tree

    summary = asyncio.run(
        crawl_area_tree(settings, seed_url, limit=limit, dry_run=dry_run)
    )
    console.print(f"[bold]crawl[/bold] {summary.scope}{' (dry-run)' if dry_run else ''}")
    console.print(
        f"  areas={summary.areas} links={summary.route_links} "
        f"routes={summary.route_pages} written={summary.written} "
        f"unchanged={summary.unchanged} errors={summary.errors}"
    )
    for msg in summary.error_messages[:10]:
        console.print(f"  [yellow]![/yellow] {msg}")
    if summary.errors and summary.route_pages == 0:
        raise typer.Exit(code=1)


@app.command()
def validate(config: Path | None = typer.Option(None, "--config")) -> None:
    """Validate the canonical dataset (pending Phase 2/3 integration)."""
    _settings(config)
    console.print("[yellow]Not implemented yet[/yellow]: validate — pending canonical model.")
    raise typer.Exit(code=2)


@app.command()
def reconcile(config: Path | None = typer.Option(None, "--config")) -> None:
    """Reconcile source observations into canonical routes (pending Phase 10)."""
    _settings(config)
    console.print("[yellow]Not implemented yet[/yellow]: reconcile — pending Phase 10.")
    raise typer.Exit(code=2)


def main() -> None:
    app()


if __name__ == "__main__":
    main()
