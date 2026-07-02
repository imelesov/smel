import asyncio
from datetime import datetime, timedelta

import uvicorn
from aiogram import Bot, Dispatcher, Router, F
from aiogram.client.default import DefaultBotProperties
from aiogram.filters import CommandStart, Command
from aiogram.types import Message, CallbackQuery, WebAppInfo
from aiogram.utils.keyboard import InlineKeyboardBuilder
from fastapi import FastAPI, Request

from db import (
    init_db,
    ensure_user,
    get_user,
    regenerate_uuid,
    get_payment,
    get_payment_by_provider_id,
    set_payment_status,
    activate_subscription,
    get_balance,
    add_balance,
    subtract_balance,
    get_referral_stats,
    mark_referral_connected,
    reward_referrer_for_payment,
)
from payments import create_payment, create_crypto_payment, check_crypto_payment

# ──────────────────────────────────────────────────────────────────────────
# НАСТРОЙКИ
# ──────────────────────────────────────────────────────────────────────────

# ВАЖНО: токен НЕЛЬЗЯ хранить в коде. Положите его в файл .env:
#   BOT_TOKEN=ваш_токен
# и раскомментируйте строки с dotenv ниже (либо передавайте через переменные окружения сервера).
import os
from dotenv import load_dotenv
load_dotenv()

TOKEN = os.getenv("BOT_TOKEN", "8806324044:AAEVEIXZCRG1fWAfIVYz1b69C3jEDIEQmrc")

CHANNEL_USERNAME = "@smelvpn"
CHANNEL_URL = "https://t.me/smelvpn"
SUPPORT_URL = "https://t.me/smelvpn_help"

SBP_PHONE = "+79289888898"
SBP_BANK = "Т-Банк"

ADMIN_IDS = [
    1947875357,
    1742568382,
]

PRICES = {
    "basic": {"1m": 200, "3m": 540, "6m": 960},
    "standard": {"1m": 400, "3m": 1080, "6m": 1920},
    "family": {"1m": 500, "3m": 1350, "6m": 2400},
}

DEVICES_BY_PLAN = {
    "basic": 2,
    "standard": 4,
    "family": 6,
}

PLAN_NAMES = {
    "basic": "Базовый",
    "standard": "Стандарт",
    "family": "Семейный",
}

PERIODS = {
    "1m": "1 месяц",
    "3m": "3 месяца",
    "6m": "6 месяцев",
}

PERIOD_DAYS = {
    "1m": 30,
    "3m": 90,
    "6m": 180,
}

RU_MONTHS = {
    1: "января", 2: "февраля", 3: "марта", 4: "апреля",
    5: "мая", 6: "июня", 7: "июля", 8: "августа",
    9: "сентября", 10: "октября", 11: "ноября", 12: "декабря",
}


def format_date_ru(date_obj) -> str:
    return f"{date_obj.day} {RU_MONTHS[date_obj.month]} {date_obj.year}"

bot = Bot(token=TOKEN, default=DefaultBotProperties(parse_mode="HTML"))
dp = Dispatcher()
router = Router()
app = FastAPI()


# ──────────────────────────────────────────────────────────────────────────
# КЛАВИАТУРЫ
# ──────────────────────────────────────────────────────────────────────────

def main_keyboard():
    kb = InlineKeyboardBuilder()

    kb.button(text="🛡️ Mini App", web_app=WebAppInfo(url="https://imelesov.github.io/smel/"))
    kb.button(text="Подключить VPN", callback_data="connect_vpn", icon_custom_emoji_id="5323761960829862762")
    kb.button(text="Оплатить подписку", callback_data="pay", icon_custom_emoji_id="5445350406215465190")
    kb.button(text="Пригласить друга", callback_data="invite", icon_custom_emoji_id="5260450573768990626", style="primary")
    kb.button(text="Наш канал", url=CHANNEL_URL, icon_custom_emoji_id="5260268501515377807")
    kb.button(text="Тех.Поддержка", url=SUPPORT_URL, icon_custom_emoji_id="5260535596941582167")
    kb.button(text="Профиль", callback_data="profile", icon_custom_emoji_id="5258011929993026890")
    kb.button(text="О сервисе", callback_data="about", icon_custom_emoji_id="5448218903220176945")

    kb.adjust(1, 1, 1, 1, 2, 1, 1)

    return kb.as_markup()


