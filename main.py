import asyncio
import base64
import os
import random
import string
import time
from datetime import date, datetime
import aiosqlite
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
)
from aiogram.enums import ParseMode
from aiogram.exceptions import TelegramBadRequest
from openai import AsyncOpenAI

# ================= НАСТРОЙКИ ДЛЯ ХОСТИНГА (ENV) =================
BOT_TOKEN = os.getenv("BOT_TOKEN", "").strip()
UNLOCK_API_KEY = os.getenv("UNLOCK_API_KEY", "").strip()
UNLOCK_BASE_URL = os.getenv("UNLOCK_BASE_URL", "https://unlockapi.space/v1").strip()

if not BOT_TOKEN:
    raise RuntimeError("Не задана переменная окружения BOT_TOKEN! Добавь её в настройках хостинга.")
if not UNLOCK_API_KEY:
    raise RuntimeError("Не задана переменная окружения UNLOCK_API_KEY! Добавь её в настройках хостинга.")

ADMIN_ID = int(os.getenv("ADMIN_ID", "1991878700"))

CHANNEL_USERNAME = os.getenv("CHANNEL_USERNAME", "@AetherNeural")
CHANNEL_URL = os.getenv("CHANNEL_URL", "https://t.me/AetherNeural")

# Путь к базе (на некоторых хостингах для сохранения при редеплое используют папку /data или текущую)
DB_PATH = os.getenv("DB_PATH", "users.db")

FREE_DAILY_LIMIT = 5
MAX_HISTORY_MESSAGES = 16
DEFAULT_ENGINE_MODEL = "gpt-6-luna"

FALLBACK_MODELS = [
    "gpt-6-luna",
    "gpt-5.6-luna",
    "gpt-5-mini",
    "gemini-3.5-flash-lite",
    "gemini-3.1-flash-lite",
    "deepseek-v4-flash",
    "claude-haiku-5-5",
]

EMOJI_IDS = {
    "gemini": "5321197740800120767",
    "gpt": "5310259124817134249",
    "claude": "5321196473784773037",
    "grok": "5319288443153445517",
    "deepseek": "5456541677944612102",
}

