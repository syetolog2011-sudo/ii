import asyncio
import base64
import html
import io
import os
import random
import re
import shutil
import string
import time
from datetime import date, datetime
from urllib.parse import quote
import aiosqlite
from PIL import Image
from aiogram import Bot, Dispatcher, F, Router
from aiogram.filters import CommandStart, Command
from aiogram.types import (
    Message,
    CallbackQuery,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
    LabeledPrice,
    PreCheckoutQuery,
    BotCommand,
    FSInputFile,
)
from aiogram.enums import ParseMode
from aiogram.exceptions import TelegramBadRequest
from openai import AsyncOpenAI

# ================= НАСТРОЙКИ ДЛЯ ХОСТИНГА (ENV) =================
BOT_TOKEN = os.getenv("BOT_TOKEN", "").strip()
UNLOCK_API_KEY = os.getenv("UNLOCK_API_KEY", "").strip()
UNLOCK_BASE_URL = os.getenv("UNLOCK_BASE_URL", "https" + "://" + "unlockapi.space/v1").strip()

if not BOT_TOKEN:
    raise RuntimeError("Не задана переменная окружения BOT_TOKEN! Добавь её в настройках хостинга.")
if not UNLOCK_API_KEY:
    raise RuntimeError("Не задана переменная окружения UNLOCK_API_KEY! Добавь её в настройках хостинга.")

ADMIN_ID = int(os.getenv("ADMIN_ID", "1991878700"))

CHANNEL_USERNAME = os.getenv("CHANNEL_USERNAME", "@AetherNeural")
CHANNEL_URL = os.getenv("CHANNEL_URL", "https" + "://" + "t.me/AetherNeural")

DB_PATH = os.getenv("DB_PATH", "data/users.sqlite3")

FREE_DAILY_LIMIT = 5
PHOTO_COST = 1          # Разбор 1 фото = 1 запрос
VIDEO_COST = 1          # Разбор 1 видео = 1 запрос
MAX_ALBUM_PHOTOS = 4
MAX_HISTORY_MESSAGES = 16
DEFAULT_ENGINE_MODEL = "gpt-6-luna"
VISION_MODEL = os.getenv("VISION_MODEL", "gemini-3.5-flash-lite").strip()
WHISPER_MODEL = os.getenv("WHISPER_MODEL", "whisper-1").strip()
USERS_PER_PAGE = 8

DISCOUNT_DELAY_SECONDS = 2 * 3600      # Через 2 часа после первого сообщения
DISCOUNT_DURATION_SECONDS = 36 * 3600  # Скидка действует 36 часов

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

VISION_FALLBACK_MODELS = [
    VISION_MODEL,
    "gemini-3.5-flash-lite",
    "gemini-3.1-flash-lite",
    "gpt-5-mini",
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
    "sub_trial": {"type": "sub", "title": "Пробный 1 день", "stars": 59, "value": 1},
    "sub_standard": {"type": "sub", "title": "Стандарт 7 дней", "stars": 149, "value": 7},
    "sub_premium": {"type": "sub", "title": "Премиум 30 дней", "stars": 349, "value": 30},
    "pack_30": {"type": "pack", "title": "Пакет +30 запросов", "stars": 79, "value": 30},
    "pack_100": {"type": "pack", "title": "Пакет +100 запросов", "stars": 199, "value": 100},
    "pack_300": {"type": "pack", "title": "Пакет +300 запросов", "stars": 449, "value": 300},
}

