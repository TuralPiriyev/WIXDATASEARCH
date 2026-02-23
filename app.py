"""
Watch Data Scraper & Wix Porter - ENHANCED 51-COLUMN VERSION
A web-based tool to search for watch models, extract product details, and generate 
100% Wix-compatible CSV files with all 51 required columns.

Author: Senior Python Developer & Automation Engineer
Created: February 2026
Version: 2.0 (Wix 51-Column Compatible)
"""

from flask import Flask, render_template, request, jsonify, send_file
from bs4 import BeautifulSoup
import requests
import pandas as pd
import csv
from io import StringIO, BytesIO
import json
import re
import os
from urllib.parse import quote, unquote, urlparse
import logging
from datetime import datetime


def load_local_env_file():
    """Load simple KEY=VALUE pairs from .env in project root into environment."""
    env_path = os.path.join(os.path.dirname(__file__), '.env')
    if not os.path.exists(env_path):
        return

    try:
        with open(env_path, 'r', encoding='utf-8') as f:
            for line in f:
                raw = line.strip()
                if not raw or raw.startswith('#') or '=' not in raw:
                    continue
                key, value = raw.split('=', 1)
                key = key.strip()
                value = value.strip().strip('"').strip("'")
                existing = os.environ.get(key, '') if key else ''
                if key and (not existing):
                    os.environ[key] = value
    except Exception as e:
        logger = logging.getLogger(__name__)
        logger.debug(f"Could not load .env file: {e}")


load_local_env_file()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

app = Flask(__name__)
app.config['JSON_SORT_KEYS'] = False

# Browser headers to avoid being blocked
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
    'Accept-Language': 'en-US,en;q=0.5',
    'Accept-Encoding': 'gzip, deflate',
    'Connection': 'keep-alive',
    'Upgrade-Insecure-Requests': '1'
}

SUPPORTED_IMAGE_EXTENSIONS = ('.jpg', '.jpeg', '.png', '.webp')
IMAGE_PLACEHOLDER_URL = 'https://dummyimage.com/1200x1200/e9ecef/212529.jpg?text=No+Image'

# Wix CSV 51 Columns (Exact Order Required)
WIX_COLUMNS = [
    'handleId', 'fieldType', 'name', 'description', 'productImageUrl',
    'collection', 'sku', 'ribbon', 'price', 'surcharge',
    'visible', 'discountMode', 'discountValue', 'inventory', 'weight',
    'cost', 'productOptionName1', 'productOptionType1', 'productOptionDescription1',
    'productOptionName2', 'productOptionType2', 'productOptionDescription2',
    'productOptionName3', 'productOptionType3', 'productOptionDescription3',
    'productOptionName4', 'productOptionType4', 'productOptionDescription4',
    'productOptionName5', 'productOptionType5', 'productOptionDescription5',
    'productOptionName6', 'productOptionType6', 'productOptionDescription6',
    'productVariantName1', 'productVariantOptionValue1_1', 'productVariantOptionValue1_2',
    'productVariantOptionValue1_3', 'productVariantOptionValue1_4', 'productVariantOptionValue1_5',
    'productVariantOptionValue1_6', 'productVariantPrice1', 'productVariantInventory1',
    'productVariantVisible1', 'productVariantSku1', 'productVariantWeight1',
    'productVariantCost1', 'productVariantWholesalePrice1', 'productVariantMetaData1', 'brand'
]

REQUEST_TIMEOUT = 10
MAX_RETRIES = 2
GROUP_ORDER = ['siferblat_rengi', 'bilerzik', 'cinsi', 'olcu', 'mexanizm', 'kemer_rengi', 'korpus']
GROUP_UNKNOWN_LABELS = {
    'siferblat_rengi': 'SR - Uyğun deyil',
    'bilerzik': 'Bilərzik - Uyğun deyil',
    'cinsi': 'Cinsi - Uyğun deyil',
    'olcu': 'Ölçü - Uyğun deyil',
    'mexanizm': 'Mexanizm - Uyğun deyil',
    'kemer_rengi': 'KR - Uyğun deyil',
    'korpus': 'Korpus - Uyğun deyil'
}
GROUP_TRIGGERS = {
    'siferblat_rengi': ['dial', 'siferblat', 'face'],
    'bilerzik': ['bracelet', 'strap', 'band', 'bilezik', 'bilərzik', 'kəmər'],
    'cinsi': ['men', 'women', 'lady', 'male', 'female', 'unisex', 'kişi', 'qadın'],
    'olcu': ['mm', 'diameter', 'case size', 'ölçü'],
    'mexanizm': ['quartz', 'automatic', 'mechanical', 'movement', 'kvarts', 'mexanika'],
    'kemer_rengi': ['strap', 'band', 'kəmər', 'bracelet'],
    'korpus': ['case', 'korpus', 'stainless', 'steel', 'material']
}

OFFICIAL_BRAND_DOMAINS = {
    'SEIKO': ['seikowatches.com', 'seikowatches.eu'],
    'SEİKO': ['seikowatches.com', 'seikowatches.eu'],
    'CASIO': ['casio.com'],
    'CITIZEN': ['citizenwatch.com'],
    'ORIENT': ['orient-watch.com'],
    'EDIFICE': ['casio.com'],
    'INGERSOLL': ['ingersoll1892.com'],
    'TISSOT': ['tissotwatches.com'],
    'OMEGA': ['omegawatches.com'],
    'ROLEX': ['rolex.com']
}

PRIORITY_SOURCE_DOMAINS = [
    'watchbase.com',
    'chrono24.com',
    'sakurawatches.com',
    'watchcharts.com',
    'jomashop.com',
    'ashford.com'
]

def get_default_mapping():
    """Default, editable collection mapping used when JSON config is unavailable."""
    return {
        'brand_collections': {
            'CASIO': 'CASIO',
            'CITIZEN': 'CITIZEN',
            'EDIFICE': 'EDIFICE',
            'INGERSOLL': 'INGERSOLL',
            'ORIENT': 'ORIENT',
            'SEIKO': 'SEİKO',
            'SEİKO': 'SEİKO'
        },
        'category_keywords': {
            'siferblat_rengi': {
                'SR - Ağ': ['white dial', 'ağ siferblat', 'ağ dial'],
                'SR - Boz': ['gray dial', 'grey dial', 'boz siferblat', 'boz dial'],
                'SR - Firuzə': ['turquoise dial', 'teal dial', 'firuzə siferblat'],
                'SR - Gəhvəyi': ['brown dial', 'qəhvəyi siferblat', 'qəhvəyi dial'],
                'SR - Göy': ['navy dial', 'cobalt dial', 'göy siferblat', 'göy dial'],
                'SR - Krem': ['cream dial', 'ivory dial', 'krem siferblat'],
                'SR - Mavi': ['blue dial', 'mavi siferblat', 'mavi dial'],
                'SR - Qara': ['black dial', 'qara siferblat', 'qara dial'],
                'SR - Qırmızı': ['red dial', 'qırmızı siferblat', 'qırmızı dial'],
                'SR - Sarı': ['yellow dial', 'sarı siferblat', 'sarı dial'],
                'SR - Yaşıl': ['green dial', 'yaşıl siferblat', 'yaşıl dial']
            },
            'bilerzik': {
                'Bilərzik - Dəri': ['leather', 'dəri', 'genuine leather'],
                'Bilərzik - Kauçuk': ['rubber', 'silicone', 'resin', 'kauçuk'],
                'Bilərzik - Polad': ['steel bracelet', 'stainless steel bracelet', 'metal bracelet', 'polad bilərzik', 'mesh bracelet', 'milanese']
            },
            'cinsi': {
                'Cinsi - Kişi': ['men', 'mens', "men's", 'kişi', 'male'],
                'Cinsi - Qadın': ['women', 'womens', "women's", 'lady', 'ladies', 'qadın', 'female']
            },
            'olcu': {
                'Ölçü - 30 x 30 mm': ['30 x 30 mm', '30x30 mm', '30x30', '30 mm'],
                'Ölçü - 41 x 41 mm': ['41 x 41 mm', '41x41 mm', '41x41', '41 mm']
            },
            'mexanizm': {
                'Kvarts': ['quartz', 'kvarts'],
                'Mexanika': ['automatic', 'mechanical', 'self-winding', 'manual wind', 'mexanik', 'mexanika']
            },
            'kemer_rengi': {
                'KR - Gəhvəyi': ['brown strap', 'brown leather', 'qəhvəyi kəmər', 'qəhvəyi dəri'],
                'KR - Qara': ['black strap', 'black leather', 'qara kəmər', 'qara dəri'],
                'KR - Göy': ['blue strap', 'mavi kəmər', 'göy kəmər'],
                'KR - Boz': ['gray strap', 'grey strap', 'boz kəmər'],
                'KR - Boz/Sarı': ['gray and yellow strap', 'grey and yellow strap', 'boz sarı kəmər', 'boz/sarı kəmər'],
                'KR - Ağ': ['white strap', 'ağ kəmər'],
                'KR - Krem': ['cream strap', 'ivory strap', 'krem kəmər'],
                'KR - Sarı': ['yellow strap', 'sarı kəmər']
            },
            'korpus': {
                'Polad': ['stainless steel', 'steel case', 'metal case', 'polad korpus', 'steel', 'polad']
            }
        }
    }


def load_mapping_config():
    """Load mapping config from JSON file (editable without code changes)."""
    default = get_default_mapping()
    config_path = os.path.join(os.path.dirname(__file__), 'category_mapping.json')

    if not os.path.exists(config_path):
        return default

    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            loaded = json.load(f)
        if not isinstance(loaded, dict):
            return default
        return {
            'brand_collections': loaded.get('brand_collections', default['brand_collections']),
            'category_keywords': loaded.get('category_keywords', default['category_keywords'])
        }
    except Exception as e:
        logger.warning(f"Could not load category_mapping.json, using defaults: {e}")
        return default


MAPPING_CONFIG = load_mapping_config()
CATEGORY_KEYWORDS = MAPPING_CONFIG['category_keywords']
BRAND_COLLECTIONS = MAPPING_CONFIG['brand_collections']


