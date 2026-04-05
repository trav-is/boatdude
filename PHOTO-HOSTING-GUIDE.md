# 📸 Boat Dude Photo Hosting Guide

## Directory Structure

```
photos/
├── boats/
│   ├── boat-001/
│   │   ├── primary/
│   │   │   └── boat-001-main.jpg
│   │   ├── gallery/
│   │   │   ├── boat-001-01.jpg
│   │   │   ├── boat-001-02.jpg
│   │   │   └── boat-001-03.jpg
│   │   └── thumbnails/
│   │       ├── boat-001-01-thumb.jpg
│   │       ├── boat-001-02-thumb.jpg
│   │       └── boat-001-03-thumb.jpg
│   ├── boat-002/
│   │   ├── primary/
│   │   ├── gallery/
│   │   └── thumbnails/
│   └── boat-003/
│       ├── primary/
│       ├── gallery/
│       └── thumbnails/
├── pwcs/
│   ├── pwc-001/
│   │   ├── primary/
│   │   ├── gallery/
│   │   └── thumbnails/
│   └── pwc-002/
└── assets/
    ├── placeholders/
    └── logos/
```

## 📏 Image Size Guidelines

### **Primary Images (Main Listing Photo)**
- **Resolution**: 1200x800px (3:2 aspect ratio)
- **File Size**: 200-400KB
- **Format**: JPEG (optimized)
- **Quality**: 85-90%

### **Gallery Images**
- **Resolution**: 1920x1280px (3:2 aspect ratio)
- **File Size**: 300-600KB
- **Format**: JPEG (optimized)
- **Quality**: 85-90%

### **Thumbnails**
- **Resolution**: 300x200px (3:2 aspect ratio)
- **File Size**: 20-50KB
- **Format**: JPEG (optimized)
- **Quality**: 80%

## 🎯 Naming Convention

### **File Naming Pattern**
```
{boat-id}-{photo-number}-{type}.jpg
```

### **Examples**
```
boat-001-main.jpg          # Primary image
boat-001-01.jpg           # Gallery image 1
boat-001-02.jpg           # Gallery image 2
boat-001-01-thumb.jpg     # Thumbnail for gallery image 1
boat-001-02-thumb.jpg     # Thumbnail for gallery image 2
```

## 📁 Directory Organization

### **Primary Folder**
- Contains the main listing photo
- Used for card thumbnails and lightbox
- Should be the best representative image

### **Gallery Folder**
- Contains all additional photos
- Numbered sequentially (01, 02, 03...)
- Used for detail page gallery

### **Thumbnails Folder**
- Contains smaller versions of gallery images
- Used for thumbnail navigation
- Automatically generated from gallery images

## 🛠️ Image Processing Workflow

### **1. Original Photos**
- Keep high-resolution originals (3000x2000px+)
- Store in a separate `originals/` folder
- Use for future reprocessing if needed

### **2. Processing Steps**
1. **Resize** to target dimensions
2. **Optimize** for web (compress)
3. **Generate thumbnails** automatically
4. **Rename** according to convention
5. **Upload** to appropriate folders

### **3. Recommended Tools**
- **Photoshop**: Batch processing with actions
- **GIMP**: Free alternative with batch processing
- **ImageMagick**: Command-line automation
- **TinyPNG**: Online compression
- **Squoosh**: Google's image optimization tool

## 🌐 URL Structure

### **Base URL Examples**
```
https://yoursite.com/photos/boats/boat-001/primary/boat-001-main.jpg
https://yoursite.com/photos/boats/boat-001/gallery/boat-001-01.jpg
https://yoursite.com/photos/boats/boat-001/thumbnails/boat-001-01-thumb.jpg
```

### **CDN Integration**
If using a CDN (Cloudflare, AWS CloudFront):
```
https://cdn.yoursite.com/photos/boats/boat-001/primary/boat-001-main.jpg
```

## 📊 Google Sheets Integration

### **Photo Gallery Sheet Columns**
Update your Photo Gallery sheet to use the new URLs:

| Column | Example Value |
|--------|---------------|
| `boat_id` | boat-001 |
| `photo_id` | boat-001-01 |
| `photo_url` | https://yoursite.com/photos/boats/boat-001/gallery/boat-001-01.jpg |
| `photo_alt` | 2021 MasterCraft X24 - Interior view |
| `photo_order` | 1 |
| `is_primary` | false |
| `photo_type` | interior |
| `photo_notes` | Interior view with seating |

## 🚀 Performance Optimization

### **Lazy Loading**
- Images load only when needed
- Reduces initial page load time
- Better mobile experience

### **Responsive Images**
- Different sizes for different screen sizes
- Mobile-optimized versions
- Retina display support

### **Caching**
- Set proper cache headers
- Use CDN for global delivery
- Compress images appropriately

## 📱 Mobile Considerations

### **Mobile-Specific Sizes**
- **Mobile Primary**: 800x533px
- **Mobile Gallery**: 1200x800px
- **Mobile Thumbnails**: 150x100px

### **Progressive Loading**
- Show low-quality placeholder first
- Load high-quality version progressively
- Smooth user experience

## 🔧 Implementation Script

### **Automated Thumbnail Generation**
```bash
#!/bin/bash
# Generate thumbnails for all gallery images
for file in gallery/*.jpg; do
    filename=$(basename "$file" .jpg)
    convert "$file" -resize 300x200^ -gravity center -extent 300x200 "thumbnails/${filename}-thumb.jpg"
done
```

### **Batch Image Optimization**
```bash
#!/bin/bash
# Optimize all images for web
for file in *.jpg; do
    convert "$file" -quality 85 -strip "$file"
done
```

## 📋 Checklist for New Boat Photos

- [ ] Take high-quality photos (3000x2000px+)
- [ ] Choose best photo for primary image
- [ ] Process all images to correct sizes
- [ ] Generate thumbnails
- [ ] Rename files according to convention
- [ ] Upload to correct directories
- [ ] Update Google Sheets with new URLs
- [ ] Test on website
- [ ] Verify mobile display

## 🎯 Benefits of Self-Hosting

✅ **Full Control** - No dependency on external services
✅ **Better Performance** - Optimized for your needs
✅ **Cost Effective** - No third-party fees
✅ **Reliability** - No external service downtime
✅ **Customization** - Full control over image processing
✅ **SEO Benefits** - Images hosted on your domain

## 🚨 Important Notes

- **Always keep originals** - You may need to reprocess
- **Test on mobile** - Ensure images look good on small screens
- **Monitor file sizes** - Keep pages loading fast
- **Use HTTPS** - Secure image delivery
- **Backup regularly** - Don't lose your photos!

---

**Need help setting this up?** I can help you create the directory structure and processing scripts!
