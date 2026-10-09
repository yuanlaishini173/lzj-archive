"""Shared helpers: HTTP with retries, JSON store that only ever grows."""
import json
import os
import time
import urllib.request

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(ROOT, "data")
UA = "Mozilla/5.0 (compatible; lzj-archive/1.0; +https://github.com/)"


def fetch(url, timeout=60, retries=4, binary=False):
    last = None
    for i in range(retries):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": UA})
            with urllib.request.urlopen(req, timeout=timeout) as r:
                body = r.read()
                return body if binary else body.decode("utf-8", errors="replace")
        except Exception as e:  # network flakiness is expected; back off and retry
            last = e
            time.sleep(2 * (i + 1))
    raise last


def load(name, default=None):
    path = os.path.join(DATA, name)
    if not os.path.exists(path):
        return {} if default is None else default
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def save(name, obj):
    path = os.path.join(DATA, name)
    tmp = path + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(obj, f, ensure_ascii=False, indent=1, sort_keys=True)
        f.write("\n")
    os.replace(tmp, path)


def today():
    return time.strftime("%Y-%m-%d", time.gmtime())
