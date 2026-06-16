import streamlit as st
import requests
from bs4 import BeautifulSoup
import re
import time
import urllib.parse
from datetime import datetime

st.set_page_config(page_title="AUS Property Valuator", page_icon="🏠", layout="centered", initial_sidebar_state="collapsed")

st.markdown("""
<style>
  @import url('https://fonts.googleapis.com/css2?family=DM+Serif+Display:ital@0;1&family=Inter:wght@300;400;500;600&family=JetBrains+Mono:wght@400;500&display=swap');
  html,body,[class*="css"]{font-family:'Inter',sans-serif;}
  #MainMenu,footer,header{visibility:hidden;}
  .block-container{padding:2rem 1rem 4rem;max-width:780px;}
  .hero{text-align:center;padding:3rem 0 2rem;border-bottom:1px solid #e5e7eb;margin-bottom:2rem;}
  .hero-tag{font-size:.72rem;letter-spacing:.16em;text-transform:uppercase;color:#6b7280;margin-bottom:.75rem;}
  .hero-title{font-family:'DM Serif Display',serif;font-size:clamp(2rem,5vw,3.2rem);color:#0f172a;line-height:1.15;margin:0 0 .5rem;}
  .hero-title em{font-style:italic;color:#1d4ed8;}
  .hero-sub{color:#6b7280;font-size:.95rem;}
  .section-head{font-size:.75rem;font-weight:700;letter-spacing:.1em;text-transform:uppercase;color:#6b7280;margin:1.6rem 0 .6rem;}
  .est-row{display:flex;align-items:flex-start;gap:1.2rem;margin-bottom:.9rem;padding:.9rem 1rem;background:#f9fafb;border-radius:10px;border-left:3px solid #1d4ed8;}
  .est-logo{font-size:.65rem;font-weight:700;letter-spacing:.08em;color:#1d4ed8;text-transform:uppercase;min-width:80px;padding-top:.15rem;line-height:1.4;}
  .est-body{flex:1;}
  .est-value{font-family:'JetBrains Mono',monospace;font-size:1.25rem;font-weight:500;color:#111827;}
  .est-range{font-size:.78rem;color:#6b7280;margin-top:.1rem;}
  .est-note{font-size:.78rem;color:#374151;margin-top:.25rem;line-height:1.5;}
  .est-link{display:inline-block;margin-top:.35rem;font-size:.75rem;color:#1d4ed8;text-decoration:none;}
  .est-link:hover{text-decoration:underline;}
  .comp-item{font-size:.78rem;color:#374151;margin-top:.2rem;padding:.25rem 0;}
  .val-card{background:#fff;border:1px solid #e5e7eb;border-radius:14px;padding:2rem;margin-top:1.5rem;box-shadow:0 4px 24px rgba(0,0,0,.06);}
  .val-address{font-size:.85rem;color:#6b7280;margin-bottom:.4rem;}
  .val-headline{font-family:'DM Serif Display',serif;font-size:1.5rem;color:#0f172a;margin-bottom:1.2rem;border-bottom:1px solid #f3f4f6;padding-bottom:.9rem;}
  .disclaimer{font-size:.72rem;color:#9ca3af;margin-top:1.4rem;line-height:1.6;border-top:1px solid #f3f4f6;padding-top:.9rem;}
  .footer{text-align:center;font-size:.72rem;color:#d1d5db;margin-top:3rem;}
  div[data-testid="stButton"] button[kind="secondary"]{background:#f9fafb!important;border:1px solid #e5e7eb!important;border-radius:8px!important;text-align:left!important;font-size:.88rem!important;color:#111827!important;padding:.55rem .9rem!important;margin-bottom:4px!important;}
  div[data-testid="stButton"] button[kind="secondary"]:hover{background:#eff6ff!important;border-color:#1d4ed8!important;color:#1d4ed8!important;}
</style>
""", unsafe_allow_html=True)

