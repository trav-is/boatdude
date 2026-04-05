#!/usr/bin/env python3
"""
Pull marketplace listings and emit Google Sheets-ready CSV files.

Current adapter targets OnlyInboards-style dealer pages, but the script accepts
any dealer URL that follows the same listing/page structure.
"""

from __future__ import annotations

import argparse
import csv
import datetime as dt
import json
import re
import sys
import urllib.parse
import urllib.request
from html import unescape
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Tuple


BOATS_HEADERS = [
    "published",
    "id",
    "title",
    "category",
    "status",
    "price",
    "price_display",
    "year",
    "make",
    "model",
    "length_ft",
    "hours",
    "engine",
    "hull",
    "color",
    "location",
    "description",
    "primary_image_url",
    "gallery_urls",
    "contact_phone",
    "contact_email",
    "created_at",
    "condition",
    "trailer_included",
    "propulsion",
    "beam_ft",
    "draft_ft",
    "fuel_capacity",
    "seating_capacity",
    "features",
    "history",
    "maintenance_notes",
]

PHOTOS_HEADERS = [
    "boat_id",
    "photo_id",
    "photo_url",
    "photo_alt",
    "photo_order",
    "is_primary",
    "photo_type",
    "photo_notes",
]


def fetch_text(url: str, timeout_sec: int = 30) -> str:
    req = urllib.request.Request(
        url,
        headers={"User-Agent": "BDD-Inventory-Puller/1.0 (+https://boatdudedeals.com)"},
    )
    with urllib.request.urlopen(req, timeout=timeout_sec) as response:
        return response.read().decode("utf-8", errors="replace")


def clean_text(value: str) -> str:
    no_tags = re.sub(r"<[^>]+>", " ", value or "")
    normalized_ws = re.sub(r"\s+", " ", unescape(no_tags)).strip()
    return normalized_ws


def normalize_money(value: str) -> Tuple[str, str]:
    digits = re.sub(r"[^\d.]", "", value or "")
    if not digits:
        return "", "Call for price"
    numeric = str(int(float(digits)))
    display = f"${int(float(digits)):,}"
    return numeric, display


def listing_id_from_url(url: str, prefix: str) -> str:
    m = re.search(r"-([0-9]{5,})/?$", url)
    if m:
        return f"{prefix}-{m.group(1)}"
    slug = urllib.parse.urlsplit(url).path.rstrip("/").split("/")[-1]
    slug = re.sub(r"[^a-zA-Z0-9\-]+", "-", slug).strip("-").lower()
    return f"{prefix}-{slug}"


def parse_ld_json(html: str) -> Dict:
    m = re.search(
        r'<script type="application/ld\+json">\s*(\{.*?\})\s*</script>',
        html,
        flags=re.S,
    )
    if not m:
        return {}
    try:
        return json.loads(m.group(1))
    except json.JSONDecodeError:
        return {}


def parse_listing_detail_items(html: str) -> Dict[str, str]:
    pairs = re.findall(
        r'oib-boat-detail-label">([^<:]+):</span>\s*(?:<div[^>]*>\s*)?<span class="oib-boat-detail-value"[^>]*>(.*?)</span>',
        html,
        flags=re.S,
    )
    out: Dict[str, str] = {}
    for raw_label, raw_value in pairs:
        label = clean_text(raw_label).lower()
        value = clean_text(raw_value)
        if label:
            out[label] = value
    return out


def parse_description(html: str) -> str:
    m = re.search(r"DESCRIPTION\s*</h2>\s*<p[^>]*>(.*?)</p>", html, flags=re.S)
    if m:
        return clean_text(m.group(1))
    return ""


