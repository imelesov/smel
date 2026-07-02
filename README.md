# Smel VPN Mini App

Полноценный Telegram Mini App для VPN сервиса с интеграцией в существующий бэкенд.

## Функционал

- ✅ **Главный экран** - статус подключения, быстрые действия
- ✅ **Профиль** - информация о подписке, VPN ключ, баланс
- ✅ **Подписки** - выбор тарифов, оплата (СБП, CryptoBot, баланс)
- ✅ **Реферальная система** - приглашение друзей, статистика, бонусы
- ✅ **Интеграция с API** - полноценная работа с существующим бэкендом
- ✅ **Анимации** - плавные переходы, загрузка, hover эффекты
- ✅ **Telegram тема** - автоматическая адаптация под тему пользователя

## Установка

1. Установите зависимости:
```bash
npm install
```

## Запуск локально

### 1. Запустите VPN бэкенд (если не запущен)

```bash
cd ..
python main.py
```

Бэкенд будет доступен на `http://localhost:8000`

### 2. Запустите Mini App

```bash
npm run dev
```

Приложение будет доступно по адресу: `https://localhost:5173/`

⚠️ **Важно**: При первом запуске браузер покажет предупреждение о самоподписанном сертификате. Это нормально для локальной разработки. Нажмите "Продолжить" или "Advanced" → "Proceed to localhost".

## Структура проекта

```
miniapp/
├── src/
│   ├── screens/
│   │   ├── HomeScreen.jsx          # Главный экран
│   │   ├── ProfileScreen.jsx       # Профиль пользователя
│   │   ├── SubscriptionScreen.jsx  # Подписки и оплата
│   │   └── ReferralScreen.jsx      # Реферальная система
│   ├── App.jsx                     # Главный компонент с навигацией
│   ├── App.css                     # Стили приложения
│   ├── main.jsx                    # Точка входа
│   └── index.css                   # Глобальные стили
├── index.html                      # HTML с Telegram WebApp SDK
├── vite.config.js                  # Конфигурация Vite с HTTPS
└── package.json                    # Зависимости
```

## API Интеграция

Mini App использует следующие API endpoints из бэкенда:

- `GET /api/user/{telegram_id}` - данные пользователя
- `GET /api/referrals/{telegram_id}` - реферальная статистика
- `GET /api/plans` - список тарифов
- `POST /api/pay` - создание платежа СБП
- `POST /api/pay/crypto` - создание платежа CryptoBot
- `POST /api/pay/balance` - оплата с баланса
- `POST /api/regenerate-uuid` - перевыпуск VPN ключа

## Интеграция с Telegram

### 1. Настройка BotFather

1. Создайте бота через [@BotFather](https://t.me/BotFather)
2. Получите токен бота
3. Настройте домен через `/setdomain` в BotFather

### 2. Добавление Mini App в бот

В `bot.py` добавьте кнопку для открытия Mini App:

```python
def main_keyboard():
    kb = InlineKeyboardBuilder()
    kb.button(
        text="🛡️ Mini App",
        web_app=WebAppInfo(url="https://your-domain.com")
    )
    # ... остальные кнопки
    return kb.as_markup()
```

### 3. Деплой

Для продакшена нужно:

1. Собрать проект:
```bash
npm run build
```

2. Задеплоить `dist/` папку на хостинг с HTTPS (Vercel, Netlify, etc.)

3. Настроить домен в BotFather через `/setdomain`

## Тестирование в Telegram

Для локального тестирования в Telegram используйте ngrok:

1. Установите ngrok: https://ngrok.com/download
2. Запустите ngrok:
```bash
ngrok http 5173
```
3. Скопируйте HTTPS URL из ngrok
4. Используйте этот URL в BotFather через `/setdomain`

## Технологии

- React 18
- Vite 5
- Telegram WebApp SDK
- Lucide React (иконки)
- CSS Variables для темизации
- FastAPI (бэкенд)
- Supabase (база данных)

## Экраны приложения

### HomeScreen
- Статус подписки
- Быстрые действия (профиль, подписка, рефералы)
- Промо карточка для оформления подписки

### ProfileScreen
- Информация о пользователе
- Тариф, устройства, срок подписки
- VPN ключ с возможностью копирования
- Перевыпуск ключа

### SubscriptionScreen
- Выбор тарифа (Базовый, Стандарт, Семейный)
- Выбор срока (1, 3, 6 месяцев)
- Способы оплаты (СБП, CryptoBot, Баланс)
- Подтверждение оплаты

### ReferralScreen
- Бонусы за приглашения
- Статистика (приглашено, подключили, баланс)
- Реферальная ссылка
- Инструкция по использованию
