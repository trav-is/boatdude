# Admin Tools — CSV Workflow (No Server)

The admin page now lets you manage inventory data locally and export a CSV you can upload to Google Sheets later.

## What you get
- `admin/index.html` — UI with Import/Download CSV and a small table view
- `admin/admin.js` — Stores entries in your browser (localStorage) and exports CSV

This is local-only until you upload the CSV to your Sheet.

## Typical flow
1. Import existing CSV (optional): Click “Import CSV” and pick a file exported from your Sheet.
2. Add/update entries:
   - Append Row (Add Listing) creates or updates an item by `id` in local storage.
   - Update Row edits a single field for an existing `id`.
3. Download CSV: Click “Download CSV” to save `boats-admin-export.csv`.
4. Upload to Google Sheets: Open your inventory Sheet and import/replace with the new CSV.

### Optional: Share a listing
- Use the Share column to:
  - Copy Caption: copies a generated caption (title, specs, price) with a link
  - Share: uses the system share sheet if available (mobile Safari/Chrome)
  - Tweet: opens Twitter/X intent with caption and link
  - Facebook: opens Facebook share dialog with the link

The link points to your site’s listing detail using the `#id` route (e.g., `/index.html#boat-007`).

## Columns used
The CSV uses the same headers the site expects:

```text
id,title,category,status,price,price_display,year,make,model,length_ft,hours,engine,hull,color,location,description,primary_image_url,gallery_urls,contact_phone,contact_email,created_at,published,condition,trailer_included,propulsion,beam_ft,draft_ft,fuel_capacity,seating_capacity,features,history,maintenance_notes
```

Notes:
- Only fields you provide are filled; others remain empty.
- `created_at` is auto-filled on add if missing.
- Import expects a header row matching the list above (case-insensitive compare is OK).

## Going live later
When you’re ready to push changes directly to Google:
- Keep this CSV flow, or
- Re-enable the Apps Script section later to write via a web app.

For now, this keeps the workflow simple and offline-friendly.
