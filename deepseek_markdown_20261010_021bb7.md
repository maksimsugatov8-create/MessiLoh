# 🎓 Telegram-бот для анкет выпускников

Бот собирает анкеты выпускников школ: ФИО, контакты, школу, планы на будущее.
Ответы сохраняются в CSV-файл, администратор получает уведомления.

## 🚀 Быстрый старт

1. Создайте бота через [@BotFather](https://t.me/BotFather) → команда `/newbot`
2. Скопируйте токен
3. Установите переменные окружения:
   - `BOT_TOKEN` — токен от BotFather
   - `ADMIN_ID` — ваш Telegram ID (узнать у [@userinfobot](https://t.me/userinfobot))
4. Установите зависимости: `pip install -r requirements.txt`
5. Запустите: `python bot.py`

## 📋 Команды

- `/start` — начать заполнение анкеты
- `/cancel` — отменить заполнение
- `/stats` — количество анкет (только для админа)

## 📁 Данные

Ответы сохраняются в `surveys.csv` в формате с разделителем `;` (открывается в Excel).

## 🌐 Развёртывание

Подходит для [Render](https://render.com), [Railway](https://railway.app), [PythonAnywhere](https://pythonanywhere.com).
Укажите переменные окружения `BOT_TOKEN` и `ADMIN_ID` в настройках хостинга.