"""Report assembly: executive summary + per-source summary + technical appendix."""
import datetime as dt

from .finding import sort_findings, finding_template, merge_findings
from .pdf import PDF
from .severity_matrix import matrix, matrix_markdown, source_matrix, source_matrix_markdown

SEVERITY_CAPTION = {
    "Critical": "requires immediate remediation",
    "High": "should be remediated before the next release",
    "Medium": "remediate on the normal change schedule",
    "Low": "remediate as convenient",
    "Info": "informational — no action required",
}

RULESET_VERSION = "v0.3.0"


def summary_counts(findings):
    counts = {}
    for f in findings:
        counts[f.severity_normalized] = counts.get(f.severity_normalized, 0) + 1
    return counts


def to_markdown(findings, engagement="Security assessment", title=None, subtitle="", footer="", accent=None, ruleset_version=RULESET_VERSION):
    """Markdown report: exec summary, per-source summary, severity matrix, technical appendix."""
    merged = merge_findings(findings)
    ordered = sort_findings(merged)
    counts = summary_counts(ordered)
    today = dt.date.today().isoformat()
    doc_title = title or f"{engagement} — report"

    lines = [f"# {doc_title}", ""]
    if subtitle:
        lines.append(f"_{subtitle}_")
        lines.append("")
    if accent:
        lines.append(f"<!-- Accent: {accent} -->")
        lines.append("")

    lines.append(f"_Generated {today} · {len(ordered)} findings · ruleset {ruleset_version}_")
    lines.append("")
    lines.append("## Executive summary")
    lines.append("")
    if not ordered:
        lines.append(f"No issues found by ruleset {ruleset_version}.")
    else:
        lines.append("| Severity | Count | Meaning |")
        lines.append("|---|---|---|")
        for sev in ("Critical", "High", "Medium", "Low", "Info"):
            if sev in counts:
                lines.append(f"| **{sev}** | {counts[sev]} | {SEVERITY_CAPTION[sev]} |")
        lines.append("")
        for f in ordered:
            if f.severity_normalized in ("Critical", "High"):
                lines.append(f"- **{f.title}** ({f.severity_normalized}) at {f.host}{f.path}")

    # Per-source summary if sources exist
    sm = source_matrix(ordered)
    if sm["by_source"]:
        lines.append("")
        lines.append("## Per-source summary")
        lines.append("")
        lines.append(source_matrix_markdown(sm))

    # Severity matrix
    m = matrix(ordered)
    if m["by_tool"]:
        lines.append("")
        lines.append("## Severity matrix")
        lines.append("")
        lines.append(matrix_markdown(m))

    lines.append("")
    lines.append("## Technical appendix")
    lines.append("")
    if not ordered:
        lines.append(f"No issues found by ruleset {ruleset_version}.")
    else:
        for f in ordered:
            lines.append(finding_template(f))
            lines.append("")

    if footer:
        lines.append("---")
        lines.append(f"_{footer}_")
        lines.append("")

    return "\n".join(lines)


def to_pdf(findings, engagement="Security assessment", title=None, subtitle="", footer="", accent=None, ruleset_version=RULESET_VERSION):
    """PDF report with executive summary, per-source summary, severity matrix, technical appendix."""
    merged = merge_findings(findings)
    ordered = sort_findings(merged)
    counts = summary_counts(ordered)
    doc_title = title or engagement

    pdf = PDF(doc_title, subtitle=subtitle, footer=footer, accent=accent)
    page = pdf.add_page()
    page.title(doc_title)
    if subtitle:
        page.subtitle(subtitle)
    page.body(f"Generated {dt.date.today().isoformat()} - {len(ordered)} findings - ruleset {ruleset_version}")

    page.heading("Executive summary")
    if not ordered:
        page.body(f"No issues found by ruleset {ruleset_version}.")
    else:
        for sev in ("Critical", "High", "Medium", "Low", "Info"):
            if sev in counts:
                page.body(f"{sev}: {counts[sev]} - {SEVERITY_CAPTION[sev]}", style="italic")
        page.body(" ")

        # Per-source summary
        sm = source_matrix(ordered)
        if sm["by_source"]:
            page.heading("Per-source summary")
            for src, data in sorted(sm["by_source"].items()):
                t_counts = ", ".join(f"{s}: {c}" for s, c in data["counts"].items())
                page.body(f"{src} ({data['tool']}): {t_counts}")
            page.body(" ")

        page.heading("Technical appendix")
        for f in ordered:
            page.heading(f"[{f.severity_normalized}] {f.title}")
            page.body(f"Where: {f.host}{f.path}")
            det_by = f"Detected by: {f.tool}"
            if f.sources:
                det_by += f" ({', '.join(f.sources)})"
            page.body(det_by)
            if f.detail:
                page.body(f"Detail. {f.detail}")
            if f.remediation:
                page.body(f"Remediation. {f.remediation}")

    return pdf.build()
