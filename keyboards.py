from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.types import WebAppInfo
from config.settings import CHANNEL_URL, PLAN_NAMES, PERIODS, PRICES, PLAN_EMOJI


def main_keyboard():
    kb = InlineKeyboardBuilder()
    kb.button(text="🛡️ Mini App", web_app=WebAppInfo(url="https://smel.vercel.app/"))
    kb.button(text="Подключить VPN", callback_data="connect_vpn", icon_custom_emoji_id="5323761960829862762")
    kb.button(text="Оплатить подписку", callback_data="pay", icon_custom_emoji_id="5445350406215465190")
    kb.button(text="Пригласить друга", callback_data="invite", icon_custom_emoji_id="5260450573768990626", style="primary")
    kb.button(text="Наш канал", url=CHANNEL_URL, icon_custom_emoji_id="5260268501515377807")
    kb.button(text="Тех.Поддержка", url="https://t.me/smelvpn_help", icon_custom_emoji_id="5260535596941582167")
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


def period_keyboard(plan: str):
    kb = InlineKeyboardBuilder()
    for period, label in PERIODS.items():
        price = PRICES[plan][period]
        kb.button(text=f"{label} — {price}₽", callback_data=f"{plan}:{period}")
    kb.button(text="Назад", callback_data="pay")
    kb.adjust(1)
    return kb.as_markup()


def payment_method_keyboard(plan: str, period: str):
    kb = InlineKeyboardBuilder()
    kb.button(text="СБП", callback_data=f"sbp:{plan}:{period}", icon_custom_emoji_id="5444860552310457690")
    kb.button(text="CryptoBot", callback_data=f"crypto:{plan}:{period}", icon_custom_emoji_id="5445033158456145975")
    kb.button(text="Списать с баланса", callback_data=f"balance:{plan}:{period}", icon_custom_emoji_id="5258011929993026890")
    kb.button(text="Назад", callback_data=f"plan_{plan}")
    kb.adjust(1)
    return kb.as_markup()


def sbp_keyboard(payment_id: str, plan: str):
    kb = InlineKeyboardBuilder()
    kb.button(text="Я оплатил", callback_data=f"paid:{payment_id}", icon_custom_emoji_id="5974352611711651172")
    kb.button(text="Назад", callback_data=f"plan_{plan}")
    kb.adjust(1)
    return kb.as_markup()


def admin_payment_keyboard(payment_id: str):
    kb = InlineKeyboardBuilder()
    kb.button(text="✅ Подтвердить", callback_data=f"confirm:{payment_id}")
    kb.button(text="❌ Отклонить", callback_data=f"reject:{payment_id}")
    kb.adjust(2)
    return kb.as_markup()


def crypto_keyboard(pay_url: str, payment_id: str, plan: str):
    kb = InlineKeyboardBuilder()
    kb.button(text="Оплатить", url=pay_url, icon_custom_emoji_id="5258011929993026890")
    kb.button(text="✅ Я оплатил", callback_data=f"checkcrypto:{payment_id}")
    kb.button(text="Назад", callback_data=f"plan_{plan}")
    kb.adjust(1)
    return kb.as_markup()


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


def about_keyboard():
    kb = InlineKeyboardBuilder()
    kb.button(text="Пользовательское соглашение", url="https://telegra.ph/Polzovatelskoe-soglashenie-SMEL-VPN-06-27")
    kb.button(text="Политика конфиденциальности", url="https://telegra.ph/Politika-konfidencialnosti-Smel-VPN-06-27")
    kb.button(text="Перечень данных", url="https://telegra.ph/Perechen-dannyh-podlezhashchih-obrabotke-SMEL-VPN-06-27")
    kb.button(text="Назад", callback_data="back")
    kb.adjust(1)
    return kb.as_markup()
