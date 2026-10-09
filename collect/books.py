"""Books: bibliography (authored works + translations) parsed from zh.wikipedia.

Metadata only — the books themselves are copyrighted. Each entry links to a
Google Books search for where to buy/preview it.
"""
import re
import urllib.parse

from common import fetch, load, save, today

WIKI = ("https://zh.wikipedia.org/w/index.php?title=%E5%8A%89%E4%BB%B2%E6%95%AC"
        "&action=raw")
STORE = "books.json"


def unwiki(s):
    s = re.sub(r"<ref[^>]*/>|<ref[^>]*>.*?</ref>", "", s, flags=re.S)
    s = re.sub(r"\{\{le\|([^|}]+)\|[^}]*\}\}", r"\1", s)
    s = re.sub(r"\{\{[^}]*\}\}", "", s)
    s = re.sub(r"\[\[(?:[^|\]]*\|)?([^\]]+)\]\]", r"\1", s)
    return s.strip()


def section(raw, name):
    m = re.search(r"===\s*%s\s*===\n(.*?)(?=\n==)" % name, raw, re.S)
    return [l[1:].strip() for l in m.group(1).splitlines() if l.startswith("*")] if m else []


def main():
    raw = fetch(WIKI)
    store = load(STORE)
    for kind, name in (("book", "著作"), ("translation", "译著")):
        for line in section(raw, name):
            line = unwiki(line)
            t = re.match(r"《(.+?)》(.*)", line)
            if not t:
                continue
            title, rest = t.group(1), t.group(2).strip("，, ")
            years = re.findall(r"(\d{4})年", rest)
            key = re.sub(r"\W", "", title)[:40]
            store[key] = {
                "id": key,
                "title": title,
                "kind": kind,
                "detail": rest,
                "date": min(years) if years else "",
                "url": "https://www.google.com/search?tbm=bks&q=" + urllib.parse.quote(title + " 劉仲敬"),
                "first_seen": store.get(key, {}).get("first_seen", today()),
            }
    save(STORE, store)
    print("books: %d items" % len(store))


if __name__ == "__main__":
    main()
