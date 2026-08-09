"""
Android Pixel 10 Pro device simulator with Jio India SIM network simulation.

Every call to create_device_profile() produces a UNIQUE fingerprint while
remaining within the genuine Pixel 10 Pro specification envelope:

  ─ Hardware randomisation ─
    • RAM (12 GB / 16 GB weighted)
    • CPU cores (7–8)
    • Storage (128 / 256 / 512 / 1024 GB)
    • Screen viewport (nav bar style, font scale, display zoom)
    • GPU renderer variant
    • Build ID + security patch date

  ─ Identity randomisation ─
    • IMEI (Luhn-valid, random TAC + serial)
    • Android ID (16-char hex)
    • Chrome version (major 148–150, random build+patch)
    • Session UUID

  ─ Jio SIM randomisation ─
    • MNC (21 telecom circles)
    • ICCID / IMSI / phone number
    • NR band (n78 / n28 / n5)
    • Signal strength, speed, latency

  ─ Fingerprint noise ─
    • Canvas rendering noise
    • AudioContext noise
    • Battery level + charging state
    • Performance.now() jitter
    • WebGL shader precision bits
    • Font hash perturbation
"""

import hashlib
import math
import random
import string
import uuid
from dataclasses import dataclass, field

import config


# ── Helpers ───────────────────────────────────────────────────────────────────

def _luhn_checksum(number: str) -> int:
    digits = [int(d) for d in number]
    odd_digits = digits[-1::-2]
    even_digits = digits[-2::-2]
    total = sum(odd_digits)
    for d in even_digits:
        total += sum(divmod(d * 2, 10))
    return total % 10


def _clamp(value, lo, hi):
    return max(lo, min(hi, value))


def _gauss_clamped(mean, std, lo, hi) -> float:
    return _clamp(random.gauss(mean, std), lo, hi)


# ── IMEI / Android ID ────────────────────────────────────────────────────────

def _generate_imei() -> str:
    tac = random.choice(config.PIXEL_TAC_PREFIXES)
    serial = "".join(random.choices(string.digits, k=6))
    partial = tac + serial
    check_digit = (10 - _luhn_checksum(partial + "0")) % 10
    return partial + str(check_digit)


def _generate_android_id() -> str:
    return "".join(random.choices("0123456789abcdef", k=16))


# ── Build / version ──────────────────────────────────────────────────────────

def _random_build_info() -> tuple[str, str]:
    """Return (build_id, security_patch) from the pool."""
    idx = random.randrange(len(config.BUILD_IDS))
    return config.BUILD_IDS[idx], config.SECURITY_PATCHES[idx]


def _generate_device_fingerprint(model: str, build_id: str, android: str) -> str:
    slug = model.lower().replace(" ", "_")
    return f"google/{slug}/{slug}:{android}/{build_id}/eng.user.release-keys"


# ── Chrome version ───────────────────────────────────────────────────────────

def _random_chrome_version() -> tuple[str, int]:
    """Return (full_version_string, major_version)."""
    major = random.choices(
        config.CHROME_MAJOR_VERSIONS,
        weights=config.CHROME_MAJOR_WEIGHTS,
        k=1,
    )[0]
    b_lo, b_hi = config.CHROME_BUILD_RANGES[major]
    p_lo, p_hi = config.CHROME_PATCH_RANGES[major]
    build = random.randint(b_lo, b_hi)
    patch = random.randint(p_lo, p_hi)
    return f"{major}.0.{build}.{patch}", major


# ── Hardware randomisation ───────────────────────────────────────────────────

def _random_hardware() -> dict:
    """Return a dict of randomly selected hardware parameters."""
    return {
        "ram":  random.choices(config.RAM_VARIANTS,
                               weights=config.RAM_WEIGHTS, k=1)[0],
        "cores": random.choices(config.CPU_CORE_VARIANTS,
                                weights=config.CPU_CORE_WEIGHTS, k=1)[0],
        "storage": random.choices(config.STORAGE_VARIANTS_GB,
                                  weights=config.STORAGE_WEIGHTS, k=1)[0],
        "gpu_renderer": random.choices(config.GPU_RENDERERS,
                                       weights=config.GPU_RENDERER_WEIGHTS, k=1)[0],
        "gpu_vendor":   config.GPU_VENDORS[0],
        "viewport": random.choices(config.SCREEN_VIEWPORTS,
                                   weights=config.SCREEN_WEIGHTS, k=1)[0],
    }


