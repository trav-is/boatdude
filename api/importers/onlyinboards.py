#!/usr/bin/env python3
from __future__ import annotations

import re
from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from typing import Dict, Any, Optional

import requests
from bs4 import BeautifulSoup

US_STATE_ABBR: Dict[str, str] = {
  'alabama': 'AL', 'alaska': 'AK', 'arizona': 'AZ', 'arkansas': 'AR',
  'california': 'CA', 'colorado': 'CO', 'connecticut': 'CT', 'delaware': 'DE',
  'florida': 'FL', 'georgia': 'GA', 'hawaii': 'HI', 'idaho': 'ID',
  'illinois': 'IL', 'indiana': 'IN', 'iowa': 'IA', 'kansas': 'KS',
  'kentucky': 'KY', 'louisiana': 'LA', 'maine': 'ME', 'maryland': 'MD',
  'massachusetts': 'MA', 'michigan': 'MI', 'minnesota': 'MN', 'mississippi': 'MS',
  'missouri': 'MO', 'montana': 'MT', 'nebraska': 'NE', 'nevada': 'NV',
  'new hampshire': 'NH', 'new jersey': 'NJ', 'new mexico': 'NM', 'new york': 'NY',
  'north carolina': 'NC', 'north dakota': 'ND', 'ohio': 'OH', 'oklahoma': 'OK',
  'oregon': 'OR', 'pennsylvania': 'PA', 'rhode island': 'RI', 'south carolina': 'SC',
  'south dakota': 'SD', 'tennessee': 'TN', 'texas': 'TX', 'utah': 'UT',
  'vermont': 'VT', 'virginia': 'VA', 'washington': 'WA', 'west virginia': 'WV',
  'wisconsin': 'WI', 'wyoming': 'WY', 'district of columbia': 'DC'
}


def _clean_spaces(value: Optional[str]) -> str:
  if not value:
    return ""
  return re.sub(r'\s+', ' ', value).strip()


def _extract_listing_id_from_url(url: str) -> Optional[str]:
  m = re.search(r'(\d{5,})/?$', url)
  return m.group(1) if m else None


def _search_value(text: str, pattern: str, flags: int = re.IGNORECASE) -> Optional[str]:
  m = re.search(pattern, text, flags)
  return m.group(1).strip() if m else None


def _normalize_location(raw: Optional[str]) -> str:
  if not raw:
    return ""
  raw = _clean_spaces(raw.replace(' ,', ','))
  # Expect formats like "CORNELIUS , North Carolina, 28031"
  # Build "Cornelius, NC 28031" when possible
  parts = [p.strip() for p in raw.split(',')]
  if len(parts) == 3:
    city = parts[0].title()
    state_name = parts[1].strip().lower()
    zip_code = parts[2].strip()
    state_abbr = US_STATE_ABBR.get(state_name, parts[1])
    return f"{city}, {state_abbr} {zip_code}".strip()
  return raw


def _parse_price(text: str) -> (Optional[int], Optional[str]):
  # Look for $155,999 patterns
  m = re.search(r'\$[\s]*([0-9][0-9,]+)', text)
  if m:
    disp = f"${m.group(1)}"
    numeric = int(m.group(1).replace(',', ''))
    return numeric, disp
  # Look for "Asking Price" lines
  m2 = re.search(r'Asking\s+Price[^$]*\$\s*([0-9][0-9,]+)', text, re.IGNORECASE)
  if m2:
    disp = f"${m2.group(1)}"
    numeric = int(m2.group(1).replace(',', ''))
    return numeric, disp
  return None, None


@dataclass
class BoatRecord:
  published: bool
  id: str
  title: str
  category: str
  status: str
  price: Optional[int]
  price_display: str
  year: Optional[int]
  make: str
  model: str
  length_ft: Optional[float]
  hours: Optional[int]
  engine: str
  hull: str
  color: str
  location: str
  description: str
  contact_phone: str
  contact_email: str
  created_at: str

  def to_sheet_dict(self) -> Dict[str, Any]:
    d = asdict(self)
    # Google Sheets expects Y/N for published; handled upstream in push
    return d


def parse_onlyinboards_listing(url: str, timeout_sec: int = 15) -> BoatRecord:
  resp = requests.get(url, timeout=timeout_sec, headers={"User-Agent": "Mozilla/5.0"})
  resp.raise_for_status()
  soup = BeautifulSoup(resp.text, 'html.parser')
  full_text = _clean_spaces(soup.get_text(separator='\n'))

  # Title
  h1 = soup.find('h1')
  title = _clean_spaces(h1.get_text()) if h1 else ""
  if not title:
    # Fallback: "YYYY Make Model" from detected fields
    year = _search_value(full_text, r'Year:\s*(\d{4})')
    make = _search_value(full_text, r'Make:\s*([A-Za-z][\w\s/&\-]+)')
    model = _search_value(full_text, r'Model:\s*([A-Za-z0-9][\w\s/&\-]+)')
    title = _clean_spaces(" ".join([p for p in [year, make, model] if p]))

  # Core fields from text
  year_str = _search_value(full_text, r'Year:\s*(\d{4})')
  make = _search_value(full_text, r'Make:\s*([A-Za-z][\w\s/&\-]+)') or ""
  model = _search_value(full_text, r'Model:\s*([A-Za-z0-9][\w\s/&\-]+)') or ""
  hours_str = _search_value(full_text, r'Engine\s*Hours:\s*([0-9]+)')
  engine = _search_value(full_text, r'Engine:\s*([A-Za-z0-9][^;\n]+)') or ""
  length_str = _search_value(full_text, r'Length:\s*([0-9]+(?:\.[0-9]+)?)')
  location_raw = _search_value(full_text, r'Location:\s*([A-Za-z ,]+,[^,\n]*,\s*\d{5})')
  price_val, price_display = _parse_price(full_text)

  # Description block heuristic
  desc = ""
  desc_candidates = [
    _search_value(full_text, r'DESCRIPTION\s*(.+?)\s*Asking\s+Price', flags=re.IGNORECASE | re.DOTALL),
    _search_value(full_text, r'DESCRIPTION\s*(.+?)\s*(CORNELIUS|Location|Dealer|$)', flags=re.IGNORECASE | re.DOTALL),
  ]
  for c in desc_candidates:
    if c and len(c) > 20:
      desc = _clean_spaces(c)
      break
  if not desc:
    # fallback: take some text near "DESCRIPTION"
    m = re.search(r'DESCRIPTION(.{60,600})', full_text, re.IGNORECASE | re.DOTALL)
    if m:
      desc = _clean_spaces(m.group(1))

  # Normalize fields
  year = int(year_str) if year_str and year_str.isdigit() else None
  hours = int(hours_str) if hours_str and hours_str.isdigit() else None
  length_ft = float(length_str) if length_str else None
  location = _normalize_location(location_raw or "")
  created_at = datetime.now(timezone.utc).isoformat()
  listing_id = _extract_listing_id_from_url(url)
  safe_id = f"oib-{listing_id}" if listing_id else re.sub(r'[^a-z0-9\-]+', '-', (title or 'onlyinboards-item').lower()).strip('-')

  # Build record
  return BoatRecord(
    published=True,
    id=safe_id,
    title=title or "Boat",
    category="Boat",
    status="available",
    price=price_val,
    price_display=price_display or (str(price_val) if price_val else ""),
    year=year,
    make=make,
    model=model,
    length_ft=length_ft,
    hours=hours,
    engine=engine or "",
    hull="Fiberglass",
    color="",
    location=location,
    description=desc or "",
    contact_phone="",
    contact_email="",
    created_at=created_at
  )


