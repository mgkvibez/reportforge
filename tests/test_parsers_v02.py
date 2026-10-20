import unittest

from reportforge.zap import parse_alerts
from reportforge.nuclei import parse_results
from reportforge.severity_matrix import matrix, matrix_markdown

ZAP_SAMPLE = """[
 {"site": "https://example.test", "name": "Content Security Policy Missing",
  "risk": "Medium", "confidence": "Medium",
  "description": "No CSP header.", "solution": "Add a CSP.",
  "reference": "https://owasp.org/www-community/controls/csp"},
 {"site": "https://example.test", "name": "Missing Anti-clickjacking Header",
  "risk": "Low", "description": "No XFO.", "solution": "Add XFO."}
]"""

NUCLEI_SAMPLE = """{"template-id": "git-config", "host": "https://example.test", "matched-at": "https://example.test/.git/config", "type": "http", "info": {"name": "Git Config Exposure", "severity": "medium", "description": "Git config file is public.", "reference": ["https://nuclei.template/123"]}}
{"template-id": "open-redirect", "host": "https://example.test", "matched-at": "https://example.test/r?u=", "type": "http", "info": {"name": "Open Redirect", "severity": "high", "description": "Redirects."}}"""


class TestZap(unittest.TestCase):
    def test_parses_alerts(self):
        findings = parse_alerts(ZAP_SAMPLE)
        self.assertEqual(len(findings), 2)
        csp = findings[0]
        self.assertEqual(csp.tool, "OWASP ZAP")
        self.assertEqual(csp.severity_normalized, "Medium")
        self.assertEqual(csp.references, ["https://owasp.org/www-community/controls/csp"])

    def test_missing_fields_degrade(self):
        xfo = parse_alerts(ZAP_SAMPLE)[1]
        self.assertEqual(xfo.confidence, "")
        self.assertEqual(xfo.references, [])

    def test_accepts_file_path(self):
        import tempfile, pathlib
        with tempfile.TemporaryDirectory() as td:
            p = pathlib.Path(td) / "zap.json"
            p.write_text(ZAP_SAMPLE)
            self.assertEqual(len(parse_alerts(str(p))), 2)


class TestNuclei(unittest.TestCase):
    def test_parses_jsonl(self):
        findings = parse_results(NUCLEI_SAMPLE)
        self.assertEqual(len(findings), 2)
        git = findings[0]
        self.assertEqual(git.tool, "nuclei")
        self.assertEqual(git.severity_normalized, "Medium")
        self.assertEqual(git.path, "https://example.test/.git/config")

    def test_severity_mapping(self):
        findings = parse_results(NUCLEI_SAMPLE)
        self.assertEqual(findings[1].severity_normalized, "High")

    def test_blank_lines_skipped(self):
        self.assertEqual(len(parse_results("\n\n" + NUCLEI_SAMPLE + "\n")), 2)


class TestMatrix(unittest.TestCase):
    def test_multi_tool_matrix(self):
        findings = parse_alerts(ZAP_SAMPLE) + parse_results(NUCLEI_SAMPLE)
        m = matrix(findings)
        self.assertEqual(m["by_tool"]["OWASP ZAP"]["Medium"], 1)
        self.assertEqual(m["by_tool"]["nuclei"]["High"], 1)
        self.assertEqual(m["cvss_bands"]["Critical"], "9.0 - 10.0")

    def test_markdown_table(self):
        md = matrix_markdown(matrix(parse_alerts(ZAP_SAMPLE)))
        self.assertIn("| OWASP ZAP |", md)
        self.assertIn("CVSS v3.1 bands", md)


if __name__ == "__main__":
    unittest.main()
