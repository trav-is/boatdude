# The Boat Dude — No‑Build MVP

A clean, mobile‑first gallery to list boats & PWCs. No backend required. The live app loads **CSV**: either **local export files** (dev) or **Google Sheets “publish to web” CSV URLs** (prod). Sample static data still lives in `data/boats.json` for reference; the current UI uses the CSV pipeline in `app.js`.

## Quick Start (Local dev)
1. `python3 -m http.server 8080` from this folder.
2. On `localhost`, `app.js` uses the `local` profile: `data/exports/boats-sheet.csv` + `data/exports/photos-sheet.csv` (generate them with `scripts/pull_marketplace.py` or paste from Sheets).
3. Open `http://localhost:8080` — inventory loads from those CSVs.

## Switch to Google Sheets (Phone‑friendly updates)
This lets anyone update inventory from their phone. The site reads a published CSV of your Sheet.

1. **Make a copy of the template:** Import `data/boats-template.csv` into Google Sheets. Keep the column headers as‑is.
2. **Fill rows** for each listing. Put multiple image URLs in `gallery_urls` separated by commas. (Tip: store photos in Google Drive, then use the shareable file link converted to a direct image link e.g. `https://drive.google.com/uc?export=view&id=FILE_ID`)
3. **Publish as CSV:** In Google Sheets, go to **File → Share → Publish to web**. Choose **Link**, select the sheet/tab, and choose **CSV** format. Copy the URL.
4. **Paste URLs into the prod profile:** Open `app.js`, find `PROFILES.prod`, and set `boatsCsvUrl` / `photosCsvUrl` to your two published CSV links.
5. **Deploy** the site. Each time you update the Google Sheet, the website reflects the changes on refresh (no rebuild needed).

> If your Sheet has a `status` column of `sold` the card will gray out. `pending` shows an amber badge. Anything else is considered `available`.

### Columns (must match exactly)
- `id` — unique id like `mcx24-2021`
- `title` — shown on the card (fallback is Year Make Model)
- `category` — `Boat` or `PWC`
- `status` — `available`, `pending`, or `sold`
- `price` — number (e.g. `199900`); leave blank for “Call for price”
- `price_display` — optional override (e.g. `Call for price`, `$19,995 OBO`)
- `year`, `make`, `model`
- `length_ft` — numeric feet (e.g. `24`)
- `hours` — numeric
- `engine`, `hull`, `color`
- `location`
- `description` — plain text
- `primary_image_url` — optional; uses first gallery image if empty
- `gallery_urls` — comma‑separated list of image URLs
- `contact_phone`, `contact_email` — overrides global contact for a single listing
- `created_at` — ISO date like `2025-09-01T12:00:00Z` (for sorting; optional)

## Accessibility
- Keyboard navigation for cards and the photo lightbox
- Visible focus rings; semantic headings; alt text
- High‑contrast dark mode

## Deploy in Minutes
- **Netlify**: drag‑and‑drop this folder to Netlify. Done.
- **Cloudflare Pages**: create a project and point to this folder.
- **CPanel/FTP**: upload all files to your web root (e.g., `public_html`).

## Pull Inventory From Marketplace (Sheets-Compatible)
If production currently reads Google Sheets, keep that flow and generate fresh CSVs to paste/import into your two sheet tabs.

Run:

```bash
python3 scripts/pull_marketplace.py \
  --dealer-url "https://onlyinboards.com/dealeruserprofile/80113" \
  --boats-out "data/exports/boats-sheet.csv" \
  --photos-out "data/exports/photos-sheet.csv" \
  --snapshot-out "data/exports/onlyinboards-snapshot.json"
```

What this gives you:
- `data/exports/boats-sheet.csv` for your Boats tab
- `data/exports/photos-sheet.csv` for your Photo Gallery tab
- `data/exports/onlyinboards-snapshot.json` for audit/debug

Notes:
- IDs are stable as `oib-<listing_id>` so re-runs keep matching rows.
- Script currently pulls active listings and defaults to `published=Y`, `status=available`.
- You can reuse it for other similar sites by changing `--dealer-url` (example: PontoonsOnly dealer URL).

### Runtime Environment Switch (Local vs DreamHost/Prod)
`app.js` now has two profiles:
- `local` (default on `localhost`): reads `data/exports/boats-sheet.csv` and `data/exports/photos-sheet.csv`
- `prod` (default on non-localhost): reads Google Sheets published CSV URLs

You can override profile with query param:
- Local CSV mode: `http://localhost:8080/?env=local`
- Force prod mode locally: `http://localhost:8080/?env=prod`

## Upgrading Later (No‑Database CMS)
When you’re ready for a friendlier editor with image uploads:
- Use **Decap (Netlify) CMS**: adds `/admin` with a form to add/edit boats and upload photos from a phone. Content lives in your Git repo. No servers.
- Or add a tiny **Google Apps Script** endpoint to let a simple admin page modify the Sheet directly.

I can drop in either option when you’re ready. For now, this MVP keeps things simple and fast.

## GitHub
This folder is a static site; initialize Git locally, create an empty repo on GitHub, then connect and push:

```bash
cd /path/to/dev
git init
git add -A
git commit -m "Initial commit: Boat Dude MVP"
git branch -M main
git remote add origin https://github.com/YOUR_USER/YOUR_REPO.git
git push -u origin main
```

DreamHost deploys whatever you upload or pull; keep `main` aligned with production when you deploy from Git.

— Built 2025-09-14