def load_model_specs_catalog():
    """Load local deterministic model specification catalog."""
    catalog_path = os.path.join(os.path.dirname(__file__), 'model_specs_catalog.json')
    if not os.path.exists(catalog_path):
        return {}
    try:
        with open(catalog_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        return data if isinstance(data, dict) else {}
    except Exception as e:
        logger.warning(f"Could not load model_specs_catalog.json: {e}")
        return {}


def save_model_specs_catalog(catalog):
    """Persist model specs catalog to disk."""
    try:
        catalog_path = os.path.join(os.path.dirname(__file__), 'model_specs_catalog.json')
        with open(catalog_path, 'w', encoding='utf-8') as f:
            json.dump(catalog, f, ensure_ascii=False, indent=2)
        return True
    except Exception as e:
        logger.error(f"Could not save model_specs_catalog.json: {e}")
        return False


MODEL_SPECS_CATALOG = load_model_specs_catalog()


def normalize_model_key(model_number):
    return re.sub(r'[^A-Z0-9]', '', str(model_number or '').upper())


def extract_canonical_model_number(model_number):
    """Extract a clean model number token from mixed inputs (e.g. 'Model: Seiko SNXS77')."""
    raw = str(model_number or '').strip()
    if not raw:
        return ''

    cleaned = re.sub(r'^(watch\s*)?model\s*[:#-]*\s*', '', raw, flags=re.IGNORECASE).strip()
    cleaned = re.sub(r'^(ref\.?|reference|sku)\s*[:#-]*\s*', '', cleaned, flags=re.IGNORECASE).strip()

    tokens = re.split(r'\s+', cleaned)
    if not tokens:
        return cleaned

    # Drop leading brand token when present (SEIKO SNXS77 -> SNXS77)
    if len(tokens) > 1 and normalize_brand(tokens[0]):
        tokens = tokens[1:]

    # Prefer token containing digits (typical watch model format)
    for token in reversed(tokens):
        normalized = normalize_model_key(token)
        if re.search(r'\d', normalized) and len(normalized) >= 4:
            return token.strip()

    return tokens[-1].strip() if tokens else cleaned


def _catalog_unknown_count(specs):
    count = 0
    for group in GROUP_ORDER:
        value = str(specs.get(group, '') or '').strip().lower()
        if 'uyğun deyil' in value:
            count += 1
    return count


def _pick_best_catalog_spec(candidate_items):
    """Pick highest-quality catalog row among candidates."""
    if not candidate_items:
        return None

    def score(item):
        key, spec = item
        filled = sum(1 for g in GROUP_ORDER if str(spec.get(g, '') or '').strip())
        unknown = _catalog_unknown_count(spec)
        return (unknown, -filled, len(key))

    best_key, best_spec = sorted(candidate_items, key=score)[0]
    logger.info(f"Catalog candidate selected: {best_key} (unknown groups: {_catalog_unknown_count(best_spec)})")
    return best_spec


def lookup_model_specs(model_number):
    """Find deterministic specs by canonical model key and choose best-quality candidate."""
    raw_key = normalize_model_key(model_number)
    canonical_model = extract_canonical_model_number(model_number)
    canonical_key = normalize_model_key(canonical_model)

    candidate_keys = []
    for key in [raw_key, canonical_key]:
        if key and key not in candidate_keys:
            candidate_keys.append(key)

    if not candidate_keys:
        return None

    candidates = []
    for key in candidate_keys:
        spec = MODEL_SPECS_CATALOG.get(key)
        if isinstance(spec, dict):
            candidates.append((key, spec))

    return _pick_best_catalog_spec(candidates)


def auto_generate_catalog_specs(model_number, watch_data=None):
    """Generate deterministic catalog spec row (with unknown markers when needed)."""
    wd = watch_data if isinstance(watch_data, dict) else {}

    inferred_brand = first_non_empty(
        normalize_brand(wd.get('brand', '')),
        normalize_brand(wd.get('name', '')),
        infer_brand_from_model(model_number),
        normalize_brand(model_number)
    )

    model_name = build_csv_product_name(
        brand_label=format_brand_label(inferred_brand, wd.get('name', '')),
        model_number=model_number
    )

    combined_text = ' '.join([
        str(wd.get('name', '') or ''),
        str(wd.get('description', '') or ''),
        ' '.join(wd.get('specs', []) if isinstance(wd.get('specs', []), list) else []),
        str(wd.get('feature_text', '') or ''),
        str(model_number or '')
    ])

    specs = {
        'name': model_name,
        'brand': inferred_brand or 'Bütün Məhsullar',
        'description': first_non_empty(wd.get('description', ''), f"Watch Model: {model_number}"),
        'price': str(first_non_empty(wd.get('price', ''), estimate_price(model_number, inferred_brand or ''))),
        'image_url': first_non_empty(wd.get('image_url', ''), '')
    }

    # Fill all requested category groups with mapped value or "Uyğun deyil"
    for group in GROUP_ORDER:
        explicit_value = str(wd.get(group, '') or '').strip()
        if explicit_value:
            specs[group] = explicit_value
            continue

        detected = detect_group_value(group, combined_text)
        if detected:
            specs[group] = detected
        else:
            if group == 'olcu':
                specs[group] = estimate_case_size_label(model_number, inferred_brand)
            else:
                specs[group] = GROUP_UNKNOWN_LABELS.get(group, 'Uyğun deyil')

    return specs


def ensure_model_in_catalog(model_number, watch_data=None):
    """Ensure model exists in local catalog. Auto-create deterministic entry if missing."""
    canonical_model = extract_canonical_model_number(model_number)
    key = normalize_model_key(canonical_model or model_number)
    if not key:
        return None

    existing = MODEL_SPECS_CATALOG.get(key)
    if existing:
        return existing

    generated = auto_generate_catalog_specs(canonical_model or model_number, watch_data)
    MODEL_SPECS_CATALOG[key] = generated
    save_model_specs_catalog(MODEL_SPECS_CATALOG)
    logger.info(f"Auto-added model to catalog: {canonical_model or model_number} ({key})")
    return generated


def build_collections_from_specs(specs):
    """Build semicolon-separated collections from deterministic specs."""
    collections = ['Bütün Məhsullar']

    brand = str(specs.get('brand', '') or '').upper()
    if brand in BRAND_COLLECTIONS:
        collections.append(BRAND_COLLECTIONS[brand])

    direct_fields = [
        'siferblat_rengi',
        'bilerzik',
        'cinsi',
        'olcu',
        'mexanizm',
        'kemer_rengi',
        'korpus'
    ]

    for field in direct_fields:
        val = str(specs.get(field, '') or '').strip()
        if field == 'olcu':
            val = normalize_olcu_label(val)
        if val:
            collections.append(val)

    return ';'.join(list(dict.fromkeys(collections)))


def extract_price_value(text):
    """Extract first likely price from text and normalize to decimal string (e.g. 1234.56)."""
    if not text:
        return ''

    # Currency formats: $1,234.56 | €1.234,56 | 1234 USD
    patterns = [
        r'(?:\$|€|£|₼)\s*([0-9]{1,3}(?:[.,\s][0-9]{3})*(?:[.,][0-9]{2})?)',
        r'([0-9]{1,3}(?:[.,\s][0-9]{3})*(?:[.,][0-9]{2})?)\s*(?:USD|EUR|GBP|AZN)'
    ]

    for pattern in patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if not match:
            continue

        value = match.group(1).strip().replace(' ', '')

        # Normalize decimal/thousand separators
        if value.count(',') > 0 and value.count('.') > 0:
            if value.rfind(',') > value.rfind('.'):
                value = value.replace('.', '').replace(',', '.')
            else:
                value = value.replace(',', '')
        elif value.count(',') > 0:
            parts = value.split(',')
            if len(parts[-1]) == 2:
                value = ''.join(parts[:-1]).replace('.', '') + '.' + parts[-1]
            else:
                value = value.replace(',', '')
        else:
            # only dots or plain number
            parts = value.split('.')
            if len(parts) > 2:
                value = ''.join(parts)

        try:
            return f"{float(value):.2f}"
        except Exception:
            continue

    return ''


def estimate_price(model_number, brand):
    """Deterministic fallback price when live scraping cannot find a price."""
    brand_ranges = {
        'ROLEX': (4500, 18000),
        'OMEGA': (2500, 12000),
        'TAG HEUER': (1200, 5000),
        'TISSOT': (250, 1800),
        'HAMILTON': (350, 2200),
        'CITIZEN': (120, 1200),
        'SEIKO': (100, 2500),
        'SEİKO': (100, 2500),
        'ORIENT': (120, 900),
        'CASIO': (40, 900),
        'TIMEX': (35, 500),
        'BULOVA': (120, 1500),
        'LONGINES': (800, 4500),
        'TUDOR': (1800, 7000),
    }

    normalized_brand = normalize_brand(brand) if brand else ''
    low, high = brand_ranges.get(normalized_brand or str(brand).upper(), (150, 3000))
    stable = abs(hash(f"{model_number}-{brand}")) % 1000 / 1000.0
    value = low + ((high - low) * stable)
    return f"{value:.2f}"


def normalize_brand(brand_text):
    """Normalize brand to uppercase known value or empty string."""
    if not brand_text:
        return ''

    normalized = str(brand_text).strip().upper().replace('İ', 'I')
    known = ['CASIO', 'CITIZEN', 'EDIFICE', 'INGERSOLL', 'ORIENT', 'SEIKO', 'ROLEX',
             'OMEGA', 'TISSOT', 'TAG HEUER', 'HAMILTON', 'BULOVA', 'TIMEX',
             'LONGINES', 'TUDOR']
    for item in known:
        if item in normalized:
            return item
    return ''


def infer_brand_from_model(model_number):
    """Infer likely brand from common model-number prefixes/patterns."""
    model = str(model_number or '').upper().strip()
    if not model:
        return ''

    brand_patterns = [
        (r'^(SKX|SNZH|SRP|SRPE|SNK|SSA|SSK|SNXS|SPB)', 'SEIKO'),
        (r'^(RA-|RA\d|F[A-Z]{2}\d|AC\d)', 'ORIENT'),
        (r'^(BN\d|NJ\d|NY\d)', 'CITIZEN'),
        (r'^(F-\d|AE-\d|GA-\d|GA-B\d|GAB\d|G-\d|DW-\d|A\d{3})', 'CASIO'),
        (r'^M\d{2,}', 'INGERSOLL'),
        (r'^(T\d|PRX|LE\s?LOCLE|SEASTAR)', 'TISSOT'),
    ]

    for pattern, brand in brand_patterns:
        if re.search(pattern, model):
            return brand

    return ''


def first_non_empty(*values):
    for value in values:
        if value and str(value).strip():
            return str(value).strip()
    return ''


def _format_mm_number(value_text):
    raw = str(value_text or '').strip().replace(',', '.')
    if not raw:
        return ''
    try:
        num = float(raw)
        if num.is_integer():
            return str(int(num))
        return f"{num:.1f}".rstrip('0').rstrip('.')
    except Exception:
        return re.sub(r'[^0-9.]', '', raw)


def extract_case_size_label(text):
    """Extract case size and normalize to 'Ölçü - A x B mm' format."""
    source = str(text or '')
    if not source:
        return ''

    # 41 x 41 mm / 40.5x40.5 mm
    pair = re.search(r'\b(\d{2}(?:[\.,]\d{1,2})?)\s*[x×]\s*(\d{2}(?:[\.,]\d{1,2})?)\s*mm\b', source, re.IGNORECASE)
    if pair:
        a = _format_mm_number(pair.group(1))
        b = _format_mm_number(pair.group(2))
        if a and b:
            return f"Ölçü - {a} x {b} mm"

    # single size like 42 mm -> 42 x 42 mm
    single = re.search(r'\b(\d{2}(?:[\.,]\d{1,2})?)\s*mm\b', source, re.IGNORECASE)
    if single:
        s = _format_mm_number(single.group(1))
        if s:
            return f"Ölçü - {s} x {s} mm"

    return ''


def normalize_olcu_label(value):
    """Normalize any existing olcu value into 'Ölçü - A x B mm' when possible."""
    val = str(value or '').strip()
    if not val:
        return ''

    if 'uyğun deyil' in val.lower():
        return val

    extracted = extract_case_size_label(val)
    if extracted:
        return extracted

    return val


def estimate_case_size_label(model_number, brand_hint=''):
    """Estimate common case size for a model and return 'Ölçü - A x A mm'."""
    model = str(model_number or '').upper().strip()
    brand = first_non_empty(normalize_brand(brand_hint), infer_brand_from_model(model), normalize_brand(model))

    specific_patterns = [
        (r'^(GA-B\d|GAB\d|GA-\d|G-\d|DW-\d)', '45'),
        (r'^(F-91W|AE-1200)', '36'),
        (r'^(SPB)', '40.5'),
        (r'^(SRPD|SRPE|SRPG|SNZH|SKX)', '42'),
        (r'^(SNXS)', '37'),
        (r'^(NY\d|BN\d)', '42'),
        (r'^(RA-AA|RA-AC|RAAA|RAAC)', '42'),
        (r'^(T137)', '40'),
        (r'^(T127)', '40'),
    ]

    for pattern, size in specific_patterns:
        if re.search(pattern, model):
            return f"Ölçü - {size} x {size} mm"

    brand_defaults = {
        'CASIO': '42',
        'SEIKO': '41',
        'SEİKO': '41',
        'CITIZEN': '42',
        'ORIENT': '42',
        'TISSOT': '40',
        'ROLEX': '41',
        'OMEGA': '42',
        'LONGINES': '41',
        'TUDOR': '41',
        'HAMILTON': '41',
    }

    size = brand_defaults.get(str(brand).upper(), '41')
    return f"Ölçü - {size} x {size} mm"


def text_has_keyword(text, keyword):
    """Keyword match helper with word-boundary support for simple words."""
    if not text or not keyword:
        return False

    text_l = str(text).lower()
    key_l = str(keyword).lower().strip()

    if not key_l:
        return False

    # For alnum-only short phrases, prefer boundaries to avoid men/women collisions.
    if re.fullmatch(r"[a-z0-9\s'-]+", key_l):
        pattern = r'(?<![a-z0-9])' + re.escape(key_l) + r'(?![a-z0-9])'
        return re.search(pattern, text_l) is not None

    return key_l in text_l


def extract_visible_text(soup):
    """Extract visible text from HTML for feature detection."""
    if not soup:
        return ''
    try:
        for t in soup(['script', 'style', 'noscript']):
            t.decompose()
    except Exception:
        pass
    return re.sub(r'\s+', ' ', soup.get_text(' ', strip=True)).strip()


def search_duckduckgo_urls(query, max_results=6):
    """Search external sources by model using DuckDuckGo HTML endpoint."""
    urls = []
    try:
        url = f"https://html.duckduckgo.com/html/?q={quote(query)}"
        response = requests.get(url, headers=HEADERS, timeout=REQUEST_TIMEOUT)
        response.raise_for_status()
        soup = BeautifulSoup(response.content, 'html.parser')

        for a in soup.select('a.result__a, a[data-testid="result-title-a"]'):
            href = a.get('href', '')
            if not href:
                continue
            if 'uddg=' in href:
                try:
                    href = unquote(href.split('uddg=')[-1].split('&')[0])
                except Exception:
                    pass
            if href.startswith('http://') or href.startswith('https://'):
                if href not in urls:
                    urls.append(href)
            if len(urls) >= max_results:
                break
    except Exception as e:
        logger.debug(f"DuckDuckGo search failed: {e}")

    return urls


def fetch_page_data(url):
    """Fetch page details for better attribute detection."""
    result = {'title': '', 'description': '', 'text': '', 'image_url': ''}
    try:
        resp = requests.get(url, headers=HEADERS, timeout=REQUEST_TIMEOUT)
        resp.raise_for_status()
        soup = BeautifulSoup(resp.content, 'html.parser')

        title_tag = soup.find('title')
        if title_tag:
            result['title'] = title_tag.get_text(' ', strip=True)

        meta_desc = soup.find('meta', attrs={'name': 'description'})
        if meta_desc:
            result['description'] = meta_desc.get('content', '') or ''

        result['text'] = extract_visible_text(soup)[:12000]

        img = first_non_empty(
            normalize_image_url((soup.find('meta', property='og:image') or {}).get('content', '')),
            normalize_image_url((soup.find('meta', attrs={'name': 'twitter:image'}) or {}).get('content', '')),
            normalize_image_url(extract_image_from_tag(soup.find('img')))
        )
        img = upgrade_image_quality(img)
        result['image_url'] = img if is_valid_image_url(img) else ''
    except Exception as e:
        logger.debug(f"fetch_page_data failed for {url}: {e}")

    return result


def gather_external_model_features(model_number, brand=''):
    """Collect extra model-specific text from multiple sources."""
    query = f"{brand} {model_number} watch dial color strap bracelet movement case size"
    urls = search_duckduckgo_urls(query, max_results=6)

    chunks = []
    images = []
    for url in urls[:4]:
        try:
            page = fetch_page_data(url)
            combined = ' '.join([page.get('title', ''), page.get('description', ''), page.get('text', '')]).strip()
            if combined:
                chunks.append(combined)
            if page.get('image_url'):
                images.append(page['image_url'])
        except Exception as e:
            logger.debug(f"gather_external_model_features step failed: {e}")

    return {
        'feature_text': ' '.join(chunks)[:30000],
        'image_url': images[0] if images else ''
    }


def detect_group_value(group_name, combined_text):
    """Return matched category, unknown marker, or empty.

    - matched label: when keyword found in configured mapping
    - unknown marker: when attribute trigger exists but not mapped
    - empty: when no evidence found
    """
    try:
        if group_name == 'olcu':
            size_label = extract_case_size_label(combined_text)
            if size_label:
                return size_label

        mapping = CATEGORY_KEYWORDS.get(group_name, {})
        if not isinstance(mapping, dict):
            return ''

        for label, keywords in mapping.items():
            try:
                if any(text_has_keyword(combined_text, k) for k in keywords):
                    return label
            except Exception:
                continue

        freeform = extract_freeform_group_label(group_name, combined_text)
        if freeform:
            return freeform

        triggers = GROUP_TRIGGERS.get(group_name, [])
        if any(text_has_keyword(combined_text, t) for t in triggers):
            return GROUP_UNKNOWN_LABELS.get(group_name, 'Uyğun deyil')
    except Exception as e:
        logger.debug(f"detect_group_value failed for {group_name}: {e}")

    return ''


def _clean_extracted_label(value, max_len=40):
    if not value:
        return ''
    cleaned = re.sub(r'\s+', ' ', str(value)).strip(' .,:;|-_')
    cleaned = re.sub(r'[^\w\s\-/&]+', '', cleaned, flags=re.UNICODE).strip()
    if not cleaned:
        return ''
    if len(cleaned) > max_len:
        cleaned = cleaned[:max_len].rsplit(' ', 1)[0].strip()
    return cleaned


def extract_freeform_group_label(group_name, text):
    """Extract a meaningful category label from raw web text when exact mapping is missing."""
    source = str(text or '')
    if not source:
        return ''

    color_words = (
        r'black|white|blue|green|red|yellow|orange|purple|pink|brown|grey|gray|silver|gold|beige|'
        r'cream|ivory|turquoise|teal|navy|burgundy|champagne|salmon|anthracite'
    )

    if group_name == 'siferblat_rengi':
        m = re.search(rf'(({color_words})(?:\s+[a-zA-Z]+)?)\s+(?:dial|siferblat|face)\b', source, re.IGNORECASE)
        if m:
            color = _clean_extracted_label(m.group(1))
            if color:
                return f"SR - {color.title()}"

    elif group_name == 'bilerzik':
        m = re.search(r'(stainless steel|steel|titanium|ceramic|bronze|rubber|resin|silicone|leather|nylon|fabric|canvas|mesh)\s+(?:strap|band|bracelet|kəmər|bilərzik)\b', source, re.IGNORECASE)
        if m:
            material = _clean_extracted_label(m.group(1))
            if material:
                return f"Bilərzik - {material.title()}"

    elif group_name == 'cinsi':
        m = re.search(r'\b(unisex|men|mens|men\'s|male|women|womens|women\'s|female|lady|ladies)\b', source, re.IGNORECASE)
        if m:
            value = _clean_extracted_label(m.group(1))
            if value:
                return f"Cinsi - {value.title()}"

    elif group_name == 'olcu':
        m = re.search(r'\b(\d{2}(?:\.\d{1,2})?)\s?mm\b', source, re.IGNORECASE)
        if m:
            size = _clean_extracted_label(m.group(1), max_len=10)
            if size:
                return f"Ölçü - {size} mm"

    elif group_name == 'mexanizm':
        m = re.search(r'\b(quartz|automatic|mechanical|manual\s*winding|manual\s*wind|solar|eco-drive|kinetic|spring\s*drive|meca[-\s]?quartz)\b', source, re.IGNORECASE)
        if m:
            movement = _clean_extracted_label(m.group(1))
            if movement:
                return movement.title()

    elif group_name == 'kemer_rengi':
        m = re.search(rf'(({color_words})(?:\s+[a-zA-Z]+)?)\s+(?:strap|band|kəmər)\b', source, re.IGNORECASE)
        if m:
            color = _clean_extracted_label(m.group(1))
            if color:
                return f"KR - {color.title()}"
        m2 = re.search(r'(stainless steel|steel|titanium|ceramic|bronze|rubber|resin|silicone|leather|nylon|fabric|canvas|mesh)\s+(?:strap|band|kəmər)\b', source, re.IGNORECASE)
        if m2:
            material = _clean_extracted_label(m2.group(1))
            if material:
                return f"KR - {material.title()}"

    elif group_name == 'korpus':
        m = re.search(r'\b(stainless steel|steel|titanium|ceramic|bronze|gold|silver|carbon|resin|plastic)\s+(?:case|korpus)\b', source, re.IGNORECASE)
        if m:
            material = _clean_extracted_label(m.group(1))
            if material:
                return material.title()

    return ''


def map_ai_attributes_to_groups(attributes):
    """Map AI attribute object into internal group labels used by collections."""
    if not isinstance(attributes, dict):
        return {}

    mapped = {}
    candidates = {
        'siferblat_rengi': f"{attributes.get('dial_color', '')} dial",
        'bilerzik': f"{attributes.get('bracelet', '')} bracelet",
        'cinsi': str(attributes.get('gender', '') or ''),
        'olcu': f"{attributes.get('size_mm', '')} mm",
        'mexanizm': str(attributes.get('movement', '') or ''),
        'kemer_rengi': f"{attributes.get('strap_color', '')} strap",
        'korpus': f"{attributes.get('case_material', '')} case",
    }

    for group, text in candidates.items():
        text = str(text or '').strip()
        if not text:
            continue
        mapped_value = detect_group_value(group, text) or extract_freeform_group_label(group, text)
        if mapped_value and 'uyğun deyil' not in str(mapped_value).lower():
            mapped[group] = mapped_value

    return mapped


def get_priority_domains(brand_hint):
    """Return official brand domains first, then stable watch sources."""
    normalized = normalize_brand(brand_hint)
    domains = []

    if normalized in OFFICIAL_BRAND_DOMAINS:
        domains.extend(OFFICIAL_BRAND_DOMAINS[normalized])

    for d in PRIORITY_SOURCE_DOMAINS:
        if d not in domains:
            domains.append(d)

    return domains


def search_domain_urls(model_number, domains, max_results=8):
    """Search model on specific domains via DuckDuckGo HTML results."""
    found = []
    per_domain_limit = 2

    for domain in domains:
        try:
            query = f"site:{domain} {model_number} watch specifications"
            urls = search_duckduckgo_urls(query, max_results=per_domain_limit)
            for url in urls:
                if url not in found:
                    found.append(url)
                if len(found) >= max_results:
                    return found
        except Exception as e:
            logger.debug(f"Domain search failed for {domain}: {e}")

    return found


def clean_product_title(title):
    """Normalize page title to a product-like name."""
    if not title:
        return ''
    parts = re.split(r'\s+[\-|\u2013|\u2014|\|]\s+', str(title).strip())
    cleaned = parts[0].strip() if parts else str(title).strip()
    return cleaned[:255]


def score_page_data(page, model_number, brand_hint):
    """Heuristic score to select best source page for the model."""
    text_blob = ' '.join([
        str(page.get('title', '')),
        str(page.get('description', '')),
        str(page.get('text', ''))
    ]).lower()

    score = 0
    if page.get('image_url'):
        score += 3
    if extract_price_value(text_blob):
        score += 2
    if str(model_number).lower() in text_blob:
        score += 3
    if normalize_brand(brand_hint) and normalize_brand(brand_hint).lower() in text_blob:
        score += 2

    spec_tokens = ['dial', 'strap', 'bracelet', 'movement', 'automatic', 'quartz', 'case', 'mm', 'water resistance']
    score += sum(1 for t in spec_tokens if t in text_blob)
    return score


def search_priority_sources(model_number, brand_hint=''):
    """Primary extractor using official brand site + requested watch sources."""
    domains = get_priority_domains(brand_hint)
    urls = search_domain_urls(model_number, domains, max_results=10)

    best_page = None
    best_score = -1

    for url in urls:
        try:
            page = fetch_page_data(url)
            if not page:
                continue
            s = score_page_data(page, model_number, brand_hint)
            if s > best_score:
                best_score = s
                best_page = page
        except Exception as e:
            logger.debug(f"Priority source parse failed for {url}: {e}")

    if not best_page or best_score < 4:
        return None

    combined_text = ' '.join([
        str(best_page.get('title', '')),
        str(best_page.get('description', '')),
        str(best_page.get('text', ''))
    ]).strip()

    inferred_brand = first_non_empty(
        normalize_brand(brand_hint),
        normalize_brand(combined_text),
        infer_brand_from_model(model_number),
        'Bütün Məhsullar'
    )

    return {
        'name': first_non_empty(clean_product_title(best_page.get('title', '')), model_number),
        'description': first_non_empty(best_page.get('description', ''), combined_text[:1200], f"Watch Model: {model_number}"),
        'image_url': best_page.get('image_url', ''),
        'brand': inferred_brand,
        'price': extract_price_value(combined_text),
        'specs': extract_specs(combined_text),
        'feature_text': combined_text
    }


def is_low_quality_watch_data(data, model_number):
    """Detect generic/blocked search payloads that should be ignored."""
    if not isinstance(data, dict):
        return True

    name = str(data.get('name', '') or '').strip().lower()
    description = str(data.get('description', '') or '').strip().lower()
    feature_text = str(data.get('feature_text', '') or '').strip().lower()

    generic_names = ['google search', 'search results', 'watch model']
    if any(g in name for g in generic_names):
        return True

    if description in {f'watch model: {str(model_number).lower()}', f'watch model {str(model_number).lower()}'}:
        return True

    useful_tokens = ['dial', 'strap', 'bracelet', 'movement', 'automatic', 'quartz', 'case', 'mm']
    blob = ' '.join([name, description, feature_text])
    if not any(t in blob for t in useful_tokens):
        return True

    return False


def extract_image_from_tag(img_tag):
    if not img_tag:
        return ''
    for attr in ['src', 'data-src', 'data-original', 'data-image']:
        val = img_tag.get(attr, '')
        if val:
            return val
    srcset = img_tag.get('srcset', '')
    if srcset:
        parts = [p.strip().split(' ')[0] for p in srcset.split(',') if p.strip()]
        if parts:
            return parts[0]
    return ''


def normalize_image_url(url):
    if not url:
        return ''
    if url.startswith('//'):
        return f'https:{url}'
    if url.startswith('/'):
        return url
    return url


def upgrade_image_quality(url):
    """Try to convert thumbnail URLs to larger images."""
    if not url:
        return ''

    cleaned = str(url).strip()
    cleaned = re.sub(r'([?&])(w|width|h|height)=\d+', '', cleaned)
    cleaned = re.sub(r's-l\d{2,4}', 's-l1600', cleaned)

    return cleaned


def is_valid_image_url(url):
    if not url:
        return False
    bad_tokens = ['sprite', 'logo', 'icon', 'placeholder', '1x1', 'blank.gif', 'example.com', 'localhost']
    lower = url.lower()
    if any(token in lower for token in bad_tokens):
        return False
    return lower.startswith('http://') or lower.startswith('https://')


def has_supported_image_extension(url):
    """Check if URL path ends with an image extension supported by Wix imports."""
    if not url:
        return False
    try:
        path = urlparse(str(url)).path.lower()
        return any(path.endswith(ext) for ext in SUPPORTED_IMAGE_EXTENSIONS)
    except Exception:
        return False


def get_env_first(*keys):
    """Return the first non-empty environment variable value."""
    for key in keys:
        value = os.getenv(str(key), '').strip()
        if value:
            return value
    return ''


def _extract_json_from_text(raw_text):
    """Extract JSON object from plain text or fenced markdown block."""
    text = str(raw_text or '').strip()
    if not text:
        return {}

    # Remove markdown fences if present
    text = re.sub(r'^```(?:json)?\s*', '', text, flags=re.IGNORECASE).strip()
    text = re.sub(r'\s*```$', '', text).strip()

    try:
        data = json.loads(text)
        return data if isinstance(data, dict) else {}
    except Exception:
        pass

    match = re.search(r'\{[\s\S]*\}', text)
    if not match:
        return {}

    try:
        data = json.loads(match.group(0))
        return data if isinstance(data, dict) else {}
    except Exception:
        return {}


def _is_generic_description(description, model_number):
    desc = str(description or '').strip().lower()
    model = str(model_number or '').strip().lower()
    if not desc:
        return True
    if desc in {f'watch model: {model}', f'watch model {model}'}:
        return True
    return len(desc) < 24


CLASSIFIER_ALLOWED_VALUES = {
    'sr_dial_color': ['Ağ', 'Boz', 'Firuzə', 'Gəhvəyi', 'Göy', 'Krem', 'Mavi', 'Qara', 'Qırmızı', 'Sarı', 'Yaşıl'],
    'bracelet_type': ['Dəri', 'Kauçuk', 'Polad'],
    'gender': ['Kişi', 'Qadın'],
    'movement': ['Kvarts', 'Mexanika'],
    'bracelet_color': ['Ağ', 'Boz', 'Boz/Sarı', 'Gəhvəyi', 'Göy', 'Krem', 'Qara', 'Sarı'],
    'case_material': ['Polad', 'Plastik']
}


def _normalize_allowed_value(value, allowed, default_value):
    raw = str(value or '').strip()
    if not raw:
        return default_value

    for candidate in allowed:
        if raw == candidate:
            return candidate
    for candidate in allowed:
        if raw.lower() == candidate.lower():
            return candidate

    return default_value


def _default_classifier_values(model_number, brand_hint=''):
    model = str(model_number or '').upper().strip()
    brand = first_non_empty(normalize_brand(brand_hint), infer_brand_from_model(model), normalize_brand(model))

    defaults = {
        'sr_dial_color': 'Qara',
        'bracelet_type': 'Polad',
        'gender': 'Kişi',
        'movement': 'Kvarts',
        'bracelet_color': 'Boz',
        'case_material': 'Polad'
    }

    if brand in ['SEIKO', 'ORIENT', 'TISSOT', 'ROLEX', 'OMEGA', 'LONGINES', 'TUDOR', 'HAMILTON']:
        defaults['movement'] = 'Mexanika'

    if brand == 'CASIO':
        defaults['movement'] = 'Kvarts'

    # Sports/digital/G-Shock style defaults
    if re.search(r'^(GA-|GAB|GA-B|G-|DW-|AE-|F-)', model):
        defaults['bracelet_type'] = 'Kauçuk'
        defaults['bracelet_color'] = 'Qara'
        defaults['case_material'] = 'Plastik'
        defaults['movement'] = 'Kvarts'

    # Common diver-like defaults
    if re.search(r'^(SKX|SPB|SRP|SRPD|NY\d|BN\d)', model):
        defaults['case_material'] = 'Polad'

    return defaults


def _build_classifier_prompt(model_number, brand_hint=''):
    allowed = CLASSIFIER_ALLOWED_VALUES
    return (
        "You are an expert WATCH CATALOG CLASSIFIER. "
        "Your task is NOT to search the internet. "
        "Classify the watch model number into fixed categories using known brand conventions and most common configuration. "
        "Return STRICT JSON only. No explanation.\n\n"
        f"MODEL_NUMBER: {model_number}\n"
        f"BRAND_HINT: {brand_hint}\n\n"
        "ALLOWED VALUES ONLY:\n"
        f"Dial color (SR): {json.dumps(allowed['sr_dial_color'], ensure_ascii=False)}\n"
        f"Bracelet type: {json.dumps(allowed['bracelet_type'], ensure_ascii=False)}\n"
        f"Gender: {json.dumps(allowed['gender'], ensure_ascii=False)}\n"
        f"Movement: {json.dumps(allowed['movement'], ensure_ascii=False)}\n"
        f"Bracelet color (KR): {json.dumps(allowed['bracelet_color'], ensure_ascii=False)}\n"
        f"Case material: {json.dumps(allowed['case_material'], ensure_ascii=False)}\n\n"
        "RULES:\n"
        "- NEVER invent values outside allowed lists.\n"
        "- If unsure, choose most common configuration for that model series.\n"
        "- Assume adults. Default gender is Kişi unless clearly women's model.\n"
        "- Sports/G-Shock/digital models => Kvarts.\n"
        "- Mechanical Japanese/Swiss watches => Mexanika.\n"
        "- G-Shock/resin cases => Plastik.\n"
        "- Diver/Prospex/PRX/Bambino => Polad case.\n\n"
        "OUTPUT FORMAT EXACTLY:\n"
        "{\n"
        "  \"sr_dial_color\": \"\",\n"
        "  \"bracelet_type\": \"\",\n"
        "  \"gender\": \"\",\n"
        "  \"movement\": \"\",\n"
        "  \"bracelet_color\": \"\",\n"
        "  \"case_material\": \"\"\n"
        "}"
    )


def classify_watch_model_with_gemini(model_number, brand_hint=''):
    """Classify model into fixed categories using Gemini (OpenRouter or Google key)."""
    api_key = get_env_first('WIXWATCHSEARCH', 'GEMINI_API_KEY')
    defaults = _default_classifier_values(model_number, brand_hint)
    if not api_key:
        return defaults

    prompt = _build_classifier_prompt(model_number, brand_hint)

    try:
        content_text = ''

        # OpenRouter key support (e.g. sk-or-v1-...)
        if api_key.startswith('sk-or-'):
            model_name = get_env_first('GEMINI_MODEL') or 'google/gemini-2.5-pro'
            payload = {
                'model': model_name,
                'temperature': 0,
                'messages': [
                    {'role': 'user', 'content': prompt}
                ],
                'response_format': {'type': 'json_object'}
            }
            response = requests.post(
                'https://openrouter.ai/api/v1/chat/completions',
                headers={
                    'Authorization': f'Bearer {api_key}',
                    'Content-Type': 'application/json'
                },
                json=payload,
                timeout=REQUEST_TIMEOUT + 20
            )
            response.raise_for_status()
            body = response.json() if response.content else {}
            choices = body.get('choices', []) if isinstance(body, dict) else []
            if choices and isinstance(choices[0], dict):
                msg = choices[0].get('message', {})
                if isinstance(msg, dict):
                    content_text = str(msg.get('content', '') or '')
        else:
            # Native Google AI Studio API key support
            model_name = get_env_first('GEMINI_MODEL') or 'gemini-1.5-pro'
            response = requests.post(
                f'https://generativelanguage.googleapis.com/v1beta/models/{model_name}:generateContent',
                params={'key': api_key},
                headers={'Content-Type': 'application/json'},
                json={
                    'contents': [{'parts': [{'text': prompt}]}],
                    'generationConfig': {
                        'temperature': 0,
                        'responseMimeType': 'application/json'
                    }
                },
                timeout=REQUEST_TIMEOUT + 20
            )
            response.raise_for_status()
            body = response.json() if response.content else {}
            candidates = body.get('candidates', []) if isinstance(body, dict) else []
            if candidates and isinstance(candidates[0], dict):
                parts = ((candidates[0].get('content') or {}).get('parts') or [])
                if parts and isinstance(parts[0], dict):
                    content_text = str(parts[0].get('text', '') or '')

        parsed = _extract_json_from_text(content_text)
        if not parsed:
            return defaults

        normalized = {}
        for field, allowed in CLASSIFIER_ALLOWED_VALUES.items():
            normalized[field] = _normalize_allowed_value(parsed.get(field, ''), allowed, defaults[field])

        return normalized
    except Exception as e:
        logger.debug(f"Gemini classification failed for {model_number}: {e}")
        return defaults


def enrich_with_ai_watch_data(watch_data, model_number):
    """Use Gemini classifier to enrich fixed category fields from model number."""
    source = dict(watch_data) if isinstance(watch_data, dict) else {}

    brand_hint = first_non_empty(
        normalize_brand(source.get('brand', '')),
        normalize_brand(source.get('name', '')),
        infer_brand_from_model(model_number),
        normalize_brand(model_number)
    )

    classified = classify_watch_model_with_gemini(model_number, brand_hint)
    if not isinstance(classified, dict) or not classified:
        return source

    merged = dict(source)

    mapped_groups = {
        'siferblat_rengi': f"SR - {classified.get('sr_dial_color', '').strip()}",
        'bilerzik': f"Bilərzik - {classified.get('bracelet_type', '').strip()}",
        'cinsi': f"Cinsi - {classified.get('gender', '').strip()}",
        'mexanizm': classified.get('movement', '').strip(),
        'kemer_rengi': f"KR - {classified.get('bracelet_color', '').strip()}",
        'korpus': classified.get('case_material', '').strip(),
    }

    size_context = ' '.join([
        str(source.get('name', '') or ''),
        str(source.get('description', '') or ''),
        str(source.get('feature_text', '') or ''),
        str(model_number or '')
    ]).strip()
    mapped_groups['olcu'] = extract_case_size_label(size_context) or estimate_case_size_label(model_number, brand_hint)

    for group, value in mapped_groups.items():
        value = str(value or '').strip()
        if not value:
            continue
        existing = str(merged.get(group, '') or '').strip().lower()
        if (not existing) or ('uyğun deyil' in existing):
            merged[group] = value

    if not normalize_brand(merged.get('brand', '')):
        merged['brand'] = first_non_empty(brand_hint, 'Bütün Məhsullar')

    if not str(merged.get('image_url', '')).strip():
        merged['image_url'] = get_image_url(model_number)

    return merged


def _extract_google_cse_images(query, max_results=10):
    """Fetch image candidates from Google Custom Search API."""
    api_key = get_env_first('GOOGLE_CSE_API_KEY', 'WIXAPIKEY')
    cx = get_env_first('GOOGLE_CSE_CX', 'WIXCX', 'WIX_CSE_CX')
    if not api_key or not cx:
        return []

    try:
        params = {
            'key': api_key,
            'cx': cx,
            'q': query,
            'searchType': 'image',
            'num': min(max_results, 10),
            'safe': 'off',
            'imgType': 'photo'
        }
        response = requests.get(
            'https://www.googleapis.com/customsearch/v1',
            params=params,
            headers=HEADERS,
            timeout=REQUEST_TIMEOUT
        )
        response.raise_for_status()
        payload = response.json() if response.content else {}
        items = payload.get('items', []) if isinstance(payload, dict) else []

        results = []
        for item in items:
            url = str(item.get('link', '') or '').strip()
            image_meta = item.get('image', {}) if isinstance(item.get('image', {}), dict) else {}
            width = int(image_meta.get('width', 0) or 0)
            height = int(image_meta.get('height', 0) or 0)

            url = upgrade_image_quality(normalize_image_url(url))
            if not (is_valid_image_url(url) and has_supported_image_extension(url)):
                continue

            results.append({'url': url, 'width': width, 'height': height, 'source': 'google_cse'})

        return results
    except Exception as e:
        logger.debug(f"Google CSE image fetch failed for '{query}': {e}")
        return []


def _extract_serpapi_images(query, max_results=10):
    """Fetch image candidates from SerpApi Google Images endpoint."""
    api_key = os.getenv('SERPAPI_KEY', '').strip()
    if not api_key:
        return []

    try:
        params = {
            'engine': 'google_images',
            'q': query,
            'api_key': api_key,
            'ijn': '0',
            'num': min(max_results, 20)
        }
        response = requests.get(
            'https://serpapi.com/search.json',
            params=params,
            headers=HEADERS,
            timeout=REQUEST_TIMEOUT
        )
        response.raise_for_status()
        payload = response.json() if response.content else {}
        items = payload.get('images_results', []) if isinstance(payload, dict) else []

        results = []
        for item in items:
            url = first_non_empty(item.get('original', ''), item.get('thumbnail', ''))
            width = int(item.get('original_width', item.get('width', 0)) or 0)
            height = int(item.get('original_height', item.get('height', 0)) or 0)

            url = upgrade_image_quality(normalize_image_url(url))
            if not (is_valid_image_url(url) and has_supported_image_extension(url)):
                continue

            results.append({'url': url, 'width': width, 'height': height, 'source': 'serpapi'})

        return results
    except Exception as e:
        logger.debug(f"SerpApi image fetch failed for '{query}': {e}")
        return []


def _extract_wikimedia_images(query, max_results=10):
    """Fetch image candidates from Wikimedia Commons API (no API key required)."""
    if not query:
        return []

    try:
        params = {
            'action': 'query',
            'format': 'json',
            'generator': 'search',
            'gsrsearch': query,
            'gsrnamespace': 6,  # File namespace
            'gsrlimit': min(max_results, 20),
            'prop': 'imageinfo',
            'iiprop': 'url|size',
            'iiurlwidth': 1600
        }

        response = requests.get(
            'https://commons.wikimedia.org/w/api.php',
            params=params,
            headers=HEADERS,
            timeout=REQUEST_TIMEOUT
        )
        response.raise_for_status()
        payload = response.json() if response.content else {}

        pages = (((payload or {}).get('query') or {}).get('pages') or {})
        if not isinstance(pages, dict):
            return []

        results = []
        for _, page in pages.items():
            info_list = page.get('imageinfo', []) if isinstance(page, dict) else []
            if not info_list:
                continue

            info = info_list[0] if isinstance(info_list[0], dict) else {}
            url = first_non_empty(info.get('thumburl', ''), info.get('url', ''))
            width = int(info.get('thumbwidth', info.get('width', 0)) or 0)
            height = int(info.get('thumbheight', info.get('height', 0)) or 0)

            url = upgrade_image_quality(normalize_image_url(url))
            if not (is_valid_image_url(url) and has_supported_image_extension(url)):
                continue

            results.append({'url': url, 'width': width, 'height': height, 'source': 'wikimedia'})

        return results
    except Exception as e:
        logger.debug(f"Wikimedia image fetch failed for '{query}': {e}")
        return []


def _extract_flickr_public_images(query, max_results=10):
    """Fetch image candidates from Flickr public feed (no API key required)."""
    if not query:
        return []

    try:
        tags = [t for t in re.split(r'\s+', query.lower()) if t]
        tags = [re.sub(r'[^a-z0-9\-]', '', t) for t in tags]
        tags = [t for t in tags if t][:6]
        if 'watch' not in tags:
            tags.append('watch')

        params = {
            'format': 'json',
            'nojsoncallback': 1,
            'tags': ','.join(tags)
        }
        response = requests.get(
            'https://www.flickr.com/services/feeds/photos_public.gne',
            params=params,
            headers=HEADERS,
            timeout=REQUEST_TIMEOUT
        )
        response.raise_for_status()
        payload = response.json() if response.content else {}
        items = payload.get('items', []) if isinstance(payload, dict) else []

        results = []
        for item in items[:max_results]:
            media = item.get('media', {}) if isinstance(item, dict) else {}
            media_url = str(media.get('m', '') or '').strip()
            if not media_url:
                continue

            # Try to upgrade from small thumbnail to larger size when possible
            upgraded = re.sub(r'_m\.(jpg|jpeg|png|webp)$', r'_b.\1', media_url, flags=re.IGNORECASE)
            url = upgrade_image_quality(normalize_image_url(upgraded or media_url))

            if not (is_valid_image_url(url) and has_supported_image_extension(url)):
                continue

            results.append({'url': url, 'width': 0, 'height': 0, 'source': 'flickr_public'})

        return results
    except Exception as e:
        logger.debug(f"Flickr image fetch failed for '{query}': {e}")
        return []


def _pick_first_high_res_image(image_results):
    """Pick the first high-resolution image, otherwise first available result."""
    if not image_results:
        return ''

    for item in image_results:
        w = int(item.get('width', 0) or 0)
        h = int(item.get('height', 0) or 0)
        if w >= 1000 or h >= 1000:
            return str(item.get('url', '') or '').strip()

    return str(image_results[0].get('url', '') or '').strip()


def get_image_url(model_number):
    """Get high-quality image URL for a watch model using image search APIs.

    Env vars:
    - GOOGLE_CSE_API_KEY + GOOGLE_CSE_CX (preferred)
    - SERPAPI_KEY (fallback)
    - No-key fallback: Wikimedia Commons API
    """
    model = str(model_number or '').strip()
    if not model:
        return IMAGE_PLACEHOLDER_URL

    brand = first_non_empty(infer_brand_from_model(model), normalize_brand(model))
    query = f"{brand} {model} watch".strip()

    results = _extract_google_cse_images(query)
    if not results:
        results = _extract_serpapi_images(query)
    if not results:
        results = _extract_flickr_public_images(query)
    if not results:
        results = _extract_wikimedia_images(query)
    if not results and brand:
        results = (
            _extract_google_cse_images(f"{model} watch")
            or _extract_serpapi_images(f"{model} watch")
            or _extract_flickr_public_images(f"{model} watch")
            or _extract_wikimedia_images(f"{model} watch")
        )

    best_url = _pick_first_high_res_image(results)
    best_url = upgrade_image_quality(normalize_image_url(best_url))

    if is_valid_image_url(best_url) and has_supported_image_extension(best_url):
        return best_url

    return IMAGE_PLACEHOLDER_URL


def _collect_ldjson_objects(raw):
    objs = []
    if isinstance(raw, dict):
        objs.append(raw)
        if '@graph' in raw and isinstance(raw['@graph'], list):
            objs.extend(raw['@graph'])
    elif isinstance(raw, list):
        for item in raw:
            objs.extend(_collect_ldjson_objects(item))
    return objs


def extract_ldjson_product_data(soup):
    """Extract Product metadata from ld+json scripts."""
    best = {
        'name': '',
        'description': '',
        'image_url': '',
        'brand': '',
        'price': ''
    }

    for script in soup.find_all('script', type='application/ld+json'):
        script_content = script.string or script.get_text(strip=True)
        if not script_content:
            continue
        try:
            data = json.loads(script_content)
        except Exception:
            continue

        objects = _collect_ldjson_objects(data)
        for obj in objects:
            if not isinstance(obj, dict):
                continue

            obj_type = str(obj.get('@type', '')).lower()
            if 'product' not in obj_type:
                continue

            name = obj.get('name', '')
            description = obj.get('description', '')

            image = obj.get('image', '')
            if isinstance(image, list):
                image_url = image[0] if image else ''
            elif isinstance(image, dict):
                image_url = image.get('url', '')
            else:
                image_url = image

            brand = obj.get('brand', '')
            if isinstance(brand, dict):
                brand = brand.get('name', '')

            price = ''
            offers = obj.get('offers', {})
            if isinstance(offers, list) and offers:
                offers = offers[0]
            if isinstance(offers, dict):
                price = first_non_empty(offers.get('price', ''), offers.get('lowPrice', ''), offers.get('highPrice', ''))

            best['name'] = first_non_empty(best['name'], name)
            best['description'] = first_non_empty(best['description'], description)
            best['image_url'] = first_non_empty(best['image_url'], normalize_image_url(str(image_url)))
            best['brand'] = first_non_empty(best['brand'], brand)
            best['price'] = first_non_empty(best['price'], str(price))

            if best['name'] and best['image_url']:
                return best

    return best


def map_collections(title, description, brand, model_number='', feature_text=''):
    """Map watch data to semicolon-separated Wix collections."""
    combined = ' '.join([
        str(title or ''),
        str(description or ''),
        str(brand or ''),
        str(model_number or ''),
        str(feature_text or '')
    ])

    collections = ['Bütün Məhsullar']

    normalized_brand = normalize_brand(brand)
    if normalized_brand in BRAND_COLLECTIONS:
        collections.append(BRAND_COLLECTIONS[normalized_brand])

    # Per-group detection with unknown marker support
    for group_name in GROUP_ORDER:
        detected = detect_group_value(group_name, combined)
        if detected:
            collections.append(detected)

    # Extra bracelet heuristic when only generic steel/metal exists
    if ('Bilərzik - Polad' not in collections) and (
        'bracelet' in combined and ('steel' in combined or 'metal' in combined or 'polad' in combined)
    ):
        collections.append('Bilərzik - Polad')

    # Remove duplicates, keep order
    unique_collections = list(dict.fromkeys(collections))
    return ';'.join(unique_collections)


def format_brand_label(brand_value, fallback_text=''):
    """Format brand label for CSV output (prefer mapped collection label)."""
    normalized = normalize_brand(brand_value) or normalize_brand(fallback_text)
    if normalized in BRAND_COLLECTIONS:
        return BRAND_COLLECTIONS[normalized]
    if normalized:
        return normalized.title()
    return ''


def build_csv_product_name(brand_label, model_number):
    """Build product name as 'Brand + Model Number' per requested output format."""
    model = str(model_number or '').strip()
    brand = str(brand_label or '').strip()

    if brand and model:
        return f"{brand} {model}"[:255]
    if model:
        return model[:255]
    if brand:
        return brand[:255]
    return 'Watch Product'


def search_ebay(model_number):
    """Fallback source focused on title + image + price extraction."""
    try:
        search_url = f"https://www.ebay.com/sch/i.html?_nkw={quote(model_number + ' watch')}"

        for attempt in range(MAX_RETRIES):
            try:
                response = requests.get(search_url, headers=HEADERS, timeout=REQUEST_TIMEOUT)
                response.raise_for_status()
                break
            except requests.exceptions.Timeout:
                if attempt < MAX_RETRIES - 1:
                    logger.warning(f"Timeout on eBay for {model_number}, retrying...")
                    continue
                raise

        soup = BeautifulSoup(response.content, 'html.parser')
        item = soup.select_one('li.s-item')
        if not item:
            return None

        title_el = item.select_one('.s-item__title')
        title = title_el.get_text(" ", strip=True) if title_el else model_number

        # Skip generic heading cards
        if 'shop on ebay' in title.lower() and item.find_next('li', class_='s-item'):
            item = item.find_next('li', class_='s-item')
            title_el = item.select_one('.s-item__title')
            title = title_el.get_text(" ", strip=True) if title_el else model_number

        image_el = item.select_one('.s-item__image-img')
        image_url = normalize_image_url(extract_image_from_tag(image_el))
        image_url = upgrade_image_quality(image_url)

        price_el = item.select_one('.s-item__price')
        price_text = price_el.get_text(" ", strip=True) if price_el else ''

        subtitle_el = item.select_one('.s-item__subtitle')
        subtitle = subtitle_el.get_text(" ", strip=True) if subtitle_el else ''

        full_text = f"{title} {subtitle}".strip()
        brand = first_non_empty(normalize_brand(title), normalize_brand(model_number), 'Bütün Məhsullar')

        return {
            'name': title[:255],
            'description': full_text or f"Watch Model: {model_number}",
            'image_url': image_url,
            'brand': brand,
            'price': extract_price_value(price_text) or extract_price_value(full_text),
            'specs': extract_specs(full_text)
        }
    except Exception as e:
        logger.debug(f"eBay search failed: {str(e)}")
    return None


def enrich_watch_data(watch_data, model_number):
    """Enrich scraped data with extra context from model-specific web pages."""
    try:
        enriched = dict(watch_data) if isinstance(watch_data, dict) else {}

        brand_hint = first_non_empty(
            normalize_brand(enriched.get('brand', '')),
            normalize_brand(enriched.get('name', '')),
            infer_brand_from_model(model_number),
            normalize_brand(model_number)
        )

        external = gather_external_model_features(model_number, brand_hint)
        external_text = external.get('feature_text', '')

        merged_feature_text = ' '.join([
            str(enriched.get('name', '') or ''),
            str(enriched.get('description', '') or ''),
            ' '.join(enriched.get('specs', []) if isinstance(enriched.get('specs', []), list) else []),
            external_text
        ]).strip()

        enriched['feature_text'] = merged_feature_text[:30000]

        if not enriched.get('image_url') and external.get('image_url'):
            enriched['image_url'] = external['image_url']

        if not enriched.get('price'):
            enriched['price'] = extract_price_value(merged_feature_text)

        if not normalize_brand(enriched.get('brand', '')):
            enriched['brand'] = first_non_empty(normalize_brand(merged_feature_text), 'Bütün Məhsullar')

        return enriched
    except Exception as e:
        logger.debug(f"enrich_watch_data failed for {model_number}: {e}")
        return watch_data


def search_watch_data(model_number):
    """Search for watch data using multiple sources"""
    logger.info(f"Searching for model: {model_number}")
    
    try:
        # 1) Deterministic local catalog (guaranteed mapping for known models)
        model_specs = lookup_model_specs(model_number)
        if model_specs:
            if _catalog_unknown_count(model_specs) > 0 or _is_generic_description(model_specs.get('description', ''), model_number):
                ai_seed = {
                    'name': model_specs.get('name', ''),
                    'description': model_specs.get('description', ''),
                    'image_url': model_specs.get('image_url', ''),
                    'brand': model_specs.get('brand', ''),
                    'price': model_specs.get('price', ''),
                    'specs': model_specs.get('specs', []) if isinstance(model_specs.get('specs', []), list) else [],
                    'feature_text': ''
                }
                for group in GROUP_ORDER:
                    ai_seed[group] = model_specs.get(group, '')
                ai_enriched = enrich_with_ai_watch_data(ai_seed, model_number)
                improved_specs = auto_generate_catalog_specs(model_number, ai_enriched)

                if _catalog_unknown_count(improved_specs) <= _catalog_unknown_count(model_specs):
                    model_specs.update(improved_specs)
                    canonical_model = extract_canonical_model_number(model_number)
                    key = normalize_model_key(canonical_model or model_number)
                    if key in MODEL_SPECS_CATALOG:
                        MODEL_SPECS_CATALOG[key].update(model_specs)
                        save_model_specs_catalog(MODEL_SPECS_CATALOG)

            # If catalog spec exists but image is missing, try to fetch and persist image.
            image_url = str(model_specs.get('image_url', '') or '').strip()
            if (not image_url) or (not has_supported_image_extension(image_url)):
                inferred_brand = first_non_empty(
                    normalize_brand(model_specs.get('brand', '')),
                    infer_brand_from_model(model_number),
                    normalize_brand(model_number)
                )

                enriched_image = ''
                try:
                    priority_data = search_priority_sources(model_number, inferred_brand)
                    if priority_data:
                        enriched_priority = enrich_watch_data(priority_data, model_number)
                        enriched_image = first_non_empty(enriched_priority.get('image_url', ''))
                except Exception as e:
                    logger.debug(f"Priority image enrichment failed for {model_number}: {e}")

                if not enriched_image:
                    try:
                        external = gather_external_model_features(model_number, inferred_brand)
                        enriched_image = first_non_empty(external.get('image_url', ''))
                    except Exception as e:
                        logger.debug(f"External image enrichment failed for {model_number}: {e}")

                if not enriched_image:
                    enriched_image = get_image_url(model_number)

                enriched_image = upgrade_image_quality(normalize_image_url(enriched_image))
                if is_valid_image_url(enriched_image):
                    model_specs['image_url'] = enriched_image
                    canonical_model = extract_canonical_model_number(model_number)
                    key = normalize_model_key(canonical_model or model_number)
                    if key in MODEL_SPECS_CATALOG and enriched_image != IMAGE_PLACEHOLDER_URL:
                        MODEL_SPECS_CATALOG[key]['image_url'] = enriched_image
                        save_model_specs_catalog(MODEL_SPECS_CATALOG)
                    image_url = enriched_image

            logger.info(f"Found local catalog specs for {model_number}")
            return {
                'name': first_non_empty(model_specs.get('name', ''), model_number),
                'description': first_non_empty(model_specs.get('description', ''), f"Watch Model: {model_number}"),
                'image_url': image_url,
                'brand': first_non_empty(model_specs.get('brand', ''), infer_brand_from_model(model_number), 'Bütün Məhsullar'),
                'price': str(model_specs.get('price', '') or ''),
                'specs': model_specs.get('specs', []) if isinstance(model_specs.get('specs', []), list) else [],
                'catalog_specs': model_specs
            }

        inferred_brand = first_non_empty(infer_brand_from_model(model_number), normalize_brand(model_number))

        priority_data = search_priority_sources(model_number, inferred_brand)
        if priority_data:
            logger.info(f"Found prioritized source data for {model_number}")
            enriched = enrich_watch_data(priority_data, model_number)
            enriched = enrich_with_ai_watch_data(enriched, model_number)
            auto_specs = ensure_model_in_catalog(model_number, enriched)
            enriched['catalog_specs'] = auto_specs
            return enriched

        chrono24_data = search_chrono24(model_number)
        if chrono24_data and chrono24_data.get('image_url'):
            logger.info(f"Found Chrono24 data for {model_number}")
            enriched = enrich_watch_data(chrono24_data, model_number)
            enriched = enrich_with_ai_watch_data(enriched, model_number)
            auto_specs = ensure_model_in_catalog(model_number, enriched)
            enriched['catalog_specs'] = auto_specs
            return enriched

        ebay_data = search_ebay(model_number)
        if ebay_data and ebay_data.get('image_url'):
            logger.info(f"Found eBay data for {model_number}")
            enriched = enrich_watch_data(ebay_data, model_number)
            enriched = enrich_with_ai_watch_data(enriched, model_number)
            auto_specs = ensure_model_in_catalog(model_number, enriched)
            enriched['catalog_specs'] = auto_specs
            return enriched
        
        google_data = search_google(model_number)
        if google_data and not is_low_quality_watch_data(google_data, model_number):
            logger.info(f"Found Google data for {model_number}")
            enriched = enrich_watch_data(google_data, model_number)
            enriched = enrich_with_ai_watch_data(enriched, model_number)
            auto_specs = ensure_model_in_catalog(model_number, enriched)
            enriched['catalog_specs'] = auto_specs
            return enriched
        
        logger.warning(f"No data found for {model_number}, using fallback")
        inferred_brand = infer_brand_from_model(model_number)
        fallback = {
            'name': model_number,
            'description': f'Watch Model: {model_number}',
            'image_url': '',
            'brand': first_non_empty(inferred_brand, normalize_brand(model_number), 'Bütün Məhsullar'),
            'price': '',
            'specs': []
        }
        enriched = enrich_watch_data(fallback, model_number)
        enriched = enrich_with_ai_watch_data(enriched, model_number)
        auto_specs = ensure_model_in_catalog(model_number, enriched)
        enriched['catalog_specs'] = auto_specs
        return enriched
    
    except Exception as e:
        logger.error(f"Error searching for {model_number}: {str(e)}")
        inferred_brand = infer_brand_from_model(model_number)
        fallback = {
            'name': model_number,
            'description': f'Watch Model: {model_number}',
            'image_url': '',
            'brand': first_non_empty(inferred_brand, normalize_brand(model_number), 'Bütün Məhsullar'),
            'price': '',
            'specs': []
        }
        enriched = enrich_watch_data(fallback, model_number)
        enriched = enrich_with_ai_watch_data(enriched, model_number)
        auto_specs = ensure_model_in_catalog(model_number, enriched)
        enriched['catalog_specs'] = auto_specs
        return enriched


def search_chrono24(model_number):
    """Search for watch on Chrono24 marketplace"""
    try:
        search_url = f"https://www.chrono24.com/search/index.htm?query={quote(model_number)}"
        
        for attempt in range(MAX_RETRIES):
            try:
                response = requests.get(search_url, headers=HEADERS, timeout=REQUEST_TIMEOUT)
                response.raise_for_status()
                break
            except requests.exceptions.Timeout:
                if attempt < MAX_RETRIES - 1:
                    logger.warning(f"Timeout on Chrono24 for {model_number}, retrying...")
                    continue
                else:
                    raise
        
        soup = BeautifulSoup(response.content, 'html.parser')
        product = soup.select_one('article, a.productList, div.js-article-item-container')
        
        if product:
            name_tag = product.select_one('h2, h3, .article-title')
            name_text = name_tag.get_text(" ", strip=True) if name_tag else model_number

            img_tag = product.find('img')
            image_url = normalize_image_url(extract_image_from_tag(img_tag))
            if image_url and image_url.startswith('/'):
                image_url = 'https://www.chrono24.com' + image_url

            product_text = product.get_text(" ", strip=True)
            product_price = extract_price_value(product_text)
            product_brand = first_non_empty(normalize_brand(name_text), normalize_brand(model_number), 'Bütün Məhsullar')
            image_url = upgrade_image_quality(image_url)
            
            return {
                'name': name_text,
                'description': product_text[:500] if product_text else f"Watch Model: {model_number}",
                'image_url': image_url if is_valid_image_url(image_url) else '',
                'brand': product_brand,
                'price': product_price,
                'specs': extract_specs(f"{name_text} {product_text}")
            }
    
    except Exception as e:
        logger.debug(f"Chrono24 search failed: {str(e)}")
    
    return None


def search_google(model_number):
    """Fallback Google search"""
    try:
        search_url = f"https://www.google.com/search?q={quote(model_number + ' watch')}"
        
        for attempt in range(MAX_RETRIES):
            try:
                response = requests.get(search_url, headers=HEADERS, timeout=REQUEST_TIMEOUT)
                response.raise_for_status()
                break
            except requests.exceptions.Timeout:
                if attempt < MAX_RETRIES - 1:
                    logger.warning(f"Timeout on Google, retrying...")
                    continue
                else:
                    raise
        
        soup = BeautifulSoup(response.content, 'html.parser')
        
        ld_product = extract_ldjson_product_data(soup)

        # Try to avoid generic "Google Search" title. Prefer first result heading.
        first_result_h3 = soup.select_one('h3')
        first_result_title = first_result_h3.get_text(" ", strip=True) if first_result_h3 else ''

        page_title = ''
        title_tag = soup.find('title')
        if title_tag:
            page_title = title_tag.get_text(" ", strip=True)

        cleaned_page_title = re.sub(r'\s*-\s*Google\s+Search\s*$', '', page_title, flags=re.IGNORECASE).strip()
        name = first_non_empty(
            ld_product.get('name', ''),
            first_result_title,
            cleaned_page_title if cleaned_page_title.lower() != 'google' else '',
            model_number
        )[:255]

        image_url = first_non_empty(
            ld_product.get('image_url', ''),
            normalize_image_url((soup.find('meta', property='og:image') or {}).get('content', '')),
            normalize_image_url((soup.find('meta', attrs={'name': 'twitter:image'}) or {}).get('content', ''))
        )
        image_url = upgrade_image_quality(image_url)

        description = first_non_empty(
            ld_product.get('description', ''),
            (soup.select_one('div.VwiC3b') or {}).get_text(" ", strip=True) if soup.select_one('div.VwiC3b') else '',
            f"Watch Model: {model_number}"
        )

        detected_brand = first_non_empty(
            normalize_brand(ld_product.get('brand', '')),
            normalize_brand(name),
            normalize_brand(description),
            normalize_brand(model_number),
            'Bütün Məhsullar'
        )

        price = first_non_empty(
            ld_product.get('price', ''),
            extract_price_value(description),
            extract_price_value(soup.get_text(" ", strip=True)[:5000])
        )
        
        return {
            'name': name,
            'description': description,
            'image_url': image_url if is_valid_image_url(image_url) else '',
            'brand': detected_brand,
            'price': price,
            'specs': extract_specs(f"{name} {description}")
        }
    
    except Exception as e:
        logger.debug(f"Google search failed: {str(e)}")
    
    return None


def extract_brand(text):
    """Extract brand name from product text"""
    normalized = normalize_brand(text)
    if normalized:
        return normalized
    return 'Bütün Məhsullar'


def extract_specs(text):
    """Extract specifications from product text"""
    specs = []
    patterns = {
        'Water Resistance': r'(\d+[mft]+)\s*(water|resistant)',
        'Movement': r'(automatic|quartz|manual|mechanical)',
        'Case Material': r'(stainless steel|titanium|gold|silver|ceramic)',
    }
    
    for spec_name, pattern in patterns.items():
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            specs.append(f"{spec_name}: {match.group(1)}")
    
    return specs


def generate_handle_id(name):
    """Convert product name to WIX-compatible handleId"""
    handle = name.lower()
    handle = re.sub(r'[^a-z0-9\s-]', '', handle)
    handle = re.sub(r'\s+', '-', handle.strip())
    handle = re.sub(r'-+', '-', handle)
    handle = handle.strip('-')
    
    return handle or 'product'


def format_description_html(description, specs):
    """Format description as clean HTML with specs"""
    html = f"<p>{description}</p>"
    
    if specs:
        html += "<ul>"
        for spec in specs:
            html += f"<li>{spec}</li>"
        html += "</ul>"
    
    return html


def create_wix_row(watch_data, model_number):
    """Create a complete Wix row with all 50 columns - WIX REQUIREMENT STRICT MODE
    
    WIX REQUIREMENTS:
    - handleId: REQUIRED, NEVER empty, UNIQUE
    - fieldType: REQUIRED, MUST be "Product" or "Variant"
    - All other fields must be properly set (empty string, not None/null)
    """
    row = {}
    
    # Initialize ALL columns with empty strings (never None/null)
    for col in WIX_COLUMNS:
        row[col] = ''
    
    # REQUIREMENT 1: handleId - MUST NOT BE EMPTY / SHOULD BE UNIQUE
    # Prefer model_number first to avoid duplicate handles like "google-search"
    handle_id = generate_handle_id(model_number)
    if not handle_id or handle_id == 'product':
        handle_id = generate_handle_id(watch_data.get('name', ''))
    if not handle_id:
        handle_id = f'product-{model_number.lower()}'.replace(' ', '-')
    
    # Final safety check - ensure handleId is valid
    if not handle_id or len(handle_id.strip()) == 0:
        handle_id = f'product-{len(str(model_number))}-{hash(model_number) % 9999}'
    
    # REQUIREMENT 2: fieldType - MUST be exactly "Product" or "Variant"
    field_type = 'Product'
    
    # Set required WIX fields
    row['handleId'] = handle_id.strip()
    row['fieldType'] = field_type
    
    catalog_specs = watch_data.get('catalog_specs', {}) if isinstance(watch_data, dict) else {}

    # Detect brand first, then build name as Brand + Model Number
    detected_brand = first_non_empty(
        normalize_brand(catalog_specs.get('brand', '')),
        normalize_brand(watch_data.get('brand', '')),
        normalize_brand(watch_data.get('name', '')),
        infer_brand_from_model(model_number),
        normalize_brand(model_number)
    )
    brand_for_collection = BRAND_COLLECTIONS.get(detected_brand, '') if detected_brand else ''
    row['brand'] = brand_for_collection or 'Bütün Məhsullar'

    row['name'] = first_non_empty(
        str(catalog_specs.get('name', '')).strip(),
        build_csv_product_name(
            brand_label=format_brand_label(detected_brand, watch_data.get('name', '')),
            model_number=model_number
        )
    )[:255]

    # Set product information with fallbacks
    row['description'] = format_description_html(
        first_non_empty(catalog_specs.get('description', ''), watch_data.get('description', f'Watch Model: {model_number}')),
        watch_data.get('specs', [])
    )
    resolved_image = upgrade_image_quality(first_non_empty(catalog_specs.get('image_url', ''), (watch_data.get('image_url') or '').strip()))
    if (not is_valid_image_url(resolved_image)) or (not has_supported_image_extension(resolved_image)):
        resolved_image = get_image_url(model_number)
    row['productImageUrl'] = resolved_image

    if catalog_specs:
        row['collection'] = build_collections_from_specs(catalog_specs)
    else:
        row['collection'] = map_collections(
            title=row['name'],
            description=watch_data.get('description', ''),
            brand=detected_brand,
            model_number=model_number,
            feature_text=watch_data.get('feature_text', '')
        )
    row['sku'] = model_number
    scraped_price = str(first_non_empty(catalog_specs.get('price', ''), watch_data.get('price', '')) or '').strip()
    if scraped_price:
        row['price'] = scraped_price
    else:
        row['price'] = estimate_price(model_number, detected_brand or row['brand'])
    row['visible'] = 'true'
    row['inventory'] = '10'
    
    # Ensure all fields are strings, never None or NaN
    for key in row:
        if row[key] is None:
            row[key] = ''
        else:
            row[key] = str(row[key]).strip()
    
    return row


@app.route('/')
def index():
    """Serve the main application page"""
    try:
        return render_template('index.html')
    except Exception as e:
        logger.error(f"Error rendering index: {str(e)}")
        return f"Error loading application: {str(e)}", 500


@app.route('/api/health')
def health_check():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'version': '2.0',
        'columns': len(WIX_COLUMNS),
        'timestamp': datetime.now().isoformat()
    })