def subscribe_keyboard():
    kb = InlineKeyboardBuilder()
    kb.button(text="Подписаться", url=CHANNEL_URL, icon_custom_emoji_id="5260268501515377807")
    kb.button(text="Проверить подписку", callback_data="check_sub", icon_custom_emoji_id="5260726538302660868")
    kb.adjust(1)
    return kb.as_markup()


def profile_keyboard():
    kb = InlineKeyboardBuilder()
    kb.button(text="Мои платежи", callback_data="payments", icon_custom_emoji_id="5444860552310457690")
    kb.button(text="Мои устройства", callback_data="devices", icon_custom_emoji_id="5447512780515078098")
    kb.button(text="Назад", callback_data="back")
    kb.adjust(1)
    return kb.as_markup()


def pay_plans_keyboard():
    kb = InlineKeyboardBuilder()
    kb.button(text="Базовый — от 200₽", callback_data="plan_basic", icon_custom_emoji_id="5258011929993026890")
    kb.button(text="Стандарт — от 400₽", callback_data="plan_standard", icon_custom_emoji_id="5258513401784573443")
    kb.button(text="Семейный — от 500₽", callback_data="plan_family", icon_custom_emoji_id="5257963315258204021")
    kb.button(text="Назад", callback_data="back")
    kb.adjust(1)
    return kb.as_markup()

# ──────────────────────────────────────────────────────────────────────────
# ВСПОМОГАТЕЛЬНОЕ
# ──────────────────────────────────────────────────────────────────────────

async def is_subscribed(user_id: int) -> bool:
    try:
        # Админы всегда считаются подписанными
        if user_id in ADMIN_IDS:
            return True
        
        member = await bot.get_chat_member(chat_id=CHANNEL_USERNAME, user_id=user_id)
        # Все статусы кроме left и kicked считаются подписанными
        # member, administrator, creator, restricted - все считаются подписанными
        return member.status in ["member", "administrator", "creator", "restricted"]
    except Exception as e:
        print(f"Ошибка проверки подписки для {user_id}: {e}")
        return False


def welcome_text(message_user, user_row) -> str:
    full_name = message_user.full_name
    subscription_until = user_row[6] if user_row else None

    if subscription_until:
        expires_date = datetime.strptime(subscription_until, "%d.%m.%Y")
        is_active = expires_date.date() >= datetime.now().date()
        status = "активна 🎉" if is_active else "истекла ❌"
        date_text = format_date_ru(expires_date)
        sub_line = f"╰ До: {date_text}"
    else:
        status = "не активна"
        sub_line = ""

    text = (
        f"<blockquote>"
        f'<tg-emoji emoji-id="5974048815789903111">{full_name}</tg-emoji> {full_name} [<code>{message_user.id}</code>]\n'
        f"</blockquote>\n\n"
        f"╭ Подписка: <code>{status}</code>\n"
    )

    if sub_line:
        text += sub_line + "\n"

    return text


async def show_main_menu(target_user, send_func):
    user_row = await get_user(target_user.id)
    await send_func(welcome_text(target_user, user_row), reply_markup=main_keyboard())
# ──────────────────────────────────────────────────────────────────────────
# СТАРТ / ПОДПИСКА НА КАНАЛ
# ──────────────────────────────────────────────────────────────────────────

PENDING_REFERRERS = {}


@router.message(CommandStart())
async def start(message: Message):
    referrer_id = None
    args = message.text.split(maxsplit=1)
    if len(args) > 1 and args[1].isdigit():
        referrer_id = int(args[1])

    # Проверка подписки временно отключена
    # if not await is_subscribed(message.from_user.id):
    #     if referrer_id:
    #         PENDING_REFERRERS[message.from_user.id] = referrer_id
    # 
    #     await message.answer(
    #         "🔒 Для использования бота подпишитесь на наш канал",
    #         reply_markup=subscribe_keyboard()
    #     )
    #     return

    if referrer_id is None:
        referrer_id = PENDING_REFERRERS.pop(message.from_user.id, None)

    await ensure_user(
        message.from_user.id,
        message.from_user.username,
        message.from_user.first_name,
        referrer_id=referrer_id,
    )

    await show_main_menu(message.from_user, message.answer)
