# pixel-gemini

**Pixel 10 Pro Google One + Jio India Gemini Offer Bot – Telegram Interface**

A Replit-hosted Telegram bot that simulates a Google Pixel 10 Pro (Android 16)
with a **Jio India 5G SIM**, logs into a user-supplied Gmail account, and
retrieves Gemini Pro offer activation links from Google One and Jio.

---

## Supported Offers

| Offer | Duration | Value | Eligibility |
|---|---|---|---|
| 🟢 **Google One Gemini Pro** | 12 months free | ~$239 | Pixel device users |
| 🟡 **Jio India Google AI Pro** | 18 months free | ₹35,100 (~$420) | Jio 5G SIM users (₹349+ plan) |

### Jio Gemini Offer Details
The [Jio Google Gemini Offer](https://www.jio.com/google-gemini-offer/) provides
**18 months of free Google AI Pro** subscription to Jio Unlimited 5G users aged
18+. Benefits include:
- **Gemini 3** — Enhanced access to the most capable model
- **5 TB Storage** — Google Photos, Drive, and Gmail
- **Veo 3** — AI video generation tool
- **NotebookLM** — Research assistant with 5× higher limits
- **Google Workspace AI** — Gemini in Gmail, Docs, Vids, and more
- **AI Image Editing** — Nano Banana with higher limits

---

## Project Structure

```
pixel-gemini/
├── main.py               # Telegram bot entry point
├── device_simulator.py   # Pixel 10 Pro + Jio SIM network simulation
├── google_automation.py  # Google One + Jio offer login and detection
├── config.py             # Configuration, Jio network constants, keywords
├── requirements.txt      # Python dependencies
├── test_totp.py          # TOTP verification test script
└── README.md             # This file
```

---

## Features

| Feature | Details |
|---|---|
| 📱 Device simulation | Pixel 10 Pro (Android 16) with unique IMEI, Android ID, and user-agent per session |
| 📶 Jio SIM simulation | Full Jio India 5G SIM profile: MCC/MNC (405/874), ICCID, IMSI, phone number, n78 band |
| 🤖 Telegram bot | `/start`, `/login`, `/check_offer`, `/check_jio_offer`, `/sim_info`, `/get_link`, `/status` |
| 🔐 Gmail login | Selenium-based Google account authentication with TOTP 2FA support |
| 💳 Google One detection | Scans for 12-month Gemini Pro offer |
| 🟡 Jio offer detection | Scans Jio + Google One for 18-month AI Pro with 39 Jio-specific keywords |
| 🌏 Indian locale | en-IN language, Asia/Kolkata timezone, Indian number format |
| 🔄 Session management | In-memory per-user sessions; passwords deleted from chat on capture |

---

## Setup on Replit

### 1. Fork / import this repository

Open [Replit](https://replit.com) and create a new Repl from this GitHub repo.

### 2. Create a Telegram Bot

1. Open Telegram and search for **@BotFather**.
2. Send `/newbot` and follow the prompts.
3. Copy the API token you receive (looks like `123456:ABC-DEF…`).

### 3. Set the environment variable

In the Replit sidebar click **Secrets** (🔒) and add:

| Key | Value |
|---|---|
| `TELEGRAM_BOT_TOKEN` | Your token from BotFather |

### 4. Install dependencies

```bash
pip install -r requirements.txt
```

Replit runs this automatically on first start if you use a `pyproject.toml`
or if the Run button is configured to execute `pip install` first.

### 5. Run the bot

Click **Run** in Replit, or execute:

```bash
python main.py
```

The bot will start polling for Telegram updates.

---

## Usage

| Command | Description |
|---|---|
| `/start` | Show welcome message and command list |
| `/login` | Enter Gmail email, password, and 2FA secret |
| `/check_offer` | Check Google One for 12-month Gemini Pro offer |
| `/check_jio_offer` | Check Jio + Google One for 18-month free Google AI Pro |
| `/sim_info` | View Jio SIM network profile (ICCID, IMSI, phone, signal) |
| `/get_link` | Retrieve the last captured offer link |
| `/status` | View current session info, device profile, and SIM info |

### Typical Jio flow

```
You: /start
Bot: Welcome…

You: /login
Bot: Please enter your Gmail address:

You: user@gmail.com
Bot: Email received. Now enter your password:

You: ••••••••
Bot: Password received. Enter your 2FA secret:

You: JBSWY3DPEHPK3PXP
Bot: ✅ Credentials saved. New Pixel 10 Pro + Jio 5G profile created…

You: /check_jio_offer
Bot: 🚀 Starting Jio 5G Gemini Offer Check
     📶 SIM: Jio 5G (n78)
     📞 Phone: +91 8XXXX XXXXX
     🎯 Target: 18-month free Google AI Pro (₹35,100)

Bot: 🤖 Starting Pixel 10 Pro + Jio 5G SIM simulator…
Bot: 🌐 Step 1/6 — Loading Google sign-in page…
Bot: ✅ Step 5/6 — Logged in successfully!
Bot: 🔍 Scanning Jio Gemini Offer page…
Bot: 🔑 Jio keywords matched (12): jio, gemini pro, 18 months…
Bot: 🎉 Jio Gemini Offer Found!
     🔗 https://one.google.com/…
```

### SIM info example

```
You: /sim_info
Bot: 📶 SIM Network — Jio
     Carrier: Reliance Jio Infocomm Limited
     Network: 5G (n78)
     MCC/MNC: 405/874
     SIM Operator: 405874
     ICCID: 8991874XXXXXXXXXXXXX
     IMSI: 405874XXXXXXXXX
     Phone: +91 8XXXX XXXXX
     Signal: -65 dBm
     Speed: ↓150 Mbps / ↑30 Mbps
     Latency: 15 ms
     Locale: en-IN  |  TZ: Asia/Kolkata
     Country: IN
```

---

## Jio SIM Network Simulation

The bot simulates a complete Jio India 5G SIM profile:

| Parameter | Value | Description |
|---|---|---|
| MCC | `405` | Mobile Country Code (India) |
| MNC | `874` | Mobile Network Code (Reliance Jio 5G) |
| SIM Operator | `405874` | MCC + MNC combined |
| ICCID | `8991874…` | 20-digit SIM serial (Luhn-valid) |
| IMSI | `405874…` | 15-digit subscriber identity |
| NR Band | `n78` | Jio's primary 5G band (3.5 GHz) |
| Network Type | `5G` | Jio True 5G (Standalone) |
| Downlink | ~150 Mbps | Typical Jio 5G speed |
| Latency | ~15 ms | Low latency 5G SA |
| Locale | `en-IN` | English (India) |
| Timezone | `Asia/Kolkata` | IST (UTC+5:30) |
| Phone Format | `+91 XXXXX XXXXX` | Indian mobile format |

### JS Injection
The bot injects a `window.__jio_sim__` object into every page with full
SIM details, allowing Google services to detect the Jio 5G carrier and
validate eligibility for the Gemini offer.

### Jio Offer Keywords (39 total)
The bot scans pages for these keyword categories:
- **Duration/Pricing**: `18 month`, `35,100`, `free for 18`
- **Jio-specific**: `jio`, `jio 5g`, `jio unlimited`, `myjio`, `reliance jio`
- **Gemini Plan**: `gemini 3`, `google ai pro`, `gemini pro plan`
- **Actions**: `claim offer`, `activate offer`, `free subscription`
- **Benefits**: `5 tb storage`, `veo`, `notebooklm`, `deep research`, `workspace`

---

## Technical Notes

- **Headless Chrome** via Selenium with mobile emulation matching
  the Pixel 10 Pro screen (412 × 915 CSS, pixel ratio 3.5).
- **CDP timezone/locale override** — sets `Asia/Kolkata` and `en-IN`
  for proper Indian regional detection.
- A new **IMEI**, **Android ID**, **Chrome version**, and **Jio SIM**
  (ICCID, IMSI, phone number) are generated per session.
- The **user agent** uses Chrome UA Reduction (Android 10; K) while
  the real device identity is sent via Sec-CH-UA-Model client hints.
- Credentials are stored **in memory only** and never written to disk.
  The Telegram message containing the password is deleted immediately.

---

## Requirements

- Python 3.10+
- Google Chrome / Chromium installed (Replit provides this)
- `chromedriver` on PATH (managed automatically by `webdriver-manager`)

---

## Disclaimer

This project is provided for educational and personal use only.
Automating Google account access may violate Google's Terms of Service.
Use responsibly and only with accounts you own.