SYSTEM_PROMPT = (
    "Отвечай четко, по делу и на языке пользователя. "
    "Никогда не используй Markdown-разметку со звездочками (** или *) и решетками (###). Пиши обычным чистым текстом без выделения звездочками. "
    "Никогда не используй LaTeX-разметку (\\frac, \\cdot, \\times, \\[,\\], $$, \\sqrt и обратные слэши \\). "
    "Все математические и химические формулы пиши обычными читаемыми символами: *, /, ^, =, √, индексы цифрами (например, H2O, x^2, (a + b) / 2)."
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
MEDIA_GROUP_BUFFER: dict[str, list[Message]] = {}
USER_QUOTA_LOCKS: dict[int, asyncio.Lock] = {}


def get_user_lock(user_id: int) -> asyncio.Lock:
    if user_id not in USER_QUOTA_LOCKS:
        USER_QUOTA_LOCKS[user_id] = asyncio.Lock()
    return USER_QUOTA_LOCKS[user_id]


# ================= СЖАТИЕ ФОТО ДЛЯ МИНИМАЛЬНОГО РАСХОДА ТОКЕНОВ =================
def compress_image_bytes(raw_bytes: bytes, max_side: int = 1024, quality: int = 75) -> str:
    img = Image.open(io.BytesIO(raw_bytes))
    if img.mode in ("RGBA", "P", "LA"):
        bg = Image.new("RGB", img.size, (255, 255, 255))
        if img.mode == "P":
            img = img.convert("RGBA")
        bg.paste(img, mask=img.split()[-1] if "A" in img.mode else None)
        img = bg
    elif img.mode != "RGB":
        img = img.convert("RGB")

    w, h = img.size
    if max(w, h) > max_side:
        if w >= h:
            new_w = max_side
            new_h = max(1, int(h * (max_side / w)))
        else:
            new_h = max_side
            new_w = max(1, int(w * (max_side / h)))
        img = img.resize((new_w, new_h), Image.Resampling.LANCZOS)

    out = io.BytesIO()
    img.save(out, format="JPEG", quality=quality, optimize=True)
    return base64.b64encode(out.getvalue()).decode("utf-8")


# ================= ОЧИСТКА И ФОРМАТИРОВАНИЕ ОТВЕТОВ НЕЙРОСЕТИ =================
def format_ai_response(raw_text: str) -> tuple[str, str]:
    text = raw_text.replace("\r\n", "\n")

    text = re.sub(r"\\\[\vert{}\\\]|\\\(\vert{}\\\)", "", text)
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


# ================= ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ НЕДЕЛИ И ЦЕН =================
def current_week_key() -> str:
    iso = date.today().isocalendar()
    return f"{iso.year}-W{iso.week:02d}"


def has_active_discount(user: dict) -> bool:
    return (user.get("discount_until") or 0) > time.time()


def get_product_price(product: dict, discount_active: bool) -> int:
    base = product["stars"]
    if discount_active:
        return max(1, round(base * 0.5))
    return base


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
                paid_at REAL
            )
        """)
        await db.execute("""
            CREATE TABLE IF NOT EXISTS weekly_refs (
                week_key TEXT,
                referrer_id INTEGER,
                count INTEGER DEFAULT 0,
                PRIMARY KEY (week_key, referrer_id)
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
        await db.execute(
            "INSERT OR IGNORE INTO bot_settings (key, value) VALUES ('engine_model', ?)",
            (DEFAULT_ENGINE_MODEL,),
        )
        await db.execute(
            "INSERT OR IGNORE INTO bot_settings (key, value) VALUES ('active_week', ?)",
            (current_week_key(),),
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
            wk = current_week_key()
            await db.execute("UPDATE users SET ref_rewarded = 1 WHERE user_id = ?", (user_id,))
            await db.execute("UPDATE users SET bonus_limit = bonus_limit + 2 WHERE user_id = ?", (ref_id,))
            await db.execute(
                """
                INSERT INTO weekly_refs (week_key, referrer_id, count)
                VALUES (?, ?, 1)
                ON CONFLICT(week_key, referrer_id) DO UPDATE SET count = count + 1
                """,
                (wk, ref_id),
            )
            await db.commit()
            try:
                await bot.send_message(
                    ref_id,
                    "🎉 По твоей ссылке подписался на канал новый друг!\n"
                    "• Начислено <b>+2 запроса в день</b>\n"
                    "• Засчитан <b>+1 балл</b> в еженедельный лидерборд (/top)!",
                    parse_mode=ParseMode.HTML,
                )
            except Exception:
                pass


# ================= ФОНОВЫЙ ПЛАНИРОВЩИК: СКИДКА 50% НА 36 ЧАСОВ ЧЕРЕЗ 2 ЧАСА =================
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
                        "🔥 <b>ПЕРСОНАЛЬНАЯ СКИДКА 50% НА 36 ЧАСОВ УЖЕ АКТИВНА!</b>\n\n"
                        "Мы снизили цены вдвое на все тарифы и пакеты запросов специально для тебя на ближайшие <b>36 часов</b> (скидка уже применена ко всем ценам ниже):\n\n"
                        "👑 <b>Подписки (безлимит на все PRO-модели):</b>\n"
                        f"• Пробный 1 день: <s>59 ⭐</s> → <b>{get_product_price(PRODUCTS['sub_trial'], True)} ⭐</b>\n"
                        f"• Стандарт 7 дней: <s>149 ⭐</s> → <b>{get_product_price(PRODUCTS['sub_standard'], True)} ⭐</b>\n"
                        f"• Премиум 30 дней: <s>349 ⭐</s> → <b>{get_product_price(PRODUCTS['sub_premium'], True)} ⭐</b>\n\n"
                        "⚡ <b>Пакеты запросов (расходуются после дневного лимита):</b>\n"
                        f"• +30 запросов: <s>79 ⭐</s> → <b>{get_product_price(PRODUCTS['pack_30'], True)} ⭐</b>\n"
                        f"• +100 запросов: <s>199 ⭐</s> → <b>{get_product_price(PRODUCTS['pack_100'], True)} ⭐</b>\n"
                        f"• +300 запросов: <s>449 ⭐</s> → <b>{get_product_price(PRODUCTS['pack_300'], True)} ⭐</b>\n\n"
                        "👇 Жми на любой тариф прямо сейчас, пока действует акция:"
                    )
                    try:
                        await bot.send_message(
                            uid,
                            offer_text,
                            reply_markup=shop_kb(discount_active=True),
                            parse_mode=ParseMode.HTML,
                        )
                    except Exception:
                        pass

                    await asyncio.sleep(0.1)
        except Exception:
            pass
        await asyncio.sleep(60)


# ================= ЕЖЕНЕДЕЛЬНЫЙ ЛИДЕРБОРД И НАГРАДЫ =================
async def distribute_weekly_rewards(bot: Bot, week_to_close: str) -> str:
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute(
            """
            SELECT w.referrer_id, w.count, u.full_name, u.pro_until
            FROM weekly_refs w
            LEFT JOIN users u ON u.user_id = w.referrer_id
            WHERE w.week_key = ? AND w.count > 0
            ORDER BY w.count DESC
            LIMIT 10
            """,
            (week_to_close,),
        ) as cur:
            winners = await cur.fetchall()

        if not winners:
            return f"Неделя {week_to_close}: участников в топе не было."

        report_lines = [f"🏆 <b>Итоги лидерборда за неделю {week_to_close}:</b>\n"]
        now = time.time()

        for idx, w in enumerate(winners, start=1):
            uid = w["referrer_id"]
            cnt = w["count"]
            name = html.escape(w["full_name"] or str(uid))

            if idx == 1:
                days = 30
                new_until = max(now, w["pro_until"] or 0) + days * 86400
                await db.execute("UPDATE users SET pro_until = ? WHERE user_id = ?", (new_until, uid))
                prize_text = "👑 Подписка на 30 дней"
            elif idx == 2:
                days = 15
                new_until = max(now, w["pro_until"] or 0) + days * 86400
                await db.execute("UPDATE users SET pro_until = ? WHERE user_id = ?", (new_until, uid))
                prize_text = "🥈 Подписка на 15 дней"
            elif idx == 3:
                days = 7
                new_until = max(now, w["pro_until"] or 0) + days * 86400
                await db.execute("UPDATE users SET pro_until = ? WHERE user_id = ?", (new_until, uid))
                prize_text = "🥉 Подписка на 7 дней"
            else:
                await db.execute("UPDATE users SET extra_requests = extra_requests + 20 WHERE user_id = ?", (uid,))
                prize_text = "⚡ Пакет +20 запросов"

            report_lines.append(f"{idx}. <b>{name}</b> ({cnt} реф.) — {prize_text}")

            try:
                await bot.send_message(
                    uid,
                    f"🏆 <b>Поздравляем! Ты занял {idx} место в недельном лидерборде!</b>\n"
                    f"Приглашено друзей: <b>{cnt}</b>\n"
                    f"Твоя награда: <b>{prize_text}</b> уже зачислена на аккаунт!",
                    parse_mode=ParseMode.HTML,
                )
            except Exception:
                pass

        await db.commit()
        return "\n".join(report_lines)


async def weekly_leaderboard_watcher(bot: Bot):
    while True:
        try:
            saved_week = await get_setting("active_week", current_week_key())
            now_week = current_week_key()
            if saved_week != now_week:
                report = await distribute_weekly_rewards(bot, saved_week)
                await set_setting("active_week", now_week)
                try:
                    await bot.send_message(ADMIN_ID, report, parse_mode=ParseMode.HTML)
                except Exception:
                    pass
        except Exception:
            pass
        await asyncio.sleep(600)


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
            InlineKeyboardButton(text="🏆 Топ недели", callback_data="leaderboard"),
        ],
        [
            InlineKeyboardButton(text="👥 +2 за друга", callback_data="ref_info"),
        ],
    ]
    if user_id == ADMIN_ID:
        buttons.append([InlineKeyboardButton(text="🛠 Админ-панель", callback_data="admin_panel")])

    return InlineKeyboardMarkup(inline_keyboard=buttons)