@router.callback_query(F.data == "check_sub")
async def check_sub(call: CallbackQuery):
    # Проверка подписки временно отключена
    # if not await is_subscribed(call.from_user.id):
    #     await call.answer("❌ Вы ещё не подписались на канал", show_alert=True)
    #     return
    
    await call.answer("✅ Проверка подписки отключена", show_alert=True)

    referrer_id = PENDING_REFERRERS.pop(call.from_user.id, None)

    await ensure_user(
        call.from_user.id,
        call.from_user.username,
        call.from_user.first_name,
        referrer_id=referrer_id,
    )

    await call.message.delete()
    await show_main_menu(call.from_user, call.message.answer)

@router.callback_query(F.data == "back")
async def back(call: CallbackQuery):
    user_row = await get_user(call.from_user.id)
    await call.message.edit_text(
        welcome_text(call.from_user, user_row),
        reply_markup=main_keyboard()
    )


# ──────────────────────────────────────────────────────────────────────────
# ПРОФИЛЬ
# ──────────────────────────────────────────────────────────────────────────

@router.callback_query(F.data == "profile")
async def profile(call: CallbackQuery):
    user = await get_user(call.from_user.id)

    if not user:
        await call.answer("Сначала нажмите /start", show_alert=True)
        return

    _, _, _, user_uuid, devices, plan, subscription_until, balance, _ = user

    plan_text = plan if plan else "Нет активной подписки"
    subscription_text = subscription_until if subscription_until else "Не активна"

    vless_link = (
        f"vless://{user_uuid}"
        f"@vpn.example.com:443"
        f"?security=reality&type=tcp&fp=chrome"
        f"#SmelVPN"
    )

    text = (
        '<tg-emoji emoji-id="5787589837200562063">👤</tg-emoji> <b>Ваш профиль</b>\n\n'
        f"├ Тариф: <code>{plan_text}</code>\n"
        f"├ Подписка: <code>{subscription_text}</code>\n"
        f"├ Устройства: <code>{devices}</code>\n"
        f"╰ Баланс: <code>{balance} ₽</code>\n\n"
        '<tg-emoji emoji-id="5260687681733533075">🔑</tg-emoji> <b>Ваш VPN-ключ:</b>\n\n'
        f"<code>{vless_link}</code>"
    )

    await call.message.edit_text(text, reply_markup=profile_keyboard())

@router.callback_query(F.data == "regen")
async def regen(call: CallbackQuery):
    await regenerate_uuid(call.from_user.id)
    await call.answer("🔑 Ключ перевыпущен", show_alert=True)
    await profile(call)


@router.callback_query(F.data == "connect_vpn")
async def connect_vpn(call: CallbackQuery):
    referrer_id = await mark_referral_connected(call.from_user.id)

    if referrer_id:
        try:
            await bot.send_message(
                referrer_id,
                '<tg-emoji emoji-id="5974048815789903111">🎉</tg-emoji> '
                "Ваш друг подключил VPN!\n"
                "Вам начислено <b>+3 дня</b> подписки 🎁"
            )
        except Exception as e:
            print(f"Не удалось уведомить реферера {referrer_id}: {e}")

    await call.answer("⚙️ Эта функция скоро будет доступна", show_alert=True)
@router.message(Command("addbalance"))
async def add_balance_cmd(message: Message):
    if message.from_user.id not in ADMIN_IDS:
        return

    parts = message.text.split()

    if len(parts) != 3:
        await message.answer(
            "Использование:\n<code>/addbalance USER_ID СУММА</code>"
        )
        return

    try:
        target_id = int(parts[1])
        amount = int(parts[2])
    except ValueError:
        await message.answer("USER_ID и СУММА должны быть числами")
        return

    await add_balance(target_id, amount)
    new_balance = await get_balance(target_id)

    await message.answer(
        f"✅ Начислено {amount} ₽ пользователю <code>{target_id}</code>\n"
        f"Текущий баланс: {new_balance} ₽"
    )
# ──────────────────────────────────────────────────────────────────────────
# ВЫБОР ТАРИФА И СРОКА
# ──────────────────────────────────────────────────────────────────────────

