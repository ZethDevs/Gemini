"""
Telegram Bot entry point for the Pixel 10 Pro Google One Gemini Bot.

Commands:
  /start             – Show welcome message and available commands
  /login             – Begin credential capture flow (email → password → 2FA)
  /check_offer       – Run Google One automation and look for Gemini Pro offer
  /check_jio_offer   – Run Jio India 5G automation for 18-month free Gemini Pro
  /get_link          – Show the last captured offer link
  /status            – Show current session status and device profile
  /sim_info          – Show Jio SIM network profile details
"""

import asyncio
import io
import logging
import sys

from telegram import Update, InputMediaPhoto, ReplyKeyboardRemove
from telegram.ext import (
    Application,
    CommandHandler,
    ConversationHandler,
    MessageHandler,
    ContextTypes,
    filters,
)

import config
from device_simulator import create_device_profile
from google_automation import (
    GoogleAutomationError,
    check_gemini_offer,
    check_jio_gemini_offer,
)

# ── Logging ───────────────────────────────────────────────────────────────────
logging.basicConfig(level=config.LOG_LEVEL, format=config.LOG_FORMAT)
logger = logging.getLogger(__name__)

# ── Conversation states ───────────────────────────────────────────────────────
AWAIT_EMAIL, AWAIT_PASSWORD, AWAIT_TOTP = range(3)


# ── Helpers ───────────────────────────────────────────────────────────────────

def _get_session(chat_id: int) -> dict:
    """Return (creating if absent) the session dict for *chat_id*."""
    if chat_id not in config.SESSION_STORE:
        config.SESSION_STORE[chat_id] = {}
    return config.SESSION_STORE[chat_id]


def _make_progress_callback(bot, chat_id: int, loop: asyncio.AbstractEventLoop):
    """
    Return a thread-safe callback that sends a text message + optional
    screenshot photo to Telegram from inside the Selenium worker thread.
    """
    def _cb(msg: str, screenshot_bytes: bytes | None = None):
        async def _send():
            try:
                if screenshot_bytes:
                    await bot.send_photo(
                        chat_id=chat_id,
                        photo=io.BytesIO(screenshot_bytes),
                        caption=msg,
                    )
                else:
                    await bot.send_message(
                        chat_id=chat_id,
                        text=msg,
                    )
            except Exception as e:
                logger.warning("Progress send error: %s", e)

        asyncio.run_coroutine_threadsafe(_send(), loop)

    return _cb


