import asyncio
import uuid

from aiogram import Bot, Dispatcher, F, Router
from aiogram.filters import CommandStart
from aiogram.types import Message, CallbackQuery
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.client.default import DefaultBotProperties

TOKEN = "8806324044:AAEVEIXZCRG1fWAfIVYz1b69C3jEDIEQmrc"

bot = Bot(
    token=TOKEN,
    default=DefaultBotProperties(parse_mode="HTML")
)

referrals = {}

dp = Dispatcher()
router = Router()

users = {}


# ---------------- KEYBOARDS ----------------

def main_keyboard():
    kb = InlineKeyboardBuilder()

    kb.button(
        text="Подключить VPN",
        callback_data="profile",
        icon_custom_emoji_id="5323761960829862762"
    )

    kb.button(
        text="Оплатить подписку",
        callback_data="pay",
        icon_custom_emoji_id="5445350406215465190"
    )

    kb.button(
        text="Пригласить друга",
        callback_data="invite",
        style="primary",
        icon_custom_emoji_id="5260450573768990626"
    )

    kb.button(
        text="Наш канал",
        url="https://t.me/smelvpn",
        icon_custom_emoji_id="5260268501515377807"
    )

    kb.button(
        text="Помощь",
        url="https://t.me/smelvpn_help",
        icon_custom_emoji_id="5260535596941582167"
    )

    kb.button(
        text="Профиль",
        callback_data="profile",
        icon_custom_emoji_id="5258011929993026890"
    )

    kb.button(
        text="О сервисе",
        callback_data="about",
    )

    kb.adjust(1, 1, 1, 2, 1, 1)

    return kb.as_markup()


def profile_keyboard():
    kb = InlineKeyboardBuilder()

    kb.button(text="Мои платежи",
              callback_data="payments",
              icon_custom_emoji_id="5444860552310457690"
    )
    kb.button(text="Мои устройства",
              callback_data="devices",
                icon_custom_emoji_id = "5447512780515078098"
    )
    kb.button(
        text="Перевыпустить ключ",
        callback_data="regen",
        icon_custom_emoji_id="5260687681733533075"
    )
    kb.button(text="Назад", callback_data="back")

    kb.adjust(1)
    return kb.as_markup()


# ---------------- START ----------------

@router.message(CommandStart())
async def start(message: Message):

    uid = str(message.from_user.id)
    username = message.from_user.username or message.from_user.first_name

    if uid not in users:
        users[uid] = {
            "uuid": str(uuid.uuid4()),
            "devices": 0
        }

    if uid not in referrals:
        referrals[uid] = {
            "invited": 0,
            "connected": 0,
            "balance": 0
        }

    text = (
        f"<blockquote>"
        f'<tg-emoji emoji-id="5974048815789903111">☺️</tg-emoji> {username} [{uid}]\n'
        f"</blockquote>\n\n"
        '╭ Подписка: <code>активна</code>\n'
        '╰ До: 27.06.2026'
    )

    await message.answer(text, reply_markup=main_keyboard())

def invite_keyboard():
    kb = InlineKeyboardBuilder()

    kb.button(
        text="Поделиться",
        callback_data="ref_send",
        icon_custom_emoji_id="5260450573768990626"
    )

    kb.button(
        text="QR код",
        callback_data="ref_qr",
        icon_custom_emoji_id="5445033158456145975"
    )

    kb.button(
        text="Назад",
        callback_data="back",
    )

    kb.adjust(1)
    return kb.as_markup()

@router.callback_query(F.data == "invite")
async def invite(call: CallbackQuery):

    uid = str(call.from_user.id)

    data = referrals.setdefault(uid, {
        "invited": 0,
        "connected": 0,
        "balance": 0
    })

    ref_link = f"https://t.me/zronetbot?start={uid}"

    text = (
        '<b><tg-emoji emoji-id="5427127139151397446">☺️</tg-emoji> Пригласите друга и получите:</b>\n\n'

        "╭ 3 дня — если друг подключит VPN\n"
        "╰ 10% с оплат ваших друзей\n\n"

        "<b>Статистика:</b>\n"
        f"├ Приглашено: <code>{data['invited']}</code> чел.\n"
        f"│ ╰ Подключили: <code>{data['connected']}</code> чел.\n"
        "│\n"
        f"╰ Накоплено: <code>{data['balance']} ₽</code>\n\n"

        "<b>🔗 Твоя реферальная ссылка:</b>\n"
        f"<code>{ref_link}</code>"
    )

    await call.message.edit_text(text, reply_markup=invite_keyboard())

# ---------------- PROFILE ----------------

