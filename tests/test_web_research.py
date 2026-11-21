"""Offline tests for web search parsing, provider fallback, and diagnostics."""
import sys
import unittest
from pathlib import Path
from unittest.mock import patch, MagicMock

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "agents" / "research-specialist"))
import web_research
from web_research import ResultsParser, clean, classify_response, search


class ParserTests(unittest.TestCase):
    def test_two_results(self):
        markup = (
            '<a class="result__a" href="https://example.org/a">Alpha <b>Title</b></a>'
            '<div class="result__snippet">Alpha snippet</div>'
            '<a class="result__a" href="https://example.org/b">Beta Title</a>'
            '<div class="result__snippet">Beta snippet text</div>'
        )
        parser = ResultsParser()
        parser.feed(markup)
        self.assertEqual(len(parser.items), 2)
        self.assertEqual(parser.items[0]["title"], "Alpha Title")
        self.assertEqual(parser.items[0]["snippet"], "Alpha snippet")
        self.assertEqual(parser.items[1]["url"], "https://example.org/b")
        self.assertEqual(parser.items[1]["snippet"], "Beta snippet text")

    def test_whitespace(self):
        self.assertEqual(clean(" x  y\n z "), "x y z")
        self.assertEqual(clean(" x\ty\nz "), "x y z")
        self.assertEqual(clean(" x\u00a0 y "), "x y")
        self.assertEqual(clean("  x\u00a0\t y\n z  "), "x y z")

    def test_classifies_block_page(self):
        self.assertEqual(classify_response("<html>captcha verify you are human</html>", 0), "blocked")

    def test_classifies_known_empty_page(self):
        self.assertEqual(classify_response("<p>No results found</p>", 0), "empty")

    def test_unknown_markup_is_not_empty(self):
        self.assertEqual(classify_response("<html><title>Search</title><p>layout changed</p>", 0), "unrecognized")

    def test_results_override_empty_marker(self):
        self.assertEqual(classify_response("No results found <a>", 1), "results")

    def _mock_response(self, body):
        response = MagicMock()
        response.status = 200
        response.read.return_value = body
        response.__enter__.return_value = response
        return response

    def test_block_page_raises_clear_error(self):
        with patch.object(web_research, "urlopen", return_value=self._mock_response(
            b"<html>captcha verify you are human</html>"
        )):
            with self.assertRaisesRegex(RuntimeError, "bot-check or blocked"):
                web_research._search_duckduckgo("test query", limit=5, timeout=15)

    def test_unknown_page_raises_diagnostic(self):
        with patch.object(web_research, "urlopen", return_value=self._mock_response(
            b"<html><title>Search</title><p>new markup</p></html>"
        )):
            with self.assertRaisesRegex(RuntimeError, "no recognizable result markup"):
                web_research._search_duckduckgo("test query", limit=5, timeout=15)

    def test_known_empty_page_returns_empty(self):
        with patch.object(web_research, "urlopen", return_value=self._mock_response(
            b"<html><p>No results found</p></html>"
        )):
            self.assertEqual(
                web_research._search_duckduckgo("test query", limit=5, timeout=15), []
            )

    def test_fallback_runs_when_duckduckgo_is_blocked(self):
        expected = [{"title": "Result", "url": "https://example.org", "snippet": "Evidence"}]
        with patch.object(web_research, "_search_duckduckgo", side_effect=RuntimeError("blocked")) as primary, \
             patch.object(web_research, "_search_agentsearch", return_value=expected) as fallback:
            self.assertEqual(search("test query"), expected)
            primary.assert_called_once()
            fallback.assert_called_once()

    def test_duckduckgo_results_skip_fallback(self):
        expected = [{"title": "Primary", "url": "https://example.org", "snippet": "Text"}]
        with patch.object(web_research, "_search_duckduckgo", return_value=expected), \
             patch.object(web_research, "_search_agentsearch") as fallback:
            self.assertEqual(search("test query"), expected)
            fallback.assert_not_called()

    def test_both_provider_failures_are_reported(self):
        with patch.object(web_research, "_search_duckduckgo", side_effect=RuntimeError("blocked")), \
             patch.object(web_research, "_search_agentsearch", side_effect=RuntimeError("HTTP 503")):
            with self.assertRaisesRegex(RuntimeError, "Primary provider failed.*fallback failed"):
                search("test query")

    def test_agentsearch_normalizes_results(self):
        body = (
            '{"result_count":1,"results":[{"title":"Example","url":"https://example.org",'
            '"content":"Useful snippet"}]}'
        )
        with patch.object(web_research, "urlopen", return_value=self._mock_response(body.encode())):
            rows = web_research._search_agentsearch("test query", limit=5, timeout=15)
        self.assertEqual(rows, [{
            "title": "Example", "url": "https://example.org", "snippet": "Useful snippet"
        }])

    def test_rejects_invalid_limit(self):
        with self.assertRaises(ValueError):
            search("test query", limit=0)


if __name__ == "__main__":
    unittest.main()
