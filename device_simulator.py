"""
Android Pixel 10 Pro device simulator with Jio India SIM network simulation.

Each session gets unique identifiers (IMEI, Android ID, device fingerprint,
Chrome version patch, Jio SIM identifiers) while the hardware identity
remains "Pixel 10 Pro" and the SIM identity remains "Jio 5G India".

Key implementation detail:
  Chrome 110+ uses UA Reduction — the User-Agent string always shows
  "Android 10; K" regardless of real device. The actual device model
  is communicated via Sec-CH-UA-Model client hint (set via CDP).

Jio SIM Network Simulation:
  Simulates a Reliance Jio India 5G SIM card with valid MCC/MNC codes,
  ICCID, IMSI, phone number format, and network parameters to present
  the device as a Jio 5G subscriber eligible for the Google Gemini offer.
"""

import random
import string
import uuid
from dataclasses import dataclass, field

import config


# ── Real Google Pixel TAC prefixes (Type Allocation Code) ────────────────────
# These are genuine GSMA-registered TAC codes for Google Pixel devices.
PIXEL_TAC_PREFIXES = [
    "35272012",  # Pixel 9 Pro
    "35383711",  # Pixel 8 Pro
    "35174912",  # Pixel 7 Pro
    "35632208",  # Pixel 6a
    "35383714",  # Pixel 8
    "35272014",  # Pixel 9
]


# ── Helpers ───────────────────────────────────────────────────────────────────

def _luhn_checksum(number: str) -> int:
    digits = [int(d) for d in number]
    odd_digits = digits[-1::-2]
    even_digits = digits[-2::-2]
    total = sum(odd_digits)
    for d in even_digits:
        total += sum(divmod(d * 2, 10))
    return total % 10


def _generate_imei() -> str:
    """Generate a Luhn-valid IMEI using a real Google Pixel TAC prefix."""
    tac = random.choice(PIXEL_TAC_PREFIXES)   # 8-digit real TAC
    serial = "".join(random.choices(string.digits, k=6))
    partial = tac + serial                      # 14 digits
    check_digit = (10 - _luhn_checksum(partial + "0")) % 10
    return partial + str(check_digit)


def _generate_android_id() -> str:
    return "".join(random.choices("0123456789abcdef", k=16))


def _generate_device_fingerprint(model: str, build_id: str, android: str) -> str:
    slug = model.lower().replace(" ", "_")
    return f"google/{slug}/{slug}:{android}/{build_id}/eng.user.release-keys"


def _random_chrome_patch() -> str:
    """Return a realistic Chrome 149 version string with slight random patch."""
    major = config.CHROME_MAJOR_VERSION       # 149
    build = random.randint(7820, 7840)
    patch = random.randint(180, 220)
    return f"{major}.0.{build}.{patch}"


# ── Jio SIM helpers ───────────────────────────────────────────────────────────

def _generate_jio_iccid() -> str:
    """
    Generate a valid Jio SIM ICCID (Integrated Circuit Card Identifier).
    Format: 89 (telecom) + 91 (India) + 874 (Jio MNC) + 12-digit serial + check digit
    Total: 20 digits, Luhn-valid.
    """
    prefix = config.JIO_ICCID_PREFIX  # "8991874"
    serial = "".join(random.choices(string.digits, k=12))
    partial = prefix + serial  # 19 digits
    check_digit = (10 - _luhn_checksum(partial + "0")) % 10
    return partial + str(check_digit)


def _generate_jio_imsi() -> str:
    """
    Generate a valid Jio IMSI (International Mobile Subscriber Identity).
    Format: MCC (405) + MNC (874) + 9-digit subscriber ID
    Total: 15 digits.
    """
    subscriber_id = "".join(random.choices(string.digits, k=9))
    return f"{config.JIO_MCC}{config.JIO_MNC}{subscriber_id}"


def _generate_jio_phone_number() -> str:
    """
    Generate a realistic Jio India mobile number.
    Jio numbers in India start with 6, 7, 8, or 9 (typically 7 or 8 for newer).
    Format: +91-XXXXX-XXXXX (Indian mobile format).
    """
    first_digit = random.choice(["6", "7", "8", "9"])
    remaining = "".join(random.choices(string.digits, k=9))
    number = f"+91{first_digit}{remaining}"
    formatted = f"+91 {first_digit}{remaining[:4]} {remaining[4:]}"
    return number, formatted