CATEGORIES = {
    "gpt": {
        "title": "GPT (OpenAI)",
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
        "title": "Claude (Anthropic)",
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
        "title": "Gemini (Google)",
        "models": [
            {"id": "gemini-3.1-flash-lite", "name": "Gemini 3.1 Flash Lite", "pro": False, "tag": "FREE"},
            {"id": "gemini-3.5-flash-lite", "name": "Gemini 3.5 Flash Lite", "pro": False, "tag": "FREE"},
            {"id": "gemini-3.7-flash", "name": "Gemini 3.7 Flash", "pro": True, "tag": "PRO"},
            {"id": "gemini-3.8-flash", "name": "Gemini 3.8 Flash", "pro": True, "tag": "PRO"},
            {"id": "gemini-3.1-pro", "name": "Gemini 3.1 Pro", "pro": True, "tag": "PRO"},
        ],
    },
    "deepseek": {
        "title": "DeepSeek",
        "models": [
            {"id": "deepseek-v4-flash", "name": "DeepSeek V4 Flash", "pro": False, "tag": "FREE"},
            {"id": "deepseek-v4-pro", "name": "DeepSeek V4 Pro", "pro": True, "tag": "PRO"},
        ],
    },
    "grok": {
        "title": "Grok (xAI)",
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

ai_client = AsyncOpenAI(
    api_key=UNLOCK_API_KEY,
    base_url=UNLOCK_BASE_URL,
    timeout=35.0,
    max_retries=0,
)
router = Router()

USER_INPUT_STATE: dict[int, str] = {}
PROMO_DRAFT: dict[str, any] = {}
ACTIVE_GENERATIONS: set[int] = set()


# ================= ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ НЕДЕЛИ И ЦЕН =================
def current_week_key() -> str:
    iso = date.today().isocalendar()
    return f"{iso.year}-W{iso.week:02d}"


def has_active_discount(user: dict) -> bool:
    return user.get("discount_until", 0) > time.time()


def get_product_price(product: dict, discount_active: bool) -> int:
    base = product["stars"]
    if discount_active:
        return max(1, round(base * 0.5))
    return base


# ================= БАЗА ДАННЫХ =================
async def init_db():
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("""
            CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY,
                full_name TEXT DEFAULT 'Пользователь',
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
                discount_offered INTEGER DEFAULT 0
            )
        """)

        new_cols = [
            ("full_name", "TEXT DEFAULT 'Пользователь'"),
            ("extra_requests", "INTEGER DEFAULT 0"),
            ("ref_rewarded", "INTEGER DEFAULT 0"),
            ("total_requests", "INTEGER DEFAULT 0"),
            ("visited_models", "INTEGER DEFAULT 0"),
            ("discount_until", "REAL DEFAULT 0"),
            ("discount_offered", "INTEGER DEFAULT 0"),
        ]
        for col_name, col_def in new_cols:
            try:
                await db.execute(f"ALTER TABLE users ADD COLUMN {col_name} {col_def}")
            except Exception:
                pass

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


async def get_user(user_id: int, ref_id: int = 0, full_name: str = "") -> dict:
    today_str = str(date.today())
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute("SELECT * FROM users WHERE user_id = ?", (user_id,)) as cur:
            row = await cur.fetchone()

        if not row:
            valid_ref = ref_id if (ref_id and ref_id != user_id) else 0
            clean_name = (full_name or "Пользователь")[:40]
            await db.execute(
                """
                INSERT INTO users (user_id, full_name, last_reset, referred_by, ref_rewarded)
                VALUES (?, ?, ?, ?, 0)
                """,
                (user_id, clean_name, today_str, valid_ref),
            )
            await db.commit()
            return await get_user(user_id)

        user = dict(row)
        updates = []
        params = []
        if user["last_reset"] != today_str:
            updates.append("used_today = 0, last_reset = ?")
            params.append(today_str)
            user["used_today"] = 0
            user["last_reset"] = today_str
        if full_name and user.get("full_name") != full_name[:40]:
            updates.append("full_name = ?")
            params.append(full_name[:40])
            user["full_name"] = full_name[:40]

        if updates:
            params.append(user_id)
            await db.execute(f"UPDATE users SET {', '.join(updates)} WHERE user_id = ?", tuple(params))
            await db.commit()

        return user


async def try_consume_quota(user_id: int, pro_active: bool) -> str | None:
    if pro_active:
        return "pro"
    async with aiosqlite.connect(DB_PATH) as db:
        cur = await db.execute(
            """
            UPDATE users
            SET used_today = used_today + 1
            WHERE user_id = ? AND used_today < (? + bonus_limit)
            """,
            (user_id, FREE_DAILY_LIMIT),
        )
        if cur.rowcount > 0:
            await db.commit()
            return "daily"

        cur2 = await db.execute(
            """
            UPDATE users
            SET extra_requests = extra_requests - 1
            WHERE user_id = ? AND extra_requests > 0
            """,
            (user_id,),
        )
        if cur2.rowcount > 0:
            await db.commit()
            return "extra"

        return None


async def refund_quota(user_id: int, source: str | None):
    if not source or source == "pro":
        return
    async with aiosqlite.connect(DB_PATH) as db:
        if source == "daily":
            await db.execute("UPDATE users SET used_today = MAX(0, used_today - 1) WHERE user_id = ?", (user_id,))
        elif source == "extra":
            await db.execute("UPDATE users SET extra_requests = extra_requests + 1 WHERE user_id = ?", (user_id,))
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
                    "• Начислено <b>+2 запроса в день</b> навсегда\n"
                    "• Засчитан <b>+1 балл</b> в еженедельный лидерборд (/top)!",
                    parse_mode=ParseMode.HTML,
                )
            except Exception:
                pass


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
            name = w["full_name"] or str(uid)

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
                prize_text = "⚡ +20 запросов навсегда"

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


# ================= ТРИГГЕРНАЯ СКИДКА 50% НА 24 ЧАСА =================
async def check_and_send_discount_offer(user_id: int, message: Message):
    user = await get_user(user_id)
    if is_pro(user) or user.get("discount_offered", 0) == 1:
        return

    if user.get("visited_models", 0) >= 1 and user.get("total_requests", 0) >= 2:
        disc_until = time.time() + 86400
        async with aiosqlite.connect(DB_PATH) as db:
            await db.execute(
                "UPDATE users SET discount_until = ?, discount_offered = 1 WHERE user_id = ?",
                (disc_until, user_id),
            )
            await db.commit()

        user["discount_until"] = disc_until
        offer_text = (
            "🔥 <b>ПЕРСОНАЛЬНАЯ СКИДКА 50% НА 24 ЧАСА!</b>\n\n"
            "Мы видим, что тебе зашёл наш ИИ-бот! Специально для тебя мы открыли закрытую распродажу на все тарифы и пакеты запросов ровно на <b>24 часа</b>:\n\n"
            "👑 <b>Подписки (безлимит на все PRO-модели):</b>\n"
            f"• Пробный 1 день: <s>59 ⭐</s> → <b>{get_product_price(PRODUCTS['sub_trial'], True)} ⭐</b>\n"
            f"• Стандарт 7 дней: <s>149 ⭐</s> → <b>{get_product_price(PRODUCTS['sub_standard'], True)} ⭐</b>\n"
            f"• Премиум 30 дней: <s>349 ⭐</s> → <b>{get_product_price(PRODUCTS['sub_premium'], True)} ⭐</b>\n\n"
            "⚡ <b>Пакеты запросов (не сгорают никогда):</b>\n"
            f"• +30 запросов: <s>79 ⭐</s> → <b>{get_product_price(PRODUCTS['pack_30'], True)} ⭐</b>\n"
            f"• +100 запросов: <s>199 ⭐</s> → <b>{get_product_price(PRODUCTS['pack_100'], True)} ⭐</b>\n"
            f"• +300 запросов: <s>449 ⭐</s> → <b>{get_product_price(PRODUCTS['pack_300'], True)} ⭐</b>\n\n"
            "👇 Жми на любой тариф прямо сейчас, пока действует таймер:"
        )
        await message.answer(offer_text, reply_markup=shop_kb(discount_active=True), parse_mode=ParseMode.HTML)


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
            InlineKeyboardButton(text="GPT", callback_data="cat:gpt", icon_custom_emoji_id=EMOJI_IDS["gpt"]),
            InlineKeyboardButton(text="Claude", callback_data="cat:claude", icon_custom_emoji_id=EMOJI_IDS["claude"]),
        ],
        [
            InlineKeyboardButton(text="Gemini", callback_data="cat:gemini", icon_custom_emoji_id=EMOJI_IDS["gemini"]),
            InlineKeyboardButton(text="DeepSeek", callback_data="cat:deepseek", icon_custom_emoji_id=EMOJI_IDS["deepseek"]),
        ],
        [
            InlineKeyboardButton(text="Grok", callback_data="cat:grok", icon_custom_emoji_id=EMOJI_IDS["grok"]),
            InlineKeyboardButton(text="⭐ Подписка / Пакеты", callback_data="shop"),
        ],
        [
            InlineKeyboardButton(text="👤 Профиль", callback_data="profile"),
            InlineKeyboardButton(text="🏆 Топ недели", callback_data="leaderboard"),
        ],
        [
            InlineKeyboardButton(text="👥 +2 за друга", callback_data="ref_info"),
            InlineKeyboardButton(text="🧹 Сброс чата", callback_data="clear_chat"),
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

    lines.append("\n⚡ <b>Пакеты запросов навсегда (не сгорают):</b>")
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
            [InlineKeyboardButton(text="⬅️ Назад в меню", callback_data="back_cats")],
        ]
    )


