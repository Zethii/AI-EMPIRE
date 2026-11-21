"""Offline parser unit tests for web search snippets."""
import sys,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"agents"/"research-specialist"))
from web_research import ResultsParser,clean
class ParserTests(unittest.TestCase):
 def test_two_results(self):
  markup='<a class="result__a" href="https://example.org/a">Alpha <b>Title</b></a><div class="result__snippet">Alpha snippet</div><a class="result__a" href="https://example.org/b">Beta Title</a><div class="result__snippet">Beta snippet text</div>'
  p=ResultsParser();p.feed(markup)
  self.assertEqual(len(p.items),2)
  self.assertEqual(p.items[0]["title"],"Alpha Title")
  self.assertEqual(p.items[0]["snippet"],"Alpha snippet")
  self.assertEqual(p.items[1]["url"],"https://example.org/b")
  self.assertEqual(p.items[1]["snippet"],"Beta snippet text")
 def test_whitespace(self):
  self.assertEqual(clean(" x  y\n z "), "x y z")
  self.assertEqual(clean(" x\ty\nz "), "x y z")
  self.assertEqual(clean(" x\u00a0 y "), "x y")
  self.assertEqual(clean("  x\u00a0\t y\n z  "), "x y z")
if __name__=="__main__":unittest.main()
