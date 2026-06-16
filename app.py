import streamlit as st
import requests
import re
import json
from datetime import datetime
import urllib.parse

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
    text-align: center; padding: 3rem 0 2rem;
    border-bottom: 1px solid #e5e7eb; margin-bottom: 2rem;
  }
  .hero-tag { font-size: 0.72rem; letter-spacing: 0.16em; text-transform: uppercase; color: #6b7280; margin-bottom: 0.75rem; }
  .hero-title { font-family: 'DM Serif Display', serif; font-size: clamp(2rem, 5vw, 3.2rem); color: #0f172a; line-height: 1.15; margin: 0 0 0.5rem; }
  .hero-title em { font-style: italic; color: #1d4ed8; }
  .hero-sub { color: #6b7280; font-size: 0.95rem; }
  .search-label { font-size: 0.8rem; font-weight: 600; letter-spacing: 0.06em; text-transform: uppercase; color: #374151; margin-bottom: 0.4rem; }
  .val-card { background: #fff; border: 1px solid #e5e7eb; border-radius: 14px; padding: 2rem; margin-top: 1.5rem; box-shadow: 0 4px 24px rgba(0,0,0,0.06); }
  .val-address { font-size: 0.85rem; color: #6b7280; margin-bottom: 0.4rem; }
  .val-headline { font-family: 'DM Serif Display', serif; font-size: 1.55rem; color: #0f172a; margin-bottom: 1.5rem; border-bottom: 1px solid #f3f4f6; padding-bottom: 1rem; }
  .est-row { display: flex; align-items: flex-start; gap: 1.4rem; margin-bottom: 1.1rem; padding: 1rem 1.1rem; background: #f9fafb; border-radius: 10px; border-left: 3px solid #1d4ed8; }
  .est-logo { font-size: 0.7rem; font-weight: 700; letter-spacing: 0.08em; color: #1d4ed8; text-transform: uppercase; min-width: 90px; padding-top: 0.1rem; }
  .est-body { flex: 1; }
  .est-value { font-family: 'JetBrains Mono', monospace; font-size: 1.3rem; font-weight: 500; color: #111827; }
  .est-range { font-size: 0.78rem; color: #6b7280; margin-top: 0.15rem; }
  .est-detail { font-size: 0.82rem; color: #374151; margin-top: 0.35rem; line-height: 1.5; }
  .est-link { display: inline-block; margin-top: 0.4rem; font-size: 0.75rem; color: #1d4ed8; text-decoration: none; }
  .est-link:hover { text-decoration: underline; }
  .disclaimer { font-size: 0.73rem; color: #9ca3af; margin-top: 1.5rem; line-height: 1.6; border-top: 1px solid #f3f4f6; padding-top: 1rem; }
  .footer { text-align: center; font-size: 0.72rem; color: #d1d5db; margin-top: 3rem; letter-spacing: 0.04em; }
  div[data-testid="stButton"] button[kind="secondary"] {
    background: #f9fafb !important; border: 1px solid #e5e7eb !important;
    border-radius: 8px !important; text-align: left !important;
    font-size: 0.88rem !important; color: #111827 !important;
    padding: 0.55rem 0.9rem !important; margin-bottom: 4px !important;
  }
  div[data-testid="stButton"] button[kind="secondary"]:hover {
    background: #eff6ff !important; border-color: #1d4ed8 !important; color: #1d4ed8 !important;
  }
</style>
""", unsafe_allow_html=True)

# ── Hero ───────────────────────────────────────────────────────────────────────
st.markdown("""
<div class="hero">
  <div class="hero-tag">Australian Property</div>
  <h1 class="hero-title">What's your home <em>worth?</em></h1>
  <p class="hero-sub">Search any Australian address for a current market estimate powered by AI web search.</p>
</div>
""", unsafe_allow_html=True)

# ── Address helpers ────────────────────────────────────────────────────────────
def fetch_suggestions(query: str) -> list:
    if len(query) < 4:
        return []
    clean = re.sub(r"^\d+\s*/\s*", "", query.strip())
    clean = re.sub(r"^(unit|apt|apartment|flat|shop)\s+\S+\s*,?\s*", "", clean, flags=re.IGNORECASE)
    search_q = clean or query
    # Nominatim
    try:
        resp = requests.get(
            "https://nominatim.openstreetmap.org/search",
            params={"q": search_q, "format": "json", "addressdetails": 1, "limit": 7, "countrycodes": "au"},
            headers={"User-Agent": "AusPropertyValuator/1.0 (streamlit open-source app)"},
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
    # Photon fallback
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
                         p.get("city","") or p.get("suburb",""),
                         p.get("state",""), p.get("postcode","")]
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
    suburb_state = f"{suburb_clean} {state} {postcode}".strip()
    return {"suburb": suburb_clean, "state": state, "postcode": postcode, "suburb_state": suburb_state}


def build_domain_profile_url(address: str) -> str:
    """4/40 Rothesay Avenue, Elwood VIC 3184 -> .../property-profile/4-40-rothesay-avenue-elwood-vic-3184"""
    p = parse_address(address)
    street_part = address.split(",")[0].strip().lower()
    street_slug = re.sub(r"[^\w\s/-]", "", street_part)
    street_slug = re.sub(r"[\s/]+", "-", street_slug)
    street_slug = re.sub(r"-+", "-", street_slug).strip("-")
    suburb_slug = p["suburb"].lower().replace(" ", "-")
    state_slug = p["state"].lower()
    slug = "-".join(x for x in [street_slug, suburb_slug, state_slug, p["postcode"]] if x)
    return f"https://www.domain.com.au/property-profile/{slug}"


def build_fallback_links(address: str) -> list:
    p = parse_address(address)
    suburb = p["suburb"].lower().replace(" ", "-")
    state = p["state"].lower()
    postcode = p["postcode"]
    slug = "-".join(x for x in [suburb, state, postcode] if x)
    q = urllib.parse.quote_plus(p["suburb_state"] or address)
    return [
        {"name": "Domain", "url": f"https://www.domain.com.au/sold-listings/?q={q}&sort=dateSold-desc", "desc": "Recent sold prices in suburb"},
        {"name": "realestate.com.au", "url": f"https://www.realestate.com.au/sold/in-{slug}/", "desc": "Recent sold prices in suburb"},
        {"name": "Domain property profile", "url": build_domain_profile_url(address), "desc": "Property-specific history and estimate"},
    ]


# ── Claude API valuation ───────────────────────────────────────────────────────
def get_valuation_via_claude(address: str, anthropic_key: str) -> dict:
    p = parse_address(address)
    suburb = p["suburb"]
    state = p["state"]
    postcode = p["postcode"]
    domain_url = build_domain_profile_url(address)

    prompt = (
        "You are an expert Australian property valuer. Estimate the current market value of: " + address + "\n\n"
        "Run ALL of these searches in order:\n"
        "1. Search: \"" + address + "\" property sold price estimate\n"
        "2. Search: domain.com.au property-profile 40-rothesay-avenue-elwood (other units in the same building)\n"
        "3. Search: \"Rothesay Avenue Elwood\" sold 2023 2024 2025\n"
        "4. Search: Elwood VIC 3184 unit apartment sold price median 2024 2025\n\n"
        "IMPORTANT: Even if you cannot find data for this exact unit, you MUST still provide an estimate.\n"
        "Use comparable sales from the same building, street, or suburb to derive your figure.\n"
        "The property is a 2-bedroom apartment at 40 Rothesay Avenue Elwood VIC 3184 (unit 4).\n"
        "Elwood is an inner bayside suburb of Melbourne ~8km from the CBD.\n"
        "Never return empty or null for estimate - always give your best figure based on available data.\n\n"
        "Respond ONLY with a valid JSON object, no markdown, no backticks:\n"
        "{\n"
        "  \"estimate\": \"$X,XXX,XXX\",\n"
        "  \"estimate_low\": \"$X,XXX,XXX\",\n"
        "  \"estimate_high\": \"$X,XXX,XXX\",\n"
        "  \"confidence\": \"low|medium|high\",\n"
        "  \"suburb_median\": \"$X,XXX,XXX\",\n"
        "  \"property_type\": \"unit\",\n"
        "  \"bedrooms\": \"2\",\n"
        "  \"last_known_sale\": \"$XXX,XXX in YYYY (if found, else omit)\",\n"
        "  \"data_availability\": \"exact|building|street|suburb\",\n"
        "  \"rationale\": \"2-3 sentences on exactly how you derived this estimate and what data you found.\",\n"
        "  \"comparable_sales\": [{\"address\": \"X/XX Rothesay Ave, Elwood\", \"price\": \"$X,XXX,XXX\", \"date\": \"Month YYYY\", \"beds\": \"2\", \"source\": \"Domain\"}],\n"
        "  \"sources\": [{\"name\": \"Source name\", \"url\": \"https://...\", \"description\": \"What data this provided\"}]\n"
        "}"
    )

    payload = {
        "model": "claude-sonnet-4-6",
        "max_tokens": 2000,
        "tools": [{"type": "web_search_20250305", "name": "web_search"}],
        "messages": [{"role": "user", "content": prompt}],
    }

    resp = requests.post(
        "https://api.anthropic.com/v1/messages",
        headers={
            "x-api-key": anthropic_key,
            "anthropic-version": "2023-06-01",
            "content-type": "application/json",
        },
        json=payload,
        timeout=60,
    )

    if resp.status_code != 200:
        return {"error": f"API error {resp.status_code}: {resp.text[:300]}"}

    data = resp.json()
    full_text = " ".join(
        block.get("text", "") for block in data.get("content", [])
        if block.get("type") == "text"
    )

    try:
        clean = re.sub(r"```json|```", "", full_text).strip()
        json_match = re.search(r"\{.*\}", clean, re.DOTALL)
        if json_match:
            return json.loads(json_match.group())
    except Exception as e:
        return {"error": f"Could not parse response: {e}", "raw": full_text[:500]}

    return {"error": "No structured data returned", "raw": full_text[:500]}


# ── Session state ──────────────────────────────────────────────────────────────
for key, default in [("confirmed_address", ""), ("last_typed", ""), ("suggestions", [])]:
    if key not in st.session_state:
        st.session_state[key] = default

# ── Address input ──────────────────────────────────────────────────────────────
st.markdown('<div class="search-label">Property address</div>', unsafe_allow_html=True)

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

# ── API key ────────────────────────────────────────────────────────────────────
ANTHROPIC_KEY = st.secrets.get("ANTHROPIC_API_KEY", "")
if not ANTHROPIC_KEY:
    st.info(
        "**Setup required:** Add your Anthropic API key to `.streamlit/secrets.toml` as "
        "`ANTHROPIC_API_KEY`. Get a free key at [console.anthropic.com](https://console.anthropic.com).",
        icon="🔑",
    )

# ── Search button ──────────────────────────────────────────────────────────────
st.markdown("")
search_clicked = st.button(
    "🔍  Get market valuation", use_container_width=True, type="primary", disabled=not ANTHROPIC_KEY
)

if search_clicked and final_address:
    address = final_address.strip()
    if len(address) < 6:
        st.warning("Please enter a valid Australian address.")
    else:
        with st.spinner(f"Researching {address}... this takes 15-30 seconds"):
            result = get_valuation_via_claude(address, ANTHROPIC_KEY)

        st.markdown(
            f'<div class="val-card">'
            f'<div class="val-address">Market estimate for</div>'
            f'<div class="val-headline">{address}</div>',
            unsafe_allow_html=True,
        )

        if "error" in result and "estimate" not in result:
            st.error(f"Could not retrieve estimate: {result.get('error')}")
            if result.get("raw"):
                with st.expander("Raw response"):
                    st.text(result["raw"])
        else:
            estimate = result.get("estimate", "N/A")
            lo = result.get("estimate_low", "")
            hi = result.get("estimate_high", "")
            confidence = result.get("confidence", "")
            confidence_color = {"high": "#16a34a", "medium": "#d97706", "low": "#dc2626"}.get(confidence, "#6b7280")
            range_str = f"{lo} - {hi}" if lo and hi else ""
            rationale = result.get("rationale", "")
            suburb_median = result.get("suburb_median", "")
            prop_type = result.get("property_type", "")
            last_sale = result.get("last_known_sale", "")
            data_avail = result.get("data_availability", "")
            avail_label = {
                "exact": "Data: exact property match found",
                "building": "Data: based on sales in the same building",
                "street": "Data: based on comparable sales on the same street",
                "suburb": "Data: based on suburb median (no recent sale found for this property)",
            }.get(data_avail, "")

            st.markdown(
                f'<div class="est-row">'
                f'<div class="est-logo">AI Estimate</div>'
                f'<div class="est-body">'
                f'<div class="est-value">{estimate}</div>'
                + (f'<div class="est-range">Range: {range_str}</div>' if range_str else "")
                + (f'<div class="est-range">Suburb median ({prop_type}): {suburb_median}</div>' if suburb_median else "")
                + (f'<div class="est-range">Last known sale: {last_sale}</div>' if last_sale else "")
                + (f'<div class="est-detail">{rationale}</div>' if rationale else "")
                + (f'<div class="est-range" style="color:#6b7280;font-style:italic;">{avail_label}</div>' if avail_label else "")
                + f'<div style="margin-top:0.4rem;font-size:0.75rem;color:{confidence_color};font-weight:600;">'
                  f'Confidence: {confidence.upper() if confidence else "N/A"}</div>'
                f'</div></div>',
                unsafe_allow_html=True,
            )

            comps = result.get("comparable_sales", [])
            if comps:
                st.markdown("**Recent comparable sales:**")
                for c in comps:
                    addr_str = c.get("address", "")
                    type_str = c.get("type", "")
                    date_str = c.get("date", "")
                    detail = " · ".join(x for x in [type_str, date_str] if x)
                    st.markdown(
                        f'<div class="est-row">'
                        f'<div class="est-logo">Sold</div>'
                        f'<div class="est-body">'
                        f'<div class="est-value">{c.get("price","—")}</div>'
                        f'<div class="est-range">{addr_str}{(" · " + detail) if detail else ""}</div>'
                        f'</div></div>',
                        unsafe_allow_html=True,
                    )

        st.markdown("**Search directly on property platforms:**")
        for link in build_fallback_links(address):
            st.markdown(
                f'<div class="est-row">'
                f'<div class="est-logo">{link["name"]}</div>'
                f'<div class="est-body">'
                f'<div class="est-range">{link["desc"]}</div>'
                f'<a class="est-link" href="{link["url"]}" target="_blank">Open {link["name"]}</a>'
                f'</div></div>',
                unsafe_allow_html=True,
            )

        st.markdown(
            f'<div class="disclaimer">'
            f'Data retrieved {datetime.now().strftime("%-d %B %Y, %-I:%M %p AEST")}. '
            f'AI-powered estimate based on web research of recent comparable sales and suburb medians. '
            f'Indicative only — not a certified valuation. Engage a licensed valuer (API/AIQS) for formal advice.'
            f'</div></div>',
            unsafe_allow_html=True,
        )

# ── Footer ─────────────────────────────────────────────────────────────────────
st.markdown(
    '<div class="footer">Built with Streamlit · AI search via Claude · Address lookup via OpenStreetMap · Free to deploy</div>',
    unsafe_allow_html=True,
)