def models_in_category_kb(cat_key: str, current_model: str, pro_active: bool) -> InlineKeyboardMarkup:
    cat = CATEGORIES[cat_key]
    buttons = []
    for m in cat["models"]:
        check = "✅ " if m["id"] == current_model else ""
        lock = "🔒 " if (m["pro"] and not pro_active) else ""
        btn_text = f"{check}{lock}{m['name']} [{m['tag']}]"
        buttons.append([InlineKeyboardButton(text=btn_text, callback_data=f"set_model:{cat_key}:{m['id']}")])

    buttons.append([InlineKeyboardButton(text="⬅️ Назад к категориям", callback_data="back_cats")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def shop_kb(discount_active: bool = False) -> InlineKeyboardMarkup:
    buttons = []
    for key, p in PRODUCTS.items():
        price = get_product_price(p, discount_active)
        if discount_active:
            label = f"🔥 {p['title']} — {price} ⭐ (вместо {p['stars']})"
        else:
            icon = "👑" if p["type"] == "sub" else "⚡"
            label = f"{icon} {p['title']} — {price} ⭐"
        buttons.append([InlineKeyboardButton(text=label, callback_data=f"buy:{key}")])

    buttons.append([InlineKeyboardButton(text="⬅️ Назад в меню", callback_data="back_cats")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def render_shop_text(user: dict) -> str:
    disc = has_active_discount(user)
    if disc:
        exp = datetime.fromtimestamp(user["discount_until"]).strftime("%d.%m %H:%M")
        header = f"🔥 <b>АКТИВНА ПЕРСОНАЛЬНАЯ СКИДКА 50% (до {exp})!</b>\nВсе цены ниже снижены вдвое:\n\n"
    else:
        header = "⭐ <b>Магазин подписок и пакетов</b>\n\n"

    lines = [header, "👑 <b>Безлимитные подписки (все PRO-модели):</b>"]
    for key in ("sub_trial", "sub_standard", "sub_premium"):
        p = PRODUCTS[key]
        price = get_product_price(p, disc)
        if disc:
            lines.append(f"• {p['title']}: <s>{p['stars']} ⭐</s> → <b>{price} ⭐</b>")
        else:
            lines.append(f"• {p['title']} — <b>{price} ⭐</b>")

    lines.append("\n⚡ <b>Пакеты запросов (расходуются после дневного лимита):</b>")
    for key in ("pack_30", "pack_100", "pack_300"):
        p = PRODUCTS[key]
        price = get_product_price(p, disc)
        if disc:
            lines.append(f"• {p['title']}: <s>{p['stars']} ⭐</s> → <b>{price} ⭐</b>")
        else:
            lines.append(f"• {p['title']} — <b>{price} ⭐</b>")

    return "\n".join(lines)


def profile_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="🎟 Активировать промокод", callback_data="promo_enter")],
            [InlineKeyboardButton(text="⭐ Купить подписку или пакет", callback_data="shop")],
            [InlineKeyboardButton(text="🏆 Лидерборд недели", callback_data="leaderboard")],
            [InlineKeyboardButton(text="🧹 Сброс чата", callback_data="clear_chat")],
            [InlineKeyboardButton(text="⬅️ Назад в меню", callback_data="back_cats")],
        ]
    )


