#!/usr/bin/env python3
"""
Flask API server for The Boat Dude admin interface
Handles communication between admin interface and Google Sheets
"""

from flask import Flask, request, jsonify
from flask import make_response
from flask_cors import CORS
import json
import logging
import os
from typing import List, Dict, Any
from xml.etree.ElementTree import Element, SubElement, tostring
from xml.dom import minidom
from sheets_service import create_sheets_service, BOATS_SHEET_ID, PHOTOS_SHEET_ID
from importers.onlyinboards import parse_onlyinboards_listing

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)

# Configure CORS for the admin interface - use permissive for development
CORS(app, 
     origins=['http://localhost:8000', 'http://127.0.0.1:8000'],
     methods=['GET', 'POST', 'PUT', 'DELETE', 'OPTIONS'],
     allow_headers=['Content-Type', 'Authorization', 'Origin', 'Accept'],
     supports_credentials=False)

# Initialize sheets service
try:
    sheets_service = create_sheets_service()
    logger.info("Google Sheets service initialized successfully")
except Exception as e:
    logger.exception(f"Failed to initialize Google Sheets service: {e}")
    sheets_service = None

def _parse_city_state_zip(location_value: str) -> Dict[str, str]:
    """
    Parse a freeform location string into city, state, and zip.
    Returns empty strings for anything that can't be parsed.
    """
    if not location_value:
        return {'city': '', 'state': '', 'zip': ''}
    value = str(location_value).strip()
    # Try to split "City, ST" or "City ST"
    if ',' in value:
        parts = [p.strip() for p in value.split(',', 1)]
        city = parts[0]
        remainder = parts[1]
    else:
        # Assume last token is state code if two letters
        tokens = value.split()
        if len(tokens) >= 2 and len(tokens[-1]) in (2, 3):
            city = ' '.join(tokens[:-1])
            remainder = tokens[-1]
        else:
            return {'city': value, 'state': '', 'zip': ''}
    # Extract state and optional zip from remainder
    remainder_tokens = remainder.split()
    state = remainder_tokens[0] if remainder_tokens else ''
    zip_code = ''
    if len(remainder_tokens) >= 2 and remainder_tokens[1].isdigit():
        zip_code = remainder_tokens[1]
    return {'city': city, 'state': state, 'zip': zip_code}

def _coerce_int_string(value: Any) -> str:
    try:
        if value is None or value == '':
            return ''
        # Handle strings like "22.5"
        num = float(str(value).replace(',', '').strip())
        if num.is_integer():
            return str(int(num))
        return str(int(round(num)))
    except Exception:
        return ''

def _is_truthy(value: Any) -> bool:
    if value is None:
        return False
    s = str(value).strip().lower()
    return s in ('y', 'yes', 'true', '1')

def _build_pontoonsonly_xml(boats: List[Dict[str, Any]], photos: List[Dict[str, Any]]) -> str:
    """
    Build Pontoonsonly XML feed from boats and photos data.
    """
    # Index photos by boat_id and order them with primary first, then by photo_order, then by url
    photos_by_boat: Dict[str, List[Dict[str, Any]]] = {}
    for p in photos or []:
        boat_id = str(p.get('boat_id', '')).strip()
        if not boat_id:
            continue
        photos_by_boat.setdefault(boat_id, []).append(p)
    for boat_id, plist in photos_by_boat.items():
        def sort_key(item: Dict[str, Any]):
            is_primary = str(item.get('is_primary', '')).strip().lower() in ('true', '1', 'y', 'yes')
            raw_order = item.get('photo_order', '')
            try:
                order_val = int(str(raw_order).strip())
            except Exception:
                order_val = 9999
            return (0 if is_primary else 1, order_val, str(item.get('photo_url', '')))
        plist.sort(key=sort_key)

    root = Element('inventory')

    for boat in boats or []:
        # Only include published and available units
        if not _is_truthy(boat.get('published', 'Y')):
            continue
        status = str(boat.get('status', '')).strip().lower()
        if status and status not in ('available', 'for sale', 'active'):
            continue

        listing = SubElement(root, 'listing')

        # Stock number
        SubElement(listing, 'stocknumber').text = str(boat.get('id', '') or '')
        # Category
        SubElement(listing, 'category').text = str(boat.get('category', '') or '')
        # Title
        SubElement(listing, 'title').text = str(boat.get('title', '') or '')
        # Description
        SubElement(listing, 'description').text = str(boat.get('description', '') or '')
        # Sale price
        SubElement(listing, 'saleprice').text = _coerce_int_string(boat.get('price', ''))

        # Location parsing
        loc = _parse_city_state_zip(boat.get('location', ''))
        SubElement(listing, 'zip').text = loc['zip']
        SubElement(listing, 'city').text = loc['city']
        SubElement(listing, 'state').text = loc['state']

        # Make, year, length, horsepower (unknown -> blank)
        SubElement(listing, 'make').text = str(boat.get('make', '') or '')
        SubElement(listing, 'year').text = _coerce_int_string(boat.get('year', ''))
        SubElement(listing, 'length').text = _coerce_int_string(boat.get('length_ft', ''))
        SubElement(listing, 'horsepower').text = ''

        # Photos (up to 14)
        ordered_urls: List[str] = []
        # Prefer photos sheet; if empty, try inline fields that might exist
        boat_photos = photos_by_boat.get(str(boat.get('id', '')).strip(), [])
        if boat_photos:
            for p in boat_photos:
                url = str(p.get('photo_url', '')).strip()
                if url:
                    ordered_urls.append(url)
        else:
            # Fallbacks if photos sheet isn't populated
            primary = str(boat.get('primary_image', '') or boat.get('primary_image_url', '')).strip()
            if primary:
                ordered_urls.append(primary)
            gallery_val = boat.get('gallery') or boat.get('gallery_urls')
            if isinstance(gallery_val, list):
                ordered_urls.extend([str(u).strip() for u in gallery_val if u])
            elif isinstance(gallery_val, str):
                for u in gallery_val.split(','):
                    u = u.strip()
                    if u:
                        ordered_urls.append(u)

        for idx, url in enumerate(ordered_urls[:14], start=1):
            SubElement(listing, f'photo{idx}').text = url

    # Pretty print
    rough_string = tostring(root, encoding='utf-8')
    reparsed = minidom.parseString(rough_string)
    return reparsed.toprettyxml(indent="  ", encoding='UTF-8').decode('utf-8')

