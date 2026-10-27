"""nuclei output parser (JSONL).

nuclei -j emits one JSON object per line: template-id, info (name,
severity, description, reference), matched-at, host, and more.
"""
import json

from .finding import Finding

SEVERITY_MAP = {"critical": "Critical", "high": "High", "medium": "Medium",
                "low": "Low", "info": "Info", "informational": "Info"}


def parse_results(jsonl_source, source_name=None):
    """Parse nuclei JSONL output (path or string) into Findings."""
    if source_name is None and isinstance(jsonl_source, str) and "\n" not in jsonl_source and not jsonl_source.startswith("{"):
        source_name = jsonl_source

    if isinstance(json_source := jsonl_source, str) and "\n" not in json_source and not json_source.startswith("{"):
        lines = open(json_source, encoding="utf-8").read().splitlines()
    else:
        lines = jsonl_source.splitlines() if isinstance(jsonl_source, str) else list(jsonl_source)

    sources = [source_name] if source_name else []

    findings = []
    for line in lines:
        line = line.strip()
        if not line:
            continue
        row = json.loads(line)
        info = row.get("info", {})
        raw_sev = (info.get("severity") or "info").lower()
        refs = info.get("reference") or []
        if isinstance(refs, str):
            refs = [refs]
        findings.append(Finding(
            title=(info.get("name") or row.get("template-id") or "Untitled match").strip(),
            severity=SEVERITY_MAP.get(raw_sev, "Info"),
            host=(row.get("host") or "").strip(),
            path=(row.get("matched-at") or "").strip(),
            detail=(info.get("description") or "").strip(),
            remediation=(info.get("remediation") or "").strip(),
            confidence=(row.get("type") or "").strip(),
            tool="nuclei",
            references=list(refs),
            sources=list(sources),
        ))
    return findings
