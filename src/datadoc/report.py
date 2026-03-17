"""Report generation for DataDoc."""

from __future__ import annotations

from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from datadoc.models import QualityReport


def render_report(report: QualityReport, console: Console | None = None) -> str:
    """Render a quality report to console and return as string."""
    console = console or Console()
    lines: list[str] = []

    # Header
    header = f"Data Quality Report: {report.dataset_name}"
    lines.append(header)
    lines.append(f"Rows: {report.row_count}  Columns: {report.column_count}")
    lines.append(f"Overall Completeness: {report.overall_completeness:.1%}")
    lines.append(f"Quality Score: {report.overall_quality_score:.1%}")
    lines.append("")

    console.print(Panel(f"[bold]{header}[/bold]\n"
                        f"Rows: {report.row_count}  Columns: {report.column_count}\n"
                        f"Completeness: {report.overall_completeness:.1%}  "
                        f"Quality: {report.overall_quality_score:.1%}"))

    # Profiles table
    if report.profiles:
        table = Table(title="Column Profiles")
        table.add_column("Column")
        table.add_column("Type")
        table.add_column("Complete", justify="right")
        table.add_column("Unique", justify="right")
        table.add_column("Nulls", justify="right")
        for p in report.profiles:
            table.add_row(
                p.name, p.inferred_type.value,
                f"{p.completeness:.1%}", f"{p.uniqueness:.1%}",
                str(p.null_count),
            )
            lines.append(f"  {p.name}: {p.inferred_type.value} complete={p.completeness:.1%} unique={p.uniqueness:.1%}")
        console.print(table)

    # Validation
    if report.validation_results:
        lines.append("\nValidation Results:")
        vtable = Table(title="Validation Results")
        vtable.add_column("Rule")
        vtable.add_column("Status")
        vtable.add_column("Failures", justify="right")
        for desc, result in report.validation_results.items():
            status = "[green]PASS[/green]" if result["passed"] else "[red]FAIL[/red]"
            vtable.add_row(desc, status, str(result["failing_count"]))
            lines.append(f"  {'PASS' if result['passed'] else 'FAIL'}: {desc} ({result['failing_count']} failures)")
        console.print(vtable)

    # Issues
    if report.issues:
        lines.append("\nIssues:")
        for issue in report.issues:
            lines.append(f"  - {issue}")
            console.print(f"  [yellow]![/yellow] {issue}")

    if report.cleaning_actions:
        lines.append("\nCleaning Actions:")
        for action in report.cleaning_actions:
            lines.append(f"  - {action}")
            console.print(f"  [cyan]>[/cyan] {action}")

    return "\n".join(lines)
