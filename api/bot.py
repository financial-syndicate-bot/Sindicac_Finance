import os
import telebot
import requests
from flask import Flask, request

# Данные берем из настроек Vercel (Environment Variables)
BOT_TOKEN = os.getenv("BOT_TOKEN")
CURRENCY_API_KEY = os.getenv("CURRENCY_API_KEY")
WELCOME_IMAGE_URL = "https://i.imgur.com/4M7IWwP.jpeg"

bot = telebot.TeleBot(BOT_TOKEN, threaded=False)
app = Flask(__name__)

# Сообщения
strings = {
    'ru': {
        'welcome': "<b>💹 Financial Syndicate</b>\n\nВыбери язык:",
        'btn_report': "📊 Курсы валют",
        'btn_crypto': "₿ Крипта",
        'btn_support': "❤️ Поддержать",
        'choose_lang': "🌐 Выбери язык:",
    },
    'en': {
        'welcome': "<b>💹 Financial Syndicate</b>\n\nChoose language:",
        'btn_report': "📊 Exchange Rates",
        'btn_crypto': "₿ Crypto",
        'btn_support': "❤️ Support",
        'choose_lang': "🌐 Choose language:",
    }
}

user_languages = {}

def get_lang_keyboard():
    markup = telebot.types.InlineKeyboardMarkup()
    markup.row(
        telebot.types.InlineKeyboardButton("🇷🇺 Русский", callback_data="l_ru"),
        telebot.types.InlineKeyboardButton("🇬🇧 English", callback_data="l_en"),
    )
    return markup

@bot.message_handler(commands=['start'])
def send_welcome(message):
    bot.send_photo(
        message.chat.id,
        WELCOME_IMAGE_URL,
        caption=strings['ru']['welcome'],
        reply_markup=get_lang_keyboard(),
        parse_mode='HTML'
    )

@bot.callback_query_handler(func=lambda call: call.data.startswith('l_'))
def set_lang(call):
    lang = call.data.split('_')[1]
    user_languages[call.from_user.id] = lang
    bot.answer_callback_query(call.id)
    bot.send_message(call.message.chat.id, "✅ Done! / Ready!")

# --- ЭТОТ БЛОК НУЖЕН ДЛЯ VERCEL ---

@app.route('/' + BOT_TOKEN, methods=['POST'])
def getMessage():
    json_string = request.get_data().decode('utf-8')
    update = telebot.types.Update.de_json(json_string)
    bot.process_new_updates([update])
    return "!", 200

@app.route("/")
def webhook():
    bot.remove_webhook()
    # Автоматически берет URL проекта из Vercel
    project_url = os.getenv("VERCEL_URL")
    bot.set_webhook(url=f'https://{project_url}/{BOT_TOKEN}')
    return "Webhook set successfully!", 200
