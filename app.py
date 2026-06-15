import streamlit as st
import requests
from bs4 import BeautifulSoup
import urllib.parse
import re
import time
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

  .hero {
    text-align: center;
    padding: 3rem 0 2rem;
    border-bottom: 1px solid #e5e7eb;
    margin-bottom: 2rem;
  }
  .hero-tag {
    font-size: 0.72rem;
    letter-spacing: 0.16em;
    text-transform: uppercase;
    color: #6b7280;
    margin-bottom: 0.75rem;
  }
  .hero-title {
    font-family: 'DM Serif Display', serif;
    font-size: clamp(2rem, 5vw, 3.2rem);
    color: #0f172a;
    line-height: 1.15;
    margin: 0 0 0.5rem;
  }
  .hero-title em { font-style: italic; color: #1d4ed8; }
  .hero-sub { color: #6b7280; font-size: 0.95rem; }

  .search-label {
    font-size: 0.8rem;
    font-weight: 600;
    letter-spacing: 0.06em;
    text-transform: uppercase;
    color: #374151;
    margin-bottom: 0.4rem;
  }

  .val-card {
    background: #fff;
    border: 1px solid #e5e7eb;
    border-radius: 14px;
    padding: 2rem;
    margin-top: 1.5rem;
    box-shadow: 0 4px 24px rgba(0,0,0,0.06);
  }
  .val-address { font-size: 0.85rem; color: #6b7280; margin-bottom: 0.4rem; }
  .val-headline {
    font-family: 'DM Serif Display', serif;
    font-size: 1.55rem;
    color: #0f172a;
    margin-bottom: 1.5rem;
    border-bottom: 1px solid #f3f4f6;
    padding-bottom: 1rem;
  }
  .est-row {
    display: flex;
    align-items: flex-start;
    gap: 1.4rem;
    margin-bottom: 1.1rem;
    padding: 1rem 1.1rem;
    background: #f9fafb;
    border-radius: 10px;
    border-left: 3px solid #1d4ed8;
  }
  .est-logo {
    font-size: 0.7rem;
    font-weight: 700;
    letter-spacing: 0.08em;
    color: #1d4ed8;
    text-transform: uppercase;
    min-width: 80px;
    padding-top: 0.1rem;
  }
  .est-body { flex: 1; }
  .est-value {
    font-family: 'JetBrains Mono', monospace;
    font-size: 1.3rem;
    font-weight: 500;
    color: #111827;
  }
  .est-range { font-size: 0.78rem; color: #6b7280; margin-top: 0.15rem; }
  .est-link {
    display: inline-block;
    margin-top: 0.4rem;
    font-size: 0.75rem;
    color: #1d4ed8;
    text-decoration: none;
  }
  .est-link:hover { text-decoration: underline; }

  .info-banner {
    background: #eff6ff;
    border: 1px solid #bfdbfe;
    border-radius: 10px;
    padding: 1rem 1.2rem;
    color: #1e40af;
    font-size: 0.88rem;
    margin-top: 1rem;
  }
  .disclaimer {
    font-size: 0.73rem;
    color: #9ca3af;
    margin-top: 1.5rem;
    line-height: 1.6;
    border-top: 1px solid #f3f4f6;
    padding-top: 1rem;
  }
  .footer {
    text-align: center;
    font-size: 0.72rem;
    color: #d1d5db;
    margin-top: 3rem;
    letter-spacing: 0.04em;
  }

  /* Make suggestion buttons look like list items */
  div[data-testid="stButton"] button[kind="secondary"] {
    background: #f9fafb !important;
    border: 1px solid #e5e7eb !important;
    border-radius: 8px !important;
    text-align: left !important;
    font-size: 0.88rem !important;
    color: #111827 !important;
    padding: 0.55rem 0.9rem !important;
    margin-bottom: 4px !important;
  }
  div[data-testid="stButton"] button[kind="secondary"]:hover {
    background: #eff6ff !important;
    border-color: #1d4ed8 !important;
    color: #1d4ed8 !important;
  }
</style>
""", unsafe_allow_html=True)

# ── Hero ───────────────────────────────────────────────────────────────────────
st.markdown("""
<div class="hero">
  <div class="hero-tag">Australian Property</div>
  <h1 class="hero-title">What's your home <em>worth?</em></h1>
  <p class="hero-sub">Search any Australian address for a current market estimate from multiple sources.</p>
</div>
""", unsafe_allow_html=True)

# ── Free geocoding: Nominatim (OpenStreetMap) with Photon fallback ─────────────
def fetch_suggestions(query: str) -> list[str]:
    """
    Returns a list of address suggestion strings.
    Primary: Nominatim (OpenStreetMap) — 100% free, no key needed.
    Fallback: Photon (Komoot) — also 100% free, no key needed.
    Both are open-source geocoders used by millions of apps.
    """
    if len(query) < 4:
        return []

    # Strip unit/apartment prefix so "4/40 Rothesay" → "40 Rothesay" for better geocoding
    clean_query = re.sub(r"^\d+\s*/\s*", "", query.strip())
    clean_query = re.sub(r"^(unit|apt|apartment|flat|shop)\s+\S+\s*,?\s*", "", clean_query, flags=re.IGNORECASE)
    query = clean_query or query

    # ── Try Nominatim first ────────────────────────────────────────────────────
    try:
        resp = requests.get(
            "https://nominatim.openstreetmap.org/search",
            params={
                "q": query,
                "format": "json",
                "addressdetails": 1,
                "limit": 7,
                "countrycodes": "au",
            },
            headers={"User-Agent": "AusPropertyValuator/1.0 (streamlit open-source app)"},
            timeout=5,
        )
        if resp.status_code == 200:
            data = resp.json()
            results, seen = [], set()
            for item in data:
                label = item.get("display_name", "")
                # Strip trailing ", Australia"
                parts = [p.strip() for p in label.split(",")]
                if parts and parts[-1].lower() == "australia":
                    parts = parts[:-1]
                clean = ", ".join(parts[:5])
                if clean and clean not in seen:
                    seen.add(clean)
                    results.append(clean)
            if results:
                return results
    except Exception:
        pass

    # ── Fallback: Photon (Komoot) ──────────────────────────────────────────────
    try:
        resp = requests.get(
            "https://photon.komoot.io/api/",
            params={"q": query, "limit": 7, "lang": "en", "bbox": "112,-44,154,-10"},
            headers={"User-Agent": "AusPropertyValuator/1.0"},
            timeout=5,
        )
        if resp.status_code == 200:
            features = resp.json().get("features", [])
            results, seen = [], set()
            for f in features:
                p = f.get("properties", {})
                # Only Australian results
                if p.get("country", "").lower() not in ("australia", "au"):
                    continue
                parts = [
                    p.get("housenumber", ""),
                    p.get("street", ""),
                    p.get("city", "") or p.get("suburb", ""),
                    p.get("state", ""),
                    p.get("postcode", ""),
                ]
                clean = ", ".join(x for x in parts if x)
                if clean and clean not in seen:
                    seen.add(clean)
                    results.append(clean)
            if results:
                return results
    except Exception:
        pass

    return []


# ── Session state ──────────────────────────────────────────────────────────────
for key, default in [("confirmed_address", ""), ("last_typed", ""), ("suggestions", [])]:
    if key not in st.session_state:
        st.session_state[key] = default

# ── Address input ──────────────────────────────────────────────────────────────
st.markdown('<div class="search-label">Property address</div>', unsafe_allow_html=True)

typed = st.text_input(
    "address_field",
    value=st.session_state.confirmed_address or "",
    placeholder="Start typing — e.g. 42 Collins Street, Melbourne…",
    label_visibility="collapsed",
)

# Re-fetch suggestions only when the typed value actually changes
if typed and typed != st.session_state.confirmed_address and typed != st.session_state.last_typed:
    st.session_state.last_typed = typed
    st.session_state.confirmed_address = ""  # reset confirmation when user edits
    if len(typed) >= 4:
        with st.spinner("Searching addresses…"):
            st.session_state.suggestions = fetch_suggestions(typed)
    else:
        st.session_state.suggestions = []

# Show suggestion buttons
if st.session_state.suggestions and not st.session_state.confirmed_address:
    st.caption("Select your address from the list:")
    for suggestion in st.session_state.suggestions:
        if st.button(f"📍 {suggestion}", key=f"s_{hash(suggestion)}", use_container_width=True):
            st.session_state.confirmed_address = suggestion
            st.session_state.suggestions = []
            st.rerun()

# Final resolved address
final_address = st.session_state.confirmed_address or typed

if st.session_state.confirmed_address:
    st.success(f"✅ Selected: {st.session_state.confirmed_address}")

# ── Address parsing ────────────────────────────────────────────────────────────
def parse_address(address: str) -> dict:
    """
    Handles formats like:
      4/40 Rothesay Avenue, Elwood VIC 3186
      Unit 4, 40 Rothesay Avenue, Elwood VIC 3186
      42 Collins Street, Melbourne VIC 3000
    Returns suburb, state, postcode, suburb_state
    """
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

    suburb_state = suburb_clean
    if state:
        suburb_state += f" {state}"
    if postcode:
        suburb_state += f" {postcode}"

    return {
        "suburb": suburb_clean,
        "state": state,
        "postcode": postcode,
        "suburb_state": suburb_state.strip(),
    }


# ── Property data scraping ─────────────────────────────────────────────────────
SCRAPE_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "en-AU,en;q=0.9",
}


def format_domain_search_url(address: str) -> str:
    p = parse_address(address)
    q = p["suburb_state"] or address
    return f"https://www.domain.com.au/sold-listings/?q={urllib.parse.quote_plus(q)}&sort=dateSold-desc"


def get_proptrack_url(address: str) -> str:
    p = parse_address(address)
    suburb_slug = p["suburb"].lower().replace(" ", "-")
    state_slug = p["state"].lower()
    postcode = p["postcode"]
    # REA property profile URL format
    return f"https://www.realestate.com.au/neighbourhoods/{suburb_slug}-{state_slug}-{postcode}/"


def search_domain_sold(address: str):
    try:
        p = parse_address(address)
        suburb_state = p["suburb_state"] or address
        url = (
            f"https://www.domain.com.au/sold-listings/"
            f"?q={urllib.parse.quote_plus(suburb_state)}&sort=dateSold-desc"
        )
        resp = requests.get(url, headers=SCRAPE_HEADERS, timeout=10)
        soup = BeautifulSoup(resp.text, "html.parser")
        prices = []
        for tag in soup.find_all("p", {"data-testid": "listing-card-price"})[:8]:
            m = re.search(r"\$([\d,]+)", tag.text)
            if m:
                val = int(m.group(1).replace(",", ""))
                if val > 50_000:
                    prices.append(val)
        if prices:
            avg = sum(prices) // len(prices)
            return {
                "value": f"${avg:,}",
                "range": f"Based on {len(prices)} recent sales in {p['suburb'] or 'area'}: ${min(prices):,} – ${max(prices):,}",
                "url": url,
                "source": "Domain (recent sales)",
            }
    except Exception:
        pass
    return None


def search_rea_sold(address: str):
    try:
        p = parse_address(address)
        suburb = p["suburb"].lower().replace(" ", "-")
        state = p["state"].lower()
        postcode = p["postcode"]
        # REA sold URL: /sold/in-elwood-vic-3184/
        location_slug = "-".join(filter(None, [suburb, state, postcode]))
        url = f"https://www.realestate.com.au/sold/in-{location_slug}/?sortType=soldDate"
        resp = requests.get(url, headers=SCRAPE_HEADERS, timeout=10)
        soup = BeautifulSoup(resp.text, "html.parser")
        prices = []
        for span in soup.find_all("span", class_=re.compile(r"price", re.I)):
            m = re.search(r"\$([\d,]+)", span.text)
            if m:
                val = int(m.group(1).replace(",", ""))
                if val > 100_000:
                    prices.append(val)
        if prices:
            avg = sum(prices) // len(prices)
            return {
                "value": f"${avg:,}",
                "range": f"Based on {len(prices)} recent sales in {p['suburb'] or 'area'}: ${min(prices):,} – ${max(prices):,}",
                "url": url,
                "source": "realestate.com.au (recent sales)",
            }
    except Exception:
        pass
    return None


def get_price_estimate(address: str):
    results = []
    with st.spinner("Fetching market data from Domain & REA…"):
        r1 = search_domain_sold(address)
        if r1:
            results.append(r1)
        time.sleep(0.4)
        r2 = search_rea_sold(address)
        if r2:
            results.append(r2)

    results.append({
        "value": None,
        "range": "View current listings and Domain Estimate (free account required)",
        "url": format_domain_search_url(address),
        "source": "Domain — search directly",
    })
    results.append({
        "value": None,
        "range": "View PropTrack automated valuation (free account required)",
        "url": get_proptrack_url(address),
        "source": "realestate.com.au — view property",
    })
    return results


# ── Search button ──────────────────────────────────────────────────────────────
st.markdown("")
search_clicked = st.button("🔍  Get market valuation", use_container_width=True, type="primary")

if search_clicked:
    address = final_address.strip() if final_address else ""
    if len(address) < 6:
        st.warning("Please enter or select a valid Australian address first.")
    else:
        results = get_price_estimate(address)
        has_values = [r for r in results if r.get("value")]

        st.markdown(f"""
        <div class="val-card">
          <div class="val-address">Market estimate for</div>
          <div class="val-headline">{address}</div>
        """, unsafe_allow_html=True)

        if not has_values:
            st.markdown("""
            <div class="info-banner">
              ⚠️ <strong>No scraped estimates returned</strong> for this suburb — Domain and REA
              may have blocked the automated request. Use the direct links below to view
              estimates on each platform (free account required on each site).
            </div>
            """, unsafe_allow_html=True)

        for r in results:
            value_html = f'<div class="est-value">{r["value"]}</div>' if r.get("value") else ""
            range_html = f'<div class="est-range">{r["range"]}</div>' if r.get("range") else ""
            label = r["source"].split("(")[0].split("—")[0].strip()
            link_html = f'<a class="est-link" href="{r["url"]}" target="_blank">Open {label} ↗</a>'

            st.markdown(f"""
            <div class="est-row">
              <div class="est-logo">{label}</div>
              <div class="est-body">{value_html}{range_html}{link_html}</div>
            </div>
            """, unsafe_allow_html=True)

        st.markdown(f"""
          <div class="disclaimer">
            Data retrieved {datetime.now().strftime("%-d %B %Y, %-I:%M %p AEST")}.
            Suburb-level estimates are based on recent comparable sales and are indicative only — not a certified valuation.
            Address autocomplete powered by OpenStreetMap Nominatim &amp; Photon — 100% free, no API key required.
          </div>
        </div>
        """, unsafe_allow_html=True)

# ── Footer ─────────────────────────────────────────────────────────────────────
st.markdown("""
<div class="footer">Built with Streamlit · Address search via OpenStreetMap · 100% free to run</div>
""", unsafe_allow_html=True)
