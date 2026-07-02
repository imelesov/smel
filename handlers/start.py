from aiogram import Router, F
from aiogram.filters import CommandStart
from aiogram.types import Message, CallbackQuery

import logging

from config.settings import CHANNEL_USERNAME
from db import ensure_user, get_user
from keyboards import main_keyboard, subscribe_keyboard
from services.subscription import welcome_text

logger = logging.getLogger(__name__)

router = Router()

PENDING_REFERRERS = {}


async def is_subscribed(bot, user_id: int) -> bool:
    try:
        member = await bot.get_chat_member(chat_id=CHANNEL_USERNAME, user_id=user_id)
        return member.status not in ["left", "kicked"]
    except Exception:
        return False


async def show_main_menu(bot, target_user, send_func):
    user_row = await get_user(target_user.id)
    await send_func(welcome_text(target_user, user_row), reply_markup=main_keyboard())


@router.message(CommandStart())
async def start(message: Message, bot):
    try:
        referrer_id = None
        args = message.text.split(maxsplit=1)
        if len(args) > 1 and args[1].isdigit():
            referrer_id = int(args[1])

        # Проверка подписки временно отключена
        # if not await is_subscribed(bot, message.from_user.id):
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

        await show_main_menu(bot, message.from_user, message.answer)
    except Exception as e:
        logger.error(f"Ошибка в start handler: {e}")


@router.callback_query(F.data == "check_sub")
async def check_sub(call: CallbackQuery, bot):
    try:
        # Проверка подписки временно отключена
        # if not await is_subscribed(bot, call.from_user.id):
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
        await show_main_menu(bot, call.from_user, call.message.answer)
    except Exception as e:
        logger.error(f"Ошибка в check_sub handler: {e}")


@router.callback_query(F.data == "back")
async def back(call: CallbackQuery):
    user_row = await get_user(call.from_user.id)
    await call.message.edit_text(
        welcome_text(call.from_user, user_row),
        reply_markup=main_keyboard()
    )
