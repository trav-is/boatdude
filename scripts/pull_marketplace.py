#!/usr/bin/env python3
"""
Pull marketplace listings and emit Google Sheets-ready CSV files.

Adapters:
- onlyinboards.com — dealer inventory pages with /listings/ links and pagination (?page=)
- pontoonsonly.com — filtered search/browse URLs (e.g. ?k=dealername) harvest listing links from
  page 1; single listing URLs (…_i12345); optional `--urls-file` for extra lines. Pagination on
  search uses form postback, so only the first results page is fetched unless you add more URLs.

With no `--source`, `--listing-url`, `--urls-file`, or `--dealer-url`, the script uses the default
Boat Dude Deals inventory URLs for both sites (see DEFAULT_MARKETPLACE_SOURCES).
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

# Used when no URL is passed on the command line (same feeds as README examples).
DEFAULT_MARKETPLACE_SOURCES: Tuple[str, ...] = (
    "https://onlyinboards.com/dealeruserprofile/80113",
    "https://www.pontoonsonly.com/search?k=boatdudedeals",
)


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


def marketplace_host(url: str) -> str:
    host = (urllib.parse.urlsplit(url).netloc or "").lower()
    if "onlyinboards.com" in host:
        return "onlyinboards"
    if "pontoonsonly.com" in host:
        return "pontoons"
    return "unknown"


def default_id_prefix_for_url(url: str) -> str:
    h = marketplace_host(url)
    if h == "pontoons":
        return "po"
    if h == "onlyinboards":
        return "oib"
    return "listing"


def listing_id_from_url(url: str, prefix: str) -> str:
    if marketplace_host(url) == "pontoons":
        m = re.search(r"_i(\d+)/?$", url, re.I)
        if m:
            return f"{prefix}-{m.group(1)}"
    m = re.search(r"-([0-9]{5,})/?$", url)
    if m:
        return f"{prefix}-{m.group(1)}"
    slug = urllib.parse.urlsplit(url).path.rstrip("/").split("/")[-1]
    slug = re.sub(r"[^a-zA-Z0-9\-]+", "-", slug).strip("-").lower()
    return f"{prefix}-{slug}"


def is_pontoons_listing_url(url: str) -> bool:
    return bool(re.search(r"_i\d+", urllib.parse.urlsplit(url).path or "", re.I))


# --- OnlyInboards ---


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


def parse_description_oib(html: str) -> str:
    m = re.search(r"DESCRIPTION\s*</h2>\s*<p[^>]*>(.*?)</p>", html, flags=re.S)
    if m:
        return clean_text(m.group(1))
    return ""


def parse_gallery_urls_oib(base_url: str, html: str, ld_json: Dict, listing_url: str) -> List[str]:
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
        if listing_numeric_id:
            marker = f"-{listing_numeric_id}-image"
            if marker not in normalized.lower():
                continue
        if normalized not in seen:
            deduped.append(normalized)
            seen.add(normalized)
    return deduped


def infer_page_count_oib(html: str) -> int:
    m = re.search(r"Page\s+\d+\s+of\s+(\d+)", html, flags=re.I)
    if not m:
        return 1
    return max(1, int(m.group(1)))


def parse_listing_urls_oib(base_url: str, html: str) -> List[str]:
    rels = re.findall(r'href="(/listings/[^"]+)"', html)
    unique: List[str] = []
    seen = set()
    for rel in rels:
        abs_url = urllib.parse.urljoin(base_url, rel)
        if abs_url not in seen:
            unique.append(abs_url)
            seen.add(abs_url)
    return unique


def collect_listing_urls_oib(dealer_url: str, max_pages: int = 10) -> List[str]:
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
            total_pages = infer_page_count_oib(html)

        links = parse_listing_urls_oib(base_url, html)
        for link in links:
            if link not in seen:
                all_links.append(link)
                seen.add(link)

        if page >= (total_pages or 1):
            break
        if not links:
            break

    return all_links


def map_onlyinboards_listing(
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
    description = parse_description_oib(html) or clean_text(str(ld.get("description", "")))
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

    gallery = parse_gallery_urls_oib(base_url, html, ld, listing_url)
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


# --- PontoonsOnly ---


def parse_pontoons_meta(html: str) -> Dict[str, str]:
    out: Dict[str, str] = {}
    for raw_label, raw_value in re.findall(
        r'<div class="meta">\s*<strong>([^<]+):</strong>\s*(.*?)</div>',
        html,
        flags=re.S,
    ):
        label = clean_text(raw_label).lower().rstrip(":")
        value = clean_text(raw_value)
        if label:
            out[label] = value
    return out


def parse_pontoons_description(html: str) -> str:
    m = re.search(
        r'<div id="description"[^>]*class="description"[^>]*>\s*<p>(.*?)</p>',
        html,
        flags=re.S | re.I,
    )
    if m:
        return clean_text(m.group(1))
    return ""


def parse_pontoons_gallery(html: str) -> List[str]:
    """Full-size JPEG URLs from swipebox links inside the listing photos block."""
    m_block = re.search(
        r'<div class="photos">(.*?)(?:<div id="description"|<div id="useful_info")',
        html,
        flags=re.S | re.I,
    )
    block = m_block.group(1) if m_block else html
    hrefs = re.findall(r'href=[\'"]([^\'"]+\.(?:jpe?g|webp))[\'"]', block, flags=re.I)
    hrefs = [h for h in hrefs if "Photo/" in h or "/photo/" in h.lower()]
    deduped: List[str] = []
    seen = set()
    for h in hrefs:
        full = re.sub(r"_small(\.(?:jpe?g|webp))$", r"\1", h, flags=re.I)
        if full not in seen:
            deduped.append(full)
            seen.add(full)
    return deduped


def parse_pontoons_price_location_title(html: str) -> Tuple[str, str, str, str]:
    title = ""
    m_h1 = re.search(r'<div class="heading">\s*<h1>(.*?)</h1>', html, flags=re.S | re.I)
    if m_h1:
        title = clean_text(m_h1.group(1))

    price_num, price_display = "", "Call for price"
    m_price = re.search(r'<span class="price">\s*([^<]+)', html, flags=re.I)
    if m_price:
        price_num, price_display = normalize_money(clean_text(m_price.group(1)))

    location = ""
    m_loc = re.search(r'<h4 id="item_location">([^<]+)</h4>', html, flags=re.I)
    if m_loc:
        location = clean_text(m_loc.group(1))

    return title, price_num, price_display, location


def parse_pontoons_browse_counts(html: str) -> Optional[Tuple[int, int, int]]:
    """Parse 'Browsing N-M of T listings' from search results; return (start, end, total) or None."""
    m = re.search(
        r"Browsing\s*<strong>\s*(\d+)\s*-\s*(\d+)\s*</strong>\s*of\s*<strong>\s*(\d+)\s*</strong>",
        html,
        flags=re.I,
    )
    if not m:
        return None
    return int(m.group(1)), int(m.group(2)), int(m.group(3))


def parse_listing_urls_pontoons_page(html: str, base_url: str) -> List[str]:
    rels = re.findall(r'href="(/[^"]+_i\d+)"', html)
    rels += re.findall(r'href="([^"/][^"]*_i\d+)"', html)
    unique: List[str] = []
    seen = set()
    for rel in rels:
        path = rel if rel.startswith("/") else "/" + rel
        abs_url = urllib.parse.urljoin(base_url, path)
        if abs_url not in seen:
            unique.append(abs_url)
            seen.add(abs_url)
    return unique


def collect_listing_urls_pontoons(seed_url: str, max_pages: int = 1) -> List[str]:
    """Harvest listing URLs from a browse/search page (first page only by default)."""
    parsed = urllib.parse.urlsplit(seed_url)
    base_url = f"{parsed.scheme}://{parsed.netloc}"
    if is_pontoons_listing_url(seed_url):
        return [urllib.parse.urlunsplit((parsed.scheme, parsed.netloc, parsed.path, parsed.query, ""))]

    all_links: List[str] = []
    seen = set()
    for _ in range(max(1, max_pages)):
        html = fetch_text(seed_url)
        counts = parse_pontoons_browse_counts(html)
        if counts and counts[1] < counts[2]:
            print(
                f"PontoonsOnly: results show {counts[0]}-{counts[1]} of {counts[2]}; "
                "only the first page is fetched (search pagination is not a simple ?page= link). "
                "Add `--listing-url` / `--urls-file` entries for listings beyond this page.",
                file=sys.stderr,
            )
        for link in parse_listing_urls_pontoons_page(html, base_url):
            if link not in seen:
                all_links.append(link)
                seen.add(link)
        break
    if not all_links and not is_pontoons_listing_url(seed_url):
        print(
            "PontoonsOnly: no _i#### links on this page. "
            "Use a listing URL (…_i12345), a search URL with visible results, or `--urls-file`.",
            file=sys.stderr,
        )
    return all_links


def map_pontoons_listing(
    listing_url: str,
    html: str,
    dealer_phone: str,
    dealer_email: str,
    default_published: str,
    id_prefix: str,
) -> Tuple[Dict[str, str], List[Dict[str, str]]]:
    meta = parse_pontoons_meta(html)
    description = parse_pontoons_description(html)
    title, price_num, price_display, location = parse_pontoons_price_location_title(html)
    gallery = parse_pontoons_gallery(html)
    primary = gallery[0] if gallery else ""

    year = meta.get("year", "")
    make = meta.get("make", "")
    length_raw = meta.get("length", "")
    length_ft = re.sub(r"\s*feet?\s*$", "", length_raw, flags=re.I).strip()
    horsepower = meta.get("horsepower", "")

    boat_id = listing_id_from_url(listing_url, id_prefix)
    model_guess = ""
    if title and make and make.lower() in title.lower():
        model_guess = re.sub(
            re.escape(make),
            "",
            title,
            flags=re.I,
            count=1,
        ).strip()
        model_guess = re.sub(r"^\s*(new|used)\s+", "", model_guess, flags=re.I).strip()
        model_guess = re.sub(r"\s*[-–—]\s*.*$", "", model_guess).strip()
        m_y = re.search(r"\b(19|20)\d{2}\b", model_guess)
        if m_y:
            model_guess = model_guess.replace(m_y.group(0), "").strip()

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
        "model": model_guess,
        "length_ft": length_ft,
        "hours": "",
        "engine": horsepower,
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
        "propulsion": "",
        "beam_ft": "",
        "draft_ft": "",
        "fuel_capacity": "",
        "seating_capacity": "",
        "features": "",
        "history": "",
        "maintenance_notes": "",
    }

    photo_rows: List[Dict[str, str]] = []
    for i, photo_url in enumerate(gallery, start=1):
        photo_rows.append(
            {
                "boat_id": boat_id,
                "photo_id": f"{boat_id}-{i:02d}",
                "photo_url": photo_url,
                "photo_alt": title,
                "photo_order": str(i),
                "is_primary": "true" if i == 1 else "false",
                "photo_type": "exterior",
                "photo_notes": "",
            }
        )

    return boat_row, photo_rows


def map_listing_to_rows(
    listing_url: str,
    html: str,
    dealer_phone: str,
    dealer_email: str,
    default_published: str,
    id_prefix: str,
) -> Tuple[Dict[str, str], List[Dict[str, str]]]:
    host = marketplace_host(listing_url)
    if host == "pontoons":
        return map_pontoons_listing(
            listing_url, html, dealer_phone, dealer_email, default_published, id_prefix
        )
    return map_onlyinboards_listing(
        listing_url, html, dealer_phone, dealer_email, default_published, id_prefix
    )


def collect_listing_urls(dealer_url: str, max_pages: int = 10) -> List[str]:
    host = marketplace_host(dealer_url)
    if host == "pontoons":
        return collect_listing_urls_pontoons(dealer_url, max_pages=max_pages)
    if host == "onlyinboards":
        return collect_listing_urls_oib(dealer_url, max_pages=max_pages)
    print(f"Unknown marketplace host in URL: {dealer_url}", file=sys.stderr)
    return []


def dedupe_urls_preserve_order(urls: Iterable[str]) -> List[str]:
    out: List[str] = []
    seen: set = set()
    for raw in urls:
        u = (raw or "").strip()
        if not u or u in seen:
            continue
        out.append(u)
        seen.add(u)
    return out


def read_urls_from_files(paths: List[str]) -> List[str]:
    """One URL per line; blank lines and # comments skipped."""
    out: List[str] = []
    for raw in paths:
        p = Path(raw).expanduser()
        if not p.is_file():
            print(f"URLs file not found: {p}", file=sys.stderr)
            continue
        for line in p.read_text(encoding="utf-8", errors="replace").splitlines():
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            out.append(line)
    return out