async def admin_kb() -> InlineKeyboardMarkup:
    engine = await get_engine_model()
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="👥 Пользователи (просмотр / выдача / снятие)", callback_data="adm_users:0")],
            [InlineKeyboardButton(text="📢 Рассылка всем пользователям", callback_data="adm_broadcast")],
            [InlineKeyboardButton(text=f"⚙️ Общий движок (текст): {engine}", callback_data="adm_set_engine")],
            [InlineKeyboardButton(text="🎟 Создать промокод", callback_data="adm_promo_create")],
            [InlineKeyboardButton(text="📋 Список промокодов", callback_data="adm_promo_list")],
            [InlineKeyboardButton(text="🏆 Завершить неделю и выдать призы", callback_data="adm_finish_week")],
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


# ================= ВИДЕО (АНАЛИЗ В GEMINI / CLAUDE / GPT, 1 ВИДЕО = 1 ЗАПРОС) =================
async def generate_video_response(
    user_id: int, selected_model: str, caption: str, b64_video: str, mime_type: str
) -> str:
    if user_id == ADMIN_ID and selected_model:
        candidates = [selected_model] + [m for m in VIDEO_FALLBACK_MODELS if m != selected_model]
    else:
        engine = await get_engine_model()
        candidates = [engine] + [m for m in VIDEO_FALLBACK_MODELS if m != engine]

    user_content = [
        {"type": "text", "text": caption},
        {"type": "image_url", "image_url": {"url": f"data:{mime_type};base64,{b64_video}"}},
    ]
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
                max_tokens=1500,
            )
            content = response.choices[0].message.content
            if content:
                return content
        except Exception as e:
            last_error = e
            continue

    raise last_error or RuntimeError("Выбранная модель временно не смогла обработать видео")


@router.message(F.video)
async def handle_video(message: Message, bot: Bot):
    user_id = message.from_user.id
    user = await get_user(user_id, full_name=message.from_user.full_name, username=message.from_user.username or "")
    if not await ensure_subscribed(bot, user_id, message):
        return

    video = message.video
    if video.file_size and video.file_size > 20 * 1024 * 1024:
        await message.answer("⚠️ Видео слишком тяжёлое (лимит Telegram для ботов — до 20 МБ). Сожми видео или обрежь его.")
        return

    model_id = user["selected_model"]
    pro_active = is_pro(user) or (user_id == ADMIN_ID)
    if ALL_MODELS_MAP.get(model_id, {}).get("pro") and not pro_active:
        disc = has_active_discount(user)
        await message.answer(
            "🔒 Срок подписки истек. Выбери бесплатную модель в /menu или продли тариф:",
            reply_markup=shop_kb(disc),
        )
        return

    quota_receipt = await try_consume_quota(user_id, pro_active, count=VIDEO_COST)
    if not quota_receipt:
        disc = has_active_discount(user)
        await message.answer(
            "⏳ Бесплатный лимит на сегодня и пакет запросов исчерпаны.\n"
            "Приходи завтра, пригласи друга за +2 запроса (/top) или оформи подписку / пакет:",
            reply_markup=shop_kb(disc),
            parse_mode=ParseMode.HTML,
        )
        return

    shown_model = ALL_MODELS_MAP.get(model_id, {}).get("name", model_id)
    wait_msg = await message.answer(f"🎬 <i>Анализирую видео ({shown_model})...</i>", parse_mode=ParseMode.HTML)

    try:
        file_info = await bot.get_file(video.file_id)
        downloaded = await bot.download_file(file_info.file_path)
        b64_video = base64.b64encode(downloaded.read()).decode("utf-8")
        mime_type = video.mime_type or "video/mp4"
        caption = (message.caption or "").strip() or "Подробно разбери, что происходит на этом видео, и ответь на задание или вопрос."

        answer_text = await generate_video_response(
            user_id=user_id,
            selected_model=model_id,
            caption=caption,
            b64_video=b64_video,
            mime_type=mime_type,
        )

        await add_history(user_id, "user", f"[Отправил видео с подписью: {caption}]")
        await add_history(user_id, "assistant", answer_text)

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
            f"⚠️ <b>Не удалось обработать видео:</b>\n<code>{str(e)[:250]}</code>",
            parse_mode=ParseMode.HTML,
        )


