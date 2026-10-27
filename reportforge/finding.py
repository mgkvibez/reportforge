"""The finding format: one issue, fully described, severity-ordered."""
from dataclasses import dataclass, field

SEVERITY_ORDER = {"Critical": 4, "High": 3, "Medium": 2, "Low": 1,
                  "Informational": 0, "Info": 0}


@dataclass
class Finding:
    title: str
    severity: str
    host: str = ""
    path: str = ""
    detail: str = ""
    remediation: str = ""
    tool: str = "manual"
    confidence: str = ""
    references: list = field(default_factory=list)
    sources: list = field(default_factory=list)

    @property
    def attributions(self):
        return self.sources

    @property
    def sort_key(self):
        return (-SEVERITY_ORDER.get(self.severity_normalized, -1), self.title)

    @property
    def severity_normalized(self):
        s = (self.severity or "").strip().capitalize()
        return "Info" if s in ("Info", "Informational") else s

    def to_dict(self):
        return {
            "title": self.title, "severity": self.severity_normalized,
            "host": self.host, "path": self.path, "detail": self.detail,
            "remediation": self.remediation, "tool": self.tool,
            "confidence": self.confidence, "references": self.references,
            "sources": self.sources,
        }


def dedupe_key(finding):
    """Stable deduplication key: (tool, title, endpoint) normalized."""
    tool_norm = (finding.tool or "").strip().lower()
    title_norm = (finding.title or "").strip().lower()
    host_norm = (finding.host or "").strip().lower()
    path_norm = (finding.path or "").strip().lower()
    endpoint_norm = (host_norm + path_norm).rstrip('/')
    return (tool_norm, title_norm, endpoint_norm)


def merge_findings(findings):
    """Deduplicate findings by stable key, preserving attributions & resolving severity conflicts."""
    if not findings:
        return []

    merged_by_key = {}
    key_order = []

    for f in findings:
        key = dedupe_key(f)
        if key not in merged_by_key:
            merged_by_key[key] = Finding(
                title=f.title,
                severity=f.severity_normalized,
                host=f.host,
                path=f.path,
                detail=f.detail,
                remediation=f.remediation,
                tool=f.tool,
                confidence=f.confidence,
                references=list(f.references),
                sources=list(f.sources) if f.sources else ([f.tool] if f.tool else []),
            )
            key_order.append(key)
        else:
            existing = merged_by_key[key]
            # 1. Resolve severity conflict
            f_sev = f.severity_normalized
            e_sev = existing.severity_normalized
            e_order = SEVERITY_ORDER.get(e_sev, -1)
            f_order = SEVERITY_ORDER.get(f_sev, -1)

            if f_order != e_order:
                max_sev = f_sev if f_order > e_order else e_sev
                min_sev = e_sev if f_order > e_order else f_sev
                existing.severity = max_sev
                note = f"\n\n[Note: Conflicting severities ({min_sev}, {max_sev}) resolved to max severity {max_sev}.]"
                if note not in existing.detail:
                    existing.detail = (existing.detail + note).strip()

            # 2. Combine sources / attributions
            new_sources = f.sources if f.sources else ([f.tool] if f.tool else [])
            for src in new_sources:
                if src and src not in existing.sources:
                    existing.sources.append(src)

            # 3. Combine details / remediations if different
            if f.detail and f.detail not in existing.detail:
                if existing.detail:
                    existing.detail += "\n\n" + f.detail
                else:
                    existing.detail = f.detail

            if f.remediation and f.remediation not in existing.remediation:
                if existing.remediation:
                    existing.remediation += "\n\n" + f.remediation
                else:
                    existing.remediation = f.remediation

            # 4. Merge references
            for ref in f.references:
                if ref and ref not in existing.references:
                    existing.references.append(ref)

            # 5. Confidence (prefer non-empty)
            if not existing.confidence and f.confidence:
                existing.confidence = f.confidence

            # 6. Tool
            if f.tool and f.tool not in existing.tool:
                existing.tool = f"{existing.tool}, {f.tool}"

    return [merged_by_key[k] for k in key_order]


def finding_template(finding):
    """Reusable markdown block for one finding."""
    lines = [f"### [{finding.severity_normalized}] {finding.title}", ""]
    lines.append(f"**Where:** `{finding.host}{finding.path}`  ")
    det_by = f"**Detected by:** {finding.tool}"
    if finding.sources:
        det_by += f" ({', '.join(finding.sources)})"
    if finding.confidence:
        det_by += f" (confidence: {finding.confidence})"
    lines.append(det_by)
    lines.append("")
    if finding.detail:
        lines.append(f"**Detail.** {finding.detail}")
        lines.append("")
    if finding.remediation:
        lines.append(f"**Remediation.** {finding.remediation}")
        lines.append("")
    for ref in finding.references:
        lines.append(f"- Reference: {ref}")
    return "\n".join(lines)


def sort_findings(findings):
    return sorted(findings, key=lambda f: f.sort_key)