@router.callback_query(F.data == "pay")
async def pay(call: CallbackQuery):
    text = (
        '<tg-emoji emoji-id="5447242579827523388">💰</tg-emoji> <b>Выберите удобный тариф</b>\n\n'
        '<tg-emoji emoji-id="5258011929993026890">🟢</tg-emoji> <b>Базовый</b>\n'
        '╰ 2 устройства\n\n'
        '<tg-emoji emoji-id="5258513401784573443">🟡</tg-emoji> <b>Стандарт</b>\n'
        '╰ 4 устройства\n\n'
        '<tg-emoji emoji-id="5257963315258204021">🔵</tg-emoji> <b>Семейный</b>\n'
        '╰ 6 устройств\n\n'
        "⭐ <b>Почему выбирают нас:</b>\n"
        "— высокая скорость\n"
        "— стабильные сервера\n"
        "— защита данных\n"
        "— простое подключение"
    )
    await call.message.edit_text(text, reply_markup=pay_plans_keyboard())

PLAN_EMOJI = {
    "basic": "5258011929993026890",
    "standard": "5258513401784573443",
    "family": "5257963315258204021",
}


@router.callback_query(F.data.startswith("plan_"))
async def choose_plan(call: CallbackQuery):
    plan = call.data.replace("plan_", "")  # basic / standard / family

    kb = InlineKeyboardBuilder()
    for period, label in PERIODS.items():
        price = PRICES[plan][period]
        kb.button(text=f"{label} — {price}₽", callback_data=f"{plan}:{period}")
    kb.button(text="Назад", callback_data="pay")
    kb.adjust(1)

    emoji_id = PLAN_EMOJI.get(plan, "5258011929993026890")

    text = (
        f'<tg-emoji emoji-id="{emoji_id}">💳</tg-emoji> <b>Тариф: {PLAN_NAMES[plan]}</b>\n\n'
        '<tg-emoji emoji-id="5787589837200562063">📅</tg-emoji> Выберите срок подписки:'
    )

    await call.message.edit_text(text, reply_markup=kb.as_markup())

@router.callback_query(F.data.regexp(r"^(basic|standard|family):(1m|3m|6m)$"))
async def choose_payment_method(call: CallbackQuery):
    plan, period = call.data.split(":")
    price = PRICES[plan][period]

    kb = InlineKeyboardBuilder()
    kb.button(text="СБП", callback_data=f"sbp:{plan}:{period}", icon_custom_emoji_id="5444860552310457690")
    kb.button(text="CryptoBot", callback_data=f"crypto:{plan}:{period}", icon_custom_emoji_id="5445033158456145975")
    kb.button(text="Списать с баланса", callback_data=f"balance:{plan}:{period}", icon_custom_emoji_id="5258011929993026890")
    kb.button(text="Назад", callback_data=f"plan_{plan}")
    kb.adjust(1)

    text = (
        '<tg-emoji emoji-id="5258011929993026890">💳</tg-emoji> <b>Выберите способ оплаты</b>\n\n'
        f"╰ Стоимость: <code>{price} ₽</code>"
    )

    await call.message.edit_text(text, reply_markup=kb.as_markup())


@router.callback_query(F.data.startswith("balance:"))
async def pay_with_balance(call: CallbackQuery):
    _, plan, period = call.data.split(":")
    price = PRICES[plan][period]

    current_balance = await get_balance(call.from_user.id)

    if current_balance < price:
        missing = price - current_balance
        await call.answer(
            f"❌ Недостаточно средств\n\n"
            f"Нужно: {price} ₽\n"
            f"На балансе: {current_balance} ₽\n"
            f"Не хватает: {missing} ₽",
            show_alert=True
        )
        return

    await subtract_balance(call.from_user.id, price)

    expires = datetime.now() + timedelta(days=PERIOD_DAYS.get(period, 30))
    devices = DEVICES_BY_PLAN.get(plan, 0)
    plan_name = PLAN_NAMES.get(plan, plan)

    await activate_subscription(call.from_user.id, plan, plan_name, period, devices, expires)

    await call.message.edit_text(
        '<tg-emoji emoji-id="5974048815789903111">🎉</tg-emoji> <b>Оплата прошла успешно!</b>\n\n'
        f"Списано с баланса: {price} ₽\n"
        "Подписка активирована 🚀"
    )