async def admin_kb() -> InlineKeyboardMarkup:
    engine = await get_engine_model()
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="🎟 Создать промокод", callback_data="adm_promo_create")],
            [InlineKeyboardButton(text="📋 Список промокодов", callback_data="adm_promo_list")],
            [InlineKeyboardButton(text=f"⚙️ Движок API: {engine}", callback_data="adm_set_engine")],
            [InlineKeyboardButton(text="🏆 Завершить неделю и выдать призы", callback_data="adm_finish_week")],
            [InlineKeyboardButton(text="👑 Выдать Премиум себе (30 дн.)", callback_data="adm_self_pro")],
            [InlineKeyboardButton(text="🎁 Выдать подписку по ID", callback_data="adm_give_pro")],
            [InlineKeyboardButton(text="❌ Забрать подписку по ID", callback_data="adm_remove_pro")],
            [InlineKeyboardButton(text="➕ Добавить лимит запросов по ID", callback_data="adm_give_limit")],
            [InlineKeyboardButton(text="🔌 Проверить живые модели API", callback_data="adm_check_api")],
            [InlineKeyboardButton(text="⬅️ В главное меню", callback_data="back_cats")],
        ]
    )


def admin_cancel_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[[InlineKeyboardButton(text="❌ Отмена", callback_data="admin_panel")]]
    )


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
        "🎖 4–10 места — <b>+20 запросов навсегда</b>\n",
        "📊 <b>Текущий ТОП-10:</b>",
    ]

    if not top_rows:
        lines.append("<i>Пока никто не пригласил друзей на этой неделе. Стань первым!</i>")
    else:
        medals = {1: "🥇", 2: "🥈", 3: "🥉"}
        for idx, r in enumerate(top_rows, start=1):
            prefix = medals.get(idx, f"{idx}.")
            name = r["full_name"] or f"ID {r['referrer_id']}"
            lines.append(f"{prefix} <b>{name}</b> — {r['count']} др.")

    lines.append(f"\n👤 Твой результат за неделю: <b>{my_count} др.</b>")
    return "\n".join(lines)


