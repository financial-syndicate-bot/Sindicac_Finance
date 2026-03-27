import os
import telebot
import requests
from flask import Flask, request

TOKEN = os.getenv("BOT_TOKEN")
VERCEL_URL = os.getenv("VERCEL_URL")
CURRENCY_API_KEY = os.getenv("CURRENCY_API_KEY")

bot = telebot.TeleBot(TOKEN, threaded=False)
app = Flask(__name__)

strings = {
    'ru': {
        'welcome': "<b>💹 Financial Syndicate</b>\n\nВыбери язык / Choose language:",
        'btn_report': "📊 Курсы валют",
        'btn_crypto': "₿ Крипта",
        'loading': "⏳ <i>Загружаю данные...</i>",
    },
    'en': {
        'welcome': "<b>💹 Financial Syndicate</b>\n\nChoose language:",
        'btn_report': "📊 Exchange Rates",
        'btn_crypto': "₿ Crypto",
        'loading': "⏳ <i>Loading data...</i>",
    }
}

def get_lang_inline():
    markup = telebot.types.InlineKeyboardMarkup()
    markup.row(
        telebot.types.InlineKeyboardButton("🇷🇺 Русский", callback_data="l_ru"),
        telebot.types.InlineKeyboardButton("🇬🇧 English", callback_data="l_en")
    )
    return markup

def get_main_keyboard(lang):
    markup = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True)
    s = strings.get(lang, strings['ru'])
    markup.row(s['btn_report'], s['btn_crypto'])
    return markup

@bot.message_handler(commands=['start'])
def start(message):
    bot.send_message(message.chat.id, strings['ru']['welcome'], 
                     reply_markup=get_lang_inline(), parse_mode='HTML')

@bot.callback_query_handler(func=lambda call: call.data.startswith('l_'))
def set_language(call):
    lang = call.data.split('_')[1]
    bot.answer_callback_query(call.id)
    bot.send_message(call.message.chat.id, "✅ Done / Готово", 
                     reply_markup=get_main_keyboard(lang))

@bot.message_handler(func=lambda m: True)
def handle_text(message):
    # По умолчанию ставим ru, если язык еще не выбран
    lang = 'ru'
    if message.text in [strings['en']['btn_report'], strings['en']['btn_crypto']]:
        lang = 'en'
        
    if "Курсы" in message.text or "Rates" in message.text:
        bot.send_message(message.chat.id, strings[lang]['loading'], parse_mode='HTML')
        try:
            url = f"https://v6.exchangerate-api.com/v6/{CURRENCY_API_KEY}/latest/USD"
            r = requests.get(url, timeout=7).json()
            rub = r['conversion_rates']['RUB']
            text = f"🇺🇸 USD → RUB: <b>{rub:.2f}</b>" if lang == 'ru' else f"USD/RUB: <b>{rub:.2f}</b>"
            bot.send_message(message.chat.id, text, parse_mode='HTML')
        except Exception as e:
            bot.send_message(message.chat.id, f"Error: API key or Connection issue")

@app.route('/' + TOKEN, methods=['POST'])
def getMessage():
    try:
        json_string = request.get_data().decode('utf-8')
        update = telebot.types.Update.de_json(json_string)
        bot.process_new_updates([update])
        return "!", 200
    except Exception as e:
        print(f"Update error: {e}")
        return "ok", 200

@app.route('/')
def webhook():
    try:
        bot.remove_webhook()
        bot.set_webhook(url=f'https://{VERCEL_URL}/{TOKEN}')
        return "✅ Вебхук настроен!", 200
    except Exception as e:
        return f"❌ Ошибка: {str(e)}", 500
