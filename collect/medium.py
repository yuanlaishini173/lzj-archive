"""Medium: Liu Zhongjing's public Medium posts, stored in full text.

The feed only carries the latest ~10 posts, so the archive accumulates
whatever has ever appeared there and never drops older posts.
"""
import os
import re
import xml.etree.ElementTree as ET

from common import DATA, fetch, load, save, today

FEED = "https://medium.com/feed/@LiuZhongjing"
STORE = "medium.json"
NS = {"content": "http://purl.org/rss/1.0/modules/content/", "dc": "http://purl.org/dc/elements/1.1/"}
MONTHS = {m: i + 1 for i, m in enumerate("Jan Feb Mar Apr May Jun Jul Aug Sep Oct Nov Dec".split())}


def clean(html):
    html = re.sub(r"<(script|style|iframe)[^>]*>.*?</\1>", "", html, flags=re.S | re.I)
    html = re.sub(r'<img[^>]+src="https://medium\.com/_/stat[^"]*"[^>]*>', "", html)  # tracking pixel
    return re.sub(r"\son\w+=\"[^\"]*\"", "", html)


def main():
    store = load(STORE)
    xml = fetch(FEED)
    os.makedirs(os.path.join(DATA, "medium"), exist_ok=True)
    for item in ET.fromstring(xml).iter("item"):
        link = item.findtext("link").split("?")[0]
        pid = link.rstrip("/").rsplit("-", 1)[-1]
        d = item.findtext("pubDate").split()  # Wed, 25 Nov 2020 12:18:50 GMT
        date = "%s-%02d-%02d" % (d[3], MONTHS[d[2]], int(d[1]))
        body = clean(item.findtext("content:encoded", namespaces=NS) or "")
        with open(os.path.join(DATA, "medium", pid + ".html"), "w", encoding="utf-8") as f:
            f.write(body)
        text = re.sub(r"<[^>]+>", " ", body)
        store[pid] = {
            "id": pid,
            "title": item.findtext("title"),
            "url": link,
            "date": date,
            "tags": [c.text for c in item.findall("category")],
            "chars": len(re.sub(r"\s+", "", text)),
            "first_seen": store.get(pid, {}).get("first_seen", today()),
        }
    save(STORE, store)
    print("medium: %d items" % len(store))


if __name__ == "__main__":
    main()
