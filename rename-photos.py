#!/usr/bin/env python3
"""
Rename processed photos to clean naming convention
boat-001-001.jpg, boat-001-002.jpg, etc.
"""

import os
import shutil
from pathlib import Path

def rename_photos(directory="photos-optimized/boats/boat-001/gallery"):
    """Rename photos to clean naming convention"""
    
    gallery_dir = Path(directory)
    if not gallery_dir.exists():
        print(f"❌ Directory not found: {directory}")
        return
    
    # Get all jpg files
    jpg_files = list(gallery_dir.glob("*.jpg"))
    jpg_files.sort()  # Sort alphabetically for consistent ordering
    
    print(f"🚤 Renaming {len(jpg_files)} photos in {directory}")
    print("=" * 50)
    
    # Create backup directory
    backup_dir = gallery_dir / "original_names"
    backup_dir.mkdir(exist_ok=True)
    
    # Rename files
    for i, old_file in enumerate(jpg_files, 1):
        new_name = f"boat-001-{i:03d}.jpg"
        new_path = gallery_dir / new_name
        
        # Skip if already renamed
        if old_file.name.startswith("boat-001-"):
            print(f"⏭️  Skipping {old_file.name} (already renamed)")
            continue
        
        # Backup original name
        backup_path = backup_dir / old_file.name
        shutil.copy2(old_file, backup_path)
        
        # Rename file
        old_file.rename(new_path)
        print(f"✅ {old_file.name} → {new_name}")
    
    # Also rename thumbnails
    thumbnails_dir = gallery_dir / "thumbnails"
    if thumbnails_dir.exists():
        print(f"\n🖼️  Renaming thumbnails...")
        rename_thumbnails(thumbnails_dir, backup_dir)
    
    print(f"\n✅ Renaming complete!")
    print(f"📁 Original names backed up to: {backup_dir}")
    print(f"📊 Renamed {len(jpg_files)} photos")

def rename_thumbnails(thumbnails_dir, backup_dir):
    """Rename thumbnail files to match new naming"""
    
    # Create thumbnails backup
    thumb_backup = backup_dir / "thumbnails"
    thumb_backup.mkdir(exist_ok=True)
    
    # Get all thumbnail files
    thumb_files = list(thumbnails_dir.glob("*.jpg"))
    thumb_files.sort()
    
    for i, old_thumb in enumerate(thumb_files, 1):
        # Determine thumbnail type from filename
        if "_medium" in old_thumb.name:
            new_name = f"boat-001-{i:03d}_medium.jpg"
        elif "_small" in old_thumb.name:
            new_name = f"boat-001-{i:03d}_small.jpg"
        else:
            continue  # Skip if not a recognized thumbnail
        
        new_path = thumbnails_dir / new_name
        
        # Skip if already renamed
        if old_thumb.name.startswith("boat-001-"):
            continue
        
        # Backup original
        backup_path = thumb_backup / old_thumb.name
        shutil.copy2(old_thumb, backup_path)
        
        # Rename
        old_thumb.rename(new_path)
        print(f"  ✅ {old_thumb.name} → {new_name}")

if __name__ == "__main__":
    import sys
    
    # Allow custom directory
    directory = sys.argv[1] if len(sys.argv) > 1 else "photos-optimized/boats/boat-001/gallery"
    
    print("🚤 The Boat Dude - Photo Renamer")
    print("=" * 40)
    
    rename_photos(directory)

