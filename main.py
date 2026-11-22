import asyncio
import base64
import html
import io
import os
import random
import secrets
import re
import shutil
import string
import time
from datetime import date, datetime
from urllib.parse import quote
import aiohttp
import aiosqlite
from aiogram import Bot, Dispatcher, F, Router
from aiogram.filters import CommandStart, Command
import hashlib
import hmac
import json
from urllib.parse import parse_qsl
from aiohttp import web
from aiogram.types import (
    Message,
    CallbackQuery,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
    LabeledPrice,
    PreCheckoutQuery,
    BotCommand,
    FSInputFile,
    WebAppInfo,
)
from aiogram.enums import ParseMode
from aiogram.exceptions import TelegramBadRequest
from openai import AsyncOpenAI

# ================= НАСТРОЙКИ ДЛЯ ХОСТИНГА (ENV) =================
BOT_TOKEN = os.getenv("BOT_TOKEN", "").strip()
UNLOCK_API_KEY = os.getenv("UNLOCK_API_KEY", "").strip()
UNLOCK_BASE_URL = os.getenv("UNLOCK_BASE_URL", "https" + "://" + "unlockapi.space/v1").strip()

# Ключи Platega API (из личного кабинета app.platega.io)
PLATEGA_MERCHANT_ID = os.getenv("PLATEGA_MERCHANT_ID", "").strip()
PLATEGA_SECRET = os.getenv("PLATEGA_SECRET", "").strip()
PLATEGA_BASE_URL = os.getenv("PLATEGA_BASE_URL", "https://app.platega.io").rstrip("/").strip()
PLATEGA_SBP_METHOD = int(os.getenv("PLATEGA_SBP_METHOD", "2"))  # 2 = СБП QR в Platega

if not BOT_TOKEN:
    raise RuntimeError("Не задана переменная окружения BOT_TOKEN! Добавь её в настройках хостинга.")
if not UNLOCK_API_KEY:
    raise RuntimeError("Не задана переменная окружения UNLOCK_API_KEY! Добавь её в настройках хостинга.")

ADMIN_ID = int(os.getenv("ADMIN_ID", "1991878700"))

CHANNEL_USERNAME = os.getenv("CHANNEL_USERNAME", "@AetherNeural")
CHANNEL_URL = os.getenv("CHANNEL_URL", "https" + "://" + "t.me/AetherNeural")
BOT_PUBLIC_URL = os.getenv("BOT_PUBLIC_URL", "https://t.me/AetherNeural_bot").strip()
WEBAPP_URL = os.getenv("WEBAPP_URL", "").strip()
WEBAPP_PORT = int(os.getenv("PORT", os.getenv("WEBAPP_PORT", "8080")))

# Документы и поддержка
TERMS_URL = os.getenv("TERMS_URL", "https://telegra.ph/Polzovatelskoe-soglashenie-Oferta-11-15").strip()
PRIVACY_URL = os.getenv("PRIVACY_URL", "https://telegra.ph/Politika-konfidencialnosti-11-15-68").strip()
SUPPORT_USERNAME = os.getenv("SUPPORT_USERNAME", "AetherNeuralhelp").lstrip("@").strip()
SUPPORT_URL = f"https://t.me/{SUPPORT_USERNAME}"

DB_PATH = os.getenv("DB_PATH", "data/users.sqlite3")

FREE_DAILY_LIMIT = 5
PHOTO_COST = 1          # Разбор 1 фото = 1 запрос
VIDEO_COST = 1          # Разбор 1 видео = 1 запрос
MAX_ALBUM_PHOTOS = 10   # Максимум 10 фото в одном альбоме
MAX_HISTORY_MESSAGES = 16
DEFAULT_ENGINE_MODEL = "gpt-6-luna"
WHISPER_MODEL = os.getenv("WHISPER_MODEL", "whisper-1").strip()
USERS_PER_PAGE = 8

DISCOUNT_DELAY_SECONDS = 2 * 3600      # Через 2 часа после первого сообщения
DISCOUNT_DURATION_SECONDS = 36 * 3600  # Скидка действует 36 часов
DISCOUNT_PERCENT = 30                  # Персональная скидка 30%

REF_COMMISSION_PERCENT = 25            # 25% с каждой покупки реферала
MIN_WITHDRAW_RUB = 100.0               # Минимальная сумма вывода 100 ₽
STARS_TO_RUB_RATE = 1.3                # Курс 1 ⭐ = 1.3 ₽ для расчёта партнёрки

MAX_CUSTOM_SUB_DAYS = 60               # Максимум 60 дней при кастомной покупке подписки
MIN_CUSTOM_PACK_REQS = 1               # Минимум 1 запрос (3 ₽ — минималка Platega)
MAX_CUSTOM_PACK_REQS = 500             # Максимум 500 запросов при кастомной покупке пакета
MIN_RUB_AMOUNT = 3                     # Минимальная сумма платежа в Platega (3 ₽)

# Фильтр запрещённого контента
FORBIDDEN_PATTERNS = [
    r"(?:детск\w*|несовершеннолетн\w*|малолетн\w*|лоли|школот\w*|ребен\w*|девочк\w*|мальчик\w*)\s*(?:порн\w*|секс\w*|интим\w*|голы\w*|обнажен\w*|эротик\w*)",
    r"(?:порн\w*|секс\w*|интим\w*|голы\w*|обнажен\w*)\s*(?:с\s+)?(?:дет\w*|несовершеннолетн\w*|малолетн\w*|подростк\w*)",
    r"(?:cp|csam|child\s*porn|underage\s*sex|loli\s*porn)",
    r"(?:как\s+(?:сделать|собрать|изготовить|сварить)|инструкци\w*\s+по\s+изготовлени\w*|рецепт\s+изготовлени\w*)\s*(?:бомб\w*|взрывчат\w*|оружи\w*|огнестрел\w*|пистолет\w*|автомат\w*|гранат\w*|коктейл\w*\s+молотов\w*|тротил\w*|гексоген\w*|порох\w*)",
    r"(?:how\s+to\s+(?:make|build|manufacture))\s+(?:a\s+)?(?:bomb|explosive|gun|firearm|weapon|ricin|meth)",
    r"(?:как\s+(?:сварить|изготовить|синтезировать)|рецепт)\s*(?:мефедрон\w*|амфетамин\w*|героин\w*|наркотик\w*|соль\s+для\s+курени\w*)",
    r"(?:способы\s+(?:суицида|самоубийства)|как\s+покончить\s+с\s+собой)",
]
FORBIDDEN_REGEX = re.compile("|".join(FORBIDDEN_PATTERNS), flags=re.IGNORECASE)


def is_content_forbidden(text: str) -> bool:
    if not text:
        return False
    return bool(FORBIDDEN_REGEX.search(text))


TEXT_FILE_EXTS = {
    ".txt", ".py", ".js", ".ts", ".jsx", ".tsx", ".html", ".htm", ".css",
    ".json", ".csv", ".md", ".xml", ".yaml", ".yml", ".ini", ".cfg", ".conf",
    ".log", ".sql", ".sh", ".bat", ".cpp", ".c", ".h", ".hpp", ".cs", ".java",
    ".kt", ".go", ".rs", ".php", ".rb", ".lua", ".r", ".swift", ".env",
}

FALLBACK_MODELS = [
    "gpt-6-luna",
    "gpt-5.6-luna",
    "gpt-5-mini",
    "gemini-3.5-flash-lite",
    "gemini-3.1-flash-lite",
    "deepseek-v4-flash",
    "claude-haiku-5-5",
]

VIDEO_FALLBACK_MODELS = [
    "gemini-3.5-flash-lite",
    "gemini-3.1-flash-lite",
    "gemini-3.7-flash",
    "gemini-3.1-pro",
    "gpt-5-mini",
    "claude-haiku-5-5",
]

CATEGORIES = {
    "gpt": {
        "title": "🤖 GPT (OpenAI)",
        "models": [
            {"id": "gpt-6-luna", "name": "GPT-6 Luna", "pro": False, "tag": "FREE"},
            {"id": "gpt-5.6-luna", "name": "GPT-5.6 Luna", "pro": False, "tag": "FREE"},
            {"id": "gpt-5-mini", "name": "GPT-5 Mini", "pro": False, "tag": "FREE"},
            {"id": "gpt-5.4-mini", "name": "GPT-5.4 Mini", "pro": True, "tag": "PRO"},
            {"id": "gpt-6.1-terra", "name": "GPT-6.1 Terra", "pro": True, "tag": "PRO"},
            {"id": "gpt-6-sol", "name": "GPT-6 Sol", "pro": True, "tag": "PRO"},
            {"id": "gpt-5.3-codex", "name": "GPT-5.3 Codex", "pro": True, "tag": "PRO"},
            {"id": "gpt-5.6", "name": "GPT-5.6", "pro": True, "tag": "PRO"},
            {"id": "gpt-5.5", "name": "GPT-5.5", "pro": True, "tag": "PRO"},
        ],
    },
    "claude": {
        "title": "🧠 Claude (Anthropic)",
        "models": [
            {"id": "claude-haiku-5-5", "name": "Claude Haiku 5.5", "pro": False, "tag": "FREE"},
            {"id": "claude-haiku-4-5", "name": "Claude Haiku 4.5", "pro": True, "tag": "PRO"},
            {"id": "claude-sonnet-5", "name": "Claude Sonnet 5", "pro": True, "tag": "PRO"},
            {"id": "claude-sonnet-5-5", "name": "Claude Sonnet 5.5", "pro": True, "tag": "PRO"},
            {"id": "claude-opus-5", "name": "Claude Opus 5", "pro": True, "tag": "PRO"},
            {"id": "claude-opus-5-5", "name": "Claude Opus 5.5", "pro": True, "tag": "PRO"},
        ],
    },
    "gemini": {
        "title": "✨ Gemini (Google)",
        "models": [
            {"id": "gemini-3.1-flash-lite", "name": "Gemini 3.1 Flash Lite", "pro": False, "tag": "FREE"},
            {"id": "gemini-3.5-flash-lite", "name": "Gemini 3.5 Flash Lite", "pro": False, "tag": "FREE"},
            {"id": "gemini-3.7-flash", "name": "Gemini 3.7 Flash", "pro": True, "tag": "PRO"},
            {"id": "gemini-3.8-flash", "name": "Gemini 3.8 Flash", "pro": True, "tag": "PRO"},
            {"id": "gemini-3.1-pro", "name": "Gemini 3.1 Pro", "pro": True, "tag": "PRO"},
            {"id": "gemini-4-argon", "name": "Gemini 4 Argon", "pro": True, "tag": "PRO"},
            {"id": "gemini-4-carbon", "name": "Gemini 4 Carbon", "pro": True, "tag": "PRO"},
            {"id": "gemini-4-neon", "name": "Gemini 4 Neon", "pro": True, "tag": "PRO"},
        ],
    },
    "deepseek": {
        "title": "🐋 DeepSeek",
        "models": [
            {"id": "deepseek-v4-flash", "name": "DeepSeek V4 Flash", "pro": False, "tag": "FREE"},
            {"id": "deepseek-v4-pro", "name": "DeepSeek V4 Pro", "pro": True, "tag": "PRO"},
        ],
    },
    "grok": {
        "title": "⚡ Grok (xAI)",
        "models": [
            {"id": "grok-4.5", "name": "Grok 4.5", "pro": True, "tag": "PRO"},
            {"id": "grok-4.6", "name": "Grok 4.6", "pro": True, "tag": "PRO"},
        ],
    },
}

ALL_MODELS_MAP = {}
for cat_data in CATEGORIES.values():
    for m in cat_data["models"]:
        if m["id"] not in ALL_MODELS_MAP:
            ALL_MODELS_MAP[m["id"]] = m

PRODUCTS = {
    "sub_trial": {"type": "sub", "title": "Пробный 1 день", "stars": 29, "rub": 39, "value": 1},
    "sub_standard": {"type": "sub", "title": "Стандарт 7 дней", "stars": 115, "rub": 149, "value": 7},
    "sub_premium": {"type": "sub", "title": "Премиум 30 дней", "stars": 269, "rub": 349, "value": 30},
    "pack_30": {"type": "pack", "title": "Пакет +30 запросов", "stars": 79, "rub": 99, "value": 30},
    "pack_100": {"type": "pack", "title": "Пакет +100 запросов", "stars": 199, "rub": 259, "value": 100},
    "pack_300": {"type": "pack", "title": "Пакет +300 запросов", "stars": 449, "rub": 589, "value": 300},
}

SYSTEM_PROMPT = (
    "Отвечай четко, по делу и на языке пользователя. "
    "Когда пользователь просит создать или написать код, просто выдавай готовый, чистый и рабочий код в блоках кода (```язык ... ```) с минимальным пояснением. "
    "Не пытайся сам собирать, компилировать, запускать проект, создавать архивы или рендерить превью — просто отдай сам код текстом. "
    "Вне блоков кода не используй лишние звездочки (** или *) и решетки (###). "
    "Никогда не используй LaTeX-разметку (\\frac, \\cdot, \\times, \\[,\\], $$, \\sqrt и обратные слэши \\). "
    "Все математические и химические формулы пиши обычными читаемыми символами: *, /, ^, =, √, индексы цифрами (например, H2O, x^2, (a + b) / 2). "
    "Строго отказывайся выполнять запросы, связанные с сексуальным контентом с участием несовершеннолетних, изготовлением оружия, взрывчатки, наркотиков или причинением вреда."
)

ai_client = AsyncOpenAI(
    api_key=UNLOCK_API_KEY,
    base_url=UNLOCK_BASE_URL,
    timeout=90.0,
    max_retries=0,
)
router = Router()

USER_INPUT_STATE: dict[int, str] = {}
PROMO_DRAFT: dict[str, any] = {}
BROADCAST_DRAFT: dict[str, int] = {}
GLOBAL_DISCOUNT_DRAFT: dict[str, any] = {}
MEDIA_GROUP_BUFFER: dict[str, list[Message]] = {}
USER_QUOTA_LOCKS: dict[int, asyncio.Lock] = {}
TX_FULFILL_LOCKS: dict[str, asyncio.Lock] = {}


def get_user_lock(user_id: int) -> asyncio.Lock:
    if user_id not in USER_QUOTA_LOCKS:
        USER_QUOTA_LOCKS[user_id] = asyncio.Lock()
    return USER_QUOTA_LOCKS[user_id]


def get_tx_lock(tx_id: str) -> asyncio.Lock:
    if tx_id not in TX_FULFILL_LOCKS:
        TX_FULFILL_LOCKS[tx_id] = asyncio.Lock()
    return TX_FULFILL_LOCKS[tx_id]


# ================= РАСЧЁТ ЦЕН (ГОТОВЫХ И КАСТОМНЫХ) СО СКИДКОЙ =================
async def get_global_discount() -> dict:
    """Возвращает {'active': bool, 'percent': int, 'until': float} для глобальной акции."""
    raw_pct = await get_setting("global_discount_percent", "0")
    raw_until = await get_setting("global_discount_until", "0")
    try:
        pct = int(raw_pct)
    except Exception:
        pct = 0
    try:
        until = float(raw_until)
    except Exception:
        until = 0.0

    if pct > 0 and until > time.time():
        return {"active": True, "percent": pct, "until": until}
    return {"active": False, "percent": 0, "until": 0.0}


async def get_effective_discount(user: dict) -> dict:
    """Возвращает максимальную активную скидку пользователя (глобальную или персональную):
    {'active': bool, 'percent': int, 'until': float, 'is_global': bool}."""
    now = time.time()
    pers_until = float(user.get("discount_until") or 0)
    pers_active = pers_until > now
    pers_pct = DISCOUNT_PERCENT if pers_active else 0

    g_disc = await get_global_discount()
    glob_active = g_disc["active"]
    glob_pct = g_disc["percent"] if glob_active else 0
    glob_until = g_disc["until"] if glob_active else 0.0

    if not pers_active and not glob_active:
        return {"active": False, "percent": 0, "until": 0.0, "is_global": False}

    if glob_pct >= pers_pct and glob_active:
        return {"active": True, "percent": glob_pct, "until": glob_until, "is_global": True}
    return {"active": True, "percent": pers_pct, "until": pers_until, "is_global": False}


def has_active_discount(user: dict) -> bool:
    return (user.get("discount_until") or 0) > time.time()


def apply_discount_rub(base_rub: int, discount_percent: int) -> int:
    # На суммы меньше 5 ₽ скидка не распространяется; минималка для рублёвых платежей — 3 ₽
    if base_rub < 5:
        return max(MIN_RUB_AMOUNT, base_rub)
    if discount_percent > 0:
        return max(MIN_RUB_AMOUNT, round(base_rub * (100 - discount_percent) / 100))
    return max(MIN_RUB_AMOUNT, base_rub)


def apply_discount_stars(base_stars: int, discount_percent: int) -> int:
    if base_stars < 5:
        return max(1, base_stars)
    if discount_percent > 0:
        return max(1, round(base_stars * (100 - discount_percent) / 100))
    return max(1, base_stars)


def get_product_price(product: dict, discount_percent: int | bool) -> int:
    pct = (DISCOUNT_PERCENT if discount_percent else 0) if isinstance(discount_percent, bool) else int(discount_percent)
    return apply_discount_stars(product["stars"], pct)


def get_product_rub_price(product: dict, discount_percent: int | bool) -> int:
    pct = (DISCOUNT_PERCENT if discount_percent else 0) if isinstance(discount_percent, bool) else int(discount_percent)
    return apply_discount_rub(product["rub"], pct)


def calc_custom_sub_price(days: int, discount_percent: int | bool) -> tuple[int, int]:
    """Возвращает (rub_price, stars_price) для кастомного срока подписки от 1 до 60 дней."""
    pct = (DISCOUNT_PERCENT if discount_percent else 0) if isinstance(discount_percent, bool) else int(discount_percent)
    if days == 1:
        base_rub, base_stars = 39, 29
    elif days == 7:
        base_rub, base_stars = 149, 115
    elif days == 30:
        base_rub, base_stars = 349, 269
    elif days < 7:
        base_rub = days * 32
        base_stars = days * 25
    elif days < 30:
        base_rub = days * 18
        base_stars = days * 14
    else:
        base_rub = days * 12
        base_stars = days * 9

    return apply_discount_rub(base_rub, pct), apply_discount_stars(base_stars, pct)


def calc_custom_pack_price(reqs: int, discount_percent: int | bool) -> tuple[int, int]:
    """Возвращает (rub_price, stars_price) для кастомного пакета от 1 до 500 запросов (1 запрос = 3 ₽ без скидки)."""
    pct = (DISCOUNT_PERCENT if discount_percent else 0) if isinstance(discount_percent, bool) else int(discount_percent)
    if reqs == 1:
        base_rub, base_stars = 3, 3
    elif reqs == 30:
        base_rub, base_stars = 99, 79
    elif reqs == 100:
        base_rub, base_stars = 259, 199
    elif reqs == 300:
        base_rub, base_stars = 589, 449
    elif reqs < 100:
        base_rub = max(MIN_RUB_AMOUNT, round(reqs * 3.3))
        base_stars = max(2, round(reqs * 2.6))
    elif reqs < 300:
        base_rub = round(reqs * 2.5)
        base_stars = round(reqs * 2.0)
    else:
        base_rub = round(reqs * 1.9)
        base_stars = round(reqs * 1.5)

    return apply_discount_rub(base_rub, pct), apply_discount_stars(base_stars, pct)


def resolve_order_details(order_code: str, discount_percent: int | bool) -> dict | None:
    pct = (DISCOUNT_PERCENT if discount_percent else 0) if isinstance(discount_percent, bool) else int(discount_percent)
    if order_code.startswith("prod:"):
        prod_key = order_code.split(":", 1)[1]
        p = PRODUCTS.get(prod_key)
        if not p:
            return None
        return {
            "order_code": order_code,
            "type": p["type"],
            "title": p["title"],
            "value": p["value"],
            "rub": get_product_rub_price(p, pct),
            "stars": get_product_price(p, pct),
            "back_cb": "shop:subs" if p["type"] == "sub" else "shop:packs",
        }
    elif order_code.startswith("csub:"):
        val_s = order_code.split(":", 1)[1]
        if not val_s.isdigit():
            return None
        days = int(val_s)
        if not (1 <= days <= MAX_CUSTOM_SUB_DAYS):
            return None
        rub_p, stars_p = calc_custom_sub_price(days, pct)
        return {
            "order_code": order_code,
            "type": "sub",
            "title": f"Подписка на {days} дн.",
            "value": days,
            "rub": rub_p,
            "stars": stars_p,
            "back_cb": "shop:subs",
        }
    elif order_code.startswith("cpack:"):
        val_s = order_code.split(":", 1)[1]
        if not val_s.isdigit():
            return None
        reqs = int(val_s)
        if not (MIN_CUSTOM_PACK_REQS <= reqs <= MAX_CUSTOM_PACK_REQS):
            return None
        rub_p, stars_p = calc_custom_pack_price(reqs, pct)
        return {
            "order_code": order_code,
            "type": "pack",
            "title": f"Пакет +{reqs} запр.",
            "value": reqs,
            "rub": rub_p,
            "stars": stars_p,
            "back_cb": "shop:packs",
        }
    return None


# ================= ОЧИСТКА И ФОРМАТИРОВАНИЕ ОТВЕТОВ НЕЙРОСЕТИ =================
def format_ai_response(raw_text: str) -> tuple[str, str]:
    text = raw_text.replace("\r\n", "\n")

    text = re.sub(r"\\\[|\\\]|\\\(|\\\)", "", text)
    text = text.replace("$$", "")
    text = re.sub(r"\\frac\{([^{}]+)\}\{([^{}]+)\}", r"(\1 / \2)", text)
    text = re.sub(r"\\sqrt\{([^{}]+)\}", r"√(\1)", text)
    text = (
        text.replace(r"\cdot", "·")
        .replace(r"\times", "×")
        .replace(r"\approx", "≈")
        .replace(r"\neq", "≠")
        .replace(r"\leq", "≤")
        .replace(r"\geq", "≥")
    )
    text = re.sub(r"\\[a-zA-Z]+\{([^{}]*)\}", r"\1", text)
    text = re.sub(r"\\[a-zA-Z]+", "", text)
    text = text.replace("\\", "")

    text = re.sub(r"^#{1,6}\s*(.+)$", r"\1", text, flags=re.MULTILINE)
    text = re.sub(r"^\s*[-*_]{3,}\s*$", "", text, flags=re.MULTILINE)
    text = re.sub(r"^\s*[\*\-]\s+", "• ", text, flags=re.MULTILINE)

    text = text.replace("**", "")

    plain = text.replace("__", "").replace("```", "").replace("`", "")

    escaped = html.escape(text)
    escaped = re.sub(r"```(?:\w+)?\n?(.*?)```", r"<pre><code>\1</code></pre>", escaped, flags=re.DOTALL)
    escaped = re.sub(r"`([^`\n]+)`", r"<code>\1</code>", escaped)

    return escaped.strip(), plain.strip()


async def send_formatted_answer(message: Message, raw_text: str):
    html_text, plain_text = format_ai_response(raw_text)
    for i in range(0, len(html_text), 3800):
        chunk_html = html_text[i : i + 3800]
        chunk_plain = plain_text[i : i + 3800]
        try:
            await message.answer(chunk_html, parse_mode=ParseMode.HTML)
        except Exception:
            await message.answer(chunk_plain)


# ================= БАЗА ДАННЫХ =================
async def init_db():
    db_dir = os.path.dirname(os.path.abspath(DB_PATH))
    if db_dir:
        os.makedirs(db_dir, exist_ok=True)

    if os.path.exists(DB_PATH) and os.path.getsize(DB_PATH) > 0:
        try:
            shutil.copy2(DB_PATH, f"{DB_PATH}.bak")
        except Exception:
            pass

    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("""
            CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY,
                full_name TEXT DEFAULT 'Пользователь',
                username TEXT DEFAULT '',
                selected_model TEXT DEFAULT 'gpt-6-luna',
                used_today INTEGER DEFAULT 0,
                last_reset TEXT,
                pro_until REAL DEFAULT 0,
                bonus_limit INTEGER DEFAULT 0,
                extra_requests INTEGER DEFAULT 0,
                referred_by INTEGER DEFAULT 0,
                ref_rewarded INTEGER DEFAULT 0,
                ref_balance REAL DEFAULT 0,
                ref_total_earned REAL DEFAULT 0,
                total_requests INTEGER DEFAULT 0,
                visited_models INTEGER DEFAULT 0,
                discount_until REAL DEFAULT 0,
                discount_offered INTEGER DEFAULT 0,
                joined_at REAL DEFAULT 0,
                first_seen_at REAL DEFAULT 0
            )
        """)

        new_cols = [
            ("full_name", "TEXT DEFAULT 'Пользователь'"),
            ("username", "TEXT DEFAULT ''"),
            ("extra_requests", "INTEGER DEFAULT 0"),
            ("ref_rewarded", "INTEGER DEFAULT 0"),
            ("ref_balance", "REAL DEFAULT 0"),
            ("ref_total_earned", "REAL DEFAULT 0"),
            ("total_requests", "INTEGER DEFAULT 0"),
            ("visited_models", "INTEGER DEFAULT 0"),
            ("discount_until", "REAL DEFAULT 0"),
            ("discount_offered", "INTEGER DEFAULT 0"),
            ("joined_at", "REAL DEFAULT 0"),
            ("first_seen_at", "REAL DEFAULT 0"),
        ]
        for col_name, col_def in new_cols:
            try:
                await db.execute(f"ALTER TABLE users ADD COLUMN {col_name} {col_def}")
            except Exception:
                pass

        await db.execute(
            "UPDATE users SET first_seen_at = COALESCE(NULLIF(joined_at, 0), ?) WHERE first_seen_at = 0 OR first_seen_at IS NULL",
            (time.time(),),
        )
        await db.execute(
            "UPDATE users SET used_today = (? + bonus_limit) WHERE used_today > (? + bonus_limit)",
            (FREE_DAILY_LIMIT, FREE_DAILY_LIMIT),
        )

        await db.execute("""
            CREATE TABLE IF NOT EXISTS payments (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                product_key TEXT,
                title TEXT,
                stars INTEGER,
                rub_amount REAL DEFAULT 0,
                method TEXT DEFAULT 'stars',
                paid_at REAL
            )
        """)
        for col_name, col_def in [("rub_amount", "REAL DEFAULT 0"), ("method", "TEXT DEFAULT 'stars'")]:
            try:
                await db.execute(f"ALTER TABLE payments ADD COLUMN {col_name} {col_def}")
            except Exception:
                pass

        await db.execute("""
            CREATE TABLE IF NOT EXISTS platega_transactions (
                transaction_id TEXT PRIMARY KEY,
                user_id INTEGER,
                order_code TEXT,
                title TEXT,
                item_type TEXT,
                item_value INTEGER,
                rub_amount REAL,
                redirect_url TEXT,
                status TEXT DEFAULT 'PENDING',
                created_at REAL,
                confirmed_at REAL DEFAULT 0
            )
        """)

        await db.execute("""
            CREATE TABLE IF NOT EXISTS withdrawals (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                amount REAL,
                requisites TEXT,
                status TEXT DEFAULT 'pending',
                created_at REAL
            )
        """)
        await db.execute("""
            CREATE TABLE IF NOT EXISTS chat_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                role TEXT,
                content TEXT
            )
        """)
        await db.execute("""
            CREATE TABLE IF NOT EXISTS request_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                req_type TEXT,
                user_query TEXT,
                bot_reply TEXT,
                model_used TEXT,
                created_at REAL
            )
        """)
        await db.execute("""
            CREATE TABLE IF NOT EXISTS bot_settings (
                key TEXT PRIMARY KEY,
                value TEXT
            )
        """)
        await db.execute("""
            CREATE TABLE IF NOT EXISTS promocodes (
                code TEXT PRIMARY KEY,
                reward_type TEXT,
                amount INTEGER,
                max_uses INTEGER,
                used_count INTEGER DEFAULT 0
            )
        """)
        await db.execute("""
            CREATE TABLE IF NOT EXISTS promo_uses (
                user_id INTEGER,
                code TEXT,
                PRIMARY KEY (user_id, code)
            )
        """)
        await db.execute("""
            CREATE TABLE IF NOT EXISTS web_auth_codes (
                code TEXT PRIMARY KEY,
                user_id INTEGER,
                expires_at REAL
            )
        """)
        await db.execute("""
            CREATE TABLE IF NOT EXISTS web_sessions (
                token TEXT PRIMARY KEY,
                user_id INTEGER,
                created_at REAL,
                expires_at REAL
            )
        """)
        await db.execute("""
            CREATE TABLE IF NOT EXISTS user_sessions (
                user_id INTEGER PRIMARY KEY,
                sessions_json TEXT DEFAULT '[]',
                updated_at REAL DEFAULT 0
            )
        """)
        await db.execute(
            "INSERT OR IGNORE INTO bot_settings (key, value) VALUES ('engine_model', ?)",
            (DEFAULT_ENGINE_MODEL,),
        )
        await db.commit()


