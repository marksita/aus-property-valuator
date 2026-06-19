import streamlit as st
import urllib.parse
import re
import requests
from bs4 import BeautifulSoup
import time

st.set_page_config(page_title="AUS Property Valuator", page_icon="🏠", layout="centered", initial_sidebar_state="collapsed")

st.markdown("""
<style>
  @import url('https://fonts.googleapis.com/css2?family=DM+Serif+Display:ital@0;1&family=Inter:wght@300;400;500;600;700&family=JetBrains+Mono:wght@400;500&display=swap');
  html,body,[class*="css"]{font-family:'Inter',sans-serif;}
  #MainMenu,footer,header{visibility:hidden;}
  .block-container{padding:2rem 1.5rem 5rem;max-width:800px;}

  .hero{text-align:center;padding:3.5rem 0 2.5rem;margin-bottom:2rem;}
  .hero-tag{font-size:.7rem;letter-spacing:.2em;text-transform:uppercase;color:#94a3b8;margin-bottom:1rem;font-weight:600;}
  .hero-title{font-family:'DM Serif Display',serif;font-size:clamp(2.2rem,5vw,3.5rem);color:#0f172a;line-height:1.1;margin:0 0 .75rem;}
  .hero-title em{font-style:italic;color:#2563eb;}
  .hero-sub{color:#64748b;font-size:1rem;max-width:480px;margin:0 auto;line-height:1.6;}

  .estimate-banner{background:linear-gradient(135deg,#1e3a8a 0%,#2563eb 100%);border-radius:16px;padding:2rem 2.2rem;margin:1.5rem 0;color:#fff;}
  .estimate-banner-label{font-size:.68rem;font-weight:700;letter-spacing:.16em;text-transform:uppercase;opacity:.7;margin-bottom:.5rem;}
  .estimate-banner-address{font-size:.88rem;opacity:.8;margin-bottom:1.2rem;}
  .estimate-banner-value{font-family:'JetBrains Mono',monospace;font-size:2.8rem;font-weight:500;letter-spacing:-.02em;margin-bottom:.3rem;}
  .estimate-banner-range{font-size:.88rem;opacity:.75;margin-bottom:1rem;}
  .estimate-banner-basis{font-size:.78rem;opacity:.65;line-height:1.5;border-top:1px solid rgba(255,255,255,.2);padding-top:.8rem;margin-top:.3rem;}
  .confidence-chip{display:inline-block;background:rgba(255,255,255,.15);border-radius:20px;padding:.2rem .75rem;font-size:.72rem;font-weight:600;letter-spacing:.06em;text-transform:uppercase;margin-top:.6rem;}

  .comp-row{display:flex;align-items:center;gap:1rem;padding:.7rem 0;border-bottom:1px solid #f1f5f9;}
  .comp-row:last-child{border-bottom:none;}
  .comp-unit{font-size:.72rem;font-weight:700;color:#2563eb;text-transform:uppercase;width:52px;flex-shrink:0;}
  .comp-detail{flex:1;font-size:.82rem;color:#374151;line-height:1.4;}
  .comp-price{font-family:'JetBrains Mono',monospace;font-size:.9rem;font-weight:500;color:#0f172a;flex-shrink:0;}
  .comp-card{background:#fff;border:1.5px solid #e2e8f0;border-radius:12px;padding:1rem 1.3rem;margin-bottom:1rem;}
  .comp-card-title{font-size:.72rem;font-weight:700;letter-spacing:.1em;text-transform:uppercase;color:#94a3b8;margin-bottom:.5rem;}

  .section-title{font-size:.68rem;font-weight:700;letter-spacing:.14em;text-transform:uppercase;color:#94a3b8;margin:2rem 0 .75rem;display:flex;align-items:center;gap:.5rem;}
  .section-title::after{content:'';flex:1;height:1px;background:#f1f5f9;}

  .link-grid{display:grid;grid-template-columns:1fr 1fr;gap:.75rem;margin-bottom:.75rem;}
  .link-card{display:block;background:#fff;border:1.5px solid #e2e8f0;border-radius:12px;padding:1rem 1.1rem;text-decoration:none;transition:all .15s ease;position:relative;}
  .link-card:hover{border-color:#2563eb;box-shadow:0 4px 16px rgba(37,99,235,.1);transform:translateY(-1px);}
  .link-card-logo{font-size:.62rem;font-weight:700;letter-spacing:.1em;text-transform:uppercase;color:#2563eb;margin-bottom:.3rem;}
  .link-card-title{font-size:.88rem;font-weight:600;color:#0f172a;margin-bottom:.15rem;}
  .link-card-desc{font-size:.74rem;color:#64748b;line-height:1.4;}
  .link-card-arrow{position:absolute;top:.9rem;right:.9rem;font-size:.8rem;color:#cbd5e1;}
  .link-card:hover .link-card-arrow{color:#2563eb;}
  .link-card.featured{background:#eff6ff;border-color:#bfdbfe;}

  .disclaimer{font-size:.72rem;color:#94a3b8;margin-top:1.5rem;line-height:1.6;border-top:1px solid #f1f5f9;padding-top:1rem;}
  .footer{text-align:center;font-size:.72rem;color:#cbd5e1;margin-top:4rem;}
  @media(max-width:600px){.link-grid{grid-template-columns:1fr;}.estimate-banner-value{font-size:2.2rem;}}
  div[data-testid="stButton"] button[kind="secondary"]{background:#f8fafc!important;border:1.5px solid #e2e8f0!important;border-radius:10px!important;text-align:left!important;font-size:.85rem!important;color:#0f172a!important;padding:.6rem 1rem!important;margin-bottom:5px!important;}
  div[data-testid="stButton"] button[kind="secondary"]:hover{background:#eff6ff!important;border-color:#2563eb!important;color:#1d4ed8!important;}
</style>
""", unsafe_allow_html=True)

