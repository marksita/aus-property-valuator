import streamlit as st
import urllib.parse
import re

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

  .address-card{background:#fff;border:2px solid #e2e8f0;border-radius:16px;padding:2rem;margin-bottom:1.5rem;box-shadow:0 2px 12px rgba(0,0,0,.04);}
  .address-display{font-family:'DM Serif Display',serif;font-size:1.4rem;color:#0f172a;margin:0 0 .25rem;}
  .address-sub{font-size:.82rem;color:#94a3b8;margin:0;}

  .section-title{font-size:.68rem;font-weight:700;letter-spacing:.14em;text-transform:uppercase;color:#94a3b8;margin:2rem 0 .75rem;display:flex;align-items:center;gap:.5rem;}
  .section-title::after{content:'';flex:1;height:1px;background:#f1f5f9;}

  .link-grid{display:grid;grid-template-columns:1fr 1fr;gap:.75rem;margin-bottom:.75rem;}
  .link-grid.single{grid-template-columns:1fr;}

  .link-card{display:block;background:#fff;border:1.5px solid #e2e8f0;border-radius:12px;padding:1.1rem 1.2rem;text-decoration:none;transition:all .15s ease;position:relative;overflow:hidden;}
  .link-card:hover{border-color:#2563eb;box-shadow:0 4px 16px rgba(37,99,235,.1);transform:translateY(-1px);}
  .link-card::before{content:'';position:absolute;top:0;left:0;width:3px;height:100%;background:#2563eb;opacity:0;}
  .link-card:hover::before{opacity:1;}
  .link-card-logo{font-size:.62rem;font-weight:700;letter-spacing:.1em;text-transform:uppercase;color:#2563eb;margin-bottom:.35rem;}
  .link-card-title{font-size:.9rem;font-weight:600;color:#0f172a;margin-bottom:.2rem;line-height:1.3;}
  .link-card-desc{font-size:.75rem;color:#64748b;line-height:1.4;}
  .link-card-arrow{position:absolute;top:1rem;right:1rem;font-size:.8rem;color:#cbd5e1;}
  .link-card:hover .link-card-arrow{color:#2563eb;}

  .link-card.featured{background:linear-gradient(135deg,#eff6ff 0%,#fff 100%);border-color:#bfdbfe;}
  .link-card.featured .link-card-logo{color:#1d4ed8;}

  .info-box{background:#f8fafc;border:1.5px solid #e2e8f0;border-radius:12px;padding:1.1rem 1.3rem;margin-bottom:1rem;font-size:.82rem;color:#475569;line-height:1.6;}
  .info-box strong{color:#0f172a;}

  .footer{text-align:center;font-size:.72rem;color:#cbd5e1;margin-top:4rem;letter-spacing:.04em;}

  div[data-testid="stButton"] button[kind="secondary"]{background:#f8fafc!important;border:1.5px solid #e2e8f0!important;border-radius:10px!important;text-align:left!important;font-size:.85rem!important;color:#0f172a!important;padding:.6rem 1rem!important;margin-bottom:5px!important;transition:all .15s!important;}
  div[data-testid="stButton"] button[kind="secondary"]:hover{background:#eff6ff!important;border-color:#2563eb!important;color:#1d4ed8!important;}

  @media(max-width:600px){.link-grid{grid-template-columns:1fr;}}
</style>
""", unsafe_allow_html=True)

# ── Hero ───────────────────────────────────────────────────────────────────────
st.markdown("""
<div class="hero">
  <div class="hero-tag">Australian Property Research</div>
  <h1 class="hero-title">What's your property<br/><em>worth?</em></h1>
  <p class="hero-sub">Enter any Australian address to instantly open the right page on every major property platform.</p>
</div>
""", unsafe_allow_html=True)

# ── Address helpers ────────────────────────────────────────────────────────────
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


def build_links(address: str) -> dict:
    p = parse_address(address)
    sub = p["suburb"]
    state = p["state"]
    pc = p["postcode"]
    unit = p["unit"]
    snum = p["street_num"]
    sname = p["street_name"]
    full = p["full"]

    # Slugs
    sname_slug = sname.lower().replace(" ", "-")
    sub_slug = sub.lower().replace(" ", "-")
    state_l = state.lower()

    # Domain property profile slug:  4-40-rothesay-avenue-elwood-vic-3184
    if unit:
        domain_prop_slug = f"{unit}-{snum}-{sname_slug}-{sub_slug}-{state_l}-{pc}"
    else:
        domain_prop_slug = f"{snum}-{sname_slug}-{sub_slug}-{state_l}-{pc}"

    # Domain building profile: 40-rothesay-avenue-elwood-vic-3184
    domain_bldg_slug = f"{snum}-{sname_slug}-{sub_slug}-{state_l}-{pc}"

    # Domain street profile
    domain_street_slug = f"{sname_slug}-{sub_slug}-{state_l}-{pc}"

    # REA sold slug: elwood-vic-3184
    rea_suburb_slug = "-".join(x for x in [sub_slug, state_l, pc] if x)

    # Encoded strings
    q_full = urllib.parse.quote_plus(full)
    q_suburb = urllib.parse.quote_plus(f"{sub} {state} {pc}".strip())
    q_street = urllib.parse.quote_plus(f"{snum} {sname}, {sub} {state}".strip())

    return {
        "p": p,
        "property": {
            "domain_profile":  f"https://www.domain.com.au/property-profile/{domain_prop_slug}",
            "domain_building": f"https://www.domain.com.au/building-profile/{domain_bldg_slug}/",
            "domain_street":   f"https://www.domain.com.au/street-profile/{domain_street_slug}/",
            "rea_profile":     f"https://www.realestate.com.au/property/{domain_prop_slug}/",
        },
        "sold": {
            "domain_sold":     f"https://www.domain.com.au/sold-listings/?q={q_suburb}&sort=dateSold-desc",
            "rea_sold":        f"https://www.realestate.com.au/sold/in-{rea_suburb_slug}/",
            "auhouseprices":   f"https://www.auhouseprices.com/sold/list/{state}/{urllib.parse.quote(sub)}/",
            "allhomes":        f"https://www.allhomes.com.au/sale/{sub_slug}-{state_l}-{pc}/sold/",
        },
        "estimate": {
            "propvalue":       f"https://www.propertyvalue.com.au/search/?q={q_full}",
            "domain_search":   f"https://www.domain.com.au/sale/?q={q_suburb}",
            "rea_estimate":    f"https://www.realestate.com.au/neighbourhoods/{sub_slug}-{state_l}-{pc}/",
            "realestate_sold": f"https://www.realestate.com.au/sold/in-{rea_suburb_slug}/?sortType=soldDate",
        },
        "suburb": {
            "domain_suburb":   f"https://www.domain.com.au/suburb-profile/{sub_slug}-{state_l}-{pc}/",
            "rea_suburb":      f"https://www.realestate.com.au/neighbourhoods/{sub_slug}-{state_l}-{pc}/",
            "sqm_research":    f"https://sqmresearch.com.au/property-vacancy-rate.php?postcode={pc}",
            "abs":             f"https://www.abs.gov.au/census/find-census-data/quickstats/2021/{pc}",
        },
    }


def fetch_suggestions(query: str) -> list:
    try:
        import requests
        clean = re.sub(r"^\d+\s*/\s*", "", query.strip())
        clean = re.sub(r"^(unit|apt|apartment|flat)\s+\S+\s*,?\s*", "", clean, flags=re.I)
        q = clean or query
        for url, params in [
            ("https://nominatim.openstreetmap.org/search",
             {"q": q, "format": "json", "addressdetails": 1, "limit": 7, "countrycodes": "au"}),
            ("https://photon.komoot.io/api/",
             {"q": q, "limit": 7, "lang": "en", "bbox": "112,-44,154,-10"}),
        ]:
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
for k, v in [("confirmed",""), ("last_typed",""), ("suggestions",[]), ("searched","")]:
    if k not in st.session_state: st.session_state[k] = v

# ── Search box ─────────────────────────────────────────────────────────────────
typed = st.text_input("addr", value=st.session_state.confirmed or "",
                      placeholder="e.g. 4/40 Rothesay Avenue, Elwood VIC 3184",
                      label_visibility="collapsed")

if typed and typed != st.session_state.confirmed and typed != st.session_state.last_typed:
    st.session_state.last_typed = typed
    st.session_state.confirmed = ""
    st.session_state.searched = ""
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

col1, col2 = st.columns([3, 1])
with col1:
    go = st.button("🔍  Research this property", use_container_width=True, type="primary")
with col2:
    clear = st.button("Clear", use_container_width=True)
    if clear:
        for k in ["confirmed","last_typed","suggestions","searched"]:
            st.session_state[k] = "" if k != "suggestions" else []
        st.rerun()

if go and len(final.strip()) > 5:
    st.session_state.searched = final.strip()

# ── Results ────────────────────────────────────────────────────────────────────
if st.session_state.searched:
    address = st.session_state.searched
    links = build_links(address)
    p = links["p"]

    # Address card
    unit_str = f"Unit {p['unit']}, " if p["unit"] else ""
    st.markdown(f"""
    <div class="address-card">
      <div class="address-display">{unit_str}{p['street_num']} {p['street_name']}</div>
      <p class="address-sub">{p['suburb']} {p['state']} {p['postcode']} &nbsp;&middot;&nbsp; Click any link below to open in that platform</p>
    </div>
    """, unsafe_allow_html=True)

    # ── Property profile ───────────────────────────────────────────────────────
    st.markdown('<div class="section-title">Property profile &amp; estimates</div>', unsafe_allow_html=True)
    st.markdown(f"""
    <div class="link-grid">
      <a class="link-card featured" href="{links['property']['domain_profile']}" target="_blank">
        <div class="link-card-logo">Domain</div>
        <div class="link-card-title">Property Profile</div>
        <div class="link-card-desc">Domain Estimate, sale history &amp; property details for this specific address</div>
        <div class="link-card-arrow">&#8599;</div>
      </a>
      <a class="link-card featured" href="{links['estimate']['propvalue']}" target="_blank">
        <div class="link-card-logo">PropertyValue.com.au</div>
        <div class="link-card-title">Free AVM Estimate</div>
        <div class="link-card-desc">Automated valuation — no account needed. Search for this address.</div>
        <div class="link-card-arrow">&#8599;</div>
      </a>
    </div>
    <div class="link-grid">
      <a class="link-card" href="{links['property']['domain_building']}" target="_blank">
        <div class="link-card-logo">Domain</div>
        <div class="link-card-title">Building Profile</div>
        <div class="link-card-desc">All units at {p['street_num']} {p['street_name']} with individual estimates</div>
        <div class="link-card-arrow">&#8599;</div>
      </a>
      <a class="link-card" href="{links['property']['rea_profile']}" target="_blank">
        <div class="link-card-logo">realestate.com.au</div>
        <div class="link-card-title">PropTrack Estimate</div>
        <div class="link-card-desc">REA's automated valuation and property history</div>
        <div class="link-card-arrow">&#8599;</div>
      </a>
    </div>
    """, unsafe_allow_html=True)

    # ── Recent sales ───────────────────────────────────────────────────────────
    st.markdown('<div class="section-title">Recent sold prices</div>', unsafe_allow_html=True)
    st.markdown(f"""
    <div class="link-grid">
      <a class="link-card" href="{links['sold']['domain_sold']}" target="_blank">
        <div class="link-card-logo">Domain</div>
        <div class="link-card-title">Sold Listings</div>
        <div class="link-card-desc">Recent sales in {p['suburb']} sorted by date</div>
        <div class="link-card-arrow">&#8599;</div>
      </a>
      <a class="link-card" href="{links['sold']['rea_sold']}" target="_blank">
        <div class="link-card-logo">realestate.com.au</div>
        <div class="link-card-title">Sold Prices</div>
        <div class="link-card-desc">Recent sales history in {p['suburb']}</div>
        <div class="link-card-arrow">&#8599;</div>
      </a>
      <a class="link-card" href="{links['sold']['auhouseprices']}" target="_blank">
        <div class="link-card-logo">AuHousePrices.com</div>
        <div class="link-card-title">Sold Price History</div>
        <div class="link-card-desc">Free sold price database — no account needed</div>
        <div class="link-card-arrow">&#8599;</div>
      </a>
      <a class="link-card" href="{links['property']['domain_street']}" target="_blank">
        <div class="link-card-logo">Domain</div>
        <div class="link-card-title">Street Profile</div>
        <div class="link-card-desc">All sales on {p['street_name']} over time</div>
        <div class="link-card-arrow">&#8599;</div>
      </a>
    </div>
    """, unsafe_allow_html=True)

    # ── Suburb data ────────────────────────────────────────────────────────────
    st.markdown('<div class="section-title">Suburb market data</div>', unsafe_allow_html=True)
    st.markdown(f"""
    <div class="link-grid">
      <a class="link-card" href="{links['suburb']['domain_suburb']}" target="_blank">
        <div class="link-card-logo">Domain</div>
        <div class="link-card-title">{p['suburb']} Suburb Profile</div>
        <div class="link-card-desc">Median prices, days on market, auction clearance rates</div>
        <div class="link-card-arrow">&#8599;</div>
      </a>
      <a class="link-card" href="{links['suburb']['rea_suburb']}" target="_blank">
        <div class="link-card-logo">realestate.com.au</div>
        <div class="link-card-title">{p['suburb']} Neighbourhood</div>
        <div class="link-card-desc">PropTrack suburb insights and price trends</div>
        <div class="link-card-arrow">&#8599;</div>
      </a>
      <a class="link-card" href="{links['suburb']['sqm_research']}" target="_blank">
        <div class="link-card-logo">SQM Research</div>
        <div class="link-card-title">Vacancy &amp; Supply Data</div>
        <div class="link-card-desc">Independent market research for postcode {p['postcode']}</div>
        <div class="link-card-arrow">&#8599;</div>
      </a>
      <a class="link-card" href="{links['suburb']['abs']}" target="_blank">
        <div class="link-card-logo">ABS Census</div>
        <div class="link-card-title">Demographic Data</div>
        <div class="link-card-desc">Income, ownership rates &amp; household stats for {p['postcode']}</div>
        <div class="link-card-arrow">&#8599;</div>
      </a>
    </div>
    """, unsafe_allow_html=True)

    # ── Tip box ────────────────────────────────────────────────────────────────
    tip = ""
    if p["unit"]:
        tip = f"<strong>Tip for unit {p['unit']}/{p['street_num']}:</strong> If the property profile shows no estimate, try the <strong>Building Profile</strong> link — it lists all units in the block ({p['street_num']} {p['street_name']}) with individual Domain Estimates, including units that may not have their own profile page."
    else:
        tip = f"<strong>Tip:</strong> The Domain Property Profile is the best starting point — it shows the Domain Estimate, full sale history, and links to comparable recent sales nearby."

    st.markdown(f'<div class="info-box">{tip}</div>', unsafe_allow_html=True)

st.markdown('<div class="footer">Built with Streamlit &middot; Links to Domain, REA, PropertyValue &amp; more &middot; Free to use</div>', unsafe_allow_html=True)
