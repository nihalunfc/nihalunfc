# Notes for Claude sessions in nihal's GitHub profile repo

This repo is the README shown on github.com/nihalunfc. It is written for employers and investors.

## What updates itself (do not hand-edit between the markers)
`.github/workflows/refresh-readme.yml` runs `scripts/build_readme.py` every day and fills:
- `FEATURED`: from nihalsulaiman.com's `src/content/projects` (except Kaggle), `src/content/swarm` and `src/content/courses`.
- `ACTIVITY`: the newest six entries of the site's activity log (`src/content/log`, written by #UpdateLog).
- `WRITING`: the newest three blog posts.
- `FIBUB`: fibub.com totals (live tools, Learn pages, articles, courses), the five newest tools (highest #T code), the five latest articles and each course's live lessons, from the fibub repo's `src/tools`, `src/blog` and `src/courses`.
- `SHIPPED`: the newest merged pull requests across every public repo shown in the table (pushed in the last 30 days, at most 3 per repo, 10 in all). New public repos join automatically; `exclude` in `repos.json` keeps a repo out.
- `REPOS`: repos listed in `repos.json`, plus any other public repo pushed in the last 60 days (shown as New). Listed in-progress work with no push for 120 days shows as Paused.

So new projects, courses, posts and log entries reach the profile once they are on the site, fibub work once it is merged to fibub's `main`, and any merged PR in a public repo the next morning. To change a featured project, change it on the site, not here.

## What is edited by hand
About, the Now table, Kaggle results, tech stack, certifications, badges and recognition, education and experience. When nihal earns a certificate or badge, starts using a new tool, changes job, or a Kaggle rank changes or a competition ends, update that section here in the same session (and the site's CV).

When a repo finishes or a new repo should be named properly, edit `repos.json` (status `Completed`, a title and a one-line `what`), or add it to `exclude` if it is personal or scratch work.

## Rules
- Never name the former employer from the one-week BI job (Nov 2026) or any company nihal is applying to.
- No phone number. MSc specialisation is cosmology.
- Kaggle: only scores from nihal's own work; never public-notebook scores.
- Shields.io badges: Simple Icons no longer has Microsoft or LinkedIn logos, so those badges have no `logo=`.
