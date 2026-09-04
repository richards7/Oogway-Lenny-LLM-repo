#!/usr/bin/env python3
"""
Convert the ChatPRD/lennys-podcast-transcripts repo into the flat .txt format
that scripts/ingest.py consumes.

Source layout:  <repo>/episodes/<slug>/transcript.md  (YAML frontmatter + body)
Target layout:  data/transcripts/<slug>.txt           ('# Key: value' header + body)

Usage:
    python scripts/import_lennys_repo.py --repo /path/to/lennys-podcast-transcripts
    python scripts/import_lennys_repo.py --repo ... --dry-run
"""
import os
import re
import sys
import hashlib
import argparse

import yaml

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DEFAULT_OUT = os.path.join(PROJECT_ROOT, "data", "transcripts")


def split_frontmatter(raw: str):
    """Return (metadata dict, body text). Tolerates files with no frontmatter."""
    if not raw.startswith("---"):
        return {}, raw

    lines = raw.splitlines()
    end = None
    for i, line in enumerate(lines[1:], start=1):
        if line.strip() == "---":
            end = i
            break
    if end is None:
        return {}, raw

    try:
        meta = yaml.safe_load("\n".join(lines[1:end])) or {}
    except yaml.YAMLError:
        meta = {}
    if not isinstance(meta, dict):
        meta = {}
    return meta, "\n".join(lines[end + 1:]).strip()


def neutralize_headings(body: str) -> str:
    """
    ingest.py drops every line starting with '#' as a metadata comment.
    Indent markdown headings by one space so their text survives chunking.
    """
    return "\n".join(" " + ln if ln.startswith("#") else ln for ln in body.splitlines())


def canonical_slug(slugs):
    """
    Pick the best slug for a group of byte-identical transcripts. The repo carries
    some episodes under variant slugs ('wes-kao' / 'wes-kao-20', 'fei-fei' /
    'dr-fei-fei-li'). Prefer an unsuffixed, more descriptive slug.
    """
    def rank(s):
        return (s.endswith("_"), bool(re.search(r"-\d+$", s)), -len(s), s)
    return sorted(slugs, key=rank)[0]


def build_header(meta: dict, slug: str) -> str:
    title = str(meta.get("title") or meta.get("guest") or slug.replace("-", " ").title())
    title = " ".join(title.split())  # collapse YAML line-wrapped titles
    url = meta.get("youtube_url") or meta.get("spotify_url") or ""

    header = [f"# Episode Title: {title}", f"# URL: {url}"]
    if meta.get("guest"):
        header.append(f"# Guest: {meta['guest']}")
    if meta.get("publish_date"):
        header.append(f"# Published: {meta['publish_date']}")
    return "\n".join(header)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--repo", required=True, help="Path to the cloned transcripts repo")
    ap.add_argument("--out", default=DEFAULT_OUT, help="Target transcripts directory")
    ap.add_argument("--dry-run", action="store_true", help="Report without writing")
    args = ap.parse_args()

    episodes_dir = os.path.join(args.repo, "episodes")
    if not os.path.isdir(episodes_dir):
        sys.exit(f"No 'episodes/' directory under {args.repo}")

    os.makedirs(args.out, exist_ok=True)

    parsed = {}
    skipped_empty = 0

    for slug in sorted(os.listdir(episodes_dir)):
        src = os.path.join(episodes_dir, slug, "transcript.md")
        if not os.path.isfile(src):
            continue

        with open(src, "r", encoding="utf-8") as f:
            meta, body = split_frontmatter(f.read())

        body = neutralize_headings(body).strip()
        if not body:
            skipped_empty += 1
            print(f"[SKIP] {slug}: empty body")
            continue

        parsed[slug] = (meta, body)

    # Collapse byte-identical transcripts published under variant slugs.
    by_hash = {}
    for slug, (_meta, body) in parsed.items():
        by_hash.setdefault(hashlib.md5(body.encode("utf-8")).hexdigest(), []).append(slug)

    keep, dropped = set(), []
    for slugs in by_hash.values():
        winner = canonical_slug(slugs)
        keep.add(winner)
        dropped += [s for s in slugs if s != winner]

    written = 0
    no_url = []
    for slug in sorted(keep):
        meta, body = parsed[slug]
        if not (meta.get("youtube_url") or meta.get("spotify_url")):
            no_url.append(slug)

        content = build_header(meta, slug) + "\n\n" + body + "\n"
        dest = os.path.join(args.out, f"{slug}.txt")

        if args.dry_run:
            print(f"[DRY] would write {dest} ({len(body):,} chars)")
        else:
            with open(dest, "w", encoding="utf-8") as f:
                f.write(content)
        written += 1

    print(f"\nConverted {written} transcripts -> {args.out}")
    if skipped_empty:
        print(f"Skipped {skipped_empty} with empty bodies")
    if dropped:
        print(f"Dropped {len(dropped)} duplicate slugs: {', '.join(sorted(dropped))}")
    if no_url:
        print(f"{len(no_url)} without a source URL (citations render unlinked): {', '.join(no_url)}")
    if not args.dry_run:
        print("\nNext: python scripts/ingest.py")


if __name__ == "__main__":
    main()
