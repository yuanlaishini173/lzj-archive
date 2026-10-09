"""Build the static site in site/ from data/*.json."""
import html
import json
import os
import re
import shutil
import time

ROOT = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(ROOT, "data")
SITE = os.path.join(ROOT, "site")
TEMPLATES = os.path.join(ROOT, "templates")


def load(name):
    path = os.path.join(DATA, name)
    if not os.path.exists(path):
        return {}
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def plain(h):
    return re.sub(r"\s+", " ", html.unescape(re.sub(r"<[^>]+>", " ", h))).strip()


def main():
    items = []
    for v in load("youtube.json").values():
        items.append({"s": v.get("kind", "video"), "t": v.get("title", ""), "d": v.get("date", ""),
                      "a": 1 if v.get("date_approx") else 0, "u": v["url"],
                      "g": v.get("playlists", []), "dur": v.get("duration"), "v": v.get("views")})

    os.makedirs(os.path.join(SITE, "a"), exist_ok=True)
    with open(os.path.join(TEMPLATES, "article.html"), encoding="utf-8") as f:
        article_tpl = f.read()
    for v in load("medium.json").values():
        path = os.path.join(DATA, "medium", v["id"] + ".html")
        body = open(path, encoding="utf-8").read() if os.path.exists(path) else ""
        with open(os.path.join(SITE, "a", v["id"] + ".html"), "w", encoding="utf-8") as f:
            f.write(article_tpl.replace("{{TITLE}}", html.escape(v["title"]))
                    .replace("{{DATE}}", v["date"]).replace("{{SOURCE}}", html.escape(v["url"]))
                    .replace("{{BODY}}", body))
        items.append({"s": "article", "t": v["title"], "d": v["date"], "u": "a/%s.html" % v["id"],
                      "src": v["url"], "g": v.get("tags", []), "x": plain(body)})

    for v in load("lzjscript.json").values():
        items.append({"s": "script", "t": v["title"], "d": v.get("date", ""), "u": v["url"],
                      "g": v.get("categories", [])})

    for v in load("books.json").values():
        items.append({"s": v["kind"], "t": v["title"], "d": v.get("date", ""), "u": v["url"],
                      "n": v.get("detail", ""), "g": []})

    items.sort(key=lambda i: i["d"], reverse=True)
    for i in items:  # drop empty fields to keep data.json small
        for k in [k for k, val in i.items() if val in (None, "", [], 0) and k not in ("t", "d", "u", "s")]:
            del i[k]

    with open(os.path.join(SITE, "data.json"), "w", encoding="utf-8") as f:
        json.dump({"updated": time.strftime("%Y-%m-%d", time.gmtime()), "items": items},
                  f, ensure_ascii=False, separators=(",", ":"))
    shutil.copy(os.path.join(TEMPLATES, "index.html"), os.path.join(SITE, "index.html"))
    open(os.path.join(SITE, ".nojekyll"), "w").close()
    counts = {}
    for i in items:
        counts[i["s"]] = counts.get(i["s"], 0) + 1
    print("built site:", len(items), "items", counts)


if __name__ == "__main__":
    main()