st.markdown("""
<div class="hero">
  <div class="hero-tag">Australian Property</div>
  <h1 class="hero-title">What's your home <em>worth?</em></h1>
  <p class="hero-sub">Free market estimate for any Australian address — no account or API key needed.</p>
</div>
""", unsafe_allow_html=True)

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,*/*;q=0.9",
    "Accept-Language": "en-AU,en;q=0.9",
}

# ── Address parsing ────────────────────────────────────────────────────────────
def parse_address(address):
    addr = re.sub(r"\s+", " ", address.strip())
    parts = [p.strip() for p in addr.split(",")]
    if parts and parts[-1].lower() in ("australia", "au"):
        parts = parts[:-1]
    suburb_part = parts[-1] if parts else ""
    pc_m = re.search(r"\b(\d{4})\b", suburb_part)
    postcode = pc_m.group(1) if pc_m else ""
    st_m = re.search(r"\b(VIC|NSW|QLD|SA|WA|TAS|ACT|NT)\b", suburb_part, re.I)
    state = st_m.group(1).upper() if st_m else ""
    suburb = suburb_part
    if postcode: suburb = suburb.replace(postcode, "")
    if state: suburb = re.sub(r"\b" + state + r"\b", "", suburb, flags=re.I)
    suburb = suburb.strip(", ").strip()

    street_raw = parts[0].strip() if parts else ""
    unit_m = re.match(r"^(\d+)\s*/\s*(\d+)\s+(.+)", street_raw)
    if unit_m:
        unit, street_num, street_name = unit_m.group(1), unit_m.group(2), unit_m.group(3).strip()
    else:
        unit = ""
        sn_m = re.match(r"^(\d+)\s+(.+)", street_raw)
        street_num = sn_m.group(1) if sn_m else ""
        street_name = sn_m.group(2).strip() if sn_m else street_raw

    return {
        "suburb": suburb, "state": state, "postcode": postcode,
        "unit": unit, "street_num": street_num, "street_name": street_name,
        "suburb_state": f"{suburb} {state} {postcode}".strip(),
    }

def domain_unit_slug(unit, street_num, street_name, suburb, state, postcode):
    """Build Domain property-profile slug for a specific unit."""
    sn = street_name.lower().replace(" ", "-")
    sub = suburb.lower().replace(" ", "-")
    return f"{unit}-{street_num}-{sn}-{sub}-{state.lower()}-{postcode}"

def domain_building_url(p):
    sn = p["street_name"].lower().replace(" ", "-")
    sub = p["suburb"].lower().replace(" ", "-")
    return f"https://www.domain.com.au/building-profile/{p['street_num']}-{sn}-{sub}-{p['state'].lower()}-{p['postcode']}/"

# ── Core scraper: Domain property profile for a single unit ───────────────────
def scrape_domain_unit(unit, street_num, street_name, suburb, state, postcode):
    """Fetch Domain property profile for one specific unit. Returns dict or None."""
    slug = domain_unit_slug(unit, street_num, street_name, suburb, state, postcode)
    url = f"https://www.domain.com.au/property-profile/{slug}"
    try:
        r = requests.get(url, headers=HEADERS, timeout=10, allow_redirects=True)
        if r.status_code != 200:
            return None
        text = r.text
        # Domain embeds estimate in page as text: "estimated to be worth around $Xk"
        est_m = re.search(r"estimated to be worth around \$([\d,]+\.?\d*[km]?)", text, re.I)
        range_m = re.search(r"range from \$([\d,]+\.?\d*[km]?) to \$([\d,]+\.?\d*[km]?)", text, re.I)
        beds_m = re.search(r"(\d+)\s+bedroom", text, re.I)
        sold_m = re.search(r"last sold[^\$]*\$([\d,]+\.?\d*[km]?)", text, re.I)
        sold_date_m = re.search(r"last sold (\d+ years? ago|\w+ \d{4})", text, re.I)

        def parse_val(s):
            if not s: return None
            s = s.replace(",", "")
            if s.endswith("m"): return int(float(s[:-1]) * 1_000_000)
            if s.endswith("k"): return int(float(s[:-1]) * 1_000)
            return int(float(s))

        est_val = parse_val(est_m.group(1)) if est_m else None
        lo_val  = parse_val(range_m.group(1)) if range_m else None
        hi_val  = parse_val(range_m.group(2)) if range_m else None
        sold_val = parse_val(sold_m.group(1)) if sold_m else None

        if est_val:
            return {
                "unit": unit, "url": url,
                "estimate": est_val, "low": lo_val, "high": hi_val,
                "beds": int(beds_m.group(1)) if beds_m else None,
                "last_sold": sold_val,
                "last_sold_when": sold_date_m.group(1) if sold_date_m else None,
            }
        if sold_val:
            return {"unit": unit, "url": url, "estimate": None,
                    "last_sold": sold_val, "last_sold_when": sold_date_m.group(1) if sold_date_m else None,
                    "beds": int(beds_m.group(1)) if beds_m else None, "low": None, "high": None}
    except Exception:
        pass
    return None

