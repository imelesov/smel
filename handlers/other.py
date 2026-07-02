from aiogram import Router, F
from aiogram.types import CallbackQuery

from keyboards import about_keyboard

router = Router()


@router.callback_query(F.data == "about")
async def about(call: CallbackQuery):
    text = (
        "<b>Smel VPN</b>\n\n"
        "Smel VPN обеспечивает стабильный и безопасный доступ к сети. "
        "Мы используем современные протоколы с открытым исходным кодом, "
        "которые показывают высокую скорость и устойчивость при работе даже на слабых сетях.\n\n"
        "Все серверы оптимизированы под высокую нагрузку, а соединение защищено сквозным шифрованием.\n\n"
        "Подключение и управление сервисом полностью автоматизировано через Telegram, "
        "поэтому доступ к нему всегда остаётся простым и удобным, без ограничений со стороны маркетплейсов или приложений."
    )

    await call.message.edit_text(
        text,
        reply_markup=about_keyboard(),
        parse_mode="HTML"
    )
