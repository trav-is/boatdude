# The Boat Dude — No‑Build MVP

A clean, mobile‑first gallery to list boats & PWCs. No backend required. The app loads inventory from **static CSV files** under `data/exports/` (`boats-sheet.csv`, `photos-sheet.csv`). Paths are set in `app.js` as `SHEET_CSV_URL` and `PHOTO_GALLERY_CSV_URL` (defaults: `/data/exports/…`). Legacy sample JSON may still exist under `data/` for reference only.

## Quick Start (Local dev)
1. `python3 -m http.server 8080` from this folder.
2. Open `http://localhost:8080` — inventory loads from `data/exports/boats-sheet.csv` and `data/exports/photos-sheet.csv` (generate or refresh with `scripts/pull_marketplace.py`).
3. After editing CSVs or re-running the pull script, refresh the browser to see changes.

## Optional: Google Sheets (publish to web)
You can keep editing in Sheets and either export CSV into `data/exports/`, or point `app.js` at published CSV URLs instead of `/data/exports/…` paths.

1. **Make a copy of the template:** Import `data/boats-template.csv` into Google Sheets. Keep the column headers as‑is.
2. **Fill rows** for each listing. Put multiple image URLs in `gallery_urls` separated by commas. (Tip: store photos in Google Drive, then use the shareable file link converted to a direct image link e.g. `https://drive.google.com/uc?export=view&id=FILE_ID`)
3. **Publish as CSV** or **Download → CSV** and copy into `data/exports/`, *or* publish and paste the two CSV URLs into `SHEET_CSV_URL` / `PHOTO_GALLERY_CSV_URL` in `app.js`.
4. **Deploy** includes committing or uploading the `data/exports/` files (or relying on live Sheet URLs if you switched constants).

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
`pull_marketplace.py` writes the same column layout the UI expects. Outputs default to the paths the site loads (`data/exports/boats-sheet.csv`, `data/exports/photos-sheet.csv`) unless you pass `--boats-out` / `--photos-out`.

**Shortest run:** with no URL flags, the script pulls the default OnlyInboards dealer profile and PontoonsOnly `k=boatdudedeals` search (same two feeds as below):

```bash
python3 scripts/pull_marketplace.py
```

Run **both** marketplaces from clean inventory/search URLs (repeat `--source` per site) when you want to override:

```bash
python3 scripts/pull_marketplace.py \
  --source "https://onlyinboards.com/dealeruserprofile/80113" \
  --source "https://www.pontoonsonly.com/search?k=boatdudedeals" \
  --snapshot-out "data/exports/marketplace-snapshot.json"
```

OnlyInboards-only (same as one `--source` above; `--dealer-url` still works as a deprecated alias):

```bash
python3 scripts/pull_marketplace.py \
  --dealer-url "https://onlyinboards.com/dealeruserprofile/80113"
```

PontoonsOnly extras — explicit listing lines or a file when you do not use search (or for page 2+ of search):

```bash
# Option A — repeat flag
python3 scripts/pull_marketplace.py \
  --listing-url "https://www.pontoonsonly.com/2024-Premier-for-sale-in-Cornelius-NorthCarolina_i25518" \
  --listing-url "https://www.pontoonsonly.com/2025-Some-Other-Pontoon_i99999"

# Option B — one URL per line in a file (# starts a comment)
python3 scripts/pull_marketplace.py \
  --urls-file "data/pontoons-urls.txt"
```

What this gives you:
- `data/exports/boats-sheet.csv` for your Boats tab
- `data/exports/photos-sheet.csv` for your Photo Gallery tab
- `data/exports/marketplace-snapshot.json` (or any path you pass) for audit/debug

Notes:
- **OnlyInboards:** IDs are `oib-<numeric_id>`; use `--source` with your dealer profile URL.
- **PontoonsOnly:** IDs are `po-<id>` from `_i####` URLs. Use `--source` with a dealer keyword search (e.g. `…/search?k=boatdudedeals`) to harvest page 1, or pass listings with `--listing-url` / `--urls-file`. Search results beyond page 1 use form postback, so the script warns and you add more listing URLs manually when needed.
- Script defaults to `published=Y`, `status=available`.
- `--id-prefix` overrides auto `oib` / `po` per host if you merge feeds into one sheet.

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

`photos-optimized/` is intentionally not in the repo (large binaries). Regenerate it locally with `optimize-images.py`, or upload that folder to the host if you use disk-based images; otherwise use image URLs from Sheets/CSV.

— Built 2025-09-14