# ── Battery ──────────────────────────────────────────────────────────────────

def _random_battery() -> dict:
    level = round(random.uniform(*config.BATTERY_LEVEL_RANGE), 4)
    charging = random.random() < config.BATTERY_CHARGING_PCT
    if charging:
        # If charging, level tends to be higher
        level = round(max(level, random.uniform(0.5, 0.99)), 4)
    return {
        "level":    level,
        "charging": charging,
        "charging_time": 0 if charging else float("inf"),
        "discharging_time": float("inf") if charging else random.randint(3600, 18000),
    }


# ── Fingerprint noise seeds ──────────────────────────────────────────────────

def _random_fingerprint_seeds() -> dict:
    """Per-session noise seeds for canvas, audio, WebGL, font hashing."""
    canvas_noise = round(random.uniform(*config.CANVAS_NOISE_RANGE), 8)
    audio_noise  = round(random.uniform(*config.AUDIO_NOISE_RANGE), 10)
    # WebGL shader precision — real devices vary slightly
    webgl_vertex_prec   = random.choice([23, 24])     # HIGH_FLOAT bits
    webgl_fragment_prec = random.choice([23, 24])
    # Performance.now() jitter magnitude (µs)
    perf_jitter = round(random.uniform(0.5, 3.0), 2)
    # Font enumeration hash perturbation
    font_seed = random.randint(0, 255)
    return {
        "canvas_noise":      canvas_noise,
        "audio_noise":       audio_noise,
        "webgl_vertex_prec": webgl_vertex_prec,
        "webgl_fragment_prec": webgl_fragment_prec,
        "perf_jitter":       perf_jitter,
        "font_seed":         font_seed,
    }


# ── Jio SIM helpers ──────────────────────────────────────────────────────────

def _generate_jio_iccid(mnc: str) -> str:
    """20-digit Luhn-valid ICCID: 89 + 91 + MNC + serial + check."""
    prefix = f"8991{mnc}"
    needed = 19 - len(prefix)
    serial = "".join(random.choices(string.digits, k=needed))
    partial = prefix + serial
    check_digit = (10 - _luhn_checksum(partial + "0")) % 10
    return partial + str(check_digit)


def _generate_jio_imsi(mcc: str, mnc: str) -> str:
    subscriber_id = "".join(random.choices(string.digits, k=15 - len(mcc) - len(mnc)))
    return f"{mcc}{mnc}{subscriber_id}"


def _generate_jio_phone_number() -> tuple[str, str]:
    first_digit = random.choice(["6", "7", "8", "9"])
    remaining = "".join(random.choices(string.digits, k=9))
    raw = f"+91{first_digit}{remaining}"
    formatted = f"+91 {first_digit}{remaining[:4]} {remaining[4:]}"
    return raw, formatted


def _generate_jio_sim_profile() -> dict:
    mnc, circle = random.choice(config.JIO_MNC_POOL)
    phone_raw, phone_formatted = _generate_jio_phone_number()
    nr_band = random.choices(
        config.JIO_NR_BANDS,
        weights=config.JIO_NR_BAND_WEIGHTS, k=1,
    )[0]
    return {
        "carrier_name":    config.JIO_CARRIER_NAME,
        "carrier_full":    config.JIO_CARRIER_FULL,
        "mcc":             config.JIO_MCC,
        "mnc":             mnc,
        "circle":          circle,
        "sim_operator":    f"{config.JIO_MCC}{mnc}",
        "iccid":           _generate_jio_iccid(mnc),
        "imsi":            _generate_jio_imsi(config.JIO_MCC, mnc),
        "phone_raw":       phone_raw,
        "phone_formatted": phone_formatted,
        "network_type":    config.JIO_NETWORK_TYPE,
        "network_class":   config.JIO_NETWORK_CLASS,
        "nr_band":         nr_band,
        "iso_country":     config.JIO_ISO_COUNTRY,
        "locale":          config.JIO_LOCALE,
        "timezone":        config.JIO_TIMEZONE,
        "downlink_mbps":   round(random.uniform(*config.JIO_5G_DOWNLINK_RANGE), 1),
        "uplink_mbps":     round(random.uniform(*config.JIO_5G_UPLINK_RANGE), 1),
        "rtt_ms":          random.randint(*config.JIO_5G_RTT_RANGE),
        "signal_dbm":      random.randint(*config.JIO_5G_SIGNAL_RANGE),
    }


