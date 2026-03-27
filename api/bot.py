import os
import telebot
import requests
from flask import Flask, request

TOKEN = os.getenv("BOT_TOKEN")
VERCEL_URL = os.getenv("VERCEL_URL", "").replace("https://", "").replace("http://", "").strip("/")
CURRENCY_API_KEY = os.getenv("CURRENCY_API_KEY")

bot = telebot.TeleBot(TOKEN, threaded=False)
app = Flask(__name__)

# Тексты
STRINGS = {
    'ru': {
        'msg_lang': "✅ Язык установлен: 🇷🇺 Русский",
        'btn_rates': "📊 Курсы валют",
        'btn_crypto': "₿ Крипта",
        'loading': "⏳ <i>Загружаю данные...</i>",
        'err': "❌ Ошибка API"
    },
    'en': {
        'msg_lang': "✅ Language set: 🇬🇧 English",
        'btn_rates': "📊 Exchange Rates",
        'btn_crypto': "₿ Crypto",
        'loading': "⏳ <i>Loading...</i>",
        'err': "❌ API Error"
    }
}

# 1. Клавиатура выбора языка
def lang_keyboard():
    markup = telebot.types.InlineKeyboardMarkup()
    markup.row(
        telebot.types.InlineKeyboardButton("🇷🇺 Русский", callback_data="set_ru"),
        telebot.types.InlineKeyboardButton("🇬🇧 English", callback_data="set_en")
    )
    return markup

# 2. Главное меню (зависит от языка)
def main_keyboard(lang):
    markup = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True)
    s = STRINGS[lang]
    markup.row(s['btn_rates'], s['btn_crypto'])
    return markup

@bot.message_handler(commands=['start'])
def start(message):
    bot.send_message(message.chat.id, "<b>💹 Financial Syndicate</b>\n\nChoose language / Выберите язык:", 
                     reply_markup=lang_keyboard(), parse_mode='HTML')

# Обработка выбора языка
@bot.callback_query_handler(func=lambda call: call.data.startswith('set_'))
def handle_lang(call):
    lang = call.data.split('_')[1]
    bot.answer_callback_query(call.id)
    bot.send_message(call.message.chat.id, STRINGS[lang]['msg_lang'], 
                     reply_markup=main_keyboard(lang))

# Обработка кнопок меню (Курсы валют)
@bot.message_handler(func=lambda m: True)
def handle_menu(message):
    # Определяем язык по тексту кнопки, чтобы не хранить его в памяти
    lang = 'en' if 'Rates' in message.text else 'ru'
    
    if "Курсы" in message.text or "Rates" in message.text:
        bot.send_message(message.chat.id, STRINGS[lang]['loading'], parse_mode='HTML')
        try:
            url = f"https://v6.exchangerate-api.com/v6/{CURRENCY_API_KEY}/latest/USD"
            data = requests.get(url, timeout=7).json()
            rub = data['conversion_rates']['RUB']
            res = f"🇺🇸 USD → RUB: <b>{rub:.2f}</b>" if lang == 'ru' else f"USD/RUB: <b>{rub:.2f}</b>"
            bot.send_message(message.chat.id, res, parse_mode='HTML')
        except:
            bot.send_message(message.chat.id, STRINGS[lang]['err'])

# --- ТЕХНИЧЕСКИЙ БЛОК ДЛЯ VERCEL ---
@app.route('/' + TOKEN, methods=['POST'])
def get_update():
    if request.headers.get('content-type') == 'application/json':
        json_string = request.get_data().decode('utf-8')
        update = telebot.types.Update.de_json(json_string)
        bot.process_new_updates([update])
        return '', 200
    return 'error', 403

@app.route('/')
def setup():
    bot.remove_webhook()
    bot.set_webhook(url=f'https://{VERCEL_URL}/{TOKEN}')
    return "✅ Вебхук обновлен!", 200