async def send_db_backup(bot: Bot, reason: str = "Ручной бэкап"):
    if os.path.exists(DB_PATH) and os.path.getsize(DB_PATH) > 0:
        try:
            async with aiosqlite.connect(DB_PATH) as db:
                async with db.execute("SELECT COUNT(*) FROM users") as cur:
                    total_u = (await cur.fetchone())[0]
                async with db.execute("SELECT COUNT(*) FROM users WHERE pro_until > ?", (time.time(),)) as cur:
                    pro_u = (await cur.fetchone())[0]

            file = FSInputFile(DB_PATH, filename=os.path.basename(DB_PATH))
            await bot.send_document(
                ADMIN_ID,
                document=file,
                caption=(
                    f"💾 <b>{reason} базы данных</b> ({datetime.now().strftime('%d.%m.%Y %H:%M')})\n"
                    f"👥 Пользователей: <b>{total_u}</b> | 👑 PRO: <b>{pro_u}</b>"
                ),
                parse_mode=ParseMode.HTML,
            )
        except Exception as e:
            print(f"Ошибка отправки бэкапа: {e}")


async def get_setting(key: str, default: str = "") -> str:
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute("SELECT value FROM bot_settings WHERE key = ?", (key,)) as cur:
            row = await cur.fetchone()
            return row[0] if row else default


async def set_setting(key: str, value: str):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("INSERT OR REPLACE INTO bot_settings (key, value) VALUES (?, ?)", (key, value))
        await db.commit()


async def get_engine_model() -> str:
    return await get_setting("engine_model", DEFAULT_ENGINE_MODEL)


async def set_engine_model(model_id: str):
    await set_setting("engine_model", model_id)


async def add_history(user_id: int, role: str, content: str):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "INSERT INTO chat_history (user_id, role, content) VALUES (?, ?, ?)",
            (user_id, role, content),
        )
        await db.execute(
            """
            DELETE FROM chat_history
            WHERE user_id = ? AND id NOT IN (
                SELECT id FROM chat_history WHERE user_id = ? ORDER BY id DESC LIMIT ?
            )
            """,
            (user_id, user_id, MAX_HISTORY_MESSAGES),
        )
        await db.commit()


