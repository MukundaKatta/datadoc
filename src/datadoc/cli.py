"""CLI for DataDoc."""

from __future__ import annotations

import click
import pandas as pd
from rich.console import Console

from datadoc.auditor.cleaner import DataCleaner
from datadoc.auditor.profiler import DataProfiler
from datadoc.auditor.validator import DataValidator
from datadoc.models import QualityReport
from datadoc.report import render_report

console = Console()


@click.group()
def cli() -> None:
    """DataDoc - Data Quality Auditor."""


@cli.command()
@click.argument("path", type=click.Path(exists=True))
@click.option("--validate/--no-validate", default=True, help="Run auto-validation rules.")
@click.option("--clean/--no-clean", "do_clean", default=False, help="Apply auto-cleaning.")
@click.option("--output", "-o", type=click.Path(), default=None, help="Save cleaned CSV.")
def audit(path: str, validate: bool, do_clean: bool, output: str | None) -> None:
    """Audit a CSV file for data quality."""
    df = pd.read_csv(path)
    console.print(f"[bold]Loaded {path}: {len(df)} rows, {len(df.columns)} columns[/bold]")

    profiler = DataProfiler()
    profiles = profiler.profile_dataframe(df)

    report = QualityReport(
        dataset_name=path,
        row_count=len(df),
        column_count=len(df.columns),
        profiles=profiles,
        overall_completeness=sum(p.completeness for p in profiles) / max(len(profiles), 1),
    )

    # Identify issues
    for p in profiles:
        if p.completeness < 0.9:
            report.issues.append(f"'{p.name}' has low completeness ({p.completeness:.1%})")
        if p.uniqueness == 1.0 and p.total_count > 1:
            report.issues.append(f"'{p.name}' is fully unique (possible ID column)")

    if validate:
        validator = DataValidator()
        validator.auto_rules(df)
        report.validation_results = validator.validate(df)

    quality_scores = [p.completeness for p in profiles]
    if validate:
        pass_rate = sum(1 for r in report.validation_results.values() if r["passed"]) / max(len(report.validation_results), 1)
        quality_scores.append(pass_rate)
    report.overall_quality_score = sum(quality_scores) / max(len(quality_scores), 1)

    if do_clean:
        cleaner = DataCleaner()
        df = cleaner.clean(df)
        report.cleaning_actions = cleaner.actions
        if output:
            df.to_csv(output, index=False)
            console.print(f"[green]Cleaned data saved to {output}[/green]")

    render_report(report, console)


@cli.command()
@click.argument("path", type=click.Path(exists=True))
def profile(path: str) -> None:
    """Profile a CSV file."""
    df = pd.read_csv(path)
    profiler = DataProfiler()
    profiles = profiler.profile_dataframe(df)
    for p in profiles:
        console.print(f"\n[bold]{p.name}[/bold] ({p.inferred_type.value})")
        console.print(f"  Completeness: {p.completeness:.1%}  Uniqueness: {p.uniqueness:.1%}")
        if p.mean is not None:
            console.print(f"  Mean: {p.mean}  Median: {p.median}  Std: {p.std}")
        if p.most_common:
            top = ", ".join(f"{k}({v})" for k, v in p.most_common[:3])
            console.print(f"  Top values: {top}")


if __name__ == "__main__":
    cli()
