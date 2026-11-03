# Where to get full primary text for corpus grep

You need complete, machine-greppable text of the *whole* corpus, not a search
result page. Provenance matters: a canonical, timestamped, citable copy.

## Project Gutenberg (English / Western canon, public domain, no key)

Stable direct-text URL pattern — `<id>` is the ebook number:

```bash
curl -s --ssl-no-revoke -o vol04.txt \
  "https://www.gutenberg.org/cache/epub/<id>/pg<id>.txt"
head -30 vol04.txt      # confirms Title: ... and that the download is the right work
```

Use `--ssl-no-revoke` on Windows git-bash curl — Schannel's certificate
revocation check fails offline and reports a fake network error (see
`blocked-page-recovery`). Python `urllib`/`httpx` (certifi) also works fine.

Find candidate volume IDs by scraping the site search page rather than relying
on a book-metadata API:

```bash
curl -s "https://www.gutenberg.org/ebooks/search/?query=<author+works>" \
  | grep -oE 'ebooks/[0-9]+' | sort -u
```

Multi-volume authors (e.g. collected works in 12 volumes) put one work per
volume. Download them all, grep each, print `id / char-count / hit-count /
title` per volume — that table is the evidence that rules volumes in and out.

Large texts (≈1 MB each) walk fine through `urllib` with an explicit proxy:

```python
op = urllib.request.build_opener(urllib.request.ProxyHandler(
    {"http": "http://127.0.0.1:<port>", "https": "http://127.0.0.1:<port>"}))
```

Respect the license: Gutenberg text is public domain in the US; keep the
boilerplate header in the cached copy so the provenance travels with it.

## Classical Chinese and other traditions

- **ctext.org** (Chinese Text Project) — full-text search and plain-text
  downloads for classical Chinese texts.
- **Wikisource** — per-language, good for speeches, letters, statutes, and
  modern public-domain translations; grab the raw wikitext
  (`?action=raw`) rather than the rendered page for clean grep input.

## Local corpora

When the user is checking their *own* text (notes, an extracted book, a
manuscript), the corpus is a file on disk: grep it directly and report the file
plus offset. Same rules apply — never substitute recall for the file.

## Caching

Download once into a working directory and reuse across the session
(`cache/scratch/<author>_cache/`). Re-fetching a 1 MB volume per probe wastes
minutes on a slow link; a per-volume hit table only deserves a re-download when
the file was truncated.