@router.callback_query(F.data == "profile")
async def profile(call: CallbackQuery):

    user = users.setdefault(call.from_user.id, {
        "uuid": str(uuid.uuid4()),
        "devices": 0
    })

    vless_link = (
        f"vless://{user['uuid']}"
        f"@vpn.example.com:443"
        f"?security=reality"
        f"&type=tcp"
        f"&fp=chrome"
        f"#VPN"
    )

    text = (
        '<tg-emoji emoji-id="5787589837200562063">☺️</tg-emoji> <b>Твой ключ для подключения:</b>\n'
        f'╰ <code>{vless_link} </code>\n\n'
        f'<tg-emoji emoji-id="5447512780515078098">☺️</tg-emoji> Устройства: <b>{user["devices"]}/2</b>'
    )

    await call.message.edit_text(text, reply_markup=profile_keyboard())


@router.callback_query(F.data == "regen")
async def regen(call: CallbackQuery):
    users[call.from_user.id]["uuid"] = str(uuid.uuid4())

    await call.answer("Ключ перевыпущен", show_alert=True)
    await profile(call)


@router.callback_query(F.data == "back")
async def back(call: CallbackQuery):
    uid = call.from_user.id
    username = call.from_user.username or call.from_user.first_name

    text = (
        f"<blockquote>"
        f'<tg-emoji emoji-id="5974048815789903111">☺️</tg-emoji> {username} [{uid}]\n'
        f"</blockquote>\n\n"
        '<tg-emoji emoji-id="5974352611711651172">☺️</tg-emoji> Статус: Активен\n'
        '<tg-emoji emoji-id="5974475701179387553">☺️</tg-emoji> Подписка до: 27.06.2026\n\n'
        "Выберите нужный раздел:"
    )

    await call.message.edit_text(text, reply_markup=main_keyboard())


# ---------------- PAY ----------------

@router.callback_query(F.data == "pay")
async def pay(call: CallbackQuery):

    text = (
        '<tg-emoji emoji-id="5447242579827523388">☺️</tg-emoji> <b>Выберите удобный тариф</b>\n\n'
        '<tg-emoji emoji-id="5258011929993026890">☺️</tg-emoji> <b>Базовый</b>\n'
        '╰ 2 устройства\n\n'
        '<tg-emoji emoji-id="5258513401784573443">☺️</tg-emoji> <b>Стандарт</b>\n'
        '╰ 4 устройства\n\n'
        '<tg-emoji emoji-id="5257963315258204021">☺️</tg-emoji> <b>Семейный</b>\n'
        '╰ 6 устройств'
    )

    kb = InlineKeyboardBuilder()

    kb.button(text="Базовый — от 200₽ для себя",
              callback_data="plan_basic",
              icon_custom_emoji_id="5258011929993026890"
    )
    kb.button(text="Стандарт — от 400₽ для компании",
              callback_data="plan_standard",
              icon_custom_emoji_id="5258513401784573443"
    )
    kb.button(text="Семейный — от 500₽ для семьи",
              callback_data="plan_family",
              icon_custom_emoji_id="5257963315258204021"
    )
    kb.button(text="Назад", callback_data="back")

    kb.adjust(1)

    await call.message.edit_text(text, reply_markup=kb.as_markup())


@router.callback_query(F.data.startswith("plan_"))
async def choose_plan(call: CallbackQuery):

    tariffs = {
        "plan_basic": 'Базовый',
        "plan_standard": "Стандарт",
        "plan_family": "Семейный"
    }

    text = (
        f'<tg-emoji emoji-id="5258011929993026890">☺️</tg-emoji> <b>Тариф: {tariffs[call.data]}</b>\n\n'
        '<tg-emoji emoji-id="5787589837200562063">☺️</tg-emoji> Выберите срок подписки:'
    )

    kb = InlineKeyboardBuilder()

    kb.button(text="1 месяц — оплата", callback_data="pay_1m")
    kb.button(text="3 месяца — оплата", callback_data="pay_3m")
    kb.button(text="6 месяцев — оплата", callback_data="pay_6m")
    kb.button(text="Назад", callback_data="pay")

    kb.adjust(1)

    await call.message.edit_text(text, reply_markup=kb.as_markup())


@router.callback_query(F.data.contains("pay_"))
async def finish(call: CallbackQuery):

    await call.message.edit_text(
        "💳 <b>Создаём ссылку на оплату...</b>\n\n"
        "После оплаты доступ активируется автоматически ⚡"
    )


# ---------------- OTHER ----------------

@router.callback_query(F.data == "invite")
async def invite(call: CallbackQuery):
    await call.answer("Реферальная система пока не настроена")


@router.callback_query(F.data == "about")
async def about(call: CallbackQuery):
    await call.answer("VPN Bot by lodi and mls")


# ---------------- RUN ----------------

async def main():
    dp.include_router(router)

    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())