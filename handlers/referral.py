from aiogram import Router, F
from aiogram.types import CallbackQuery

import logging

from db import get_referral_stats, get_balance
from keyboards import invite_keyboard

logger = logging.getLogger(__name__)

router = Router()


@router.callback_query(F.data == "invite")
async def invite(call: CallbackQuery, bot):
    try:
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
    except Exception as e:
        logger.error(f"Ошибка в invite handler: {e}")