# ──────────────────────────────────────────────────────────────────────────
# ОПЛАТА: СБП (ручное подтверждение админом)
# ──────────────────────────────────────────────────────────────────────────

@router.callback_query(F.data.startswith("sbp:"))
async def sbp(call: CallbackQuery):
    _, plan, period = call.data.split(":")
    price = PRICES[plan][period]

    payment_id = await create_payment(call.from_user.id, plan, period, price, provider="sbp")

    kb = InlineKeyboardBuilder()
    kb.button(text="Я оплатил", callback_data=f"paid:{payment_id}", icon_custom_emoji_id="5974352611711651172")
    kb.button(text="Назад", callback_data=f"plan_{plan}")
    kb.adjust(1)

    text = (
        '<tg-emoji emoji-id="5444860552310457690">🏦</tg-emoji> <b>Оплата по СБП</b>\n\n'
        f"├ Сумма: <code>{price} ₽</code>\n"
        f"├ Номер: <code>{SBP_PHONE}</code>\n"
        f"╰ Банк: {SBP_BANK}\n\n"
        "После перевода нажмите кнопку ниже."
    )

    await call.message.edit_text(text, reply_markup=kb.as_markup())


@router.callback_query(F.data.startswith("paid:"))
async def paid(call: CallbackQuery):
    payment_id = call.data.split(":")[1]
    payment = await get_payment(payment_id)

    if not payment:
        await call.answer("Заявка не найдена ❌", show_alert=True)
        return

    _, user_id, plan, period, price, *_ = payment

    kb = InlineKeyboardBuilder()
    kb.button(text="✅ Подтвердить", callback_data=f"confirm:{payment_id}")
    kb.button(text="❌ Отклонить", callback_data=f"reject:{payment_id}")
    kb.adjust(2)

    for admin in ADMIN_IDS:
        try:
            await bot.send_message(
                admin,
                '<tg-emoji emoji-id="5445350406215465190">💸</tg-emoji> <b>Новая заявка на оплату</b>\n\n'
                f"├ Пользователь: <code>{user_id}</code>\n"
                f"├ Тариф: {plan}\n"
                f"├ Период: {period}\n"
                f"╰ Сумма: {price} ₽",
                reply_markup=kb.as_markup()
            )
        except Exception as e:
            print(f"Не удалось уведомить админа {admin}: {e}")

    await call.message.edit_text(
        '<tg-emoji emoji-id="5974475701179387553">⏳</tg-emoji> Заявка отправлена администратору.\nПроверка занимает 1–5 минут.'
    )

@router.callback_query(F.data.startswith("confirm:"))
async def confirm(call: CallbackQuery):
    if call.from_user.id not in ADMIN_IDS:
        await call.answer("Недостаточно прав", show_alert=True)
        return

    payment_id = call.data.split(":")[1]
    payment = await get_payment(payment_id)

    if not payment:
        await call.answer("Заявка не найдена", show_alert=True)
        return

    _, user_id, plan, period, price, _, _, status = payment

    if status == "paid":
        await call.answer("Уже подтверждено ранее", show_alert=True)
        return

    expires = datetime.now() + timedelta(days=PERIOD_DAYS.get(period, 30))
    devices = DEVICES_BY_PLAN.get(plan, 0)
    plan_name = PLAN_NAMES.get(plan, plan)

    await activate_subscription(user_id, plan, plan_name, period, devices, expires)
    await set_payment_status(payment_id, "paid")

    try:
        await bot.send_message(
            user_id,
            '<tg-emoji emoji-id="5974048815789903111">🎉</tg-emoji> <b>Оплата прошла успешно!</b>\n\n'
            "Подписка активирована.\n"
            "Теперь можно пользоваться VPN 🚀"
        )
    except Exception as e:
        print(f"Не удалось уведомить пользователя {user_id}: {e}")

    await call.message.edit_text(
        '<tg-emoji emoji-id="5974352611711651172">✅</tg-emoji> Платёж подтверждён.'
    )


