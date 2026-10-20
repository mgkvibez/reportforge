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
        self.assertIn("No findings", md)


if __name__ == "__main__":
    unittest.main()
