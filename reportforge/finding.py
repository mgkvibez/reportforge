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
        }


def finding_template(finding):
    """Reusable markdown block for one finding."""
    lines = [f"### [{finding.severity_normalized}] {finding.title}", ""]
    lines.append(f"**Where:** `{finding.host}{finding.path}`  ")
    lines.append(f"**Detected by:** {finding.tool}"
                 + (f" (confidence: {finding.confidence})" if finding.confidence else ""))
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