def parse_gallery_urls(base_url: str, html: str, ld_json: Dict, listing_url: str) -> List[str]:
    urls: List[str] = []
    listing_numeric_id = ""
    m_listing_id = re.search(r"-([0-9]{5,})/?$", listing_url)
    if m_listing_id:
        listing_numeric_id = m_listing_id.group(1)

    image_nodes = ld_json.get("image", []) if isinstance(ld_json, dict) else []
    for node in image_nodes:
        if isinstance(node, dict) and node.get("url"):
            urls.append(node["url"])
        elif isinstance(node, str):
            urls.append(node)

    rels = re.findall(
        r'<img src="(/getmedia/[^"?]+\.(?:webp|jpg|jpeg|png))(?:\?[^"]*)?"',
        html,
        flags=re.I,
    )
    for rel in rels:
        urls.append(urllib.parse.urljoin(base_url, rel))

    deduped: List[str] = []
    seen = set()
    for u in urls:
        if not u:
            continue
        normalized = u.split("?")[0]
        # Keep only listing-specific gallery assets and skip global/site assets.
        if listing_numeric_id:
            marker = f"-{listing_numeric_id}-image"
            if marker not in normalized.lower():
                continue
        if normalized not in seen:
            deduped.append(normalized)
            seen.add(normalized)
    return deduped


def infer_page_count(html: str) -> int:
    m = re.search(r"Page\s+\d+\s+of\s+(\d+)", html, flags=re.I)
    if not m:
        return 1
    return max(1, int(m.group(1)))


def parse_listing_urls(base_url: str, html: str) -> List[str]:
    rels = re.findall(r'href="(/listings/[^"]+)"', html)
    unique = []
    seen = set()
    for rel in rels:
        abs_url = urllib.parse.urljoin(base_url, rel)
        if abs_url not in seen:
            unique.append(abs_url)
            seen.add(abs_url)
    return unique


def collect_listing_urls(dealer_url: str, max_pages: int = 10) -> List[str]:
    parsed = urllib.parse.urlsplit(dealer_url)
    base_url = f"{parsed.scheme}://{parsed.netloc}"
    path = parsed.path or "/"

    all_links: List[str] = []
    seen = set()
    total_pages = None

    for page in range(1, max_pages + 1):
        q = f"{parsed.query}&page={page}" if parsed.query else f"page={page}"
        page_url = urllib.parse.urlunsplit(
            (parsed.scheme, parsed.netloc, path, q if page > 1 else parsed.query, "")
        )
        html = fetch_text(page_url)
        if total_pages is None:
            total_pages = infer_page_count(html)

        links = parse_listing_urls(base_url, html)
        for link in links:
            if link not in seen:
                all_links.append(link)
                seen.add(link)

        if page >= (total_pages or 1):
            break
        if not links:
            break

    return all_links


def map_listing_to_rows(
    listing_url: str,
    html: str,
    dealer_phone: str,
    dealer_email: str,
    default_published: str,
    id_prefix: str,
) -> Tuple[Dict[str, str], List[Dict[str, str]]]:
    parsed = urllib.parse.urlsplit(listing_url)
    base_url = f"{parsed.scheme}://{parsed.netloc}"

    ld = parse_ld_json(html)
    details = parse_listing_detail_items(html)
    description = parse_description(html) or clean_text(str(ld.get("description", "")))
    title = clean_text(str(ld.get("name", "")))
    if not title:
        m = re.search(r"<h1>(.*?)</h1>", html, flags=re.S)
        title = clean_text(m.group(1) if m else "")

    price_num = ""
    price_display = "Call for price"
    offers = ld.get("offers", {}) if isinstance(ld, dict) else {}
    if isinstance(offers, dict) and offers.get("price") is not None:
        price_num, price_display = normalize_money(str(offers.get("price")))
    if not price_num:
        m_price = re.search(r"Asking Price\s*</p>\s*<p[^>]*>\s*([^<]+)\s*</p>", html, flags=re.S)
        if m_price:
            price_num, price_display = normalize_money(clean_text(m_price.group(1)))

    year = details.get("year", "")
    make = details.get("make", "")
    model = details.get("model", "") or clean_text(str(ld.get("model", "")))
    hours = details.get("engine hours", "")
    engine = details.get("engine", "")
    length_ft = details.get("length", "").replace("feet", "").strip()
    location = details.get("location", "")

    gallery = parse_gallery_urls(base_url, html, ld, listing_url)
    primary = gallery[0] if gallery else ""

    boat_id = listing_id_from_url(listing_url, id_prefix)
    boat_row = {
        "published": default_published,
        "id": boat_id,
        "title": title,
        "category": "Boat",
        "status": "available",
        "price": price_num,
        "price_display": price_display,
        "year": year,
        "make": make,
        "model": model,
        "length_ft": length_ft,
        "hours": hours,
        "engine": engine,
        "hull": "",
        "color": "",
        "location": location,
        "description": description,
        "primary_image_url": primary,
        "gallery_urls": ",".join(gallery),
        "contact_phone": dealer_phone,
        "contact_email": dealer_email,
        "created_at": dt.datetime.now(dt.timezone.utc).isoformat(),
        "condition": "",
        "trailer_included": "",
        "propulsion": details.get("drive type", ""),
        "beam_ft": "",
        "draft_ft": "",
        "fuel_capacity": "",
        "seating_capacity": "",
        "features": "",
        "history": "",
        "maintenance_notes": "",
    }

    photo_rows: List[Dict[str, str]] = []
    for i, url in enumerate(gallery, start=1):
        photo_rows.append(
            {
                "boat_id": boat_id,
                "photo_id": f"{boat_id}-{i:02d}",
                "photo_url": url,
                "photo_alt": title,
                "photo_order": str(i),
                "is_primary": "true" if i == 1 else "false",
                "photo_type": "exterior",
                "photo_notes": "",
            }
        )

    return boat_row, photo_rows


