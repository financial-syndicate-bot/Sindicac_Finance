import os
import telebot
import requests
from flask import Flask, request

# Загрузка ключей из настроек Vercel
TOKEN = os.getenv("BOT_TOKEN")
CURRENCY_API_KEY = os.getenv("CURRENCY_API_KEY")
VERCEL_URL = os.getenv("VERCEL_URL")

bot = telebot.TeleBot(TOKEN, threaded=False)
app = Flask(__name__)

# --- Данные бота ---
WELCOME_IMAGE_URL = "https://i.imgur.com/4M7IWwP.jpeg"
strings = {
    'ru': {
        'welcome': "<b>💹 Financial Syndicate</b>\n\nВыбери язык:",
        'rates': "📊 Курсы валют",
    },
    'en': {
        'welcome': "<b>💹 Financial Syndicate</b>\n\nChoose language:",
        'rates': "📊 Exchange Rates",
    }
}

# --- Логика бота ---
def get_lang_keyboard():
    markup = telebot.types.InlineKeyboardMarkup()
    markup.row(
        telebot.types.InlineKeyboardButton("🇷🇺 Русский", callback_data="l_ru"),
        telebot.types.InlineKeyboardButton("🇬🇧 English", callback_data="l_en")
    )
    return markup

@bot.message_handler(commands=['start'])
def send_welcome(message):
    try:
        bot.send_photo(
            message.chat.id, 
            WELCOME_IMAGE_URL, 
            caption=strings['ru']['welcome'], 
            reply_markup=get_lang_keyboard(),
            parse_mode='HTML'
        )
    except Exception as e:
        bot.reply_to(message, "Financial Syndicate: Выберите язык / Choose language", reply_markup=get_lang_keyboard())

@bot.callback_query_handler(func=lambda call: call.data.startswith('l_'))
def set_lang(call):
    bot.answer_callback_query(call.id)
    bot.send_message(call.message.chat.id, "✅ Настройка завершена! / Setup complete!")

# --- Настройка Webhook для Vercel ---
@app.route('/' + TOKEN, methods=['POST'])
def getMessage():
    try:
        json_string = request.get_data().decode('utf-8')
        update = telebot.types.Update.de_json(json_string)
        bot.process_new_updates([update])
        return "!", 200
    except Exception as e:
        print(f"Error: {e}")
        return "Error", 500

@app.route("/")
def webhook():
    bot.remove_webhook()
    # Установка связи с Telegram
    status = bot.set_webhook(url=f'https://{VERCEL_URL}/{TOKEN}')
    if status:
        return "Webhook set успешно!", 200
    else:
        return "Webhook failed", 500