# ── Handlers ──────────────────────────────────────────────────────────────────

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send welcome message with command menu."""
    await update.message.reply_text(
        "🤖 *Pixel 10 Pro Google One + Jio Bot*\n\n"
        "This bot simulates a Google Pixel 10 Pro (Android 16) with a "
        "*Jio India 5G SIM*, logs into your Google account, and retrieves "
        "Gemini Pro offer links.\n\n"
        "🎯 *Supported Offers:*\n"
        "• *12-month* free Gemini Pro (Google One — Pixel device)\n"
        "• *18-month* free Google AI Pro (Jio 5G — ₹35,100 value)\n\n"
        "📋 *Available Commands:*\n"
        "• /login – Enter your Gmail credentials + 2FA\n"
        "• /check\\_offer – Detect Gemini Pro on Google One\n"
        "• /check\\_jio\\_offer – Detect Jio 18-month free Gemini offer\n"
        "• /get\\_link – Show the last captured offer link\n"
        "• /sim\\_info – View Jio SIM network profile\n"
        "• /status – View current session & device info\n\n"
        "⚠️ *Privacy Note:* Credentials are held in memory only for the "
        "duration of the session and never stored persistently.",
        parse_mode="Markdown",
    )


# ── /login conversation ───────────────────────────────────────────────────────

async def login_start(update: Update,
                      context: ContextTypes.DEFAULT_TYPE) -> int:
    await update.message.reply_text(
        "📧 Please enter your Gmail address:",
        reply_markup=ReplyKeyboardRemove(),
    )
    return AWAIT_EMAIL


async def login_email(update: Update,
                      context: ContextTypes.DEFAULT_TYPE) -> int:
    email = update.message.text.strip()
    context.user_data["pending_email"] = email
    await update.message.reply_text(
        f"✅ Email received: `{email}`\n\n🔒 Now enter your password:",
        parse_mode="Markdown",
    )
    return AWAIT_PASSWORD


async def login_password(update: Update,
                         context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data["pending_password"] = update.message.text.strip()
    try:
        await update.message.delete()
    except Exception:
        pass
    await update.effective_chat.send_message(
        "✅ Password received.\n\n"
        "🔐 Now enter your *2FA secret key* (the 32-character base32 code "
        "from your authenticator app).\n\n"
        "If you don't have 2FA enabled, send `none`.",
        parse_mode="Markdown",
    )
    return AWAIT_TOTP


async def login_totp(update: Update,
                     context: ContextTypes.DEFAULT_TYPE) -> int:
    chat_id = update.effective_chat.id
    raw = update.message.text.strip()
    totp_secret = None if raw.lower() == "none" else raw.upper().replace(" ", "")

    email = context.user_data.pop("pending_email", "")
    password = context.user_data.pop("pending_password", "")

    try:
        await update.message.delete()
    except Exception:
        pass

    session = _get_session(chat_id)
    session["email"] = email
    session["password"] = password
    session["totp_secret"] = totp_secret
    session["device"] = create_device_profile()
    session["offer_link"] = None

    totp_status = "✅ 2FA secret saved" if totp_secret else "⚠️ No 2FA (proceeding without)"

    await context.bot.send_message(
        chat_id=chat_id,
        text=(
            "✅ *Credentials saved* — new Pixel 10 Pro profile created.\n\n"
            f"{totp_status}\n\n"
            + session["device"].summary()
            + "\n\nUse /check\\_offer to start the automation."
        ),
        parse_mode="Markdown",
    )
    return ConversationHandler.END


async def login_cancel(update: Update,
                       context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data.pop("pending_email", None)
    await update.message.reply_text(
        "❌ Login cancelled.",
        reply_markup=ReplyKeyboardRemove(),
    )
    return ConversationHandler.END


# ── /check_offer ──────────────────────────────────────────────────────────────

async def check_offer(update: Update,
                      context: ContextTypes.DEFAULT_TYPE) -> None:
    """Run Google One automation with live step-by-step Telegram updates."""
    chat_id = update.effective_chat.id
    session = _get_session(chat_id)

    if not session.get("email") or not session.get("password"):
        await update.message.reply_text(
            "⚠️ No credentials found. Please use /login first."
        )
        return

    device = session.get("device")
    if not device:
        device = create_device_profile()
        session["device"] = device

    await update.message.reply_text(
        "🚀 *Starting automation — you'll get a live update at every step.*\n\n"
        "Screenshots will be sent for each stage so you can follow along.",
        parse_mode="Markdown",
    )

    loop = asyncio.get_event_loop()
    progress_cb = _make_progress_callback(context.bot, chat_id, loop)

    try:
        offer_link = await loop.run_in_executor(
            None,
            lambda: check_gemini_offer(
                session["email"],
                session["password"],
                device,
                totp_secret=session.get("totp_secret"),
                progress_callback=progress_cb,
            ),
        )
    except GoogleAutomationError as exc:
        await context.bot.send_message(
            chat_id=chat_id,
            text=f"❌ *Error:* {exc}",
            parse_mode="Markdown",
        )
        return
    except Exception as exc:
        logger.exception("Unexpected error in check_offer for chat %s", chat_id)
        await context.bot.send_message(
            chat_id=chat_id,
            text=f"❌ Unexpected error: {exc}",
        )
        return

    if offer_link:
        session["offer_link"] = offer_link
        await context.bot.send_message(
            chat_id=chat_id,
            text=(
                "🎉 *Gemini Pro Offer Found!*\n\n"
                "Tap the link below to activate your 12-month free Gemini Pro:\n\n"
                f"🔗 {offer_link}\n\n"
                "_Use /get\\_link to retrieve this link again._"
            ),
            parse_mode="Markdown",
        )
    else:
        await context.bot.send_message(
            chat_id=chat_id,
            text=(
                "😔 No active Gemini Pro offer detected on this account.\n\n"
                "The offer may not be available in your region or may have "
                "already been activated. Try again later."
            ),
        )


# ── /get_link ─────────────────────────────────────────────────────────────────

async def get_link(update: Update,
                   context: ContextTypes.DEFAULT_TYPE) -> None:
    chat_id = update.effective_chat.id
    link = _get_session(chat_id).get("offer_link")
    if link:
        await update.message.reply_text(
            f"🔗 *Last captured offer link:*\n\n{link}",
            parse_mode="Markdown",
        )
    else:
        await update.message.reply_text(
            "ℹ️ No offer link captured yet. Use /check\\_offer first.",
            parse_mode="Markdown",
        )


# ── /check_jio_offer ──────────────────────────────────────────────────────────

async def check_jio_offer(update: Update,
                          context: ContextTypes.DEFAULT_TYPE) -> None:
    """Run Jio India 5G automation to detect the 18-month free Gemini offer."""
    chat_id = update.effective_chat.id
    session = _get_session(chat_id)

    if not session.get("email") or not session.get("password"):
        await update.message.reply_text(
            "⚠️ No credentials found. Please use /login first."
        )
        return

    device = session.get("device")
    if not device:
        device = create_device_profile(jio_sim=True)
        session["device"] = device
    elif not device.is_jio_sim:
        # Re-create with Jio SIM if existing device doesn't have one
        from device_simulator import _generate_jio_sim_profile
        device.sim_profile = _generate_jio_sim_profile()
        session["device"] = device

    sim = device.sim_profile
    await update.message.reply_text(
        "🚀 *Starting Jio 5G Gemini Offer Check*\n\n"
        f"📶 SIM: {sim.get('carrier_name')} {sim.get('network_type')} "
        f"({sim.get('nr_band')})\n"
        f"📞 Phone: {sim.get('phone_formatted')}\n"
        f"🎯 Target: 18-month free Google AI Pro (₹35,100)\n\n"
        "Live updates will follow for each step.",
        parse_mode="Markdown",
    )

    loop = asyncio.get_event_loop()
    progress_cb = _make_progress_callback(context.bot, chat_id, loop)

    try:
        offer_link = await loop.run_in_executor(
            None,
            lambda: check_jio_gemini_offer(
                session["email"],
                session["password"],
                device,
                totp_secret=session.get("totp_secret"),
                progress_callback=progress_cb,
            ),
        )
    except GoogleAutomationError as exc:
        await context.bot.send_message(
            chat_id=chat_id,
            text=f"❌ *Error:* {exc}",
            parse_mode="Markdown",
        )
        return
    except Exception as exc:
        logger.exception("Unexpected error in check_jio_offer for chat %s", chat_id)
        await context.bot.send_message(
            chat_id=chat_id,
            text=f"❌ Unexpected error: {exc}",
        )
        return

    if offer_link:
        session["offer_link"] = offer_link
        await context.bot.send_message(
            chat_id=chat_id,
            text=(
                "🎉 *Jio Gemini Offer Found!*\n\n"
                "Tap the link below to activate your *18-month free "
                "Google AI Pro* subscription (₹35,100 value):\n\n"
                f"🔗 {offer_link}\n\n"
                "📋 *Benefits include:*\n"
                "• Gemini 3 access\n"
                "• 5 TB Google storage\n"
                "• AI Video Tool (Veo 3)\n"
                "• NotebookLM (5× limits)\n"
                "• Gemini in Gmail, Docs & more\n"
                "• AI Image Editing\n\n"
                "_Use /get\\_link to retrieve this link again._",
            ),
            parse_mode="Markdown",
        )
    else:
        await context.bot.send_message(
            chat_id=chat_id,
            text=(
                "😔 No active Jio Gemini offer detected.\n\n"
                "*Possible reasons:*\n"
                "• Your Google account is not linked to a Jio number\n"
                "• You need an active Jio 5G plan (₹349+)\n"
                "• You must be 18+ years old\n"
                "• The offer may already be claimed on this number\n\n"
                "💡 Make sure you have:\n"
                f"1. A Jio SIM with ₹{config.JIO_MIN_PLAN_AMOUNT}+ "
                f"unlimited 5G plan\n"
                "2. Registered on MyJio app with your Gmail\n"
                f"3. Visit: {config.JIO_GEMINI_OFFER_URL}\n\n"
                "Try again after confirming your Jio 5G eligibility.",
            ),
            parse_mode="Markdown",
        )


# ── /sim_info ─────────────────────────────────────────────────────────────────

async def sim_info(update: Update,
                   context: ContextTypes.DEFAULT_TYPE) -> None:
    """Show the Jio SIM network profile for the current session."""
    chat_id = update.effective_chat.id
    session = _get_session(chat_id)
    device = session.get("device")

    if not device:
        device = create_device_profile(jio_sim=True)
        session["device"] = device

    if device.is_jio_sim:
        await update.message.reply_text(
            device.sim_summary(),
            parse_mode="Markdown",
        )
    else:
        await update.message.reply_text(
            "ℹ️ No Jio SIM profile attached.\n"
            "Use /check\\_jio\\_offer to create one automatically.",
            parse_mode="Markdown",
        )


# ── /status ───────────────────────────────────────────────────────────────────

async def status(update: Update,
                 context: ContextTypes.DEFAULT_TYPE) -> None:
    chat_id = update.effective_chat.id
    session = _get_session(chat_id)

    if not session:
        await update.message.reply_text(
            "ℹ️ No active session. Use /login to get started."
        )
        return

    email = session.get("email", "—")
    has_creds = bool(session.get("email") and session.get("password"))
    has_2fa = bool(session.get("totp_secret"))
    offer_link = session.get("offer_link")
    device = session.get("device")

    lines = [
        "📊 *Session Status*\n",
        f"Account: `{email}`",
        f"Credentials loaded: {'✅' if has_creds else '❌'}",
        f"2FA enabled: {'✅' if has_2fa else '❌'}",
        f"Offer link captured: {'✅' if offer_link else '❌'}",
    ]
    if offer_link:
        lines.append(f"🔗 {offer_link}")
    if device:
        lines.append("\n" + device.summary())

    await update.message.reply_text(
        "\n".join(lines),
        parse_mode="Markdown",
    )


# ── Application setup ─────────────────────────────────────────────────────────

def main() -> None:
    token = config.TELEGRAM_BOT_TOKEN
    if not token:
        logger.error(
            "TELEGRAM_BOT_TOKEN is not set. Add it to Replit Secrets and restart."
        )
        sys.exit(1)

    app = Application.builder().token(token).build()

    login_conv = ConversationHandler(
        entry_points=[CommandHandler("login", login_start)],
        states={
            AWAIT_EMAIL: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, login_email)
            ],
            AWAIT_PASSWORD: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, login_password)
            ],
            AWAIT_TOTP: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, login_totp)
            ],
        },
        fallbacks=[CommandHandler("cancel", login_cancel)],
    )

    app.add_handler(CommandHandler("start", start))
    app.add_handler(login_conv)
    app.add_handler(CommandHandler("check_offer", check_offer))
    app.add_handler(CommandHandler("check_jio_offer", check_jio_offer))
    app.add_handler(CommandHandler("get_link", get_link))
    app.add_handler(CommandHandler("sim_info", sim_info))
    app.add_handler(CommandHandler("status", status))

    logger.info("Bot is running. Press Ctrl-C to stop.")
    app.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
