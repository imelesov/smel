import os
import uuid as uuid_lib
from datetime import datetime, timedelta

from dotenv import load_dotenv
from supabase import create_async_client, AsyncClient

load_dotenv()

# ──────────────────────────────────────────────────────────────────────────
# 🔑 СЮДА ВСТАВЛЯЮТСЯ КЛЮЧИ SUPABASE (или положи их в .env рядом с ботом):
#
#   SUPABASE_URL=https://xxxxxxxxxxxx.supabase.co
#   SUPABASE_KEY=eyJhbGciOi...   <- service_role ключ (Project Settings -> API)
#
# ВАЖНО: используй именно service_role ключ (не anon!), т.к. бот работает
# на сервере и таблицы защищены Row Level Security (см. supabase_schema.sql).
# Никогда не публикуй и не коммить service_role ключ в открытый репозиторий.
# ──────────────────────────────────────────────────────────────────────────
SUPABASE_URL = "https://paudlewzafpgpocrzruw.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InBhdWRsZXd6YWZwZ3BvY3J6cnV3Iiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc4MjU2MTI3OCwiZXhwIjoyMDk4MTM3Mjc4fQ.GfWRyZU7axn4VRjNPX9bN1Dn0rNf0WOMR-2rHWacAiE"

_client: AsyncClient | None = None


async def get_client() -> AsyncClient:
    """Создаёт (один раз) и возвращает асинхронный клиент Supabase."""
    global _client
    if _client is None:
        if not SUPABASE_URL or not SUPABASE_KEY:
            raise RuntimeError(
                "SUPABASE_URL / SUPABASE_KEY не заданы. Укажи их в .env "
                "(см. .env.example) или прямо в db.py."
            )
        _client = await create_async_client(SUPABASE_URL, SUPABASE_KEY)
    return _client


async def init_db():
    """
    Таблицы в Supabase создаются ОДИН РАЗ через SQL Editor в дашборде
    (файл supabase_schema.sql). Эта функция просто проверяет соединение.
    """
    db = await get_client()
    await db.table("users").select("telegram_id").limit(1).execute()


async def get_user(telegram_id: int):
    """Возвращает (telegram_id, username, first_name, uuid, devices, plan, subscription_until, balance, referrer_id) или None."""
    db = await get_client()
    res = await (
        db.table("users")
        .select("telegram_id,username,first_name,uuid,devices,plan,subscription_until,balance,referrer_id")
        .eq("telegram_id", telegram_id)
        .execute()
    )

    if not res.data:
        return None

    row = res.data[0]
    return (
        row["telegram_id"],
        row["username"],
        row["first_name"],
        row["uuid"],
        row["devices"],
        row["plan"],
        row["subscription_until"],
        row["balance"],
        row["referrer_id"],
    )


async def ensure_user(telegram_id: int, username: str, first_name: str, referrer_id: int = None) -> str:
    """Создаёт пользователя, если его ещё нет в базе. Возвращает его uuid (новый или существующий)."""
    user = await get_user(telegram_id)
    if user:
        return user[3]

    new_uuid = str(uuid_lib.uuid4())

    # реферал не может быть сам себе пригласившим
    if referrer_id == telegram_id:
        referrer_id = None

    db = await get_client()

    await db.table("users").insert(
        {
            "telegram_id": telegram_id,
            "username": username,
            "first_name": first_name,
            "uuid": new_uuid,
            "devices": 0,
            "referrer_id": referrer_id,
        }
    ).execute()

    if referrer_id:
        await (
            db.table("referrals")
            .upsert(
                {
                    "referrer_id": referrer_id,
                    "referred_id": telegram_id,
                    "connected": 0,
                },
                on_conflict="referred_id",
                ignore_duplicates=True,
            )
            .execute()
        )

    return new_uuid


async def regenerate_uuid(telegram_id: int) -> str:
    new_uuid = str(uuid_lib.uuid4())

    db = await get_client()
    await db.table("users").update({"uuid": new_uuid}).eq("telegram_id", telegram_id).execute()

    return new_uuid


async def get_payment(payment_id: str):
    """Возвращает (id, user_id, plan, period, price, provider, provider_id, status) или None."""
    db = await get_client()
    res = await (
        db.table("payments")
        .select("id,user_id,plan,period,price,provider,provider_id,status")
        .eq("id", payment_id)
        .execute()
    )

    if not res.data:
        return None

    row = res.data[0]
    return (
        row["id"],
        row["user_id"],
        row["plan"],
        row["period"],
        row["price"],
        row["provider"],
        row["provider_id"],
        row["status"],
    )


