"""Severity matrix with CVSS mapping and per-source breakdown.

Maps scanner severities into a CVSS-anchored band so mixed-tool
reports can be compared on one scale. CVSS v3.1 qualitative bands.
"""
CVSS_BANDS = {
    "Critical": "9.0 - 10.0",
    "High": "7.0 - 8.9",
    "Medium": "4.0 - 6.9",
    "Low": "0.1 - 3.9",
    "Info": "n/a (informational)",
}


def matrix(findings):
    """Tool x severity matrix: {tool: {severity: count}} + CVSS bands."""
    by_tool = {}
    for f in findings:
        tool = f.tool
        by_tool.setdefault(tool, {})
        sev = f.severity_normalized
        by_tool[tool][sev] = by_tool[tool].get(sev, 0) + 1
    return {"by_tool": by_tool, "cvss_bands": CVSS_BANDS}


def matrix_markdown(m):
    """Markdown table for the severity matrix."""
    sevs = ["Critical", "High", "Medium", "Low", "Info"]
    lines = ["| Tool | " + " | ".join(sevs) + " |",
             "|" + "---|" * (len(sevs) + 1)]
    for tool, counts in sorted(m["by_tool"].items()):
        cells = [str(counts.get(s, 0)) for s in sevs]
        lines.append(f"| {tool} | " + " | ".join(cells) + " |")
    lines.append("")
    lines.append("CVSS v3.1 bands: " + "; ".join(
        f"{k}: {v}" for k, v in m["cvss_bands"].items() if k != "Info"))
    return "\n".join(lines)


def source_matrix(findings):
    """Source x severity matrix: {source: {tool, counts}}."""
    by_source = {}
    for f in findings:
        srcs = f.sources or [f.tool]
        for src in srcs:
            if src not in by_source:
                by_source[src] = {"tool": f.tool, "counts": {}}
            sev = f.severity_normalized
            by_source[src]["counts"][sev] = by_source[src]["counts"].get(sev, 0) + 1
    return {"by_source": by_source}


def source_matrix_markdown(sm):
    """Markdown table for per-source summary."""
    sevs = ["Critical", "High", "Medium", "Low", "Info"]
    lines = ["| Source | Tool | " + " | ".join(sevs) + " | Total |",
             "|" + "---|" * (len(sevs) + 3)]
    for src, data in sorted(sm["by_source"].items()):
        tool = data["tool"]
        counts = data["counts"]
        cells = [str(counts.get(s, 0)) for s in sevs]
        total = sum(counts.get(s, 0) for s in sevs)
        lines.append(f"| {src} | {tool} | " + " | ".join(cells) + f" | {total} |")
    return "\n".join(lines)