@router.callback_query(F.data.startswith("reject:"))
async def reject(call: CallbackQuery):
    if call.from_user.id not in ADMIN_IDS:
        await call.answer("Недостаточно прав", show_alert=True)
        return

    payment_id = call.data.split(":")[1]
    await set_payment_status(payment_id, "rejected")
    await call.message.edit_text(
        '<tg-emoji emoji-id="5974408293349635007">❌</tg-emoji> Заявка отклонена'
    )


# ──────────────────────────────────────────────────────────────────────────
# ОПЛАТА: CryptoBot
# ──────────────────────────────────────────────────────────────────────────

@router.callback_query(F.data.startswith("crypto:"))
async def crypto(call: CallbackQuery):
    _, plan, period = call.data.split(":")
    price = PRICES[plan][period]

    try:
        pay_url, payment_id = await create_crypto_payment(
            user_id=call.from_user.id, plan=plan, period=period, price=price
        )
    except RuntimeError as e:
        await call.answer("⚠️ Оплата криптой временно недоступна", show_alert=True)
        print(e)
        return

    kb = InlineKeyboardBuilder()
    kb.button(text="Оплатить", url=pay_url, icon_custom_emoji_id="5258011929993026890")
    kb.button(text="✅ Я оплатил", callback_data=f"checkcrypto:{payment_id}")
    kb.button(text="Назад", callback_data=f"plan_{plan}")
    kb.adjust(1)

    text = (
        '<tg-emoji emoji-id="5445033158456145975">₿</tg-emoji> <b>Оплата через CryptoBot</b>\n\n'
        f"├ Сумма: <code>{price} ₽</code> (в любой валюте по курсу CryptoBot)\n"
        "╰ Нажмите «Оплатить», выберите криптовалюту и переведите сумму\n\n"
        "После оплаты нажмите «✅ Я оплатил» — подписка активируется автоматически."
    )

    await call.message.edit_text(text, reply_markup=kb.as_markup())


@router.callback_query(F.data.startswith("checkcrypto:"))
async def check_crypto(call: CallbackQuery):
    payment_id = call.data.split(":")[1]

    is_paid = await check_crypto_payment(payment_id)

    if not is_paid:
        await call.answer("⏳ Оплата пока не найдена. Попробуйте через минуту.", show_alert=True)
        return

    payment = await get_payment(payment_id)
    _, user_id, plan, period, price, *_ = payment

    expires = datetime.now() + timedelta(days=PERIOD_DAYS.get(period, 30))
    devices = DEVICES_BY_PLAN.get(plan, 0)
    plan_name = PLAN_NAMES.get(plan, plan)

    await activate_subscription(user_id, plan, plan_name, period, devices, expires)
    await set_payment_status(payment_id, "paid")
    await reward_referrer_for_payment(user_id, price)

    await call.message.edit_text(
        '<tg-emoji emoji-id="5974048815789903111">🎉</tg-emoji> <b>Оплата прошла успешно!</b>\n\n'
        "Подписка активирована 🚀"
    )
@app.post("/cryptobot/webhook")
async def cryptobot_webhook(request: Request):
    data = await request.json()

    if data.get("update_type") != "invoice_paid":
        return {"ok": True}

    invoice = data["payload"]
    invoice_id = str(invoice["invoice_id"])

    payment = await get_payment_by_provider_id(invoice_id)
    if not payment:
        return {"ok": True}

    payment_id, user_id, plan, period, price, _, _, status = payment

    if status == "paid":
        return {"ok": True}

    expires = datetime.now() + timedelta(days=PERIOD_DAYS.get(period, 30))
    devices = DEVICES_BY_PLAN.get(plan, 0)
    plan_name = PLAN_NAMES.get(plan, plan)

    await activate_subscription(user_id, plan, plan_name, period, devices, expires)
    await set_payment_status(payment_id, "paid")

    try:
        await bot.send_message(
            user_id,
            "🎉 <b>Оплата через CryptoBot прошла!</b>\n\n"
            "Подписка активирована автоматически 🚀"
        )
    except Exception as e:
        print(f"Не удалось уведомить пользователя {user_id}: {e}")

    return {"ok": True}


# ──────────────────────────────────────────────────────────────────────────
# API ДЛЯ MINI APP
# ──────────────────────────────────────────────────────────────────────────

