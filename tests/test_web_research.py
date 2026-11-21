"""Offline tests for web search parsing and response classification."""
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

    def test_block_page_raises_clear_error(self):
        response = MagicMock()
        response.status = 200
        response.read.return_value = b"<html>captcha verify you are human</html>"
        response.__enter__.return_value = response
        with patch.object(web_research, "urlopen", return_value=response):
            with self.assertRaisesRegex(RuntimeError, "bot-check or blocked"):
                search("test query")

    def test_unknown_page_raises_diagnostic(self):
        response = MagicMock()
        response.status = 200
        response.read.return_value = b"<html><title>Search</title><p>new markup</p></html>"
        response.__enter__.return_value = response
        with patch.object(web_research, "urlopen", return_value=response):
            with self.assertRaisesRegex(RuntimeError, "no recognizable result markup"):
                search("test query")

    def test_known_empty_page_returns_empty(self):
        response = MagicMock()
        response.status = 200
        response.read.return_value = b"<html><p>No results found</p></html>"
        response.__enter__.return_value = response
        with patch.object(web_research, "urlopen", return_value=response):
            self.assertEqual(search("test query"), [])

    def test_rejects_invalid_limit(self):
        with self.assertRaises(ValueError):
            search("test query", limit=0)


if __name__ == "__main__":
    unittest.main()
