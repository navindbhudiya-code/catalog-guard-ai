"""Build AuditReport from GraphState and render it as markdown."""

from __future__ import annotations

from catalogguard.models import AuditReport, GraphState


def build_report(state: GraphState, products_scanned: int) -> AuditReport:
    """Consolidate the audit state into a report."""
    return AuditReport(
        store_url=state.config.store_url,
        products_scanned=products_scanned,
        checks_run=list(state.config.checks),
        issues=list(state.issues),
        proposals=list(state.proposals),
        token_cost=dict(state.token_ledger),
    )


def _counts_table(title: str, counts: dict[str, int]) -> list[str]:
    lines = [f"### {title}", "", "| Key | Count |", "| --- | --- |"]
    lines += [f"| {key} | {value} |" for key, value in sorted(counts.items())]
    return [*lines, ""]


def render_markdown(report: AuditReport) -> str:
    """Render a human-readable markdown scorecard for the audit."""
    lines = [
        "# CatalogGuard Audit Report",
        "",
        f"- Store: {report.store_url}",
        f"- Products scanned: {report.products_scanned}",
        f"- Checks run: {', '.join(report.checks_run) or 'none'}",
        f"- Total issues: {report.issue_count}",
        "",
    ]

    if not report.issues:
        lines.append("No issues found. ✅")
        return "\n".join(lines) + "\n"

    lines += _counts_table("Issues by dimension", report.counts_by_dimension())
    lines += _counts_table("Issues by severity", report.counts_by_severity())

    lines += [
        "### Issues",
        "",
        "| SKU | Dimension | Severity | Code | Message |",
        "| --- | --- | --- | --- | --- |",
    ]
    for issue in report.issues:
        lines.append(
            f"| {issue.sku} | {issue.dimension.value} | {issue.severity.value} "
            f"| {issue.code} | {issue.message} |"
        )
    lines.append("")
    return "\n".join(lines) + "\n"
