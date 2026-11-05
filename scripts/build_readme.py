"""Keep the profile README in step with nihal's work.

Fills the marked blocks in README.md:
  FEATURED  projects, Swarm Intelligence and courses from nihalsulaiman.com's content files
  ACTIVITY  the newest entries of the site's activity log (#UpdateLog)
  WRITING   the newest blog posts
  REPOS     public repositories: the ones listed in repos.json, plus any new
            public repo with recent pushes; listed work with no push in
            PAUSED_DAYS shows as Paused

The site repo must be checked out next to this one (SITE_DIR, default ./site).
Run by .github/workflows/refresh-readme.yml every day. Locally:
  git clone --depth 1 https://github.com/nihalunfc/nihalunfc.github.io site
  python scripts/build_readme.py
"""
import json
import os
import re
import urllib.request
from datetime import date, datetime, timezone
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent.parent
SITE = Path(os.environ.get("SITE_DIR", ROOT / "site"))
SITE_URL = "https://nihalsulaiman.com"
OWNER = "nihalunfc"
NEW_REPO_DAYS = 60   # an unlisted public repo pushed within this many days is shown as new work
PAUSED_DAYS = 120    # listed in-progress work with no push for this long shows as Paused
NOW = datetime.now(timezone.utc)

COLOURS = {"In progress": "2563eb", "Live": "16a34a", "Completed": "16a34a", "Published": "16a34a", "Paused": "6b7280", "New": "7c3aed"}
STATUS_WORDS = {"Ongoing": "In progress", "Complete": "Completed"}
LOG_ICONS = {"done": "✅", "progress": "🔧", "started": "🚀", "blocked": "⛔", "idea": "💡"}
FIELD_NAMES = {"hospitality": "Hospitality", "retail": "Retail", "logistics": "Logistics", "energy": "Energy", "crisis": "Crisis management", "science": "Science", "health": "Health", "finance": "Finance"}


# ---------- helpers ----------

def badge(status):
    return f'<img src="https://img.shields.io/badge/-{status.replace(" ", "%20")}-{COLOURS.get(status, "6b7280")}?style=flat-square" alt="{status}">'


def as_dt(value):
    if isinstance(value, datetime):
        return value if value.tzinfo else value.replace(tzinfo=timezone.utc)
    if isinstance(value, date):
        return datetime(value.year, value.month, value.day, tzinfo=timezone.utc)
    return datetime.fromisoformat(str(value).replace("Z", "+00:00"))


def month(value):
    return as_dt(value).strftime("%b %Y")


def day(value):
    return as_dt(value).strftime("%d %b %Y")


def url(href):
    return href if href.startswith("http") else SITE_URL + href


def cell(text):
    return str(text).replace("|", "\\|").replace("\n", " ").strip()


def frontmatter(path):
    text = path.read_text(encoding="utf-8")
    m = re.match(r"^---\s*\n(.*?)\n---", text, re.S)
    return (yaml.safe_load(m.group(1)) or {}) if m else {}


def collection(name):
    folder = SITE / "src" / "content" / name
    return [(p.stem, frontmatter(p)) for p in sorted(folder.glob("*.md"))] if folder.exists() else []


def api(path):
    req = urllib.request.Request(f"https://api.github.com{path}", headers={"Accept": "application/vnd.github+json", "User-Agent": "profile-readme-refresh"})
    if os.environ.get("GITHUB_TOKEN"):
        req.add_header("Authorization", f"Bearer {os.environ['GITHUB_TOKEN']}")
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.load(r)


def all_repos():
    if os.environ.get("REPO_DATA_FILE"):  # offline testing
        return json.loads(Path(os.environ["REPO_DATA_FILE"]).read_text())
    return api(f"/users/{OWNER}/repos?type=owner&per_page=100&sort=pushed")


# ---------- blocks ----------

