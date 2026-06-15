import streamlit as st
import requests
import re
import json
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
    text-align: center; padding: 3rem 0 2rem;
    border-bottom: 1px solid #e5e7eb; margin-bottom: 2rem;
  }
  .hero-tag {
    font-size: 0.72rem; letter-spacing: 0.16em;
    text-transform: uppercase; color: #6b7280; margin-bottom: 0.75rem;
  }
  .hero-title {
    font-family: 'DM Serif Display', serif;
    font-size: clamp(2rem, 5vw, 3.2rem);
    color: #0f172a; line-height: 1.15; margin: 0 0 0.5rem;
  }
  .hero-title em { font-style: italic; color: #1d4ed8; }
  .hero-sub { color: #6b7280; font-size: 0.95rem; }

  .search-label {
    font-size: 0.8rem; font-weight: 600; letter-spacing: 0.06em;
    text-transform: uppercase; color: #374151; margin-bottom: 0.4rem;
  }
  .val-card {
    background: #fff; border: 1px solid #e5e7eb; border-radius: 14px;
    padding: 2rem; margin-top: 1.5rem; box-shadow: 0 4px 24px rgba(0,0,0,0.06);
  }
  .val-address { font-size: 0.85rem; color: #6b7280; margin-bottom: 0.4rem; }
  .val-headline {
    font-family: 'DM Serif Display', serif; font-size: 1.55rem;
    color: #0f172a; margin-bottom: 1.5rem;
    border-bottom: 1px solid #f3f4f6; padding-bottom: 1rem;
  }
  .est-row {
    display: flex; align-items: flex-start; gap: 1.4rem;
    margin-bottom: 1.1rem; padding: 1rem 1.1rem;
    background: #f9fafb; border-radius: 10px; border-left: 3px solid #1d4ed8;
  }
  .est-logo {
    font-size: 0.7rem; font-weight: 700; letter-spacing: 0.08em;
    color: #1d4ed8; text-transform: uppercase; min-width: 90px; padding-top: 0.1rem;
  }
  .est-body { flex: 1; }
  .est-value {
    font-family: 'JetBrains Mono', monospace; font-size: 1.3rem;
    font-weight: 500; color: #111827;
  }
  .est-range { font-size: 0.78rem; color: #6b7280; margin-top: 0.15rem; }
  .est-detail { font-size: 0.82rem; color: #374151; margin-top: 0.35rem; line-height: 1.5; }
  .est-link {
    display: inline-block; margin-top: 0.4rem;
    font-size: 0.75rem; color: #1d4ed8; text-decoration: none;
  }
  .est-link:hover { text-decoration: underline; }
  .disclaimer {
    font-size: 0.73rem; color: #9ca3af; margin-top: 1.5rem;
    line-height: 1.6; border-top: 1px solid #f3f4f6; padding-top: 1rem;
  }
  .footer {
    text-align: center; font-size: 0.72rem; color: #d1d5db;
    margin-top: 3rem; letter-spacing: 0.04em;
  }
  div[data-testid="stButton"] button[kind="secondary"] {
    background: #f9fafb !important; border: 1px solid #e5e7eb !important;
    border-radius: 8px !important; text-align: left !important;
    font-size: 0.88rem !important; color: #111827 !important;
    padding: 0.55rem 0.9rem !important; margin-bottom: 4px !important;
  }
  div[data-testid="stButton"] button[kind="secondary"]:hover {
    background: #eff6ff !important; border-color: #1d4ed8 !important;
    color: #1d4ed8 !important;
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

# ── Helpers ────────────────────────────────────────────────────────────────────
NOMINATIM_HEADERS = {"User-Agent": "AusPropertyValuator/1.0 (streamlit open-source app)"}

def fetch_suggestions(query: str) -> list:
    if len(query) < 4:
        return []
    # Strip unit prefix for better geocoding: "4/40 Rothesay" → "40 Rothesay"
    clean = re.sub(r"^\d+\s*/\s*", "", query.strip())
    clean = re.sub(r"^(unit|apt|apartment|flat|shop)\s+\S+\s*,?\s*", "", clean, flags=re.IGNORECASE)
    search_q = clean or query
    try:
        resp = requests.get(
            "https://nominatim.openstreetmap.org/search",
            params={"q": search_q, "format": "json", "addressdetails": 1,
                    "limit": 7, "countrycodes": "au"},
            headers=NOMINATIM_HEADERS, timeout=5,
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
            headers={"User-Agent": "AusPropertyValuator/1.0"}, timeout=5,
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
    """Extract suburb, state, postcode from any AU address format."""
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


def get_valuation_via_claude(address: str, anthropic_key: str) -> dict:
    """
    Use Claude with web_search tool to research the property value.
    Returns structured data with estimate, comparable sales, and sources.
    """
    p = parse_address(address)
    suburb = p["suburb"]
    state = p["state"]
    postcode = p["postcode"]

    prompt = f"""You are an Australian property research assistant. 
    
Research the current market value of this property: {address}

Use your web search tool to find:
1. Recent sold prices for comparable properties at this specific address or on the same street in {suburb} {state} {postcode}
2. Current median house/unit price for {suburb} {state}
3. Any listing or estimate for this specific address if available

Then respond ONLY with a JSON object (no markdown, no backticks) in this exact format:
{{
  "estimate": "$X,XXX,XXX",
  "estimate_low": "$X,XXX,XXX",
  "estimate_high": "$X,XXX,XXX",
  "confidence": "low|medium|high",
  "suburb_median": "$X,XXX,XXX",
  "property_type": "apartment|house|townhouse|unit",
  "bedrooms_assumed": "2",
  "rationale": "Brief 1-2 sentence explanation of how the estimate was derived.",
  "comparable_sales": [
    {{"address": "X Rothesay Ave, Elwood", "price": "$X,XXX,XXX", "date": "Month Year", "type": "2br unit"}},
    {{"address": "...", "price": "...", "date": "...", "type": "..."}}
  ],
  "sources": [
    {{"name": "Domain.com.au", "url": "https://...", "description": "Sold listings in {suburb}"}},
    {{"name": "realestate.com.au", "url": "https://...", "description": "..."}}
  ]
}}

If you cannot find enough data, still return the JSON with your best estimate based on suburb median, and set confidence to "low".
Return ONLY the JSON object."""

    payload = {
        "model": "claude-sonnet-4-6",
        "max_tokens": 2000,
        "tools": [{"type": "web_search_20250305", "name": "web_search"}],
        "messages": [{"role": "user", "content": prompt}]
    }

    resp = requests.post(
        "https://api.anthropic.com/v1/messages",
        headers={
            "x-api-key": anthropic_key,
            "anthropic-version": "2023-06-01",
            "anthropic-beta": "interleaved-thinking-2025-05-14",
            "content-type": "application/json",
        },
        json=payload,
        timeout=60,
    )

    if resp.status_code != 200:
        return {"error": f"API error {resp.status_code}: {resp.text[:200]}"}

    data = resp.json()
    # Extract text from all content blocks
    full_text = " ".join(
        block.get("text", "") for block in data.get("content", [])
        if block.get("type") == "text"
    )

    # Parse JSON from response
    try:
        # Strip any accidental markdown fences
        clean = re.sub(r"```json|```", "", full_text).strip()
        # Find JSON object
        json_match = re.search(r"\{.*\}", clean, re.DOTALL)
        if json_match:
            return json.loads(json_match.group())
    except Exception as e:
        return {"error": f"Could not parse response: {str(e)}", "raw": full_text[:500]}

    return {"error": "No structured data returned", "raw": full_text[:500]}


def build_fallback_links(address: str) -> list:
    """Always provide direct links to property platforms."""
    p = parse_address(address)
    suburb = p["suburb"].lower().replace(" ", "-")
    state = p["state"].lower()
    postcode = p["postcode"]
    slug = "-".join(filter(None, [suburb, state, postcode]))
    import urllib.parse
    q = urllib.parse.quote_plus(p["suburb_state"] or address)
    return [
        {"name": "Domain", "url": f"https://www.domain.com.au/sold-listings/?q={q}&sort=dateSold-desc", "desc": "Recent sold prices in suburb"},
        {"name": "realestate.com.au", "url": f"https://www.realestate.com.au/sold/in-{slug}/", "desc": "Recent sold prices in suburb"},
        {"name": "Domain property profile", "url": f"https://www.domain.com.au/property-profile/{address.lower().replace(' ','-').replace(',','').replace('/','-')}", "desc": "Property-specific history"},
    ]


# ── Session state ──────────────────────────────────────────────────────────────
for key, default in [("confirmed_address", ""), ("last_typed", ""), ("suggestions", [])]:
    if key not in st.session_state:
        st.session_state[key] = default

# ── Address input ──────────────────────────────────────────────────────────────
st.markdown('<div class="search-label">Property address</div>', unsafe_allow_html=True)

typed = st.text_input(
    "address_field",
    value=st.session_state.confirmed_address or "",
    placeholder="e.g. 4/40 Rothesay Avenue, Elwood VIC 3186",
    label_visibility="collapsed",
)

if typed and typed != st.session_state.confirmed_address and typed != st.session_state.last_typed:
    st.session_state.last_typed = typed
    st.session_state.confirmed_address = ""
    if len(typed) >= 4:
        with st.spinner("Searching addresses…"):
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
    st.success(f"✅ {st.session_state.confirmed_address}")

# ── API key ────────────────────────────────────────────────────────────────────
ANTHROPIC_KEY = st.secrets.get("ANTHROPIC_API_KEY", "")

if not ANTHROPIC_KEY:
    st.info(
        "**Setup required:** Add your free Anthropic API key to `.streamlit/secrets.toml` as `ANTHROPIC_API_KEY` "
        "to enable AI-powered property search. Get a free key at [console.anthropic.com](https://console.anthropic.com).",
        icon="🔑"
    )

# ── Search ─────────────────────────────────────────────────────────────────────
st.markdown("")
search_clicked = st.button("🔍  Get market valuation", use_container_width=True, type="primary",
                           disabled=not ANTHROPIC_KEY)

if search_clicked and final_address:
    address = final_address.strip()
    if len(address) < 6:
        st.warning("Please enter a valid Australian address.")
    else:
        with st.spinner(f"Researching {address}… this takes 15–30 seconds"):
            result = get_valuation_via_claude(address, ANTHROPIC_KEY)

        st.markdown(f"""
        <div class="val-card">
          <div class="val-address">Market estimate for</div>
          <div class="val-headline">{address}</div>
        """, unsafe_allow_html=True)

        if "error" in result and "estimate" not in result:
            st.error(f"Could not retrieve estimate: {result.get('error')}")
            if result.get("raw"):
                with st.expander("Raw response"):
                    st.text(result["raw"])
        else:
            # Main estimate
            estimate = result.get("estimate", "N/A")
            lo = result.get("estimate_low", "")
            hi = result.get("estimate_high", "")
            confidence = result.get("confidence", "")
            confidence_color = {"high": "#16a34a", "medium": "#d97706", "low": "#dc2626"}.get(confidence, "#6b7280")
            range_str = f"{lo} – {hi}" if lo and hi else ""
            rationale = result.get("rationale", "")
            suburb_median = result.get("suburb_median", "")
            prop_type = result.get("property_type", "")

            st.markdown(f"""
            <div class="est-row">
              <div class="est-logo">AI Estimate</div>
              <div class="est-body">
                <div class="est-value">{estimate}</div>
                {"<div class='est-range'>Range: " + range_str + "</div>" if range_str else ""}
                {"<div class='est-range'>Suburb median (" + prop_type + "): " + suburb_median + "</div>" if suburb_median else ""}
                {"<div class='est-detail'>" + rationale + "</div>" if rationale else ""}
                <div style="margin-top:0.4rem;font-size:0.75rem;color:{confidence_color};font-weight:600;">
                  Confidence: {confidence.upper() if confidence else "—"}
                </div>
              </div>
            </div>
            """, unsafe_allow_html=True)

            # Comparable sales
            comps = result.get("comparable_sales", [])
            if comps:
                st.markdown("**Recent comparable sales:**")
                for c in comps:
                    st.markdown(f"""
                    <div class="est-row">
                      <div class="est-logo">Sold</div>
                      <div class="est-body">
                        <div class="est-value">{c.get('price','—')}</div>
                        <div class="est-range">{c.get('address','')}{' · ' + c.get('type','') if c.get('type') else ''}{' · ' + c.get('date','') if c.get('date') else ''}</div>
                      </div>
                    </div>
                    """, unsafe_allow_html=True)

        # Always show direct links
        st.markdown("**Search directly on property platforms:**")
        for link in build_fallback_links(address):
            st.markdown(f"""
            <div class="est-row">
              <div class="est-logo">{link['name']}</div>
              <div class="est-body">
                <div class="est-range">{link['desc']}</div>
                <a class="est-link" href="{link['url']}" target="_blank">Open {link['name']} ↗</a>
              </div>
            </div>
            """, unsafe_allow_html=True)

        st.markdown(f"""
          <div class="disclaimer">
            Data retrieved {datetime.now().strftime("%-d %B %Y, %-I:%M %p AEST")}.
            AI-powered estimate based on web research of recent comparable sales and suburb medians.
            Indicative only — not a certified valuation. Engage a licensed valuer (API/AIQS) for formal advice.
          </div>
        </div>
        """, unsafe_allow_html=True)

# ── Footer ─────────────────────────────────────────────────────────────────────
st.markdown("""
<div class="footer">Built with Streamlit · AI search via Claude · Address lookup via OpenStreetMap · Free to deploy</div>
""", unsafe_allow_html=True)
