"""Burp Suite issues XML -> Finding records.

Supports Burp's 'Save issues' XML export: an <issues> root with one
<issue> per finding. Unknown fields are ignored; missing fields
degrade to empty strings rather than crashing the report.
"""
import xml.etree.ElementTree as ET

from .finding import Finding


def _text(node, tag):
    child = node.find(tag)
    return (child.text or "").strip() if child is not None and child.text else ""


def parse_issues(xml_source, source_name=None):
    """Parse a Burp XML export (path or string) into Findings."""
    if source_name is None and isinstance(xml_source, str) and "<" not in xml_source:
        source_name = xml_source

    if isinstance(xml_source, str) and "<" not in xml_source:
        tree = ET.parse(xml_source)
    else:
        tree = ET.ElementTree(ET.fromstring(xml_source))
    root = tree.getroot()

    sources = [source_name] if source_name else []

    findings = []
    for node in root.findall(".//issue"):
        host_node = node.find("host")
        host = host_node.text.strip() if host_node is not None and host_node.text else ""
        findings.append(Finding(
            title=_text(node, "name") or "Untitled issue",
            severity=_text(node, "severity") or "Informational",
            host=host,
            path=_text(node, "path"),
            detail=_text(node, "issueDetail"),
            remediation=_text(node, "remediationBackground"),
            confidence=_text(node, "confidence"),
            tool="Burp Suite",
            sources=list(sources),
        ))
    return findings
