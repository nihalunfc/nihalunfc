"""Refresh the repository table in README.md.

Reads repos.json, asks the GitHub API for each repo's creation date, last push
and main language, and rewrites the block between the REPOS markers.
Run locally with `python scripts/build_readme.py` (set GITHUB_TOKEN to avoid
rate limits) or let .github/workflows/refresh-readme.yml run it weekly.
"""
import json
import os
import re
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OWNER = "nihalunfc"
START, END = "<!-- REPOS:START -->", "<!-- REPOS:END -->"
STATUS_COLOUR = {"In progress": "2563eb", "Completed": "16a34a"}


def api(path):
    req = urllib.request.Request(f"https://api.github.com{path}", headers={"Accept": "application/vnd.github+json", "User-Agent": "profile-readme-refresh"})
    token = os.environ.get("GITHUB_TOKEN")
    if token:
        req.add_header("Authorization", f"Bearer {token}")
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.load(r)


def month(iso):
    return datetime.fromisoformat(iso.replace("Z", "+00:00")).strftime("%b %Y")


def day(iso):
    return datetime.fromisoformat(iso.replace("Z", "+00:00")).strftime("%d %b %Y")


def badge(status):
    colour = STATUS_COLOUR.get(status, "6b7280")
    label = status.replace(" ", "%20")
    return f'<img src="https://img.shields.io/badge/-{label}-{colour}?style=flat-square" alt="{status}">'


def build():
    cfg = json.loads((ROOT / "repos.json").read_text())
    rows = []
    for item in cfg["repos"]:
        info = api(f"/repos/{OWNER}/{item['name']}")
        if info.get("private"):
            continue  # never list private work
        links = f"[Code]({info['html_url']})"
        if item.get("demo"):
            links += f" · [{item.get('demo_label', 'Write-up')}]({item['demo']})"
        rows.append((info["pushed_at"], f"| **{item['title']}**<br><sub>{item['what']}</sub> | {badge(item['status'])} | {item.get('language') or info.get('language') or '-'} | {month(info['created_at'])} | {day(info['pushed_at'])} | {links} |"))
    rows.sort(reverse=True)
    head = "| Repository | Status | Language | Started | Last updated | Links |\n| :-- | :-- | :-- | :-- | :-- | :-- |"
    return "\n".join([START, head, *[r for _, r in rows], "", f"<sub>Dates refresh automatically every week. Last refresh: {datetime.now(timezone.utc):%d %b %Y}.</sub>", END])


def main():
    readme = ROOT / "README.md"
    text = readme.read_text()
    new = re.sub(re.escape(START) + r".*?" + re.escape(END), lambda _: build(), text, flags=re.S)
    if new != text:
        readme.write_text(new)
        print("README.md updated")
    else:
        print("README.md unchanged")


if __name__ == "__main__":
    main()