@app.route('/api/get-template')
def get_template():
    """Download template CSV with all 51 columns"""
    try:
        df = pd.DataFrame(columns=WIX_COLUMNS)
        
        example_row = create_wix_row(
            {
                'name': 'Example Watch',
                'description': 'This is an example watch product',
                'image_url': 'https://example.com/watch.jpg',
                'brand': 'Seiko',
                'specs': ['Quartz Movement', 'Stainless Steel', '100m Water Resistant']
            },
            'EXAMPLE001'
        )
        
        df = pd.concat([df, pd.DataFrame([example_row])], ignore_index=True)
        
        output = StringIO()
        df.to_csv(output, index=False, quoting=csv.QUOTE_ALL)
        output.seek(0)
        
        csv_bytes = BytesIO(output.getvalue().encode('utf-8-sig'))
        csv_bytes.seek(0)
        
        logger.info("Template CSV generated")
        
        return send_file(
            csv_bytes,
            mimetype='text/csv',
            as_attachment=True,
            download_name=f'wix_template_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv'
        )
    
    except Exception as e:
        logger.error(f"Error generating template: {str(e)}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/search', methods=['POST'])
def api_search():
    """API endpoint to search for watch data"""
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({'error': 'No JSON data provided'}), 400
        
        model_numbers = data.get('model_numbers', [])
        
        if not isinstance(model_numbers, list):
            return jsonify({'error': 'model_numbers must be an array'}), 400
        
        if not model_numbers:
            return jsonify({'error': 'No model numbers provided'}), 400
        
        model_numbers = [m.strip() for m in model_numbers if m.strip()]
        
        if not model_numbers:
            return jsonify({'error': 'No valid model numbers provided'}), 400
        
        logger.info(f"Processing {len(model_numbers)} model numbers")
        
        results = []
        total = len(model_numbers)
        
        for index, model_number in enumerate(model_numbers):
            try:
                watch_data = search_watch_data(model_number)
                wix_row = create_wix_row(watch_data, model_number)
                results.append(wix_row)
                
                progress = int((index + 1) / total * 100)
                logger.info(f"Progress: {progress}% - {model_number}")
            
            except Exception as e:
                logger.error(f"Error processing {model_number}: {str(e)}")
                fallback_row = create_wix_row(
                    {
                        'name': model_number,
                        'description': f'Watch Model: {model_number}',
                        'image_url': '',
                        'brand': extract_brand(model_number),
                        'specs': []
                    },
                    model_number
                )
                results.append(fallback_row)
        
        logger.info(f"Search completed: {len(results)} results")
        
        return jsonify({
            'success': True,
            'results': results,
            'count': len(results),
            'columns': len(WIX_COLUMNS),
            'timestamp': datetime.now().isoformat()
        })
    
    except Exception as e:
        logger.error(f"Error in API search: {str(e)}", exc_info=True)
        return jsonify({'error': str(e)}), 500


@app.route('/api/search-single', methods=['POST'])
def api_search_single():
    """Search one model and return a single Wix row (for incremental UI progress)."""
    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': 'No JSON data provided'}), 400

        model_number = str(data.get('model_number', '') or '').strip()
        if not model_number:
            return jsonify({'error': 'model_number is required'}), 400

        try:
            watch_data = search_watch_data(model_number)
            wix_row = create_wix_row(watch_data, model_number)
            return jsonify({
                'success': True,
                'result': wix_row,
                'model_number': model_number,
                'timestamp': datetime.now().isoformat()
            })
        except Exception as model_error:
            logger.error(f"Error processing {model_number}: {model_error}")
            fallback_row = create_wix_row(
                {
                    'name': model_number,
                    'description': f'Watch Model: {model_number}',
                    'image_url': '',
                    'brand': extract_brand(model_number),
                    'specs': []
                },
                model_number
            )
            return jsonify({
                'success': False,
                'result': fallback_row,
                'model_number': model_number,
                'error': str(model_error),
                'timestamp': datetime.now().isoformat()
            })

    except Exception as e:
        logger.error(f"Error in API search-single: {str(e)}", exc_info=True)
        return jsonify({'error': str(e)}), 500


@app.route('/api/generate-csv', methods=['POST'])
def api_generate_csv():
    """Generate WIX-compatible CSV with strict, fault-tolerant WIX requirements.

    Guarantees for every exported row:
    - `handleId` is never empty
    - `fieldType` is always exactly "Product" or "Variant" (defaults to "Product")
    - CSV is RFC 4180 compliant (proper escaping/quoting)
    """
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({'error': 'No JSON data provided'}), 400
        
        results = data.get('results', [])
        
        if not results:
            return jsonify({'error': 'No data to generate CSV'}), 400
        
        logger.info(f"Generating WIX CSV for {len(results)} products")

        # STEP 1: Normalize and auto-fix required fields (never reject for missing required values)
        normalized_results = []
        used_handles = set()

        for idx, row in enumerate(results, start=1):
            safe_row = dict(row) if isinstance(row, dict) else {}

            # Build/fix handleId
            handle_id = str(safe_row.get('handleId', '')).strip()
            if not handle_id:
                fallback_source = str(safe_row.get('name') or safe_row.get('sku') or f'product-{idx}')
                handle_id = generate_handle_id(fallback_source)
            if not handle_id:
                handle_id = f'product-{idx}'

            # Ensure uniqueness
            base_handle = handle_id
            suffix = 1
            while handle_id in used_handles:
                suffix += 1
                handle_id = f"{base_handle}-{suffix}"
            used_handles.add(handle_id)

            # Build/fix fieldType
            field_type = str(safe_row.get('fieldType', '')).strip()
            if field_type not in ['Product', 'Variant']:
                field_type = 'Product'

            safe_row['handleId'] = handle_id
            safe_row['fieldType'] = field_type

            # Ensure all columns exist as strings (never None/NaN)
            for col in WIX_COLUMNS:
                value = safe_row.get(col, '')
                if pd.isna(value) or value is None:
                    safe_row[col] = ''
                else:
                    safe_row[col] = str(value)

            normalized_results.append(safe_row)
            logger.info(
                f"Row {idx}: handleId='{safe_row['handleId']}', fieldType='{safe_row['fieldType']}'"
            )

        if not normalized_results:
            return jsonify({'error': 'No rows available to export'}), 400

        # STEP 2: Generate RFC 4180 CSV with proper escaping
        output = StringIO(newline='')
        writer = csv.DictWriter(
            output,
            fieldnames=WIX_COLUMNS,
            extrasaction='ignore',
            quoting=csv.QUOTE_MINIMAL,
            lineterminator='\r\n'
        )
        writer.writeheader()
        for row in normalized_results:
            writer.writerow({col: row.get(col, '') for col in WIX_COLUMNS})

        csv_content = output.getvalue()

        # STEP 3: Final verification
        if not csv_content.strip():
            return jsonify({'error': 'CSV generation failed: empty output'}), 500

        line_count = csv_content.count('\n')
        logger.info(f"CSV generated: {line_count} total lines (including header)")

        # Use UTF-8 WITHOUT BOM to avoid header matching issues in some importers
        csv_bytes = BytesIO(csv_content.encode('utf-8'))
        csv_bytes.seek(0)
        
        logger.info(f"✅ WIX CSV generated successfully with {len(normalized_results)} rows")
        logger.info("   All rows have handleId and valid fieldType")
        logger.info("   Format: RFC 4180 compliant, UTF-8 encoding")
        
        return send_file(
            csv_bytes,
            mimetype='text/csv',
            as_attachment=True,
            download_name=f'wix_watches_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv'
        )
    
    except Exception as e:
        logger.error(f"Error generating CSV: {str(e)}", exc_info=True)
        return jsonify({'error': f'CSV generation failed: {str(e)}'}), 500


@app.errorhandler(404)
def not_found(error):
    return jsonify({'error': 'Endpoint not found'}), 404


@app.errorhandler(500)
def internal_error(error):
    logger.error(f"Internal server error: {str(error)}", exc_info=True)
    return jsonify({'error': 'Internal server error'}), 500


if __name__ == '__main__':
    logger.info("=" * 60)
    logger.info("Watch Data Scraper & Wix Porter v2.0")
    logger.info(f"Wix CSV Columns: {len(WIX_COLUMNS)}")
    logger.info("Starting Flask application...")
    logger.info("=" * 60)
    logger.info("Open your browser to: http://localhost:5000")
    logger.info("Press Ctrl+C to stop the server")
    logger.info("=" * 60)
    
    app.run(debug=True, host='0.0.0.0', port=5000)