# ================= ГОЛОСОВЫЕ СООБЩЕНИЯ (AUDIO -> WHISPER -> НЕЙРОСЕТЬ) =================
@router.message(F.voice)
async def handle_voice(message: Message, bot: Bot):
    user_id = message.from_user.id
    user = await get_user(user_id, full_name=message.from_user.full_name, username=message.from_user.username or "")
    if not await ensure_subscribed(bot, user_id, message):
        return

    model_id = user["selected_model"]
    pro_active = is_pro(user) or (user_id == ADMIN_ID)
    if ALL_MODELS_MAP.get(model_id, {}).get("pro") and not pro_active:
        disc = has_active_discount(user)
        await message.answer(
            "🔒 Срок подписки истек. Выбери бесплатную модель в /menu или продли тариф:",
            reply_markup=shop_kb(disc),
        )
        return

    quota_receipt = await try_consume_quota(user_id, pro_active, count=1)
    if not quota_receipt:
        disc = has_active_discount(user)
        await message.answer(
            "⏳ Бесплатный лимит на сегодня и пакет запросов исчерпаны.\n"
            "Приходи завтра, пригласи друга за +2 запроса (/top) или оформи подписку / пакет:",
            reply_markup=shop_kb(disc),
        )
        return

    wait_msg = await message.answer("🎙 <i>Слушаю голосовое и готовлю ответ...</i>", parse_mode=ParseMode.HTML)
    try:
        file_info = await bot.get_file(message.voice.file_id)
        downloaded = await bot.download_file(file_info.file_path)
        audio_bio = io.BytesIO(downloaded.read())
        audio_bio.name = "voice.ogg"

        transcript = await ai_client.audio.transcriptions.create(
            model=WHISPER_MODEL,
            file=audio_bio,
        )
        recognized_text = (getattr(transcript, "text", None) or "").strip()
        if not recognized_text:
            raise RuntimeError("Не удалось разобрать слова в голосовом сообщении")

        history = await get_history(user_id)
        answer_text = await generate_text_response(
            user_id=user_id,
            selected_model=model_id,
            history=history,
            user_text=recognized_text,
        )

        await add_history(user_id, "user", recognized_text)
        await add_history(user_id, "assistant", answer_text)

        async with aiosqlite.connect(DB_PATH) as db:
            await db.execute("UPDATE users SET total_requests = total_requests + 1 WHERE user_id = ?", (user_id,))
            await db.commit()

        await wait_msg.delete()
        full_reply = f"🗣 Вы сказали: {recognized_text}\n\n{answer_text}"
        await send_formatted_answer(message, full_reply)

    except Exception as e:
        await refund_quota(user_id, quota_receipt)
        await wait_msg.edit_text(
            f"⚠️ <b>Не удалось обработать голосовое:</b>\n<code>{str(e)[:250]}</code>",
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
        disc = has_active_discount(user)
        await message.answer(
            "🔒 Срок подписки истек. Выбери бесплатную модель в /menu или продли тариф:",
            reply_markup=shop_kb(disc),
        )
        return

    quota_receipt = await try_consume_quota(user_id, pro_active, count=1)
    if not quota_receipt:
        disc = has_active_discount(user)
        await message.answer(
            "⏳ Бесплатный лимит на сегодня и пакет запросов исчерпаны.\n"
            "Приходи завтра, пригласи друга за +2 запроса (/top) или оформи подписку / пакет:",
            reply_markup=shop_kb(disc),
        )
        return

    wait_msg = await message.answer(f"📄 <i>Читаю файл {html.escape(fname)} и решаю...</i>", parse_mode=ParseMode.HTML)
    try:
        file_info = await bot.get_file(document.file_id)
        downloaded = await bot.download_file(file_info.file_path)
        file_text = decode_text_bytes(downloaded.read()).strip()

        if not file_text:
            raise RuntimeError("Файл пустой")

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

        await add_history(user_id, "user", f"[Файл {fname}]: {task_caption}\n{file_text[:1500]}")
        await add_history(user_id, "assistant", answer_text)

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
        disc_str = f"🔥 <b>Активна 50% (до {d_exp})</b>"
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
            "SELECT title, stars, paid_at FROM payments WHERE user_id = ? ORDER BY paid_at DESC LIMIT 10",
            (target_id,),
        ) as cur:
            pay_rows = await cur.fetchall()

        async with db.execute(
            "SELECT COALESCE(SUM(stars), 0) FROM payments WHERE user_id = ?",
            (target_id,),
        ) as cur:
            total_stars = (await cur.fetchone())[0]

    if pay_rows:
        pay_lines = []
        for p in pay_rows:
            p_date = datetime.fromtimestamp(p["paid_at"]).strftime("%d.%m.%y %H:%M")
            pay_lines.append(f"  • {html.escape(p['title'])} — <b>{p['stars']} ⭐</b> ({p_date})")
        payments_block = "\n".join(pay_lines)
    else:
        payments_block = "  <i>Покупок пока нет</i>"

    cur_model = ALL_MODELS_MAP.get(user["selected_model"], {}).get("name", user["selected_model"])
    ref_by = f"<code>{user['referred_by']}</code>" if user.get("referred_by") else "сам пришёл"

    text = (
        f"👤 <b>Карточка пользователя</b>\n\n"
        f"📛 Имя: <b>{html.escape(user.get('full_name') or 'Пользователь')}</b>{uname_str}\n"
        f"🆔 ID: <code>{target_id}</code>\n"
        f"📅 В боте с: <b>{joined_str}</b>\n"
        f"🔗 Пригласил: {ref_by} | Привёл друзей: <b>{refs_count}</b>\n\n"
        f"💎 Подписка: {sub_str}\n"
        f"🏷 Скидка 50%: {disc_str}\n"
        f"🤖 Модель: <b>{cur_model}</b>\n"
        f"⚡ Запросы сегодня: <b>{user['used_today']}/{total_daily}</b> (осталось {left_today})\n"
        f"📦 Запросы из пакета: <b>{user.get('extra_requests', 0)} шт.</b>\n"
        f"🎁 Бонус к дневному лимиту: <b>+{user['bonus_limit']} в день</b>\n"
        f"📊 Всего запросов за всё время: <b>{user.get('total_requests', 0)}</b>\n\n"
        f"💳 <b>История покупок (всего на {total_stars} ⭐):</b>\n"
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


# ================= ЛИДЕРБОРД НЕДЕЛИ =================
async def render_leaderboard_text(user_id: int) -> str:
    wk = current_week_key()
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute(
            """
            SELECT w.referrer_id, w.count, u.full_name
            FROM weekly_refs w
            LEFT JOIN users u ON u.user_id = w.referrer_id
            WHERE w.week_key = ? AND w.count > 0
            ORDER BY w.count DESC
            LIMIT 10
            """,
            (wk,),
        ) as cur:
            top_rows = await cur.fetchall()

        async with db.execute(
            "SELECT count FROM weekly_refs WHERE week_key = ? AND referrer_id = ?",
            (wk, user_id),
        ) as cur:
            my_row = await cur.fetchone()
            my_count = my_row["count"] if my_row else 0

    lines = [
        f"🏆 <b>Еженедельный лидерборд ({wk})</b>\n",
        "Приглашай друзей по своей ссылке — каждый подписавшийся на канал друг даёт <b>+1 балл</b> в рейтинг!\n",
        "🎁 <b>Награды в конце недели:</b>",
        "🥇 1 место — <b>Подписка на 30 дней</b>",
        "🥈 2 место — <b>Подписка на 15 дней</b>",
        "🥉 3 место — <b>Подписка на 7 дней</b>",
        "🎖 4–10 места — <b>Пакет +20 запросов</b>\n",
        "📊 <b>Текущий ТОП-10:</b>",
    ]

    if not top_rows:
        lines.append("<i>Пока никто не пригласил друзей на этой неделе. Стань первым!</i>")
    else:
        medals = {1: "🥇", 2: "🥈", 3: "🥉"}
        for idx, r in enumerate(top_rows, start=1):
            prefix = medals.get(idx, f"{idx}.")
            name = html.escape(r["full_name"] or f"ID {r['referrer_id']}")
            lines.append(f"{prefix} <b>{name}</b> — {r['count']} др.")

    lines.append(f"\n👤 Твой результат за неделю: <b>{my_count} др.</b>")
    return "\n".join(lines)


@router.message(Command("top"))
async def cmd_top(message: Message, bot: Bot):
    await get_user(message.from_user.id, full_name=message.from_user.full_name, username=message.from_user.username or "")
    if not await ensure_subscribed(bot, message.from_user.id, message):
        return
    kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="🔗 Моя реферальная ссылка", callback_data="ref_info")],
            [InlineKeyboardButton(text="⬅️ В меню", callback_data="back_cats")],
        ]
    )
    await message.answer(await render_leaderboard_text(message.from_user.id), reply_markup=kb, parse_mode=ParseMode.HTML)


