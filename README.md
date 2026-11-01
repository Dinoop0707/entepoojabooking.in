# EntePooja - Kerala Pooja Booking (Flask Demo)

A responsive Flask prototype with homepage, service discovery, detail pages, booking requests, user registration, login, account page and logout.

## Start

```bash
python -m pip install -r requirements.txt
python app.py
```

Visit http://127.0.0.1:5000

## Customize brand and contact details

**Edit only `constants.py`** for the public-facing brand name, tagline, email, phone, Instagram handle, WhatsApp, address, region and footer description. `BRAND_NAME = "EntePooja"` is the current value. Restart Flask after editing. Empty social/contact values are hidden in the footer.

## Accounts

- `/register` creates a local account; `/login` signs in; `/account` displays profile; `/logout` signs out (POST).
- Passwords are hashed with Werkzeug; they are not stored as plain text.
- User accounts and booking requests are stored in `bookings.sqlite3` (automatically created). Existing bookings in an older SQLite database remain intact.
- CSRF tokens protect POST forms, and sessions use HttpOnly/SameSite cookies.
- This is **a local development prototype**, not a production-ready authentication service. Add HTTPS, a persistent secret key, email verification, password reset, production-grade rate limiting, secure hosting and privacy policy before deploying.
- Booking requests are **not linked to user accounts yet**. No live priest availability, payment processing or notifications are connected.

## Production notes

Set a long random `SECRET_KEY` environment variable and use HTTPS with `COOKIE_SECURE=1`. Do not deploy with the fallback local-preview secret. Do not commit `bookings.sqlite3` or `.env` to source control.


## Account, cart, bulk requests (new)
- Log in or register before adding poojas to the cart.
- Browse Services, select **Add to cart**, choose quantity, and open **Cart** in the header.
- Cart supports quantity edits and removal (quantity 0). Submit a bulk request to create a printable estimated bill.
- **My Account** shows My Cart, individual booking requests submitted while signed in, and bulk requests with printable bills.
- Existing booking requests made before login cannot be automatically attributed to an account.
- `bookings.sqlite3` is migrated in place on startup; keep your original DB file when replacing the project. Back it up first.
- The bulk checkout is a **request only**: dates, venues and priest details must be coordinated separately; no payment is charged.
- For production, add real availability, booking lifecycle, tax calculation, secure deployment and transactional payment integration.
