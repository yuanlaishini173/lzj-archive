"""YouTube: Liu Zhongjing's official channel (videos, live streams, playlists).

Listing uses yt-dlp's flat playlist mode (no video downloads). Upload dates in
flat mode are only approximate ("3 years ago"), so each run also:
  * takes exact dates for the newest ~15 uploads from the channel RSS feed;
  * resolves exact dates for up to RESOLVE_LIMIT older videos via yt-dlp.
Items are never removed; a video that disappears keeps its record.
"""
import json
import os
import re
import subprocess
import sys
import time
import xml.etree.ElementTree as ET

from common import fetch, load, save, today

CHANNELS = {
    "UC0KwJ-ig7udwmMgGjZyR41A": "Zhongjing Liu | 劉仲敬 官方頻道",
}
TABS = {"videos": "video", "streams": "live"}
RESOLVE_LIMIT = int(os.environ.get("YT_RESOLVE_LIMIT", "250"))
STORE = "youtube.json"


def ytdlp(args, timeout=1800):
    cmd = [sys.executable, "-m", "yt_dlp", "--ignore-errors", "--no-warnings"] + args
    r = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
    if r.returncode != 0 and not r.stdout:
        print("  yt-dlp failed:", r.stderr.strip()[-400:])
    return r.stdout


def flat(url, approx=False):
    args = ["--flat-playlist", "-J"]
    if approx:
        args += ["--extractor-args", "youtubetab:approximate_date"]
    out = ytdlp(args + [url])
    try:
        data = json.loads(out)
    except ValueError:
        return []
    if not isinstance(data, dict):  # e.g. channel has no such tab
        return []
    return [e for e in data.get("entries") or [] if e and e.get("id")]


def ymd(ts):
    return time.strftime("%Y-%m-%d", time.gmtime(ts))


def main():
    store = load(STORE)
    seen_today = today()
    n_before = len(store)

    for cid, cname in CHANNELS.items():
        base = "https://www.youtube.com/channel/" + cid
        for tab, kind in TABS.items():
            entries = flat(base + "/" + tab, approx=True)
            print("%s/%s: %d entries" % (cid, tab, len(entries)))
            for e in entries:
                vid = e["id"]
                it = store.setdefault(vid, {"id": vid, "first_seen": seen_today})
                it.update({
                    "title": e.get("title") or it.get("title", ""),
                    "url": "https://www.youtube.com/watch?v=" + vid,
                    "kind": kind,
                    "channel": cname,
                    "last_seen": seen_today,
                })
                if e.get("duration"):
                    it["duration"] = int(e["duration"])
                if e.get("view_count") is not None:
                    it["views"] = e["view_count"]
                if not it.get("date") and e.get("timestamp"):
                    it["date"] = ymd(e["timestamp"])
                    it["date_approx"] = True

        save(STORE, store)

        # Exact dates for the newest uploads.
        try:
            xml = fetch("https://www.youtube.com/feeds/videos.xml?channel_id=" + cid)
            ns = {"a": "http://www.w3.org/2005/Atom", "yt": "http://www.youtube.com/xml/schemas/2015"}
            for en in ET.fromstring(xml).findall("a:entry", ns):
                vid = en.find("yt:videoId", ns).text
                it = store.setdefault(vid, {"id": vid, "first_seen": seen_today, "kind": "video",
                                            "channel": cname, "url": "https://www.youtube.com/watch?v=" + vid})
                it["title"] = en.find("a:title", ns).text
                it["date"] = en.find("a:published", ns).text[:10]
                it.pop("date_approx", None)
                it["last_seen"] = seen_today
        except Exception as ex:
            print("  rss failed:", ex)

        # Playlists -> tags.
        pls = flat(base + "/playlists")
        print("%s/playlists: %d" % (cid, len(pls)))
        if pls:
            for it in store.values():
                if it.get("channel") == cname:
                    it["playlists"] = []
            for p in pls:
                ptitle = p.get("title") or ""
                for e in flat("https://www.youtube.com/playlist?list=" + p["id"]):
                    if e["id"] in store and ptitle not in store[e["id"]]["playlists"]:
                        store[e["id"]]["playlists"].append(ptitle)

    save(STORE, store)

    # Resolve exact upload dates for a batch of approximate ones.
    todo = sorted((v for v in store.values() if v.get("date_approx")),
                  key=lambda v: v.get("date", ""), reverse=True)[:RESOLVE_LIMIT]
    if todo:
        out = ytdlp(["--skip-download", "--sleep-requests", "1",
                     "--print", "%(id)s\t%(upload_date)s\t%(duration)s"]
                    + [v["url"] for v in todo], timeout=5400)
        fixed = 0
        for line in out.splitlines():
            parts = line.split("\t")
            if len(parts) == 3 and re.fullmatch(r"\d{8}", parts[1]) and parts[0] in store:
                d = parts[1]
                it = store[parts[0]]
                it["date"] = "%s-%s-%s" % (d[:4], d[4:6], d[6:])
                it.pop("date_approx", None)
                if parts[2].isdigit():
                    it["duration"] = int(parts[2])
                fixed += 1
        print("exact dates resolved: %d/%d" % (fixed, len(todo)))

    save(STORE, store)
    print("youtube: %d -> %d items" % (n_before, len(store)))


if __name__ == "__main__":
    main()
