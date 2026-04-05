# 🚤 Boat Dude - Low-Rent Relational Database Setup

## Overview
Your boat inventory system now uses **two Google Sheets** to create a simple relational database:
1. **Boats Sheet** - Main boat information
2. **Photo Gallery Sheet** - Photo management for each boat

## 📊 Sheet 1: Boats Inventory

### Setup Steps:
1. **Create Google Sheet** called "Boat Dude Inventory"
2. **Import** `boats-enhanced.csv` template
3. **Publish as CSV**:
   - File → Share → Publish to web
   - Choose "Entire document" and "CSV"
   - Copy the URL
4. **Paste URL** in `app.js` line 5: `const SHEET_CSV_URL = "YOUR_URL_HERE";`

### Columns to Edit:
- `id` - Unique identifier (e.g., "boat-001")
- `title` - Display name (e.g., "2021 MasterCraft X24")
- `status` - available/pending/sold
- `price` - Number (e.g., 199900)
- `price_display` - Display format (e.g., "$199,900")
- `description` - Detailed description
- `features` - Comma-separated features
- `history` - Ownership history
- `maintenance_notes` - Service records

## 📸 Sheet 2: Photo Gallery Management

### Setup Steps:
1. **Create Google Sheet** called "Boat Dude Photos"
2. **Import** `photo-gallery-template.csv` template
3. **Publish as CSV**:
   - File → Share → Publish to web
   - Choose "Entire document" and "CSV"
   - Copy the URL
4. **Paste URL** in `app.js` line 6: `const PHOTO_GALLERY_CSV_URL = "YOUR_URL_HERE";`

### Columns Explained:
- `boat_id` - Must match the `id` from Boats sheet
- `photo_id` - Unique photo identifier (e.g., "boat-001-01")
- `photo_url` - Direct image URL
- `photo_alt` - Alt text for accessibility
- `photo_order` - Display order (1, 2, 3...)
- `is_primary` - true/false (which photo shows first)
- `photo_type` - exterior/interior/engine/etc.
- `photo_notes` - Description of the photo

## 🔗 URL Sharing

Each boat now has its own shareable URL:
- `yoursite.com#boat-001` - Direct link to specific boat
- Perfect for sharing individual listings
- Works with social media and email

## 📱 Boomer-Friendly Workflow

### Adding a New Boat:
1. **Add row** to Boats sheet with all details
2. **Add rows** to Photos sheet for each photo
3. **Set photo_order** (1, 2, 3...)
4. **Set is_primary** to "true" for main photo
5. **Save both sheets** - website updates automatically!

### Managing Photos:
1. **Upload photos** to Google Drive
2. **Get shareable links** (convert to direct image links)
3. **Add photo rows** with boat_id matching the boat
4. **Reorder photos** by changing photo_order numbers
5. **Change primary photo** by setting is_primary to "true"

### Updating Boat Status:
1. **Change status** from "available" to "pending" to "sold"
2. **Update price** if needed
3. **Add maintenance notes** for service records
4. **Save sheet** - changes appear immediately

## 🎯 Pro Tips

### Photo Management:
- Use Google Drive for photo storage
- Convert shareable links to direct image links
- Name photos descriptively (e.g., "boat-001-main.jpg")
- Keep photo_order sequential (1, 2, 3...)

### Boat IDs:
- Use consistent format: "boat-001", "boat-002", etc.
- Must match exactly between both sheets
- No spaces or special characters

### Status Updates:
- "available" - Green badge, shows in listings
- "pending" - Yellow badge, shows in listings
- "sold" - Gray badge, shows in listings

## 🚀 Benefits

✅ **Easy photo management** - No more comma-separated URLs
✅ **Shareable links** - Each boat has its own URL
✅ **Professional detail pages** - Comprehensive boat information
✅ **Boomer-friendly** - Just edit spreadsheets
✅ **Real-time updates** - Changes appear immediately
✅ **Mobile-friendly** - Works on phones and tablets

## 🔧 Troubleshooting

### Photos not showing?
- Check that `boat_id` matches exactly in both sheets
- Verify photo URLs are direct image links (not Google Drive share links)
- Make sure `photo_order` numbers are sequential

### Boat not appearing?
- Check that `id` field is filled in Boats sheet
- Verify CSV URLs are correct in `app.js`
- Make sure sheets are published as CSV

### URL not working?
- Check that boat `id` exists in the Boats sheet
- Verify the URL format: `yoursite.com#boat-001`
- Make sure the boat is not marked as "sold" if you want it visible

---

**Need help?** The system is designed to be simple, but if you get stuck, just ask!