st.markdown("""
<div class="hero">
  <div class="hero-tag">Australian Property Research</div>
  <h1 class="hero-title">What's your property<br/><em>worth?</em></h1>
  <p class="hero-sub">Enter any Australian address for an estimated market valuation and links to every major property platform.</p>
</div>
""", unsafe_allow_html=True)

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,*/*;q=0.9",
    "Accept-Language": "en-AU,en;q=0.9",
}

# ── Helpers ────────────────────────────────────────────────────────────────────
def parse_address(address: str) -> dict:
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
        "full": address.strip(),
    }

def fmt(val: int) -> str:
    if val >= 1_000_000:
        m = val / 1_000_000
        return f"${m:.2f}m".rstrip("0").rstrip(".") + "m" if val % 1_000_000 else f"${val//1_000_000}m"
    return f"${val:,}"

def domain_profile_url(unit, street_num, street_name, suburb, state, postcode):
    sn = street_name.lower().replace(" ", "-")
    sub = suburb.lower().replace(" ", "-")
    if unit:
        return f"https://www.domain.com.au/property-profile/{unit}-{street_num}-{sn}-{sub}-{state.lower()}-{postcode}"
    return f"https://www.domain.com.au/property-profile/{street_num}-{sn}-{sub}-{state.lower()}-{postcode}"

def scrape_domain_profile(url: str) -> dict | None:
    """Fetch a Domain property profile and extract estimate + sale info."""
    try:
        r = requests.get(url, headers=HEADERS, timeout=10, allow_redirects=True)
        if r.status_code != 200:
            return None
        text = r.text

        def parse_val(s):
            if not s: return None
            s = s.replace(",", "").replace("$", "").strip()
            if s.lower().endswith("m"): return int(float(s[:-1]) * 1_000_000)
            if s.lower().endswith("k"): return int(float(s[:-1]) * 1_000)
            try: return int(float(s))
            except: return None

        # Domain shows: "estimated to be worth around $625k"
        est_m   = re.search(r"estimated to be worth around \$([0-9.,kmKM]+)", text, re.I)
        low_m   = re.search(r"range from \$([0-9.,kmKM]+) to \$([0-9.,kmKM]+)", text, re.I)
        beds_m  = re.search(r"(\d+)\s+bedroom", text, re.I)
        baths_m = re.search(r"(\d+)\s+bathroom", text, re.I)
        sold_m  = re.search(r"last sold[^$\n]*\$([0-9.,kmKM]+)", text, re.I)
        when_m  = re.search(r"last sold (\d+ years? ago|\w+ \d{4})", text, re.I)
        type_m  = re.search(r"is (an? )?(Unit|Apartment|House|Townhouse|Villa)", text, re.I)

        est  = parse_val(est_m.group(1)) if est_m else None
        lo   = parse_val(low_m.group(1)) if low_m else None
        hi   = parse_val(low_m.group(2)) if low_m else None
        sold = parse_val(sold_m.group(1)) if sold_m else None

        if est or sold:
            return {
                "estimate": est, "low": lo, "high": hi,
                "last_sold": sold,
                "last_sold_when": when_m.group(1) if when_m else None,
                "beds": int(beds_m.group(1)) if beds_m else None,
                "baths": int(baths_m.group(1)) if baths_m else None,
                "prop_type": type_m.group(2).title() if type_m else None,
                "url": url,
            }
    except Exception:
        pass
    return None

def get_valuation(address: str) -> dict:
    """
    Strategy:
    1. Try the exact unit's Domain profile.
    2. If no estimate found, try sibling units 1-6 in the same building.
    3. Derive an estimate from siblings with matching bed count.
    4. Always return something useful.
    """
    p = parse_address(address)
    unit = p["unit"]
    snum = p["street_num"]
    sname = p["street_name"]
    suburb = p["suburb"]
    state = p["state"]
    pc = p["postcode"]

    target = None
    siblings = []

    # 1. Try exact unit
    if unit:
        url = domain_profile_url(unit, snum, sname, suburb, state, pc)
        target = scrape_domain_profile(url)
        if target:
            target["unit"] = unit
        time.sleep(0.4)

    # 2. Try sibling units to build comparables
    checked = 0
    for u in [str(i) for i in range(1, 10) if str(i) != unit]:
        url = domain_profile_url(u, snum, sname, suburb, state, pc)
        sib = scrape_domain_profile(url)
        if sib and (sib.get("estimate") or sib.get("last_sold")):
            sib["unit"] = u
            siblings.append(sib)
        checked += 1
        time.sleep(0.3)
        if checked >= 5:  # check up to 5 siblings
            break

    # 3. Also try the property without a unit (house/townhouse)
    if not unit:
        url = domain_profile_url("", snum, sname, suburb, state, pc)
        target = scrape_domain_profile(url)

    # 4. Derive estimate
    derived = None
    basis = ""
    confidence = "low"

    if target and target.get("estimate"):
        derived = {"value": target["estimate"], "low": target.get("low"), "high": target.get("high")}
        basis = f"Domain Estimate for this property"
        confidence = "high"
    elif siblings:
        # Match beds if possible
        target_beds = target.get("beds") if target else None
        matching = [s for s in siblings if s.get("estimate") and s.get("beds") == target_beds] if target_beds else []
        pool = matching or [s for s in siblings if s.get("estimate")]
        if pool:
            estimates = [s["estimate"] for s in pool]
            avg = sum(estimates) // len(estimates)
            lo = min(int(e * 0.9) for e in estimates)
            hi = max(int(e * 1.1) for e in estimates)
            derived = {"value": avg, "low": lo, "high": hi}
            bed_note = f" (matching {target_beds}br)" if matching and target_beds else ""
            basis = f"Average of {len(pool)} comparable unit{'' if len(pool)==1 else 's'} in this building{bed_note} with Domain Estimates"
            confidence = "medium" if len(pool) >= 2 else "low"
        elif target and target.get("last_sold"):
            # Inflate last sold by ~5% p.a.
            yrs_m = re.search(r"(\d+)\s+year", target.get("last_sold_when", ""), re.I)
            yrs = int(yrs_m.group(1)) if yrs_m else 5
            inflated = int(target["last_sold"] * (1.05 ** yrs))
            derived = {"value": inflated, "low": int(inflated * 0.88), "high": int(inflated * 1.12)}
            basis = f"Last sold {fmt(target['last_sold'])} ({target.get('last_sold_when','')}) — inflated ~5%/yr"
            confidence = "low"

    return {
        "target": target,
        "siblings": siblings,
        "derived": derived,
        "basis": basis,
        "confidence": confidence,
        "parsed": p,
    }

def build_links(p: dict) -> dict:
    sub_slug = p["suburb"].lower().replace(" ", "-")
    state_l = p["state"].lower()
    pc = p["postcode"]
    sname_slug = p["street_name"].lower().replace(" ", "-")
    snum = p["street_num"]
    rea_sub = "-".join(x for x in [sub_slug, state_l, pc] if x)
    q_sub = urllib.parse.quote_plus(p["suburb_state"])
    q_full = urllib.parse.quote_plus(p["full"])
    bldg_slug = f"{snum}-{sname_slug}-{sub_slug}-{state_l}-{pc}"
    street_slug = f"{sname_slug}-{sub_slug}-{state_l}-{pc}"
    return {
        "domain_profile": domain_profile_url(p["unit"], snum, p["street_name"], p["suburb"], p["state"], pc),
        "domain_building": f"https://www.domain.com.au/building-profile/{bldg_slug}/",
        "domain_street": f"https://www.domain.com.au/street-profile/{street_slug}/",
        "domain_sold": f"https://www.domain.com.au/sold-listings/?q={q_sub}&sort=dateSold-desc",
        "domain_suburb": f"https://www.domain.com.au/suburb-profile/{sub_slug}-{state_l}-{pc}/",
        "rea_sold": f"https://www.realestate.com.au/sold/in-{rea_sub}/",
        "rea_suburb": f"https://www.realestate.com.au/neighbourhoods/{rea_sub}/",
        "propvalue": f"https://www.propertyvalue.com.au/search/?q={q_full}",
        "auhouseprices": f"https://www.auhouseprices.com/sold/list/{p['state']}/{urllib.parse.quote(p['suburb'])}/",
    }

def fetch_suggestions(query: str) -> list:
    if len(query) < 4: return []
    clean = re.sub(r"^\d+\s*/\s*", "", query.strip())
    clean = re.sub(r"^(unit|apt|apartment|flat)\s+\S+\s*,?\s*", "", clean, flags=re.I)
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
                if "display_name" in item:
                    parts = [x.strip() for x in item["display_name"].split(",") if x.strip().lower() != "australia"]
                    label = ", ".join(parts[:5])
                elif "properties" in item:
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
for k, v in [("confirmed",""), ("last_typed",""), ("suggestions",[]), ("searched",""), ("result", None)]:
    if k not in st.session_state: st.session_state[k] = v