def _generate_jio_sim_profile() -> dict:
    """Generate a complete Jio SIM profile with all network identifiers."""
    phone_raw, phone_formatted = _generate_jio_phone_number()
    return {
        "carrier_name":      config.JIO_CARRIER_NAME,
        "carrier_full":      config.JIO_CARRIER_FULL,
        "mcc":               config.JIO_MCC,
        "mnc":               config.JIO_MNC,
        "sim_operator":      config.JIO_SIM_OPERATOR,
        "iccid":             _generate_jio_iccid(),
        "imsi":              _generate_jio_imsi(),
        "phone_raw":         phone_raw,
        "phone_formatted":   phone_formatted,
        "network_type":      config.JIO_NETWORK_TYPE,
        "network_class":     config.JIO_NETWORK_CLASS,
        "nr_band":           config.JIO_5G_NR_BAND,
        "iso_country":       config.JIO_ISO_COUNTRY,
        "locale":            config.JIO_LOCALE,
        "timezone":          config.JIO_TIMEZONE,
        "downlink_mbps":     config.JIO_5G_DOWNLINK_MBPS + random.uniform(-20, 20),
        "uplink_mbps":       config.JIO_5G_UPLINK_MBPS + random.uniform(-5, 5),
        "rtt_ms":            int(config.JIO_5G_RTT_MS + random.uniform(-5, 5)),
        "signal_dbm":        config.JIO_5G_SIGNAL_DBM + random.randint(-15, 10),
    }


# ── Device profile dataclass ──────────────────────────────────────────────────