# ══════════════════════════════════════════════════════════════════════════════
#  DeviceProfile dataclass
# ══════════════════════════════════════════════════════════════════════════════

@dataclass
class DeviceProfile:
    # Unique per-session identifiers
    imei:               str
    android_id:         str
    device_fingerprint: str
    user_agent:         str
    chrome_version:     str
    chrome_major:       int
    build_id:           str
    security_patch:     str

    # Hardware (randomised per session)
    device_memory:        int
    hardware_concurrency: int
    storage_gb:           int
    screen_width:         int
    screen_height:        int
    pixel_ratio:          float
    gpu_vendor:           str
    gpu_renderer:         str

    # Per-session noise
    battery:              dict
    fingerprint_seeds:    dict

    # Optional SIM profile
    sim_profile:          dict = field(default_factory=dict)
    session_id:           str  = field(default_factory=lambda: str(uuid.uuid4()))

    # Fixed identity
    model:           str = config.DEVICE_MODEL
    brand:           str = config.DEVICE_BRAND
    manufacturer:    str = config.DEVICE_MANUFACTURER
    android_version: str = config.ANDROID_VERSION
    android_sdk:     str = config.ANDROID_SDK
    max_touch_points: int = 5

    # ── Properties ────────────────────────────────────────────────────────────

    @property
    def is_jio_sim(self) -> bool:
        return bool(self.sim_profile and self.sim_profile.get("carrier_name") == "Jio")

    # ── CDP client hints ─────────────────────────────────────────────────────

    def client_hints_metadata(self) -> dict:
        major = str(self.chrome_major)
        # Not:A-Brand version rotates per session to match real Chrome behaviour
        nab_ver = str(random.randint(8, 99))
        return {
            "brands": [
                {"brand": "Google Chrome",  "version": major},
                {"brand": "Chromium",       "version": major},
                {"brand": "Not:A-Brand",    "version": nab_ver},
            ],
            "fullVersionList": [
                {"brand": "Google Chrome",  "version": self.chrome_version},
                {"brand": "Chromium",       "version": self.chrome_version},
                {"brand": "Not:A-Brand",    "version": f"{nab_ver}.0.0.0"},
            ],
            "platform":        "Android",
            "platformVersion": f"{self.android_version}.0.0",
            "architecture":    "arm",
            "model":           self.model,
            "mobile":          True,
            "bitness":         "64",
            "wow64":           False,
        }

    # ── Navigator JS injection ───────────────────────────────────────────────

    def navigator_js(self) -> str:
        """
        JavaScript injected via CDP Page.addScriptToEvaluateOnNewDocument.
        Every value below is unique per session (hardware, battery, noise seeds).
        """
        gv  = self.gpu_vendor.replace("'", "\\'")
        gr  = self.gpu_renderer.replace("'", "\\'")
        bat = self.battery
        fps = self.fingerprint_seeds
        sim = self.sim_profile or {}

        # Pre-compute all sim strings to avoid f-string backslash issues
        s_locale       = sim.get("locale", "en-US")
        s_timezone     = sim.get("timezone", "UTC")
        s_downlink     = round(sim.get("downlink_mbps", 12.5), 1)
        s_rtt          = sim.get("rtt_ms", 45)
        s_net_type     = sim.get("network_type", "4G").lower()
        s_carrier      = sim.get("carrier_name", "").replace("'", "\\'")
        s_carrier_full = sim.get("carrier_full", "").replace("'", "\\'")
        s_mcc          = sim.get("mcc", "")
        s_mnc          = sim.get("mnc", "")
        s_sim_op       = sim.get("sim_operator", "")
        s_nr_band      = sim.get("nr_band", "")
        s_signal       = sim.get("signal_dbm", -70)
        s_iso          = sim.get("iso_country", "")
        s_circle       = sim.get("circle", "").replace("'", "\\'")
        jio_min_plan   = config.JIO_MIN_PLAN_AMOUNT

        # Screen
        sw = self.screen_width
        sh = self.screen_height
        pr = self.pixel_ratio

        # Battery
        bat_level = bat["level"]
        bat_charging = "true" if bat["charging"] else "false"
        bat_ct = bat["charging_time"] if bat["charging_time"] != float("inf") else "Infinity"
        bat_dt = bat["discharging_time"] if bat["discharging_time"] != float("inf") else "Infinity"

        # Fingerprint noise
        cn = fps["canvas_noise"]
        an = fps["audio_noise"]
        wv = fps["webgl_vertex_prec"]
        wf = fps["webgl_fragment_prec"]
        pj = fps["perf_jitter"]
        fs = fps["font_seed"]

        # Hardware
        dm = self.device_memory
        hc = self.hardware_concurrency
        sg = self.storage_gb

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

  // ── 3. Hardware (randomised per session) ────────────────────────────────
  try {{
    Object.defineProperty(navigator, 'deviceMemory', {{
      get: () => {dm},
      configurable: true
    }});
  }} catch (e) {{}}
  try {{
    Object.defineProperty(navigator, 'hardwareConcurrency', {{
      get: () => {hc},
      configurable: true
    }});
  }} catch (e) {{}}
  try {{
    Object.defineProperty(navigator, 'maxTouchPoints', {{
      get: () => {self.max_touch_points},
      configurable: true
    }});
  }} catch (e) {{}}
  // Storage API (navigator.storage.estimate) — randomised quota
  try {{
    const quota = {sg} * 1024 * 1024 * 1024;
    const usage = Math.floor(quota * (0.15 + Math.random() * 0.45));
    if (navigator.storage && navigator.storage.estimate) {{
      const origEstimate = navigator.storage.estimate.bind(navigator.storage);
      navigator.storage.estimate = () => Promise.resolve({{
        quota: quota,
        usage: usage,
        usageDetails: {{ }},
      }});
    }}
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

  // ── 6. Language & Locale ────────────────────────────────────────────────
  try {{
    Object.defineProperty(navigator, 'language', {{
      get: () => '{s_locale}',
      configurable: true
    }});
    Object.defineProperty(navigator, 'languages', {{
      get: () => Object.freeze(['{s_locale}', 'en-IN', 'en', 'hi']),
      configurable: true
    }});
  }} catch (e) {{}}

  // ── 7. Screen geometry (randomised viewport) ───────────────────────────
  try {{
    Object.defineProperty(screen, 'width',       {{ get: () => {sw},  configurable: true }});
    Object.defineProperty(screen, 'height',      {{ get: () => {sh}, configurable: true }});
    Object.defineProperty(screen, 'availWidth',  {{ get: () => {sw},  configurable: true }});
    Object.defineProperty(screen, 'availHeight', {{ get: () => {sh}, configurable: true }});
    Object.defineProperty(screen, 'colorDepth',  {{ get: () => 24, configurable: true }});
    Object.defineProperty(screen, 'pixelDepth',  {{ get: () => 24, configurable: true }});
    Object.defineProperty(window, 'devicePixelRatio', {{
      get: () => {pr},
      configurable: true
    }});
    Object.defineProperty(window, 'innerWidth',  {{ get: () => {sw},  configurable: true }});
    Object.defineProperty(window, 'innerHeight', {{ get: () => {sh}, configurable: true }});
    // Screen orientation — Pixel 10 Pro portrait
    try {{
      Object.defineProperty(screen.orientation, 'type', {{
        get: () => 'portrait-primary',
        configurable: true
      }});
      Object.defineProperty(screen.orientation, 'angle', {{
        get: () => 0,
        configurable: true
      }});
    }} catch (e2) {{}}
  }} catch (e) {{}}

  // ── 8. WebGL GPU fingerprint (randomised renderer variant) ─────────────
  const patchWebGL = (Ctx) => {{
    if (!Ctx) return;
    const orig = Ctx.prototype.getParameter;
    Ctx.prototype.getParameter = function (param) {{
      if (param === 0x9245) return '{gv}';
      if (param === 0x9246) return '{gr}';
      if (param === 0x1F00) return '{gv}';
      if (param === 0x1F01) return '{gr}';
      // Shader precision — varies per session
      if (param === 0x8DFA) return {wv};   // VERTEX_SHADER HIGH_FLOAT precision
      if (param === 0x8DFF) return {wf};   // FRAGMENT_SHADER HIGH_FLOAT precision
      return orig.call(this, param);
    }};
  }};
  try {{ patchWebGL(WebGLRenderingContext);  }} catch (e) {{}}
  try {{ patchWebGL(WebGL2RenderingContext); }} catch (e) {{}}

  // ── 8b. Canvas fingerprint noise ───────────────────────────────────────
  try {{
    const noise = {cn};
    const origToDataURL = HTMLCanvasElement.prototype.toDataURL;
    HTMLCanvasElement.prototype.toDataURL = function (type) {{
      if (type === 'image/png' || !type) {{
        const ctx = this.getContext('2d');
        if (ctx) {{
          const style = ctx.fillStyle;
          ctx.fillStyle = 'rgba(255,255,255,0.01)';
          ctx.fillRect(0, 0, 1, 1);
          ctx.fillStyle = style;
        }}
      }}
      return origToDataURL.apply(this, arguments);
    }};
    const origGetImageData = CanvasRenderingContext2D.prototype.getImageData;
    CanvasRenderingContext2D.prototype.getImageData = function () {{
      const data = origGetImageData.apply(this, arguments);
      const px = data.data;
      for (let i = 0; i < px.length; i += 4) {{
        px[i]   = Math.min(255, Math.max(0, px[i]   + Math.round((Math.random()-0.5)*2)));
        px[i+1] = Math.min(255, Math.max(0, px[i+1] + Math.round((Math.random()-0.5)*2)));
      }}
      return data;
    }};
  }} catch (e) {{}}

  // ── 9. Battery API (randomised level + charging state) ─────────────────
  try {{
    const fakeBattery = {{
      charging:         {bat_charging},
      chargingTime:     {bat_ct},
      dischargingTime:  {bat_dt},
      level:            {bat_level},
      addEventListener:    () => {{}},
      removeEventListener: () => {{}},
      dispatchEvent:       () => false,
    }};
    navigator.getBattery = () => Promise.resolve(fakeBattery);
  }} catch (e) {{}}

  // ── 10. Network info – cellular connection ─────────────────────────────
  try {{
    const conn = {{
      effectiveType: '4g',
      downlink:      {s_downlink},
      rtt:           {s_rtt},
      saveData:      false,
      type:          'cellular',
      addEventListener:    () => {{}},
      removeEventListener: () => {{}},
    }};
    Object.defineProperty(navigator, 'connection', {{
      get: () => conn,
      configurable: true
    }});

    // Android TelephonyManager-style SIM info for Google services
    window.__jio_sim__ = Object.freeze({{
      carrierName:   '{s_carrier}',
      carrierFull:   '{s_carrier_full}',
      mcc:           '{s_mcc}',
      mnc:           '{s_mnc}',
      circle:        '{s_circle}',
      simOperator:   '{s_sim_op}',
      networkType:   '{s_net_type}',
      nrBand:        '{s_nr_band}',
      signalDbm:     {s_signal},
      isoCountry:    '{s_iso}',
      locale:        '{s_locale}',
      timezone:      '{s_timezone}',
      eligible:      true,
      planType:      'unlimited_5g',
      planAmount:    {jio_min_plan},
    }});
  }} catch (e) {{}}

  // ── 11. Timezone ───────────────────────────────────────────────────────
  try {{
    const origResolvedOptions = Intl.DateTimeFormat.prototype.resolvedOptions;
    Intl.DateTimeFormat.prototype.resolvedOptions = function () {{
      const opts = origResolvedOptions.call(this);
      opts.timeZone = '{s_timezone}';
      return opts;
    }};
  }} catch (e) {{}}

  // ── 12. Plugins / MimeTypes ────────────────────────────────────────────
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

  // ── 13. Permissions ────────────────────────────────────────────────────
  try {{
    const origQuery = navigator.permissions.query.bind(navigator.permissions);
    navigator.permissions.query = (params) => {{
      if (params && params.name === 'notifications') {{
        return Promise.resolve({{ state: 'denied', onchange: null }});
      }}
      return origQuery(params);
    }};
  }} catch (e) {{}}

  // ── 14. Chrome runtime object ──────────────────────────────────────────
  try {{
    if (!window.chrome) {{
      window.chrome = {{
        runtime: {{
          connect:     () => {{}},
          sendMessage: () => {{}},
        }},
        loadTimes:  () => {{}},
        csi:        () => {{}},
      }};
    }}
  }} catch (e) {{}}

  // ── 15. AudioContext fingerprint noise ─────────────────────────────────
  try {{
    const aNoise = {an};
    const origCreateOscillator = AudioContext.prototype.createOscillator;
    AudioContext.prototype.createOscillator = function () {{
      const osc = origCreateOscillator.call(this);
      osc._fnoise = aNoise;
      return osc;
    }};
    const origGetFloat = AnalyserNode.prototype.getFloatFrequencyData;
    AnalyserNode.prototype.getFloatFrequencyData = function (arr) {{
      origGetFloat.call(this, arr);
      for (let i = 0; i < arr.length; i++) {{
        arr[i] += (Math.random() - 0.5) * aNoise * 100;
      }}
    }};
  }} catch (e) {{}}

  // ── 16. Performance.now() jitter ───────────────────────────────────────
  try {{
    const jitter = {pj};
    const origNow = performance.now.bind(performance);
    performance.now = function () {{
      return origNow() + (Math.random() - 0.5) * jitter;
    }};
  }} catch (e) {{}}

  // ── 17. Font fingerprint perturbation ──────────────────────────────────
  try {{
    const fseed = {fs};
    const origMeasure = CanvasRenderingContext2D.prototype.measureText;
    CanvasRenderingContext2D.prototype.measureText = function (text) {{
      const m = origMeasure.call(this, text);
      // Slight width perturbation based on seed + text hash
      let hash = fseed;
      for (let i = 0; i < text.length; i++) {{
        hash = ((hash << 5) - hash + text.charCodeAt(i)) | 0;
      }}
      const perturbation = (hash % 100) / 100000;  // ±0.001 px max
      Object.defineProperty(m, 'width', {{ value: m.width + perturbation }});
      return m;
    }};
  }} catch (e) {{}}

}})();
"""

    # ── Headers ───────────────────────────────────────────────────────────────

    def as_headers(self) -> dict:
        sim = self.sim_profile or {}
        locale = sim.get("locale", "en-US")
        return {
            "User-Agent":      self.user_agent,
            "Accept-Language": f"{locale},{locale.split('-')[0]};q=0.9,en;q=0.8",
            "Accept-Encoding": "gzip, deflate, br",
        }

    # ── Summaries ─────────────────────────────────────────────────────────────

    def sim_summary(self) -> str:
        sim = self.sim_profile
        if not sim:
            return "📶 *SIM Network:* No SIM profile attached"
        return (
            f"📶 *SIM Network — {sim.get('carrier_name', 'Unknown')}*\n"
            f"Carrier: {sim.get('carrier_full', '—')}\n"
            f"Circle: {sim.get('circle', '—')}\n"
            f"Network: {sim.get('network_type', '—')} ({sim.get('nr_band', '—')})\n"
            f"MCC/MNC: `{sim.get('mcc', '—')}`/`{sim.get('mnc', '—')}`\n"
            f"SIM Operator: `{sim.get('sim_operator', '—')}`\n"
            f"ICCID: `{sim.get('iccid', '—')}`\n"
            f"IMSI: `{sim.get('imsi', '—')}`\n"
            f"Phone: `{sim.get('phone_formatted', '—')}`\n"
            f"Signal: {sim.get('signal_dbm', '—')} dBm\n"
            f"Speed: ↓{sim.get('downlink_mbps', 0):.0f} Mbps / "
            f"↑{sim.get('uplink_mbps', 0):.0f} Mbps\n"
            f"Latency: {sim.get('rtt_ms', '—')} ms\n"
            f"Locale: {sim.get('locale', '—')}  |  TZ: {sim.get('timezone', '—')}\n"
            f"Country: {sim.get('iso_country', '—').upper()}"
        )

    def summary(self) -> str:
        bat = self.battery
        fps = self.fingerprint_seeds
        lines = [
            "📱 *Device Profile*",
            f"Model: {self.model}  |  Build: `{self.build_id}`",
            f"Android: {self.android_version} (SDK {self.android_sdk})  |  Patch: {self.security_patch}",
            f"Chrome: {self.chrome_version}",
            f"RAM: {self.device_memory} GB  |  CPU: {self.hardware_concurrency} cores  |  "
            f"Storage: {self.storage_gb} GB",
            f"Screen: {self.screen_width}×{self.screen_height} @{self.pixel_ratio}×",
            f"GPU: {self.gpu_renderer}",
            f"IMEI: `{self.imei}`",
            f"Android ID: `{self.android_id}`",
            f"Battery: {bat['level']*100:.0f}% "
            f"{'⚡ charging' if bat['charging'] else '🔋 discharging'}",
            f"Fingerprint noise: canvas={fps['canvas_noise']}  "
            f"audio={fps['audio_noise']}  perf_jitter={fps['perf_jitter']}",
            f"Session: `{self.session_id[:8]}…`",
        ]
        if self.is_jio_sim:
            sim = self.sim_profile
            lines.append(f"\n📶 *SIM: {sim.get('carrier_name')} {sim.get('network_type')}*")
            lines.append(f"Phone: `{sim.get('phone_formatted', '—')}`")
            lines.append(f"Circle: {sim.get('circle', '—')}  |  "
                         f"MCC/MNC: `{sim.get('mcc')}/{sim.get('mnc')}`  |  "
                         f"Band: {sim.get('nr_band')}")
            lines.append(f"Speed: ↓{sim.get('downlink_mbps', 0):.0f} Mbps  |  "
                         f"Latency: {sim.get('rtt_ms')} ms  |  "
                         f"Signal: {sim.get('signal_dbm')} dBm")
            lines.append(f"Locale: {sim.get('locale')}  |  TZ: {sim.get('timezone')}")
        return "\n".join(lines)

    def fingerprint_hash(self) -> str:
        """Return a short hash summarising all randomised parameters."""
        raw = (
            f"{self.imei}|{self.android_id}|{self.chrome_version}|"
            f"{self.build_id}|{self.device_memory}|{self.hardware_concurrency}|"
            f"{self.screen_width}x{self.screen_height}|{self.gpu_renderer}|"
            f"{self.battery['level']}|{self.fingerprint_seeds['canvas_noise']}"
        )
        return hashlib.sha256(raw.encode()).hexdigest()[:12]


# ══════════════════════════════════════════════════════════════════════════════
#  Public factory
# ══════════════════════════════════════════════════════════════════════════════

def create_device_profile(jio_sim: bool = True) -> DeviceProfile:
    """
    Create a fresh Pixel 10 Pro device profile.

    Every field is randomised within the real specification envelope so that
    each session presents a unique fingerprint while remaining a plausible
    Pixel 10 Pro device on a Jio 5G network.

    Args:
        jio_sim: Attach a Jio 5G SIM profile (default True).
    """
    # Chrome version
    chrome_version, chrome_major = _random_chrome_version()
    user_agent = config.USER_AGENT_TEMPLATE.format(chrome=chrome_version)

    # Build / patch
    build_id, security_patch = _random_build_info()
    fingerprint = _generate_device_fingerprint(
        config.DEVICE_MODEL, build_id, config.ANDROID_VERSION,
    )

    # Hardware
    hw = _random_hardware()
    vw_w, vw_h, vw_pr = hw["viewport"]

    # Battery + noise
    battery = _random_battery()
    fp_seeds = _random_fingerprint_seeds()

    # SIM
    sim_profile = _generate_jio_sim_profile() if jio_sim else {}

    return DeviceProfile(
        imei=_generate_imei(),
        android_id=_generate_android_id(),
        device_fingerprint=fingerprint,
        user_agent=user_agent,
        chrome_version=chrome_version,
        chrome_major=chrome_major,
        build_id=build_id,
        security_patch=security_patch,
        device_memory=hw["ram"],
        hardware_concurrency=hw["cores"],
        storage_gb=hw["storage"],
        screen_width=vw_w,
        screen_height=vw_h,
        pixel_ratio=vw_pr,
        gpu_vendor=hw["gpu_vendor"],
        gpu_renderer=hw["gpu_renderer"],
        battery=battery,
        fingerprint_seeds=fp_seeds,
        sim_profile=sim_profile,
    )