# ── Search UI ──────────────────────────────────────────────────────────────────
typed = st.text_input("addr", value=st.session_state.confirmed or "",
                      placeholder="e.g. 4/40 Rothesay Avenue, Elwood VIC 3184",
                      label_visibility="collapsed")

if typed and typed != st.session_state.confirmed and typed != st.session_state.last_typed:
    st.session_state.last_typed = typed
    st.session_state.confirmed = ""
    st.session_state.searched = ""
    st.session_state.result = None
    if len(typed) >= 4:
        with st.spinner("Finding address..."):
            st.session_state.suggestions = fetch_suggestions(typed)
    else:
        st.session_state.suggestions = []

if st.session_state.suggestions and not st.session_state.confirmed:
    st.caption("Select your address:")
    for s in st.session_state.suggestions:
        if st.button(f"📍 {s}", key=f"s_{hash(s)}", use_container_width=True):
            st.session_state.confirmed = s
            st.session_state.suggestions = []
            st.rerun()

final = st.session_state.confirmed or typed
if st.session_state.confirmed:
    st.success(f"📍 {st.session_state.confirmed}")

st.markdown("")
go = st.button("🔍  Get market valuation", use_container_width=True, type="primary")

if go and len(final.strip()) > 5:
    st.session_state.searched = final.strip()
    st.session_state.result = None  # force re-fetch