# ── Main estimation logic ──────────────────────────────────────────────────────
def get_estimate(address):
    p = parse_address(address)
    unit = p["unit"]
    street_num = p["street_num"]
    street_name = p["street_name"]
    suburb = p["suburb"]
    state = p["state"]
    postcode = p["postcode"]

    results = {"target": None, "siblings": [], "errors": []}

    # 1. Try the exact unit first
    if unit:
        data = scrape_domain_unit(unit, street_num, street_name, suburb, state, postcode)
        if data and (data.get("estimate") or data.get("last_sold")):
            results["target"] = data
        time.sleep(0.4)

    # 2. Try sibling units (1–6) to build comparable data and fill gaps
    for u in [str(i) for i in range(1, 7) if str(i) != unit]:
        sib = scrape_domain_unit(u, street_num, street_name, suburb, state, postcode)
        if sib and (sib.get("estimate") or sib.get("last_sold")):
            results["siblings"].append(sib)
        time.sleep(0.3)
        if len(results["siblings"]) >= 4:
            break

    return results, p

def format_dollars(val):
    if val is None: return None
    if val >= 1_000_000: return f"${val/1_000_000:.2f}m".rstrip("0").rstrip(".")+"m" if val % 1_000_000 else f"${val//1_000_000:,}m"
    return f"${val:,}"

# ── Address autocomplete ───────────────────────────────────────────────────────
def fetch_suggestions(query):
    if len(query) < 4: return []
    clean = re.sub(r"^\d+\s*/\s*", "", query.strip())
    clean = re.sub(r"^(unit|apt|apartment|flat|shop)\s+\S+\s*,?\s*", "", clean, flags=re.IGNORECASE)
    q = clean or query
    for url, params in [
        ("https://nominatim.openstreetmap.org/search",
         {"q": q, "format": "json", "addressdetails": 1, "limit": 7, "countrycodes": "au"}),
        ("https://photon.komoot.io/api/",
         {"q": q, "limit": 7, "lang": "en", "bbox": "112,-44,154,-10"}),
    ]:
        try:
            r = requests.get(url, params=params, headers={"User-Agent": "AusPropertyValuator/1.0"}, timeout=5)
            if r.status_code != 200: continue
            data = r.json()
            items = data if isinstance(data, list) else data.get("features", [])
            out, seen = [], set()
            for item in items:
                if isinstance(item, dict) and "display_name" in item:
                    parts = [x.strip() for x in item["display_name"].split(",") if x.strip().lower() != "australia"]
                    label = ", ".join(parts[:5])
                elif isinstance(item, dict) and "properties" in item:
                    pp = item["properties"]
                    if pp.get("country","").lower() not in ("australia","au"): continue
                    label = ", ".join(x for x in [pp.get("housenumber",""), pp.get("street",""),
                                                   pp.get("city","") or pp.get("suburb",""),
                                                   pp.get("state",""), pp.get("postcode","")] if x)
                else: continue
                if label and label not in seen:
                    seen.add(label); out.append(label)
            if out: return out
        except Exception:
            pass
    return []

