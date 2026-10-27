"""OWASP ZAP export parser (JSON baseline scan export).

ZAP's baseline export is a JSON array of alerts, each with site,
name, riskcode/risk, description, solution and reference fields.
Fields degrade gracefully like the Burp parser.
"""
import json

from .finding import Finding


def parse_alerts(json_source, source_name=None):
    """Parse a ZAP alerts JSON export (path or string) into Findings."""
    if source_name is None and isinstance(json_source, str) and not json_source.lstrip().startswith(("[", "{")):
        source_name = json_source

    if isinstance(json_source, str) and not json_source.lstrip().startswith(("[", "{")):
        with open(json_source, encoding="utf-8") as fh:
            rows = json.load(fh)
    else:
        rows = json.loads(json_source) if isinstance(json_source, str) else json_source

    sources = [source_name] if source_name else []

    findings = []
    for row in rows:
        reference = row.get("reference", "")
        refs = [r for r in reference.splitlines() if r.strip()]
        findings.append(Finding(
            title=(row.get("name") or "Untitled alert").strip(),
            severity=(row.get("risk") or "Informational").strip(),
            host=(row.get("site") or "").strip(),
            path=(row.get("url") or "").strip(),
            detail=(row.get("description") or "").strip(),
            remediation=(row.get("solution") or "").strip(),
            confidence=(row.get("confidence") or "").strip(),
            tool="OWASP ZAP",
            references=refs,
            sources=list(sources),
        ))
    return findings
