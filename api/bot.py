import os
import telebot
import requests
from flask import Flask, request

# Данные из Environment Variables Vercel
TOKEN = os.getenv("BOT_TOKEN")
VERCEL_URL = os.getenv("VERCEL_URL")
CURRENCY_API_KEY = os.getenv("CURRENCY_API_KEY")

bot = telebot.TeleBot(TOKEN, threaded=False)
app = Flask(__name__)

# Тексты и настройки
strings = {
    'ru': {
        'welcome': "<b>💹 Financial Syndicate Terminal</b>\n\nВыбери язык:",
        'btn_report': "📊 Курсы валют",
        'btn_crypto': "₿ Крипта",
        'loading': "⏳ <i>Загружаю данные...</i>",
    },
    'en': {
        'welcome': "<b>💹 Financial Syndicate Terminal</b>\n\nChoose language:",
        'btn_report': "📊 Exchange Rates",
        'btn_crypto': "₿ Crypto",
        'loading': "⏳ <i>Loading data...</i>",
    }
}

# Хранилище языков (в памяти Vercel оно сбрасывается, но для сессии хватит)
user_langs = {}

# Клавиатуры
def get_main_keyboard(lang):
    markup = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True)
    s = strings[lang]
    markup.row(s['btn_report'], s['btn_crypto'])
    return markup

def get_lang_inline():
    markup = telebot.types.InlineKeyboardMarkup()
    markup.row(
        telebot.types.InlineKeyboardButton("🇷🇺 Русский", callback_data="l_ru"),
        telebot.types.InlineKeyboardButton("🇬🇧 English", callback_data="l_en")
    )
    return markup

# --- ОБРАБОТЧИКИ ---

@bot.message_handler(commands=['start'])
def start(message):
    bot.send_message(message.chat.id, strings['ru']['welcome'], 
                     reply_markup=get_lang_inline(), parse_mode='HTML')

@bot.callback_query_handler(func=lambda call: call.data.startswith('l_'))
def set_language(call):
    lang = call.data.split('_')[1]
    user_langs[call.from_user.id] = lang
    bot.answer_callback_query(call.id)
    bot.send_message(call.message.chat.id, "✅ Done / Готово", 
                     reply_markup=get_main_keyboard(lang))

@bot.message_handler(func=lambda m: True)
def handle_text(message):
    lang = user_langs.get(message.from_user.id, 'ru')
    
    if message.text in [strings['ru']['btn_report'], strings['en']['btn_report']]:
        bot.send_message(message.chat.id, strings[lang]['loading'], parse_mode='HTML')
        # Здесь вызывается ваша функция fetch_forex()
        url = f"https://v6.exchangerate-api.com/v6/{CURRENCY_API_KEY}/latest/USD"
        try:
            r = requests.get(url, timeout=5).json()
            rub = r['conversion_rates']['RUB']
            text = f"🇺🇸 USD → RUB: <b>{rub:.2f}</b>" if lang == 'ru' else f"USD/RUB: <b>{rub:.2f}</b>"
            bot.send_message(message.chat.id, text, parse_mode='HTML')
        except:
            bot.send_message(message.chat.id, "Error API")

# --- СЕРВЕРНАЯ ЧАСТЬ ---

@app.route('/' + TOKEN, methods=['POST'])
def getMessage():
    if request.headers.get('content-type') == 'application/json':
        json_string = request.get_data().decode('utf-8')
        update = telebot.types.Update.de_json(json_string)
        bot.process_new_updates([update])
        return "!", 200
    return "error", 403

@app.route('/')
def webhook():
    bot.remove_webhook()
    bot.set_webhook(url=f'https://{VERCEL_URL}/{TOKEN}')
    return "✅ Бот полностью обновлен и готов!", 200