def featured(log, pushed):
    """Projects, swarm and courses from the site, newest activity first.

    Last updated is the newest of the page's own dates, its activity-log
    entries and the last push to its code repository."""
    last_log = {}
    for _, e in log:
        if e.get("ref"):
            last_log[e["ref"]] = max(last_log.get(e["ref"], as_dt(e["time"])), as_dt(e["time"]))

    rows = []
    for pid, p in collection("projects"):
        if p.get("category") == "Kaggle":
            continue  # Kaggle has its own table
        status = STATUS_WORDS.get(p.get("status"), p.get("status", "In progress"))
        repo_push = pushed.get(p.get("repo", "").rstrip("/").split("/")[-1]) if p.get("repo") else None
        updated = max([as_dt(x) for x in (p.get("date"), p.get("updated"), last_log.get(f"projects/{pid}"), repo_push) if x])
        links = [f"[Write-up]({SITE_URL}/projects/{pid}/)"]
        if p.get("demo"):
            links.insert(0, f"[Live]({url(p['demo'])})")
        if p.get("repo"):
            links.append(f"[Code]({p['repo']})")
        rows.append((p.get("order", 50), updated, p["title"], p["summary"], FIELD_NAMES.get(p.get("field"), ""), status, p["date"], links))

    swarm = collection("swarm")
    if swarm:
        dates = [as_dt(s["date"]) for _, s in swarm]
        refs = [last_log[k] for k in last_log if k.startswith("swarm/")]
        fields = ", ".join(sorted({FIELD_NAMES.get(s.get("field"), "") for _, s in swarm}))
        stats = "; ".join(f"{st['value']} {st['label']}" for _, s in swarm for st in s.get("stats", [])[:1])
        demos = " · ".join(f"[{s['title']}]({url(s['demo'])})" for _, s in sorted(swarm, key=lambda x: x[1].get("order", 50)) if s.get("demo"))
        status = "Live" if any(s.get("status") == "Live" for _, s in swarm) else "In progress"
        if pushed.get("swarm-intelligence"):
            refs.append(as_dt(pushed["swarm-intelligence"]))
        rows.append((0, max(dates + refs), "Swarm Intelligence ⭐ flagship", f"One multi-agent engine where every battery, drone or hotel system decides for itself and the group still acts as one team. {stats}.", fields, status, min(dates), [demos, f"[How it works]({SITE_URL}/swarm/)"]))

    for cid, c in collection("courses"):
        updated = max([as_dt(x) for x in (c.get("date"), c.get("updated"), last_log.get(f"courses/{cid}")) if x])
        rows.append((60 + c.get("order", 50), updated, f"{c['title']} (course)", c["summary"], "Teaching", c.get("status", "Live"), c["date"], [f"[Start learning]({url(c['href'])})"]))

    rows.sort(key=lambda r: (r[0] != 0, -r[1].timestamp()))
    out = ["| Project | Field | Status | Started | Last updated | Links |", "| :-- | :-- | :-- | :-- | :-- | :-- |"]
    for _, updated, title, summary, field, status, started, links in rows:
        out.append(f"| **{cell(title)}**<br><sub>{cell(summary)}</sub> | {field} | {badge(status)} | {month(started)} | {month(updated)} | {' · '.join(links)} |")
    return "\n".join(out)


def activity(log, n=6):
    out = []
    for _, e in log[:n]:
        link = e.get("link") or e.get("commit") or e.get("repo")
        title = f"[{cell(e['title'])}]({url(link)})" if link else cell(e["title"])
        out.append(f"- {LOG_ICONS.get(e.get('status'), '•')} **{day(e['time'])}** · {cell(e['project'])}: {title}")
    out.append(f"\n<sub>From my <a href=\"{SITE_URL}/log/\">activity log</a>, where every piece of work is recorded as it happens.</sub>")
    return "\n".join(out)


def writing(n=3):
    posts = [(pid, p) for pid, p in collection("blog") if not p.get("draft")]
    posts.sort(key=lambda x: as_dt(x[1]["date"]), reverse=True)
    out = [f"- [{cell(p['title'])}]({SITE_URL}/blog/{pid}/) <sub>· {day(p['date'])}</sub>" for pid, p in posts[:n]]
    out.append(f"\n<sub><a href=\"{SITE_URL}/blog/\">All posts</a> · <a href=\"{SITE_URL}/rss.xml\">RSS</a></sub>")
    return "\n".join(out)


def repos(infos):
    cfg = json.loads((ROOT / "repos.json").read_text())
    listed = {r["name"]: r for r in cfg["repos"]}
    skip = set(cfg.get("exclude", [])) | {OWNER}
    rows = []
    for info in infos:
        name = info["name"]
        if info.get("private") or info.get("fork") or info.get("archived") or name in skip:
            continue
        pushed = as_dt(info["pushed_at"])
        idle = (NOW - pushed).days
        item = listed.get(name)
        if item is None:
            if idle > NEW_REPO_DAYS:
                continue  # old, unlisted work is left off
            item = {"title": name, "what": info.get("description") or "New work, details coming soon", "status": "New"}
        status = item["status"]
        if status == "In progress" and idle > PAUSED_DAYS:
            status = "Paused"
        links = f"[Code]({info['html_url']})"
        if item.get("demo"):
            links += f" · [{item.get('demo_label', 'Write-up')}]({item['demo']})"
        lang = item.get("language") or info.get("language") or "-"
        rows.append((pushed, f"| **{cell(item['title'])}**<br><sub>{cell(item['what'])}</sub> | {badge(status)} | {lang} | {month(info['created_at'])} | {day(pushed)} | {links} |"))
    rows.sort(reverse=True)
    head = ["| Repository | Status | Language | Started | Last updated | Links |", "| :-- | :-- | :-- | :-- | :-- | :-- |"]
    return "\n".join(head + [r for _, r in rows])


# ---------- main ----------

def fill(text, name, body):
    start, end = f"<!-- {name}:START -->", f"<!-- {name}:END -->"
    if start not in text:
        return text
    return re.sub(re.escape(start) + r".*?" + re.escape(end), lambda _: f"{start}\n{body}\n{end}", text, flags=re.S)


def main():
    readme = ROOT / "README.md"
    text = readme.read_text(encoding="utf-8")
    infos = all_repos()
    pushed = {i["name"]: i["pushed_at"] for i in infos if not i.get("private")}
    new = fill(text, "REPOS", repos(infos))
    if SITE.exists():
        log = sorted(collection("log"), key=lambda x: as_dt(x[1]["time"]), reverse=True)
        new = fill(new, "FEATURED", featured(log, pushed))
        new = fill(new, "ACTIVITY", activity(log))
        new = fill(new, "WRITING", writing())
    else:
        print(f"Site checkout not found at {SITE}; only the repository table was refreshed")
    if new != text:
        readme.write_text(new, encoding="utf-8")
        print("README.md updated")
    else:
        print("README.md unchanged")


if __name__ == "__main__":
    main()
