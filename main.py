import asyncio
import logging
import traceback
from datetime import datetime, timedelta

import uvicorn
from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from fastapi import FastAPI, Request

from config.settings import BOT_TOKEN

# Принудительно используем тестовый токен
BOT_TOKEN = "8806324044:AAEVEIXZCRG1fWAfIVYz1b69C3jEDIEQmrc"
from db import (
    init_db, get_payment_by_provider_id, set_payment_status,
    activate_subscription
)
from payments import check_crypto_payment
from services.subscription import calculate_subscription_expires, get_plan_devices, get_plan_name

# ──────────────────────────────────────────────────────────────────────────
# LOGGING
# ──────────────────────────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# ──────────────────────────────────────────────────────────────────────────
# BOT & APP INIT
# ──────────────────────────────────────────────────────────────────────────
bot = Bot(token=BOT_TOKEN, default=DefaultBotProperties(parse_mode="HTML"))
dp = Dispatcher()
app = FastAPI()

# ──────────────────────────────────────────────────────────────────────────
# IMPORT HANDLERS
# ──────────────────────────────────────────────────────────────────────────
from handlers import start, profile, payment, referral, other

dp.include_router(start.router)
dp.include_router(profile.router)
dp.include_router(payment.router)
dp.include_router(referral.router)
dp.include_router(other.router)

# ──────────────────────────────────────────────────────────────────────────
# WEBHOOK FOR CRYPTOBOT
# ──────────────────────────────────────────────────────────────────────────
@app.post("/cryptobot/webhook")
async def cryptobot_webhook(request: Request):
    """Webhook для автоматической обработки оплат от CryptoBot"""
    try:
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

        expires = calculate_subscription_expires(period)
        devices = get_plan_devices(plan)
        plan_name = get_plan_name(plan)

        await activate_subscription(user_id, plan, plan_name, period, devices, expires)
        await set_payment_status(payment_id, "paid")

        try:
            await bot.send_message(
                user_id,
                "🎉 <b>Оплата через CryptoBot прошла!</b>\n\n"
                "Подписка активирована автоматически 🚀"
            )
        except Exception as e:
            logger.error(f"Не удалось уведомить пользователя {user_id}: {e}")

        return {"ok": True}
    except Exception as e:
        logger.error(f"Ошибка в webhook CryptoBot: {e}")
        traceback.print_exc()
        return {"ok": True}


# ──────────────────────────────────────────────────────────────────────────
# BOT STARTUP
# ──────────────────────────────────────────────────────────────────────────
async def run_bot():
    """Запуск бота через polling"""
    try:
        await bot.delete_webhook(drop_pending_updates=True)
        logger.info("Бот запущен")
        await dp.start_polling(bot)
    except Exception as e:
        logger.error(f"Ошибка при запуске бота: {e}")
        traceback.print_exc()


async def run_webhook_server():
    """Запуск сервера для вебхуков (CryptoBot)"""
    config = uvicorn.Config(app, host="0.0.0.0", port=8000, log_level="info")
    server = uvicorn.Server(config)
    logger.info("Webhook сервер запущен на порту 8000")
    await server.serve()


async def main():
    """Главная функция запуска"""
    try:
        await init_db()
        logger.info("База данных инициализирована")
        
        # Запускаем бота и webhook сервер параллельно
        await asyncio.gather(run_bot(), run_webhook_server())
    except Exception as e:
        logger.error(f"Критическая ошибка: {e}")
        traceback.print_exc()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Бот остановлен")
    except Exception:
        logger.error("Неожиданная ошибка")
        traceback.print_exc()
        input("\nНажми Enter, чтобы закрыть программу...")