# ── Session state ──────────────────────────────────────────────────────────────
for k, v in [("confirmed_address",""), ("last_typed",""), ("suggestions",[])]:
    if k not in st.session_state: st.session_state[k] = v

# ── UI ─────────────────────────────────────────────────────────────────────────
st.markdown('<p style="font-size:.8rem;font-weight:600;letter-spacing:.06em;text-transform:uppercase;color:#374151;margin-bottom:.4rem">Property address</p>', unsafe_allow_html=True)

typed = st.text_input("addr", value=st.session_state.confirmed_address or "",
                      placeholder="e.g. 4/40 Rothesay Avenue, Elwood VIC 3184",
                      label_visibility="collapsed")

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

st.markdown("")
go = st.button("🔍  Get market valuation", use_container_width=True, type="primary")

if go:
    address = final_address.strip()
    if len(address) < 6:
        st.warning("Please enter a valid Australian property address.")
    else:
        with st.spinner(f"Checking Domain property profiles for {address} and nearby units..."):
            results, p = get_estimate(address)

        target = results["target"]
        siblings = results["siblings"]

        st.markdown(
            f'<div class="val-card">'
            f'<div class="val-address">Market estimate for</div>'
            f'<div class="val-headline">{address}</div>',
            unsafe_allow_html=True,
        )

        # ── Target unit result ────────────────────────────────────────────────
        if target and target.get("estimate"):
            lo = format_dollars(target.get("low"))
            hi = format_dollars(target.get("high"))
            st.markdown('<div class="section-head">Domain estimate — this property</div>', unsafe_allow_html=True)
            st.markdown(
                f'<div class="est-row"><div class="est-logo">Domain<br/>Estimate</div>'
                f'<div class="est-body">'
                f'<div class="est-value">{format_dollars(target["estimate"])}</div>'
                + (f'<div class="est-range">Range: {lo} &ndash; {hi}</div>' if lo and hi else "")
                + (f'<div class="est-note">Last sold: {format_dollars(target["last_sold"])}'
                   + (f' ({target["last_sold_when"]})' if target.get("last_sold_when") else "") + '</div>'
                   if target.get("last_sold") else "")
                + f'<a class="est-link" href="{target["url"]}" target="_blank">View on Domain</a>'
                f'</div></div>',
                unsafe_allow_html=True,
            )

        elif target and target.get("last_sold"):
            st.markdown('<div class="section-head">This property — last known sale</div>', unsafe_allow_html=True)
            st.markdown(
                f'<div class="est-row"><div class="est-logo">Domain<br/>Last Sale</div>'
                f'<div class="est-body">'
                f'<div class="est-value">{format_dollars(target["last_sold"])}</div>'
                + (f'<div class="est-range">{target["last_sold_when"]}</div>' if target.get("last_sold_when") else "")
                + '<div class="est-note">No current Domain Estimate available for this unit — using comparable units below.</div>'
                + f'<a class="est-link" href="{target["url"]}" target="_blank">View on Domain</a>'
                f'</div></div>',
                unsafe_allow_html=True,
            )

        # ── Estimate from siblings if no target estimate ───────────────────────
        sib_estimates = [s["estimate"] for s in siblings if s.get("estimate")]
        if not (target and target.get("estimate")) and sib_estimates:
            # Weight by bed count similarity
            avg = sum(sib_estimates) // len(sib_estimates)
            lo_sib = min(sib_estimates)
            hi_sib = max(sib_estimates)
            st.markdown('<div class="section-head">Estimated value — derived from same building</div>', unsafe_allow_html=True)
            st.markdown(
                f'<div class="est-row"><div class="est-logo">Building<br/>Average</div>'
                f'<div class="est-body">'
                f'<div class="est-value">{format_dollars(avg)}</div>'
                f'<div class="est-range">Range of units in building: {format_dollars(lo_sib)} &ndash; {format_dollars(hi_sib)}</div>'
                f'<div class="est-note">Domain has no estimate for unit {p["unit"]} directly. '
                f'This is the average of {len(sib_estimates)} other units at {p["street_num"]} {p["street_name"]} with active estimates.</div>'
                f'</div></div>',
                unsafe_allow_html=True,
            )

        # ── Comparable units in the building ─────────────────────────────────
        if siblings:
            st.markdown('<div class="section-head">Other units in the same building (Domain)</div>', unsafe_allow_html=True)
            for s in siblings:
                beds_str = f'{s["beds"]}br ' if s.get("beds") else ""
                sold_str = (f' &bull; Last sold {format_dollars(s["last_sold"])}'
                           + (f' ({s["last_sold_when"]})' if s.get("last_sold_when") else "")
                           if s.get("last_sold") else "")
                est_str = format_dollars(s["estimate"]) if s.get("estimate") else "No estimate"
                lo = format_dollars(s.get("low"))
                hi = format_dollars(s.get("high"))
                st.markdown(
                    f'<div class="est-row"><div class="est-logo">Unit {s["unit"]}<br/>{beds_str}</div>'
                    f'<div class="est-body">'
                    f'<div class="est-value">{est_str}</div>'
                    + (f'<div class="est-range">Range: {lo} &ndash; {hi}</div>' if lo and hi else "")
                    + (f'<div class="est-range">{sold_str.replace(" &bull; ","")}</div>' if sold_str else "")
                    + f'<a class="est-link" href="{s["url"]}" target="_blank">View unit {s["unit"]} on Domain</a>'
                    f'</div></div>',
                    unsafe_allow_html=True,
                )

        if not target and not siblings:
            st.info(
                f"Domain has no property profile for this address or its neighbouring units. "
                f"Try the direct links below — the building profile and street profile on Domain may have the data.",
                icon="ℹ️"
            )

        # ── Always-show direct links ───────────────────────────────────────────
        unit = p["unit"]
        sn = p["street_name"].lower().replace(" ","-")
        sub = p["suburb"].lower().replace(" ","-")
        state_l = p["state"].lower()
        pc = p["postcode"]
        snum = p["street_num"]
        q = urllib.parse.quote_plus(p["suburb_state"])

        st.markdown('<div class="section-head">Research further</div>', unsafe_allow_html=True)
        links = [
            ("Domain building profile", domain_building_url(p),
             f"All units at {snum} {p['street_name']} with estimates"),
            ("Domain street profile", f"https://www.domain.com.au/street-profile/rothesay-avenue-{sub}-{state_l}-{pc}/",
             "Recent sales on the same street"),
            ("Domain sold listings", f"https://www.domain.com.au/sold-listings/?q={q}&sort=dateSold-desc",
             f"Recent sales in {p['suburb']}"),
            ("AuHousePrices.com", f"https://www.auhouseprices.com/sold/list/{p['state']}/{urllib.parse.quote(p['suburb'])}/",
             "Free sold price history — no login needed"),
            ("PropertyValue.com.au", f"https://www.propertyvalue.com.au/search/?q={urllib.parse.quote_plus(address)}",
             "Another free automated estimate"),
        ]
        for label, url, note in links:
            st.markdown(
                f'<div class="est-row"><div class="est-logo">{label.split(".")[0].split(" ")[0]}</div>'
                f'<div class="est-body"><div class="est-note">{note}</div>'
                f'<a class="est-link" href="{url}" target="_blank">Open {label}</a>'
                f'</div></div>',
                unsafe_allow_html=True,
            )

        st.markdown(
            f'<div class="disclaimer">Retrieved {datetime.now().strftime("%-d %B %Y, %-I:%M %p AEST")}. '
            f'Estimates sourced from Domain.com.au property profiles. Indicative only — not a certified valuation. '
            f'Engage a licensed valuer (API/AIQS member) for formal advice.</div></div>',
            unsafe_allow_html=True,
        )

st.markdown('<div class="footer">Built with Streamlit &middot; Data via Domain.com.au &middot; 100% free</div>', unsafe_allow_html=True)
