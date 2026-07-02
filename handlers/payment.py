from datetime import datetime, timedelta
from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import CallbackQuery, Message

import logging

from config.settings import (
    PRICES, PERIOD_DAYS, DEVICES_BY_PLAN, PLAN_NAMES, 
    PLAN_EMOJI, SBP_PHONE, SBP_BANK, ADMIN_IDS
)
from db import (
    get_payment, get_payment_by_provider_id, set_payment_status,
    activate_subscription, get_balance, add_balance, subtract_balance,
    reward_referrer_for_payment
)
from payments import create_payment, create_crypto_payment, check_crypto_payment
from keyboards import (
    pay_plans_keyboard, period_keyboard, payment_method_keyboard,
    sbp_keyboard, admin_payment_keyboard, crypto_keyboard
)
from services.subscription import calculate_subscription_expires, get_plan_devices, get_plan_name

logger = logging.getLogger(__name__)

router = Router()


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


@router.callback_query(F.data.startswith("plan_"))
async def choose_plan(call: CallbackQuery):
    plan = call.data.replace("plan_", "")

    emoji_id = PLAN_EMOJI.get(plan, "5258011929993026890")

    text = (
        f'<tg-emoji emoji-id="{emoji_id}">💳</tg-emoji> <b>Тариф: {PLAN_NAMES[plan]}</b>\n\n'
        '<tg-emoji emoji-id="5787589837200562063">📅</tg-emoji> Выберите срок подписки:'
    )

    await call.message.edit_text(text, reply_markup=period_keyboard(plan))


@router.callback_query(F.data.regexp(r"^(basic|standard|family):(1m|3m|6m)$"))
async def choose_payment_method(call: CallbackQuery):
    plan, period = call.data.split(":")
    price = PRICES[plan][period]

    text = (
        '<tg-emoji emoji-id="5258011929993026890">💳</tg-emoji> <b>Выберите способ оплаты</b>\n\n'
        f"╰ Стоимость: <code>{price} ₽</code>"
    )

    await call.message.edit_text(text, reply_markup=payment_method_keyboard(plan, period))


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

    expires = calculate_subscription_expires(period)
    devices = get_plan_devices(plan)
    plan_name = get_plan_name(plan)

    await activate_subscription(call.from_user.id, plan, plan_name, period, devices, expires)

    await call.message.edit_text(
        '<tg-emoji emoji-id="5974048815789903111">🎉</tg-emoji> <b>Оплата прошла успешно!</b>\n\n'
        f"Списано с баланса: {price} ₽\n"
        "Подписка активирована 🚀"
    )


# ──────────────────────────────────────────────────────────────────────────
# СБП (ручное подтверждение админом)
# ──────────────────────────────────────────────────────────────────────────

@router.callback_query(F.data.startswith("sbp:"))
async def sbp(call: CallbackQuery):
    _, plan, period = call.data.split(":")
    price = PRICES[plan][period]

    payment_id = await create_payment(call.from_user.id, plan, period, price, provider="sbp")

    text = (
        '<tg-emoji emoji-id="5444860552310457690">🏦</tg-emoji> <b>Оплата по СБП</b>\n\n'
        f"├ Сумма: <code>{price} ₽</code>\n"
        f"├ Номер: <code>{SBP_PHONE}</code>\n"
        f"╰ Банк: {SBP_BANK}\n\n"
        "После перевода нажмите кнопку ниже."
    )

    await call.message.edit_text(text, reply_markup=sbp_keyboard(payment_id, plan))


@router.callback_query(F.data.startswith("paid:"))
async def paid(call: CallbackQuery, bot):
    try:
        payment_id = call.data.split(":")[1]
        payment = await get_payment(payment_id)

        if not payment:
            await call.answer("Заявка не найдена ❌", show_alert=True)
            return

        _, user_id, plan, period, price, *_ = payment

        for admin in ADMIN_IDS:
            try:
                await bot.send_message(
                    admin,
                    '<tg-emoji emoji-id="5445350406215465190">💸</tg-emoji> <b>Новая заявка на оплату</b>\n\n'
                    f"├ Пользователь: <code>{user_id}</code>\n"
                    f"├ Тариф: {plan}\n"
                    f"├ Период: {period}\n"
                    f"╰ Сумма: {price} ₽",
                    reply_markup=admin_payment_keyboard(payment_id)
                )
            except Exception as e:
                logger.error(f"Не удалось уведомить админа {admin}: {e}")

        await call.message.edit_text(
            '<tg-emoji emoji-id="5974475701179387553">⏳</tg-emoji> Заявка отправлена администратору.\nПроверка занимает 1–5 минут.'
        )
    except Exception as e:
        logger.error(f"Ошибка в paid handler: {e}")


@router.callback_query(F.data.startswith("confirm:"))
async def confirm(call: CallbackQuery, bot):
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

    expires = calculate_subscription_expires(period)
    devices = get_plan_devices(plan)
    plan_name = get_plan_name(plan)

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
# CryptoBot
# ──────────────────────────────────────────────────────────────────────────

@router.callback_query(F.data.startswith("crypto:"))
async def crypto(call: CallbackQuery):
    try:
        _, plan, period = call.data.split(":")
        price = PRICES[plan][period]

        try:
            pay_url, payment_id = await create_crypto_payment(
                user_id=call.from_user.id, plan=plan, period=period, price=price
            )
        except RuntimeError as e:
            await call.answer("⚠️ Оплата криптой временно недоступна", show_alert=True)
            logger.error(f"Ошибка создания crypto платежа: {e}")
            return

        text = (
            '<tg-emoji emoji-id="5445033158456145975">₿</tg-emoji> <b>Оплата через CryptoBot</b>\n\n'
            f"├ Сумма: <code>{price} ₽</code> (в любой валюте по курсу CryptoBot)\n"
            "╰ Нажмите «Оплатить», выберите криптовалюту и переведите сумму\n\n"
            "После оплаты нажмите «✅ Я оплатил» — подписка активируется автоматически."
        )

        await call.message.edit_text(text, reply_markup=crypto_keyboard(pay_url, payment_id, plan))
    except Exception as e:
        logger.error(f"Ошибка в crypto handler: {e}")


@router.callback_query(F.data.startswith("checkcrypto:"))
async def check_crypto(call: CallbackQuery):
    payment_id = call.data.split(":")[1]

    is_paid = await check_crypto_payment(payment_id)

    if not is_paid:
        await call.answer("⏳ Оплата пока не найдена. Попробуйте через минуту.", show_alert=True)
        return

    payment = await get_payment(payment_id)
    _, user_id, plan, period, price, *_ = payment

    expires = calculate_subscription_expires(period)
    devices = get_plan_devices(plan)
    plan_name = get_plan_name(plan)

    await activate_subscription(user_id, plan, plan_name, period, devices, expires)
    await set_payment_status(payment_id, "paid")
    await reward_referrer_for_payment(user_id, price)

    await call.message.edit_text(
        '<tg-emoji emoji-id="5974048815789903111">🎉</tg-emoji> <b>Оплата прошла успешно!</b>\n\n'
        "Подписка активирована 🚀"
    )


# ──────────────────────────────────────────────────────────────────────────
# Admin commands
# ──────────────────────────────────────────────────────────────────────────

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
