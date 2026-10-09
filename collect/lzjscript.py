"""刘仲敬文稿站 (lzjscript.com): fan-made transcript site, now offline.

Posts were members-only, so this is an index only: title, date and a Wayback
Machine link per post, discovered through the Wayback CDX API. Each run picks
up any newly archived posts.
"""
import json
import re
import html
from concurrent.futures import ThreadPoolExecutor

from common import fetch, load, save, today

STORE = "lzjscript.json"
CDX = ("https://web.archive.org/cdx/search/cdx?url=lzjscript.com&matchType=domain"
       "&filter=original:.*/archives/[0-9]%2B/%3F"
       "&fl=original,timestamp,statuscode&output=json&limit=100000")


def clean_title(t):
    return re.sub(r"\s*[-|–—]\s*(刘仲敬文稿站)?\s*$", "", html.unescape(t).strip())


def snapshot(pid, ts, url):
    raw = "https://web.archive.org/web/%sid_/%s" % (ts, url)
    try:
        s = fetch(raw, timeout=90, retries=3)
    except Exception as e:
        print("  fail", pid, e)
        return pid, None
    title = re.search(r"<title>(.*?)</title>", s, re.S)
    title = clean_title(title.group(1)) if title else ""
    pub = re.search(r'article:published_time" content="([^"]+)"', s)
    cats = re.findall(r'rel="category tag">([^<]+)<', s)
    return pid, {
        "id": pid,
        "title": title,
        "date": pub.group(1)[:10] if pub else "",
        "categories": sorted(set(html.unescape(c) for c in cats)),
        "url": "https://web.archive.org/web/%s/%s" % (ts, url),
        "orig_url": "https://www.lzjscript.com/archives/" + pid,
        "first_seen": today(),
    }


def main():
    store = load(STORE)
    for rec in store.values():
        rec["title"] = clean_title(rec["title"])
    rows = json.loads(fetch(CDX, timeout=180, retries=8))[1:]
    # Prefer the newest 200 snapshot per post; fall back to redirects.
    latest = {}
    for url, ts, status in rows:
        m = re.fullmatch(r"https?://(?:www\.)?lzjscript\.com(?::80)?/archives/(\d+)/?", url)
        if not m:
            continue
        pid = m.group(1)
        rank = (status == "200", ts)
        if pid not in latest or rank > latest[pid][0]:
            latest[pid] = (rank, ts, url)
    latest = {p: (ts, u) for p, (_, ts, u) in latest.items()}
    todo = [(p, ts, u) for p, (ts, u) in latest.items() if p not in store or not store[p].get("title")]
    print("lzjscript: %d posts in wayback, %d to fetch" % (len(latest), len(todo)))
    with ThreadPoolExecutor(2) as ex:
        for i, (pid, rec) in enumerate(ex.map(lambda a: snapshot(*a), todo)):
            if rec and rec["title"]:
                store[pid] = rec
            if i % 50 == 49:
                save(STORE, store)
                print("  %d/%d" % (i + 1, len(todo)))
    save(STORE, store)
    print("lzjscript: %d items" % len(store))


if __name__ == "__main__":
    main()
