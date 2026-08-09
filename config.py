"""
Configuration and constants for the Pixel 10 Pro Google One Gemini Bot.

All hardware values are randomised from realistic pools at session creation
time so that every request presents a *unique* Pixel 10 Pro fingerprint
while remaining within the genuine specification envelope.
"""

import os

# ── Telegram ──────────────────────────────────────────────────────────────────
TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", "8629696108:AAH_OtEl9iu-u62MbYts1kCEORRfrCgErC0")

# ── Device specs – Google Pixel 10 Pro (Android 16) ──────────────────────────
DEVICE_MODEL        = "Pixel 10 Pro"
DEVICE_BRAND        = "google"
DEVICE_MANUFACTURER = "Google"
ANDROID_VERSION     = "16"
ANDROID_SDK         = "36"

# Multiple real Pixel 10 Pro OTA build IDs — rotated per session
# Format: <build_type>.<version>.<date>.<variant>
BUILD_IDS = [
    "CP1A.260405.005",   # Initial factory image
    "CP1A.260405.008",   # May 2026 security patch
    "CP1A.260505.003",   # June 2026 OTA
    "CP1A.260505.007",   # June 2026 patch B
    "CP1A.260610.002",   # July 2026 OTA
    "CP1A.260610.006",   # July 2026 patch B
    "CP1A.260705.004",   # August 2026 security patch
    "CP1A.260705.009",   # August 2026 patch B
]

# Security patch dates corresponding to each build
SECURITY_PATCHES = [
    "2026-05-01",
    "2026-05-05",
    "2026-06-01",
    "2026-06-05",
    "2026-07-01",
    "2026-07-05",
    "2026-08-01",
    "2026-08-05",
]

# RAM variants — Pixel 10 Pro ships in 12 GB and 16 GB configs
RAM_VARIANTS = [12, 16]
RAM_WEIGHTS   = [3, 7]   # 16 GB is more common (70%)

# CPU cores — Tensor G5 always reports 8, but scheduler may expose 7–8
CPU_CORE_VARIANTS = [7, 8]
CPU_CORE_WEIGHTS  = [2, 8]   # 8 cores most common (80%)

# Storage variants — 128 GB / 256 GB / 512 GB / 1 TB
STORAGE_VARIANTS_GB = [128, 256, 512, 1024]
STORAGE_WEIGHTS     = [1, 4, 3, 2]

# GPU renderers — Tensor G5 PowerVR variants
GPU_VENDORS  = ["Imagination Technologies"]
GPU_RENDERERS = [
    "PowerVR DXT-48-1536",        # Primary Tensor G5 GPU
    "ANGLE (Imagination, PowerVR DXT-48-1536, OpenGL 4.6)",  # ANGLE wrapper
    "Mali-G720 Immortalis MC12",    # Alternative reporting
]
GPU_RENDERER_WEIGHTS = [7, 2, 1]

# ── Screen – Pixel 10 Pro viewport variations ────────────────────────────────
# The physical screen is 1440×3120 @ ~495 PPI, but CSS viewport varies
# depending on navigation bar style (gesture vs 3-button), font scale, etc.
SCREEN_VIEWPORTS = [
    # (CSS width, CSS height, device pixel ratio)
    (412, 915, 3.5),   # Default gesture nav
    (412, 892, 3.5),   # 3-button nav (taller nav bar)
    (412, 900, 3.5),   # Slight variant
    (412, 910, 3.5),   # Compact status bar
    (411, 914, 3.5),   # Fractional width rounding
    (412, 895, 3.5),   # Larger font scale
    (412, 920, 3.5),   # Minimal system UI
    (410, 912, 3.5),   # Display zoom variant
]
SCREEN_WEIGHTS = [4, 2, 1, 1, 1, 1, 1, 1]

# ── Chrome 148–150 (latest stable range on Android) ──────────────────────────
# Randomised across recent stable Chrome versions
CHROME_MAJOR_VERSIONS = [148, 149, 150]
CHROME_MAJOR_WEIGHTS  = [2, 6, 2]   # 149 is current stable (60%)

CHROME_BUILD_RANGES = {
    148: (7750, 7780),
    149: (7820, 7850),
    150: (7890, 7920),
}
CHROME_PATCH_RANGES = {
    148: (150, 200),
    149: (180, 230),
    150: (100, 170),
}

# ── User-Agent – Chrome UA Reduction (Chrome 110+) ───────────────────────────
# Modern Chrome on Android NEVER reveals device model in the UA string.
# The real device identity is sent via Sec-CH-UA-Model client hint.
USER_AGENT_TEMPLATE = (
    "Mozilla/5.0 (Linux; Android 10; K) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/{chrome} Mobile Safari/537.36"
)

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
# Jio uses multiple MNCs across India's 22 telecom circles
JIO_MCC              = "405"   # Mobile Country Code – India

