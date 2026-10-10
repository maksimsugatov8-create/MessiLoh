"""
Telegram-бот для анкет выпускников.
"""
import os
import csv
import time
import json
import requests
from html import escape
from datetime import datetime

# ============ НАСТРОЙКИ ============
TOKEN = os.environ.get("BOT_TOKEN", "").strip()
_admin_raw = os.environ.get("ADMIN_ID", "0").strip()
ADMIN_ID = int(_admin_raw) if _admin_raw.isdigit() else 0
CSV_FILE = "surveys.csv"
API = f"https://api.telegram.org/bot{TOKEN}/"

users = {}

STEPS = [
    ("fio", "👤 Введите ваше ФИО полностью:"),
    ("birth_date", "🎂 Дата рождения (например, 15.06.2007):"),
    ("city", "🏙 В каком городе вы живёте?"),
    ("school", "🏫 Номер или название школы:"),
    ("graduation_year", "📅 Год выпуска (например, 2024):"),
    ("class_letter", "🔤 Буква класса (например, А):"),
    ("phone", "📞 Номер телефона:"),
    ("email", "📧 Email:"),
    ("university", "🎓 Куда поступили? (ВУЗ/колледж, или «нет»):"),
    ("specialty", "📚 Специальность / направление:"),
    ("plans", "🚀 Ваши планы на будущее:"),
    ("hobbies", "🎨 Ваши хобби и увлечения:"),
]


def send(chat_id, text, reply_markup=None):
    payload = {"chat_id": chat_id, "text": text, "parse_mode": "HTML"}
    if reply_markup:
        payload["reply_markup"] = json.dumps(reply_markup)
    try:
        r = requests.post(API + "sendMessage", data=payload, timeout=15)
        # Логируем ошибки Telegram, чтобы их было видно
        if not r.json().get("ok"):
            print(f"⚠️ Telegram error: {r.text}")
    except Exception as e:
        print(f"Ошибка отправки: {e}")


def save_survey(user_id, username, data):
    file_exists = os.path.isfile(CSV_FILE)
    headers = [
        "Дата", "Telegram ID", "Username", "ФИО", "Дата рождения", "Город",
        "Школа", "Год выпуска", "Класс", "Телефон", "Email",
        "ВУЗ", "Специальность", "Планы", "Хобби"
    ]
    with open(CSV_FILE, "a", newline="", encoding="utf-8-sig") as f:
        writer = csv.writer(f, delimiter=";")
        if not file_exists:
            writer.writerow(headers)
        writer.writerow([
            datetime.now().strftime("%Y-%m-%d %H:%M"),
            user_id,
            f"@{username}" if username else "—",
        ] + [data.get(key, "") for key, _ in STEPS])


def start_survey(chat_id):
    users[chat_id] = {"step": 0, "data": {}}
    send(chat_id,
         "👋 Привет! Заполним анкету выпускника.\n\n"
         "Для отмены введите /cancel.\n\n"
         f"📝 <b>Вопрос 1/{len(STEPS)}</b>\n{STEPS[0][1]}")


def handle_answer(chat_id, username, user_id, text):
    state = users[chat_id]
    step_index = state["step"]
    key, _ = STEPS[step_index]
    state["data"][key] = text
    state["step"] += 1

    if state["step"] < len(STEPS):
        _, next_question = STEPS[state["step"]]
        num = state["step"] + 1
        send(chat_id, f"📝 <b>Вопрос {num}/{len(STEPS)}</b>\n{next_question}")
    else:
        d = state["data"]
        summary = (
            "📋 <b>Проверьте вашу анкету:</b>\n\n"
            f"👤 ФИО: {escape(d.get('fio', ''))}\n"
            f"🎂 Дата рождения: {escape(d.get('birth_date', ''))}\n"
            f"🏙 Город: {escape(d.get('city', ''))}\n"
            f"🏫 Школа: {escape(d.get('school', ''))}\n"
            f"📅 Год выпуска: {escape(d.get('graduation_year', ''))}\n"
            f"🔤 Класс: {escape(d.get('class_letter', ''))}\n"
            f"📞 Телефон: {escape(d.get('phone', ''))}\n"
            f"📧 Email: {escape(d.get('email', ''))}\n"
            f"🎓 ВУЗ: {escape(d.get('university', ''))}\n"
            f"📚 Специальность: {escape(d.get('specialty', ''))}\n"
            f"🚀 Планы: {escape(d.get('plans', ''))}\n"
            f"🎨 Хобби: {escape(d.get('hobbies', ''))}\n\n"
            "Если всё верно — напишите <b>да</b>. Если хотите заново — <b>нет</b>."
        )
        state["step"] = -1
        send(chat_id, summary)


def handle_confirmation(chat_id, username, user_id, text):
    state = users[chat_id]
    answer = text.strip().lower()

    if answer in ("да", "yes", "y", "д"):
        save_survey(user_id, username, state["data"])
        send(chat_id, "✅ <b>Спасибо! Ваша анкета сохранена.</b>")
        if ADMIN_ID:
            fio = escape(state["data"].get("fio", "?"))
            send(ADMIN_ID, f"📥 Новая анкета от {fio}")
        del users[chat_id]
    elif answer in ("нет", "no", "n", "н"):
        send(chat_id, "🔄 Начинаем заново.")
        start_survey(chat_id)
    else:
        send(chat_id, "Пожалуйста, ответьте «да» или «нет».")


def main():
    if not TOKEN or ":" not in TOKEN:
        print("❌ BOT_TOKEN не задан или неверный формат!")
        print("   Проверьте переменные окружения на хостинге.")
        return

    print("🤖 Бот запущен. Ожидаю сообщения...")
    print(f"   Admin ID: {ADMIN_ID}")

    last_update_id = 0

    while True:
        try:
            r = requests.get(
                API + "getUpdates",
                params={"offset": last_update_id + 1, "timeout": 30},
                timeout=40,
            )
            data = r.json()
            if not data.get("ok"):
                print(f"⚠️ Ошибка Telegram API: {data}")
                time.sleep(5)
                continue
            updates = data.get("result", [])
        except Exception as e:
            print(f"Ошибка соединения: {e}")
            time.sleep(5)
            continue

        for update in updates:
            last_update_id = update["update_id"]
            msg = update.get("message")
            if not msg or "text" not in msg:
                continue

            chat_id = msg["chat"]["id"]
            user_id = msg["from"]["id"]
            username = msg["from"].get("username", "")
            text = msg["text"]

            try:
                if text == "/start":
                    start_survey(chat_id)
                elif text == "/cancel":
                    users.pop(chat_id, None)
                    send(chat_id, "❌ Заполнение отменено. /start — начать заново.")
                elif text == "/stats" and user_id == ADMIN_ID:
                    count = 0
                    if os.path.isfile(CSV_FILE):
                        with open(CSV_FILE, "r", encoding="utf-8-sig") as f:
                            count = sum(1 for _ in f) - 1
                    send(chat_id, f"📊 Всего анкет: {count}")
                elif chat_id in users:
                    state = users[chat_id]
                    if state["step"] == -1:
                        handle_confirmation(chat_id, username, user_id, text)
                    else:
                        handle_answer(chat_id, username, user_id, text)
                else:
                    send(chat_id, "Напишите /start, чтобы начать заполнение анкеты.")
            except Exception as e:
                print(f"Ошибка обработки сообщения: {e}")

        time.sleep(1)


if __name__ == "__main__":
    main()