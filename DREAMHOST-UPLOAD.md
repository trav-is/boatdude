# DreamHost Upload Guide

## Files to Upload to DreamHost

Upload these files to your DreamHost web directory (usually `public_html` or your domain folder):

### ✅ Required Files
```
index.html
app.js
styles.css
assets/
├── logo/
│   └── the_boat_dude_1.PNG
└── logo.svg
data/
├── boats.json
└── boats-template.csv
photos/
├── boats/
│   ├── boat-001/
│   ├── boat-002/
│   └── boat-003/
└── pwcs/
    ├── pwc-001/
    └── pwc-002/
```

### ❌ Do NOT Upload (Development Only)
```
server.py
start-server.sh
optimize-images.py
requirements.txt
README-DEV.md
DREAMHOST-UPLOAD.md
.scratch.txt
```

## Upload Steps

1. **Connect to DreamHost** via FTP/SFTP or File Manager
2. **Navigate** to your domain's web directory
3. **Upload** all the required files maintaining the folder structure
4. **Set permissions** (if needed):
   - HTML/CSS/JS files: 644
   - Images: 644
   - Directories: 755

## After Upload

1. **Test the site** by visiting your domain
2. **Check images** load properly
3. **Verify** Google Sheets integration works (if using)
4. **Test** all functionality (search, filters, lightbox, etc.)

## File Structure on DreamHost
```
your-domain.com/
├── index.html
├── app.js
├── styles.css
├── assets/
│   ├── logo/
│   │   └── the_boat_dude_1.PNG
│   └── logo.svg
├── data/
│   ├── boats.json
│   └── boats-template.csv
└── photos/
    ├── boats/
    │   ├── boat-001/
    │   │   ├── gallery/
    │   │   ├── primary/
    │   │   └── thumbnails/
    │   ├── boat-002/
    │   └── boat-003/
    └── pwcs/
        ├── pwc-001/
        └── pwc-002/
```

## Notes

- The site is **completely static** - no server-side processing needed
- **Google Sheets integration** works from any web host
- **All images** should be optimized before upload for best performance
- **No database** or server configuration required