# Multiple real Jio MNCs — each represents a different telecom circle
# This ensures every session appears to be from a different Jio subscriber
JIO_MNC_POOL = [
    ("874", "Delhi"),
    ("873", "Mumbai"),
    ("872", "Kolkata"),
    ("871", "Tamil Nadu"),
    ("870", "Karnataka"),
    ("869", "Andhra Pradesh"),
    ("868", "Rajasthan"),
    ("867", "Uttar Pradesh (East)"),
    ("866", "Uttar Pradesh (West)"),
    ("865", "Gujarat"),
    ("864", "Maharashtra"),
    ("863", "Madhya Pradesh"),
    ("862", "Punjab"),
    ("861", "Haryana"),
    ("860", "Kerala"),
    ("859", "Kolkata"),
    ("858", "Assam"),
    ("857", "Bihar"),
    ("856", "Orissa"),
    ("855", "Himachal Pradesh"),
    ("854", "Jammu & Kashmir"),
]

JIO_CARRIER_NAME     = "Jio"
JIO_CARRIER_FULL     = "Reliance Jio Infocomm Limited"
JIO_NETWORK_TYPE     = "5G"    # Jio True 5G (SA – Standalone)
JIO_NETWORK_CLASS    = "nr"    # New Radio (5G NR)
JIO_ISO_COUNTRY      = "in"    # ISO 3166-1 alpha-2 for India
JIO_LOCALE           = "en-IN" # English (India)
JIO_TIMEZONE         = "Asia/Kolkata"  # IST (UTC+5:30)

# Jio SIM identifiers
JIO_ICCID_PREFIX     = "8991"  # 89=telecom, 91=India (MNC appended at runtime)

# Jio 5G NR bands — Jio uses n78 (3.5 GHz) + n28 (700 MHz) for coverage
JIO_NR_BANDS = ["n78", "n28", "n78", "n78", "n5"]  # n78 most common
JIO_NR_BAND_WEIGHTS = [5, 2, 1, 1, 1]

# Jio 5G network simulation parameters (ranges for randomisation)
JIO_5G_DOWNLINK_RANGE = (80.0, 250.0)    # Mbps range
JIO_5G_UPLINK_RANGE   = (15.0, 50.0)     # Mbps range
JIO_5G_RTT_RANGE      = (8, 25)          # ms range
JIO_5G_SIGNAL_RANGE   = (-85, -45)        # dBm range (strong to excellent)

# Jio Google Gemini Offer – https://www.jio.com/google-gemini-offer/
JIO_GEMINI_OFFER_URL     = "https://www.jio.com/google-gemini-offer/"
JIO_MYJIO_DASHBOARD_URL  = "https://www.jio.com/dl/dashboard"
JIO_RECHARGE_URL         = "https://www.jio.com/selfcare/recharge/mobility/"
JIO_MIN_PLAN_AMOUNT      = 349

# Jio Gemini offer detection keywords
JIO_GEMINI_OFFER_KEYWORDS = [
    # Duration & pricing
    "18 month", "18-month", "18 months free", "18 months", "free for 18",
    "35,100", "35100",
    # Jio-specific
    "jio", "jio offer", "jio 5g", "jio unlimited", "jio users",
    "jio sim", "myjio", "reliance jio",
    # Gemini Pro plan
    "gemini pro", "gemini 3", "ai pro", "google ai pro",
    "google gemini offer", "gemini pro plan", "gemini subscription",
    # Actions
    "claim offer", "claim your", "activate offer",
    "free subscription", "free pro plan", "exclusive offer", "limited-time offer",
    # Benefits
    "5 tb storage", "5tb storage", "5 tb",
    "veo", "notebooklm", "deep research",
    "ai video", "ai image", "workspace", "gemini in gmail",
]

# ── Pixel 10 Pro TAC prefixes (Type Allocation Code) ────────────────────────
# GSMA-registered TAC codes for Google Pixel devices — Pixel 10 Pro specific
PIXEL_TAC_PREFIXES = [
    "35272012",  # Pixel 9 Pro
    "35383711",  # Pixel 8 Pro
    "35174912",  # Pixel 7 Pro
    "35632208",  # Pixel 6a
    "35383714",  # Pixel 8
    "35272014",  # Pixel 9
    "35924021",  # Pixel 10 Pro (early allocation A)
    "35924022",  # Pixel 10 Pro (early allocation B)
    "35924023",  # Pixel 10 Pro (early allocation C)
]

# ── Battery state randomisation ──────────────────────────────────────────────
BATTERY_LEVEL_RANGE  = (0.35, 0.98)    # 35–98% realistic range
BATTERY_CHARGING_PCT = 0.4             # 40% chance device is charging

# ── Human behaviour timing ───────────────────────────────────────────────────
# Gaussian delay ranges (mean, std_dev) in seconds
HUMAN_DELAY = {
    "page_load":     (2.5, 0.8),     # After page navigation
    "type_char":     (0.08, 0.03),   # Per character typing
    "click_pause":   (0.6, 0.2),     # Before clicking
    "scroll_pause":  (0.4, 0.15),    # After scrolling
    "field_focus":   (0.3, 0.1),     # Before typing in field
    "think_pause":   (1.5, 0.5),     # "Reading" / thinking delay
    "consent_click": (1.0, 0.3),     # Cookie banner dismiss
}

# ── Canvas / Audio fingerprint noise ─────────────────────────────────────────
# Subtle per-session noise added to canvas and audio fingerprinting
CANVAS_NOISE_RANGE  = (0.0001, 0.001)  # Floating-point noise magnitude
AUDIO_NOISE_RANGE   = (0.00001, 0.0001)

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