async def get_payment_by_provider_id(provider_id: str):
    db = await get_client()
    res = await (
        db.table("payments")
        .select("id,user_id,plan,period,price,provider,provider_id,status")
        .eq("provider_id", provider_id)
        .execute()
    )

    if not res.data:
        return None

    row = res.data[0]
    return (
        row["id"],
        row["user_id"],
        row["plan"],
        row["period"],
        row["price"],
        row["provider"],
        row["provider_id"],
        row["status"],
    )


async def set_payment_status(payment_id: str, status: str):
    db = await get_client()
    await db.table("payments").update({"status": status}).eq("id", payment_id).execute()


async def activate_subscription(user_id: int, plan: str, plan_name: str, period: str, devices: int, expires_at):
    """Продлевает/активирует подписку пользователю и обновляет его профиль."""
    expires_str_full = expires_at.isoformat()
    expires_str_human = expires_at.strftime("%d.%m.%Y")

    db = await get_client()

    await (
        db.table("subscriptions")
        .upsert(
            {
                "user_id": user_id,
                "plan": plan,
                "period": period,
                "expires_at": expires_str_full,
            },
            on_conflict="user_id",
        )
        .execute()
    )

    await (
        db.table("users")
        .update(
            {
                "plan": plan_name,
                "devices": devices,
                "subscription_until": expires_str_human,
            }
        )
        .eq("telegram_id", user_id)
        .execute()
    )


async def get_balance(telegram_id: int) -> int:
    user = await get_user(telegram_id)
    return user[7] if user else 0


async def add_balance(telegram_id: int, amount: int):
    """Атомарно увеличивает баланс через RPC-функцию increment_balance (см. supabase_schema.sql)."""
    db = await get_client()
    await db.rpc("increment_balance", {"p_telegram_id": telegram_id, "p_amount": amount}).execute()


async def subtract_balance(telegram_id: int, amount: int) -> bool:
    """Списывает с баланса, если хватает средств. Возвращает True/False.
    Атомарно через RPC-функцию decrement_balance_if_enough (см. supabase_schema.sql)."""
    db = await get_client()
    res = await db.rpc(
        "decrement_balance_if_enough", {"p_telegram_id": telegram_id, "p_amount": amount}
    ).execute()
    return bool(res.data)


async def extend_subscription_days(telegram_id: int, days: int):
    """Продлевает подписку пользователю на N дней (от текущей даты окончания или от сегодня)."""
    user = await get_user(telegram_id)
    if not user:
        return

    subscription_until = user[6]

    if subscription_until:
        try:
            current_expiry = datetime.strptime(subscription_until, "%d.%m.%Y")
        except ValueError:
            current_expiry = datetime.now()
    else:
        current_expiry = datetime.now()

    base = max(current_expiry, datetime.now())
    new_expiry = base + timedelta(days=days)

    db = await get_client()
    await (
        db.table("users")
        .update({"subscription_until": new_expiry.strftime("%d.%m.%Y")})
        .eq("telegram_id", telegram_id)
        .execute()
    )


async def get_referral_stats(telegram_id: int):
    """Возвращает (invited_count, connected_count)."""
    db = await get_client()

    invited_res = await (
        db.table("referrals")
        .select("referred_id", count="exact")
        .eq("referrer_id", telegram_id)
        .execute()
    )
    invited = invited_res.count or 0

    connected_res = await (
        db.table("referrals")
        .select("referred_id", count="exact")
        .eq("referrer_id", telegram_id)
        .eq("connected", 1)
        .execute()
    )
    connected = connected_res.count or 0

    return invited, connected


async def mark_referral_connected(referred_id: int) -> int | None:
    """
    Отмечает, что приглашённый пользователь подключил VPN.
    Если это первое подключение — начисляет рефереру +3 дня подписки.
    Возвращает referrer_id, если бонус начислен, иначе None.
    """
    db = await get_client()

    res = await (
        db.table("referrals")
        .select("referrer_id,connected")
        .eq("referred_id", referred_id)
        .execute()
    )

    if not res.data or res.data[0]["connected"] == 1:
        return None

    referrer_id = res.data[0]["referrer_id"]

    await db.table("referrals").update({"connected": 1}).eq("referred_id", referred_id).execute()

    await extend_subscription_days(referrer_id, 3)
    return referrer_id


async def reward_referrer_for_payment(referred_id: int, price: int) -> int | None:
    """Начисляет рефереру 10% от оплаты приглашённого. Возвращает referrer_id, если начислено."""
    db = await get_client()

    res = await db.table("referrals").select("referrer_id").eq("referred_id", referred_id).execute()

    if not res.data:
        return None

    referrer_id = res.data[0]["referrer_id"]
    bonus = round(price * 0.10)

    if bonus > 0:
        await add_balance(referrer_id, bonus)

    return referrer_id