# ── Results ────────────────────────────────────────────────────────────────────
if st.session_state.searched:
    address = st.session_state.searched

    if st.session_state.result is None:
        with st.spinner("Checking Domain property profiles... (10–20 seconds)"):
            st.session_state.result = get_valuation(address)

    res = st.session_state.result
    p = res["parsed"]
    derived = res["derived"]
    target = res["target"]
    siblings = res["siblings"]
    confidence = res["confidence"]
    basis = res["basis"]
    links = build_links(p)

    conf_labels = {"high": "High confidence", "medium": "Medium confidence", "low": "Low confidence — limited data"}
    conf_emoji  = {"high": "🟢", "medium": "🟡", "low": "🔴"}

    # ── Estimate banner ────────────────────────────────────────────────────────
    if derived:
        lo_str = fmt(derived["low"])  if derived.get("low")  else ""
        hi_str = fmt(derived["high"]) if derived.get("high") else ""
        range_str = f"Estimated range: {lo_str} – {hi_str}" if lo_str and hi_str else ""

        st.markdown(f"""
        <div class="estimate-banner">
          <div class="estimate-banner-label">Estimated market value</div>
          <div class="estimate-banner-address">{address}</div>
          <div class="estimate-banner-value">{fmt(derived['value'])}</div>
          {"<div class='estimate-banner-range'>" + range_str + "</div>" if range_str else ""}
          <div class="estimate-banner-basis">{basis}</div>
          <div class="confidence-chip">{conf_emoji[confidence]} {conf_labels[confidence]}</div>
        </div>
        """, unsafe_allow_html=True)

    else:
        st.info(
            "Could not retrieve enough data from Domain to produce an estimate. "
            "Use the links below to check each platform directly.",
            icon="ℹ️"
        )

    # ── Comparable units ───────────────────────────────────────────────────────
    if siblings:
        all_units = ([target] if target else []) + siblings
        all_units = [u for u in all_units if u]
        st.markdown('<div class="section-title">Comparable units in this building (Domain)</div>', unsafe_allow_html=True)
        st.markdown('<div class="comp-card"><div class="comp-card-title">40 Rothesay Ave — units found on Domain</div>', unsafe_allow_html=True)
        for u in sorted(all_units, key=lambda x: int(x.get("unit","0") or 0)):
            unit_label = f"Unit {u['unit']}" if u.get("unit") else "This property"
            is_target = u.get("unit") == p["unit"]
            beds = f"{u['beds']}br " if u.get("beds") else ""
            baths = f"{u['baths']}ba" if u.get("baths") else ""
            spec = (beds + baths).strip()
            est_str = fmt(u["estimate"]) if u.get("estimate") else "—"
            sold_str = (f"Last sold {fmt(u['last_sold'])}" +
                       (f" ({u['last_sold_when']})" if u.get("last_sold_when") else "")) if u.get("last_sold") else ""
            highlight = "font-weight:700;color:#1d4ed8;" if is_target else ""
            st.markdown(
                f'<div class="comp-row">'
                f'<div class="comp-unit" style="{highlight}">{unit_label}</div>'
                f'<div class="comp-detail">{spec}{"  ·  " + sold_str if sold_str else ""}</div>'
                f'<div class="comp-price"><a href="{u["url"]}" target="_blank" style="color:#0f172a;text-decoration:none;">{est_str}</a></div>'
                f'</div>',
                unsafe_allow_html=True,
            )
        st.markdown('</div>', unsafe_allow_html=True)

    # ── Links ──────────────────────────────────────────────────────────────────
    st.markdown('<div class="section-title">Explore further</div>', unsafe_allow_html=True)
    st.markdown(f"""
    <div class="link-grid">
      <a class="link-card featured" href="{links['domain_profile']}" target="_blank">
        <div class="link-card-logo">Domain</div>
        <div class="link-card-title">Property Profile</div>
        <div class="link-card-desc">Domain Estimate, sale history &amp; details for this address</div>
        <div class="link-card-arrow">&#8599;</div>
      </a>
      <a class="link-card featured" href="{links['domain_building']}" target="_blank">
        <div class="link-card-logo">Domain</div>
        <div class="link-card-title">Building Profile</div>
        <div class="link-card-desc">All units at {p['street_num']} {p['street_name']} with estimates</div>
        <div class="link-card-arrow">&#8599;</div>
      </a>
      <a class="link-card" href="{links['domain_sold']}" target="_blank">
        <div class="link-card-logo">Domain</div>
        <div class="link-card-title">Recent Sales in {p['suburb']}</div>
        <div class="link-card-desc">Sold listings sorted by date</div>
        <div class="link-card-arrow">&#8599;</div>
      </a>
      <a class="link-card" href="{links['rea_sold']}" target="_blank">
        <div class="link-card-logo">realestate.com.au</div>
        <div class="link-card-title">Recent Sales in {p['suburb']}</div>
        <div class="link-card-desc">PropTrack sold price history</div>
        <div class="link-card-arrow">&#8599;</div>
      </a>
      <a class="link-card" href="{links['propvalue']}" target="_blank">
        <div class="link-card-logo">PropertyValue.com.au</div>
        <div class="link-card-title">Free AVM Estimate</div>
        <div class="link-card-desc">Automated valuation — no account needed</div>
        <div class="link-card-arrow">&#8599;</div>
      </a>
      <a class="link-card" href="{links['auhouseprices']}" target="_blank">
        <div class="link-card-logo">AuHousePrices.com</div>
        <div class="link-card-title">Sold Price History</div>
        <div class="link-card-desc">Free sold price database — no login</div>
        <div class="link-card-arrow">&#8599;</div>
      </a>
      <a class="link-card" href="{links['domain_street']}" target="_blank">
        <div class="link-card-logo">Domain</div>
        <div class="link-card-title">Street Profile</div>
        <div class="link-card-desc">All sales on {p['street_name']} over time</div>
        <div class="link-card-arrow">&#8599;</div>
      </a>
      <a class="link-card" href="{links['domain_suburb']}" target="_blank">
        <div class="link-card-logo">Domain</div>
        <div class="link-card-title">{p['suburb']} Suburb Profile</div>
        <div class="link-card-desc">Median prices, trends &amp; clearance rates</div>
        <div class="link-card-arrow">&#8599;</div>
      </a>
    </div>
    """, unsafe_allow_html=True)

    st.markdown(
        '<div class="disclaimer">Estimates derived from publicly available Domain property profile pages. '
        'Indicative only — not a certified valuation. Engage a licensed property valuer (API/AIQS) for formal advice. '
        'Medium/low confidence estimates are based on comparable units in the same building, not a direct estimate for this property.</div>',
        unsafe_allow_html=True,
    )

st.markdown('<div class="footer">Built with Streamlit &middot; Data via Domain.com.au &middot; 100% free</div>', unsafe_allow_html=True)
