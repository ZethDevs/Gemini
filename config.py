"""
Configuration and constants for the Pixel 10 Pro Google One Gemini Bot.
"""

import os

# ── Telegram ──────────────────────────────────────────────────────────────────
TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", "")

# ── Device specs – Google Pixel 10 Pro (Android 16) ──────────────────────────
DEVICE_MODEL        = "Pixel 10 Pro"
DEVICE_BRAND        = "google"
DEVICE_MANUFACTURER = "Google"
ANDROID_VERSION     = "16"
ANDROID_SDK         = "36"
BUILD_ID            = "CP1A.260405.005"       # Pixel 10 Pro build fingerprint

# Hardware profile (used for navigator injection)
DEVICE_RAM_GB           = 16                  # 16 GB RAM (spoofed as 16 via JS)
DEVICE_CPU_CORES        = 8                   # Tensor G5: 8 reported cores
DEVICE_MAX_TOUCH        = 5                   # 5-point multitouch (realistic)
DEVICE_GPU_VENDOR       = "Imagination Technologies"
DEVICE_GPU_RENDERER     = "PowerVR DXT-48-1536"  # Tensor G5 GPU

# Screen – Pixel 10 Pro: CSS viewport 412×915 @3.5× density (~495 PPI)
SCREEN_CSS_WIDTH    = 412
SCREEN_CSS_HEIGHT   = 915
SCREEN_PIXEL_RATIO  = 3.5

# ── Chrome 149 (latest stable on Android) ────────────────────────────────────
CHROME_VERSION       = "149.0.7827.200"
CHROME_MAJOR_VERSION = 149

# ── User-Agent – Chrome UA Reduction (Chrome 110+) ───────────────────────────
# Modern Chrome on Android NEVER reveals device model in the UA string.
# The real device identity is sent via Sec-CH-UA-Model client hint.
# Format: "Mozilla/5.0 (Linux; Android 10; K) ... Chrome/<version> Mobile Safari/537.36"
USER_AGENT_TEMPLATES = [
    (
        "Mozilla/5.0 (Linux; Android 10; K) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/{chrome} Mobile Safari/537.36"
    ),
]

# ── Google URLs ───────────────────────────────────────────────────────────────
GMAIL_LOGIN_URL       = "https://accounts.google.com/signin/v2/identifier"
GOOGLE_ONE_URL        = "https://one.google.com/"
GOOGLE_ONE_OFFERS_URL = "https://one.google.com/about/plans"

# ── Gemini offer detection keywords ──────────────────────────────────────────
GEMINI_OFFER_KEYWORDS = [
    "gemini pro",
    "gemini advanced",
    "12 month",
    "12-month",
    "free trial",
    "activate",
    "get started",
    "claim offer",
    "redeem",
]

# ── Jio India SIM Network Configuration ──────────────────────────────────────
# Reliance Jio Infocomm Limited – India's largest 5G operator
# MCC 405 = India (mobile), MNC 874 = Jio (primary 5G network)
JIO_MCC              = "405"   # Mobile Country Code – India
JIO_MNC              = "874"   # Mobile Network Code – Reliance Jio 5G
JIO_CARRIER_NAME     = "Jio"
JIO_CARRIER_FULL     = "Reliance Jio Infocomm Limited"
JIO_NETWORK_TYPE     = "5G"    # Jio True 5G (SA – Standalone)
JIO_NETWORK_CLASS    = "nr"    # New Radio (5G NR)
JIO_ISO_COUNTRY      = "in"    # ISO 3166-1 alpha-2 for India
JIO_LOCALE           = "en-IN" # English (India)
JIO_TIMEZONE         = "Asia/Kolkata"  # IST (UTC+5:30)

# Jio SIM identifiers
JIO_ICCID_PREFIX     = "8991874"  # Jio ICCID prefix (89=telecom, 91=India, 874=Jio)
JIO_SIM_OPERATOR     = "405874"   # MCC+MNC combined

# Jio 5G network simulation parameters
JIO_5G_DOWNLINK_MBPS = 150.0    # Typical Jio 5G download speed
JIO_5G_UPLINK_MBPS   = 30.0     # Typical Jio 5G upload speed
JIO_5G_RTT_MS        = 15       # Low latency on Jio True 5G SA
JIO_5G_SIGNAL_DBM    = -65      # Strong 5G signal (dBm)
JIO_5G_NR_BAND       = "n78"    # Jio's primary 5G band (3.5 GHz)

# Jio Google Gemini Offer – https://www.jio.com/google-gemini-offer/
# Free 18-month Google AI Pro subscription (₹35,100 value) for Jio 5G users
JIO_GEMINI_OFFER_URL     = "https://www.jio.com/google-gemini-offer/"
JIO_MYJIO_DASHBOARD_URL  = "https://www.jio.com/dl/dashboard"
JIO_RECHARGE_URL         = "https://www.jio.com/selfcare/recharge/mobility/"
JIO_MIN_PLAN_AMOUNT      = 349   # Minimum ₹349 unlimited 5G plan required

# Jio Gemini offer detection keywords – matches content on Google One / Gemini
# pages that indicate the Jio-exclusive 18-month free Pro plan
JIO_GEMINI_OFFER_KEYWORDS = [
    # Duration & pricing keywords
    "18 month",
    "18-month",
    "18 months free",
    "18 months",
    "free for 18",
    "35,100",
    "35100",
    # Jio-specific keywords
    "jio",
    "jio offer",
    "jio 5g",
    "jio unlimited",
    "jio users",
    "jio sim",
    "myjio",
    "reliance jio",
    # Gemini Pro plan keywords (Jio variant)
    "gemini pro",
    "gemini 3",
    "ai pro",
    "google ai pro",
    "google gemini offer",
    "gemini pro plan",
    "gemini subscription",
    # Offer action keywords
    "claim offer",
    "claim your",
    "activate offer",
    "free subscription",
    "free pro plan",
    "exclusive offer",
    "limited-time offer",
    # Benefit keywords unique to the Jio Gemini deal
    "5 tb storage",
    "5tb storage",
    "5 tb",
    "veo",
    "notebooklm",
    "deep research",
    "ai video",
    "ai image",
    "workspace",
    "gemini in gmail",
]

# ── Selenium / WebDriver ──────────────────────────────────────────────────────
WEBDRIVER_TIMEOUT  = 30   # seconds – explicit wait
IMPLICIT_WAIT      = 10   # seconds
PAGE_LOAD_TIMEOUT  = 60   # seconds
HEADLESS           = True # always headless on Replit

# ── Session storage ───────────────────────────────────────────────────────────
SESSION_STORE: dict = {}

# ── Logging ───────────────────────────────────────────────────────────────────
LOG_LEVEL  = "INFO"
LOG_FORMAT = "%(asctime)s [%(levelname)s] %(name)s: %(message)s"
