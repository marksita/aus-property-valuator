import streamlit as st
import requests
from bs4 import BeautifulSoup
import re
import time
import urllib.parse
from datetime import datetime

# ── Page config ────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="AUS Property Valuator",
    page_icon="🏠",
    layout="centered",
    initial_sidebar_state="collapsed",
)

# ── Styles ─────────────────────────────────────────────────────────────────────
st.markdown("""
<style>
  @import url('https://fonts.googleapis.com/css2?family=DM+Serif+Display:ital@0;1&family=Inter:wght@300;400;500;600&family=JetBrains+Mono:wght@400;500&display=swap');
  html, body, [class*="css"] { font-family: 'Inter', sans-serif; }
  #MainMenu, footer, header { visibility: hidden; }
  .block-container { padding: 2rem 1rem 4rem; max-width: 780px; }
  .hero { text-align:center; padding:3rem 0 2rem; border-bottom:1px solid #e5e7eb; margin-bottom:2rem; }
  .hero-tag { font-size:0.72rem; letter-spacing:0.16em; text-transform:uppercase; color:#6b7280; margin-bottom:0.75rem; }
  .hero-title { font-family:'DM Serif Display',serif; font-size:clamp(2rem,5vw,3.2rem); color:#0f172a; line-height:1.15; margin:0 0 0.5rem; }
  .hero-title em { font-style:italic; color:#1d4ed8; }
  .hero-sub { color:#6b7280; font-size:0.95rem; }
  .val-card { background:#fff; border:1px solid #e5e7eb; border-radius:14px; padding:2rem; margin-top:1.5rem; box-shadow:0 4px 24px rgba(0,0,0,0.06); }
  .val-address { font-size:0.85rem; color:#6b7280; margin-bottom:0.4rem; }
  .val-headline { font-family:'DM Serif Display',serif; font-size:1.55rem; color:#0f172a; margin-bottom:1.5rem; border-bottom:1px solid #f3f4f6; padding-bottom:1rem; }
  .est-row { display:flex; align-items:flex-start; gap:1.4rem; margin-bottom:1.1rem; padding:1rem 1.1rem; background:#f9fafb; border-radius:10px; border-left:3px solid #1d4ed8; }
  .est-logo { font-size:0.7rem; font-weight:700; letter-spacing:0.08em; color:#1d4ed8; text-transform:uppercase; min-width:90px; padding-top:0.1rem; }
  .est-body { flex:1; }
  .est-value { font-family:'JetBrains Mono',monospace; font-size:1.3rem; font-weight:500; color:#111827; }
  .est-range { font-size:0.78rem; color:#6b7280; margin-top:0.15rem; }
  .est-detail { font-size:0.82rem; color:#374151; margin-top:0.35rem; line-height:1.5; }
  .est-link { display:inline-block; margin-top:0.4rem; font-size:0.75rem; color:#1d4ed8; text-decoration:none; }
  .est-link:hover { text-decoration:underline; }
  .section-label { font-size:0.8rem; font-weight:600; letter-spacing:0.06em; text-transform:uppercase; color:#374151; margin:1.4rem 0 0.6rem; }
  .disclaimer { font-size:0.73rem; color:#9ca3af; margin-top:1.5rem; line-height:1.6; border-top:1px solid #f3f4f6; padding-top:1rem; }
  .footer { text-align:center; font-size:0.72rem; color:#d1d5db; margin-top:3rem; letter-spacing:0.04em; }
  div[data-testid="stButton"] button[kind="secondary"] {
    background:#f9fafb !important; border:1px solid #e5e7eb !important; border-radius:8px !important;
    text-align:left !important; font-size:0.88rem !important; color:#111827 !important;
    padding:0.55rem 0.9rem !important; margin-bottom:4px !important;
  }
  div[data-testid="stButton"] button[kind="secondary"]:hover {
    background:#eff6ff !important; border-color:#1d4ed8 !important; color:#1d4ed8 !important;
  }
</style>
""", unsafe_allow_html=True)

st.markdown("""
<div class="hero">
  <div class="hero-tag">Australian Property</div>
  <h1 class="hero-title">What's your home <em>worth?</em></h1>
  <p class="hero-sub">Search any Australian address for a free market estimate — no account required.</p>
</div>
""", unsafe_allow_html=True)

# ── Constants ──────────────────────────────────────────────────────────────────
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
    "Accept-Language": "en-AU,en;q=0.9",
    "Accept-Encoding": "gzip, deflate, br",
    "Connection": "keep-alive",
}

