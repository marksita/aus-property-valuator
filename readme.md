# 🏠 Australian Property Valuator

A **100% free** Streamlit app that estimates the current market value of any Australian residential property. No API keys, no credit card, no paid services required.

---

## ✨ Features

- **Address autocomplete** — powered by OpenStreetMap Nominatim + Photon (both free, no key needed)
- **Market estimates** — scraped from Domain.com.au and realestate.com.au recent sales
- **Direct source links** — to each platform's property/listing page
- **Zero cost** — GitHub + Streamlit Community Cloud are both free tiers

---

## 🚀 Deploy in 3 steps (totally free)

### Step 1 — Push to GitHub

1. Create a free account at [github.com](https://github.com)
2. Create a new repository, e.g. `aus-property-valuator`
3. Upload all files from this folder (drag & drop on GitHub, or `git push`)

### Step 2 — Deploy on Streamlit Community Cloud

1. Go to [share.streamlit.io](https://share.streamlit.io) → sign in with GitHub
2. Click **"New app"** → select your repo, branch `main`, file `app.py`
3. Click **Deploy** — live in ~60 seconds at a free `*.streamlit.app` URL ✅

That's it — no secrets or API keys needed.

### Step 3 — (Optional) Run locally

```bash
git clone https://github.com/YOUR_USERNAME/aus-property-valuator
cd aus-property-valuator
pip install -r requirements.txt
streamlit run app.py
```

---

## 📊 How it works

| Feature | Service | Cost |
|---------|---------|------|
| Address autocomplete | OpenStreetMap Nominatim | Free (no key) |
| Address autocomplete fallback | Photon by Komoot | Free (no key) |
| Recent sold prices | Domain.com.au (scraped) | Free |
| Recent sold prices | realestate.com.au (scraped) | Free |
| Hosting | Streamlit Community Cloud | Free |
| Code hosting | GitHub | Free |

> **Note:** Real-time per-property automated valuations (CoreLogic, PropTrack) sit behind paid APIs used by banks. This app provides suburb-level comparable sales as a free proxy, plus direct links to each platform where registered users can view proprietary estimates.

---

## ⚖️ Disclaimer

Estimates are indicative only based on recent comparable sales in the suburb. Not a formal property valuation. For a certified valuation, engage a licensed property valuer (API/AIQS member).

---

## 🛠 Tech stack

- [Streamlit](https://streamlit.io) — UI framework
- [Nominatim](https://nominatim.openstreetmap.org) / [Photon](https://photon.komoot.io) — Free geocoding
- [BeautifulSoup4](https://www.crummy.com/software/BeautifulSoup/) — HTML parsing
- [Requests](https://requests.readthedocs.io) — HTTP client
