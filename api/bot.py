import os
import telebot
import requests
from flask import Flask, request

# Берем настройки из Environment Variables
TOKEN = os.getenv("BOT_TOKEN")
CURRENCY_API_KEY = os.getenv("CURRENCY_API_KEY")
VERCEL_URL = os.getenv("VERCEL_URL")

bot = telebot.TeleBot(TOKEN, threaded=False)
app = Flask(__name__)

# Тексты сообщений
WELCOME_IMAGE = "https://i.imgur.com/4M7IWwP.jpeg"
TEXT_RU = "<b>💹 Financial Syndicate</b>\n\nВыбери язык:"
TEXT_EN = "<b>💹 Financial Syndicate</b>\n\nChoose language:"

def get_keyboard():
    markup = telebot.types.InlineKeyboardMarkup()
    markup.row(
        telebot.types.InlineKeyboardButton("🇷🇺 Русский", callback_data="l_ru"),
        telebot.types.InlineKeyboardButton("🇬🇧 English", callback_data="l_en")
    )
    return markup

@bot.message_handler(commands=['start'])
def start(message):
    try:
        # Пытаемся отправить фото
        bot.send_photo(message.chat.id, WELCOME_IMAGE, caption=TEXT_RU, reply_markup=get_keyboard(), parse_mode='HTML')
    except:
        # Если фото не грузится, шлем просто текст
        bot.send_message(message.chat.id, TEXT_RU, reply_markup=get_keyboard(), parse_mode='HTML')

@bot.callback_query_handler(func=lambda call: call.data.startswith('l_'))
def lang_answer(call):
    bot.answer_callback_query(call.id)
    bot.send_message(call.message.chat.id, "✅ Бот готов к работе!")

# --- Логика сервера ---
@app.route('/' + TOKEN, methods=['POST'])
def receive_update():
    if request.headers.get('content-type') == 'application/json':
        json_string = request.get_data().decode('utf-8')
        update = telebot.types.Update.de_json(json_string)
        bot.process_new_updates([update])
        return '', 200
    return 'Forbidden', 403

@app.route('/')
def setup_webhook():
    bot.remove_webhook()
    bot.set_webhook(url=f'https://{VERCEL_URL}/{TOKEN}')
    return "✅ Вебхук успешно обновлен!", 200