# ── Address helpers ────────────────────────────────────────────────────────────
def fetch_suggestions(query: str) -> list:
    if len(query) < 4:
        return []
    clean = re.sub(r"^\d+\s*/\s*", "", query.strip())
    clean = re.sub(r"^(unit|apt|apartment|flat|shop)\s+\S+\s*,?\s*", "", clean, flags=re.IGNORECASE)
    search_q = clean or query
    try:
        resp = requests.get(
            "https://nominatim.openstreetmap.org/search",
            params={"q": search_q, "format": "json", "addressdetails": 1, "limit": 7, "countrycodes": "au"},
            headers={"User-Agent": "AusPropertyValuator/1.0 (open-source streamlit app)"},
            timeout=5,
        )
        if resp.status_code == 200:
            results, seen = [], set()
            for item in resp.json():
                label = item.get("display_name", "")
                parts = [p.strip() for p in label.split(",")]
                if parts and parts[-1].lower() == "australia":
                    parts = parts[:-1]
                clean_label = ", ".join(parts[:5])
                if clean_label and clean_label not in seen:
                    seen.add(clean_label)
                    results.append(clean_label)
            if results:
                return results
    except Exception:
        pass
    try:
        resp = requests.get(
            "https://photon.komoot.io/api/",
            params={"q": search_q, "limit": 7, "lang": "en", "bbox": "112,-44,154,-10"},
            headers={"User-Agent": "AusPropertyValuator/1.0"},
            timeout=5,
        )
        if resp.status_code == 200:
            results, seen = [], set()
            for f in resp.json().get("features", []):
                p = f.get("properties", {})
                if p.get("country", "").lower() not in ("australia", "au"):
                    continue
                parts = [p.get("housenumber",""), p.get("street",""),
                         p.get("city","") or p.get("suburb",""), p.get("state",""), p.get("postcode","")]
                label = ", ".join(x for x in parts if x)
                if label and label not in seen:
                    seen.add(label)
                    results.append(label)
            if results:
                return results
    except Exception:
        pass
    return []


def parse_address(address: str) -> dict:
    addr = re.sub(r"\s+", " ", address.strip())
    parts = [p.strip() for p in addr.split(",")]
    if parts and parts[-1].lower() in ("australia", "au"):
        parts = parts[:-1]
    suburb_part = parts[-1] if parts else ""
    postcode_m = re.search(r"\b(\d{4})\b", suburb_part)
    postcode = postcode_m.group(1) if postcode_m else ""
    state_m = re.search(r"\b(VIC|NSW|QLD|SA|WA|TAS|ACT|NT)\b", suburb_part, re.IGNORECASE)
    state = state_m.group(1).upper() if state_m else ""
    suburb_clean = suburb_part
    if postcode:
        suburb_clean = suburb_clean.replace(postcode, "")
    if state:
        suburb_clean = re.sub(r"\b" + state + r"\b", "", suburb_clean, flags=re.IGNORECASE)
    suburb_clean = suburb_clean.strip(", ").strip()
    return {
        "suburb": suburb_clean,
        "state": state,
        "postcode": postcode,
        "suburb_state": f"{suburb_clean} {state} {postcode}".strip(),
    }


def build_address_slug(address: str) -> str:
    """4/40 Rothesay Avenue, Elwood VIC 3184 -> 4-40-rothesay-avenue-elwood-vic-3184"""
    p = parse_address(address)
    street_part = address.split(",")[0].strip().lower()
    street_slug = re.sub(r"[^\w\s/-]", "", street_part)
    street_slug = re.sub(r"[\s/]+", "-", street_slug)
    street_slug = re.sub(r"-+", "-", street_slug).strip("-")
    parts = [street_slug, p["suburb"].lower().replace(" ", "-"), p["state"].lower(), p["postcode"]]
    return "-".join(x for x in parts if x)


# ── Data sources ───────────────────────────────────────────────────────────────