@router.callback_query(F.data == "leaderboard")
async def cb_leaderboard(call: CallbackQuery, bot: Bot):
    if not await ensure_subscribed(bot, call.from_user.id, call.message):
        await call.answer()
        return
    kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="🔗 Моя реферальная ссылка", callback_data="ref_info")],
            [InlineKeyboardButton(text="⬅️ В меню", callback_data="back_cats")],
        ]
    )
    try:
        await call.message.edit_text(await render_leaderboard_text(call.from_user.id), reply_markup=kb, parse_mode=ParseMode.HTML)
    except TelegramBadRequest:
        pass
    await call.answer()


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
    if has_active_discount(user):
        d_exp = datetime.fromtimestamp(user["discount_until"]).strftime("%d.%m %H:%M")
        disc_line = f"\n🔥 Персональная скидка 50%: <b>Активна до {d_exp}</b>"

    return (
        f"👤 <b>Профиль — {html.escape(first_name)}</b>\n\n"
        f"🆔 Твой ID: <code>{user_id}</code>\n"
        f"{sub_block}\n"
        f"{req_block}\n"
        f"📦 Запросы из пакета: <b>{extra} шт.</b>\n"
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

    return (
        "🛠 <b>Админ-панель управления</b>\n\n"
        f"⚙️ Общий движок (текст): <code>{engine}</code>\n"
        f"📸 Движок разбора фото: <code>{VISION_MODEL}</code> (сжатие 1024px, 1 запр.)\n"
        f"👥 Всего пользователей: <b>{total_users}</b>\n"
        f"💎 Активных подписок: <b>{pro_users}</b>\n"
        f"⭐ Заработано за всё время: <b>{total_stars} ⭐</b>\n"
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


@router.callback_query(F.data == "adm_finish_week")
async def cb_adm_finish_week(call: CallbackQuery, bot: Bot):
    if call.from_user.id != ADMIN_ID:
        return
    wk = current_week_key()
    report = await distribute_weekly_rewards(bot, wk)
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("DELETE FROM weekly_refs WHERE week_key = ?", (wk,))
        await db.commit()
    await call.message.answer(report, parse_mode=ParseMode.HTML)
    await call.answer("🏆 Призы недели выданы!")


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
@router.message(CommandStart())
async def cmd_start(message: Message, bot: Bot):
    USER_INPUT_STATE.pop(message.from_user.id, None)
    args = message.text.split()
    ref_id = int(args[1]) if len(args) > 1 and args[1].isdigit() else 0
    user = await get_user(
        message.from_user.id,
        ref_id,
        full_name=message.from_user.full_name,
        username=message.from_user.username or "",
    )

    if not await ensure_subscribed(bot, message.from_user.id, message):
        return

    cur_model_name = ALL_MODELS_MAP.get(user["selected_model"], {}).get("name", user["selected_model"])
    text = (
        f"👋 <b>Привет, {html.escape(message.from_user.first_name)}!</b>\n\n"
        f"Я — твой универсальный ИИ-помощник. Вот что я умею:\n"
        f"💬 Отвечать на любые вопросы и писать код\n"
        f"📸 Решать задачи и разбирать конспекты по фото\n"
        f"🎬 Анализировать видеоролики, голосовые и файлы\n\n"
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
    disc = has_active_discount(user)
    await message.answer(render_shop_text(user), reply_markup=shop_kb(disc), parse_mode=ParseMode.HTML)


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


@router.callback_query(F.data == "ref_info")
async def cb_ref_info(call: CallbackQuery, bot: Bot):
    try:
        if not await ensure_subscribed(bot, call.from_user.id, call.message):
            await call.answer()
            return
        me = await bot.get_me()
        bot_username = me.username or "AetherNeural_bot"
        base_tg = "https" + "://" + "t.me"
        ref_link = f"{base_tg}/{bot_username}?start={call.from_user.id}"
        share_text = quote("Бесплатный ИИ-бот без VPN: GPT-6, Claude 5 и Gemini!")
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

        buttons.append([InlineKeyboardButton(text="⬅️ В меню", callback_data="back_cats")])
        kb = InlineKeyboardMarkup(inline_keyboard=buttons)

        await call.message.answer(
            f"👥 <b>Бонус за друзей + Лидерборд недели</b>\n\n"
            f"За каждого друга, который перейдет по твоей ссылке и <b>подпишется на канал</b>:\n"
            f"• Твой дневной лимит вырастет на <b>+2 запроса</b>\n"
            f"• Ты получишь <b>+1 балл</b> в еженедельный топ (/top) с розыгрышем подписок на 30, 15 и 7 дней!\n\n"
            f"🔗 Твоя ссылка:\n<code>{ref_link}</code>",
            reply_markup=kb,
            parse_mode=ParseMode.HTML,
            disable_web_page_preview=True,
        )
        await call.answer()
    except Exception as e:
        await call.answer(f"Ошибка: {str(e)[:150]}", show_alert=True)


@router.callback_query(F.data == "shop")
async def cb_shop(call: CallbackQuery, bot: Bot):
    if not await ensure_subscribed(bot, call.from_user.id, call.message):
        await call.answer()
        return
    user = await get_user(call.from_user.id, full_name=call.from_user.full_name, username=call.from_user.username or "")
    disc = has_active_discount(user)
    try:
        await call.message.edit_text(render_shop_text(user), reply_markup=shop_kb(disc), parse_mode=ParseMode.HTML)
    except TelegramBadRequest:
        pass
    await call.answer()


# ================= ОПЛАТА TELEGRAM STARS (ПОДПИСКИ И ПАКЕТЫ) =================
@router.callback_query(F.data.startswith("buy:"))
async def cb_buy(call: CallbackQuery):
    prod_key = call.data.split(":", 1)[1]
    product = PRODUCTS.get(prod_key)
    if not product:
        await call.answer("Товар не найден", show_alert=True)
        return

    user = await get_user(call.from_user.id)
    disc = has_active_discount(user)
    final_price = get_product_price(product, disc)

    if product["type"] == "sub":
        desc = f"Безлимитный доступ ко всем PRO-моделям на {product['value']} дн."
    else:
        desc = f"Пакет на {product['value']} дополнительных запросов."

    await call.message.answer_invoice(
        title=product["title"] + (" (Скидка 50%)" if disc else ""),
        description=desc,
        payload=f"prod:{prod_key}",
        currency="XTR",
        prices=[LabeledPrice(label=product["title"], amount=final_price)],
    )
    await call.answer()


@router.pre_checkout_query()
async def pre_checkout(query: PreCheckoutQuery):
    await query.answer(ok=True)


@router.message(F.successful_payment)
async def successful_payment(message: Message):
    payload = message.successful_payment.invoice_payload
    prod_key = payload.split(":", 1)[1]
    product = PRODUCTS[prod_key]
    paid_stars = message.successful_payment.total_amount
    user = await get_user(message.from_user.id)

    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "INSERT INTO payments (user_id, product_key, title, stars, paid_at) VALUES (?, ?, ?, ?, ?)",
            (message.from_user.id, prod_key, product["title"], paid_stars, time.time()),
        )

        if product["type"] == "sub":
            days = product["value"]
            base_time = max(time.time(), user["pro_until"])
            new_pro_until = base_time + days * 86400
            exp_date = datetime.fromtimestamp(new_pro_until).strftime("%d.%m.%Y %H:%M")

            await db.execute("UPDATE users SET pro_until = ? WHERE user_id = ?", (new_pro_until, message.from_user.id))
            await db.commit()

            await message.answer(
                f"🎉 <b>Оплата прошла успешно!</b>\n"
                f"Тариф <b>«{product['title']}»</b> активен до <b>{exp_date}</b>.\n"
                f"Все модели разблокированы в /menu.",
                parse_mode=ParseMode.HTML,
            )
        else:
            packs = product["value"]
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


# ================= ГЕНЕРАЦИЯ (ТЕКСТ И ЭКОНОМНЫЙ РАЗБОР ФОТО) =================
async def get_candidates_for_user(user_id: int, selected_model: str) -> list[str]:
    if user_id == ADMIN_ID and selected_model:
        return [selected_model] + [m for m in FALLBACK_MODELS if m != selected_model]
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


async def generate_photos_response(caption: str, b64_images: list[str]) -> str:
    seen = set()
    candidates = []
    for m in VISION_FALLBACK_MODELS:
        if m and m not in seen:
            seen.add(m)
            candidates.append(m)

    user_content: list[dict] = [{"type": "text", "text": caption}]
    for b64_img in b64_images:
        user_content.append(
            {
                "type": "image_url",
                "image_url": {
                    "url": f"data:image/jpeg;base64,{b64_img}",
                    "detail": "auto",
                },
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
                max_tokens=1200,
            )
            content = response.choices[0].message.content
            if content:
                return content
        except Exception as e:
            last_error = e
            continue

    raise last_error or RuntimeError("Модели распознавания фото временно недоступны")


# ================= ОБРАБОТКА ОДИНОЧНЫХ ФОТО И АЛЬБОМОВ (1 ФОТО = 1 ЗАПРОС, СЖАТИЕ ДО 1024px) =================
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
        disc = has_active_discount(user)
        total_limit = FREE_DAILY_LIMIT + (user.get("bonus_limit") or 0)
        daily_left = max(0, total_limit - (user.get("used_today") or 0))
        extra_left = user.get("extra_requests") or 0
        avail = daily_left + extra_left
        await first_msg.answer(
            f"⏳ <b>Недостаточно запросов для обработки {count} фото</b> (1 фото = 1 запрос).\n"
            f"Сейчас доступно: <b>{avail} запр.</b>\n\n"
            "Пригласи друга (/top) или оформи подписку / пакет:",
            reply_markup=shop_kb(disc),
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
        loop = asyncio.get_running_loop()
        b64_list: list[str] = []
        caption = ""
        for msg in messages:
            if msg.caption and not caption:
                caption = msg.caption
            photo = msg.photo[-2] if len(msg.photo) >= 2 and msg.photo[-2].width >= 750 else msg.photo[-1]
            file_info = await bot.get_file(photo.file_id)
            downloaded = await bot.download_file(file_info.file_path)
            raw_bytes = downloaded.read()
            compressed_b64 = await loop.run_in_executor(None, compress_image_bytes, raw_bytes, 1024, 75)
            b64_list.append(compressed_b64)

        if not caption:
            if count > 1:
                caption = f"Подробно разбери и реши все задания с этих {count} фотографий по порядку, объединив ответ в один структурированный текст."
            else:
                caption = "Подробно разбери и реши то, что изображено на фото."

        answer_text = await generate_photos_response(
            caption=caption,
            b64_images=b64_list,
        )

        await add_history(user_id, "user", f"[Отправил {count} фото с подписью: {caption}]")
        await add_history(user_id, "assistant", answer_text)

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
            await asyncio.sleep(1.3)
            batch = MEDIA_GROUP_BUFFER.pop(mg_id, [])
            if batch:
                batch.sort(key=lambda m: m.message_id)
                await process_photo_batch(batch, bot)
    else:
        await process_photo_batch([message], bot)


# ================= ОБРАБОТКА ТЕКСТА, ПРОМОКОДОВ И АДМИН-ВВОДА =================
@router.message(F.text)
async def handle_prompt(message: Message, bot: Bot):
    user_id = message.from_user.id
    text_in = message.text.strip()

    if USER_INPUT_STATE.get(user_id) == "promo_activate":
        USER_INPUT_STATE.pop(user_id, None)
        if not await ensure_subscribed(bot, user_id, message):
            return
        ok, reply_text = await redeem_promocode(user_id, text_in)
        await message.answer(reply_text, reply_markup=profile_kb(), parse_mode=ParseMode.HTML)
        return

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

    model_id = user["selected_model"]
    pro_active = is_pro(user) or (user_id == ADMIN_ID)

    if ALL_MODELS_MAP.get(model_id, {}).get("pro") and not pro_active:
        disc = has_active_discount(user)
        await message.answer(
            "🔒 Срок подписки истек. Выбери бесплатную модель в /menu или продли тариф:",
            reply_markup=shop_kb(disc),
        )
        return

    quota_receipt = await try_consume_quota(user_id, pro_active, count=1)
    if not quota_receipt:
        disc = has_active_discount(user)
        await message.answer(
            "⏳ Бесплатный лимит на сегодня и пакет запросов исчерпаны.\n"
            "Приходи завтра, пригласи друга за +2 запроса (/top) или оформи подписку / пакет:",
            reply_markup=shop_kb(disc),
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

        await add_history(user_id, "user", message.text)
        await add_history(user_id, "assistant", answer_text)

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
        BotCommand(command="top", description="Еженедельный лидерборд и призы"),
        BotCommand(command="clear", description="Очистить память диалога"),
    ]
    await bot.set_my_commands(commands)


async def main():
    await init_db()
    bot = Bot(token=BOT_TOKEN)
    await setup_bot_commands(bot)
    asyncio.create_task(weekly_leaderboard_watcher(bot))
    asyncio.create_task(delayed_discount_watcher(bot))
    dp = Dispatcher()
    dp.include_router(router)
    print("Бот запущен!")
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
