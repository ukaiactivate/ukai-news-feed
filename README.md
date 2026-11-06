# UKAI Daily AI News feed

This repository hosts the RSS feed that Ready Membership imports into the resources section of [ukai.co](https://ukai.co).

**Feed address:** https://ukaiactivate.github.io/ukai-news-feed/feed.xml

## How it works

1. A scheduled Claude task finds the day's AI news and writes each story in the UKAI house style.
2. `tools/build.py` saves the story to `data/items.json`, creates a branded 1200 x 630 image in `images/`, and rebuilds `feed.xml`.
3. The changes are pushed here and GitHub Pages publishes them.
4. Ready's RSS connector picks up new items, including the image.

## Feed format

Each item carries:

- `title`, `pubDate`, `category` and a unique `guid`
- `description`: a short plain-text standfirst
- `content:encoded`: the full article HTML, including related UKAI links and the source
- the image three ways, so the importer can use whichever it supports: `enclosure`, `media:content` and `media:thumbnail`

The feed keeps the latest 50 items.

## Search engines

This site is blocked from search engines (`robots.txt` and a `noindex` home page), so the ukai.co articles are the only indexed copy of each story.

## Adding a story by hand

```
python3 tools/build.py add path/to/item.json
```

The item format is described at the top of `tools/build.py`. Images need `rsvg-convert` (librsvg). The brand fonts are bundled in `tools/fonts` under the SIL Open Font License.