@dataclass
class DeviceProfile:
    imei:               str
    android_id:         str
    device_fingerprint: str
    user_agent:         str
    chrome_version:     str
    sim_profile:        dict = field(default_factory=dict)
    session_id:         str = field(default_factory=lambda: str(uuid.uuid4()))

    # Fixed Pixel 10 Pro hardware identity
    model:           str   = config.DEVICE_MODEL
    brand:           str   = config.DEVICE_BRAND
    manufacturer:    str   = config.DEVICE_MANUFACTURER
    android_version: str   = config.ANDROID_VERSION
    android_sdk:     str   = config.ANDROID_SDK
    build_id:        str   = config.BUILD_ID

    # Hardware capabilities (spoofed via CDP + JS injection)
    device_memory:          int   = 16        # 16 GB RAM (spoofed, browser API has no cap in JS)
    hardware_concurrency:   int   = 8         # Tensor G5 reported cores
    max_touch_points:       int   = 5         # realistic multitouch
    screen_width:           int   = config.SCREEN_CSS_WIDTH   # 412
    screen_height:          int   = config.SCREEN_CSS_HEIGHT  # 915
    pixel_ratio:            float = config.SCREEN_PIXEL_RATIO # 3.5
    gpu_vendor:             str   = config.DEVICE_GPU_VENDOR
    gpu_renderer:           str   = config.DEVICE_GPU_RENDERER

    @property
    def is_jio_sim(self) -> bool:
        """Check if this device has a Jio SIM profile attached."""
        return bool(self.sim_profile and self.sim_profile.get("carrier_name") == "Jio")

    def client_hints_metadata(self) -> dict:
        """
        Full userAgentMetadata dict for CDP Emulation.setUserAgentOverride.
        This is what Google reads via the Sec-CH-UA-* headers to identify
        the real device behind the reduced User-Agent string.
        """
        major = str(config.CHROME_MAJOR_VERSION)
        return {
            "brands": [
                {"brand": "Google Chrome",  "version": major},
                {"brand": "Chromium",       "version": major},
                {"brand": "Not:A-Brand",    "version": "24"},
            ],
            "fullVersionList": [
                {"brand": "Google Chrome",  "version": self.chrome_version},
                {"brand": "Chromium",       "version": self.chrome_version},
                {"brand": "Not:A-Brand",    "version": "24.0.0.0"},
            ],
            "platform":        "Android",
            "platformVersion": f"{config.ANDROID_VERSION}.0.0",
            "architecture":    "arm",
            "model":           self.model,      # "Pixel 10 Pro" — the real device hint
            "mobile":          True,
            "bitness":         "64",
            "wow64":           False,
        }

    def navigator_js(self) -> str:
        """
        JavaScript injected on every new document via CDP
        Page.addScriptToEvaluateOnNewDocument.

        Overrides all detectable browser fingerprint signals to match a real
        physical Pixel 10 Pro running Chrome 149 on Jio 5G India network.
        """
        gpu_vendor   = self.gpu_vendor.replace("'", "\\'")
        gpu_renderer = self.gpu_renderer.replace("'", "\\'")

        # Jio SIM network parameters for JS injection
        sim = self.sim_profile or {}
        sim_locale       = sim.get("locale", "en-US")
        sim_timezone     = sim.get("timezone", "UTC")
        sim_downlink     = round(sim.get("downlink_mbps", 12.5), 1)
        sim_rtt          = sim.get("rtt_ms", 45)
        sim_network_type = sim.get("network_type", "4G").lower()
        sim_carrier      = sim.get("carrier_name", "").replace("'", "\\'")
        sim_carrier_full = sim.get("carrier_full", "").replace("'", "\\'")
        sim_mcc          = sim.get("mcc", "")
        sim_mnc          = sim.get("mnc", "")
        sim_sim_operator = sim.get("sim_operator", "")
        sim_nr_band      = sim.get("nr_band", "")
        sim_signal       = sim.get("signal_dbm", -70)
        sim_iso_country  = sim.get("iso_country", "")
        jio_min_plan     = config.JIO_MIN_PLAN_AMOUNT

        return f"""
(function () {{
  'use strict';

  // ── 1. Remove automation trace ──────────────────────────────────────────
  try {{
    const desc = Object.getOwnPropertyDescriptor(navigator, 'webdriver');
    if (desc) {{
      Object.defineProperty(navigator, 'webdriver', {{
        get: () => undefined,
        configurable: true
      }});
    }}
  }} catch (e) {{}}

  // ── 2. Platform ─────────────────────────────────────────────────────────
  try {{
    Object.defineProperty(navigator, 'platform', {{
      get: () => 'Linux armv8l',
      configurable: true
    }});
  }} catch (e) {{}}

  // ── 3. Hardware ─────────────────────────────────────────────────────────
  try {{
    Object.defineProperty(navigator, 'deviceMemory', {{
      get: () => {self.device_memory},
      configurable: true
    }});
  }} catch (e) {{}}

  try {{
    Object.defineProperty(navigator, 'hardwareConcurrency', {{
      get: () => {self.hardware_concurrency},
      configurable: true
    }});
  }} catch (e) {{}}

  try {{
    Object.defineProperty(navigator, 'maxTouchPoints', {{
      get: () => {self.max_touch_points},
      configurable: true
    }});
  }} catch (e) {{}}

  // ── 4. Touch support flags ──────────────────────────────────────────────
  try {{
    window.ontouchstart = null;
    window.ontouchmove  = null;
    window.ontouchend   = null;
    window.TouchEvent   = window.TouchEvent || function () {{}};
  }} catch (e) {{}}

  // ── 5. Vendor ───────────────────────────────────────────────────────────
  try {{
    Object.defineProperty(navigator, 'vendor', {{
      get: () => 'Google Inc.',
      configurable: true
    }});
  }} catch (e) {{}}

  // ── 6. Language & Locale (Jio India: en-IN) ─────────────────────────────
  try {{
    Object.defineProperty(navigator, 'language', {{
      get: () => '{sim_locale}',
      configurable: true
    }});
    Object.defineProperty(navigator, 'languages', {{
      get: () => Object.freeze(['{sim_locale}', 'en-IN', 'en', 'hi']),
      configurable: true
    }});
  }} catch (e) {{}}

  // ── 7. Screen geometry ──────────────────────────────────────────────────
  try {{
    Object.defineProperty(screen, 'width',       {{ get: () => {self.screen_width},  configurable: true }});
    Object.defineProperty(screen, 'height',      {{ get: () => {self.screen_height}, configurable: true }});
    Object.defineProperty(screen, 'availWidth',  {{ get: () => {self.screen_width},  configurable: true }});
    Object.defineProperty(screen, 'availHeight', {{ get: () => {self.screen_height}, configurable: true }});
    Object.defineProperty(screen, 'colorDepth',  {{ get: () => 24, configurable: true }});
    Object.defineProperty(screen, 'pixelDepth',  {{ get: () => 24, configurable: true }});
    Object.defineProperty(window, 'devicePixelRatio', {{
      get: () => {self.pixel_ratio},
      configurable: true
    }});
    Object.defineProperty(window, 'innerWidth',  {{ get: () => {self.screen_width},  configurable: true }});
    Object.defineProperty(window, 'innerHeight', {{ get: () => {self.screen_height}, configurable: true }});
  }} catch (e) {{}}

  // ── 8. WebGL GPU fingerprint ────────────────────────────────────────────
  const patchWebGL = (Ctx) => {{
    if (!Ctx) return;
    const orig = Ctx.prototype.getParameter;
    Ctx.prototype.getParameter = function (param) {{
      if (param === 0x9245) return '{gpu_vendor}';   // UNMASKED_VENDOR_WEBGL
      if (param === 0x9246) return '{gpu_renderer}'; // UNMASKED_RENDERER_WEBGL
      if (param === 0x1F00) return '{gpu_vendor}';   // VENDOR
      if (param === 0x1F01) return '{gpu_renderer}'; // RENDERER
      return orig.call(this, param);
    }};
  }};
  try {{ patchWebGL(WebGLRenderingContext);  }} catch (e) {{}}
  try {{ patchWebGL(WebGL2RenderingContext); }} catch (e) {{}}

  // ── 9. Battery API ──────────────────────────────────────────────────────
  try {{
    const level = 0.82 + Math.random() * 0.16;
    const fakeBattery = {{
      charging: true,
      chargingTime: 0,
      dischargingTime: Infinity,
      level: level,
      addEventListener:    () => {{}},
      removeEventListener: () => {{}},
      dispatchEvent:       () => false,
    }};
    navigator.getBattery = () => Promise.resolve(fakeBattery);
  }} catch (e) {{}}

  // ── 10. Network info – Jio 5G India SIM ─────────────────────────────────
  // Simulates navigator.connection API as a Jio 5G cellular connection.
  // effectiveType "4g" is the highest Chrome reports (no "5g" enum yet).
  // The actual 5G identity is in the downlink speed and custom properties.
  try {{
    const conn = {{
      effectiveType: '4g',
      downlink:      {sim_downlink},
      rtt:           {sim_rtt},
      saveData:      false,
      type:          'cellular',
      addEventListener:    () => {{}},
      removeEventListener: () => {{}},
    }};
    Object.defineProperty(navigator, 'connection', {{
      get: () => conn,
      configurable: true
    }});

    // ── Android TelephonyManager-style SIM info (exposed for Google apps) ──
    // Google services on Android read these to detect carrier & eligibility.
    window.__jio_sim__ = Object.freeze({{
      carrierName:   '{sim_carrier}',
      carrierFull:   '{sim_carrier_full}',
      mcc:           '{sim_mcc}',
      mnc:           '{sim_mnc}',
      simOperator:   '{sim_sim_operator}',
      networkType:   '{sim_network_type}',
      nrBand:        '{sim_nr_band}',
      signalDbm:     {sim_signal},
      isoCountry:    '{sim_iso_country}',
      locale:        '{sim_locale}',
      timezone:      '{sim_timezone}',
      eligible:      true,   // Jio 5G user → eligible for Gemini offer
      planType:      'unlimited_5g',
      planAmount:    {jio_min_plan},
    }});
  }} catch (e) {{}}

  // ── 11. Timezone (Jio India: Asia/Kolkata IST UTC+5:30) ────────────────
  try {{
    const origResolvedOptions = Intl.DateTimeFormat.prototype.resolvedOptions;
    Intl.DateTimeFormat.prototype.resolvedOptions = function () {{
      const opts = origResolvedOptions.call(this);
      opts.timeZone = '{sim_timezone}';
      return opts;
    }};
  }} catch (e) {{}}

  // ── 12. Plugins / MimeTypes (Android Chrome has none) ──────────────────
  try {{
    Object.defineProperty(navigator, 'plugins', {{
      get: () => Object.freeze([]),
      configurable: true
    }});
    Object.defineProperty(navigator, 'mimeTypes', {{
      get: () => Object.freeze([]),
      configurable: true
    }});
  }} catch (e) {{}}

  // ── 13. Permissions (notifications always denied on Android) ───────────
  try {{
    const origQuery = navigator.permissions.query.bind(navigator.permissions);
    navigator.permissions.query = (params) => {{
      if (params && params.name === 'notifications') {{
        return Promise.resolve({{ state: 'denied', onchange: null }});
      }}
      return origQuery(params);
    }};
  }} catch (e) {{}}

  // ── 14. Chrome runtime object (present on real Chrome) ─────────────────
  try {{
    if (!window.chrome) {{
      window.chrome = {{
        runtime: {{
          connect:   () => {{}},
          sendMessage: () => {{}},
        }},
        loadTimes:  () => {{}},
        csi:        () => {{}},
      }};
    }}
  }} catch (e) {{}}

}})();
"""

    def as_headers(self) -> dict:
        sim = self.sim_profile or {}
        locale = sim.get("locale", "en-US")
        return {
            "User-Agent":      self.user_agent,
            "Accept-Language": f"{locale},{locale.split('-')[0]};q=0.9,en;q=0.8",
            "Accept-Encoding": "gzip, deflate, br",
        }

    def sim_summary(self) -> str:
        """Return a formatted summary of the Jio SIM network profile."""
        sim = self.sim_profile
        if not sim:
            return "📶 *SIM Network:* No SIM profile attached"

        return (
            f"📶 *SIM Network — {sim.get('carrier_name', 'Unknown')}*\n"
            f"Carrier: {sim.get('carrier_full', '—')}\n"
            f"Network: {sim.get('network_type', '—')} ({sim.get('nr_band', '—')})\n"
            f"MCC/MNC: `{sim.get('mcc', '—')}`/`{sim.get('mnc', '—')}`\n"
            f"SIM Operator: `{sim.get('sim_operator', '—')}`\n"
            f"ICCID: `{sim.get('iccid', '—')}`\n"
            f"IMSI: `{sim.get('imsi', '—')}`\n"
            f"Phone: `{sim.get('phone_formatted', '—')}`\n"
            f"Signal: {sim.get('signal_dbm', '—')} dBm\n"
            f"Speed: ↓{sim.get('downlink_mbps', 0):.0f} Mbps / ↑{sim.get('uplink_mbps', 0):.0f} Mbps\n"
            f"Latency: {sim.get('rtt_ms', '—')} ms\n"
            f"Locale: {sim.get('locale', '—')}  |  TZ: {sim.get('timezone', '—')}\n"
            f"Country: {sim.get('iso_country', '—').upper()}"
        )

    def summary(self) -> str:
        lines = [
            f"📱 *Device Profile*",
            f"Model: {self.model}  |  Build: {self.build_id}",
            f"Android: {self.android_version}  |  Chrome: {self.chrome_version}",
            f"RAM: {self.device_memory}GB  |  CPU: {self.hardware_concurrency} cores",
            f"Screen: {self.screen_width}×{self.screen_height} @{self.pixel_ratio}×",
            f"GPU: {self.gpu_renderer}",
            f"IMEI: `{self.imei}`",
            f"Android ID: `{self.android_id}`",
            f"Session: `{self.session_id[:8]}…`",
        ]
        if self.is_jio_sim:
            sim = self.sim_profile
            lines.append(f"\n📶 *SIM: {sim.get('carrier_name')} {sim.get('network_type')}*")
            lines.append(f"Phone: `{sim.get('phone_formatted', '—')}`")
            lines.append(f"MCC/MNC: `{sim.get('mcc')}/{sim.get('mnc')}`  |  Band: {sim.get('nr_band')}")
            lines.append(f"Speed: ↓{sim.get('downlink_mbps', 0):.0f} Mbps  |  Latency: {sim.get('rtt_ms')} ms")
            lines.append(f"Locale: {sim.get('locale')}  |  TZ: {sim.get('timezone')}")
        return "\n".join(lines)


# ── Public factory ────────────────────────────────────────────────────────────

def create_device_profile(jio_sim: bool = True) -> DeviceProfile:
    """
    Create a fresh Pixel 10 Pro device profile with unique per-session
    identifiers, a fully spoofed hardware fingerprint, and an optional
    Jio India 5G SIM network profile.

    Args:
        jio_sim: If True (default), attach a Jio 5G SIM profile so the
                 device appears as a Jio India subscriber eligible for
                 the Google Gemini 18-month free Pro offer.
    """
    chrome_version = _random_chrome_patch()

    # Chrome UA Reduction: device model never appears in UA string
    template   = config.USER_AGENT_TEMPLATES[0]
    user_agent = template.format(chrome=chrome_version)

    fingerprint = _generate_device_fingerprint(
        config.DEVICE_MODEL,
        config.BUILD_ID,
        config.ANDROID_VERSION,
    )

    sim_profile = _generate_jio_sim_profile() if jio_sim else {}

    return DeviceProfile(
        imei=_generate_imei(),
        android_id=_generate_android_id(),
        device_fingerprint=fingerprint,
        user_agent=user_agent,
        chrome_version=chrome_version,
        sim_profile=sim_profile,
    )