def _load_local_boats() -> List[Dict[str, Any]]:
    """
    Load boats from local files for development fallback.
    Prefers data/boats.json, falls back to data/boats-clean.csv.
    """
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    json_path = os.path.join(project_root, 'data', 'boats.json')
    csv_path = os.path.join(project_root, 'data', 'boats-clean.csv')
    try:
        if os.path.exists(json_path):
            with open(json_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                if isinstance(data, list):
                    return data
        if os.path.exists(csv_path):
            import csv
            with open(csv_path, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                return list(reader)
    except Exception as e:
        logger.warning(f"Local boats load failed: {e}")
    return []

@app.route('/feeds/pontoonsonly.xml', methods=['GET'])
def get_pontoonsonly_feed():
    """Generate Pontoonsonly XML feed from Google Sheets and return it"""
    try:
        boats: List[Dict[str, Any]] = []
        photos: List[Dict[str, Any]] = []

        if sheets_service:
            try:
                boats = sheets_service.get_boats_data(BOATS_SHEET_ID)
                photos = sheets_service.get_photos_data(PHOTOS_SHEET_ID)
            except Exception as e:
                logger.warning(f"Sheets fetch failed, falling back to local data: {e}")
        else:
            logger.warning("Sheets service unavailable, using local data fallback")

        # Fallback to local data if no boats from Sheets
        if not boats:
            boats = _load_local_boats()
            photos = []  # builder will use primary_image/gallery fields if present

        xml_string = _build_pontoonsonly_xml(boats, photos)

        # Also write to data/pontoonsonlyfeed.xml for convenience
        project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        out_path = os.path.join(project_root, 'data', 'pontoonsonlyfeed.xml')
        try:
            with open(out_path, 'w', encoding='utf-8') as f:
                f.write(xml_string)
            logger.info(f"Wrote Pontoonsonly feed to {out_path}")
        except Exception as e:
            logger.warning(f"Could not write feed file: {e}")

        response = make_response(xml_string, 200)
        response.headers['Content-Type'] = 'application/xml; charset=utf-8'
        return response
    except Exception as e:
        logger.exception(f"Failed to generate Pontoonsonly feed: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/import/onlyinboards', methods=['POST'])
def import_onlyinboards():
    """
    Import a single OnlyInboards listing URL into the live inventory Google Sheet.
    Body: { "url": "https://onlyinboards.com/listings/...." }
    """
    if not sheets_service:
        return jsonify({'error': 'Google Sheets service not available'}), 500
    try:
        data = request.get_json(silent=True) or {}
        url = (data.get('url') or '').strip()
        if not url:
            return jsonify({'error': 'Missing url'}), 400

        # Parse listing
        record = parse_onlyinboards_listing(url)
        boat = record.to_sheet_dict()

        # Merge into existing sheet by id (rewrite full sheet using existing push)
        existing = sheets_service.get_boats_data(BOATS_SHEET_ID)
        # Normalize headers used in sheets to ensure all keys exist
        merged = [row for row in existing if str(row.get('id', '')).strip() != boat['id']]
        merged.append(boat)

        ok = sheets_service.push_boats_data(merged, BOATS_SHEET_ID)
        if not ok:
            return jsonify({'error': 'Failed to write to Google Sheet'}), 500

        return jsonify({'message': 'Imported OnlyInboards listing', 'id': boat['id'], 'title': boat['title']}), 200
    except Exception as e:
        logger.exception(f"Failed to import OnlyInboards listing: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/health', methods=['GET', 'OPTIONS'])
def health_check():
    """Health check endpoint"""
    if request.method == 'OPTIONS':
        return '', 200
    return jsonify({
        'status': 'healthy',
        'sheets_connected': sheets_service is not None
    })

@app.route('/api/boats', methods=['GET', 'OPTIONS'])
def get_boats():
    """Get all boats from Google Sheets"""
    if request.method == 'OPTIONS':
        return '', 200
    if not sheets_service:
        return jsonify({'error': 'Google Sheets service not available'}), 500
    
    try:
        boats = sheets_service.get_boats_data(BOATS_SHEET_ID)
        return jsonify({'boats': boats})
    except Exception as e:
        logger.exception(f"Failed to get boats: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/boats', methods=['POST', 'OPTIONS'])
def push_boats():
    """Push boats data to Google Sheets"""
    if request.method == 'OPTIONS':
        return '', 200
    if not sheets_service:
        return jsonify({'error': 'Google Sheets service not available'}), 500
    
    try:
        data = request.get_json()
        boats = data.get('boats', [])
        
        if not boats:
            return jsonify({'error': 'No boats data provided'}), 400
        
        success = sheets_service.push_boats_data(boats, BOATS_SHEET_ID)
        
        if success:
            return jsonify({'message': f'Successfully pushed {len(boats)} boats to Google Sheets'})
        else:
            return jsonify({'error': 'Failed to push boats data'}), 500
            
    except Exception as e:
        logger.exception(f"Failed to push boats: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/photos', methods=['GET'])
def get_photos():
    """Get all photos from Google Sheets"""
    if not sheets_service:
        return jsonify({'error': 'Google Sheets service not available'}), 500
    
    try:
        photos = sheets_service.get_photos_data(PHOTOS_SHEET_ID)
        return jsonify({'photos': photos})
    except Exception as e:
        logger.exception(f"Failed to get photos: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/photos', methods=['POST'])
def push_photos():
    """Push photos data to Google Sheets"""
    if not sheets_service:
        return jsonify({'error': 'Google Sheets service not available'}), 500
    
    try:
        data = request.get_json()
        photos = data.get('photos', [])
        
        if not photos:
            return jsonify({'error': 'No photos data provided'}), 400
        
        success = sheets_service.push_photos_data(photos, PHOTOS_SHEET_ID)
        
        if success:
            return jsonify({'message': f'Successfully pushed {len(photos)} photos to Google Sheets'})
        else:
            return jsonify({'error': 'Failed to push photos data'}), 500
            
    except Exception as e:
        logger.exception(f"Failed to push photos: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/sync', methods=['POST'])
def sync_all():
    """Sync all data (boats and photos) to Google Sheets"""
    if not sheets_service:
        return jsonify({'error': 'Google Sheets service not available'}), 500
    
    try:
        data = request.get_json()
        boats = data.get('boats', [])
        photos = data.get('photos', [])
        
        results = {}
        
        # Push boats if provided
        if boats:
            boats_success = sheets_service.push_boats_data(boats, BOATS_SHEET_ID)
            results['boats'] = {
                'success': boats_success,
                'count': len(boats),
                'message': f'{"Successfully" if boats_success else "Failed to"} push {len(boats)} boats'
            }
        
        # Push photos if provided
        if photos:
            photos_success = sheets_service.push_photos_data(photos, PHOTOS_SHEET_ID)
            results['photos'] = {
                'success': photos_success,
                'count': len(photos),
                'message': f'{"Successfully" if photos_success else "Failed to"} push {len(photos)} photos'
            }
        
        # Check if all operations were successful
        all_success = all(result['success'] for result in results.values())
        
        return jsonify({
            'success': all_success,
            'results': results,
            'message': 'Sync completed' if all_success else 'Sync completed with errors'
        })
        
    except Exception as e:
        logger.exception(f"Failed to sync data: {e}")
        return jsonify({'error': str(e)}), 500

@app.errorhandler(404)
def not_found(error):
    return jsonify({'error': 'Endpoint not found'}), 404

@app.errorhandler(500)
def internal_error(error):
    return jsonify({'error': 'Internal server error'}), 500

if __name__ == '__main__':
    # Run the Flask app on port 5001 to avoid AirTunes conflict
    app.run(host='0.0.0.0', port=5001, debug=False)
