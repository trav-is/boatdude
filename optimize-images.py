#!/usr/bin/env python3
"""
The Boat Dude - Simple Image Optimizer
Just optimizes images and puts them in the right place for the web app
"""

import os
import sys
import argparse
from pathlib import Path
from PIL import Image, ImageOps
import json

class SimpleImageOptimizer:
    def __init__(self, input_dir, output_dir, quality=85, max_width=1200):
        self.input_dir = Path(input_dir)
        self.output_dir = Path(output_dir)
        self.quality = quality
        self.max_width = max_width
        self.stats = {
            'processed': 0,
            'errors': 0,
            'total_original_size': 0,
            'total_optimized_size': 0
        }

    def optimize_image(self, input_path, output_path):
        """Optimize a single image"""
        try:
            with Image.open(input_path) as img:
                # Convert to RGB if necessary
                if img.mode in ('RGBA', 'LA', 'P'):
                    background = Image.new('RGB', img.size, (255, 255, 255))
                    if img.mode == 'P':
                        img = img.convert('RGBA')
                    background.paste(img, mask=img.split()[-1] if img.mode == 'RGBA' else None)
                    img = background
                elif img.mode != 'RGB':
                    img = img.convert('RGB')
                
                # Resize if too large
                if img.width > self.max_width:
                    ratio = self.max_width / img.width
                    new_height = int(img.height * ratio)
                    img = img.resize((self.max_width, new_height), Image.Resampling.LANCZOS)
                
                # Auto-orient based on EXIF data
                img = ImageOps.exif_transpose(img)
                
                # Save optimized image
                img.save(output_path, 'JPEG', quality=self.quality, optimize=True)
                return True
                
        except Exception as e:
            print(f"❌ Error optimizing {input_path}: {e}")
            return False

    def get_image_info(self, image_path):
        """Get image file info"""
        try:
            with Image.open(image_path) as img:
                return {
                    'width': img.width,
                    'height': img.height,
                    'file_size': image_path.stat().st_size
                }
        except Exception as e:
            return {'error': str(e)}

    def process_directory(self):
        """Process all images in the input directory (optimize in place)"""
        # Find all image files
        image_extensions = {'.jpg', '.jpeg', '.png', '.webp', '.bmp', '.tiff', '.tif'}
        image_files = []
        for ext in image_extensions:
            image_files.extend(self.input_dir.rglob(f'*{ext}'))
            image_files.extend(self.input_dir.rglob(f'*{ext.upper()}'))
        
        if not image_files:
            print("❌ No image files found")
            return
        
        print(f"🔍 Found {len(image_files)} image files")
        print(f"📁 Processing: {self.input_dir}")
        print(f"⚙️  Quality: {self.quality}%, Max width: {self.max_width}px")
        print("🔄 Optimizing in place with clean naming...")
        print()
        
        # Group images by boat/PWC folder
        boat_groups = {}
        for image_path in image_files:
            # Find boat folder (e.g., boat-001, pwc-002)
            parts = image_path.parts
            boat_folder = None
            for part in parts:
                if part.startswith(('boat-', 'pwc-')) and part.count('-') >= 1:
                    boat_folder = part
                    break
            
            if boat_folder:
                if boat_folder not in boat_groups:
                    boat_groups[boat_folder] = []
                boat_groups[boat_folder].append(image_path)
        
        # Process each boat group
        for boat_folder, images in boat_groups.items():
            print(f"🚤 Processing {boat_folder} ({len(images)} images)")
            
            # Sort images for consistent ordering
            images.sort()
            
            for i, image_path in enumerate(images, 1):
                # Generate clean filename: boat-001-001.jpg, boat-001-002.jpg, etc.
                padded_index = str(i).zfill(3)
                clean_filename = f"{boat_folder}-{padded_index}.jpg"
                output_path = image_path.parent / clean_filename
                
                # Skip if already optimized and newer
                if output_path.exists() and output_path.stat().st_mtime > image_path.stat().st_mtime:
                    print(f"    ⏭️  Skipped {clean_filename} (already optimized)")
                    continue
                
                # Get original size
                original_info = self.get_image_info(image_path)
                if 'error' in original_info:
                    print(f"    ❌ Error reading {image_path.name}: {original_info['error']}")
                    self.stats['errors'] += 1
                    continue
                
                # Optimize image
                if self.optimize_image(image_path, output_path):
                    # Get optimized size
                    optimized_info = self.get_image_info(output_path)
                    if 'error' not in optimized_info:
                        original_size = original_info['file_size']
                        optimized_size = optimized_info['file_size']
                        savings = original_size - optimized_size
                        savings_pct = (savings / original_size * 100) if original_size > 0 else 0
                        
                        print(f"    ✅ {original_size:,} → {optimized_size:,} bytes ({savings_pct:.1f}% saved) → {clean_filename}")
                        
                        self.stats['processed'] += 1
                        self.stats['total_original_size'] += original_size
                        self.stats['total_optimized_size'] += optimized_size
                        
                        # Remove original file if it's different from the optimized one
                        if image_path != output_path:
                            try:
                                image_path.unlink()
                                print(f"    🗑️  Removed original: {image_path.name}")
                            except:
                                print(f"    ⚠️  Could not remove original: {image_path.name}")
                    else:
                        print(f"    ❌ Error with optimized image")
                        self.stats['errors'] += 1
                else:
                    self.stats['errors'] += 1

    def generate_report(self):
        """Generate optimization report"""
        if self.stats['processed'] == 0:
            print("❌ No files were processed")
            return
        
        total_savings = self.stats['total_original_size'] - self.stats['total_optimized_size']
        savings_pct = (total_savings / self.stats['total_original_size'] * 100) if self.stats['total_original_size'] > 0 else 0
        
        print("\n" + "="*60)
        print("📊 OPTIMIZATION REPORT")
        print("="*60)
        print(f"✅ Files processed: {self.stats['processed']}")
        print(f"❌ Errors: {self.stats['errors']}")
        print(f"📦 Original size: {self.stats['total_original_size']:,} bytes ({self.stats['total_original_size']/1024/1024:.1f} MB)")
        print(f"📦 Optimized size: {self.stats['total_optimized_size']:,} bytes ({self.stats['total_optimized_size']/1024/1024:.1f} MB)")
        print(f"💾 Space saved: {total_savings:,} bytes ({total_savings/1024/1024:.1f} MB)")
        print(f"📈 Compression: {savings_pct:.1f}%")

def main():
    parser = argparse.ArgumentParser(description='Simple image optimizer for The Boat Dude')
    parser.add_argument('--input', '-i', default='photos-optimized', help='Input directory (default: photos-optimized)')
    parser.add_argument('--quality', '-q', type=int, default=85, help='JPEG quality 1-100 (default: 85)')
    parser.add_argument('--max-width', '-w', type=int, default=1200, help='Maximum width in pixels (default: 1200)')
    
    args = parser.parse_args()
    
    # Validate input directory
    input_path = Path(args.input)
    if not input_path.exists():
        print(f"❌ Input directory not found: {input_path}")
        print(f"💡 Create the directory and drop your raw photos in boat folders (e.g., boat-001/, boat-002/)")
        sys.exit(1)
    
    # Create optimizer (optimizes in place)
    optimizer = SimpleImageOptimizer(
        input_dir=args.input,
        output_dir=args.input,  # Same directory - optimize in place
        quality=args.quality,
        max_width=args.max_width
    )
    
    # Process images
    optimizer.process_directory()
    
    # Generate report
    optimizer.generate_report()

if __name__ == "__main__":
    main()
