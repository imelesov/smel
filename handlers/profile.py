from aiogram import Router, F
from aiogram.types import CallbackQuery

import logging

from db import get_user, regenerate_uuid, mark_referral_connected
from keyboards import profile_keyboard
from config.settings import ADMIN_IDS

logger = logging.getLogger(__name__)

router = Router()


@router.callback_query(F.data == "profile")
async def profile(call: CallbackQuery, bot):
    try:
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
    except Exception as e:
        logger.error(f"Ошибка в profile handler: {e}")


@router.callback_query(F.data == "regen")
async def regen(call: CallbackQuery):
    await regenerate_uuid(call.from_user.id)
    await call.answer("🔑 Ключ перевыпущен", show_alert=True)
    
    # Show updated profile
    user = await get_user(call.from_user.id)
    if user:
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


@router.callback_query(F.data == "connect_vpn")
async def connect_vpn(call: CallbackQuery, bot):
    try:
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
                logger.error(f"Не удалось уведомить реферера {referrer_id}: {e}")

        await call.answer("⚙️ Эта функция скоро будет доступна", show_alert=True)
    except Exception as e:
        logger.error(f"Ошибка в connect_vpn handler: {e}")


@router.callback_query(F.data == "payments")
async def payments_history(call: CallbackQuery):
    await call.answer("Раздел истории платежей пока в разработке", show_alert=True)


@router.callback_query(F.data == "devices")
async def devices_section(call: CallbackQuery):
    await call.answer("Раздел управления устройствами пока в разработке", show_alert=True)
