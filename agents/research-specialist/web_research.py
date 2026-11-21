"""Small dependency-free DuckDuckGo HTML search adapter for evidence snippets."""
from __future__ import annotations
from html.parser import HTMLParser
from urllib.parse import urlencode, urlparse, parse_qs
from urllib.request import Request, urlopen
from urllib.error import URLError, HTTPError
import re

SEARCH_URL="https://html.duckduckgo.com/html/"

def clean(text: str) -> str:
    return " ".join(re.sub(r"<[^>]+>", " ", text).split())

class DDGParser(HTMLParser):
    """Parse result titles, destination links, and snippets from DDG HTML."""
    def __init__(self):
        super().__init__()
        self.results=[]
        self._current=None
        self._capture=None
        self._buffer=[]
        self._result_depth=0
    def handle_starttag(self, tag, attrs):
        a=dict(attrs)
        classes=set(a.get("class","").split())
        if tag=="div" and "result" in classes:
            self._current={"title":"","url":"","snippet":""}
            self._result_depth=1
        elif self._current is not None:
            if tag=="a" and "result__a" in classes:
                self._capture="title";self._buffer=[]
                self._current["url"]=a.get("href","")
            elif tag in ("a","div") and ("result__snippet" in classes or "result__extras__url" in classes):
                self._capture="snippet";self._buffer=[]
        if self._capture and tag in ("br","p"):
            self._buffer.append(" ")
    def handle_data(self,data):
        if self._capture:self._buffer.append(data)
    def handle_endtag(self,tag):
        if self._capture and tag in ("a","div"):
            field=self._capture
            self._current[field]=clean("".join(self._buffer))
            self._capture=None;self._buffer=[]
        if tag=="div" and self._current is not None and self._result_depth:
            # DDG results are nested divs; finalize only on result container end.
            pass
    def close(self):
        super().close()
        # Result blocks are easiest to recover from title anchors/snippet anchors.
        # Some DDG markup has nesting variations, so keep anchors collected as pairs.
    def get_results(self):
        return [r for r in self.results if r.get("title") and r.get("url")]

class ResultsParser(HTMLParser):
    def __init__(self):
        super().__init__(); self.items=[]; self._title=None; self._snippet=None; self._text=[]; self._mode=None
    def handle_starttag(self,tag,attrs):
        c=set(dict(attrs).get("class","").split())
        if tag=="a" and "result__a" in c:
            self._title="";self._url=dict(attrs).get("href","");self._mode="title"
        elif tag in ("a","div") and "result__snippet" in c:
            self._snippet="";self._mode="snippet"
    def handle_data(self,data):
        if self._mode=="title" and self._title is not None:self._title+=data
        elif self._mode=="snippet" and self._snippet is not None:self._snippet+=data
    def handle_endtag(self,tag):
        if tag=="a" and self._mode=="title":
            if self._title and self._url:self.items.append({"title":clean(self._title),"url":self._url,"snippet":""})
            self._mode=None
        elif tag in ("a","div") and self._mode=="snippet":
            if self._snippet and self.items:self.items[-1]["snippet"]=clean(self._snippet)
            self._mode=None

def search(query: str, *, limit: int=5, timeout: int=15) -> list[dict]:
    if not query.strip():return []
    url=SEARCH_URL+"?"+urlencode({"q":query})
    req=Request(url,headers={"User-Agent":"Mozilla/5.0 (compatible; AI-EMPIRE research bot/0.1)"})
    try:
        with urlopen(req,timeout=timeout) as response:
            page=response.read(750_000).decode("utf-8",errors="replace")
    except (URLError,HTTPError,TimeoutError) as exc:
        raise RuntimeError(f"Search request failed: {exc}") from None
    parser=ResultsParser();parser.feed(page)
    valid=[]
    for row in parser.items:
        link=row["url"]
        if link.startswith("//"):link="https:"+link
        parsed=urlparse(link)
        # DDG may use redirect URLs; safely extract destination if present.
        if "duckduckgo.com" in parsed.netloc and parsed.path.startswith("/l/"):
            target=parse_qs(parsed.query).get("uddg",[])
            if target:link=target[0]
        parsed=urlparse(link)
        if parsed.scheme not in ("http","https") or not parsed.netloc:continue
        if any(link==x["url"] for x in valid):continue
        row["url"]=link
        valid.append(row)
        if len(valid)>=limit:break
    return valid
