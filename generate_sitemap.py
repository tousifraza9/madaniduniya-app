
import urllib.request
from urllib.parse import urljoin, urlparse, urldefrag
from html.parser import HTMLParser
from collections import deque
from xml.etree.ElementTree import Element, SubElement, ElementTree

DOMAIN = "https://app.madaniduniya.com/"
MAX_PAGES = 5000

class Parser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.links = []
        self.noindex = False

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)

        if tag == "a" and attrs.get("href"):
            self.links.append(attrs["href"])

        if tag == "meta" and attrs.get("name", "").lower() == "robots":
            if "noindex" in attrs.get("content", "").lower():
                self.noindex = True

def clean_url(url):
    url, _ = urldefrag(url)
    p = urlparse(url)

    if p.scheme not in ("http", "https"):
        return None

    if p.netloc.lower() != urlparse(DOMAIN).netloc.lower():
        return None

    if p.query or p.path.lower().endswith(
        (".jpg", ".png", ".gif", ".css", ".js", ".pdf",
         ".svg", ".webp", ".xml", ".ico")
    ):
        return None

    return DOMAIN.rstrip("/") + (p.path or "/")

queue = deque([DOMAIN])
visited = set()
pages = []

while queue and len(visited) < MAX_PAGES:
    url = queue.popleft()

    if url in visited:
        continue

    visited.add(url)

    try:
        req = urllib.request.Request(
            url, headers={"User-Agent": "MadaniDuniyaBot/1.0"}
        )

        with urllib.request.urlopen(req, timeout=20) as r:
            if "text/html" not in r.headers.get("Content-Type", ""):
                continue

            final_url = clean_url(r.geturl())
            if not final_url:
                continue

            html = r.read().decode("utf-8", errors="replace")

        parser = Parser()
        parser.feed(html)

        if parser.noindex:
            continue

        pages.append(final_url)

        for link in parser.links:
            new_url = clean_url(urljoin(final_url, link))
            if new_url and new_url not in visited:
                queue.append(new_url)

    except Exception as e:
        print("Skipped:", url, e)

root = Element(
    "urlset",
    xmlns="http://www.sitemaps.org/schemas/sitemap/0.9"
)

for page in sorted(set(pages)):
    SubElement(SubElement(root, "url"), "loc").text = page

ElementTree(root).write(
    "sitemap.xml",
    encoding="UTF-8",
    xml_declaration=True
)

print("Total URLs:", len(set(pages)))