def write_csv(path: Path, headers: List[str], rows: Iterable[Dict[str, str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=headers, extrasaction="ignore")
        writer.writeheader()
        for row in rows:
            writer.writerow({h: row.get(h, "") for h in headers})


def main() -> int:
    parser = argparse.ArgumentParser(description="Pull listings into Sheets-ready CSV files.")
    parser.add_argument("--dealer-url", required=True, help="Dealer page URL to crawl.")
    parser.add_argument("--boats-out", required=True, help="Output CSV path for boats.")
    parser.add_argument("--photos-out", required=True, help="Output CSV path for photos.")
    parser.add_argument("--snapshot-out", help="Optional JSON snapshot path.")
    parser.add_argument("--dealer-phone", default="704.957.0900")
    parser.add_argument("--dealer-email", default="info@boatdudedeals.com")
    parser.add_argument("--published", default="Y", choices=["Y", "N"])
    parser.add_argument("--id-prefix", default="oib")
    parser.add_argument("--max-pages", type=int, default=10)
    args = parser.parse_args()

    listing_urls = collect_listing_urls(args.dealer_url, max_pages=args.max_pages)
    if not listing_urls:
        print("No listings found. Check dealer URL or page structure.", file=sys.stderr)
        return 1

    boats: List[Dict[str, str]] = []
    photos: List[Dict[str, str]] = []
    for idx, listing_url in enumerate(listing_urls, start=1):
        try:
            html = fetch_text(listing_url)
            boat_row, photo_rows = map_listing_to_rows(
                listing_url=listing_url,
                html=html,
                dealer_phone=args.dealer_phone,
                dealer_email=args.dealer_email,
                default_published=args.published,
                id_prefix=args.id_prefix,
            )
            boats.append(boat_row)
            photos.extend(photo_rows)
            print(f"[{idx}/{len(listing_urls)}] Pulled {boat_row['id']}")
        except Exception as exc:  # pylint: disable=broad-except
            print(f"Failed to parse listing: {listing_url} ({exc})", file=sys.stderr)

    write_csv(Path(args.boats_out), BOATS_HEADERS, boats)
    write_csv(Path(args.photos_out), PHOTOS_HEADERS, photos)

    if args.snapshot_out:
        snapshot = {
            "updated_at": dt.datetime.now(dt.timezone.utc).isoformat(),
            "source": args.dealer_url,
            "listings_count": len(boats),
            "photos_count": len(photos),
            "boats": boats,
            "photos": photos,
        }
        snap_path = Path(args.snapshot_out)
        snap_path.parent.mkdir(parents=True, exist_ok=True)
        snap_path.write_text(json.dumps(snapshot, indent=2), encoding="utf-8")

    print(f"Wrote boats CSV: {args.boats_out} ({len(boats)} rows)")
    print(f"Wrote photos CSV: {args.photos_out} ({len(photos)} rows)")
    if args.snapshot_out:
        print(f"Wrote snapshot JSON: {args.snapshot_out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
