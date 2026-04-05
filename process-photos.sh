#!/bin/bash

# Boat Dude Photo Processing Script
# Requires ImageMagick: brew install imagemagick (on macOS)

# Configuration
BOAT_ID="boat-001"
SOURCE_DIR="originals"
TARGET_DIR="photos/boats/$BOAT_ID"

# Create directories if they don't exist
mkdir -p "$TARGET_DIR/primary"
mkdir -p "$TARGET_DIR/gallery"
mkdir -p "$TARGET_DIR/thumbnails"

echo "Processing photos for $BOAT_ID..."

# Process primary image (first image in originals)
if [ -f "$SOURCE_DIR/primary.jpg" ]; then
    echo "Processing primary image..."
    convert "$SOURCE_DIR/primary.jpg" \
        -resize 1200x800^ \
        -gravity center \
        -extent 1200x800 \
        -quality 85 \
        -strip \
        "$TARGET_DIR/primary/$BOAT_ID-main.jpg"
    
    echo "✓ Primary image processed: $TARGET_DIR/primary/$BOAT_ID-main.jpg"
fi

# Process gallery images
counter=1
for file in "$SOURCE_DIR"/gallery*.jpg; do
    if [ -f "$file" ]; then
        echo "Processing gallery image $counter..."
        
        # Create gallery image
        convert "$file" \
            -resize 1920x1280^ \
            -gravity center \
            -extent 1920x1280 \
            -quality 85 \
            -strip \
            "$TARGET_DIR/gallery/$BOAT_ID-$(printf "%02d" $counter).jpg"
        
        # Create thumbnail
        convert "$file" \
            -resize 300x200^ \
            -gravity center \
            -extent 300x200 \
            -quality 80 \
            -strip \
            "$TARGET_DIR/thumbnails/$BOAT_ID-$(printf "%02d" $counter)-thumb.jpg"
        
        echo "✓ Gallery image $counter processed"
        ((counter++))
    fi
done

echo "Photo processing complete for $BOAT_ID!"
echo ""
echo "Generated files:"
echo "- Primary: $TARGET_DIR/primary/$BOAT_ID-main.jpg"
echo "- Gallery: $TARGET_DIR/gallery/$BOAT_ID-*.jpg"
echo "- Thumbnails: $TARGET_DIR/thumbnails/$BOAT_ID-*-thumb.jpg"
echo ""
echo "Next steps:"
echo "1. Upload photos to your web server"
echo "2. Update Google Sheets with new URLs"
echo "3. Test on your website"