@router.message(Command("top"))
async def cmd_top(message: Message, bot: Bot):
    await get_user(message.from_user.id, full_name=message.from_user.full_name)
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
    user = await get_user(call.from_user.id, full_name=call.from_user.full_name)
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
        f"👤 <b>Профиль — {first_name}</b>\n\n"
        f"🆔 Твой ID: <code>{user_id}</code>\n"
        f"{sub_block}\n"
        f"{req_block}\n"
        f"📦 Запросы из пакетов (навсегда): <b>{extra} шт.</b>\n"
        f"🤖 Выбранная модель: <b>{cur_model_name}</b>"
        f"{disc_line}"
    )


@router.message(Command("profile"))
async def cmd_profile(message: Message, bot: Bot):
    USER_INPUT_STATE.pop(message.from_user.id, None)
    await get_user(message.from_user.id, full_name=message.from_user.full_name)
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
            return True, f"🎉 Промокод <code>{code}</code> активирован! Начислено <b>+{bonus} запросов навсегда</b>."


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

    return (
        "🛠 <b>Админ-панель управления</b>\n\n"
        f"⚙️ Активный движок: <code>{engine}</code>\n"
        f"👥 Всего пользователей: <b>{total_users}</b>\n"
        f"👑 Активных подписок: <b>{pro_users}</b>\n"
        f"🎟 Создано промокодов: <b>{promos_count}</b>\n"
        f"⚡ Запросов сегодня: <b>{today_reqs}</b>\n\n"
        "<i>Команды:\n"
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
                [InlineKeyboardButton(text="⚡ Запросы навсегда (пакет)", callback_data="promo_type:req")],
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
            "⚡ <b>Промокод на запросы — Шаг 2/4</b>\n\n"
            "Введи числом, сколько <b>несгораемых запросов</b> добавит промокод (например: <code>20</code> или <code>50</code>):",
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
        else f"+{amount} запросов навсегда"
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
        "⚙️ <b>Смена рабочего движка API</b>\n\n"
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


@router.callback_query(F.data == "adm_give_pro")
async def cb_adm_give_pro(call: CallbackQuery):
    if call.from_user.id != ADMIN_ID:
        return
    USER_INPUT_STATE[ADMIN_ID] = "give_pro"
    await call.message.edit_text(
        "🎁 <b>Выдача подписки</b>\n\nОтправь <b>ID пользователя</b> и <b>количество дней</b> через пробел.\nПример: <code>123456789 7</code>",
        reply_markup=admin_cancel_kb(),
        parse_mode=ParseMode.HTML,
    )


@router.callback_query(F.data == "adm_remove_pro")
async def cb_adm_remove_pro(call: CallbackQuery):
    if call.from_user.id != ADMIN_ID:
        return
    USER_INPUT_STATE[ADMIN_ID] = "remove_pro"
    await call.message.edit_text(
        "❌ <b>Снятие подписки</b>\n\nОтправь <b>ID пользователя</b>:\nПример: <code>123456789</code>",
        reply_markup=admin_cancel_kb(),
        parse_mode=ParseMode.HTML,
    )


@router.callback_query(F.data == "adm_give_limit")
async def cb_adm_give_limit(call: CallbackQuery):
    if call.from_user.id != ADMIN_ID:
        return
    USER_INPUT_STATE[ADMIN_ID] = "give_limit"
    await call.message.edit_text(
        "➕ <b>Добавление запросов навсегда</b>\n\nОтправь <b>ID пользователя</b> и <b>количество запросов</b> через пробел:\nПример: <code>123456789 20</code>",
        reply_markup=admin_cancel_kb(),
        parse_mode=ParseMode.HTML,
    )


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
async def cmd_delpro(message: Message):
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


# ================= ХЭНДЛЕРЫ НАВИГАЦИИ =================
@router.message(CommandStart())
async def cmd_start(message: Message, bot: Bot):
    USER_INPUT_STATE.pop(message.from_user.id, None)
    args = message.text.split()
    ref_id = int(args[1]) if len(args) > 1 and args[1].isdigit() else 0
    user = await get_user(message.from_user.id, ref_id, full_name=message.from_user.full_name)

    if not await ensure_subscribed(bot, message.from_user.id, message):
        return

    cur_model_name = ALL_MODELS_MAP.get(user["selected_model"], {}).get("name", user["selected_model"])
    text = (
        f"👋 <b>Привет, {message.from_user.first_name}!</b>\n\n"
        f"Выбери раздел ниже, чтобы переключить нейросеть, или просто отправь текст / фото задачи.\n\n"
        f"📊 Статус: <b>{format_status(user)}</b>\n"
        f"🤖 Активная модель: <b>{cur_model_name}</b>\n"
        f"🧠 Память диалога: <b>Включена (/clear — очистить)</b>"
    )
    await message.answer(text, reply_markup=categories_kb(message.from_user.id), parse_mode=ParseMode.HTML)


@router.message(Command("menu"))
async def cmd_menu(message: Message, bot: Bot):
    USER_INPUT_STATE.pop(message.from_user.id, None)
    user = await get_user(message.from_user.id, full_name=message.from_user.full_name)
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
    user = await get_user(message.from_user.id, full_name=message.from_user.full_name)
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
    user = await get_user(call.from_user.id, full_name=call.from_user.full_name)
    cat = CATEGORIES[cat_key]
    pro_active = is_pro(user)

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
    user = await get_user(call.from_user.id, full_name=call.from_user.full_name)
    model_info = ALL_MODELS_MAP.get(model_id)
    pro_active = is_pro(user)

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
    user = await get_user(call.from_user.id, full_name=call.from_user.full_name)
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
    if not await ensure_subscribed(bot, call.from_user.id, call.message):
        await call.answer()
        return
    me = await bot.get_me()
    ref_link = f"https://t.me/{me.username}?start={call.from_user.id}"
    await call.message.answer(
        f"👥 <b>Бонус за друзей + Лидерборд недели</b>\n\n"
        f"За каждого друга, который перейдет по твоей ссылке и <b>подпишется на канал</b>:\n"
        f"• Твой дневной лимит вырастет на <b>+2 запроса</b> навсегда\n"
        f"• Ты получишь <b>+1 балл</b> в еженедельный топ (/top) с розыгрышем подписок на 30, 15 и 7 дней!\n\n"
        f"🔗 Твоя ссылка:\n<code>{ref_link}</code>",
        parse_mode=ParseMode.HTML,
    )
    await call.answer()


@router.callback_query(F.data == "shop")
async def cb_shop(call: CallbackQuery, bot: Bot):
    if not await ensure_subscribed(bot, call.from_user.id, call.message):
        await call.answer()
        return
    user = await get_user(call.from_user.id, full_name=call.from_user.full_name)
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
        desc = f"Пакет на {product['value']} дополнительных запросов (не сгорают со временем)."

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
    user = await get_user(message.from_user.id)

    if product["type"] == "sub":
        days = product["value"]
        base_time = max(time.time(), user["pro_until"])
        new_pro_until = base_time + days * 86400
        exp_date = datetime.fromtimestamp(new_pro_until).strftime("%d.%m.%Y %H:%M")

        async with aiosqlite.connect(DB_PATH) as db:
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
        async with aiosqlite.connect(DB_PATH) as db:
            await db.execute(
                "UPDATE users SET extra_requests = extra_requests + ? WHERE user_id = ?",
                (packs, message.from_user.id),
            )
            await db.commit()

        await message.answer(
            f"🎉 <b>Оплата прошла успешно!</b>\n"
            f"На твой баланс зачислено <b>+{packs} запросов навсегда</b>.\n"
            f"Проверить остаток можно в /profile.",
            parse_mode=ParseMode.HTML,
        )


# ================= ЕДИНАЯ ГЕНЕРАЦИЯ (ТЕКСТ И ФОТО ЧЕРЕЗ ENGINE_MODEL) =================
async def generate_text_with_engine(history: list[dict], user_text: str) -> str:
    engine = await get_engine_model()
    candidates = [engine] + [m for m in FALLBACK_MODELS if m != engine]

    messages_payload = [
        {"role": "system", "content": "Отвечай четко, по делу и на языке пользователя. Учитывай контекст предыдущих сообщений диалога."},
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


async def generate_photo_with_engine(caption: str, b64_img: str) -> str:
    engine = await get_engine_model()
    candidates = [engine] + [m for m in FALLBACK_MODELS if m != engine]

    messages_payload = [
        {
            "role": "user",
            "content": [
                {"type": "text", "text": caption},
                {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{b64_img}"}},
            ],
        }
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

    raise last_error or RuntimeError("Модели распознавания фото временно недоступны")


# ================= ОБРАБОТКА ФОТОГРАФИЙ =================
@router.message(F.photo)
async def handle_photo(message: Message, bot: Bot):
    user_id = message.from_user.id
    user = await get_user(user_id, full_name=message.from_user.full_name)
    if not await ensure_subscribed(bot, user_id, message):
        return

    if user_id in ACTIVE_GENERATIONS:
        await message.answer("⏳ Дождись ответа на предыдущий запрос перед отправкой нового.")
        return

    pro_active = is_pro(user)
    quota_source = await try_consume_quota(user_id, pro_active)
    if not quota_source:
        disc = has_active_discount(user)
        await message.answer(
            "⏳ Бесплатный лимит на сегодня и пакетные запросы исчерпаны.\n"
            "Оформи подписку или возьми пакет запросов навсегда:",
            reply_markup=shop_kb(disc),
        )
        return

    ACTIVE_GENERATIONS.add(user_id)
    shown_model = ALL_MODELS_MAP.get(user["selected_model"], {}).get("name", user["selected_model"])
    wait_msg = await message.answer(f"📸 <i>Анализирую изображение ({shown_model})...</i>", parse_mode=ParseMode.HTML)

    try:
        photo = message.photo[-1]
        file_info = await bot.get_file(photo.file_id)
        downloaded = await bot.download_file(file_info.file_path)
        b64_img = base64.b64encode(downloaded.read()).decode("utf-8")

        caption = message.caption or "Подробно разбери и реши то, что изображено на фото."
        answer_text = await generate_photo_with_engine(caption=caption, b64_img=b64_img)

        await add_history(user_id, "user", f"[Отправил фото с подписью: {caption}]")
        await add_history(user_id, "assistant", answer_text)

        async with aiosqlite.connect(DB_PATH) as db:
            await db.execute("UPDATE users SET total_requests = total_requests + 1 WHERE user_id = ?", (user_id,))
            await db.commit()

        await wait_msg.delete()
        for i in range(0, len(answer_text), 4000):
            await message.answer(answer_text[i : i + 4000])

        await check_and_send_discount_offer(user_id, message)

    except Exception as e:
        await refund_quota(user_id, quota_source)
        await wait_msg.edit_text(
            f"⚠️ <b>Не удалось распознать фото:</b>\n<code>{str(e)[:250]}</code>",
            parse_mode=ParseMode.HTML,
        )
    finally:
        ACTIVE_GENERATIONS.discard(user_id)


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
        parts = text_in.split()

        if action == "promo_custom_val":
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
                f"✅ Рабочий движок изменен на <code>{text_in}</code> (для текста и фото).",
                reply_markup=await admin_kb(),
                parse_mode=ParseMode.HTML,
            )
            return

        elif action == "give_pro":
            if len(parts) < 2 or not parts[0].isdigit() or not parts[1].isdigit():
                await message.answer("⚠️ Неверный формат. Нужно: <code>ID ДНИ</code>", reply_markup=await admin_kb(), parse_mode=ParseMode.HTML)
                return
            target_id, days = int(parts[0]), int(parts[1])
            target = await get_user(target_id)
            new_until = max(time.time(), target["pro_until"]) + days * 86400
            async with aiosqlite.connect(DB_PATH) as db:
                await db.execute("UPDATE users SET pro_until = ? WHERE user_id = ?", (new_until, target_id))
                await db.commit()
            exp_date = datetime.fromtimestamp(new_until).strftime("%d.%m.%Y %H:%M")
            await message.answer(
                f"✅ Пользователю <code>{target_id}</code> выдана подписка на <b>{days} дн.</b> (до {exp_date})",
                reply_markup=await admin_kb(),
                parse_mode=ParseMode.HTML,
            )
            try:
                await bot.send_message(target_id, f"🎁 Тебе выдана <b>подписка на {days} дн.!</b> Открой /menu.", parse_mode=ParseMode.HTML)
            except Exception:
                pass
            return

        elif action == "remove_pro":
            if not parts[0].isdigit():
                await message.answer("⚠️ Нужно указать числовой ID.", reply_markup=await admin_kb())
                return
            target_id = int(parts[0])
            async with aiosqlite.connect(DB_PATH) as db:
                await db.execute("UPDATE users SET pro_until = 0 WHERE user_id = ?", (target_id,))
                await db.commit()
            await message.answer(
                f"❌ У пользователя <code>{target_id}</code> снята подписка.",
                reply_markup=await admin_kb(),
                parse_mode=ParseMode.HTML,
            )
            return

        elif action == "give_limit":
            if len(parts) < 2 or not parts[0].isdigit() or not parts[1].isdigit():
                await message.answer("⚠️ Неверный формат. Нужно: <code>ID ЗАПРОСЫ</code>", reply_markup=await admin_kb(), parse_mode=ParseMode.HTML)
                return
            target_id, bonus = int(parts[0]), int(parts[1])
            await get_user(target_id)
            async with aiosqlite.connect(DB_PATH) as db:
                await db.execute("UPDATE users SET extra_requests = extra_requests + ? WHERE user_id = ?", (bonus, target_id))
                await db.commit()
            await message.answer(
                f"✅ Пользователю <code>{target_id}</code> добавлено <b>+{bonus}</b> запросов навсегда.",
                reply_markup=await admin_kb(),
                parse_mode=ParseMode.HTML,
            )
            return

    user = await get_user(user_id, full_name=message.from_user.full_name)

    if not await ensure_subscribed(bot, user_id, message):
        return

    if user_id in ACTIVE_GENERATIONS:
        await message.answer("⏳ Дождись ответа на предыдущий запрос перед отправкой нового.")
        return

    model_id = user["selected_model"]
    pro_active = is_pro(user)

    if ALL_MODELS_MAP.get(model_id, {}).get("pro") and not pro_active:
        disc = has_active_discount(user)
        await message.answer(
            "🔒 Срок подписки истек. Выбери бесплатную модель в /menu или продли тариф:",
            reply_markup=shop_kb(disc),
        )
        return

    quota_source = await try_consume_quota(user_id, pro_active)
    if not quota_source:
        disc = has_active_discount(user)
        await message.answer(
            "⏳ Бесплатный лимит на сегодня и пакетные запросы исчерпаны.\n"
            "Приходи завтра, пригласи друга за +2 запроса (/top) или оформи подписку / пакет:",
            reply_markup=shop_kb(disc),
        )
        return

    ACTIVE_GENERATIONS.add(user_id)
    wait_msg = await message.answer("⏳ <i>Думаю...</i>", parse_mode=ParseMode.HTML)

    try:
        history = await get_history(user_id)
        answer_text = await generate_text_with_engine(history=history, user_text=message.text)

        await add_history(user_id, "user", message.text)
        await add_history(user_id, "assistant", answer_text)

        async with aiosqlite.connect(DB_PATH) as db:
            await db.execute("UPDATE users SET total_requests = total_requests + 1 WHERE user_id = ?", (user_id,))
            await db.commit()

        await wait_msg.delete()
        for i in range(0, len(answer_text), 4000):
            await message.answer(answer_text[i : i + 4000])

        await check_and_send_discount_offer(user_id, message)

    except Exception as e:
        await refund_quota(user_id, quota_source)
        await wait_msg.edit_text(
            f"⚠️ <b>Сервер нейросетей временно перегружен:</b>\n<code>{str(e)[:250]}</code>\n\nПопробуй повторить запрос через минуту.",
            parse_mode=ParseMode.HTML,
        )
    finally:
        ACTIVE_GENERATIONS.discard(user_id)


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
    dp = Dispatcher()
    dp.include_router(router)
    print("Бот запущен!")
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
