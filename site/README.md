# GitHub Pages site

This folder is the static site root for the project.

## Enable Pages

1. Repo **Settings → Pages**
2. Source: **GitHub Actions** (workflow `.github/workflows/pages.yml` deploys `site/`)
   - Or: Deploy from branch `main` / folder `/site` if your GitHub plan supports folder-based Pages
3. Site URL: `https://kesmitij.github.io/cdc-natality-birth-outcomes/`

## Local preview

Open `index.html` in a browser, or:

```bash
py -3.12 -m http.server 8000 --directory site
```

Rebuild after analysis:

```bash
py -3.12 scripts/build_site.py
```
