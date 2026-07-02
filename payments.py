import os
import uuid

import httpx
from dotenv import load_dotenv

from db import get_client

load_dotenv()

# Токен приложения CryptoBot (@CryptoBot -> Crypto Pay -> Create App)
# Хранить только в .env, никогда в коде!
CRYPTOBOT_TOKEN = os.getenv("CRYPTOBOT_TOKEN", "")
CRYPTOBOT_API = "https://pay.crypt.bot/api"


async def create_payment(user_id: int, plan: str, period: str, price: int, provider: str = "sbp"):
    payment_id = str(uuid.uuid4())

    db = await get_client()
    await db.table("payments").insert(
        {
            "id": payment_id,
            "user_id": user_id,
            "plan": plan,
            "period": period,
            "price": price,
            "provider": provider,
            "status": "pending",
        }
    ).execute()

    return payment_id


async def create_crypto_payment(user_id: int, plan: str, period: str, price: int):
    """
    Создаёт счёт в CryptoBot на сумму в рублях (price) и возвращает (pay_url, payment_id).
    CryptoBot сам показывает плательщику сумму в выбранной криптовалюте по своему курсу —
    конвертацию делать вручную не нужно.
    Требует CRYPTOBOT_TOKEN в переменных окружения.
    """
    if not CRYPTOBOT_TOKEN:
        raise RuntimeError("CRYPTOBOT_TOKEN не задан в .env — оплата криптой недоступна")

    payment_id = str(uuid.uuid4())

    db = await get_client()
    await db.table("payments").insert(
        {
            "id": payment_id,
            "user_id": user_id,
            "plan": plan,
            "period": period,
            "price": price,
            "provider": "crypto",
            "status": "pending",
        }
    ).execute()

    async with httpx.AsyncClient(timeout=15) as client:
        resp = await client.post(
            f"{CRYPTOBOT_API}/createInvoice",
            headers={"Crypto-Pay-API-Token": CRYPTOBOT_TOKEN},
            json={
                "currency_type": "fiat",
                "fiat": "RUB",
                "amount": str(price),
                "accepted_assets": "USDT",
                "description": f"VPN подписка: {plan} / {period}",
                "payload": payment_id,
            },
        )
        data = resp.json()

    if not data.get("ok"):
        raise RuntimeError(f"Ошибка CryptoBot API: {data}")

    invoice = data["result"]
    invoice_id = str(invoice["invoice_id"])
    pay_url = invoice["pay_url"]

    await db.table("payments").update({"provider_id": invoice_id}).eq("id", payment_id).execute()

    return pay_url, payment_id


async def check_crypto_payment(payment_id: str) -> bool:
    """
    Проверяет статус инвойса в CryptoBot по payment_id (без вебхука).
    Возвращает True, если оплачен.
    """
    from db import get_payment

    payment = await get_payment(payment_id)
    if not payment:
        return False

    _, _, _, _, _, _, provider_id, status = payment

    if status == "paid":
        return True

    if not provider_id:
        return False

    async with httpx.AsyncClient(timeout=15) as client:
        resp = await client.get(
            f"{CRYPTOBOT_API}/getInvoices",
            headers={"Crypto-Pay-API-Token": CRYPTOBOT_TOKEN},
            params={"invoice_ids": provider_id},
        )
        data = resp.json()

    if not data.get("ok"):
        return False

    items = data["result"]["items"]
    if not items:
        return False

    return items[0]["status"] == "paid"
