"""Report assembly: executive summary + technical appendix."""
import datetime as dt

from .finding import sort_findings, finding_template
from .pdf import PDF

SEVERITY_CAPTION = {
    "Critical": "requires immediate remediation",
    "High": "should be remediated before the next release",
    "Medium": "remediate on the normal change schedule",
    "Low": "remediate as convenient",
    "Info": "informational — no action required",
}


def summary_counts(findings):
    counts = {}
    for f in findings:
        counts[f.severity_normalized] = counts.get(f.severity_normalized, 0) + 1
    return counts


def to_markdown(findings, engagement="Security assessment"):
    """Markdown report: exec summary then per-finding detail."""
    ordered = sort_findings(findings)
    counts = summary_counts(ordered)
    today = dt.date.today().isoformat()

    lines = [f"# {engagement} — report", ""]
    lines.append(f"_Generated {today} · {len(ordered)} findings_")
    lines.append("")
    lines.append("## Executive summary")
    lines.append("")
    if not ordered:
        lines.append("No findings. Clean run.")
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
    lines.append("")
    lines.append("## Technical appendix")
    lines.append("")
    for f in ordered:
        lines.append(finding_template(f))
        lines.append("")
    return "\n".join(lines)


def to_pdf(findings, engagement="Security assessment"):
    """PDF report with the same structure."""
    ordered = sort_findings(findings)
    counts = summary_counts(ordered)

    pdf = PDF(engagement)
    page = pdf.add_page()
    page.title(engagement)
    page.body(f"Generated {dt.date.today().isoformat()} - {len(ordered)} findings")

    page.heading("Executive summary")
    if not ordered:
        page.body("No findings. Clean run.")
    else:
        for sev in ("Critical", "High", "Medium", "Low", "Info"):
            if sev in counts:
                page.body(f"{sev}: {counts[sev]} - {SEVERITY_CAPTION[sev]}", style="italic")
        page.body(" ")
        page.heading("Technical appendix")
        for f in ordered:
            page.heading(f"[{f.severity_normalized}] {f.title}")
            page.body(f"Where: {f.host}{f.path}")
            page.body(f"Detected by: {f.tool}")
            if f.detail:
                page.body(f"Detail. {f.detail}")
            if f.remediation:
                page.body(f"Remediation. {f.remediation}")
    return pdf.build()
