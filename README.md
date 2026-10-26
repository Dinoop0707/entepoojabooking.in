# EntePoojaBooking.in - Kerala Pooja Booking Website (Flask Prototype)

A runnable, responsive Flask implementation of the latest approved Aaradhya visual direction: ivory, deep maroon, brass gold, heritage temple imagery, elegant editorial typography, ritual discovery and booking journey.

**The name Aaradhya is a placeholder** until you finalize the brand.

## Quick start

1. Install Python 3.10 or newer.
2. Unzip the archive, then open a terminal in the `kerala-pooja-site` directory.
3. Run:

```bash
python -m venv .venv
# macOS / Linux
source .venv/bin/activate
# Windows PowerShell
# .venv\Scripts\Activate.ps1
pip install -r requirements.txt
python app.py
```

4. Visit **http://127.0.0.1:5000** in your browser.

## Pages

- `/` - Homepage, search, occasion categories and featured rituals
- `/services` - Services listing, categories, text search and visual filter UI
- `/services/ganapathi-homam` - Full ritual detail page (other services also supported)
- `/book` - Booking request form with service, date, location and contact details
- `/confirmation/<reference>` - Saved request confirmation
- `/priests` - Priest-selection coming-soon state
- `/how-it-works` - Booking process
- `/about` - Brand story

## Important limitations

- **Demo only**: booking requests are saved in a local SQLite file `bookings.sqlite3`. They are not sent to priests, and no emails are sent.
- Prices are **illustrative**, not quotations.
- There is **no payment gateway**, login system, real priest inventory, or real-time availability.
- Malayalam toggle, district-specific matching, and several filters are visual placeholders; category and name search work.
- Photography is bundled as cropped visual material from the previously generated design mockups. The web pages are actual HTML/CSS, not screenshot backgrounds. Some image crops may have lower resolution than professional photography.
- Google Fonts loads when connected to the internet; system font fallbacks work offline.
- Before public launch: replace photography with licensed high-resolution photos, connect a real database/availability service, add security and privacy policies, payment processing, notifications, verified priest profiles and translations.

## Change the name

Search for `Aaradhya` in `templates/` and `app.py` to replace the temporary name.

## Run on a different port

```bash
PORT=8000 python app.py
```

This project is intended for local evaluation, not production deployment as-is.