@app.get("/api/user/{telegram_id}")
async def api_get_user(telegram_id: int):
    user = await get_user(telegram_id)
    if not user:
        return {"error": "User not found"}
    
    _, username, first_name, user_uuid, devices, plan, subscription_until, balance, referrer_id = user
    
    return {
        "telegram_id": telegram_id,
        "username": username,
        "first_name": first_name,
        "uuid": user_uuid,
        "devices": devices,
        "plan": plan,
        "subscription_until": subscription_until,
        "balance": balance,
        "referrer_id": referrer_id
    }

@app.get("/api/referrals/{telegram_id}")
async def api_get_referrals(telegram_id: int):
    invited, connected = await get_referral_stats(telegram_id)
    balance = await get_balance(telegram_id)
    
    bot_username = (await bot.get_me()).username
    ref_link = f"https://t.me/{bot_username}?start={telegram_id}"
    
    return {
        "invited": invited,
        "connected": connected,
        "balance": balance,
        "ref_link": ref_link
    }

@app.post("/api/pay")
async def api_create_payment(request: Request):
    data = await request.json()
    user_id = data.get("user_id")
    plan = data.get("plan")
    period = data.get("period")
    
    if not all([user_id, plan, period]):
        return {"error": "Missing required fields"}
    
    price = PRICES.get(plan, {}).get(period)
    if not price:
        return {"error": "Invalid plan or period"}
    
    payment_id = await create_payment(user_id, plan, period, price, provider="sbp")
    
    return {
        "payment_id": payment_id,
        "price": price,
        "sbp_phone": SBP_PHONE,
        "sbp_bank": SBP_BANK
    }

@app.post("/api/pay/crypto")
async def api_create_crypto_payment(request: Request):
    data = await request.json()
    user_id = data.get("user_id")
    plan = data.get("plan")
    period = data.get("period")
    
    if not all([user_id, plan, period]):
        return {"error": "Missing required fields"}
    
    price = PRICES.get(plan, {}).get(period)
    if not price:
        return {"error": "Invalid plan or period"}
    
    try:
        pay_url, payment_id = await create_crypto_payment(user_id, plan, period, price)
        return {
            "payment_id": payment_id,
            "pay_url": pay_url,
            "price": price
        }
    except RuntimeError as e:
        return {"error": str(e)}

@app.post("/api/pay/balance")
async def api_pay_with_balance(request: Request):
    data = await request.json()
    user_id = data.get("user_id")
    plan = data.get("plan")
    period = data.get("period")
    
    if not all([user_id, plan, period]):
        return {"error": "Missing required fields"}
    
    price = PRICES.get(plan, {}).get(period)
    if not price:
        return {"error": "Invalid plan or period"}
    
    current_balance = await get_balance(user_id)
    
    if current_balance < price:
        return {
            "error": "Insufficient balance",
            "current_balance": current_balance,
            "required": price
        }
    
    await subtract_balance(user_id, price)
    
    expires = datetime.now() + timedelta(days=PERIOD_DAYS.get(period, 30))
    devices = DEVICES_BY_PLAN.get(plan, 0)
    plan_name = PLAN_NAMES.get(plan, plan)
    
    await activate_subscription(user_id, plan, plan_name, period, devices, expires)
    
    return {
        "success": True,
        "new_balance": await get_balance(user_id),
        "expires": expires.strftime("%d.%m.%Y"),
        "devices": devices,
        "plan": plan_name
    }

@app.get("/api/plans")
async def api_get_plans():
    return {
        "plans": PRICES,
        "devices": DEVICES_BY_PLAN,
        "plan_names": PLAN_NAMES,
        "periods": PERIODS
    }

@app.post("/api/regenerate-uuid")
async def api_regenerate_uuid(request: Request):
    data = await request.json()
    user_id = data.get("user_id")
    
    if not user_id:
        return {"error": "Missing user_id"}
    
    new_uuid = await regenerate_uuid(user_id)
    return {"uuid": new_uuid}


# ──────────────────────────────────────────────────────────────────────────
# ПРОЧИЕ РАЗДЕЛЫ
# ──────────────────────────────────────────────────────────────────────────