def write_csv(path: Path, headers: List[str], rows: Iterable[Dict[str, str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=headers, extrasaction="ignore")
        writer.writeheader()
        for row in rows:
            writer.writerow({h: row.get(h, "") for h in headers})


def main() -> int:
    parser = argparse.ArgumentParser(description="Pull listings into Sheets-ready CSV files.")
    parser.add_argument(
        "--source",
        action="append",
        default=[],
        metavar="URL",
        help=(
            "Dealer inventory, search/browse, or listing URL (repeatable). "
            "Works for onlyinboards.com and pontoonsonly.com; URL type is auto-detected. "
            "Omitted: uses default Boat Dude Deals sources for both sites."
        ),
    )
    parser.add_argument(
        "--dealer-url",
        action="append",
        default=[],
        dest="dealer_urls",
        help="Deprecated alias for --source (repeatable).",
    )
    parser.add_argument(
        "--listing-url",
        action="append",
        default=[],
        dest="listing_urls",
        help="Listing URL to pull (repeatable). No search crawl — uses each public detail page.",
    )
    parser.add_argument(
        "--urls-file",
        action="append",
        default=[],
        dest="urls_files",
        help="Text file: one listing URL per line (# comments and blank lines OK). Repeatable.",
    )
    parser.add_argument(
        "--boats-out",
        default="data/exports/boats-sheet.csv",
        help="Output CSV path for boats (default: data/exports/boats-sheet.csv).",
    )
    parser.add_argument(
        "--photos-out",
        default="data/exports/photos-sheet.csv",
        help="Output CSV path for photos (default: data/exports/photos-sheet.csv).",
    )
    parser.add_argument("--snapshot-out", help="Optional JSON snapshot path.")
    parser.add_argument("--dealer-phone", default="704.957.0900")
    parser.add_argument("--dealer-email", default="info@boatdudedeals.com")
    parser.add_argument("--published", default="Y", choices=["Y", "N"])
    parser.add_argument(
        "--id-prefix",
        default=None,
        help="Boat id prefix (default: oib for OnlyInboards, po for PontoonsOnly, per URL).",
    )
    parser.add_argument("--max-pages", type=int, default=10)
    args = parser.parse_args()

    seeds: List[str] = []
    seeds.extend(args.source or [])
    seeds.extend(args.dealer_urls or [])
    seeds.extend(args.listing_urls or [])
    seeds.extend(read_urls_from_files(list(args.urls_files or [])))
    seeds = dedupe_urls_preserve_order(seeds)

    url_args_provided = bool(
        (args.source or [])
        or (args.dealer_urls or [])
        or (args.listing_urls or [])
        or (args.urls_files or [])
    )
    if not seeds:
        if url_args_provided:
            print(
                "No listing URLs found: check --source / --listing-url / --urls-file "
                "(or deprecated --dealer-url).",
                file=sys.stderr,
            )
            return 1
        seeds = list(DEFAULT_MARKETPLACE_SOURCES)
        print(
            "Using default OnlyInboards + PontoonsOnly sources "
            f"({len(seeds)} URLs).",
            file=sys.stderr,
        )

    listing_urls: List[str] = []
    seen: set = set()

    for seed in seeds:
        host = marketplace_host(seed)
        if host == "unknown":
            print(f"Skip unknown host: {seed}", file=sys.stderr)
            continue
        if host == "pontoons" and is_pontoons_listing_url(seed):
            if seed not in seen:
                listing_urls.append(seed)
                seen.add(seed)
            continue
        if host == "onlyinboards" and "/listings/" in urllib.parse.urlsplit(seed).path:
            if seed not in seen:
                listing_urls.append(seed)
                seen.add(seed)
            continue

        for link in collect_listing_urls(seed, max_pages=args.max_pages):
            if link not in seen:
                listing_urls.append(link)
                seen.add(link)

    if not listing_urls:
        print("No listings found. Check URLs or site structure.", file=sys.stderr)
        return 1

    boats: List[Dict[str, str]] = []
    photos: List[Dict[str, str]] = []
    for idx, listing_url in enumerate(listing_urls, start=1):
        try:
            html = fetch_text(listing_url)
            prefix = args.id_prefix or default_id_prefix_for_url(listing_url)
            boat_row, photo_rows = map_listing_to_rows(
                listing_url=listing_url,
                html=html,
                dealer_phone=args.dealer_phone,
                dealer_email=args.dealer_email,
                default_published=args.published,
                id_prefix=prefix,
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
            "source": seeds,
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
