import unittest

from reportforge.burp import parse_issues
from reportforge.finding import Finding, sort_findings
from reportforge.render import to_markdown, to_pdf

SAMPLE = """<?xml version="1.0"?>
<issues burpVersion="2026.1" exportTime="2026-10-20">
  <issue>
    <name>Cross-site scripting (reflected)</name>
    <severity>High</severity>
    <confidence>Certain</confidence>
    <host ip="10.0.0.1">https://example.test</host>
    <path>/search?q=</path>
    <issueDetail>The q parameter reflects user input.</issueDetail>
    <remediationBackground>Encode output.</remediationBackground>
  </issue>
  <issue>
    <name>TLS certificate expiring</name>
    <severity>Low</severity>
    <confidence>Firm</confidence>
    <host ip="10.0.0.1">https://example.test</host>
    <path>/</path>
    <issueDetail>Cert expires in 14 days.</issueDetail>
  </issue>
  <issue>
    <name>Missing header</name>
    <severity>informational</severity>
    <host ip="10.0.0.1">https://example.test</host>
    <path>/</path>
  </issue>
</issues>"""


class TestBurpParser(unittest.TestCase):
    def test_parses_all_issues(self):
        findings = parse_issues(SAMPLE)
        self.assertEqual(len(findings), 3)

    def test_fields_mapped(self):
        xss = parse_issues(SAMPLE)[0]
        self.assertEqual(xss.title, "Cross-site scripting (reflected)")
        self.assertEqual(xss.severity_normalized, "High")
        self.assertEqual(xss.host, "https://example.test")
        self.assertEqual(xss.tool, "Burp Suite")

    def test_severity_normalization(self):
        info = parse_issues(SAMPLE)[2]
        self.assertEqual(info.severity_normalized, "Info")

    def test_missing_fields_degrade(self):
        finding = parse_issues(SAMPLE)[2]
        self.assertEqual(finding.remediation, "")


class TestOrdering(unittest.TestCase):
    def test_severity_sorted_desc(self):
        findings = parse_issues(SAMPLE)
        ordered = [f.severity_normalized for f in sort_findings(findings)]
        self.assertEqual(ordered, ["High", "Low", "Info"])


class TestRender(unittest.TestCase):
    def test_markdown_structure(self):
        md = to_markdown(parse_issues(SAMPLE), engagement="ACME test")
        self.assertIn("Executive summary", md)
        self.assertIn("Technical appendix", md)
        self.assertIn("| **High** | 1 |", md)

    def test_pdf_is_valid_and_has_pages(self):
        data = to_pdf(parse_issues(SAMPLE), engagement="ACME test")
        self.assertTrue(data.startswith(b"%PDF-1.4"))
        self.assertTrue(data.rstrip().endswith(b"%%EOF"))
        self.assertIn(b"/Count 1", data)

    def test_empty_findings_renders_clean(self):
        md = to_markdown([], engagement="ACME test")
        self.assertIn("No issues found by ruleset", md)


if __name__ == "__main__":
    unittest.main()


class TestMergeV03(unittest.TestCase):
    """v0.3: multi-file dedupe, attribution, severity conflicts, branding."""

    def _f(self, title="SQL injection", sev="High", host="api.example.com",
           path="/v1/users", tool="burp", sources=None):
        from reportforge.finding import Finding
        return Finding(title=title, severity=sev, host=host, path=path,
                       detail="detail text", remediation="fix it",
                       tool=tool, sources=sources or [])

    def test_duplicate_appears_once_with_two_sources(self):
        from reportforge.finding import merge_findings
        merged = merge_findings([
            self._f(sources=["scan-a.xml"]),
            self._f(sources=["scan-b.xml"]),
        ])
        self.assertEqual(len(merged), 1)
        self.assertEqual(sorted(merged[0].sources),
                         ["scan-a.xml", "scan-b.xml"])

    def test_different_tools_not_merged(self):
        from reportforge.finding import merge_findings
        merged = merge_findings([
            self._f(tool="burp"),
            self._f(tool="zap", sev="Medium"),
        ])
        self.assertEqual(len(merged), 2)

    def test_severity_conflict_resolves_to_max_with_note(self):
        from reportforge.finding import merge_findings
        merged = merge_findings([
            self._f(sev="Low", sources=["a.xml"]),
            self._f(sev="High", sources=["b.xml"]),
        ])
        self.assertEqual(len(merged), 1)
        self.assertEqual(merged[0].severity_normalized, "High")
        self.assertIn("resolved to max severity High", merged[0].detail)

    def test_normalized_endpoints_dedupe(self):
        from reportforge.finding import merge_findings
        merged = merge_findings([
            self._f(path="/v1/users"),
            self._f(path="/v1/users/"),
        ])
        self.assertEqual(len(merged), 1)

    def test_empty_input_returns_empty(self):
        from reportforge.finding import merge_findings
        self.assertEqual(merge_findings([]), [])


class TestBrandingV03(unittest.TestCase):
    def _findings(self):
        from reportforge.finding import Finding
        return [Finding(title="SQL injection", severity="High",
                        host="api.example.com", path="/v1/users",
                        detail="d", remediation="r", tool="burp")]

    def test_markdown_branding(self):
        from reportforge.render import to_markdown
        md = to_markdown(self._findings(), title="ACME Q4 Audit",
                         subtitle="internal", footer="ACME Ltd confidential",
                         accent="#0055ff")
        self.assertIn("ACME Q4 Audit", md)
        self.assertIn("_internal_", md)
        self.assertIn("ACME Ltd confidential", md)
        self.assertIn("<!-- Accent: #0055ff -->", md)

    def test_markdown_defaults_without_branding(self):
        from reportforge.render import to_markdown
        md = to_markdown(self._findings(), engagement="Eng")
        self.assertIn("# Eng", md)
        self.assertNotIn("Accent:", md)

    def test_pdf_branding(self):
        from reportforge.render import to_pdf
        pdf = to_pdf(self._findings(), title="ACME Q4 Audit",
                     subtitle="internal", footer="ACME Ltd confidential")
        self.assertTrue(pdf.startswith(b"%PDF"))
        # the writer emits uncompressed (text) Tj ops, so branded
        # strings are present verbatim in the raw PDF bytes
        self.assertIn(b"ACME Q4 Audit", pdf)
        self.assertIn(b"ACME Ltd confidential", pdf)
        self.assertIn(b"internal", pdf)

    def test_multi_file_merge_via_cli_path(self):
        from reportforge.burp import parse_issues
        from reportforge.finding import merge_findings
        a = parse_issues("sample-issues.xml", source_name="scan-a.xml")
        merged = merge_findings(a + a)
        self.assertEqual(len(merged), len(a))
        for f in merged:
            self.assertEqual(sorted(f.sources), ["scan-a.xml"])