def invite_keyboard(ref_link: str):
    share_url = (
        f"https://t.me/share/url?url={ref_link}"
        f"&text=Подключайся к Smel VPN 🚀"
    )

    kb = InlineKeyboardBuilder()
    kb.button(text="Поделиться", url=share_url, icon_custom_emoji_id="5260450573768990626")
    kb.button(text="Назад", callback_data="back")
    kb.adjust(1)
    return kb.as_markup()

@router.callback_query(F.data == "invite")
async def invite(call: CallbackQuery):
    invited, connected = await get_referral_stats(call.from_user.id)
    balance = await get_balance(call.from_user.id)

    bot_username = (await bot.get_me()).username
    ref_link = f"https://t.me/{bot_username}?start={call.from_user.id}"

    text = (
        '<b><tg-emoji emoji-id="5427127139151397446">🎁</tg-emoji> Пригласите друга и получите:</b>\n\n'
        "╭ 3 дня — если друг подключит VPN\n"
        "╰ 10% с оплат ваших друзей\n\n"
        "<b>Статистика:</b>\n"
        f"├ Приглашено: <code>{invited}</code> чел.\n"
        f"│ ╰ Подключили: <code>{connected}</code> чел.\n"
        "│\n"
        f"╰ Баланс: <code>{balance} ₽</code>\n\n"
        "<b>🔗 Твоя реферальная ссылка:</b>\n"
        f"<code>{ref_link}</code>"
    )

    await call.message.edit_text(text, reply_markup=invite_keyboard(ref_link))

@router.callback_query(F.data == "about")
async def about(call: CallbackQuery):
    text = (
        "<b>Smel VPN</b>\n\n"
        "Smel VPN обеспечивает стабильный и безопасный доступ к сети. "
        "Мы используем современные протоколы с открытым исходным кодом, "
        "которые показывают высокую скорость и устойчивость при работе даже на слабых сетях.\n\n"
        "Все серверы оптимизированы под высокую нагрузку, а соединение защищено сквозным шифрованием.\n\n"
        "Подключение и управление сервисом полностью автоматизировано через Telegram, "
        "поэтому доступ к нему всегда остаётся простым и удобным, без ограничений со стороны маркетплейсов или приложений."
    )

    kb = InlineKeyboardBuilder()

    kb.button(
        text="Пользовательское соглашение",
        url="https://telegra.ph/Polzovatelskoe-soglashenie-SMEL-VPN-06-27"
    )
    kb.button(
        text="Политика конфиденциальности",
        url="https://telegra.ph/Politika-konfidencialnosti-Smel-VPN-06-27"
    )
    kb.button(
        text="Перечень данных",
        url="https://telegra.ph/Perechen-dannyh-podlezhashchih-obrabotke-SMEL-VPN-06-27"
    )
    kb.button(text="Назад", callback_data="back")

    kb.adjust(1)

    await call.message.edit_text(
        text,
        reply_markup=kb.as_markup(),
        parse_mode="HTML"
    )

@router.callback_query(F.data == "payments")
async def payments_history(call: CallbackQuery):
    await call.answer("Раздел истории платежей пока в разработке", show_alert=True)


@router.callback_query(F.data == "devices")
async def devices_section(call: CallbackQuery):
    await call.answer("Раздел управления устройствами пока в разработке", show_alert=True)


# ──────────────────────────────────────────────────────────────────────────
# ЗАПУСК
# ──────────────────────────────────────────────────────────────────────────

async def run_bot():
    dp.include_router(router)
    try:
        await bot.delete_webhook(drop_pending_updates=True)
    except Exception as e:
        print("Не удалось удалить webhook:", e)
    await dp.start_polling(bot)


async def run_webhook_server():
    # Сервер для приёма вебхуков CryptoBot. Нужен публичный HTTPS-домен.
    # Если CryptoBot не используется — этот сервер можно не запускать.
    config = uvicorn.Config(app, host="0.0.0.0", port=8000, log_level="info")
    server = uvicorn.Server(config)
    await server.serve()


async def main():
    await init_db()
    await asyncio.gather(run_bot(), run_webhook_server())

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except Exception:
        import traceback
        traceback.print_exc()
        input("\nНажми Enter, чтобы закрыть программу...")
