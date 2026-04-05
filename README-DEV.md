# The Boat Dude - Development Setup

## Quick Start

### 1. Start the Local Server
```bash
# Start server on default port 8000
./start-server.sh start

# Start server on custom port
./start-server.sh start 3000

# Check server status
./start-server.sh status

# Stop server
./start-server.sh stop
```

### 2. Install Image Optimization Dependencies
```bash
pip3 install -r requirements.txt
```

### 3. Optimize Images
```bash
# Basic optimization (processes photos/ directory)
python3 optimize-images.py

# Custom settings
python3 optimize-images.py --input photos --output photos-optimized --quality 90 --max-width 1600

# Help
python3 optimize-images.py --help
```

## Server Management

The `start-server.sh` script provides easy server management:

- **Start**: `./start-server.sh start [port]`
- **Stop**: `./start-server.sh stop`
- **Restart**: `./start-server.sh restart`
- **Status**: `./start-server.sh status`

The server automatically:
- Serves `index.html` for root requests
- Adds CORS headers for development
- Handles graceful shutdown with Ctrl+C

## Image Optimization

The `optimize-images.py` script provides:

- **Automatic resizing** to max width (default: 1200px)
- **Quality compression** (default: 85%)
- **Thumbnail generation** (300x200 and 150x100)
- **Format conversion** to JPEG
- **EXIF orientation** handling
- **Detailed reporting** with before/after stats

### Features:
- Preserves aspect ratios
- Creates white backgrounds for transparent images
- Generates multiple thumbnail sizes
- Skips already processed files
- Recursive directory processing
- JSON report generation

### Example Output:
```
🚤 The Boat Dude - Image Optimizer
========================================
🔍 Found 15 image files
📁 Processing: photos
📁 Output: photos-optimized
⚙️  Quality: 85%, Max width: 1200px

[  1/ 15] Processing: boats/boat-001/primary/image1.jpg
    ✅ 2,450,123 → 1,234,567 bytes (49.6% saved)
[  2/ 15] Processing: boats/boat-001/gallery/image2.png
    ✅ 3,200,000 → 1,800,000 bytes (43.8% saved)
```

## Development Workflow

1. **Start server**: `./start-server.sh start`
2. **Open browser**: http://localhost:8000 *(data loads directly from the published Google Sheets CSV, no local API required for read-only testing)*
3. **Add/edit images**: Place in `photos/` directory
4. **Optimize images**: `python3 optimize-images.py`
5. **Update data**: Edit Google Sheets or `data/boats.json`
6. **Test changes**: Refresh browser

## Photo Gallery Manifest

- Local photos live under `photos-optimized/boat-id/filename.jpg`.  
- The gallery order/primary image is controlled by `data/photo-manifest.json`.  
- Use the new **Photo Galleries** panel in `admin/index.html` to load a boat, reorder images, pick a primary photo, then download the updated JSON.  
- Replace `data/photo-manifest.json` with your downloaded file (commit or upload it alongside the photos) to keep DreamHost in sync.

## File Structure
```
dev/
├── server.py              # Python HTTP server
├── start-server.sh        # Server management script
├── optimize-images.py     # Image optimization tool
├── requirements.txt       # Python dependencies
├── index.html            # Main site
├── app.js                # Site functionality
├── styles.css            # Site styling
├── photos/               # Original images
├── photos-optimized/     # Optimized images (generated)
└── data/                 # Boat data (JSON/CSV)
```

## Tips

- The server runs in the background - use the management script to control it
- Image optimization preserves your original files
- Thumbnails are automatically generated in `thumbnails/` subdirectories
- Check the JSON report for detailed optimization stats
- Use `--no-thumbnails` flag if you don't need thumbnail generation

## Pontoonsonly XML Feed

- Endpoint: `http://localhost:5001/feeds/pontoonsonly.xml`
- Source: Reads boats and photos from Google Sheets (uses your configured credentials)
- Output: Returns XML and also writes to `data/pontoonsonlyfeed.xml`
- Filtering: Only includes rows marked as `published` (Y/TRUE) and with `status` set to available
- Notes:
  - City/State are parsed from the `location` field (e.g., `"Mooresville, NC"`)
  - ZIP and horsepower are left blank if not available
  - Up to 14 photos are included per listing, with primary first and `photo_order` respected
  - If Google Sheets is unavailable, it falls back to local data: `data/boats.json` (preferred) or `data/boats-clean.csv`

