from datetime import datetime, timedelta
from config.settings import PERIOD_DAYS, DEVICES_BY_PLAN, PLAN_NAMES, RU_MONTHS


def format_date_ru(date_obj) -> str:
    return f"{date_obj.day} {RU_MONTHS[date_obj.month]} {date_obj.year}"


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
        f'<tg-emoji emoji-id="5787589837200562063">👤</tg-emoji> <b>{full_name}</b> [<code>{message_user.id}</code>]\n\n'
        f"╭ Подписка: <code>{status}</code>\n"
    )

    if sub_line:
        text += sub_line + "\n"

    return text


def calculate_subscription_expires(period: str) -> datetime:
    days = PERIOD_DAYS.get(period, 30)
    return datetime.now() + timedelta(days=days)


def get_plan_devices(plan: str) -> int:
    return DEVICES_BY_PLAN.get(plan, 0)


def get_plan_name(plan: str) -> str:
    return PLAN_NAMES.get(plan, plan)