async def log_user_request(user_id: int, req_type: str, user_query: str, bot_reply: str, model_used: str = ""):
    """Сохраняет постоянный журнал всех запросов пользователей (не стирается при /clear) для аудита в админке."""
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            """
            INSERT INTO request_logs (user_id, req_type, user_query, bot_reply, model_used, created_at)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (user_id, req_type, (user_query or "")[:2000], (bot_reply or "")[:2000], model_used[:60], time.time()),
        )
        # Храним последние 100 записей на каждого пользователя, чтобы база не раздувалась
        await db.execute(
            """
            DELETE FROM request_logs
            WHERE user_id = ? AND id NOT IN (
                SELECT id FROM request_logs WHERE user_id = ? ORDER BY id DESC LIMIT 100
            )
            """,
            (user_id, user_id),
        )
        await db.commit()


async def get_history(user_id: int) -> list[dict]:
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute(
            "SELECT role, content FROM chat_history WHERE user_id = ? ORDER BY id ASC",
            (user_id,),
        ) as cur:
            rows = await cur.fetchall()
            return [{"role": row["role"], "content": row["content"]} for row in rows]


async def clear_history(user_id: int):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("DELETE FROM chat_history WHERE user_id = ?", (user_id,))
        await db.commit()


async def get_user(user_id: int, ref_id: int = 0, full_name: str = "", username: str = "") -> dict:
    today_str = str(date.today())
    now = time.time()
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute("SELECT * FROM users WHERE user_id = ?", (user_id,)) as cur:
            row = await cur.fetchone()

        if not row:
            valid_ref = ref_id if (ref_id and ref_id != user_id) else 0
            clean_name = (full_name or "Пользователь")[:40]
            clean_uname = (username or "")[:40]
            await db.execute(
                """
                INSERT OR IGNORE INTO users (user_id, full_name, username, last_reset, referred_by, ref_rewarded, joined_at, first_seen_at)
                VALUES (?, ?, ?, ?, ?, 0, ?, ?)
                """,
                (user_id, clean_name, clean_uname, today_str, valid_ref, now, now),
            )
            await db.commit()
            async with db.execute("SELECT * FROM users WHERE user_id = ?", (user_id,)) as cur2:
                row = await cur2.fetchone()

        user = dict(row)
        updates = []
        params = []
        if user["last_reset"] != today_str:
            updates.append("used_today = 0, last_reset = ?")
            params.append(today_str)
            user["used_today"] = 0
            user["last_reset"] = today_str
        if not user.get("first_seen_at"):
            updates.append("first_seen_at = ?")
            params.append(now)
            user["first_seen_at"] = now
        if full_name and user.get("full_name") != full_name[:40]:
            updates.append("full_name = ?")
            params.append(full_name[:40])
            user["full_name"] = full_name[:40]
        if username is not None and username != "" and user.get("username") != username[:40]:
            updates.append("username = ?")
            params.append(username[:40])
            user["username"] = username[:40]

        if updates:
            params.append(user_id)
            await db.execute(f"UPDATE users SET {', '.join(updates)} WHERE user_id = ?", tuple(params))
            await db.commit()

        return user


async def try_consume_quota(user_id: int, pro_active: bool, count: int = 1) -> dict | None:
    if pro_active:
        return {"pro": True, "daily": 0, "extra": 0}

    lock = get_user_lock(user_id)
    async with lock:
        user = await get_user(user_id)
        total_daily_limit = FREE_DAILY_LIMIT + (user.get("bonus_limit") or 0)
        used_today = user.get("used_today") or 0
        extra_left = user.get("extra_requests") or 0

        daily_left = max(0, total_daily_limit - used_today)
        if daily_left + extra_left < count:
            return None

        take_daily = min(daily_left, count)
        take_extra = count - take_daily

        async with aiosqlite.connect(DB_PATH) as db:
            cur = await db.execute(
                """
                UPDATE users
                SET used_today = used_today + ?,
                    extra_requests = extra_requests - ?
                WHERE user_id = ?
                  AND (used_today + ?) <= (? + bonus_limit)
                  AND extra_requests >= ?
                """,
                (take_daily, take_extra, user_id, take_daily, FREE_DAILY_LIMIT, take_extra),
            )
            if cur.rowcount == 0:
                return None
            await db.commit()

        return {"pro": False, "daily": take_daily, "extra": take_extra}


async def refund_quota(user_id: int, receipt: dict | None):
    if not receipt or receipt.get("pro"):
        return
    daily_back = receipt.get("daily", 0)
    extra_back = receipt.get("extra", 0)
    if daily_back <= 0 and extra_back <= 0:
        return

    lock = get_user_lock(user_id)
    async with lock:
        async with aiosqlite.connect(DB_PATH) as db:
            await db.execute(
                """
                UPDATE users
                SET used_today = MAX(0, used_today - ?),
                    extra_requests = extra_requests + ?
                WHERE user_id = ?
                """,
                (daily_back, extra_back, user_id),
            )
            await db.commit()


async def reward_referrer_if_needed(user_id: int, bot: Bot):
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute("SELECT referred_by, ref_rewarded FROM users WHERE user_id = ?", (user_id,)) as cur:
            row = await cur.fetchone()
        if not row:
            return
        ref_id, rewarded = row["referred_by"], row["ref_rewarded"]
        if ref_id and not rewarded and ref_id != user_id:
            await db.execute("UPDATE users SET ref_rewarded = 1 WHERE user_id = ?", (user_id,))
            await db.execute("UPDATE users SET bonus_limit = bonus_limit + 2 WHERE user_id = ?", (ref_id,))
            await db.commit()
            try:
                await bot.send_message(
                    ref_id,
                    "🎉 По твоей ссылке подписался на канал новый друг!\n"
                    "• Начислено <b>+2 запроса в день</b>\n"
                    f"• Ты будешь получать <b>{REF_COMMISSION_PERCENT}%</b> со всех его покупок в боте!",
                    parse_mode=ParseMode.HTML,
                )
            except Exception:
                pass


async def credit_referral_commission(buyer_id: int, purchase_rub_amount: float, item_title: str, bot: Bot):
    if purchase_rub_amount <= 0:
        return
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute("SELECT referred_by FROM users WHERE user_id = ?", (buyer_id,)) as cur:
            row = await cur.fetchone()
        if not row or not row["referred_by"] or row["referred_by"] == buyer_id:
            return

        ref_id = row["referred_by"]
        reward_rub = round(purchase_rub_amount * (REF_COMMISSION_PERCENT / 100.0), 2)
        if reward_rub <= 0:
            return

        await db.execute(
            """
            UPDATE users
            SET ref_balance = COALESCE(ref_balance, 0) + ?,
                ref_total_earned = COALESCE(ref_total_earned, 0) + ?
            WHERE user_id = ?
            """,
            (reward_rub, reward_rub, ref_id),
        )
        await db.commit()

        async with db.execute("SELECT ref_balance FROM users WHERE user_id = ?", (ref_id,)) as cur2:
            r2 = await cur2.fetchone()
            new_bal = (r2["ref_balance"] if r2 else reward_rub) or 0.0

        try:
            await bot.send_message(
                ref_id,
                f"💸 <b>Партнёрское начисление +{reward_rub:.2f} ₽!</b>\n\n"
                f"Твой реферал оплатил тариф <b>«{html.escape(item_title)}»</b>.\n"
                f"💰 Твой реферальный баланс: <b>{new_bal:.2f} ₽</b> (вывод от {int(MIN_WITHDRAW_RUB)} ₽ в разделе /ref).",
                parse_mode=ParseMode.HTML,
            )
        except Exception:
            pass


# ================= PLATEGA API (СОЗДАНИЕ ПЛАТЕЖА И АВТОПРОВЕРКА СТАТУСА) =================
async def platega_create_transaction(amount_rub: int, description: str, payload_str: str) -> dict:
    if not PLATEGA_MERCHANT_ID or not PLATEGA_SECRET:
        raise RuntimeError("Не заданы PLATEGA_MERCHANT_ID или PLATEGA_SECRET в настройках сервера")

    url = f"{PLATEGA_BASE_URL}/transaction/process"
    headers = {
        "X-MerchantId": PLATEGA_MERCHANT_ID,
        "X-Secret": PLATEGA_SECRET,
        "Content-Type": "application/json",
    }
    body = {
        "paymentMethod": PLATEGA_SBP_METHOD,
        "paymentDetails": {
            "amount": float(amount_rub),
            "currency": "RUB",
        },
        "description": description[:120],
        "return": BOT_PUBLIC_URL,
        "failedUrl": BOT_PUBLIC_URL,
        "payload": payload_str[:120],
    }

    async with aiohttp.ClientSession() as session:
        async with session.post(url, json=body, headers=headers, timeout=25) as resp:
            raw_text = await resp.text()
            if resp.status >= 400:
                raise RuntimeError(f"Platega HTTP {resp.status}: {raw_text[:200]}")
            data = await resp.json(content_type=None)

    tx_id = str(data.get("transactionId") or data.get("id") or "").strip()
    redirect_url = str(data.get("redirect") or data.get("url") or data.get("paymentUrl") or "").strip()
    if not tx_id or not redirect_url:
        raise RuntimeError(f"Некорректный ответ Platega: {raw_text[:200]}")

    return {"transaction_id": tx_id, "redirect": redirect_url}


async def platega_fetch_status(transaction_id: str) -> str:
    if not PLATEGA_MERCHANT_ID or not PLATEGA_SECRET:
        return "ERROR"

    url = f"{PLATEGA_BASE_URL}/transaction/{transaction_id}"
    headers = {
        "X-MerchantId": PLATEGA_MERCHANT_ID,
        "X-Secret": PLATEGA_SECRET,
    }
    async with aiohttp.ClientSession() as session:
        async with session.get(url, headers=headers, timeout=20) as resp:
            if resp.status >= 400:
                return "ERROR"
            data = await resp.json(content_type=None)
            return str(data.get("status") or "").upper().strip()


async def fulfill_platega_transaction(tx_id: str, bot: Bot) -> bool:
    """Атомарно выдаёт товар при подтверждении оплаты Platega (защита от повторного начисления)."""
    lock = get_tx_lock(tx_id)
    async with lock:
        async with aiosqlite.connect(DB_PATH) as db:
            db.row_factory = aiosqlite.Row
            async with db.execute("SELECT * FROM platega_transactions WHERE transaction_id = ?", (tx_id,)) as cur:
                tx = await cur.fetchone()

            if not tx or tx["status"] == "CONFIRMED":
                return False

            user_id = tx["user_id"]
            item_type = tx["item_type"]
            item_value = tx["item_value"]
            title = tx["title"]
            rub_amount = float(tx["rub_amount"] or 0)
            order_code = tx["order_code"]

            await db.execute(
                "UPDATE platega_transactions SET status = 'CONFIRMED', confirmed_at = ? WHERE transaction_id = ?",
                (time.time(), tx_id),
            )
            await db.execute(
                "INSERT INTO payments (user_id, product_key, title, stars, rub_amount, method, paid_at) VALUES (?, ?, ?, 0, ?, 'sbp', ?)",
                (user_id, order_code, title, rub_amount, time.time()),
            )

            user = await get_user(user_id)
            if item_type == "sub":
                base_time = max(time.time(), user["pro_until"])
                new_pro_until = base_time + item_value * 86400
                exp_date = datetime.fromtimestamp(new_pro_until).strftime("%d.%m.%Y %H:%M")
                await db.execute("UPDATE users SET pro_until = ? WHERE user_id = ?", (new_pro_until, user_id))
                await db.commit()

                try:
                    await bot.send_message(
                        user_id,
                        f"🎉 <b>Оплата через СБП прошла успешно!</b>\n"
                        f"Тариф <b>«{html.escape(title)}»</b> активен до <b>{exp_date}</b>.\n"
                        f"Все модели разблокированы в /menu.",
                        parse_mode=ParseMode.HTML,
                    )
                except Exception:
                    pass
            else:
                await db.execute(
                    "UPDATE users SET extra_requests = extra_requests + ? WHERE user_id = ?",
                    (item_value, user_id),
                )
                await db.commit()

                try:
                    await bot.send_message(
                        user_id,
                        f"🎉 <b>Оплата через СБП прошла успешно!</b>\n"
                        f"На твой баланс зачислен <b>пакет на +{item_value} запросов</b>.\n"
                        f"Проверить остаток можно в /profile.",
                        parse_mode=ParseMode.HTML,
                    )
                except Exception:
                    pass

        await credit_referral_commission(user_id, rub_amount, title, bot)
        try:
            await bot.send_message(
                ADMIN_ID,
                f"💰 <b>Новая оплата СБП (Platega)!</b>\n"
                f"👤 Пользователь: <code>{user_id}</code>\n"
                f"📦 Тариф: <b>{html.escape(title)}</b>\n"
                f"💵 Сумма: <b>{rub_amount:.0f} ₽</b>",
                parse_mode=ParseMode.HTML,
            )
        except Exception:
            pass
        return True


async def platega_status_watcher(bot: Bot):
    """Фоновая автопроверка ожидающих платежей Platega каждые 10 секунд."""
    while True:
        try:
            if PLATEGA_MERCHANT_ID and PLATEGA_SECRET:
                now = time.time()
                async with aiosqlite.connect(DB_PATH) as db:
                    db.row_factory = aiosqlite.Row
                    # Проверяем транзакции не старше 45 минут
                    async with db.execute(
                        "SELECT transaction_id, created_at FROM platega_transactions WHERE status = 'PENDING' AND created_at > ?",
                        (now - 2700,),
                    ) as cur:
                        pending_rows = await cur.fetchall()

                for row in pending_rows:
                    tx_id = row["transaction_id"]
                    try:
                        st = await platega_fetch_status(tx_id)
                        if st == "CONFIRMED":
                            await fulfill_platega_transaction(tx_id, bot)
                        elif st in ("CANCELED", "CANCELLED", "EXPIRED", "FAILED"):
                            async with aiosqlite.connect(DB_PATH) as db:
                                await db.execute(
                                    "UPDATE platega_transactions SET status = ? WHERE transaction_id = ?",
                                    (st, tx_id),
                                )
                                await db.commit()
                    except Exception:
                        pass
                    await asyncio.sleep(0.25)
        except Exception:
            pass
        await asyncio.sleep(10)


# ================= ФОНОВЫЙ ПЛАНИРОВЩИК: СКИДКА 30% НА 36 ЧАСОВ ЧЕРЕЗ 2 ЧАСА =================
async def delayed_discount_watcher(bot: Bot):
    while True:
        try:
            now = time.time()
            cutoff = now - DISCOUNT_DELAY_SECONDS

            async with aiosqlite.connect(DB_PATH) as db:
                db.row_factory = aiosqlite.Row
                async with db.execute(
                    """
                    SELECT user_id FROM users
                    WHERE discount_offered = 0
                      AND first_seen_at > 0
                      AND first_seen_at <= ?
                      AND pro_until <= ?
                      AND user_id != ?
                    """,
                    (cutoff, now, ADMIN_ID),
                ) as cur:
                    eligible_users = await cur.fetchall()

                for row in eligible_users:
                    uid = row["user_id"]
                    disc_until = now + DISCOUNT_DURATION_SECONDS
                    await db.execute(
                        "UPDATE users SET discount_until = ?, discount_offered = 1 WHERE user_id = ?",
                        (disc_until, uid),
                    )
                    await db.commit()

                    offer_text = (
                        f"🔥 <b>ПЕРСОНАЛЬНАЯ СКИДКА {DISCOUNT_PERCENT}% НА 36 ЧАСОВ УЖЕ АКТИВНА!</b>\n\n"
                        f"Мы снизили цены на <b>{DISCOUNT_PERCENT}%</b> на все подписки и пакеты запросов (от 5 ₽) специально для тебя на ближайшие <b>36 часов</b>:\n\n"
                        "👑 <b>Подписки (безлимит на все PRO-модели):</b>\n"
                        f"• Пробный 1 день: <s>{PRODUCTS['sub_trial']['rub']} ₽</s> → <b>{get_product_rub_price(PRODUCTS['sub_trial'], True)} ₽</b> ({get_product_price(PRODUCTS['sub_trial'], True)} ⭐)\n"
                        f"• Стандарт 7 дней: <s>{PRODUCTS['sub_standard']['rub']} ₽</s> → <b>{get_product_rub_price(PRODUCTS['sub_standard'], True)} ₽</b> ({get_product_price(PRODUCTS['sub_standard'], True)} ⭐)\n"
                        f"• Премиум 30 дней: <s>{PRODUCTS['sub_premium']['rub']} ₽</s> → <b>{get_product_rub_price(PRODUCTS['sub_premium'], True)} ₽</b> ({get_product_price(PRODUCTS['sub_premium'], True)} ⭐)\n\n"
                        "⚡ <b>Пакеты запросов (не сгорают):</b>\n"
                        f"• +30 запросов: <s>99 ₽</s> → <b>{get_product_rub_price(PRODUCTS['pack_30'], True)} ₽</b> ({get_product_price(PRODUCTS['pack_30'], True)} ⭐)\n"
                        f"• +100 запросов: <s>259 ₽</s> → <b>{get_product_rub_price(PRODUCTS['pack_100'], True)} ₽</b> ({get_product_price(PRODUCTS['pack_100'], True)} ⭐)\n"
                        f"• +300 запросов: <s>589 ₽</s> → <b>{get_product_rub_price(PRODUCTS['pack_300'], True)} ₽</b> ({get_product_price(PRODUCTS['pack_300'], True)} ⭐)\n\n"
                        "👇 Выбери раздел в магазине прямо сейчас, пока действует скидка:"
                    )
                    try:
                        await bot.send_message(
                            uid,
                            offer_text,
                            reply_markup=shop_main_kb(),
                            parse_mode=ParseMode.HTML,
                        )
                    except Exception:
                        pass

                    await asyncio.sleep(0.1)
        except Exception:
            pass
        await asyncio.sleep(60)


# ================= ПРОВЕРКА ПОДПИСКИ НА КАНАЛ =================
async def check_channel_sub(bot: Bot, user_id: int) -> bool:
    if user_id == ADMIN_ID or not CHANNEL_USERNAME:
        return True
    try:
        member = await bot.get_chat_member(chat_id=CHANNEL_USERNAME, user_id=user_id)
        return member.status in ("member", "administrator", "creator", "restricted")
    except Exception:
        return True


def sub_required_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="📢 Подписаться на канал", url=CHANNEL_URL)],
            [InlineKeyboardButton(text="✅ Я подписался", callback_data="check_sub")],
        ]
    )


async def ensure_subscribed(bot: Bot, user_id: int, target_msg: Message) -> bool:
    if await check_channel_sub(bot, user_id):
        await reward_referrer_if_needed(user_id, bot)
        return True
    await target_msg.answer(
        "🔒 <b>Доступ к боту закрыт</b>\n\n"
        "Чтобы пользоваться нейросетями и получать бонусы за друзей, подпишись на наш канал и нажми кнопку ниже:",
        reply_markup=sub_required_kb(),
        parse_mode=ParseMode.HTML,
    )
    return False


def is_pro(user: dict) -> bool:
    return user["pro_until"] > time.time()


def format_status(user: dict) -> str:
    extra = user.get("extra_requests", 0)
    extra_str = f" + {extra} из пакета" if extra > 0 else ""
    if is_pro(user):
        if user["pro_until"] > time.time() + 365 * 5 * 86400:
            return "👑 Подписка: Навсегда"
        exp = datetime.fromtimestamp(user["pro_until"]).strftime("%d.%m.%Y %H:%M")
        return f"👑 Подписка активна (до {exp})"
    total_limit = FREE_DAILY_LIMIT + user["bonus_limit"]
    left = max(0, total_limit - user["used_today"])
    return f"🆓 Бесплатный план ({left}/{total_limit} сегодня{extra_str})"


# ================= КЛАВИАТУРЫ =================
def categories_kb(user_id: int = 0) -> InlineKeyboardMarkup:
    buttons = [
        [
            InlineKeyboardButton(text="🤖 GPT", callback_data="cat:gpt"),
            InlineKeyboardButton(text="🧠 Claude", callback_data="cat:claude"),
        ],
        [
            InlineKeyboardButton(text="✨ Gemini", callback_data="cat:gemini"),
            InlineKeyboardButton(text="🐋 DeepSeek", callback_data="cat:deepseek"),
        ],
        [
            InlineKeyboardButton(text="⚡ Grok", callback_data="cat:grok"),
            InlineKeyboardButton(text="⭐ Подписка / Пакеты", callback_data="shop"),
        ],
        [
            InlineKeyboardButton(text="👤 Профиль", callback_data="profile"),
            InlineKeyboardButton(text=f"💸 Партнёрка ({REF_COMMISSION_PERCENT}%)", callback_data="ref_info"),
        ],
        [
            InlineKeyboardButton(text="📄 Документы и поддержка", callback_data="docs"),
        ],
    ]
    if user_id == ADMIN_ID:
        buttons.append([InlineKeyboardButton(text="🛠 Админ-панель", callback_data="admin_panel")])

    return InlineKeyboardMarkup(inline_keyboard=buttons)


def docs_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="📄 Пользовательское соглашение", url=TERMS_URL)],
            [InlineKeyboardButton(text="🔒 Политика конфиденциальности", url=PRIVACY_URL)],
            [InlineKeyboardButton(text="🆘 Написать в поддержку", url=SUPPORT_URL)],
            [InlineKeyboardButton(text="⬅️ Назад в меню", callback_data="back_cats")],
        ]
    )


def models_in_category_kb(cat_key: str, current_model: str, pro_active: bool) -> InlineKeyboardMarkup:
    cat = CATEGORIES[cat_key]
    buttons = []
    for m in cat["models"]:
        check = "✅ " if m["id"] == current_model else ""
        if pro_active:
            status_tag = ""
            lock = ""
        else:
            status_tag = f" [{m['tag']}]"
            lock = "🔒 " if m["pro"] else ""
        btn_text = f"{check}{lock}{m['name']}{status_tag}"
        buttons.append([InlineKeyboardButton(text=btn_text, callback_data=f"set_model:{cat_key}:{m['id']}")])

    buttons.append([InlineKeyboardButton(text="⬅️ Назад к категориям", callback_data="back_cats")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def shop_main_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="👑 Подписка (безлимит PRO)", callback_data="shop:subs")],
            [InlineKeyboardButton(text="⚡ Пакеты запросов (от 1 шт.)", callback_data="shop:packs")],
            [InlineKeyboardButton(text="⬅️ Назад в меню", callback_data="back_cats")],
        ]
    )


async def render_shop_main_text(user: dict) -> str:
    disc_info = await get_effective_discount(user)
    disc_line = ""
    if disc_info["active"]:
        exp = datetime.fromtimestamp(disc_info["until"]).strftime("%d.%m %H:%M")
        label = "ГЛОБАЛЬНАЯ СКИДКА" if disc_info["is_global"] else "ПЕРСОНАЛЬНАЯ СКИДКА"
        disc_line = f"🔥 <b>АКТИВНА {label} {disc_info['percent']}% (до {exp})!</b>\n\n"

    return (
        f"⭐ <b>Магазин подписок и пакетов</b>\n\n"
        f"{disc_line}"
        "Выбери, что хочешь приобрести:\n\n"
        "👑 <b>Подписка</b> — полный безлимит на все PRO-модели (GPT-6, Claude 5, Gemini Pro, Grok) на выбранное количество дней.\n"
        "⚡ <b>Пакеты запросов</b> — дополнительные запросы (от 1 шт. за 3 ₽), которые не сгорают и расходуются после дневного лимита."
    )


def shop_subs_kb(discount_percent: int = 0) -> InlineKeyboardMarkup:
    buttons = []
    for key in ("sub_trial", "sub_standard", "sub_premium"):
        p = PRODUCTS[key]
        sp = get_product_price(p, discount_percent)
        rp = get_product_rub_price(p, discount_percent)
        prefix = "🔥" if discount_percent > 0 else "👑"
        buttons.append([
            InlineKeyboardButton(
                text=f"{prefix} {p['title']} — {rp} ₽ / {sp} ⭐",
                callback_data=f"choose_pay:prod:{key}",
            )
        ])

    buttons.append([InlineKeyboardButton(text=f"✏️ Выбрать своё кол-во дней (1–{MAX_CUSTOM_SUB_DAYS})", callback_data="custom_sub_enter")])
    buttons.append([InlineKeyboardButton(text="⬅️ Назад в магазин", callback_data="shop")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)


async def render_shop_subs_text(user: dict) -> str:
    disc_info = await get_effective_discount(user)
    pct = disc_info["percent"]
    lines = ["👑 <b>Подписки (безлимит на все PRO-модели)</b>\n"]
    if disc_info["active"]:
        exp = datetime.fromtimestamp(disc_info["until"]).strftime("%d.%m %H:%M")
        label = "Глобальная скидка" if disc_info["is_global"] else "Персональная скидка"
        lines.append(f"🔥 <b>{label} {pct}% активна до {exp}!</b>\n")

    for key in ("sub_trial", "sub_standard", "sub_premium"):
        p = PRODUCTS[key]
        sp = get_product_price(p, pct)
        rp = get_product_rub_price(p, pct)
        if pct > 0:
            lines.append(f"• {p['title']}: <s>{p['rub']} ₽</s> → <b>{rp} ₽</b> ({sp} ⭐)")
        else:
            lines.append(f"• {p['title']} — <b>{rp} ₽</b> / <b>{sp} ⭐</b>")

    lines.append(f"\nТакже ты можешь указать <b>любой свой срок от 1 до {MAX_CUSTOM_SUB_DAYS} дней</b> кнопкой ниже.")
    return "\n".join(lines)


def shop_packs_kb(discount_percent: int = 0) -> InlineKeyboardMarkup:
    buttons = []
    for key in ("pack_30", "pack_100", "pack_300"):
        p = PRODUCTS[key]
        sp = get_product_price(p, discount_percent)
        rp = get_product_rub_price(p, discount_percent)
        prefix = "🔥" if discount_percent > 0 else "⚡"
        buttons.append([
            InlineKeyboardButton(
                text=f"{prefix} {p['title']} — {rp} ₽ / {sp} ⭐",
                callback_data=f"choose_pay:prod:{key}",
            )
        ])

    buttons.append([
        InlineKeyboardButton(
            text=f"✏️ Выбрать своё кол-во запросов ({MIN_CUSTOM_PACK_REQS}–{MAX_CUSTOM_PACK_REQS})",
            callback_data="custom_pack_enter",
        )
    ])
    buttons.append([InlineKeyboardButton(text="⬅️ Назад в магазин", callback_data="shop")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)


async def render_shop_packs_text(user: dict) -> str:
    disc_info = await get_effective_discount(user)
    pct = disc_info["percent"]
    lines = ["⚡ <b>Пакеты запросов (расходуются после дневного лимита)</b>\n"]
    if disc_info["active"]:
        exp = datetime.fromtimestamp(disc_info["until"]).strftime("%d.%m %H:%M")
        label = "Глобальная скидка" if disc_info["is_global"] else "Персональная скидка"
        lines.append(f"🔥 <b>{label} {pct}% активна до {exp}!</b>\n")

    for key in ("pack_30", "pack_100", "pack_300"):
        p = PRODUCTS[key]
        sp = get_product_price(p, pct)
        rp = get_product_rub_price(p, pct)
        if pct > 0:
            lines.append(f"• {p['title']}: <s>{p['rub']} ₽</s> → <b>{rp} ₽</b> ({sp} ⭐)")
        else:
            lines.append(f"• {p['title']} — <b>{rp} ₽</b> / <b>{sp} ⭐</b>")

    lines.append(
        f"\nТакже ты можешь купить <b>любое количество от {MIN_CUSTOM_PACK_REQS} до {MAX_CUSTOM_PACK_REQS} запросов</b> (от 3 ₽ за 1 запрос) кнопкой ниже."
    )
    return "\n".join(lines)


def profile_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="🎟 Активировать промокод", callback_data="promo_enter")],
            [InlineKeyboardButton(text="⭐ Купить подписку или пакет", callback_data="shop")],
            [InlineKeyboardButton(text=f"💸 Партнёрка ({REF_COMMISSION_PERCENT}%) и вывод", callback_data="ref_info")],
            [InlineKeyboardButton(text="🧹 Сброс чата", callback_data="clear_chat")],
            [InlineKeyboardButton(text="⬅️ Назад в меню", callback_data="back_cats")],
        ]
    )


async def admin_kb() -> InlineKeyboardMarkup:
    engine = await get_engine_model()
    g_disc = await get_global_discount()
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute("SELECT COUNT(*) FROM withdrawals WHERE status = 'pending'") as cur:
            pending_w = (await cur.fetchone())[0]

    w_label = f"💸 Заявки на вывод ({pending_w} шт.)" if pending_w > 0 else "💸 Заявки на вывод (0)"
    if g_disc["active"]:
        exp_str = datetime.fromtimestamp(g_disc["until"]).strftime("%d.%m %H:%M")
        g_disc_label = f"🔥 Глобальная скидка: -{g_disc['percent']}% (до {exp_str})"
    else:
        g_disc_label = "🔥 Глобальная скидка (настроить)"

    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="👥 Пользователи (просмотр / выдача / снятие)", callback_data="adm_users:0")],
            [InlineKeyboardButton(text="📜 История запросов", callback_data="adm_req_hist:0")],
            [InlineKeyboardButton(text=w_label, callback_data="adm_withdrawals")],
            [InlineKeyboardButton(text=g_disc_label, callback_data="adm_gdisc_menu")],
            [InlineKeyboardButton(text="📢 Рассылка всем пользователям", callback_data="adm_broadcast")],
            [InlineKeyboardButton(text=f"⚙️ Общий движок (текст и фото): {engine}", callback_data="adm_set_engine")],
            [InlineKeyboardButton(text="🎟 Создать промокод", callback_data="adm_promo_create")],
            [InlineKeyboardButton(text="📋 Список промокодов", callback_data="adm_promo_list")],
            [InlineKeyboardButton(text="👑 Выдать Премиум себе (30 дн.)", callback_data="adm_self_pro")],
            [InlineKeyboardButton(text="💾 Скачать бэкап базы вручную", callback_data="adm_backup_now")],
            [InlineKeyboardButton(text="🔌 Проверить живые модели API", callback_data="adm_check_api")],
            [InlineKeyboardButton(text="⬅️ В главное меню", callback_data="back_cats")],
        ]
    )


def admin_cancel_kb(back_cb: str = "admin_panel") -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[[InlineKeyboardButton(text="❌ Отмена", callback_data=back_cb)]]
    )


# ================= ДОКУМЕНТЫ И ПОДДЕРЖКА =================
def render_docs_text() -> str:
    return (
        "📄 <b>Юридическая информация и поддержка</b>\n\n"
        "Ознакомься с правилами использования сервиса и политикой обработки данных по ссылкам ниже:\n\n"
        f"• Пользовательское соглашение: {TERMS_URL}\n"
        f"• Политика конфиденциальности: {PRIVACY_URL}\n"
        f"• Служба поддержки: @{SUPPORT_USERNAME}"
    )


@router.message(Command("docs"))
async def cmd_docs(message: Message):
    await message.answer(
        render_docs_text(),
        reply_markup=docs_kb(),
        parse_mode=ParseMode.HTML,
        disable_web_page_preview=True,
    )


@router.callback_query(F.data == "docs")
async def cb_docs(call: CallbackQuery):
    try:
        await call.message.edit_text(
            render_docs_text(),
            reply_markup=docs_kb(),
            parse_mode=ParseMode.HTML,
            disable_web_page_preview=True,
        )
    except TelegramBadRequest:
        pass
    await call.answer()


# ================= МАГАЗИН: РАЗДЕЛЫ, КАСТОМНЫЙ ВВОД И ОПЛАТА (PLATEGA СБП + STARS) =================
@router.callback_query(F.data == "shop")
async def cb_shop(call: CallbackQuery, bot: Bot):
    USER_INPUT_STATE.pop(call.from_user.id, None)
    if not await ensure_subscribed(bot, call.from_user.id, call.message):
        await call.answer()
        return
    user = await get_user(call.from_user.id, full_name=call.from_user.full_name, username=call.from_user.username or "")
    try:
        await call.message.edit_text(await render_shop_main_text(user), reply_markup=shop_main_kb(), parse_mode=ParseMode.HTML)
    except TelegramBadRequest:
        pass
    await call.answer()


@router.callback_query(F.data == "shop:subs")
async def cb_shop_subs(call: CallbackQuery, bot: Bot):
    USER_INPUT_STATE.pop(call.from_user.id, None)
    if not await ensure_subscribed(bot, call.from_user.id, call.message):
        await call.answer()
        return
    user = await get_user(call.from_user.id)
    disc_info = await get_effective_discount(user)
    try:
        await call.message.edit_text(
            await render_shop_subs_text(user),
            reply_markup=shop_subs_kb(disc_info["percent"]),
            parse_mode=ParseMode.HTML,
        )
    except TelegramBadRequest:
        pass
    await call.answer()


@router.callback_query(F.data == "shop:packs")
async def cb_shop_packs(call: CallbackQuery, bot: Bot):
    USER_INPUT_STATE.pop(call.from_user.id, None)
    if not await ensure_subscribed(bot, call.from_user.id, call.message):
        await call.answer()
        return
    user = await get_user(call.from_user.id)
    disc_info = await get_effective_discount(user)
    try:
        await call.message.edit_text(
            await render_shop_packs_text(user),
            reply_markup=shop_packs_kb(disc_info["percent"]),
            parse_mode=ParseMode.HTML,
        )
    except TelegramBadRequest:
        pass
    await call.answer()


@router.callback_query(F.data == "custom_sub_enter")
async def cb_custom_sub_enter(call: CallbackQuery):
    USER_INPUT_STATE[call.from_user.id] = "await_custom_sub_days"
    await call.message.edit_text(
        f"👑 <b>Свой срок подписки PRO</b>\n\n"
        f"Введи количество дней от <b>1 до {MAX_CUSTOM_SUB_DAYS}</b> одним числом (например: <code>2</code>, <code>5</code> или <code>14</code>):",
        reply_markup=InlineKeyboardMarkup(
            inline_keyboard=[[InlineKeyboardButton(text="❌ Отмена", callback_data="shop:subs")]]
        ),
        parse_mode=ParseMode.HTML,
    )
    await call.answer()


@router.callback_query(F.data == "custom_pack_enter")
async def cb_custom_pack_enter(call: CallbackQuery):
    USER_INPUT_STATE[call.from_user.id] = "await_custom_pack_reqs"
    await call.message.edit_text(
        f"⚡ <b>Свой пакет запросов</b>\n\n"
        f"Введи нужное количество запросов от <b>{MIN_CUSTOM_PACK_REQS} до {MAX_CUSTOM_PACK_REQS}</b> одним числом (1 запрос = 3 ₽):",
        reply_markup=InlineKeyboardMarkup(
            inline_keyboard=[[InlineKeyboardButton(text="❌ Отмена", callback_data="shop:packs")]]
        ),
        parse_mode=ParseMode.HTML,
    )
    await call.answer()


async def send_payment_method_choice(target_msg: Message, user_id: int, order_code: str, edit: bool = True):
    user = await get_user(user_id)
    disc_info = await get_effective_discount(user)
    order = resolve_order_details(order_code, disc_info["percent"])
    if not order:
        if edit:
            await target_msg.edit_text("⚠️ Товар не найден.", reply_markup=shop_main_kb())
        else:
            await target_msg.answer("⚠️ Товар не найден.", reply_markup=shop_main_kb())
        return

    if order["type"] == "sub":
        desc = f"Безлимитный доступ ко всем PRO-моделям на {order['value']} дн."
    else:
        desc = f"Пакет на {order['value']} дополнительных запросов."

    kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text=f"💳 СБП — {order['rub']} ₽", callback_data=f"pay_sbp:{order_code}")],
            [InlineKeyboardButton(text=f"⭐ Telegram Stars — {order['stars']} ⭐", callback_data=f"pay_stars:{order_code}")],
            [InlineKeyboardButton(text="⬅️ Назад к тарифам", callback_data=order["back_cb"])],
        ]
    )

    text = (
        f"🛒 <b>Оформление заказа</b>\n\n"
        f"📦 Тариф: <b>{order['title']}</b>\n"
        f"📝 Описание: {desc}\n\n"
        f"Чем вы хотите оплатить?"
    )

    if edit:
        try:
            await target_msg.edit_text(text, reply_markup=kb, parse_mode=ParseMode.HTML)
        except TelegramBadRequest:
            pass
    else:
        await target_msg.answer(text, reply_markup=kb, parse_mode=ParseMode.HTML)


@router.callback_query(F.data.startswith("choose_pay:"))
async def cb_choose_pay(call: CallbackQuery):
    order_code = call.data.split(":", 1)[1]
    await send_payment_method_choice(call.message, call.from_user.id, order_code, edit=True)
    await call.answer()


@router.callback_query(F.data.startswith("pay_sbp:"))
async def cb_pay_sbp(call: CallbackQuery):
    order_code = call.data.split(":", 1)[1]
    user = await get_user(call.from_user.id)
    disc_info = await get_effective_discount(user)
    order = resolve_order_details(order_code, disc_info["percent"])
    if not order:
        await call.answer("Товар не найден", show_alert=True)
        return

    await call.answer("⏳ Создаю платёжную ссылку СБП...")
    try:
        tx_data = await platega_create_transaction(
            amount_rub=order["rub"],
            description=f"{order['title']} (ID {call.from_user.id})",
            payload_str=f"{call.from_user.id}:{order_code}",
        )
        tx_id = tx_data["transaction_id"]
        pay_url = tx_data["redirect"]

        async with aiosqlite.connect(DB_PATH) as db:
            await db.execute(
                """
                INSERT INTO platega_transactions
                (transaction_id, user_id, order_code, title, item_type, item_value, rub_amount, redirect_url, status, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, 'PENDING', ?)
                """,
                (
                    tx_id,
                    call.from_user.id,
                    order_code,
                    order["title"],
                    order["type"],
                    order["value"],
                    float(order["rub"]),
                    pay_url,
                    time.time(),
                ),
            )
            await db.commit()

        kb = InlineKeyboardMarkup(
            inline_keyboard=[
                [InlineKeyboardButton(text=f"💳 Перейти к оплате ({order['rub']} ₽)", url=pay_url)],
                [InlineKeyboardButton(text="🔄 Проверить оплату", callback_data=f"chk_sbp:{tx_id}")],
                [InlineKeyboardButton(text="⬅️ Назад к выбору оплаты", callback_data=f"choose_pay:{order_code}")],
            ]
        )

        await call.message.edit_text(
            f"💳 <b>Счёт на оплату через СБП создан!</b>\n\n"
            f"📦 Тариф: <b>{order['title']}</b>\n"
            f"💰 Сумма: <b>{order['rub']} ₽</b>\n"
            f"🆔 Номер платежа: <code>{tx_id}</code>\n\n"
            f"1. Нажми <b>«Перейти к оплате»</b> и оплати по СБП.\n"
            f"2. После оплаты подписка или запросы начислятся <b>автоматически в течение 10–15 секунд</b> (или нажми «Проверить оплату»).",
            reply_markup=kb,
            parse_mode=ParseMode.HTML,
        )
    except Exception as e:
        await call.message.edit_text(
            f"⚠️ <b>Не удалось создать платёж СБП:</b>\n<code>{html.escape(str(e)[:250])}</code>\n\n"
            f"Попробуй оплатить через Telegram Stars или обратись в поддержку @{SUPPORT_USERNAME}.",
            reply_markup=InlineKeyboardMarkup(
                inline_keyboard=[
                    [InlineKeyboardButton(text="⭐ Оплатить через Telegram Stars", callback_data=f"pay_stars:{order_code}")],
                    [InlineKeyboardButton(text="⬅️ Назад", callback_data=f"choose_pay:{order_code}")],
                ]
            ),
            parse_mode=ParseMode.HTML,
        )


@router.callback_query(F.data.startswith("chk_sbp:"))
async def cb_chk_sbp(call: CallbackQuery, bot: Bot):
    tx_id = call.data.split(":", 1)[1]
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute("SELECT * FROM platega_transactions WHERE transaction_id = ?", (tx_id,)) as cur:
            tx = await cur.fetchone()

    if not tx:
        await call.answer("Транзакция не найдена.", show_alert=True)
        return

    if tx["status"] == "CONFIRMED":
        await call.answer("✅ Оплата уже подтверждена и зачислена!", show_alert=True)
        return

    st = await platega_fetch_status(tx_id)
    if st == "CONFIRMED":
        await fulfill_platega_transaction(tx_id, bot)
        await call.answer("✅ Оплата подтверждена! Доступ начислен.", show_alert=True)
        try:
            await call.message.delete()
        except Exception:
            pass
    elif st in ("CANCELED", "CANCELLED", "EXPIRED", "FAILED"):
        async with aiosqlite.connect(DB_PATH) as db:
            await db.execute("UPDATE platega_transactions SET status = ? WHERE transaction_id = ?", (st, tx_id))
            await db.commit()
        await call.answer("❌ Срок действия платежа истёк или платёж отменён.", show_alert=True)
    else:
        await call.answer("⏳ Платёж ещё не поступил. Если ты уже оплатил — подожди 10 секунд и нажми снова.", show_alert=True)


@router.callback_query(F.data.startswith("pay_stars:"))
async def cb_pay_stars(call: CallbackQuery):
    order_code = call.data.split(":", 1)[1]
    user = await get_user(call.from_user.id)
    disc_info = await get_effective_discount(user)
    pct = disc_info["percent"]
    order = resolve_order_details(order_code, pct)
    if not order:
        await call.answer("Товар не найден", show_alert=True)
        return

    if order["type"] == "sub":
        desc = f"Безлимитный доступ ко всем PRO-моделям на {order['value']} дн."
    else:
        desc = f"Пакет на {order['value']} дополнительных запросов."

    await call.message.answer_invoice(
        title=order["title"] + (f" (Скидка {pct}%)" if (pct > 0 and order["stars"] >= 5) else ""),
        description=desc,
        payload=f"ord:{order_code}",
        currency="XTR",
        prices=[LabeledPrice(label=order["title"], amount=order["stars"])],
    )
    await call.answer()


@router.pre_checkout_query()
async def pre_checkout(query: PreCheckoutQuery):
    await query.answer(ok=True)


@router.message(F.successful_payment)
async def successful_payment(message: Message, bot: Bot):
    payload = message.successful_payment.invoice_payload
    paid_stars = message.successful_payment.total_amount
    user = await get_user(message.from_user.id)
    disc_info = await get_effective_discount(user)

    if payload.startswith("ord:"):
        order_code = payload.split(":", 1)[1]
    elif payload.startswith("prod:"):
        order_code = payload
    else:
        order_code = payload

    order = resolve_order_details(order_code, disc_info["percent"])
    if not order:
        order = {
            "order_code": order_code,
            "type": "pack",
            "title": f"Оплата {paid_stars} ⭐",
            "value": paid_stars,
            "rub": round(paid_stars * STARS_TO_RUB_RATE),
            "stars": paid_stars,
        }

    rub_equivalent = round(paid_stars * STARS_TO_RUB_RATE, 2)

    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "INSERT INTO payments (user_id, product_key, title, stars, rub_amount, method, paid_at) VALUES (?, ?, ?, ?, ?, 'stars', ?)",
            (message.from_user.id, order["order_code"], order["title"], paid_stars, rub_equivalent, time.time()),
        )

        if order["type"] == "sub":
            days = order["value"]
            base_time = max(time.time(), user["pro_until"])
            new_pro_until = base_time + days * 86400
            exp_date = datetime.fromtimestamp(new_pro_until).strftime("%d.%m.%Y %H:%M")

            await db.execute("UPDATE users SET pro_until = ? WHERE user_id = ?", (new_pro_until, message.from_user.id))
            await db.commit()

            await message.answer(
                f"🎉 <b>Оплата прошла успешно!</b>\n"
                f"Тариф <b>«{order['title']}»</b> активен до <b>{exp_date}</b>.\n"
                f"Все модели разблокированы в /menu.",
                parse_mode=ParseMode.HTML,
            )
        else:
            packs = order["value"]
            await db.execute(
                "UPDATE users SET extra_requests = extra_requests + ? WHERE user_id = ?",
                (packs, message.from_user.id),
            )
            await db.commit()

            await message.answer(
                f"🎉 <b>Оплата прошла успешно!</b>\n"
                f"На твой баланс зачислен <b>пакет на +{packs} запросов</b>.\n"
                f"Проверить остаток можно в /profile.",
                parse_mode=ParseMode.HTML,
            )

    await credit_referral_commission(message.from_user.id, rub_equivalent, order["title"], bot)


# ================= ПАРТНЁРСКАЯ ПРОГРАММА (25% С ПОКУПОК + ВЫВОД ОТ 100 ₽) =================
async def render_partner_text(user_id: int, bot_username: str) -> tuple[str, InlineKeyboardMarkup]:
    user = await get_user(user_id)
    ref_bal = user.get("ref_balance") or 0.0
    ref_total = user.get("ref_total_earned") or 0.0

    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute(
            "SELECT COUNT(*) FROM users WHERE referred_by = ? AND ref_rewarded = 1",
            (user_id,),
        ) as cur:
            invited_count = (await cur.fetchone())[0]

    base_tg = "https" + "://" + "t.me"
    ref_link = f"{base_tg}/{bot_username}?start={user_id}"
    share_text = quote("Бесплатный ИИ-бот без VPN: GPT-6, Claude 5 и Gemini! Решает задачи по фото.")
    share_url = f"{base_tg}/share/url?url={quote(ref_link)}&text={share_text}"

    buttons = [
        [InlineKeyboardButton(text="📤 Отправить ссылку другу", url=share_url)],
    ]

    try:
        from aiogram.types import CopyTextButton
        buttons.append([
            InlineKeyboardButton(
                text="📋 Скопировать ссылку",
                copy_text=CopyTextButton(text=ref_link),
            )
        ])
    except Exception:
        pass

    buttons.append([
        InlineKeyboardButton(
            text=f"💸 Вывести средства ({ref_bal:.2f} ₽)",
            callback_data="withdraw_start",
        )
    ])
    buttons.append([InlineKeyboardButton(text="⬅️ В меню", callback_data="back_cats")])

    text = (
        f"💸 <b>Партнёрская программа ({REF_COMMISSION_PERCENT}% с покупок)</b>\n\n"
        f"Приглашай друзей и одноклассников по своей ссылке! За каждого друга, который запустит бота и подпишется на канал:\n"
        f"• Твой дневной лимит навсегда вырастет на <b>+2 запроса</b>\n"
        f"• Ты будешь получать <b>{REF_COMMISSION_PERCENT}% в рублях</b> с каждой его оплаты в боте!\n\n"
        f"📊 <b>Твоя статистика:</b>\n"
        f"👥 Приглашено друзей: <b>{invited_count} чел.</b>\n"
        f"💰 Доступно к выводу: <b>{ref_bal:.2f} ₽</b>\n"
        f"📈 Заработано за всё время: <b>{ref_total:.2f} ₽</b>\n"
        f"🏦 Минимальная сумма вывода: <b>{int(MIN_WITHDRAW_RUB)} ₽</b> (СБП / карта)\n\n"
        f"🔗 Твоя ссылка:\n<code>{ref_link}</code>"
    )
    return text, InlineKeyboardMarkup(inline_keyboard=buttons)


@router.message(Command("ref"))
async def cmd_ref(message: Message, bot: Bot):
    USER_INPUT_STATE.pop(message.from_user.id, None)
    await get_user(message.from_user.id, full_name=message.from_user.full_name, username=message.from_user.username or "")
    if not await ensure_subscribed(bot, message.from_user.id, message):
        return
    me = await bot.get_me()
    text, kb = await render_partner_text(message.from_user.id, me.username or "AetherNeural_bot")
    await message.answer(text, reply_markup=kb, parse_mode=ParseMode.HTML, disable_web_page_preview=True)


@router.callback_query(F.data == "ref_info")
async def cb_ref_info(call: CallbackQuery, bot: Bot):
    USER_INPUT_STATE.pop(call.from_user.id, None)
    if not await ensure_subscribed(bot, call.from_user.id, call.message):
        await call.answer()
        return
    me = await bot.get_me()
    text, kb = await render_partner_text(call.from_user.id, me.username or "AetherNeural_bot")
    try:
        await call.message.edit_text(text, reply_markup=kb, parse_mode=ParseMode.HTML, disable_web_page_preview=True)
    except TelegramBadRequest:
        await call.message.answer(text, reply_markup=kb, parse_mode=ParseMode.HTML, disable_web_page_preview=True)
    await call.answer()


@router.callback_query(F.data == "withdraw_start")
async def cb_withdraw_start(call: CallbackQuery):
    user = await get_user(call.from_user.id)
    bal = user.get("ref_balance") or 0.0
    if bal < MIN_WITHDRAW_RUB:
        await call.answer(
            f"❌ Минимальная сумма вывода — {int(MIN_WITHDRAW_RUB)} ₽. Сейчас на балансе: {bal:.2f} ₽.",
            show_alert=True,
        )
        return

    USER_INPUT_STATE[call.from_user.id] = "await_withdraw_reqs"
    await call.message.edit_text(
        f"💸 <b>Заявка на вывод средств</b>\n\n"
        f"Сумма к выводу: <b>{bal:.2f} ₽</b>\n\n"
        f"Отправь одним сообщением свои реквизиты для перевода:\n"
        f"• Номер телефона (СБП) или номер карты\n"
        f"• Название банка (например: <code>+79991234567 Т-Банк</code>):",
        reply_markup=InlineKeyboardMarkup(
            inline_keyboard=[[InlineKeyboardButton(text="❌ Отмена", callback_data="ref_info")]]
        ),
        parse_mode=ParseMode.HTML,
    )
    await call.answer()


# ================= АДМИН: УПРАВЛЕНИЕ ЗАЯВКАМИ НА ВЫВОД =================
async def render_withdrawals_admin() -> tuple[str, InlineKeyboardMarkup]:
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute(
            """
            SELECT w.*, u.full_name, u.username
            FROM withdrawals w
            LEFT JOIN users u ON u.user_id = w.user_id
            WHERE w.status = 'pending'
            ORDER BY w.id ASC
            LIMIT 10
            """
        ) as cur:
            rows = await cur.fetchall()

    if not rows:
        return (
            "💸 <b>Заявки на вывод средств</b>\n\n<i>Активных заявок пока нет.</i>",
            InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="⬅️ В админ-панель", callback_data="admin_panel")]]),
        )

    lines = ["💸 <b>Активные заявки на вывод (ожидают выплаты):</b>\n"]
    buttons = []
    for r in rows:
        wid = r["id"]
        uid = r["user_id"]
        amt = r["amount"]
        reqs = html.escape(r["requisites"])
        name = html.escape(r["full_name"] or str(uid))
        uname = f" (@{r['username']})" if r["username"] else ""
        dt_str = datetime.fromtimestamp(r["created_at"]).strftime("%d.%m %H:%M")
        lines.append(f"#{wid} | <b>{name}</b>{uname} (<code>{uid}</code>)\n   Сумма: <b>{amt:.2f} ₽</b> | {dt_str}\n   Реквизиты: <code>{reqs}</code>\n")
        buttons.append([
            InlineKeyboardButton(text=f"✅ Выплачено #{wid} ({amt:.0f} ₽)", callback_data=f"adm_w_ok:{wid}"),
            InlineKeyboardButton(text=f"❌ Отклонить #{wid}", callback_data=f"adm_w_no:{wid}"),
        ])

    buttons.append([InlineKeyboardButton(text="⬅️ В админ-панель", callback_data="admin_panel")])
    return "\n".join(lines), InlineKeyboardMarkup(inline_keyboard=buttons)


@router.callback_query(F.data == "adm_withdrawals")
async def cb_adm_withdrawals(call: CallbackQuery):
    if call.from_user.id != ADMIN_ID:
        return
    text, kb = await render_withdrawals_admin()
    try:
        await call.message.edit_text(text, reply_markup=kb, parse_mode=ParseMode.HTML)
    except TelegramBadRequest:
        pass
    await call.answer()


@router.callback_query(F.data.startswith("adm_w_ok:"))
async def cb_adm_w_ok(call: CallbackQuery, bot: Bot):
    if call.from_user.id != ADMIN_ID:
        return
    wid = int(call.data.split(":", 1)[1])
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute("SELECT * FROM withdrawals WHERE id = ?", (wid,)) as cur:
            w = await cur.fetchone()
        if not w or w["status"] != "pending":
            await call.answer("Заявка уже обработана", show_alert=True)
            return
        await db.execute("UPDATE withdrawals SET status = 'paid' WHERE id = ?", (wid,))
        await db.commit()

    await call.answer(f"✅ Заявка #{wid} отмечена как выплаченная!")
    try:
        await bot.send_message(
            w["user_id"],
            f"✅ <b>Выплата {w['amount']:.2f} ₽ успешно отправлена!</b>\n"
            f"Реквизиты: <code>{html.escape(w['requisites'])}</code>\nСпасибо за участие в партнёрской программе!",
            parse_mode=ParseMode.HTML,
        )
    except Exception:
        pass

    text, kb = await render_withdrawals_admin()
    await call.message.edit_text(text, reply_markup=kb, parse_mode=ParseMode.HTML)


@router.callback_query(F.data.startswith("adm_w_no:"))
async def cb_adm_w_no(call: CallbackQuery, bot: Bot):
    if call.from_user.id != ADMIN_ID:
        return
    wid = int(call.data.split(":", 1)[1])
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute("SELECT * FROM withdrawals WHERE id = ?", (wid,)) as cur:
            w = await cur.fetchone()
        if not w or w["status"] != "pending":
            await call.answer("Заявка уже обработана", show_alert=True)
            return
        await db.execute("UPDATE withdrawals SET status = 'rejected' WHERE id = ?", (wid,))
        await db.execute("UPDATE users SET ref_balance = ref_balance + ? WHERE user_id = ?", (w["amount"], w["user_id"]))
        await db.commit()

    await call.answer(f"❌ Заявка #{wid} отклонена, средства возвращены на баланс")
    try:
        await bot.send_message(
            w["user_id"],
            f"⚠️ <b>Заявка на вывод {w['amount']:.2f} ₽ отклонена</b> (проверь правильность реквизитов или обратись в поддержку @{SUPPORT_USERNAME}).\n"
            f"Средства возвращены на твой реферальный баланс.",
            parse_mode=ParseMode.HTML,
        )
    except Exception:
        pass

    text, kb = await render_withdrawals_admin()
    await call.message.edit_text(text, reply_markup=kb, parse_mode=ParseMode.HTML)


# ================= ВИДЕО, КРУЖОЧКИ И АУДИО (УНИВЕРСАЛЬНЫЙ ШЛЮЗ + АВТО-РАСКАДРОВКА) =================
_FFMPEG_BIN_CACHE: str | None = None


def _get_or_install_ffmpeg() -> str | None:
    """Находит системный ffmpeg, imageio_ffmpeg или автоматически ставит imageio-ffmpeg в пользовательское окружение."""
    global _FFMPEG_BIN_CACHE
    if _FFMPEG_BIN_CACHE and os.path.exists(_FFMPEG_BIN_CACHE):
        return _FFMPEG_BIN_CACHE

    fb = shutil.which("ffmpeg")
    if fb:
        _FFMPEG_BIN_CACHE = fb
        return fb

    try:
        import imageio_ffmpeg
        fb = imageio_ffmpeg.get_ffmpeg_exe()
        if fb and os.path.exists(fb):
            _FFMPEG_BIN_CACHE = fb
            return fb
    except Exception:
        pass

    # Пробуем тихо подтянуть imageio-ffmpeg на хостинг (bothost / linux)
    try:
        import subprocess
        import sys
        subprocess.run(
            [sys.executable, "-m", "pip", "install", "--quiet", "--disable-pip-version-check", "imageio-ffmpeg"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            timeout=45,
        )
        import imageio_ffmpeg
        fb = imageio_ffmpeg.get_ffmpeg_exe()
        if fb and os.path.exists(fb):
            _FFMPEG_BIN_CACHE = fb
            return fb
    except Exception:
        pass

    return None


def _extract_jpeg_frames_from_mp4_bytes(raw_bytes: bytes, max_frames: int = 5) -> list[str]:
    """Резервный парсер встроенных JPEG/MJPEG кадров или I-кадров без внешних библиотек."""
    frames: list[str] = []
    start = 0
    while len(frames) < max_frames:
        soi = raw_bytes.find(b"\xff\xd8\xff", start)
        if soi == -1:
            break
        eoi = raw_bytes.find(b"\xff\xd9", soi + 3)
        if eoi == -1:
            break
        chunk = raw_bytes[soi : eoi + 2]
        if len(chunk) > 2048:
            frames.append(base64.b64encode(chunk).decode("utf-8"))
        start = eoi + 2
    return frames


async def extract_video_frames_and_audio(raw_bytes: bytes, max_frames: int = 5) -> tuple[list[str], bytes | None]:
    """Извлекает ключевые кадры (JPEG base64) и WAV/MP3-дорожку из видео/кружочка."""
    import subprocess
    import tempfile

    def _run_extract() -> tuple[list[str], bytes | None]:
        frames: list[str] = []
        audio_bytes: bytes | None = None
        with tempfile.TemporaryDirectory() as tmpdir:
            in_path = os.path.join(tmpdir, "input.mp4")
            with open(in_path, "wb") as f:
                f.write(raw_bytes)

            ffmpeg_bin = _get_or_install_ffmpeg()
            if ffmpeg_bin:
                out_pattern = os.path.join(tmpdir, "frame_%02d.jpg")
                cmd_frames = [
                    ffmpeg_bin, "-y", "-i", in_path,
                    "-vf", "fps=1,scale='min(640,iw)':-1",
                    "-frames:v", str(max_frames),
                    "-q:v", "4",
                    out_pattern,
                ]
                subprocess.run(cmd_frames, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=20)
                for fn in sorted(os.listdir(tmpdir)):
                    if fn.startswith("frame_") and fn.endswith(".jpg"):
                        with open(os.path.join(tmpdir, fn), "rb") as img_f:
                            frames.append(base64.b64encode(img_f.read()).decode("utf-8"))

                # Если видео короче 1 секунды и fps=1 не дал кадров — берём самый первый кадр
                if not frames:
                    first_frame = os.path.join(tmpdir, "first.jpg")
                    subprocess.run(
                        [ffmpeg_bin, "-y", "-i", in_path, "-vframes", "1", "-q:v", "4", first_frame],
                        stdout=subprocess.DEVNULL,
                        stderr=subprocess.DEVNULL,
                        timeout=15,
                    )
                    if os.path.exists(first_frame):
                        with open(first_frame, "rb") as img_f:
                            frames.append(base64.b64encode(img_f.read()).decode("utf-8"))

                # Извлекаем аудиодорожку (mp3)
                out_audio = os.path.join(tmpdir, "audio.mp3")
                subprocess.run(
                    [ffmpeg_bin, "-y", "-i", in_path, "-vn", "-acodec", "libmp3lame", "-ar", "16000", "-ac", "1", out_audio],
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                    timeout=15,
                )
                if os.path.exists(out_audio) and os.path.getsize(out_audio) > 512:
                    with open(out_audio, "rb") as af:
                        audio_bytes = af.read()

                if frames or audio_bytes:
                    return frames, audio_bytes

            # Резерв через OpenCV (cv2)
            try:
                import cv2
                cap = cv2.VideoCapture(in_path)
                total = int(cap.get(cv2.CAP_PROP_FRAME_COUNT)) or 0
                if total > 0:
                    step = max(1, total // max_frames)
                    for idx in range(0, total, step):
                        if len(frames) >= max_frames:
                            break
                        cap.set(cv2.CAP_PROP_POS_FRAMES, idx)
                        ok, frame = cap.read()
                        if ok and frame is not None:
                            ok_jpg, buf = cv2.imencode(".jpg", frame, [int(cv2.IMWRITE_JPEG_QUALITY), 80])
                            if ok_jpg:
                                frames.append(base64.b64encode(buf.tobytes()).decode("utf-8"))
                cap.release()
            except Exception:
                pass

            if not frames:
                frames = _extract_jpeg_frames_from_mp4_bytes(raw_bytes, max_frames=max_frames)

        return frames, audio_bytes

    return await asyncio.to_thread(_run_extract)


async def generate_media_multimodal_response(
    user_id: int, selected_model: str, caption: str, b64_data: str, mime_type: str
) -> str:
    """Пробует отправить медиафайл через input_audio / image_url по доступным моделям (без зависания на 404)."""
    candidates = await get_candidates_for_user(user_id, selected_model)
    for m in VIDEO_FALLBACK_MODELS:
        if m not in candidates:
            candidates.append(m)

    is_audio = mime_type.startswith("audio/")
    fmt = "ogg" if "ogg" in mime_type else ("wav" if "wav" in mime_type else "mp3")

    payload_variants = []
    if is_audio:
        payload_variants.append([
            {"type": "text", "text": caption},
            {"type": "input_audio", "input_audio": {"data": b64_data, "format": fmt}},
        ])
    payload_variants.append([
        {"type": "text", "text": caption},
        {"type": "image_url", "image_url": {"url": f"data:{mime_type};base64,{b64_data}"}},
    ])

    last_error = None
    for user_content in payload_variants:
        messages_payload = [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_content},
        ]
        for candidate_id in candidates[:4]:
            try:
                response = await asyncio.wait_for(
                    ai_client.chat.completions.create(
                        model=candidate_id,
                        messages=messages_payload,
                        max_tokens=1500,
                    ),
                    timeout=20.0,
                )
                content = response.choices[0].message.content
                if content:
                    return content
            except Exception as e:
                last_error = e
                err_s = str(e)
                # Если шлюз целиком не поддерживает этот формат (404 на роуте), сразу выходим из цикла моделей
                if "Error code: 404" in err_s:
                    break
                continue

    raise last_error or RuntimeError("Модели обработки медиа временно недоступны")


async def transcribe_audio_whisper(raw_bytes: bytes, filename: str = "voice.ogg") -> str:
    """Пробует расшифровать речь через эндпоинт /audio/transcriptions с разными моделями."""
    whisper_candidates = []
    for wm in (WHISPER_MODEL, "whisper-1", "gpt-4o-mini-transcribe", "gpt-4o-transcribe"):
        if wm and wm not in whisper_candidates:
            whisper_candidates.append(wm)

    last_err = None
    for wm in whisper_candidates:
        try:
            audio_bio = io.BytesIO(raw_bytes)
            audio_bio.name = filename
            transcript = await asyncio.wait_for(
                ai_client.audio.transcriptions.create(
                    model=wm,
                    file=audio_bio,
                ),
                timeout=15.0,
            )
            txt = (getattr(transcript, "text", None) or "").strip()
            if txt:
                return txt
        except Exception as e:
            last_err = e
            err_s = str(e)
            if "404" in err_s or "503" in err_s or "No available accounts" in err_s:
                break
            continue
    if last_err:
        raise last_err
    return ""


@router.message(F.video | F.video_note)
async def handle_video(message: Message, bot: Bot):
    user_id = message.from_user.id
    user = await get_user(user_id, full_name=message.from_user.full_name, username=message.from_user.username or "")
    if not await ensure_subscribed(bot, user_id, message):
        return

    if is_content_forbidden(message.caption or ""):
        await message.answer("🚫 Запрос отклонён системой безопасности: запрещённый контент.")
        return

    is_circle = bool(message.video_note)
    media_obj = message.video_note if is_circle else message.video
    if media_obj.file_size and media_obj.file_size > 20 * 1024 * 1024:
        await message.answer("⚠️ Видео слишком тяжёлое (лимит Telegram для ботов — до 20 МБ). Сожми видео или обрежь его.")
        return

    model_id = user["selected_model"]
    pro_active = is_pro(user) or (user_id == ADMIN_ID)
    if ALL_MODELS_MAP.get(model_id, {}).get("pro") and not pro_active:
        await message.answer(
            "🔒 Срок подписки истек. Выбери бесплатную модель в /menu или продли тариф:",
            reply_markup=shop_main_kb(),
        )
        return

    quota_receipt = await try_consume_quota(user_id, pro_active, count=VIDEO_COST)
    if not quota_receipt:
        await message.answer(
            "⏳ Бесплатный лимит на сегодня и пакет запросов исчерпаны.\n"
            "Приходи завтра, пригласи друга за +2 запроса (/ref) или оформи подписку / пакет:",
            reply_markup=shop_main_kb(),
            parse_mode=ParseMode.HTML,
        )
        return

    shown_model = ALL_MODELS_MAP.get(model_id, {}).get("name", model_id)
    media_label = "кружочек" if is_circle else "видео"
    req_type_tag = "⭕ Кружочек" if is_circle else "🎬 Видео"
    wait_msg = await message.answer(f"🎬 <i>Анализирую {media_label} ({shown_model})...</i>", parse_mode=ParseMode.HTML)

    try:
        file_info = await bot.get_file(media_obj.file_id)
        downloaded = await bot.download_file(file_info.file_path)
        raw_bytes = downloaded.read()
        b64_video = base64.b64encode(raw_bytes).decode("utf-8")
        mime_type = getattr(media_obj, "mime_type", None) or "video/mp4"

        if is_circle:
            caption = (
                "Это видеосообщение (кружочек) из Telegram. Внимательно разбери, что происходит и что говорит человек "
                "в кружочке, и дай понятный, полезный ответ по существу."
            )
        else:
            caption = (message.caption or "").strip() or "Подробно разбери, что происходит на этом видео, и ответь на задание или вопрос."

        answer_text = None
        speech_text = ""

        # Шаг 1: раскадровка + извлечение аудио (работает через Vision на любом шлюзе, даже если видео 404!)
        frames_b64, extracted_audio = await extract_video_frames_and_audio(raw_bytes, max_frames=5)
        if extracted_audio or raw_bytes:
            try:
                speech_text = await transcribe_audio_whisper(
                    extracted_audio or raw_bytes,
                    filename="circle.mp3" if extracted_audio else "circle.mp4",
                )
            except Exception:
                speech_text = ""

        if speech_text and is_content_forbidden(speech_text):
            await refund_quota(user_id, quota_receipt)
            await wait_msg.edit_text("🚫 Запрос отклонён системой безопасности: запрещённый контент.")
            return

        if frames_b64:
            frame_prompt = caption
            if speech_text:
                frame_prompt += f"\n\nРасшифровка речи из {media_label}а: «{speech_text}»"
            else:
                frame_prompt += f"\n(Это {len(frames_b64)} последовательных кадров из {media_label}а пользователя)."
            answer_text = await generate_photos_response(
                user_id=user_id,
                selected_model=model_id,
                caption=frame_prompt,
                b64_images=frames_b64,
            )

        # Шаг 2: если кадры не извлеклись — пробуем прямую отправку видео в мультимодальный шлюз
        if not answer_text:
            try:
                answer_text = await generate_media_multimodal_response(
                    user_id=user_id,
                    selected_model=model_id,
                    caption=caption,
                    b64_data=b64_video,
                    mime_type=mime_type,
                )
            except Exception:
                answer_text = None

        # Шаг 3: если есть только расшифровка речи из кружочка — отвечаем по речи
        if not answer_text and speech_text:
            history = await get_history(user_id)
            answer_text = await generate_text_response(
                user_id=user_id,
                selected_model=model_id,
                history=history,
                user_text=f"{caption}\n\nРечь из {media_label}а: {speech_text}",
            )

        if not answer_text:
            raise RuntimeError(
                "API-шлюз отклонил прямой видеофайл (404), а на хостинге не установлен ffmpeg/imageio-ffmpeg для раскадровки."
            )

        if is_circle:
            log_q = f"[Кружочек]{' | Речь: ' + speech_text if speech_text else ' (видеоряд)'}"
        else:
            raw_cap = (message.caption or "").strip() or "без подписи"
            log_q = f"[Видео: {raw_cap}]{' | Речь: ' + speech_text if speech_text else ''}"

        await add_history(user_id, "user", log_q)
        await add_history(user_id, "assistant", answer_text)
        await log_user_request(user_id, req_type_tag, log_q, answer_text, model_used=shown_model)

        async with aiosqlite.connect(DB_PATH) as db:
            await db.execute(
                "UPDATE users SET total_requests = total_requests + ? WHERE user_id = ?",
                (VIDEO_COST, user_id),
            )
            await db.commit()

        await wait_msg.delete()
        await send_formatted_answer(message, answer_text)

    except Exception as e:
        await refund_quota(user_id, quota_receipt)
        await wait_msg.edit_text(
            f"⚠️ <b>Не удалось обработать {media_label}:</b>\n<code>{html.escape(str(e)[:280])}</code>",
            parse_mode=ParseMode.HTML,
        )


# ================= ГОЛОСОВЫЕ И АУДИО СООБЩЕНИЯ (VOICE / AUDIO -> WHISPER / MULTIMODAL) =================
@router.message(F.voice | F.audio)
async def handle_voice(message: Message, bot: Bot):
    user_id = message.from_user.id
    user = await get_user(user_id, full_name=message.from_user.full_name, username=message.from_user.username or "")
    if not await ensure_subscribed(bot, user_id, message):
        return

    if is_content_forbidden(message.caption or ""):
        await message.answer("🚫 Запрос отклонён системой безопасности: запрещённый контент.")
        return

    voice_obj = message.voice or message.audio
    if voice_obj.file_size and voice_obj.file_size > 20 * 1024 * 1024:
        await message.answer("⚠️ Аудиофайл слишком тяжёлый (лимит Telegram для ботов — до 20 МБ).")
        return

    model_id = user["selected_model"]
    pro_active = is_pro(user) or (user_id == ADMIN_ID)
    if ALL_MODELS_MAP.get(model_id, {}).get("pro") and not pro_active:
        await message.answer(
            "🔒 Срок подписки истек. Выбери бесплатную модель в /menu или продли тариф:",
            reply_markup=shop_main_kb(),
        )
        return

    quota_receipt = await try_consume_quota(user_id, pro_active, count=1)
    if not quota_receipt:
        await message.answer(
            "⏳ Бесплатный лимит на сегодня и пакет запросов исчерпаны.\n"
            "Приходи завтра, пригласи друга за +2 запроса (/ref) или оформи подписку / пакет:",
            reply_markup=shop_main_kb(),
        )
        return

    shown_model = ALL_MODELS_MAP.get(model_id, {}).get("name", model_id)
    req_type_tag = "🎙 Голосовое" if message.voice else "🎵 Аудио"
    wait_msg = await message.answer("🎙 <i>Слушаю голосовое и готовлю ответ...</i>", parse_mode=ParseMode.HTML)
    try:
        file_info = await bot.get_file(voice_obj.file_id)
        downloaded = await bot.download_file(file_info.file_path)
        raw_audio = downloaded.read()

        ext_from_tg = os.path.splitext(file_info.file_path or "")[1].lower()
        if not ext_from_tg:
            ext_from_tg = ".ogg" if message.voice else ".mp3"

        recognized_text = ""
        try:
            recognized_text = await transcribe_audio_whisper(raw_audio, filename=f"voice{ext_from_tg}")
        except Exception:
            recognized_text = ""

        extra_caption = (message.caption or "").strip()
        history = await get_history(user_id)

        if recognized_text:
            full_user_prompt = f"{extra_caption}\n\n{recognized_text}".strip() if extra_caption else recognized_text
            if is_content_forbidden(full_user_prompt):
                await refund_quota(user_id, quota_receipt)
                await wait_msg.edit_text("🚫 Запрос отклонён системой безопасности: запрещённый контент.")
                return

            answer_text = await generate_text_response(
                user_id=user_id,
                selected_model=model_id,
                history=history,
                user_text=full_user_prompt,
            )
            log_q = f"[ГС]: {recognized_text}" + (f" (подпись: {extra_caption})" if extra_caption else "")
            await add_history(user_id, "user", full_user_prompt)
            await add_history(user_id, "assistant", answer_text)
            await log_user_request(user_id, req_type_tag, log_q, answer_text, model_used=shown_model)

            async with aiosqlite.connect(DB_PATH) as db:
                await db.execute("UPDATE users SET total_requests = total_requests + 1 WHERE user_id = ?", (user_id,))
                await db.commit()

            await wait_msg.delete()
            full_reply = f"🗣 Вы сказали: {recognized_text}\n\n{answer_text}"
            await send_formatted_answer(message, full_reply)
        else:
            # Резерв: если Whisper вернул 503/404, отправляем аудио через input_audio / base64 во все доступные модели
            mime_audio = getattr(voice_obj, "mime_type", None) or ("audio/ogg" if message.voice else "audio/mpeg")
            b64_audio = base64.b64encode(raw_audio).decode("utf-8")
            audio_prompt = extra_caption or "Внимательно прослушай это голосовое сообщение, кратко передай суть сказанного и дай подробный ответ."
            answer_text = await generate_media_multimodal_response(
                user_id=user_id,
                selected_model=model_id,
                caption=audio_prompt,
                b64_data=b64_audio,
                mime_type=mime_audio,
            )
            log_q = f"[Голосовое сообщение]{': ' + extra_caption if extra_caption else ''}"
            await add_history(user_id, "user", log_q)
            await add_history(user_id, "assistant", answer_text)
            await log_user_request(user_id, req_type_tag, log_q, answer_text, model_used=shown_model)

            async with aiosqlite.connect(DB_PATH) as db:
                await db.execute("UPDATE users SET total_requests = total_requests + 1 WHERE user_id = ?", (user_id,))
                await db.commit()

            await wait_msg.delete()
            await send_formatted_answer(message, answer_text)

    except Exception as e:
        await refund_quota(user_id, quota_receipt)
        err_msg = str(e)
        if "503" in err_msg or "No available accounts" in err_msg or "404" in err_msg:
            human_err = (
                "На сервере API сейчас нет свободных аккаунтов для распознавания аудио "
                f"(<code>{html.escape(err_msg[:140])}</code>). Попробуй чуть позже или напиши текстом / скинь фото."
            )
        else:
            human_err = f"<code>{html.escape(err_msg[:250])}</code>"
        await wait_msg.edit_text(
            f"⚠️ <b>Не удалось обработать голосовое:</b>\n{human_err}",
            parse_mode=ParseMode.HTML,
        )


# ================= ДОКУМЕНТЫ: ТЕКСТОВЫЕ ФАЙЛЫ + ВОССТАНОВЛЕНИЕ БАЗЫ =================
def decode_text_bytes(raw: bytes) -> str:
    for enc in ("utf-8", "utf-8-sig", "cp1251", "latin-1"):
        try:
            return raw.decode(enc)
        except Exception:
            continue
    return raw.decode("utf-8", errors="replace")


@router.message(F.document)
async def handle_document(message: Message, bot: Bot):
    user_id = message.from_user.id
    document = message.document
    fname = document.file_name or ""
    ext = os.path.splitext(fname.lower())[1]

    if user_id == ADMIN_ID and ext in (".db", ".sqlite", ".sqlite3"):
        try:
            file_info = await bot.get_file(document.file_id)
            bytes_file = await bot.download_file(file_info.file_path)

            db_dir = os.path.dirname(os.path.abspath(DB_PATH))
            if db_dir:
                os.makedirs(db_dir, exist_ok=True)

            with open(DB_PATH, "wb") as f:
                f.write(bytes_file.read())

            await init_db()
            await message.answer(
                "✅ <b>База данных успешно восстановлена из файла!</b>\n"
                "Все подписки, пакеты и пользователи на месте.",
                parse_mode=ParseMode.HTML,
            )
        except Exception as e:
            await message.answer(f"❌ <b>Ошибка восстановления:</b> <code>{e}</code>", parse_mode=ParseMode.HTML)
        return

    if ext not in TEXT_FILE_EXTS:
        await message.answer(
            "⚠️ Поддерживаются текстовые файлы и исходный код (<code>.txt</code>, <code>.py</code>, <code>.js</code>, <code>.html</code>, <code>.csv</code>, <code>.json</code>, <code>.md</code>, <code>.sql</code> и др.).",
            parse_mode=ParseMode.HTML,
        )
        return

    if document.file_size and document.file_size > 2 * 1024 * 1024:
        await message.answer("⚠️ Файл слишком большой (максимум 2 МБ).")
        return

    user = await get_user(user_id, full_name=message.from_user.full_name, username=message.from_user.username or "")
    if not await ensure_subscribed(bot, user_id, message):
        return

    model_id = user["selected_model"]
    pro_active = is_pro(user) or (user_id == ADMIN_ID)
    if ALL_MODELS_MAP.get(model_id, {}).get("pro") and not pro_active:
        await message.answer(
            "🔒 Срок подписки истек. Выбери бесплатную модель в /menu или продли тариф:",
            reply_markup=shop_main_kb(),
        )
        return

    quota_receipt = await try_consume_quota(user_id, pro_active, count=1)
    if not quota_receipt:
        await message.answer(
            "⏳ Бесплатный лимит на сегодня и пакет запросов исчерпаны.\n"
            "Приходи завтра, пригласи друга за +2 запроса (/ref) или оформи подписку / пакет:",
            reply_markup=shop_main_kb(),
        )
        return

    wait_msg = await message.answer(f"📄 <i>Читаю файл {html.escape(fname)} и решаю...</i>", parse_mode=ParseMode.HTML)
    try:
        file_info = await bot.get_file(document.file_id)
        downloaded = await bot.download_file(file_info.file_path)
        file_text = decode_text_bytes(downloaded.read()).strip()

        if not file_text:
            raise RuntimeError("Файл пустой")

        if is_content_forbidden(file_text) or is_content_forbidden(message.caption or ""):
            await refund_quota(user_id, quota_receipt)
            await wait_msg.edit_text("🚫 Запрос отклонён системой безопасности: запрещённый контент.")
            return

        if len(file_text) > 18000:
            file_text = file_text[:18000] + "\n\n[...текст файла обрезан до 18 000 символов...]"

        task_caption = (message.caption or "").strip() or "Разбери содержимое этого файла и реши все задания или исправь ошибки."
        combined_prompt = f"Задача от пользователя: {task_caption}\n\nСодержимое файла ({fname}):\n{file_text}"

        history = await get_history(user_id)
        answer_text = await generate_text_response(
            user_id=user_id,
            selected_model=model_id,
            history=history,
            user_text=combined_prompt,
        )

        shown_model = ALL_MODELS_MAP.get(model_id, {}).get("name", model_id)
        doc_log_q = f"[Файл {fname}]: {task_caption}\n{file_text[:600]}"
        await add_history(user_id, "user", f"[Файл {fname}]: {task_caption}\n{file_text[:1500]}")
        await add_history(user_id, "assistant", answer_text)
        await log_user_request(user_id, "📄 Файл", doc_log_q, answer_text, model_used=shown_model)

        async with aiosqlite.connect(DB_PATH) as db:
            await db.execute("UPDATE users SET total_requests = total_requests + 1 WHERE user_id = ?", (user_id,))
            await db.commit()

        await wait_msg.delete()
        await send_formatted_answer(message, answer_text)

    except Exception as e:
        await refund_quota(user_id, quota_receipt)
        await wait_msg.edit_text(
            f"⚠️ <b>Не удалось обработать файл:</b>\n<code>{str(e)[:250]}</code>",
            parse_mode=ParseMode.HTML,
        )


# ================= РУЧНОЙ БЭКАП БАЗЫ ДАННЫХ =================
@router.callback_query(F.data == "adm_backup_now")
async def cb_adm_backup_now(call: CallbackQuery, bot: Bot):
    if call.from_user.id != ADMIN_ID:
        return
    await call.answer("💾 Формирую файл базы...")
    await send_db_backup(bot, reason="Ручной бэкап")


# ================= АДМИН: РАССЫЛКА ПО БАЗЕ =================
@router.callback_query(F.data == "adm_broadcast")
async def cb_adm_broadcast(call: CallbackQuery):
    if call.from_user.id != ADMIN_ID:
        return
    USER_INPUT_STATE[ADMIN_ID] = "adm_broadcast_msg"
    await call.message.edit_text(
        "📢 <b>Рассылка всем пользователям</b>\n\n"
        "Отправь сообщение для рассылки (можно обычный текст с эмодзи или фото с подписью):",
        reply_markup=admin_cancel_kb("admin_panel"),
        parse_mode=ParseMode.HTML,
    )
    await call.answer()


@router.callback_query(F.data == "adm_broadcast_confirm")
async def cb_adm_broadcast_confirm(call: CallbackQuery, bot: Bot):
    if call.from_user.id != ADMIN_ID:
        return
    src_chat = BROADCAST_DRAFT.get("chat_id")
    src_msg = BROADCAST_DRAFT.get("message_id")
    if not src_chat or not src_msg:
        await call.answer("⚠️ Сообщение для рассылки не найдено.", show_alert=True)
        return

    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute("SELECT user_id FROM users") as cur:
            rows = await cur.fetchall()

    user_ids = [r[0] for r in rows]
    total = len(user_ids)
    await call.message.edit_text(f"⏳ <b>Запускаю рассылку на {total} пользователей...</b>", parse_mode=ParseMode.HTML)
    await call.answer()

    sent_ok = 0
    failed = 0
    for uid in user_ids:
        try:
            await bot.copy_message(chat_id=uid, from_chat_id=src_chat, message_id=src_msg)
            sent_ok += 1
        except Exception:
            failed += 1
        await asyncio.sleep(0.05)

    BROADCAST_DRAFT.clear()
    await call.message.answer(
        f"✅ <b>Рассылка завершена!</b>\n\n"
        f"📨 Доставлено: <b>{sent_ok}</b>\n"
        f"🚫 Не доставлено (заблокировали бота): <b>{failed}</b>",
        reply_markup=await admin_kb(),
        parse_mode=ParseMode.HTML,
    )


# ================= АДМИН: ИСТОРИЯ ЗАПРОСОВ ПОЛЬЗОВАТЕЛЕЙ (АНТИ-ДЖЕЙЛБРЕЙК АУДИТ) =================
async def render_req_hist_users_page(page: int = 0) -> tuple[str, InlineKeyboardMarkup]:
    offset = page * USERS_PER_PAGE
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute(
            """
            SELECT COUNT(DISTINCT u.user_id)
            FROM users u
            WHERE u.total_requests > 0
               OR EXISTS (SELECT 1 FROM request_logs rl WHERE rl.user_id = u.user_id)
            """
        ) as cur:
            total = (await cur.fetchone())[0]

        async with db.execute(
            """
            SELECT u.user_id, u.full_name, u.username, u.total_requests,
                   (SELECT COUNT(*) FROM request_logs rl WHERE rl.user_id = u.user_id) AS logged_cnt,
                   (SELECT MAX(created_at) FROM request_logs rl WHERE rl.user_id = u.user_id) AS last_ts
            FROM users u
            WHERE u.total_requests > 0
               OR EXISTS (SELECT 1 FROM request_logs rl WHERE rl.user_id = u.user_id)
            ORDER BY COALESCE(last_ts, 0) DESC, u.total_requests DESC
            LIMIT ? OFFSET ?
            """,
            (USERS_PER_PAGE, offset),
        ) as cur:
            rows = await cur.fetchall()

    if total == 0:
        return (
            "📜 <b>История запросов</b>\n\n<i>Пока ни один пользователь не делал запросов.</i>",
            InlineKeyboardMarkup(
                inline_keyboard=[[InlineKeyboardButton(text="⬅️ В админ-панель", callback_data="admin_panel")]]
            ),
        )

    total_pages = max(1, (total + USERS_PER_PAGE - 1) // USERS_PER_PAGE)
    lines = [
        f"📜 <b>История запросов (стр. {page + 1}/{total_pages}, активных профилей: {total})</b>\n",
        "Выбери профиль ниже, чтобы посмотреть все его текстовые запросы, фото, кружочки и голосовые:\n",
    ]
    buttons = []

    for r in rows:
        uid = r["user_id"]
        name = r["full_name"] or "Без имени"
        uname = f" @{r['username']}" if r["username"] else ""
        cnt = max(r["logged_cnt"] or 0, r["total_requests"] or 0)
        last_str = datetime.fromtimestamp(r["last_ts"]).strftime("%d.%m %H:%M") if r["last_ts"] else "ранее"
        lines.append(f"• <b>{html.escape(name)}</b>{html.escape(uname)} (<code>{uid}</code>) — <b>{cnt}</b> запр. ({last_str})")
        buttons.append([
            InlineKeyboardButton(
                text=f"👤 {name[:20]} | {cnt} запр. ({last_str})",
                callback_data=f"adm_rh_u:{uid}:0:{page}",
            )
        ])

    nav_row = []
    if page > 0:
        nav_row.append(InlineKeyboardButton(text="⬅️ Назад", callback_data=f"adm_req_hist:{page - 1}"))
    if offset + USERS_PER_PAGE < total:
        nav_row.append(InlineKeyboardButton(text="Вперёд ➡️", callback_data=f"adm_req_hist:{page + 1}"))
    if nav_row:
        buttons.append(nav_row)

    buttons.append([InlineKeyboardButton(text="🔍 Найти историю по ID / нику", callback_data="adm_rh_search")])
    buttons.append([InlineKeyboardButton(text="⬅️ В админ-панель", callback_data="admin_panel")])
    return "\n".join(lines), InlineKeyboardMarkup(inline_keyboard=buttons)


async def render_user_req_logs(target_id: int, log_page: int = 0, users_page: int = 0) -> tuple[str, InlineKeyboardMarkup]:
    LOGS_PER_PAGE = 5
    offset = log_page * LOGS_PER_PAGE
    user = await get_user(target_id)
    name = html.escape(user.get("full_name") or "Пользователь")
    uname = f" (@{user['username']})" if user.get("username") else ""

    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute("SELECT COUNT(*) FROM request_logs WHERE user_id = ?", (target_id,)) as cur:
            total_logs = (await cur.fetchone())[0]
        async with db.execute(
            "SELECT * FROM request_logs WHERE user_id = ? ORDER BY id DESC LIMIT ? OFFSET ?",
            (target_id, LOGS_PER_PAGE, offset),
        ) as cur:
            logs = await cur.fetchall()

        # Если детальных логов ещё нет (старые запросы до обновления), подтягиваем из chat_history
        fallback_hist = []
        if total_logs == 0:
            async with db.execute(
                "SELECT role, content FROM chat_history WHERE user_id = ? ORDER BY id DESC LIMIT 10",
                (target_id,),
            ) as cur2:
                fallback_hist = await cur2.fetchall()

    header = (
        f"📜 <b>Запросы пользователя: {name}</b>{uname}\n"
        f"🆔 ID: <code>{target_id}</code> | Всего запросов: <b>{user.get('total_requests', 0)}</b>\n"
    )

    if total_logs == 0 and not fallback_hist:
        body = "\n<i>Детальная история запросов этого пользователя пока пуста (записи появятся после новых сообщений).</i>"
    elif total_logs == 0 and fallback_hist:
        chunks = ["\n<i>Последние сообщения из оперативной памяти чата:</i>\n"]
        for fh in reversed(fallback_hist):
            who = "👤 Запрос" if fh["role"] == "user" else "🤖 Ответ"
            snippet = html.escape((fh["content"] or "")[:320])
            chunks.append(f"<b>{who}:</b> <code>{snippet}</code>")
        body = "\n".join(chunks)
    else:
        total_pages = max(1, (total_logs + LOGS_PER_PAGE - 1) // LOGS_PER_PAGE)
        chunks = [f"📄 Страница <b>{log_page + 1}/{total_pages}</b> (записей в журнале: {total_logs})\n"]
        for item in logs:
            dt_s = datetime.fromtimestamp(item["created_at"]).strftime("%d.%m.%Y %H:%M") if item["created_at"] else ""
            rtype = html.escape(item["req_type"] or "💬 Запрос")
            m_used = f" • <i>{html.escape(item['model_used'])}</i>" if item["model_used"] else ""
            q_txt = html.escape((item["user_query"] or "")[:350])
            a_txt = html.escape((item["bot_reply"] or "")[:220])
            chunks.append(
                f"🕒 <b>{dt_s}</b> | {rtype}{m_used}\n"
                f"👤 <b>Запрос:</b> <code>{q_txt}</code>\n"
                f"🤖 <b>Ответ:</b> {a_txt}\n"
                f"────────────────────"
            )
        body = "\n".join(chunks)

    buttons = []
    if total_logs > 0:
        nav = []
        if log_page > 0:
            nav.append(InlineKeyboardButton(text="⬅️ Новее", callback_data=f"adm_rh_u:{target_id}:{log_page - 1}:{users_page}"))
        if offset + LOGS_PER_PAGE < total_logs:
            nav.append(InlineKeyboardButton(text="Старее ➡️", callback_data=f"adm_rh_u:{target_id}:{log_page + 1}:{users_page}"))
        if nav:
            buttons.append(nav)

    buttons.append([InlineKeyboardButton(text="👤 Открыть карточку профиля", callback_data=f"adm_u_view:{target_id}:{users_page}")])
    buttons.append([InlineKeyboardButton(text="⬅️ К списку профилей", callback_data=f"adm_req_hist:{users_page}")])

    full_text = header + body
    if len(full_text) > 4000:
        full_text = full_text[:3980] + "..."
    return full_text, InlineKeyboardMarkup(inline_keyboard=buttons)


@router.callback_query(F.data.startswith("adm_req_hist:"))
async def cb_adm_req_hist(call: CallbackQuery):
    if call.from_user.id != ADMIN_ID:
        return
    USER_INPUT_STATE.pop(ADMIN_ID, None)
    page = int(call.data.split(":", 1)[1])
    text, kb = await render_req_hist_users_page(page)
    try:
        await call.message.edit_text(text, reply_markup=kb, parse_mode=ParseMode.HTML)
    except TelegramBadRequest:
        pass
    await call.answer()


@router.callback_query(F.data == "adm_rh_search")
async def cb_adm_rh_search(call: CallbackQuery):
    if call.from_user.id != ADMIN_ID:
        return
    USER_INPUT_STATE[ADMIN_ID] = "adm_rh_search"
    await call.message.edit_text(
        "🔍 <b>Поиск истории запросов</b>\n\n"
        "Отправь <b>ID пользователя</b>, его <b>@username</b> или часть <b>имени</b>:",
        reply_markup=admin_cancel_kb("adm_req_hist:0"),
        parse_mode=ParseMode.HTML,
    )
    await call.answer()


@router.callback_query(F.data.startswith("adm_rh_u:"))
async def cb_adm_rh_u(call: CallbackQuery):
    if call.from_user.id != ADMIN_ID:
        return
    USER_INPUT_STATE.pop(ADMIN_ID, None)
    _, uid_s, lpage_s, upage_s = call.data.split(":")
    text, kb = await render_user_req_logs(int(uid_s), int(lpage_s), int(upage_s))
    try:
        await call.message.edit_text(text, reply_markup=kb, parse_mode=ParseMode.HTML)
    except TelegramBadRequest:
        pass
    await call.answer()


# ================= АДМИН: УПРАВЛЕНИЕ ПОЛЬЗОВАТЕЛЯМИ =================
async def render_users_list_page(page: int = 0) -> tuple[str, InlineKeyboardMarkup]:
    offset = page * USERS_PER_PAGE
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute("SELECT COUNT(*) FROM users") as cur:
            total = (await cur.fetchone())[0]
        async with db.execute(
            "SELECT * FROM users ORDER BY total_requests DESC, user_id DESC LIMIT ? OFFSET ?",
            (USERS_PER_PAGE, offset),
        ) as cur:
            rows = await cur.fetchall()

    total_pages = max(1, (total + USERS_PER_PAGE - 1) // USERS_PER_PAGE)
    lines = [
        f"👥 <b>База пользователей (стр. {page + 1}/{total_pages}, всего: {total})</b>\n",
        "Нажми на пользователя, чтобы посмотреть статистику, покупки, выдать или забрать подписку / запросы:\n",
    ]
    buttons = []
    now = time.time()

    for r in rows:
        uid = r["user_id"]
        name = r["full_name"] or "Без имени"
        badge = "👑" if (r["pro_until"] or 0) > now else "🆓"
        reqs = r["total_requests"] or 0
        lines.append(f"{badge} <b>{html.escape(name)}</b> (<code>{uid}</code>) — {reqs} запр.")
        buttons.append([
            InlineKeyboardButton(
                text=f"{badge} {name[:22]} | ID {uid} ({reqs} запр.)",
                callback_data=f"adm_u_view:{uid}:{page}",
            )
        ])

    nav_row = []
    if page > 0:
        nav_row.append(InlineKeyboardButton(text="⬅️ Назад", callback_data=f"adm_users:{page - 1}"))
    if offset + USERS_PER_PAGE < total:
        nav_row.append(InlineKeyboardButton(text="Вперёд ➡️", callback_data=f"adm_users:{page + 1}"))
    if nav_row:
        buttons.append(nav_row)

    buttons.append([InlineKeyboardButton(text="🔍 Найти по ID или имени", callback_data="adm_u_search")])
    buttons.append([InlineKeyboardButton(text="⬅️ В админ-панель", callback_data="admin_panel")])

    return "\n".join(lines), InlineKeyboardMarkup(inline_keyboard=buttons)


async def render_user_card(target_id: int, back_page: int = 0) -> tuple[str, InlineKeyboardMarkup]:
    user = await get_user(target_id)
    now = time.time()
    pro_active = is_pro(user)

    if pro_active:
        if user["pro_until"] > now + 365 * 5 * 86400:
            sub_str = "👑 <b>Активна (НАВСЕГДА)</b>"
        else:
            exp = datetime.fromtimestamp(user["pro_until"]).strftime("%d.%m.%Y %H:%M")
            sub_str = f"👑 <b>Активна до {exp}</b>"
    else:
        sub_str = "🆓 <b>Не активна</b>"

    if has_active_discount(user):
        d_exp = datetime.fromtimestamp(user["discount_until"]).strftime("%d.%m %H:%M")
        disc_str = f"🔥 <b>Активна {DISCOUNT_PERCENT}% (до {d_exp})</b>"
    elif user.get("discount_offered"):
        disc_str = "⏳ Истекла"
    else:
        disc_str = "🕒 Ожидает (через 2ч после старта)"

    total_daily = FREE_DAILY_LIMIT + user["bonus_limit"]
    left_today = max(0, total_daily - user["used_today"])
    uname_str = f" (@{user['username']})" if user.get("username") else ""
    joined_str = (
        datetime.fromtimestamp(user["joined_at"]).strftime("%d.%m.%Y %H:%M")
        if user.get("joined_at")
        else "неизвестно"
    )

    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute(
            "SELECT COUNT(*) FROM users WHERE referred_by = ? AND ref_rewarded = 1",
            (target_id,),
        ) as cur:
            refs_count = (await cur.fetchone())[0]

        async with db.execute(
            "SELECT title, stars, rub_amount, method, paid_at FROM payments WHERE user_id = ? ORDER BY paid_at DESC LIMIT 10",
            (target_id,),
        ) as cur:
            pay_rows = await cur.fetchall()

        async with db.execute(
            "SELECT COALESCE(SUM(stars), 0) FROM payments WHERE user_id = ?",
            (target_id,),
        ) as cur:
            total_stars = (await cur.fetchone())[0]

        async with db.execute(
            "SELECT COALESCE(SUM(rub_amount), 0) FROM payments WHERE user_id = ? AND method = 'sbp'",
            (target_id,),
        ) as cur:
            total_sbp_rub = (await cur.fetchone())[0]

    if pay_rows:
        pay_lines = []
        for p in pay_rows:
            p_date = datetime.fromtimestamp(p["paid_at"]).strftime("%d.%m.%y %H:%M")
            if p["method"] == "sbp":
                val_str = f"{p['rub_amount']:.0f} ₽ (СБП)"
            else:
                val_str = f"{p['stars']} ⭐"
            pay_lines.append(f"  • {html.escape(p['title'])} — <b>{val_str}</b> ({p_date})")
        payments_block = "\n".join(pay_lines)
    else:
        payments_block = "  <i>Покупок пока нет</i>"

    cur_model = ALL_MODELS_MAP.get(user["selected_model"], {}).get("name", user["selected_model"])
    ref_by = f"<code>{user['referred_by']}</code>" if user.get("referred_by") else "сам пришёл"
    ref_bal = user.get("ref_balance") or 0.0
    ref_earned = user.get("ref_total_earned") or 0.0

    text = (
        f"👤 <b>Карточка пользователя</b>\n\n"
        f"📛 Имя: <b>{html.escape(user.get('full_name') or 'Пользователь')}</b>{uname_str}\n"
        f"🆔 ID: <code>{target_id}</code>\n"
        f"📅 В боте с: <b>{joined_str}</b>\n"
        f"🔗 Пригласил: {ref_by} | Привёл друзей: <b>{refs_count}</b>\n"
        f"💸 Реф. баланс: <b>{ref_bal:.2f} ₽</b> (всего: {ref_earned:.2f} ₽)\n\n"
        f"💎 Подписка: {sub_str}\n"
        f"🏷 Скидка {DISCOUNT_PERCENT}%: {disc_str}\n"
        f"🤖 Модель: <b>{cur_model}</b>\n"
        f"⚡ Запросы сегодня: <b>{user['used_today']}/{total_daily}</b> (осталось {left_today})\n"
        f"📦 Запросы из пакета: <b>{user.get('extra_requests', 0)} шт.</b>\n"
        f"🎁 Бонус к дневному лимиту: <b>+{user['bonus_limit']} в день</b>\n"
        f"📊 Всего запросов за всё время: <b>{user.get('total_requests', 0)}</b>\n\n"
        f"💳 <b>История покупок (СБП: {total_sbp_rub:.0f} ₽ | Stars: {total_stars} ⭐):</b>\n"
        f"{payments_block}"
    )

    kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="👑 +1 дн.", callback_data=f"adm_u_pro:{target_id}:1:{back_page}"),
                InlineKeyboardButton(text="👑 +7 дн.", callback_data=f"adm_u_pro:{target_id}:7:{back_page}"),
                InlineKeyboardButton(text="👑 +30 дн.", callback_data=f"adm_u_pro:{target_id}:30:{back_page}"),
            ],
            [
                InlineKeyboardButton(text="♾ PRO навсегда", callback_data=f"adm_u_pro:{target_id}:3650:{back_page}"),
                InlineKeyboardButton(text="✏️ Свой срок PRO", callback_data=f"adm_u_pro_cust:{target_id}:{back_page}"),
            ],
            [
                InlineKeyboardButton(text="⚡ +10 запр.", callback_data=f"adm_u_req:{target_id}:10:{back_page}"),
                InlineKeyboardButton(text="⚡ +50 запр.", callback_data=f"adm_u_req:{target_id}:50:{back_page}"),
                InlineKeyboardButton(text="✏️ Выдать запр.", callback_data=f"adm_u_req_cust:{target_id}:{back_page}"),
            ],
            [
                InlineKeyboardButton(text="➖ -10 запр.", callback_data=f"adm_u_subreq:{target_id}:10:{back_page}"),
                InlineKeyboardButton(text="➖ Снять запр.", callback_data=f"adm_u_subreq_cust:{target_id}:{back_page}"),
                InlineKeyboardButton(text="🗑 Обнулить пакет", callback_data=f"adm_u_clearreq:{target_id}:{back_page}"),
            ],
            [
                InlineKeyboardButton(text="❌ Снять PRO", callback_data=f"adm_u_delpro:{target_id}:{back_page}"),
                InlineKeyboardButton(text="🔄 Сброс дня", callback_data=f"adm_u_resetday:{target_id}:{back_page}"),
            ],
            [InlineKeyboardButton(text="⬅️ К списку пользователей", callback_data=f"adm_users:{back_page}")],
        ]
    )
    return text, kb


@router.callback_query(F.data.startswith("adm_users:"))
async def cb_adm_users(call: CallbackQuery):
    if call.from_user.id != ADMIN_ID:
        return
    USER_INPUT_STATE.pop(ADMIN_ID, None)
    page = int(call.data.split(":", 1)[1])
    text, kb = await render_users_list_page(page)
    try:
        await call.message.edit_text(text, reply_markup=kb, parse_mode=ParseMode.HTML)
    except TelegramBadRequest:
        pass
    await call.answer()


@router.callback_query(F.data == "adm_u_search")
async def cb_adm_u_search(call: CallbackQuery):
    if call.from_user.id != ADMIN_ID:
        return
    USER_INPUT_STATE[ADMIN_ID] = "adm_u_search"
    await call.message.edit_text(
        "🔍 <b>Поиск пользователя</b>\n\n"
        "Отправь числовой <b>ID пользователя</b>, его <b>@username</b> или часть <b>имени</b>:",
        reply_markup=admin_cancel_kb("adm_users:0"),
        parse_mode=ParseMode.HTML,
    )
    await call.answer()


@router.callback_query(F.data.startswith("adm_u_view:"))
async def cb_adm_u_view(call: CallbackQuery):
    if call.from_user.id != ADMIN_ID:
        return
    USER_INPUT_STATE.pop(ADMIN_ID, None)
    _, uid_s, page_s = call.data.split(":")
    text, kb = await render_user_card(int(uid_s), int(page_s))
    try:
        await call.message.edit_text(text, reply_markup=kb, parse_mode=ParseMode.HTML)
    except TelegramBadRequest:
        pass
    await call.answer()


@router.callback_query(F.data.startswith("adm_u_pro:"))
async def cb_adm_u_pro(call: CallbackQuery, bot: Bot):
    if call.from_user.id != ADMIN_ID:
        return
    _, uid_s, days_s, page_s = call.data.split(":")
    target_id, days, page = int(uid_s), int(days_s), int(page_s)
    target = await get_user(target_id)
    new_until = max(time.time(), target["pro_until"]) + days * 86400
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("UPDATE users SET pro_until = ? WHERE user_id = ?", (new_until, target_id))
        await db.commit()
    await call.answer(f"👑 Выдано +{days} дн. PRO!")
    try:
        msg_days = "НАВСЕГДА" if days >= 3650 else f"на {days} дн."
        await bot.send_message(target_id, f"🎁 Администратор выдал тебе <b>подписку {msg_days}!</b> Открой /menu.", parse_mode=ParseMode.HTML)
    except Exception:
        pass
    text, kb = await render_user_card(target_id, page)
    await call.message.edit_text(text, reply_markup=kb, parse_mode=ParseMode.HTML)


@router.callback_query(F.data.startswith("adm_u_pro_cust:"))
async def cb_adm_u_pro_cust(call: CallbackQuery):
    if call.from_user.id != ADMIN_ID:
        return
    _, uid_s, page_s = call.data.split(":")
    USER_INPUT_STATE[ADMIN_ID] = f"adm_u_pro_cust:{uid_s}:{page_s}"
    await call.message.edit_text(
        f"👑 Введи количество дней подписки числом для пользователя <code>{uid_s}</code>:",
        reply_markup=admin_cancel_kb(f"adm_u_view:{uid_s}:{page_s}"),
        parse_mode=ParseMode.HTML,
    )
    await call.answer()


@router.callback_query(F.data.startswith("adm_u_req:"))
async def cb_adm_u_req(call: CallbackQuery, bot: Bot):
    if call.from_user.id != ADMIN_ID:
        return
    _, uid_s, amount_s, page_s = call.data.split(":")
    target_id, amount, page = int(uid_s), int(amount_s), int(page_s)
    await get_user(target_id)
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("UPDATE users SET extra_requests = extra_requests + ? WHERE user_id = ?", (amount, target_id))
        await db.commit()
    await call.answer(f"⚡ Начислено +{amount} запросов!")
    try:
        await bot.send_message(target_id, f"🎁 Администратор начислил тебе <b>пакет на +{amount} запросов!</b>", parse_mode=ParseMode.HTML)
    except Exception:
        pass
    text, kb = await render_user_card(target_id, page)
    await call.message.edit_text(text, reply_markup=kb, parse_mode=ParseMode.HTML)


@router.callback_query(F.data.startswith("adm_u_req_cust:"))
async def cb_adm_u_req_cust(call: CallbackQuery):
    if call.from_user.id != ADMIN_ID:
        return
    _, uid_s, page_s = call.data.split(":")
    USER_INPUT_STATE[ADMIN_ID] = f"adm_u_req_cust:{uid_s}:{page_s}"
    await call.message.edit_text(
        f"⚡ Введи количество запросов для начисления пользователю <code>{uid_s}</code>:",
        reply_markup=admin_cancel_kb(f"adm_u_view:{uid_s}:{page_s}"),
        parse_mode=ParseMode.HTML,
    )
    await call.answer()


@router.callback_query(F.data.startswith("adm_u_subreq:"))
async def cb_adm_u_subreq(call: CallbackQuery, bot: Bot):
    if call.from_user.id != ADMIN_ID:
        return
    _, uid_s, amount_s, page_s = call.data.split(":")
    target_id, amount, page = int(uid_s), int(amount_s), int(page_s)
    user = await get_user(target_id)
    cur_extra = user.get("extra_requests", 0)
    removed = min(cur_extra, amount)
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("UPDATE users SET extra_requests = MAX(0, extra_requests - ?) WHERE user_id = ?", (amount, target_id))
        await db.commit()
    await call.answer(f"➖ Списано {removed} запросов из пакета")
    if removed > 0:
        try:
            await bot.send_message(
                target_id,
                f"⚠️ Администратор забрал у тебя <b>{removed} запросов</b> из пакета.",
                parse_mode=ParseMode.HTML,
            )
        except Exception:
            pass
    text, kb = await render_user_card(target_id, page)
    await call.message.edit_text(text, reply_markup=kb, parse_mode=ParseMode.HTML)


@router.callback_query(F.data.startswith("adm_u_subreq_cust:"))
async def cb_adm_u_subreq_cust(call: CallbackQuery):
    if call.from_user.id != ADMIN_ID:
        return
    _, uid_s, page_s = call.data.split(":")
    USER_INPUT_STATE[ADMIN_ID] = f"adm_u_subreq_cust:{uid_s}:{page_s}"
    await call.message.edit_text(
        f"➖ Введи количество запросов, которое нужно забрать у пользователя <code>{uid_s}</code>:",
        reply_markup=admin_cancel_kb(f"adm_u_view:{uid_s}:{page_s}"),
        parse_mode=ParseMode.HTML,
    )
    await call.answer()


@router.callback_query(F.data.startswith("adm_u_clearreq:"))
async def cb_adm_u_clearreq(call: CallbackQuery, bot: Bot):
    if call.from_user.id != ADMIN_ID:
        return
    _, uid_s, page_s = call.data.split(":")
    target_id, page = int(uid_s), int(page_s)
    user = await get_user(target_id)
    cur_extra = user.get("extra_requests", 0)
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("UPDATE users SET extra_requests = 0 WHERE user_id = ?", (target_id,))
        await db.commit()
    await call.answer("🗑 Пакет запросов обнулён")
    if cur_extra > 0:
        try:
            await bot.send_message(
                target_id,
                f"⚠️ Администратор забрал у тебя все запросы из пакета (<b>{cur_extra} шт.</b>).",
                parse_mode=ParseMode.HTML,
            )
        except Exception:
            pass
    text, kb = await render_user_card(target_id, page)
    await call.message.edit_text(text, reply_markup=kb, parse_mode=ParseMode.HTML)


@router.callback_query(F.data.startswith("adm_u_delpro:"))
async def cb_adm_u_delpro(call: CallbackQuery, bot: Bot):
    if call.from_user.id != ADMIN_ID:
        return
    _, uid_s, page_s = call.data.split(":")
    target_id, page = int(uid_s), int(page_s)
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("UPDATE users SET pro_until = 0 WHERE user_id = ?", (target_id,))
        await db.commit()
    await call.answer("❌ Подписка снята")
    try:
        await bot.send_message(
            target_id,
            "⚠️ Администратор забрал твою <b>PRO-подписку</b>.",
            parse_mode=ParseMode.HTML,
        )
    except Exception:
        pass
    text, kb = await render_user_card(target_id, page)
    await call.message.edit_text(text, reply_markup=kb, parse_mode=ParseMode.HTML)


@router.callback_query(F.data.startswith("adm_u_resetday:"))
async def cb_adm_u_resetday(call: CallbackQuery):
    if call.from_user.id != ADMIN_ID:
        return
    _, uid_s, page_s = call.data.split(":")
    target_id, page = int(uid_s), int(page_s)
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("UPDATE users SET used_today = 0 WHERE user_id = ?", (target_id,))
        await db.commit()
    await call.answer("🔄 Дневной счётчик запросов обнулён")
    text, kb = await render_user_card(target_id, page)
    await call.message.edit_text(text, reply_markup=kb, parse_mode=ParseMode.HTML)


# ================= ПРОВЕРКА ПОДПИСКИ CALLBACK =================
@router.callback_query(F.data == "check_sub")
async def cb_check_sub(call: CallbackQuery, bot: Bot):
    user = await get_user(call.from_user.id, full_name=call.from_user.full_name, username=call.from_user.username or "")
    if await check_channel_sub(bot, call.from_user.id):
        await reward_referrer_if_needed(call.from_user.id, bot)
        cur_model_name = ALL_MODELS_MAP.get(user["selected_model"], {}).get("name", user["selected_model"])
        await call.message.edit_text(
            f"✅ <b>Подписка подтверждена!</b>\n\n"
            f"📊 Статус: <b>{format_status(user)}</b>\n"
            f"🤖 Активная модель: <b>{cur_model_name}</b>",
            reply_markup=categories_kb(call.from_user.id),
            parse_mode=ParseMode.HTML,
        )
        await call.answer("Добро пожаловать!")
    else:
        await call.answer("❌ Вы ещё не подписались на канал!", show_alert=True)


# ================= ПРОФИЛЬ И ПРОМОКОДЫ (ПОЛЬЗОВАТЕЛЬ) =================
async def render_profile_text(user_id: int, first_name: str) -> str:
    user = await get_user(user_id)
    pro_active = is_pro(user)
    cur_model_name = ALL_MODELS_MAP.get(user["selected_model"], {}).get("name", user["selected_model"])
    total_limit = FREE_DAILY_LIMIT + user["bonus_limit"]
    left = max(0, total_limit - user["used_today"])
    extra = user.get("extra_requests", 0)
    ref_bal = user.get("ref_balance") or 0.0

    if pro_active:
        if user["pro_until"] > time.time() + 365 * 5 * 86400:
            sub_block = "👑 Подписка: <b>Активна (Навсегда)</b>"
        else:
            exp_str = datetime.fromtimestamp(user["pro_until"]).strftime("%d.%m.%Y %H:%M")
            sub_block = f"👑 Подписка: <b>Активна (до {exp_str})</b>"
        req_block = f"⚡ Дневные запросы: <b>Безлимит</b> (сегодня: {user['used_today']})"
    else:
        sub_block = "🆓 Подписка: <b>Не активна (Бесплатный тариф)</b>"
        req_block = (
            f"⚡ Дневные запросы: <b>осталось {left} из {total_limit}</b>\n"
            f"🎁 Бонус за друзей/промо: <b>+{user['bonus_limit']} в день</b>"
        )

    disc_line = ""
    disc_info = await get_effective_discount(user)
    if disc_info["active"]:
        d_exp = datetime.fromtimestamp(disc_info["until"]).strftime("%d.%m %H:%M")
        d_label = "Глобальная скидка" if disc_info["is_global"] else "Персональная скидка"
        disc_line = f"\n🔥 {d_label} {disc_info['percent']}%: <b>Активна до {d_exp}</b>"

    return (
        f"👤 <b>Профиль — {html.escape(first_name)}</b>\n\n"
        f"🆔 Твой ID: <code>{user_id}</code>\n"
        f"{sub_block}\n"
        f"{req_block}\n"
        f"📦 Запросы из пакета: <b>{extra} шт.</b>\n"
        f"💸 Партнёрский баланс: <b>{ref_bal:.2f} ₽</b>\n"
        f"🤖 Выбранная модель: <b>{cur_model_name}</b>"
        f"{disc_line}"
    )


@router.message(Command("profile"))
async def cmd_profile(message: Message, bot: Bot):
    USER_INPUT_STATE.pop(message.from_user.id, None)
    await get_user(message.from_user.id, full_name=message.from_user.full_name, username=message.from_user.username or "")
    if not await ensure_subscribed(bot, message.from_user.id, message):
        return
    text = await render_profile_text(message.from_user.id, message.from_user.first_name)
    await message.answer(text, reply_markup=profile_kb(), parse_mode=ParseMode.HTML)


@router.callback_query(F.data == "profile")
async def cb_profile(call: CallbackQuery, bot: Bot):
    USER_INPUT_STATE.pop(call.from_user.id, None)
    if not await ensure_subscribed(bot, call.from_user.id, call.message):
        await call.answer()
        return
    text = await render_profile_text(call.from_user.id, call.from_user.first_name)
    try:
        await call.message.edit_text(text, reply_markup=profile_kb(), parse_mode=ParseMode.HTML)
    except TelegramBadRequest:
        pass
    await call.answer()


@router.callback_query(F.data == "promo_enter")
async def cb_promo_enter(call: CallbackQuery):
    USER_INPUT_STATE[call.from_user.id] = "promo_activate"
    await call.message.edit_text(
        "🎟 <b>Активация промокода</b>\n\n"
        "Отправь промокод в чат одним сообщением:",
        reply_markup=InlineKeyboardMarkup(
            inline_keyboard=[[InlineKeyboardButton(text="❌ Отмена", callback_data="profile")]]
        ),
        parse_mode=ParseMode.HTML,
    )
    await call.answer()


async def redeem_promocode(user_id: int, raw_code: str) -> tuple[bool, str]:
    code = raw_code.strip().upper()
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute("SELECT * FROM promocodes WHERE code = ?", (code,)) as cur:
            promo = await cur.fetchone()

        if not promo:
            return False, "❌ Промокод не найден или введён с ошибкой."

        if promo["max_uses"] > 0 and promo["used_count"] >= promo["max_uses"]:
            return False, "⏳ Лимит активаций этого промокода уже исчерпан."

        async with db.execute(
            "SELECT 1 FROM promo_uses WHERE user_id = ? AND code = ?",
            (user_id, code),
        ) as cur:
            if await cur.fetchone():
                return False, "⚠️ Ты уже активировал этот промокод ранее."

        await get_user(user_id)
        await db.execute("INSERT INTO promo_uses (user_id, code) VALUES (?, ?)", (user_id, code))
        await db.execute("UPDATE promocodes SET used_count = used_count + 1 WHERE code = ?", (code,))

        if promo["reward_type"] == "sub":
            days = promo["amount"]
            async with db.execute("SELECT pro_until FROM users WHERE user_id = ?", (user_id,)) as cur:
                cur_until = (await cur.fetchone())[0]
            new_until = max(time.time(), cur_until) + days * 86400
            await db.execute("UPDATE users SET pro_until = ? WHERE user_id = ?", (new_until, user_id))
            await db.commit()
            if days >= 3650:
                return True, f"🎉 Промокод <code>{code}</code> активирован! Тебе выдана <b>подписка НАВСЕГДА</b>!"
            exp_str = datetime.fromtimestamp(new_until).strftime("%d.%m.%Y %H:%M")
            return True, f"🎉 Промокод <code>{code}</code> активирован! Выдана подписка на <b>{days} дн.</b> (до {exp_str})."
        else:
            bonus = promo["amount"]
            await db.execute("UPDATE users SET extra_requests = extra_requests + ? WHERE user_id = ?", (bonus, user_id))
            await db.commit()
            return True, f"🎉 Промокод <code>{code}</code> активирован! Начислен <b>пакет на +{bonus} запросов</b>."


# ================= АДМИН-ПАНЕЛЬ И КОНСТРУКТОР ПРОМОКОДОВ =================
async def render_admin_text() -> str:
    today_str = str(date.today())
    engine = await get_engine_model()
    g_disc = await get_global_discount()
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute("SELECT COUNT(*) FROM users") as cur:
            total_users = (await cur.fetchone())[0]
        async with db.execute("SELECT COUNT(*) FROM users WHERE pro_until > ?", (time.time(),)) as cur:
            pro_users = (await cur.fetchone())[0]
        async with db.execute("SELECT SUM(used_today) FROM users WHERE last_reset = ?", (today_str,)) as cur:
            today_reqs = (await cur.fetchone())[0] or 0
        async with db.execute("SELECT COUNT(*) FROM promocodes") as cur:
            promos_count = (await cur.fetchone())[0]
        async with db.execute("SELECT COALESCE(SUM(stars), 0) FROM payments") as cur:
            total_stars = (await cur.fetchone())[0]
        async with db.execute("SELECT COALESCE(SUM(rub_amount), 0) FROM payments WHERE method = 'sbp'") as cur:
            total_sbp_rub = (await cur.fetchone())[0]
        async with db.execute("SELECT COUNT(*) FROM withdrawals WHERE status = 'pending'") as cur:
            pending_w = (await cur.fetchone())[0]

    platega_status = "🟢 Подключена" if (PLATEGA_MERCHANT_ID and PLATEGA_SECRET) else "🔴 Не заданы ключи"
    if g_disc["active"]:
        g_exp = datetime.fromtimestamp(g_disc["until"]).strftime("%d.%m.%Y %H:%M")
        g_disc_status = f"🔥 <b>-{g_disc['percent']}%</b> (до {g_exp})"
    else:
        g_disc_status = "⚪ Выключена"

    return (
        "🛠 <b>Админ-панель управления</b>\n\n"
        f"💳 Platega СБП: <b>{platega_status}</b>\n"
        f"🔥 Глобальная скидка: {g_disc_status}\n"
        f"⚙️ Общий движок (текст и фото): <code>{engine}</code>\n"
        f"👥 Всего пользователей: <b>{total_users}</b>\n"
        f"💎 Активных подписок: <b>{pro_users}</b>\n"
        f"💰 Касса СБП: <b>{total_sbp_rub:.0f} ₽</b> | Stars: <b>{total_stars} ⭐</b>\n"
        f"💸 Заявок на вывод: <b>{pending_w} шт.</b>\n"
        f"🎟 Создано промокодов: <b>{promos_count}</b>\n"
        f"⚡ Запросов сегодня: <b>{today_reqs}</b>\n\n"
        "<i>Быстрые команды:\n"
        "<code>/givepro ID ДНИ</code> — выдать подписку\n"
        "<code>/delpro ID</code> — снять подписку</i>"
    )


@router.message(Command("admin"))
async def cmd_admin(message: Message):
    if message.from_user.id != ADMIN_ID:
        return
    USER_INPUT_STATE.pop(ADMIN_ID, None)
    await message.answer(await render_admin_text(), reply_markup=await admin_kb(), parse_mode=ParseMode.HTML)


@router.callback_query(F.data == "admin_panel")
async def cb_admin_panel(call: CallbackQuery):
    if call.from_user.id != ADMIN_ID:
        return
    USER_INPUT_STATE.pop(ADMIN_ID, None)
    try:
        await call.message.edit_text(await render_admin_text(), reply_markup=await admin_kb(), parse_mode=ParseMode.HTML)
    except TelegramBadRequest:
        pass
    await call.answer()


# ================= АДМИН: ГЛОБАЛЬНАЯ СКИДКА ДЛЯ ВСЕХ ПОЛЬЗОВАТЕЛЕЙ =================
def format_duration_ru(seconds: int) -> str:
    days = seconds // 86400
    hours = (seconds % 86400) // 3600
    parts = []
    if days > 0:
        parts.append(f"{days} дн.")
    if hours > 0:
        parts.append(f"{hours} ч.")
    return " ".join(parts) if parts else f"{max(1, seconds // 60)} мин."


def parse_duration_to_seconds(raw: str) -> int | None:
    """Парсит срок вида '3д', '12ч', '2д 6ч', '48' (часов по умолчанию) в секунды."""
    s = raw.strip().lower()
    if not s:
        return None
    if s.isdigit():
        hrs = int(s)
        return hrs * 3600 if hrs > 0 else None

    total_sec = 0
    matched = False
    for num_s, unit in re.findall(r"(\d+)\s*([дdчhмm]?)", s):
        val = int(num_s)
        if val <= 0:
            continue
        matched = True
        if unit in ("д", "d"):
            total_sec += val * 86400
        elif unit in ("м", "m"):
            total_sec += val * 60
        else:
            total_sec += val * 3600
    return total_sec if (matched and total_sec > 0) else None


async def render_gdisc_menu() -> tuple[str, InlineKeyboardMarkup]:
    g_disc = await get_global_discount()
    buttons = []
    if g_disc["active"]:
        exp_str = datetime.fromtimestamp(g_disc["until"]).strftime("%d.%m.%Y %H:%M")
        rem_sec = max(0, int(g_disc["until"] - time.time()))
        status_block = (
            f"🟢 <b>Сейчас активна глобальная скидка: -{g_disc['percent']}%</b>\n"
            f"⏳ Действует до: <b>{exp_str}</b> (осталось {format_duration_ru(rem_sec)})\n\n"
        )
        buttons.append([InlineKeyboardButton(text="🛑 Выключить глобальную скидку", callback_data="adm_gdisc_off")])
    else:
        status_block = "⚪ <b>Сейчас глобальная скидка выключена.</b>\n\n"

    buttons.append([InlineKeyboardButton(text="🔥 Запустить / изменить глобальную скидку", callback_data="adm_gdisc_start")])
    buttons.append([InlineKeyboardButton(text="⬅️ В админ-панель", callback_data="admin_panel")])

    text = (
        "🔥 <b>Управление глобальной скидкой</b>\n\n"
        f"{status_block}"
        "Глобальная скидка действует <b>сразу для всех пользователей бота</b> на все подписки и пакеты запросов (от 5 ₽)."
    )
    return text, InlineKeyboardMarkup(inline_keyboard=buttons)


@router.callback_query(F.data == "adm_gdisc_menu")
async def cb_adm_gdisc_menu(call: CallbackQuery):
    if call.from_user.id != ADMIN_ID:
        return
    USER_INPUT_STATE.pop(ADMIN_ID, None)
    text, kb = await render_gdisc_menu()
    try:
        await call.message.edit_text(text, reply_markup=kb, parse_mode=ParseMode.HTML)
    except TelegramBadRequest:
        pass
    await call.answer()


@router.callback_query(F.data == "adm_gdisc_off")
async def cb_adm_gdisc_off(call: CallbackQuery):
    if call.from_user.id != ADMIN_ID:
        return
    await set_setting("global_discount_percent", "0")
    await set_setting("global_discount_until", "0")
    await call.answer("🛑 Глобальная скидка выключена!", show_alert=True)
    text, kb = await render_gdisc_menu()
    try:
        await call.message.edit_text(text, reply_markup=kb, parse_mode=ParseMode.HTML)
    except TelegramBadRequest:
        pass


@router.callback_query(F.data == "adm_gdisc_start")
async def cb_adm_gdisc_start(call: CallbackQuery):
    if call.from_user.id != ADMIN_ID:
        return
    GLOBAL_DISCOUNT_DRAFT.clear()
    USER_INPUT_STATE[ADMIN_ID] = "adm_gdisc_pct"
    kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="15%", callback_data="adm_gdisc_pct:15"),
                InlineKeyboardButton(text="20%", callback_data="adm_gdisc_pct:20"),
                InlineKeyboardButton(text="30%", callback_data="adm_gdisc_pct:30"),
            ],
            [
                InlineKeyboardButton(text="40%", callback_data="adm_gdisc_pct:40"),
                InlineKeyboardButton(text="50%", callback_data="adm_gdisc_pct:50"),
                InlineKeyboardButton(text="70%", callback_data="adm_gdisc_pct:70"),
            ],
            [InlineKeyboardButton(text="❌ Отмена", callback_data="adm_gdisc_menu")],
        ]
    )
    await call.message.edit_text(
        "🔥 <b>Глобальная скидка — Шаг 1/2 (Процент)</b>\n\n"
        "Выбери процент скидки кнопкой ниже или <b>введи своё число от 1 до 95</b> (например: <code>25</code>):",
        reply_markup=kb,
        parse_mode=ParseMode.HTML,
    )
    await call.answer()


async def show_gdisc_step2_duration(target_msg: Message, edit: bool = True):
    pct = GLOBAL_DISCOUNT_DRAFT.get("percent", 20)
    USER_INPUT_STATE[ADMIN_ID] = "adm_gdisc_dur"
    kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="6 часов", callback_data="adm_gdisc_dur:21600"),
                InlineKeyboardButton(text="12 часов", callback_data="adm_gdisc_dur:43200"),
                InlineKeyboardButton(text="24 часа (1 дн.)", callback_data="adm_gdisc_dur:86400"),
            ],
            [
                InlineKeyboardButton(text="2 дня (48 ч.)", callback_data="adm_gdisc_dur:172800"),
                InlineKeyboardButton(text="3 дня (72 ч.)", callback_data="adm_gdisc_dur:259200"),
                InlineKeyboardButton(text="7 дней", callback_data="adm_gdisc_dur:604800"),
            ],
            [InlineKeyboardButton(text="❌ Отмена", callback_data="adm_gdisc_menu")],
        ]
    )
    text = (
        f"⏳ <b>Глобальная скидка {pct}% — Шаг 2/2 (Срок действия)</b>\n\n"
        "Выбери длительность акции кнопкой ниже или <b>введи свой срок текстом</b>:\n"
        "• <code>12ч</code> — на 12 часов\n"
        "• <code>3д</code> — на 3 дня\n"
        "• <code>2д 12ч</code> — на 2 дня и 12 часов"
    )
    if edit:
        await target_msg.edit_text(text, reply_markup=kb, parse_mode=ParseMode.HTML)
    else:
        await target_msg.answer(text, reply_markup=kb, parse_mode=ParseMode.HTML)


@router.callback_query(F.data.startswith("adm_gdisc_pct:"))
async def cb_adm_gdisc_pct(call: CallbackQuery):
    if call.from_user.id != ADMIN_ID:
        return
    pct = int(call.data.split(":", 1)[1])
    GLOBAL_DISCOUNT_DRAFT["percent"] = pct
    await show_gdisc_step2_duration(call.message, edit=True)
    await call.answer()


async def activate_global_discount_and_ask_notify(duration_sec: int, target_msg: Message, edit: bool = True):
    USER_INPUT_STATE.pop(ADMIN_ID, None)
    pct = int(GLOBAL_DISCOUNT_DRAFT.get("percent", 20))
    until_ts = time.time() + duration_sec
    GLOBAL_DISCOUNT_DRAFT["duration_sec"] = duration_sec
    GLOBAL_DISCOUNT_DRAFT["until"] = until_ts

    await set_setting("global_discount_percent", str(pct))
    await set_setting("global_discount_until", str(until_ts))

    exp_str = datetime.fromtimestamp(until_ts).strftime("%d.%m.%Y %H:%M")
    dur_str = format_duration_ru(duration_sec)

    kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="📢 Уведомить всех пользователей об акции", callback_data="adm_gdisc_notify")],
            [InlineKeyboardButton(text="✅ Готово (без рассылки)", callback_data="adm_gdisc_menu")],
        ]
    )
    text = (
        f"✅ <b>Глобальная скидка {pct}% успешно запущена!</b>\n\n"
        f"⏳ Длительность: <b>{dur_str}</b> (до <b>{exp_str}</b>)\n"
        f"💰 Новые цены уже применяются в магазине для всех пользователей.\n\n"
        f"Отправить уведомление о старте скидки всем пользователям в личку?"
    )
    if edit:
        await target_msg.edit_text(text, reply_markup=kb, parse_mode=ParseMode.HTML)
    else:
        await target_msg.answer(text, reply_markup=kb, parse_mode=ParseMode.HTML)


@router.callback_query(F.data.startswith("adm_gdisc_dur:"))
async def cb_adm_gdisc_dur(call: CallbackQuery):
    if call.from_user.id != ADMIN_ID:
        return
    dur_sec = int(call.data.split(":", 1)[1])
    await activate_global_discount_and_ask_notify(dur_sec, call.message, edit=True)
    await call.answer()


@router.callback_query(F.data == "adm_gdisc_notify")
async def cb_adm_gdisc_notify(call: CallbackQuery, bot: Bot):
    if call.from_user.id != ADMIN_ID:
        return
    g_disc = await get_global_discount()
    if not g_disc["active"]:
        await call.answer("⚠️ Глобальная скидка уже не активна.", show_alert=True)
        return

    pct = g_disc["percent"]
    until_ts = g_disc["until"]
    exp_str = datetime.fromtimestamp(until_ts).strftime("%d.%m.%Y %H:%M")
    rem_str = format_duration_ru(max(60, int(until_ts - time.time())))

    promo_text = (
        f"🔥 <b>ГЛОБАЛЬНАЯ СКИДКА {pct}% ДЛЯ ВСЕХ УЖЕ ДЕЙСТВУЕТ!</b>\n\n"
        f"Снизили цены на <b>{pct}%</b> на все подписки и пакеты запросов (от 5 ₽) на <b>{rem_str}</b> (до <b>{exp_str}</b>):\n\n"
        "👑 <b>Подписки (безлимит на все PRO-модели):</b>\n"
        f"• Пробный 1 день: <s>{PRODUCTS['sub_trial']['rub']} ₽</s> → <b>{get_product_rub_price(PRODUCTS['sub_trial'], pct)} ₽</b> ({get_product_price(PRODUCTS['sub_trial'], pct)} ⭐)\n"
        f"• Стандарт 7 дней: <s>{PRODUCTS['sub_standard']['rub']} ₽</s> → <b>{get_product_rub_price(PRODUCTS['sub_standard'], pct)} ₽</b> ({get_product_price(PRODUCTS['sub_standard'], pct)} ⭐)\n"
        f"• Премиум 30 дней: <s>{PRODUCTS['sub_premium']['rub']} ₽</s> → <b>{get_product_rub_price(PRODUCTS['sub_premium'], pct)} ₽</b> ({get_product_price(PRODUCTS['sub_premium'], pct)} ⭐)\n\n"
        "⚡ <b>Пакеты запросов (не сгорают):</b>\n"
        f"• +30 запросов: <s>99 ₽</s> → <b>{get_product_rub_price(PRODUCTS['pack_30'], pct)} ₽</b> ({get_product_price(PRODUCTS['pack_30'], pct)} ⭐)\n"
        f"• +100 запросов: <s>259 ₽</s> → <b>{get_product_rub_price(PRODUCTS['pack_100'], pct)} ₽</b> ({get_product_price(PRODUCTS['pack_100'], pct)} ⭐)\n"
        f"• +300 запросов: <s>589 ₽</s> → <b>{get_product_rub_price(PRODUCTS['pack_300'], pct)} ₽</b> ({get_product_price(PRODUCTS['pack_300'], pct)} ⭐)\n\n"
        "👇 Переходи в магазин прямо сейчас, пока действует акция:"
    )

    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute("SELECT user_id FROM users") as cur:
            rows = await cur.fetchall()

    user_ids = [r[0] for r in rows]
    await call.message.edit_text(f"⏳ <b>Рассылаю уведомление о скидке {pct}% ({len(user_ids)} чел.)...</b>", parse_mode=ParseMode.HTML)
    await call.answer()

    sent_ok = 0
    failed = 0
    for uid in user_ids:
        try:
            await bot.send_message(uid, promo_text, reply_markup=shop_main_kb(), parse_mode=ParseMode.HTML)
            sent_ok += 1
        except Exception:
            failed += 1
        await asyncio.sleep(0.05)

    await call.message.answer(
        f"✅ <b>Рассылка об акции завершена!</b>\n\n"
        f"📨 Доставлено: <b>{sent_ok}</b>\n"
        f"🚫 Не доставлено: <b>{failed}</b>",
        reply_markup=await admin_kb(),
        parse_mode=ParseMode.HTML,
    )


@router.callback_query(F.data == "adm_promo_create")
async def cb_adm_promo_create(call: CallbackQuery):
    if call.from_user.id != ADMIN_ID:
        return
    PROMO_DRAFT.clear()
    await call.message.edit_text(
        "🎟 <b>Создание промокода — Шаг 1/4</b>\n\nЧто будет давать этот промокод?",
        reply_markup=InlineKeyboardMarkup(
            inline_keyboard=[
                [InlineKeyboardButton(text="👑 Подписка (PRO)", callback_data="promo_type:sub")],
                [InlineKeyboardButton(text="⚡ Пакет запросов", callback_data="promo_type:req")],
                [InlineKeyboardButton(text="❌ Отмена", callback_data="admin_panel")],
            ]
        ),
        parse_mode=ParseMode.HTML,
    )


@router.callback_query(F.data.startswith("promo_type:"))
async def cb_promo_type(call: CallbackQuery):
    if call.from_user.id != ADMIN_ID:
        return
    rtype = call.data.split(":", 1)[1]
    PROMO_DRAFT["type"] = rtype

    if rtype == "sub":
        await call.message.edit_text(
            "👑 <b>Промокод на подписку — Шаг 2/4</b>\n\nВыбери срок действия подписки:",
            reply_markup=InlineKeyboardMarkup(
                inline_keyboard=[
                    [InlineKeyboardButton(text="♾ Навсегда (3650 дней)", callback_data="promo_val:3650")],
                    [
                        InlineKeyboardButton(text="1 день", callback_data="promo_val:1"),
                        InlineKeyboardButton(text="7 дней", callback_data="promo_val:7"),
                        InlineKeyboardButton(text="30 дней", callback_data="promo_val:30"),
                    ],
                    [InlineKeyboardButton(text="✏️ Ввести своё число дней", callback_data="promo_val_custom")],
                    [InlineKeyboardButton(text="❌ Отмена", callback_data="admin_panel")],
                ]
            ),
            parse_mode=ParseMode.HTML,
        )
    else:
        USER_INPUT_STATE[ADMIN_ID] = "promo_custom_val"
        await call.message.edit_text(
            "⚡ <b>Промокод на пакет запросов — Шаг 2/4</b>\n\n"
            "Введи числом, сколько <b>запросов в пакет</b> добавит промокод (например: <code>20</code> или <code>50</code>):",
            reply_markup=admin_cancel_kb(),
            parse_mode=ParseMode.HTML,
        )


@router.callback_query(F.data == "promo_val_custom")
async def cb_promo_val_custom(call: CallbackQuery):
    if call.from_user.id != ADMIN_ID:
        return
    USER_INPUT_STATE[ADMIN_ID] = "promo_custom_val"
    await call.message.edit_text(
        "✏️ Введи количество дней подписки числом (например: <code>14</code> или <code>90</code>):",
        reply_markup=admin_cancel_kb(),
        parse_mode=ParseMode.HTML,
    )


async def show_promo_step3_uses(target_msg: Message, edit: bool = True):
    kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="♾ Бесконечный (без лимита людей)", callback_data="promo_uses:0")],
            [
                InlineKeyboardButton(text="1 человек", callback_data="promo_uses:1"),
                InlineKeyboardButton(text="5 человек", callback_data="promo_uses:5"),
                InlineKeyboardButton(text="10 человек", callback_data="promo_uses:10"),
            ],
            [InlineKeyboardButton(text="✏️ Ввести своё число активаций", callback_data="promo_uses_custom")],
            [InlineKeyboardButton(text="❌ Отмена", callback_data="admin_panel")],
        ]
    )
    text = "👥 <b>Лимит активаций — Шаг 3/4</b>\n\nНа сколько человек рассчитан этот промокод?"
    if edit:
        await target_msg.edit_text(text, reply_markup=kb, parse_mode=ParseMode.HTML)
    else:
        await target_msg.answer(text, reply_markup=kb, parse_mode=ParseMode.HTML)


@router.callback_query(F.data.startswith("promo_val:"))
async def cb_promo_val(call: CallbackQuery):
    if call.from_user.id != ADMIN_ID:
        return
    PROMO_DRAFT["amount"] = int(call.data.split(":", 1)[1])
    await show_promo_step3_uses(call.message, edit=True)


@router.callback_query(F.data == "promo_uses_custom")
async def cb_promo_uses_custom(call: CallbackQuery):
    if call.from_user.id != ADMIN_ID:
        return
    USER_INPUT_STATE[ADMIN_ID] = "promo_custom_uses"
    await call.message.edit_text(
        "✏️ Введи максимальное количество человек (активаций) числом (например: <code>25</code>):",
        reply_markup=admin_cancel_kb(),
        parse_mode=ParseMode.HTML,
    )


async def show_promo_step4_code(target_msg: Message, edit: bool = True):
    USER_INPUT_STATE[ADMIN_ID] = "promo_code_name"
    kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="🎲 Сгенерировать случайный код", callback_data="promo_gen_random")],
            [InlineKeyboardButton(text="❌ Отмена", callback_data="admin_panel")],
        ]
    )
    text = (
        "🔤 <b>Название промокода — Шаг 4/4</b>\n\n"
        "Введи сам промокод текстом (например: <code>FREE2026</code> или <code>VIP7</code>) "
        "или нажми кнопку ниже для автогенерации:"
    )
    if edit:
        await target_msg.edit_text(text, reply_markup=kb, parse_mode=ParseMode.HTML)
    else:
        await target_msg.answer(text, reply_markup=kb, parse_mode=ParseMode.HTML)


@router.callback_query(F.data.startswith("promo_uses:"))
async def cb_promo_uses(call: CallbackQuery):
    if call.from_user.id != ADMIN_ID:
        return
    PROMO_DRAFT["max_uses"] = int(call.data.split(":", 1)[1])
    await show_promo_step4_code(call.message, edit=True)


async def save_promo_and_reply(code: str, target_msg: Message, edit: bool = False):
    code = code.strip().upper()
    rtype = PROMO_DRAFT.get("type", "sub")
    amount = PROMO_DRAFT.get("amount", 1)
    max_uses = PROMO_DRAFT.get("max_uses", 1)

    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "INSERT OR REPLACE INTO promocodes (code, reward_type, amount, max_uses, used_count) VALUES (?, ?, ?, ?, 0)",
            (code, rtype, amount, max_uses),
        )
        await db.commit()

    reward_desc = (
        ("Подписка НАВСЕГДА" if amount >= 3650 else f"Подписка на {amount} дн.")
        if rtype == "sub"
        else f"Пакет +{amount} запросов"
    )
    uses_desc = "Бесконечный" if max_uses == 0 else f"На {max_uses} чел."

    text = (
        "✅ <b>Промокод успешно создан!</b>\n\n"
        f"🎟 Код: <code>{code}</code>\n"
        f"🎁 Награда: <b>{reward_desc}</b>\n"
        f"👥 Лимит: <b>{uses_desc}</b>"
    )
    kb = await admin_kb()
    if edit:
        await target_msg.edit_text(text, reply_markup=kb, parse_mode=ParseMode.HTML)
    else:
        await target_msg.answer(text, reply_markup=kb, parse_mode=ParseMode.HTML)


@router.callback_query(F.data == "promo_gen_random")
async def cb_promo_gen_random(call: CallbackQuery):
    if call.from_user.id != ADMIN_ID:
        return
    USER_INPUT_STATE.pop(ADMIN_ID, None)
    rand_code = "PROMO-" + "".join(random.choices(string.ascii_uppercase + string.digits, k=6))
    await save_promo_and_reply(rand_code, call.message, edit=True)


@router.callback_query(F.data == "adm_promo_list")
async def cb_adm_promo_list(call: CallbackQuery):
    if call.from_user.id != ADMIN_ID:
        return
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute("SELECT * FROM promocodes") as cur:
            rows = await cur.fetchall()

    if not rows:
        await call.answer("Список промокодов пуст!", show_alert=True)
        return

    lines = ["📋 <b>Активные промокоды:</b>\n"]
    buttons = []
    for r in rows:
        r_desc = ("PRO навсегда" if r["amount"] >= 3650 else f"PRO {r['amount']}д") if r["reward_type"] == "sub" else f"+{r['amount']} запр."
        u_desc = f"{r['used_count']}/∞" if r["max_uses"] == 0 else f"{r['used_count']}/{r['max_uses']}"
        lines.append(f"• <code>{r['code']}</code> — {r_desc} ({u_desc})")
        buttons.append([InlineKeyboardButton(text=f"🗑 Удалить {r['code']}", callback_data=f"del_promo:{r['code']}")])

    buttons.append([InlineKeyboardButton(text="⬅️ Назад в админку", callback_data="admin_panel")])
    await call.message.edit_text("\n".join(lines), reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons), parse_mode=ParseMode.HTML)


@router.callback_query(F.data.startswith("del_promo:"))
async def cb_del_promo(call: CallbackQuery):
    if call.from_user.id != ADMIN_ID:
        return
    code = call.data.split(":", 1)[1]
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("DELETE FROM promocodes WHERE code = ?", (code,))
        await db.execute("DELETE FROM promo_uses WHERE code = ?", (code,))
        await db.commit()
    await call.answer(f"🗑 Промокод {code} удален")
    await cb_admin_panel(call)


@router.callback_query(F.data == "adm_set_engine")
async def cb_adm_set_engine(call: CallbackQuery):
    if call.from_user.id != ADMIN_ID:
        return
    USER_INPUT_STATE[ADMIN_ID] = "set_engine"
    current = await get_engine_model()
    await call.message.edit_text(
        "⚙️ <b>Смена общего движка API (для обычных пользователей)</b>\n\n"
        f"Сейчас стоит: <code>{current}</code>\n\n"
        "Отправь точный ID модели с <code>unlockapi.space</code>:",
        reply_markup=admin_cancel_kb(),
        parse_mode=ParseMode.HTML,
    )


@router.callback_query(F.data == "adm_check_api")
async def cb_adm_check_api(call: CallbackQuery):
    if call.from_user.id != ADMIN_ID:
        return
    await call.answer("⏳ Запрашиваю список моделей...")
    try:
        models_page = await ai_client.models.list()
        ids = [m.id for m in models_page.data]
        preview = "\n".join(f"• <code>{mid}</code>" for mid in ids[:40]) if ids else "Пустой список"
        await call.message.answer(
            f"✅ <b>API отвечает!</b> Доступные ID моделей ({len(ids)} шт.):\n\n{preview}",
            parse_mode=ParseMode.HTML,
        )
    except Exception as e:
        await call.message.answer(f"❌ <b>Ошибка API:</b>\n<code>{str(e)[:400]}</code>", parse_mode=ParseMode.HTML)


@router.callback_query(F.data == "adm_self_pro")
async def cb_adm_self_pro(call: CallbackQuery):
    if call.from_user.id != ADMIN_ID:
        return
    user = await get_user(ADMIN_ID)
    new_until = max(time.time(), user["pro_until"]) + 30 * 86400
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("UPDATE users SET pro_until = ? WHERE user_id = ?", (new_until, ADMIN_ID))
        await db.commit()
    await call.answer("👑 Тебе выдан Премиум на 30 дней!", show_alert=True)
    await cb_admin_panel(call)


@router.message(Command("givepro"))
async def cmd_givepro(message: Message, bot: Bot):
    if message.from_user.id != ADMIN_ID:
        return
    parts = message.text.split()
    if len(parts) < 3 or not parts[1].isdigit() or not parts[2].isdigit():
        await message.answer("⚠️ Формат: <code>/givepro ID ДНИ</code>", parse_mode=ParseMode.HTML)
        return
    target_id, days = int(parts[1]), int(parts[2])
    target = await get_user(target_id)
    new_until = max(time.time(), target["pro_until"]) + days * 86400
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("UPDATE users SET pro_until = ? WHERE user_id = ?", (new_until, target_id))
        await db.commit()
    exp_date = datetime.fromtimestamp(new_until).strftime("%d.%m.%Y %H:%M")
    await message.answer(f"✅ Пользователю <code>{target_id}</code> выдана подписка на <b>{days} дн.</b> (до {exp_date})", parse_mode=ParseMode.HTML)
    try:
        await bot.send_message(target_id, f"🎁 Администратор выдал тебе <b>подписку на {days} дн.!</b> Открой /menu.", parse_mode=ParseMode.HTML)
    except Exception:
        pass


@router.message(Command("delpro"))
async def cmd_delpro(message: Message, bot: Bot):
    if message.from_user.id != ADMIN_ID:
        return
    parts = message.text.split()
    if len(parts) < 2 or not parts[1].isdigit():
        await message.answer("⚠️ Формат: <code>/delpro ID</code>", parse_mode=ParseMode.HTML)
        return
    target_id = int(parts[1])
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("UPDATE users SET pro_until = 0 WHERE user_id = ?", (target_id,))
        await db.commit()
    await message.answer(f"❌ У пользователя <code>{target_id}</code> снята подписка.", parse_mode=ParseMode.HTML)
    try:
        await bot.send_message(target_id, "⚠️ Администратор забрал твою <b>PRO-подписку</b>.", parse_mode=ParseMode.HTML)
    except Exception:
        pass


# ================= ХЭНДЛЕРЫ НАВИГАЦИИ =================
async def issue_web_auth_credentials(user_id: int) -> tuple[str, str]:
    """Создаёт одноразовый код (на 10 минут) и токен веб-сессии (на 30 дней) для безопасного входа в браузере."""
    now = time.time()
    code = "AE-" + "".join(random.choices(string.digits, k=6))
    token = secrets.token_urlsafe(32)
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("DELETE FROM web_auth_codes WHERE user_id = ? OR expires_at < ?", (user_id, now))
        await db.execute(
            "INSERT INTO web_auth_codes (code, user_id, expires_at) VALUES (?, ?, ?)",
            (code, user_id, now + 600),
        )
        await db.execute(
            "INSERT INTO web_sessions (token, user_id, created_at, expires_at) VALUES (?, ?, ?, ?)",
            (token, user_id, now, now + 30 * 86400),
        )
        await db.commit()
    return code, token


@router.message(CommandStart())
async def cmd_start(message: Message, bot: Bot):
    USER_INPUT_STATE.pop(message.from_user.id, None)
    args = message.text.split()
    start_param = args[1].strip() if len(args) > 1 else ""
    ref_id = int(start_param) if start_param.isdigit() else 0
    user = await get_user(
        message.from_user.id,
        ref_id,
        full_name=message.from_user.full_name,
        username=message.from_user.username or "",
    )

    if not await ensure_subscribed(bot, message.from_user.id, message):
        return

    if start_param == "web_auth":
        code, token = await issue_web_auth_credentials(message.from_user.id)
        buttons = []
        if WEBAPP_URL:
            sep = "&" if "?" in WEBAPP_URL else "?"
            magic_url = f"{WEBAPP_URL}{sep}token={token}&uid={message.from_user.id}"
            buttons.append([InlineKeyboardButton(text="🌐 Войти в веб-версию в 1 клик", url=magic_url)])
        buttons.append([InlineKeyboardButton(text="⬅️ В главное меню", callback_data="back_cats")])
        await message.answer(
            f"🔐 <b>Авторизация в веб-версии Aether AI</b>\n\n"
            f"Твой одноразовый код для входа в браузере (действует 10 минут):\n"
            f"👉 <code>{code}</code>\n\n"
            f"Скопируй код и вставь его на странице входа в браузере"
            + (" или нажми кнопку ниже для мгновенного входа:" if WEBAPP_URL else "."),
            reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons),
            parse_mode=ParseMode.HTML,
        )
        return

    cur_model_name = ALL_MODELS_MAP.get(user["selected_model"], {}).get("name", user["selected_model"])
    text = (
        f"👋 <b>Привет, {html.escape(message.from_user.first_name)}!</b>\n\n"
        f"Я — твой универсальный ИИ-помощник. Вот что я умею:\n"
        f"💬 Отвечать на любые вопросы и писать код\n"
        f"📸 Решать задачи и разбирать конспекты по фото (до {MAX_ALBUM_PHOTOS} шт. за раз)\n"
        f"🎬 Анализировать видео, кружочки, голосовые и файлы\n\n"
        f"📊 Статус: <b>{format_status(user)}</b>\n"
        f"🤖 Активная модель: <b>{cur_model_name}</b>"
    )
    await message.answer(text, reply_markup=categories_kb(message.from_user.id), parse_mode=ParseMode.HTML)


@router.message(Command("menu"))
async def cmd_menu(message: Message, bot: Bot):
    USER_INPUT_STATE.pop(message.from_user.id, None)
    user = await get_user(message.from_user.id, full_name=message.from_user.full_name, username=message.from_user.username or "")
    if not await ensure_subscribed(bot, message.from_user.id, message):
        return
    cur_model_name = ALL_MODELS_MAP.get(user["selected_model"], {}).get("name", user["selected_model"])
    await message.answer(
        f"⚙️ <b>Выбор нейросети</b>\n"
        f"📊 {format_status(user)}\n"
        f"🤖 Активная модель: <b>{cur_model_name}</b>",
        reply_markup=categories_kb(message.from_user.id),
        parse_mode=ParseMode.HTML,
    )


@router.message(Command("shop"))
async def cmd_shop(message: Message, bot: Bot):
    USER_INPUT_STATE.pop(message.from_user.id, None)
    user = await get_user(message.from_user.id, full_name=message.from_user.full_name, username=message.from_user.username or "")
    if not await ensure_subscribed(bot, message.from_user.id, message):
        return
    await message.answer(await render_shop_main_text(user), reply_markup=shop_main_kb(), parse_mode=ParseMode.HTML)


@router.message(Command("clear"))
async def cmd_clear(message: Message):
    await clear_history(message.from_user.id)
    await message.answer("🧹 Память диалога полностью очищена! Начинаем с чистого листа.")


@router.callback_query(F.data.startswith("cat:"))
async def cb_open_category(call: CallbackQuery, bot: Bot):
    if not await ensure_subscribed(bot, call.from_user.id, call.message):
        await call.answer()
        return

    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("UPDATE users SET visited_models = 1 WHERE user_id = ?", (call.from_user.id,))
        await db.commit()

    cat_key = call.data.split(":", 1)[1]
    user = await get_user(call.from_user.id, full_name=call.from_user.full_name, username=call.from_user.username or "")
    cat = CATEGORIES[cat_key]
    pro_active = is_pro(user) or (call.from_user.id == ADMIN_ID)

    try:
        await call.message.edit_text(
            f"<b>{cat['title']}</b>\nВыбери нужную модель из списка:",
            reply_markup=models_in_category_kb(cat_key, user["selected_model"], pro_active),
            parse_mode=ParseMode.HTML,
        )
    except TelegramBadRequest:
        pass
    await call.answer()


@router.callback_query(F.data.startswith("set_model:"))
async def cb_set_model(call: CallbackQuery, bot: Bot):
    if not await ensure_subscribed(bot, call.from_user.id, call.message):
        await call.answer()
        return
    _, cat_key, model_id = call.data.split(":", 2)
    user = await get_user(call.from_user.id, full_name=call.from_user.full_name, username=call.from_user.username or "")
    model_info = ALL_MODELS_MAP.get(model_id)
    pro_active = is_pro(user) or (call.from_user.id == ADMIN_ID)

    if model_info and model_info["pro"] and not pro_active:
        await call.answer("🔒 Эта модель доступна только по подписке! Нажми «Подписка» в меню.", show_alert=True)
        return

    if user["selected_model"] == model_id:
        await call.answer(f"✅ Модель {model_info['name']} уже выбрана!")
        return

    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("UPDATE users SET selected_model = ? WHERE user_id = ?", (model_id, call.from_user.id))
        await db.commit()

    try:
        await call.message.edit_reply_markup(
            reply_markup=models_in_category_kb(cat_key, model_id, pro_active)
        )
    except TelegramBadRequest:
        pass
    await call.answer(f"✅ Выбрана модель: {model_info['name']}")


@router.callback_query(F.data == "back_cats")
async def cb_back_cats(call: CallbackQuery, bot: Bot):
    USER_INPUT_STATE.pop(call.from_user.id, None)
    if not await ensure_subscribed(bot, call.from_user.id, call.message):
        await call.answer()
        return
    user = await get_user(call.from_user.id, full_name=call.from_user.full_name, username=call.from_user.username or "")
    cur_model_name = ALL_MODELS_MAP.get(user["selected_model"], {}).get("name", user["selected_model"])
    try:
        await call.message.edit_text(
            f"⚙️ <b>Выбор нейросети</b>\n"
            f"📊 {format_status(user)}\n"
            f"🤖 Активная модель: <b>{cur_model_name}</b>",
            reply_markup=categories_kb(call.from_user.id),
            parse_mode=ParseMode.HTML,
        )
    except TelegramBadRequest:
        pass
    await call.answer()


@router.callback_query(F.data == "clear_chat")
async def cb_clear_chat(call: CallbackQuery):
    await clear_history(call.from_user.id)
    await call.answer("🧹 Память диалога очищена!", show_alert=True)


# ================= ГЕНЕРАЦИЯ (ТЕКСТ И РАЗБОР ФОТО ЧЕРЕЗ ВЫБРАННЫЙ ДВИЖОК) =================
async def get_candidates_for_user(user_id: int, selected_model: str) -> list[str]:
    engine = await get_engine_model()
    return [engine] + [m for m in FALLBACK_MODELS if m != engine]


async def generate_text_response(user_id: int, selected_model: str, history: list[dict], user_text: str) -> str:
    candidates = await get_candidates_for_user(user_id, selected_model)

    messages_payload = [
        {"role": "system", "content": SYSTEM_PROMPT},
        *history,
        {"role": "user", "content": user_text},
    ]

    last_error = None
    for candidate_id in candidates:
        try:
            response = await ai_client.chat.completions.create(
                model=candidate_id,
                messages=messages_payload,
                max_tokens=1500,
            )
            content = response.choices[0].message.content
            if content:
                return content
        except Exception as e:
            last_error = e
            continue

    raise last_error or RuntimeError("Все модели временно недоступны")


async def generate_photos_response(user_id: int, selected_model: str, caption: str, b64_images: list[str]) -> str:
    candidates = await get_candidates_for_user(user_id, selected_model)

    user_content: list[dict] = [{"type": "text", "text": caption}]
    for b64_img in b64_images:
        user_content.append(
            {
                "type": "image_url",
                "image_url": {"url": f"data:image/jpeg;base64,{b64_img}"},
            }
        )

    messages_payload = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": user_content},
    ]

    last_error = None
    for candidate_id in candidates:
        try:
            response = await ai_client.chat.completions.create(
                model=candidate_id,
                messages=messages_payload,
                max_tokens=2500,
            )
            content = response.choices[0].message.content
            if content:
                return content
        except Exception as e:
            last_error = e
            continue

    raise last_error or RuntimeError("Модели распознавания фото временно недоступны")


# ================= ОБРАБОТКА ОДИНОЧНЫХ ФОТО И АЛЬБОМОВ (ДО 10 ФОТО, ЖЁСТКИЙ КОНТРОЛЬ ЛИМИТА) =================
async def process_photo_batch(messages: list[Message], bot: Bot):
    first_msg = messages[0]
    user_id = first_msg.from_user.id
    user = await get_user(
        user_id,
        full_name=first_msg.from_user.full_name,
        username=first_msg.from_user.username or "",
    )
    if not await ensure_subscribed(bot, user_id, first_msg):
        return

    for m in messages:
        if is_content_forbidden(m.caption or ""):
            await first_msg.answer("🚫 Запрос отклонён системой безопасности: запрещённый контент.")
            return

    if len(messages) > MAX_ALBUM_PHOTOS:
        await first_msg.answer(
            f"⚠️ За один раз можно отправить максимум <b>{MAX_ALBUM_PHOTOS} фото</b>. Раздели альбом на несколько частей.",
            parse_mode=ParseMode.HTML,
        )
        return

    count = len(messages)
    total_cost = count * PHOTO_COST
    pro_active = is_pro(user) or (user_id == ADMIN_ID)

    quota_receipt = await try_consume_quota(user_id, pro_active, count=total_cost)
    if not quota_receipt:
        total_limit = FREE_DAILY_LIMIT + (user.get("bonus_limit") or 0)
        daily_left = max(0, total_limit - (user.get("used_today") or 0))
        extra_left = user.get("extra_requests") or 0
        avail = daily_left + extra_left
        await first_msg.answer(
            f"⏳ <b>Недостаточно запросов для обработки {count} фото</b> (1 фото = 1 запрос).\n"
            f"Сейчас доступно: <b>{avail} запр.</b> (не хватает ещё <b>{total_cost - avail}</b>).\n\n"
            "Отправь меньше фотографий, пригласи друга (/ref) или оформи подписку / пакет:",
            reply_markup=shop_main_kb(),
            parse_mode=ParseMode.HTML,
        )
        return

    status_label = (
        f"📸 <i>Анализирую {count} фото...</i>"
        if count > 1
        else "📸 <i>Анализирую изображение...</i>"
    )
    wait_msg = await first_msg.answer(status_label, parse_mode=ParseMode.HTML)

    try:
        b64_list: list[str] = []
        caption = ""
        for msg in messages:
            if msg.caption and not caption:
                caption = msg.caption
            photo = msg.photo[-1]
            file_info = await bot.get_file(photo.file_id)
            downloaded = await bot.download_file(file_info.file_path)
            b64_list.append(base64.b64encode(downloaded.read()).decode("utf-8"))

        if not caption:
            if count > 1:
                caption = f"Подробно разбери и реши все задания с этих {count} фотографий по порядку, объединив ответ в один структурированный текст."
            else:
                caption = "Подробно разбери и реши то, что изображено на фото."

        answer_text = await generate_photos_response(
            user_id=user_id,
            selected_model=user["selected_model"],
            caption=caption,
            b64_images=b64_list,
        )

        shown_model = ALL_MODELS_MAP.get(user["selected_model"], {}).get("name", user["selected_model"])
        raw_photo_cap = ""
        for m in messages:
            if m.caption:
                raw_photo_cap = m.caption.strip()
                break
        photo_log_q = f"[{count} фото]" + (f": {raw_photo_cap}" if raw_photo_cap else " (без подписи)")
        await add_history(user_id, "user", f"[Отправил {count} фото с подписью: {caption}]")
        await add_history(user_id, "assistant", answer_text)
        await log_user_request(user_id, "📸 Фото", photo_log_q, answer_text, model_used=shown_model)

        async with aiosqlite.connect(DB_PATH) as db:
            await db.execute(
                "UPDATE users SET total_requests = total_requests + ? WHERE user_id = ?",
                (total_cost, user_id),
            )
            await db.commit()

        await wait_msg.delete()
        await send_formatted_answer(first_msg, answer_text)

    except Exception as e:
        await refund_quota(user_id, quota_receipt)
        await wait_msg.edit_text(
            f"⚠️ <b>Не удалось распознать фото:</b>\n<code>{str(e)[:250]}</code>",
            parse_mode=ParseMode.HTML,
        )


@router.message(F.photo)
async def handle_photo(message: Message, bot: Bot):
    if message.from_user.id == ADMIN_ID and USER_INPUT_STATE.get(ADMIN_ID) == "adm_broadcast_msg":
        USER_INPUT_STATE.pop(ADMIN_ID, None)
        BROADCAST_DRAFT["chat_id"] = message.chat.id
        BROADCAST_DRAFT["message_id"] = message.message_id
        kb = InlineKeyboardMarkup(
            inline_keyboard=[
                [InlineKeyboardButton(text="✅ Отправить всем пользователям", callback_data="adm_broadcast_confirm")],
                [InlineKeyboardButton(text="❌ Отмена", callback_data="admin_panel")],
            ]
        )
        await message.answer(
            "👆 <b>Предпросмотр рассылки готов!</b>\nПодтвердить отправку этого поста всем пользователям бота?",
            reply_markup=kb,
            parse_mode=ParseMode.HTML,
        )
        return

    mg_id = message.media_group_id
    if mg_id:
        is_first = mg_id not in MEDIA_GROUP_BUFFER
        MEDIA_GROUP_BUFFER.setdefault(mg_id, []).append(message)
        if is_first:
            await asyncio.sleep(1.5)
            batch = MEDIA_GROUP_BUFFER.pop(mg_id, [])
            if batch:
                batch.sort(key=lambda m: m.message_id)
                await process_photo_batch(batch, bot)
    else:
        await process_photo_batch([message], bot)


# ================= ОБРАБОТКА ТЕКСТА, КАСТОМНЫХ ПОКУПОК, ВЫВОДА, ПРОМОКОДОВ И АДМИН-ВВОДА =================
@router.message(F.text)
async def handle_prompt(message: Message, bot: Bot):
    user_id = message.from_user.id
    text_in = message.text.strip()
    state = USER_INPUT_STATE.get(user_id, "")

    # 1. Ввод своего количества дней подписки (1–60)
    if state == "await_custom_sub_days":
        if not text_in.isdigit() or not (1 <= int(text_in) <= MAX_CUSTOM_SUB_DAYS):
            await message.answer(
                f"⚠️ Введи целое число от <b>1 до {MAX_CUSTOM_SUB_DAYS}</b> дней:",
                reply_markup=InlineKeyboardMarkup(
                    inline_keyboard=[[InlineKeyboardButton(text="❌ Отмена", callback_data="shop:subs")]]
                ),
                parse_mode=ParseMode.HTML,
            )
            return
        USER_INPUT_STATE.pop(user_id, None)
        days = int(text_in)
        await send_payment_method_choice(message, user_id, f"csub:{days}", edit=False)
        return

    # 2. Ввод своего количества запросов в пакет (1–500)
    if state == "await_custom_pack_reqs":
        if not text_in.isdigit() or not (MIN_CUSTOM_PACK_REQS <= int(text_in) <= MAX_CUSTOM_PACK_REQS):
            await message.answer(
                f"⚠️ Введи целое число от <b>{MIN_CUSTOM_PACK_REQS} до {MAX_CUSTOM_PACK_REQS}</b> запросов:",
                reply_markup=InlineKeyboardMarkup(
                    inline_keyboard=[[InlineKeyboardButton(text="❌ Отмена", callback_data="shop:packs")]]
                ),
                parse_mode=ParseMode.HTML,
            )
            return
        USER_INPUT_STATE.pop(user_id, None)
        reqs = int(text_in)
        await send_payment_method_choice(message, user_id, f"cpack:{reqs}", edit=False)
        return

    # 3. Ввод реквизитов для вывода партнёрских средств (от 100 ₽)
    if state == "await_withdraw_reqs":
        if len(text_in) < 5:
            await message.answer(
                "⚠️ Укажи корректные реквизиты (номер телефона СБП / карты и банк):",
                reply_markup=InlineKeyboardMarkup(
                    inline_keyboard=[[InlineKeyboardButton(text="❌ Отмена", callback_data="ref_info")]]
                ),
            )
            return
        USER_INPUT_STATE.pop(user_id, None)
        lock = get_user_lock(user_id)
        async with lock:
            user_w = await get_user(user_id)
            bal = user_w.get("ref_balance") or 0.0
            if bal < MIN_WITHDRAW_RUB:
                await message.answer(f"❌ Недостаточно средств для вывода (минимум {int(MIN_WITHDRAW_RUB)} ₽).")
                return

            async with aiosqlite.connect(DB_PATH) as db:
                await db.execute("UPDATE users SET ref_balance = 0 WHERE user_id = ?", (user_id,))
                cur = await db.execute(
                    "INSERT INTO withdrawals (user_id, amount, requisites, status, created_at) VALUES (?, ?, ?, 'pending', ?)",
                    (user_id, bal, text_in[:150], time.time()),
                )
                wid = cur.lastrowid
                await db.commit()

        await message.answer(
            f"✅ <b>Заявка #{wid} на вывод {bal:.2f} ₽ создана!</b>\n\n"
            f"Реквизиты: <code>{html.escape(text_in[:150])}</code>\n"
            f"Администратор проверит заявку и переведёт средства в ближайшее время.",
            parse_mode=ParseMode.HTML,
        )
        try:
            uname = f" (@{message.from_user.username})" if message.from_user.username else ""
            adm_kb_w = InlineKeyboardMarkup(
                inline_keyboard=[
                    [
                        InlineKeyboardButton(text=f"✅ Выплачено #{wid}", callback_data=f"adm_w_ok:{wid}"),
                        InlineKeyboardButton(text=f"❌ Отклонить #{wid}", callback_data=f"adm_w_no:{wid}"),
                    ]
                ]
            )
            await bot.send_message(
                ADMIN_ID,
                f"💸 <b>Новая заявка на вывод #{wid}!</b>\n\n"
                f"👤 Пользователь: <b>{html.escape(message.from_user.full_name)}</b>{uname} (<code>{user_id}</code>)\n"
                f"💰 Сумма: <b>{bal:.2f} ₽</b>\n"
                f"🏦 Реквизиты: <code>{html.escape(text_in[:150])}</code>",
                reply_markup=adm_kb_w,
                parse_mode=ParseMode.HTML,
            )
        except Exception:
            pass
        return

    # 4. Активация промокода
    if state == "promo_activate":
        USER_INPUT_STATE.pop(user_id, None)
        if not await ensure_subscribed(bot, user_id, message):
            return
        ok, reply_text = await redeem_promocode(user_id, text_in)
        await message.answer(reply_text, reply_markup=profile_kb(), parse_mode=ParseMode.HTML)
        return

    # 5. Админ-вводы
    if user_id == ADMIN_ID and ADMIN_ID in USER_INPUT_STATE:
        action = USER_INPUT_STATE.pop(ADMIN_ID)

        if action == "adm_broadcast_msg":
            BROADCAST_DRAFT["chat_id"] = message.chat.id
            BROADCAST_DRAFT["message_id"] = message.message_id
            kb = InlineKeyboardMarkup(
                inline_keyboard=[
                    [InlineKeyboardButton(text="✅ Отправить всем пользователям", callback_data="adm_broadcast_confirm")],
                    [InlineKeyboardButton(text="❌ Отмена", callback_data="admin_panel")],
                ]
            )
            await message.answer(
                "👆 <b>Предпросмотр рассылки готов!</b>\nПодтвердить отправку этого сообщения всем пользователям бота?",
                reply_markup=kb,
                parse_mode=ParseMode.HTML,
            )
            return

        elif action == "adm_u_search":
            q = text_in.lstrip("@").strip()
            async with aiosqlite.connect(DB_PATH) as db:
                db.row_factory = aiosqlite.Row
                if q.isdigit():
                    async with db.execute("SELECT user_id FROM users WHERE user_id = ?", (int(q),)) as cur:
                        row = await cur.fetchone()
                else:
                    async with db.execute(
                        "SELECT user_id FROM users WHERE username LIKE ? OR full_name LIKE ? LIMIT 1",
                        (f"%{q}%", f"%{q}%"),
                    ) as cur:
                        row = await cur.fetchone()

            if not row:
                await message.answer(
                    "❌ Пользователь не найден в базе.",
                    reply_markup=admin_cancel_kb("adm_users:0"),
                )
                return
            text, kb = await render_user_card(row["user_id"], 0)
            await message.answer(text, reply_markup=kb, parse_mode=ParseMode.HTML)
            return

        elif action == "adm_rh_search":
            q = text_in.lstrip("@").strip()
            async with aiosqlite.connect(DB_PATH) as db:
                db.row_factory = aiosqlite.Row
                if q.isdigit():
                    async with db.execute("SELECT user_id FROM users WHERE user_id = ?", (int(q),)) as cur:
                        row = await cur.fetchone()
                else:
                    async with db.execute(
                        "SELECT user_id FROM users WHERE username LIKE ? OR full_name LIKE ? LIMIT 1",
                        (f"%{q}%", f"%{q}%"),
                    ) as cur:
                        row = await cur.fetchone()

            if not row:
                await message.answer(
                    "❌ Пользователь не найден в базе.",
                    reply_markup=admin_cancel_kb("adm_req_hist:0"),
                )
                return
            text, kb = await render_user_req_logs(row["user_id"], 0, 0)
            await message.answer(text, reply_markup=kb, parse_mode=ParseMode.HTML)
            return

        elif action.startswith("adm_u_pro_cust:"):
            _, uid_s, page_s = action.split(":")
            if not text_in.isdigit() or int(text_in) <= 0:
                USER_INPUT_STATE[ADMIN_ID] = action
                await message.answer("⚠️ Введи положительное число дней:", reply_markup=admin_cancel_kb(f"adm_u_view:{uid_s}:{page_s}"))
                return
            target_id, days, page = int(uid_s), int(text_in), int(page_s)
            target = await get_user(target_id)
            new_until = max(time.time(), target["pro_until"]) + days * 86400
            async with aiosqlite.connect(DB_PATH) as db:
                await db.execute("UPDATE users SET pro_until = ? WHERE user_id = ?", (new_until, target_id))
                await db.commit()
            try:
                await bot.send_message(target_id, f"🎁 Администратор выдал тебе <b>подписку на {days} дн.!</b> Открой /menu.", parse_mode=ParseMode.HTML)
            except Exception:
                pass
            text, kb = await render_user_card(target_id, page)
            await message.answer(text, reply_markup=kb, parse_mode=ParseMode.HTML)
            return

        elif action.startswith("adm_u_req_cust:"):
            _, uid_s, page_s = action.split(":")
            if not text_in.isdigit() or int(text_in) <= 0:
                USER_INPUT_STATE[ADMIN_ID] = action
                await message.answer("⚠️ Введи положительное число запросов:", reply_markup=admin_cancel_kb(f"adm_u_view:{uid_s}:{page_s}"))
                return
            target_id, amount, page = int(uid_s), int(text_in), int(page_s)
            await get_user(target_id)
            async with aiosqlite.connect(DB_PATH) as db:
                await db.execute("UPDATE users SET extra_requests = extra_requests + ? WHERE user_id = ?", (amount, target_id))
                await db.commit()
            try:
                await bot.send_message(target_id, f"🎁 Администратор начислил тебе <b>пакет на +{amount} запросов!</b>", parse_mode=ParseMode.HTML)
            except Exception:
                pass
            text, kb = await render_user_card(target_id, page)
            await message.answer(text, reply_markup=kb, parse_mode=ParseMode.HTML)
            return

        elif action.startswith("adm_u_subreq_cust:"):
            _, uid_s, page_s = action.split(":")
            if not text_in.isdigit() or int(text_in) <= 0:
                USER_INPUT_STATE[ADMIN_ID] = action
                await message.answer("⚠️ Введи положительное число запросов:", reply_markup=admin_cancel_kb(f"adm_u_view:{uid_s}:{page_s}"))
                return
            target_id, amount, page = int(uid_s), int(text_in), int(page_s)
            user_t = await get_user(target_id)
            removed = min(user_t.get("extra_requests", 0), amount)
            async with aiosqlite.connect(DB_PATH) as db:
                await db.execute("UPDATE users SET extra_requests = MAX(0, extra_requests - ?) WHERE user_id = ?", (amount, target_id))
                await db.commit()
            if removed > 0:
                try:
                    await bot.send_message(
                        target_id,
                        f"⚠️ Администратор забрал у тебя <b>{removed} запросов</b> из пакета.",
                        parse_mode=ParseMode.HTML,
                    )
                except Exception:
                    pass
            text, kb = await render_user_card(target_id, page)
            await message.answer(text, reply_markup=kb, parse_mode=ParseMode.HTML)
            return

        elif action == "promo_custom_val":
            if not text_in.isdigit() or int(text_in) <= 0:
                USER_INPUT_STATE[ADMIN_ID] = "promo_custom_val"
                await message.answer("⚠️ Введи положительное целое число:", reply_markup=admin_cancel_kb())
                return
            PROMO_DRAFT["amount"] = int(text_in)
            await show_promo_step3_uses(message, edit=False)
            return

        elif action == "promo_custom_uses":
            if not text_in.isdigit() or int(text_in) <= 0:
                USER_INPUT_STATE[ADMIN_ID] = "promo_custom_uses"
                await message.answer("⚠️ Введи положительное целое число:", reply_markup=admin_cancel_kb())
                return
            PROMO_DRAFT["max_uses"] = int(text_in)
            await show_promo_step4_code(message, edit=False)
            return

        elif action == "promo_code_name":
            if " " in text_in or len(text_in) < 2:
                USER_INPUT_STATE[ADMIN_ID] = "promo_code_name"
                await message.answer("⚠️ Код должен быть одним словом без пробелов (минимум 2 символа):", reply_markup=admin_cancel_kb())
                return
            await save_promo_and_reply(text_in, message, edit=False)
            return

        elif action == "adm_gdisc_pct":
            clean_pct = text_in.rstrip("%").strip()
            if not clean_pct.isdigit() or not (1 <= int(clean_pct) <= 95):
                USER_INPUT_STATE[ADMIN_ID] = "adm_gdisc_pct"
                await message.answer(
                    "⚠️ Введи целое число процентов от <b>1 до 95</b> (например: <code>25</code>):",
                    reply_markup=admin_cancel_kb("adm_gdisc_menu"),
                    parse_mode=ParseMode.HTML,
                )
                return
            GLOBAL_DISCOUNT_DRAFT["percent"] = int(clean_pct)
            await show_gdisc_step2_duration(message, edit=False)
            return

        elif action == "adm_gdisc_dur":
            dur_sec = parse_duration_to_seconds(text_in)
            if not dur_sec or dur_sec > 365 * 86400:
                USER_INPUT_STATE[ADMIN_ID] = "adm_gdisc_dur"
                await message.answer(
                    "⚠️ Неверный формат срока. Введи число часов (например <code>12</code>) или формат <code>3д</code> / <code>2д 6ч</code>:",
                    reply_markup=admin_cancel_kb("adm_gdisc_menu"),
                    parse_mode=ParseMode.HTML,
                )
                return
            await activate_global_discount_and_ask_notify(dur_sec, message, edit=False)
            return

        elif action == "set_engine":
            if not text_in or " " in text_in:
                await message.answer("⚠️ Введи корректный ID модели без пробелов.", reply_markup=await admin_kb())
                return
            await set_engine_model(text_in)
            await message.answer(
                f"✅ Общий движок изменен на <code>{text_in}</code> (для обычных пользователей).",
                reply_markup=await admin_kb(),
                parse_mode=ParseMode.HTML,
            )
            return

    user = await get_user(user_id, full_name=message.from_user.full_name, username=message.from_user.username or "")

    if not await ensure_subscribed(bot, user_id, message):
        return

    if is_content_forbidden(message.text):
        await message.answer("🚫 Запрос отклонён системой безопасности: запрещённый контент.")
        return

    model_id = user["selected_model"]
    pro_active = is_pro(user) or (user_id == ADMIN_ID)

    if ALL_MODELS_MAP.get(model_id, {}).get("pro") and not pro_active:
        await message.answer(
            "🔒 Срок подписки истек. Выбери бесплатную модель в /menu или продли тариф:",
            reply_markup=shop_main_kb(),
        )
        return

    quota_receipt = await try_consume_quota(user_id, pro_active, count=1)
    if not quota_receipt:
        await message.answer(
            "⏳ Бесплатный лимит на сегодня и пакет запросов исчерпаны.\n"
            "Приходи завтра, пригласи друга за +2 запроса (/ref) или оформи подписку / пакет:",
            reply_markup=shop_main_kb(),
        )
        return

    wait_msg = await message.answer("⏳ <i>Думаю...</i>", parse_mode=ParseMode.HTML)

    try:
        history = await get_history(user_id)
        answer_text = await generate_text_response(
            user_id=user_id,
            selected_model=model_id,
            history=history,
            user_text=message.text,
        )

        shown_model = ALL_MODELS_MAP.get(model_id, {}).get("name", model_id)
        await add_history(user_id, "user", message.text)
        await add_history(user_id, "assistant", answer_text)
        await log_user_request(user_id, "💬 Текст", message.text, answer_text, model_used=shown_model)

        async with aiosqlite.connect(DB_PATH) as db:
            await db.execute("UPDATE users SET total_requests = total_requests + 1 WHERE user_id = ?", (user_id,))
            await db.commit()

        await wait_msg.delete()
        await send_formatted_answer(message, answer_text)

    except Exception as e:
        await refund_quota(user_id, quota_receipt)
        await wait_msg.edit_text(
            f"⚠️ <b>Сервер нейросетей временно перегружен:</b>\n<code>{str(e)[:250]}</code>\n\nПопробуй повторить запрос через минуту.",
            parse_mode=ParseMode.HTML,
        )


async def setup_bot_commands(bot: Bot):
    commands = [
        BotCommand(command="start", description="Запустить бота / Главное меню"),
        BotCommand(command="menu", description="Выбрать нейросеть"),
        BotCommand(command="profile", description="Мой профиль, подписка и промокод"),
        BotCommand(command="shop", description="Купить подписку или пакет запросов"),
        BotCommand(command="ref", description="Партнёрка 25% и вывод средств"),
        BotCommand(command="docs", description="Документы, оферта и поддержка"),
        BotCommand(command="clear", description="Очистить память диалога"),
    ]
    await bot.set_my_commands(commands)


# ================= REST API ДЛЯ TELEGRAM MINI APP (VERCEL -> BOTHOST.RU) =================
def verify_telegram_webapp_init_data(init_data: str) -> dict | None:
    if not init_data:
        return None
    try:
        parsed = dict(parse_qsl(init_data, keep_blank_values=True))
        received_hash = parsed.pop("hash", "")
        if not received_hash:
            return None
        data_check_string = "\n".join(f"{k}={v}" for k, v in sorted(parsed.items()))
        secret_key = hmac.new(b"WebAppData", BOT_TOKEN.encode("utf-8"), hashlib.sha256).digest()
        calculated_hash = hmac.new(secret_key, data_check_string.encode("utf-8"), hashlib.sha256).hexdigest()
        if not hmac.compare_digest(calculated_hash, received_hash):
            return None
        user_raw = parsed.get("user")
        return json.loads(user_raw) if user_raw else None
    except Exception:
        return None


def verify_telegram_login_widget_data(auth_data: dict) -> bool:
    """Проверяет криптографическую подпись официального Telegram Login Widget."""
    if not isinstance(auth_data, dict):
        return False
    received_hash = str(auth_data.get("hash") or "").strip()
    if not received_hash:
        return False
    try:
        auth_date = int(auth_data.get("auth_date") or 0)
        if abs(time.time() - auth_date) > 86400:
            return False
        check_items = []
        for k, v in sorted(auth_data.items()):
            if k == "hash" or v is None or v == "":
                continue
            check_items.append(f"{k}={v}")
        data_check_string = "\n".join(check_items)
        secret_key = hashlib.sha256(BOT_TOKEN.encode("utf-8")).digest()
        calculated_hash = hmac.new(secret_key, data_check_string.encode("utf-8"), hashlib.sha256).hexdigest()
        return hmac.compare_digest(calculated_hash, received_hash)
    except Exception:
        return False


async def resolve_webapp_user(request: web.Request) -> dict | None:
    # 1. Вход из Telegram Mini App (initData)
    init_data = request.headers.get("X-Telegram-Init-Data", "").strip()
    tg_user = verify_telegram_webapp_init_data(init_data)
    if tg_user and tg_user.get("id"):
        uid = int(tg_user["id"])
        fname = f"{tg_user.get('first_name', '')} {tg_user.get('last_name', '')}".strip() or "Пользователь"
        uname = tg_user.get("username", "") or ""
        return await get_user(uid, full_name=fname, username=uname)

    # 2. Защищённый вход из браузера по сессионному токену (после подтверждения в Telegram)
    web_token = request.headers.get("X-Web-Auth-Token", "").strip()
    if web_token and len(web_token) >= 16:
        now = time.time()
        async with aiosqlite.connect(DB_PATH) as db:
            db.row_factory = aiosqlite.Row
            async with db.execute(
                "SELECT user_id FROM web_sessions WHERE token = ? AND expires_at > ?",
                (web_token, now),
            ) as cur:
                row = await cur.fetchone()
        if row:
            return await get_user(int(row["user_id"]))

    return None


@web.middleware
async def cors_middleware(request: web.Request, handler):
    if request.method == "OPTIONS":
        return web.Response(
            status=200,
            headers={
                "Access-Control-Allow-Origin": "*",
                "Access-Control-Allow-Methods": "GET, POST, OPTIONS",
                "Access-Control-Allow-Headers": "Content-Type, X-Telegram-Init-Data, X-Web-Auth-Token, X-User-Id",
            },
        )
    resp = await handler(request)
    resp.headers["Access-Control-Allow-Origin"] = "*"
    resp.headers["Access-Control-Allow-Methods"] = "GET, POST, OPTIONS"
    resp.headers["Access-Control-Allow-Headers"] = "Content-Type, X-Telegram-Init-Data, X-Web-Auth-Token, X-User-Id"
    return resp


async def start_miniapp_api_server(bot: Bot):
    me = await bot.get_me()
    bot_username = me.username or "AetherNeural_bot"

    async def api_health(request: web.Request):
        return web.json_response({"ok": True, "service": "AetherNeural MiniApp API"})

    async def api_me(request: web.Request):
        user = await resolve_webapp_user(request)
        if not user:
            return web.json_response({"ok": False, "error": "Открой Mini App внутри Telegram"}, status=401)
        uid = user["user_id"]
        pro_active = is_pro(user) or (uid == ADMIN_ID)
        total_daily = FREE_DAILY_LIMIT + (user.get("bonus_limit") or 0)
        left_daily = max(0, total_daily - (user.get("used_today") or 0))
        disc_info = await get_effective_discount(user)
        engine = await get_engine_model()

        async with aiosqlite.connect(DB_PATH) as db:
            async with db.execute(
                "SELECT COUNT(*) FROM users WHERE referred_by = ? AND ref_rewarded = 1",
                (uid,),
            ) as cur:
                ref_cnt = (await cur.fetchone())[0]

        host_hdr = request.headers.get("X-Forwarded-Host") or request.headers.get("Host") or ""
        proto_hdr = request.headers.get("X-Forwarded-Proto") or ("https" if host_hdr and not host_hdr.startswith("localhost") else "http")
        avatar_proxy_url = f"{proto_hdr}://{host_hdr}/api/avatar/{uid}" if host_hdr else ""

        return web.json_response({
            "ok": True,
            "user_id": uid,
            "full_name": user.get("full_name") or "Пользователь",
            "photo_url": avatar_proxy_url,
            "is_admin": uid == ADMIN_ID,
            "is_pro": pro_active,
            "selected_model": user.get("selected_model") or DEFAULT_ENGINE_MODEL,
            "engine_model": engine,
            "daily_left": left_daily,
            "daily_total": total_daily,
            "extra_requests": user.get("extra_requests") or 0,
            "ref_balance": float(user.get("ref_balance") or 0.0),
            "ref_count": ref_cnt,
            "ref_link": f"https://t.me/{bot_username}?start={uid}",
            "discount_percent": disc_info["percent"],
            "discount_until": disc_info["until"],
            "is_global_discount": disc_info["is_global"],
        })

    async def api_select_model(request: web.Request):
        user = await resolve_webapp_user(request)
        if not user:
            return web.json_response({"ok": False, "error": "Unauthorized"}, status=401)
        body = await request.json()
        model_id = str(body.get("model_id") or "").strip()
        m_info = ALL_MODELS_MAP.get(model_id)
        if not m_info:
            return web.json_response({"ok": False, "error": "Модель не найдена"}, status=400)
        pro_active = is_pro(user) or (user["user_id"] == ADMIN_ID)
        if m_info["pro"] and not pro_active:
            return web.json_response({"ok": False, "error": "Эта модель доступна только по подписке PRO"}, status=403)
        async with aiosqlite.connect(DB_PATH) as db:
            await db.execute("UPDATE users SET selected_model = ? WHERE user_id = ?", (model_id, user["user_id"]))
            await db.commit()
        return web.json_response({"ok": True, "selected_model": model_id})

    async def api_clear_history(request: web.Request):
        user = await resolve_webapp_user(request)
        if not user:
            return web.json_response({"ok": False, "error": "Unauthorized"}, status=401)
        await clear_history(user["user_id"])
        return web.json_response({"ok": True})

    async def api_chat(request: web.Request):
        user = await resolve_webapp_user(request)
        if not user:
            return web.json_response({"ok": False, "error": "Открой приложение внутри Telegram"}, status=401)
        uid = user["user_id"]
        if not await check_channel_sub(bot, uid):
            return web.json_response({"ok": False, "error": f"Подпишись на канал {CHANNEL_USERNAME} для доступа"}, status=403)

        body = await request.json()
        user_text = str(body.get("text") or "").strip()
        image_b64 = body.get("image_b64")
        req_model = str(body.get("model_id") or user.get("selected_model") or DEFAULT_ENGINE_MODEL).strip()

        if not user_text and not image_b64:
            return web.json_response({"ok": False, "error": "Пустой запрос"}, status=400)
        if is_content_forbidden(user_text):
            return web.json_response({"ok": False, "error": "Запрос отклонён системой безопасности"}, status=400)

        pro_active = is_pro(user) or (uid == ADMIN_ID)
        if ALL_MODELS_MAP.get(req_model, {}).get("pro") and not pro_active:
            return web.json_response({"ok": False, "error": "Срок PRO-подписки истёк"}, status=403)

        quota_receipt = await try_consume_quota(uid, pro_active, count=1)
        if not quota_receipt:
            return web.json_response({"ok": False, "error": "Дневной лимит и пакет запросов исчерпаны"}, status=402)

        engine_used = await get_engine_model()
        try:
            if image_b64:
                answer = await generate_photos_response(uid, req_model, user_text, [image_b64])
                log_q = f"[MiniApp Фото]: {user_text[:400]}"
                req_tag = "📸 MiniApp Фото"
            else:
                history = await get_history(uid)
                answer = await generate_text_response(uid, req_model, history, user_text)
                log_q = user_text
                req_tag = "💬 MiniApp Текст"

            await add_history(uid, "user", log_q)
            await add_history(uid, "assistant", answer)
            await log_user_request(uid, req_tag, log_q, answer, model_used=engine_used)

            async with aiosqlite.connect(DB_PATH) as db:
                await db.execute("UPDATE users SET total_requests = total_requests + 1 WHERE user_id = ?", (uid,))
                await db.commit()

            fresh = await get_user(uid)
            tot_d = FREE_DAILY_LIMIT + (fresh.get("bonus_limit") or 0)
            left_d = max(0, tot_d - (fresh.get("used_today") or 0))
            return web.json_response({
                "ok": True,
                "answer": answer,
                "engine_used": engine_used,
                "daily_left": left_d,
                "extra_requests": fresh.get("extra_requests") or 0,
            })
        except Exception as e:
            await refund_quota(uid, quota_receipt)
            return web.json_response({"ok": False, "error": str(e)[:220]}, status=500)

    async def api_promo(request: web.Request):
        user = await resolve_webapp_user(request)
        if not user:
            return web.json_response({"ok": False, "error": "Unauthorized"}, status=401)
        body = await request.json()
        code = str(body.get("code") or "").strip()
        ok, msg = await redeem_promocode(user["user_id"], code)
        if not ok:
            clean_err = re.sub(r"<[^>]+>", "", msg)
            return web.json_response({"ok": False, "error": clean_err}, status=400)
        return web.json_response({"ok": True, "message": re.sub(r"<[^>]+>", "", msg)})

    async def api_shop_sbp(request: web.Request):
        user = await resolve_webapp_user(request)
        if not user:
            return web.json_response({"ok": False, "error": "Unauthorized"}, status=401)
        body = await request.json()
        order_code = str(body.get("order_code") or "").strip()
        disc_info = await get_effective_discount(user)
        order = resolve_order_details(order_code, disc_info["percent"])
        if not order:
            return web.json_response({"ok": False, "error": "Товар не найден"}, status=400)
        try:
            tx_data = await platega_create_transaction(
                amount_rub=order["rub"],
                description=f"{order['title']} (ID {user['user_id']})",
                payload_str=f"{user['user_id']}:{order_code}",
            )
            async with aiosqlite.connect(DB_PATH) as db:
                await db.execute(
                    "INSERT INTO platega_transactions "
                    "(transaction_id, user_id, order_code, title, item_type, item_value, rub_amount, redirect_url, status, created_at) "
                    "VALUES (?, ?, ?, ?, ?, ?, ?, ?, 'PENDING', ?)",
                    (
                        tx_data["transaction_id"],
                        user["user_id"],
                        order_code,
                        order["title"],
                        order["type"],
                        order["value"],
                        float(order["rub"]),
                        tx_data["redirect"],
                        time.time(),
                    ),
                )
                await db.commit()
            return web.json_response({"ok": True, "pay_url": tx_data["redirect"], "tx_id": tx_data["transaction_id"]})
        except Exception as e:
            return web.json_response({"ok": False, "error": str(e)[:200]}, status=500)

    async def api_shop_stars(request: web.Request):
        user = await resolve_webapp_user(request)
        if not user:
            return web.json_response({"ok": False, "error": "Открой Mini App внутри Telegram"}, status=401)
        try:
            body = await request.json()
            order_code = str(body.get("order_code") or "").strip()
            disc_info = await get_effective_discount(user)
            pct = disc_info["percent"]
            order = resolve_order_details(order_code, pct)
            if not order:
                return web.json_response({"ok": False, "error": "Товар не найден"}, status=400)
            desc = (
                f"Безлимитный доступ ко всем моделям на {order['value']} дн."
                if order["type"] == "sub"
                else f"Пакет на {order['value']} дополнительных запросов."
            )
            inv_title = order["title"] + (f" (Скидка {pct}%)" if (pct > 0 and order["stars"] >= 5) else "")
            prices = [LabeledPrice(label=order["title"], amount=order["stars"])]
            inv_url = await bot.create_invoice_link(
                title=inv_title,
                description=desc,
                payload=f"ord:{order_code}",
                provider_token="",
                currency="XTR",
                prices=prices,
            )
            sent_to_tg = False
            try:
                await bot.send_invoice(
                    chat_id=user["user_id"],
                    title=inv_title,
                    description=desc,
                    payload=f"ord:{order_code}",
                    provider_token="",
                    currency="XTR",
                    prices=prices,
                )
                sent_to_tg = True
            except Exception:
                sent_to_tg = False
            return web.json_response({"ok": True, "invoice_url": inv_url, "sent_to_tg": sent_to_tg})
        except Exception as e:
            return web.json_response({"ok": False, "error": str(e)[:200]}, status=500)

    async def api_withdraw(request: web.Request):
        user = await resolve_webapp_user(request)
        if not user:
            return web.json_response({"ok": False, "error": "Unauthorized"}, status=401)
        body = await request.json()
        reqs = str(body.get("requisites") or "").strip()
        if len(reqs) < 5:
            return web.json_response({"ok": False, "error": "Укажи корректные реквизиты"}, status=400)
        uid = user["user_id"]
        async with get_user_lock(uid):
            fresh = await get_user(uid)
            bal = fresh.get("ref_balance") or 0.0
            if bal < MIN_WITHDRAW_RUB:
                return web.json_response({"ok": False, "error": f"Минимум {int(MIN_WITHDRAW_RUB)} ₽"}, status=400)
            async with aiosqlite.connect(DB_PATH) as db:
                await db.execute("UPDATE users SET ref_balance = 0 WHERE user_id = ?", (uid,))
                cur = await db.execute(
                    "INSERT INTO withdrawals (user_id, amount, requisites, status, created_at) VALUES (?, ?, ?, 'pending', ?)",
                    (uid, bal, reqs[:150], time.time()),
                )
                wid = cur.lastrowid
                await db.commit()
        try:
            await bot.send_message(
                ADMIN_ID,
                f"💸 <b>Заявка на вывод #{wid} из Mini App!</b>\n👤 <code>{uid}</code> | 💰 <b>{bal:.2f} ₽</b>\n🏦 <code>{html.escape(reqs[:150])}</code>",
                parse_mode=ParseMode.HTML,
            )
        except Exception:
            pass
        return web.json_response({"ok": True, "withdrawal_id": wid})

    async def api_admin_stats(request: web.Request):
        user = await resolve_webapp_user(request)
        if not user or user["user_id"] != ADMIN_ID:
            return web.json_response({"ok": False, "error": "Forbidden"}, status=403)
        async with aiosqlite.connect(DB_PATH) as db:
            async with db.execute("SELECT COUNT(*) FROM users") as cur:
                total_users = (await cur.fetchone())[0]
            async with db.execute("SELECT COUNT(*) FROM users WHERE pro_until > ?", (time.time(),)) as cur:
                pro_users = (await cur.fetchone())[0]
            async with db.execute("SELECT COALESCE(SUM(stars), 0) FROM payments") as cur:
                total_stars = (await cur.fetchone())[0]
            async with db.execute("SELECT COALESCE(SUM(rub_amount), 0) FROM payments WHERE method = 'sbp'") as cur:
                total_sbp_rub = (await cur.fetchone())[0]
        return web.json_response({
            "ok": True,
            "total_users": total_users,
            "pro_users": pro_users,
            "total_stars": total_stars,
            "total_sbp_rub": total_sbp_rub,
            "engine_model": await get_engine_model(),
            "global_discount": await get_global_discount(),
        })

    async def api_admin_set_engine(request: web.Request):
        user = await resolve_webapp_user(request)
        if not user or user["user_id"] != ADMIN_ID:
            return web.json_response({"ok": False, "error": "Forbidden"}, status=403)
        body = await request.json()
        new_engine = str(body.get("engine_model") or "").strip()
        if not new_engine or " " in new_engine:
            return web.json_response({"ok": False, "error": "Некорректный ID модели"}, status=400)
        await set_engine_model(new_engine)
        return web.json_response({"ok": True, "engine_model": new_engine})

    async def api_admin_global_discount(request: web.Request):
        user = await resolve_webapp_user(request)
        if not user or user["user_id"] != ADMIN_ID:
            return web.json_response({"ok": False, "error": "Forbidden"}, status=403)
        body = await request.json()
        pct = int(body.get("percent") or 0)
        hrs = int(body.get("hours") or 0)
        if pct <= 0 or hrs <= 0:
            await set_setting("global_discount_percent", "0")
            await set_setting("global_discount_until", "0")
        else:
            await set_setting("global_discount_percent", str(min(95, pct)))
            await set_setting("global_discount_until", str(time.time() + hrs * 3600))
        return web.json_response({"ok": True, "global_discount": await get_global_discount()})

    async def api_admin_logs(request: web.Request):
        user = await resolve_webapp_user(request)
        if not user or user["user_id"] != ADMIN_ID:
            return web.json_response({"ok": False, "error": "Forbidden"}, status=403)
        async with aiosqlite.connect(DB_PATH) as db:
            db.row_factory = aiosqlite.Row
            async with db.execute(
                "SELECT rl.*, COALESCE(u.full_name, 'Пользователь') AS full_name "
                "FROM request_logs rl LEFT JOIN users u ON u.user_id = rl.user_id "
                "ORDER BY rl.id DESC LIMIT 25"
            ) as cur:
                rows = await cur.fetchall()
        logs = [
            {
                "id": r["id"],
                "user_id": r["user_id"],
                "full_name": r["full_name"],
                "req_type": r["req_type"],
                "user_query": (r["user_query"] or "")[:300],
                "bot_reply": (r["bot_reply"] or "")[:200],
                "created_at": r["created_at"],
            }
            for r in rows
        ]
        return web.json_response({"ok": True, "logs": logs})

    async def api_auth_telegram_widget(request: web.Request):
        body = await request.json()
        if not verify_telegram_login_widget_data(body):
            return web.json_response({"ok": False, "error": "Неверная подпись Telegram Login Widget"}, status=401)
        uid = int(body["id"])
        fname = f"{body.get('first_name', '')} {body.get('last_name', '')}".strip() or body.get("username") or "Пользователь"
        uname = body.get("username", "") or ""
        await get_user(uid, full_name=fname, username=uname)
        token = secrets.token_urlsafe(32)
        now = time.time()
        async with aiosqlite.connect(DB_PATH) as db:
            await db.execute(
                "INSERT INTO web_sessions (token, user_id, created_at, expires_at) VALUES (?, ?, ?, ?)",
                (token, uid, now, now + 30 * 86400),
            )
            await db.commit()
        return web.json_response({"ok": True, "token": token, "user_id": uid, "full_name": fname})

    async def api_auth_verify_code(request: web.Request):
        body = await request.json()
        code = str(body.get("code") or "").strip().upper()
        if not code:
            return web.json_response({"ok": False, "error": "Введи код из бота"}, status=400)
        now = time.time()
        async with aiosqlite.connect(DB_PATH) as db:
            db.row_factory = aiosqlite.Row
            async with db.execute(
                "SELECT user_id, expires_at FROM web_auth_codes WHERE code = ?",
                (code,),
            ) as cur:
                row = await cur.fetchone()
            if not row or float(row["expires_at"]) < now:
                return web.json_response({"ok": False, "error": "Код неверный или устарел. Получи новый в боте."}, status=401)
            uid = int(row["user_id"])
            await db.execute("DELETE FROM web_auth_codes WHERE code = ?", (code,))
            token = secrets.token_urlsafe(32)
            await db.execute(
                "INSERT INTO web_sessions (token, user_id, created_at, expires_at) VALUES (?, ?, ?, ?)",
                (token, uid, now, now + 30 * 86400),
            )
            await db.commit()
        user = await get_user(uid)
        return web.json_response({
            "ok": True,
            "token": token,
            "user_id": uid,
            "full_name": user.get("full_name") or "Пользователь",
        })

    async def api_history(request: web.Request):
        user = await resolve_webapp_user(request)
        if not user:
            return web.json_response({"ok": False, "error": "Unauthorized"}, status=401)
        hist = await get_history(user["user_id"])
        return web.json_response({"ok": True, "messages": hist})

    async def api_get_sessions(request: web.Request):
        user = await resolve_webapp_user(request)
        if not user:
            return web.json_response({"ok": False, "error": "Unauthorized"}, status=401)
        uid = user["user_id"]
        async with aiosqlite.connect(DB_PATH) as db:
            db.row_factory = aiosqlite.Row
            async with db.execute(
                "SELECT sessions_json, updated_at FROM user_sessions WHERE user_id = ?",
                (uid,),
            ) as cur:
                row = await cur.fetchone()
        sessions = []
        updated_at = 0.0
        if row and row["sessions_json"]:
            try:
                sessions = json.loads(row["sessions_json"])
                updated_at = float(row["updated_at"] or 0)
            except Exception:
                sessions = []
        return web.json_response({"ok": True, "sessions": sessions, "updated_at": updated_at})

    async def api_save_sessions(request: web.Request):
        user = await resolve_webapp_user(request)
        if not user:
            return web.json_response({"ok": False, "error": "Unauthorized"}, status=401)
        uid = user["user_id"]
        body = await request.json()
        sessions = body.get("sessions")
        if not isinstance(sessions, list):
            return web.json_response({"ok": False, "error": "Invalid sessions"}, status=400)
        trimmed = sessions[:35]
        now_ts = time.time()
        async with aiosqlite.connect(DB_PATH) as db:
            await db.execute(
                "INSERT INTO user_sessions (user_id, sessions_json, updated_at) VALUES (?, ?, ?) "
                "ON CONFLICT(user_id) DO UPDATE SET sessions_json = excluded.sessions_json, updated_at = excluded.updated_at",
                (uid, json.dumps(trimmed, ensure_ascii=False), now_ts),
            )
            await db.commit()
        return web.json_response({"ok": True, "updated_at": now_ts})

    app = web.Application(middlewares=[cors_middleware], client_max_size=12 * 1024 * 1024)
    async def api_user_avatar(request: web.Request):
        uid_str = request.match_info.get("uid", "")
        if not uid_str.isdigit():
            return web.Response(status=404)
        uid = int(uid_str)
        try:
            photos = await bot.get_user_profile_photos(user_id=uid, limit=1)
            if not photos.total_count or not photos.photos:
                return web.Response(status=404)
            best_photo = photos.photos[0][-1]
            f_info = await bot.get_file(best_photo.file_id)
            bio = await bot.download_file(f_info.file_path)
            img_bytes = bio.read()
            return web.Response(
                body=img_bytes,
                content_type="image/jpeg",
                headers={"Cache-Control": "public, max-age=3600"},
            )
        except Exception:
            return web.Response(status=404)

    app.router.add_get("/", api_health)
    app.router.add_get("/api/avatar/{uid}", api_user_avatar)
    app.router.add_post("/api/auth/telegram-widget", api_auth_telegram_widget)
    app.router.add_post("/api/auth/verify-code", api_auth_verify_code)
    app.router.add_get("/api/history", api_history)
    app.router.add_get("/api/sessions", api_get_sessions)
    app.router.add_post("/api/sessions", api_save_sessions)
    app.router.add_get("/api/me", api_me)
    app.router.add_post("/api/select-model", api_select_model)
    app.router.add_post("/api/clear-history", api_clear_history)
    app.router.add_post("/api/chat", api_chat)
    app.router.add_post("/api/promo", api_promo)
    app.router.add_post("/api/shop/create-sbp", api_shop_sbp)
    app.router.add_post("/api/shop/create-stars", api_shop_stars)
    app.router.add_post("/api/withdraw", api_withdraw)
    app.router.add_get("/api/admin/stats", api_admin_stats)
    app.router.add_post("/api/admin/set-engine", api_admin_set_engine)
    app.router.add_post("/api/admin/global-discount", api_admin_global_discount)
    app.router.add_get("/api/admin/logs", api_admin_logs)

    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, "0.0.0.0", WEBAPP_PORT)
    await site.start()
    print(f"Mini App API запущен на порту {WEBAPP_PORT}")


async def main():
    await init_db()
    bot = Bot(token=BOT_TOKEN)
    await setup_bot_commands(bot)
    await start_miniapp_api_server(bot)
    asyncio.create_task(delayed_discount_watcher(bot))
    asyncio.create_task(platega_status_watcher(bot))
    dp = Dispatcher()
    dp.include_router(router)
    print("Бот запущен!")
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
