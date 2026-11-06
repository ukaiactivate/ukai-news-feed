#!/usr/bin/env python3
"""Build the UKAI Daily AI News RSS feed.

Usage:
  python3 tools/build.py add path/to/item.json   # add one story, render its image, rebuild the feed
  python3 tools/build.py build                   # rebuild feed.xml and all images from data/items.json

An item JSON file looks like:
{
  "id": "2026-11-06-ai-economic-estimate",          # unique, lowercase, hyphens
  "date": "2026-11-06T08:00:00+00:00",              # ISO 8601
  "title": "Headline in sentence case",
  "summary": "One or two sentence standfirst, plain text.",
  "category": "Policy",                             # short topic label
  "card_stat": "£120bn",                            # optional big figure for the image
  "card_line": "Short line under the figure",       # optional, used with card_stat
  "body_html": "<p>...</p><h3>Why it matters</h3><p>...</p>",
  "related": [{"title": "UKAI article title", "url": "https://ukai.co/resource/..."}],
  "source_name": "Publication name",
  "source_url": "https://..."
}
"""
import html
import json
import os
import subprocess
import sys
import tempfile
import textwrap
from datetime import datetime
from email.utils import format_datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data" / "items.json"
IMAGES = ROOT / "images"
FONTS = ROOT / "tools" / "fonts"
FEED = ROOT / "feed.xml"

SITE_URL = "https://ukaiactivate.github.io/ukai-news-feed"
CHANNEL = {
    "title": "UKAI Daily AI News",
    "link": "https://ukai.co",
    "description": "Daily summaries of AI news relevant to the UK AI industry, from UKAI.",
}
MAX_ITEMS = 50

# UKAI brand colours
DARK_TEAL = "#082D30"
MID_TEAL = "#0F4548"
BRIGHT_TEAL = "#1E9188"
MINT = "#17FFBD"
YELLOW = "#ECE55C"
REQUIRED = ["id", "date", "title", "summary", "category", "body_html", "source_name", "source_url"]


def esc(s):
    return html.escape(str(s), quote=True)


def card_svg(item):
    date = datetime.fromisoformat(item["date"]).strftime("%-d %b %Y").upper()
    kicker = f"UKAI DAILY AI NEWS · {esc(item['category'].upper())} · {date}"
    parts = [
        '<svg xmlns="http://www.w3.org/2000/svg" width="1200" height="630" viewBox="0 0 1200 630">',
        '<defs><radialGradient id="g" cx="0" cy="1" r="1.2">'
        f'<stop offset="0" stop-color="{BRIGHT_TEAL}"/><stop offset="0.55" stop-color="{MID_TEAL}"/>'
        f'<stop offset="1" stop-color="{DARK_TEAL}"/></radialGradient></defs>',
        '<rect width="1200" height="630" fill="url(#g)"/>',
        f'<text x="70" y="105" font-family="JetBrains Mono" font-weight="500" font-size="24" '
        f'fill="{YELLOW}" letter-spacing="3">{kicker}</text>',
    ]
    if item.get("card_stat"):
        parts.append(f'<text x="64" y="330" font-family="Space Grotesk" font-weight="700" '
                     f'font-size="200" fill="#FFFFFF">{esc(item["card_stat"])}</text>')
        lines = textwrap.wrap(item.get("card_line", ""), 36)[:2]
        for i, line in enumerate(lines):
            colour = "#FFFFFF" if i == 0 else MINT
            parts.append(f'<text x="70" y="{420 + i * 62}" font-family="Space Grotesk" font-weight="500" '
                         f'font-size="50" fill="{colour}">{esc(line)}</text>')
    else:
        lines = textwrap.wrap(item["title"], 30)[:4]
        top = 330 - (len(lines) - 1) * 40
        for i, line in enumerate(lines):
            parts.append(f'<text x="70" y="{top + i * 80}" font-family="Space Grotesk" font-weight="700" '
                         f'font-size="68" fill="#FFFFFF">{esc(line)}</text>')
    parts.append(f'<rect x="70" y="550" width="120" height="8" fill="{YELLOW}"/>')
    parts.append("</svg>")
    return "\n".join(parts)