def scrape_propertyvalue(address: str) -> dict | None:
    """
    propertyvalue.com.au — free automated valuation estimates, no login needed.
    URL format: /property/{unit}/{street-suburb-state-postcode}/{id}
    We search their site via their search endpoint.
    """
    try:
        p = parse_address(address)
        street_raw = address.split(",")[0].strip()
        # Strip unit number for street search: "4/40 Rothesay" -> "40 Rothesay"
        street_no_unit = re.sub(r"^\d+\s*/\s*", "", street_raw).strip()
        search_q = f"{street_no_unit}, {p['suburb']} {p['state']} {p['postcode']}"
        search_url = f"https://www.propertyvalue.com.au/search/?q={urllib.parse.quote_plus(search_q)}"
        resp = requests.get(search_url, headers=HEADERS, timeout=10, allow_redirects=True)

        if resp.status_code == 200:
            soup = BeautifulSoup(resp.text, "html.parser")

            # Look for estimate value
            for selector in [
                ".property-value", ".estimate", ".valuation",
                "[class*='estimate']", "[class*='value']", "[class*='price']"
            ]:
                el = soup.select_one(selector)
                if el:
                    m = re.search(r"\$[\d,]+", el.get_text())
                    if m:
                        val = int(m.group().replace("$","").replace(",",""))
                        if val > 100_000:
                            return {
                                "source": "PropertyValue.com.au",
                                "value": m.group(),
                                "range": None,
                                "note": "Automated valuation estimate",
                                "url": resp.url,
                            }

            # Look for any price in page
            prices = re.findall(r"\$\s*([\d,]+)", resp.text)
            prices = [int(p.replace(",","")) for p in prices if int(p.replace(",","")) > 200_000]
            if prices:
                median_p = sorted(prices)[len(prices)//2]
                return {
                    "source": "PropertyValue.com.au",
                    "value": f"${median_p:,}",
                    "range": None,
                    "note": "Based on page data",
                    "url": resp.url,
                }
    except Exception:
        pass
    return None


def scrape_auhouseprices(address: str) -> dict | None:
    """auhouseprices.com — free sold price history, no login."""
    try:
        p = parse_address(address)
        street_raw = address.split(",")[0].strip()
        street_no_unit = re.sub(r"^\d+\s*/\s*", "", street_raw).strip()
        # Build their URL format
        addr_slug = urllib.parse.quote_plus(f"{street_no_unit}, {p['suburb']} {p['state']}")
        # Their suburb_id varies — use their search
        search_url = f"https://www.auhouseprices.com/sold/list/VIC/{p['suburb'].replace(' ','+')}/?type=all&keywords={urllib.parse.quote_plus(street_no_unit)}"
        resp = requests.get(search_url, headers=HEADERS, timeout=10)

        if resp.status_code == 200:
            soup = BeautifulSoup(resp.text, "html.parser")
            prices = []
            items = []

            # Parse sold listings
            for row in soup.find_all(["div","li","tr"], class_=re.compile(r"(listing|result|sold|property)", re.I)):
                text = row.get_text(" ", strip=True)
                price_m = re.search(r"\$([\d,]+)", text)
                if price_m:
                    val = int(price_m.group(1).replace(",",""))
                    if 200_000 < val < 10_000_000:
                        prices.append(val)
                        addr_m = re.search(r"\d+[\w\s/,-]+(?:Street|St|Avenue|Ave|Road|Rd|Drive|Dr|Court|Ct|Place|Pl|Crescent|Cres)", text, re.I)
                        items.append({
                            "address": addr_m.group().strip() if addr_m else "Nearby property",
                            "price": f"${val:,}",
                        })

            if prices:
                avg = sum(prices) // len(prices)
                return {
                    "source": "AuHousePrices.com",
                    "value": f"${avg:,}",
                    "range": f"${min(prices):,} – ${max(prices):,}",
                    "note": f"Average of {len(prices)} recent nearby sales",
                    "url": search_url,
                    "comparables": items[:4],
                }
    except Exception:
        pass
    return None


def scrape_domain_profile(address: str) -> dict | None:
    """Domain property profile — public page, no login for basic data."""
    try:
        slug = build_address_slug(address)
        url = f"https://www.domain.com.au/property-profile/{slug}"
        resp = requests.get(url, headers=HEADERS, timeout=10, allow_redirects=True)

        if resp.status_code == 200:
            soup = BeautifulSoup(resp.text, "html.parser")
            text = resp.text

            # Domain Estimate
            estimate_m = re.search(r'"domainEstimate"\s*:\s*\{[^}]*"mid"\s*:\s*([\d]+)', text)
            low_m = re.search(r'"domainEstimate"\s*:\s*\{[^}]*"low"\s*:\s*([\d]+)', text)
            high_m = re.search(r'"domainEstimate"\s*:\s*\{[^}]*"high"\s*:\s*([\d]+)', text)

            if estimate_m:
                mid = int(estimate_m.group(1))
                lo = f"${int(low_m.group(1)):,}" if low_m else None
                hi = f"${int(high_m.group(1)):,}" if high_m else None
                return {
                    "source": "Domain Estimate",
                    "value": f"${mid:,}",
                    "range": f"{lo} – {hi}" if lo and hi else None,
                    "note": "Domain automated valuation",
                    "url": url,
                }

            # Last sold price
            sold_m = re.search(r'[Ll]ast\s+sold[^\$]*\$([\d,]+)', text)
            if sold_m:
                val = int(sold_m.group(1).replace(",",""))
                date_m = re.search(r'[Ll]ast\s+sold\s+(\w+\s+\d{4}|\d+\s+years?\s+ago)', text)
                return {
                    "source": "Domain (last sale)",
                    "value": f"${val:,}",
                    "range": None,
                    "note": f"Last recorded sale{': ' + date_m.group(1) if date_m else ''}",
                    "url": url,
                }
    except Exception:
        pass
    return None


def scrape_pricesfinder(address: str) -> dict | None:
    """pricesfinder.com.au — free suburb median stats."""
    try:
        p = parse_address(address)
        suburb_slug = p["suburb"].lower().replace(" ", "-")
        state_slug = p["state"].lower()
        url = f"https://pricesfinder.com.au/suburb/{suburb_slug}-{state_slug}-{p['postcode']}/"
        resp = requests.get(url, headers=HEADERS, timeout=10)
        if resp.status_code == 200:
            soup = BeautifulSoup(resp.text, "html.parser")
            text = resp.text
            # Look for unit/apartment median
            unit_m = re.search(r"[Uu]nit[^$]*median[^$]*\$([\d,]+)|median[^$]*[Uu]nit[^$]*\$([\d,]+)", text)
            if unit_m:
                val_str = unit_m.group(1) or unit_m.group(2)
                val = int(val_str.replace(",",""))
                return {
                    "source": "PricesFinder (suburb median)",
                    "value": f"${val:,}",
                    "range": None,
                    "note": f"Median unit price in {p['suburb']} {p['state']}",
                    "url": url,
                }
            prices = re.findall(r"\$([\d,]+)", text)
            prices = [int(x.replace(",","")) for x in prices if 200_000 < int(x.replace(",","")) < 5_000_000]
            if prices:
                median_p = sorted(prices)[len(prices)//2]
                return {
                    "source": "PricesFinder (suburb data)",
                    "value": f"${median_p:,}",
                    "range": None,
                    "note": f"Suburb price data for {p['suburb']} {p['state']}",
                    "url": url,
                }
    except Exception:
        pass
    return None


def get_direct_links(address: str) -> list:
    """Always-available direct links to property platforms."""
    p = parse_address(address)
    slug = build_address_slug(address)
    suburb_slug = "-".join(x for x in [p["suburb"].lower().replace(" ","-"), p["state"].lower(), p["postcode"]] if x)
    q = urllib.parse.quote_plus(p["suburb_state"])
    return [
        {
            "source": "Domain property profile",
            "value": None,
            "note": "View Domain Estimate + full sale history (free account)",
            "url": f"https://www.domain.com.au/property-profile/{slug}",
        },
        {
            "source": "Domain sold listings",
            "value": None,
            "note": f"Recent sales in {p['suburb']}",
            "url": f"https://www.domain.com.au/sold-listings/?q={q}&sort=dateSold-desc",
        },
        {
            "source": "PropertyValue.com.au",
            "value": None,
            "note": "Free automated estimate — no account needed",
            "url": f"https://www.propertyvalue.com.au/search/?q={urllib.parse.quote_plus(address)}",
        },
        {
            "source": "AuHousePrices.com",
            "value": None,
            "note": "Free sold price history",
            "url": f"https://www.auhouseprices.com/sold/list/VIC/{p['suburb'].replace(' ','+')}/?type=all",
        },
    ]


def get_all_estimates(address: str) -> list:
    """Run all scrapers and return results."""
    results = []
    scrapers = [
        ("PropertyValue.com.au", scrape_propertyvalue),
        ("Domain profile", scrape_domain_profile),
        ("AuHousePrices.com", scrape_auhouseprices),
        ("PricesFinder", scrape_pricesfinder),
    ]
    for name, fn in scrapers:
        try:
            r = fn(address)
            if r:
                results.append(r)
        except Exception:
            pass
        time.sleep(0.3)
    return results


# ── Session state ──────────────────────────────────────────────────────────────
for key, default in [("confirmed_address",""), ("last_typed",""), ("suggestions",[])]:
    if key not in st.session_state:
        st.session_state[key] = default

# ── Address input ──────────────────────────────────────────────────────────────
st.markdown('<p style="font-size:0.8rem;font-weight:600;letter-spacing:0.06em;text-transform:uppercase;color:#374151;margin-bottom:0.4rem;">Property address</p>', unsafe_allow_html=True)

typed = st.text_input(
    "address_field",
    value=st.session_state.confirmed_address or "",
    placeholder="e.g. 4/40 Rothesay Avenue, Elwood VIC 3184",
    label_visibility="collapsed",
)

if typed and typed != st.session_state.confirmed_address and typed != st.session_state.last_typed:
    st.session_state.last_typed = typed
    st.session_state.confirmed_address = ""
    if len(typed) >= 4:
        with st.spinner("Searching addresses..."):
            st.session_state.suggestions = fetch_suggestions(typed)
    else:
        st.session_state.suggestions = []

if st.session_state.suggestions and not st.session_state.confirmed_address:
    st.caption("Select your address:")
    for s in st.session_state.suggestions:
        if st.button(f"📍 {s}", key=f"s_{hash(s)}", use_container_width=True):
            st.session_state.confirmed_address = s
            st.session_state.suggestions = []
            st.rerun()

final_address = st.session_state.confirmed_address or typed
if st.session_state.confirmed_address:
    st.success(f"Selected: {st.session_state.confirmed_address}")

# ── Search button ──────────────────────────────────────────────────────────────
st.markdown("")
search_clicked = st.button("🔍  Get market valuation", use_container_width=True, type="primary")

if search_clicked:
    address = final_address.strip()
    if len(address) < 6:
        st.warning("Please enter a valid Australian property address.")
    else:
        with st.spinner(f"Searching {address}..."):
            estimates = get_all_estimates(address)
        links = get_direct_links(address)

        st.markdown(
            f'<div class="val-card">'
            f'<div class="val-address">Market estimate for</div>'
            f'<div class="val-headline">{address}</div>',
            unsafe_allow_html=True,
        )

        if estimates:
            st.markdown('<div class="section-label">Estimates found</div>', unsafe_allow_html=True)
            for r in estimates:
                comps_html = ""
                for c in r.get("comparables", []):
                    comps_html += f'<div class="est-range">&nbsp;&nbsp;&#x2022; {c["address"]} — {c["price"]}</div>'
                st.markdown(
                    f'<div class="est-row">'
                    f'<div class="est-logo">{r["source"].split("(")[0].strip()}</div>'
                    f'<div class="est-body">'
                    + (f'<div class="est-value">{r["value"]}</div>' if r.get("value") else "")
                    + (f'<div class="est-range">Range: {r["range"]}</div>' if r.get("range") else "")
                    + (f'<div class="est-detail">{r["note"]}</div>' if r.get("note") else "")
                    + comps_html
                    + f'<a class="est-link" href="{r["url"]}" target="_blank">View on {r["source"].split("(")[0].strip()}</a>'
                    f'</div></div>',
                    unsafe_allow_html=True,
                )
        else:
            st.info(
                "No automated estimates were returned for this property. "
                "This is common for units that haven't sold recently — use the direct links below to check each platform manually.",
                icon="ℹ️",
            )

        st.markdown('<div class="section-label">View on property platforms</div>', unsafe_allow_html=True)
        for link in links:
            st.markdown(
                f'<div class="est-row">'
                f'<div class="est-logo">{link["source"].split(".")[0].strip()}</div>'
                f'<div class="est-body">'
                f'<div class="est-detail">{link["note"]}</div>'
                f'<a class="est-link" href="{link["url"]}" target="_blank">Open {link["source"]}</a>'
                f'</div></div>',
                unsafe_allow_html=True,
            )

        st.markdown(
            f'<div class="disclaimer">'
            f'Data retrieved {datetime.now().strftime("%-d %B %Y, %-I:%M %p AEST")}. '
            f'Estimates are indicative only based on automated valuation models and comparable sales. '
            f'Not a certified valuation — engage a licensed property valuer (API/AIQS) for formal advice. '
            f'Sources: PropertyValue.com.au, AuHousePrices.com, Domain.com.au.'
            f'</div></div>',
            unsafe_allow_html=True,
        )

st.markdown(
    '<div class="footer">Built with Streamlit · 100% free · No API key required · Data via free property sites</div>',
    unsafe_allow_html=True,
)