def render_image(item):
    IMAGES.mkdir(exist_ok=True)
    out = IMAGES / f"{item['id']}.png"
    with tempfile.TemporaryDirectory() as tmp:
        conf = Path(tmp) / "fonts.conf"
        conf.write_text(
            '<?xml version="1.0"?><!DOCTYPE fontconfig SYSTEM "fonts.dtd"><fontconfig>'
            f"<dir>{FONTS}</dir><include ignore_missing=\"yes\">/etc/fonts/fonts.conf</include>"
            f"<cachedir>{tmp}/cache</cachedir></fontconfig>"
        )
        svg = Path(tmp) / "card.svg"
        svg.write_text(card_svg(item), encoding="utf-8")
        env = dict(os.environ, FONTCONFIG_FILE=str(conf))
        subprocess.run(["rsvg-convert", "-w", "1200", "-h", "630", "-o", str(out), str(svg)],
                       check=True, env=env)
    return out


def full_body(item):
    body = item["body_html"]
    if item.get("related"):
        links = "".join(f'<li><a href="{esc(r["url"])}">{esc(r["title"])}</a></li>' for r in item["related"])
        body += f"<h3>Related on UKAI</h3><ul>{links}</ul>"
    body += f'<p>Source: <a href="{esc(item["source_url"])}">{esc(item["source_name"])}</a></p>'
    body += "<p><em>Created by Amplify: AI-augmented, human-curated content.</em></p>"
    return body


def item_xml(item):
    img = f"{SITE_URL}/images/{item['id']}.png"
    size = (IMAGES / f"{item['id']}.png").stat().st_size
    pub = format_datetime(datetime.fromisoformat(item["date"]))
    body = full_body(item).replace("]]>", "]]]]><![CDATA[>")
    return f"""    <item>
      <title>{esc(item['title'])}</title>
      <link>{esc(item['source_url'])}</link>
      <guid isPermaLink="false">ukai-news-{esc(item['id'])}</guid>
      <pubDate>{pub}</pubDate>
      <category>{esc(item['category'])}</category>
      <description>{esc(item['summary'])}</description>
      <content:encoded><![CDATA[{body}]]></content:encoded>
      <enclosure url="{img}" length="{size}" type="image/png"/>
      <media:content url="{img}" medium="image" type="image/png" width="1200" height="630"/>
      <media:thumbnail url="{img}" width="1200" height="630"/>
    </item>"""


def write_feed(items):
    now = format_datetime(datetime.now().astimezone())
    body = "\n".join(item_xml(i) for i in items)
    FEED.write_text(f"""<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0" xmlns:content="http://purl.org/rss/1.0/modules/content/" xmlns:media="http://search.yahoo.com/mrss/" xmlns:atom="http://www.w3.org/2005/Atom">
  <channel>
    <title>{esc(CHANNEL['title'])}</title>
    <link>{CHANNEL['link']}</link>
    <description>{esc(CHANNEL['description'])}</description>
    <language>en-gb</language>
    <lastBuildDate>{now}</lastBuildDate>
    <atom:link href="{SITE_URL}/feed.xml" rel="self" type="application/rss+xml"/>
{body}
  </channel>
</rss>
""", encoding="utf-8")


def load():
    return json.loads(DATA.read_text(encoding="utf-8")) if DATA.exists() else []


def save(items):
    DATA.parent.mkdir(exist_ok=True)
    DATA.write_text(json.dumps(items, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def validate(item):
    missing = [k for k in REQUIRED if not item.get(k)]
    if missing:
        sys.exit(f"Item is missing: {', '.join(missing)}")
    datetime.fromisoformat(item["date"])


def main():
    if len(sys.argv) < 2 or sys.argv[1] not in ("add", "build"):
        sys.exit(__doc__)
    items = load()
    if sys.argv[1] == "add":
        new = json.loads(Path(sys.argv[2]).read_text(encoding="utf-8"))
        validate(new)
        items = [i for i in items if i["id"] != new["id"]]
        items.insert(0, new)
        render_image(new)
    else:
        for i in items:
            render_image(i)
    items.sort(key=lambda i: i["date"], reverse=True)
    items = items[:MAX_ITEMS]
    save(items)
    write_feed(items)
    print(f"Feed rebuilt with {len(items)} item(s): {FEED}")


if __name__ == "__main__":
    main()
