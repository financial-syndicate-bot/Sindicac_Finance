
import telebot
import requests
import threading
import schedule
import time
from telebot import types

BOT_TOKEN = "СЮДА_ТОКЕН_ОТ_BOTFATHER"
CURRENCY_API_KEY = "СЮДА_КЛЮЧ_ОТ_EXCHANGERATE"
WELCOME_IMAGE_URL = "https://i.imgur.com/4M7IWwP.jpeg"

bot = telebot.TeleBot(BOT_TOKEN)

strings = {
    'ru': {
        'welcome':     "*💹 Financial Syndicate Terminal*\n\nДобро пожаловать! Выбери язык:",
        'btn_report':  "📊 Курсы валют",
        'btn_crypto':  "₿ Крипта",
        'btn_support': "❤️ Поддержать",
        'loading':     "⏳ *Загружаю данные...*",
        'choose_lang': "🌐 Выбери язык:",
    },
    'en': {
        'welcome':     "*💹 Financial Syndicate Terminal*\n\nWelcome! Choose your language:",
        'btn_report':  "📊 Exchange Rates",
        'btn_crypto':  "₿ Crypto",
        'btn_support': "❤️ Support",
        'loading':     "⏳ *Loading data...*",
        'choose_lang': "🌐 Choose language:",
    },
}

user_languages = {}


def get_main_keyboard(lang):
    s = strings[lang]
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.row(s['btn_report'], s['btn_crypto'])
    markup.row(s['btn_support'])
    return markup


def get_lang_keyboard():
    markup = types.InlineKeyboardMarkup()
    markup.row(
        types.InlineKeyboardButton("🇷🇺 Русский", callback_data="l_ru"),
        types.InlineKeyboardButton("🇬🇧 English",  callback_data="l_en"),
    )
    return markup


def fetch_forex():
    url = f"https://v6.exchangerate-api.com/v6/{CURRENCY_API_KEY}/latest/USD"
    r = requests.get(url, timeout=10)
    return r.json().get("conversion_rates", {})


def fetch_crypto():
    url = (
        "https://api.coingecko.com/api/v3/simple/price"
        "?ids=bitcoin,ethereum,toncoin&vs_currencies=usd,rub"
    )
    r = requests.get(url, timeout=10)
    return r.json()


def generate_forex_report(lang):
    rates = fetch_forex()
    rub = rates.get("RUB", 0)
    eur = rates.get("EUR", 1)
    gbp = rates.get("GBP", 1)
    cny = rates.get("CNY", 1)
    try_r = rates.get("TRY", 1)
    if lang == 'ru':
        return (
            "📊 *Курсы валют*\n\n"
            f"🇺🇸 USD → RUB: `{rub:.2f}`\n"
            f"🇪🇺 EUR → RUB: `{rub / eur:.2f}`\n"
            f"🇬🇧 GBP → RUB: `{rub / gbp:.2f}`\n"
            f"🇨🇳 CNY → RUB: `{rub / cny:.2f}`\n"
            f"🇹🇷 TRY → RUB: `{rub / try_r:.2f}`\n\n"
            f"🕐 _Обновлено только что_"
        )
    else:
        return (
            "📊 *Exchange Rates*\n\n"
            f"🇪🇺 EUR/USD: `{eur:.4f}`\n"
            f"🇷🇺 USD/RUB: `{rub:.2f}`\n"
            f"🇬🇧 GBP/USD: `{gbp:.4f}`\n"
            f"🇨🇳 USD/CNY: `{cny:.4f}`\n\n"
            f"🕐 _Just updated_"
        )


def generate_crypto_report(lang):
    data = fetch_crypto()
    btc = data.get("bitcoin", {})
    eth = data.get("ethereum", {})
    ton = data.get("toncoin", {})
    if lang == 'ru':
        return (
            "₿ *Крипто-рынок*\n\n"
            f"🟡 Bitcoin:  `${btc.get('usd', 0):,.0f}` / `{btc.get('rub', 0):,.0f} ₽`\n"
            f"🔵 Ethereum: `${eth.get('usd', 0):,.0f}` / `{eth.get('rub', 0):,.0f} ₽`\n"
            f"💎 TON:      `${ton.get('usd', 0):.2f}` / `{ton.get('rub', 0):.2f} ₽`\n\n"
            f"🕐 _Обновлено только что_"
        )
    else:
        return (
            "₿ *Crypto Market*\n\n"
            f"🟡 Bitcoin:  `${btc.get('usd', 0):,.0f}`\n"
            f"🔵 Ethereum: `${eth.get('usd', 0):,.0f}`\n"
            f"💎 TON:      `${ton.get('usd', 0):.2f}`\n\n"
            f"🕐 _Just updated_"
        )


@bot.message_handler(commands=['start'])
def send_welcome(message):
    bot.send_photo(
        message.chat.id,
        WELCOME_IMAGE_URL,
        caption=strings['ru']['welcome'],
        reply_markup=get_lang_keyboard(),
        parse_mode='Markdown',
    )


@bot.callback_query_handler(func=lambda call: call.data.startswith('l_'))
def set_lang(call):
    lang = call.data.split('_')[1]
    user_languages[call.from_user.id] = lang
    bot.answer_callback_query(call.id)
    bot.send_message(
        call.message.chat.id,
        "✅ Done!",
        reply_markup=get_main_keyboard(lang),
    )


@bot.message_handler(commands=['lang'])
def change_lang(message):
    lang = user_languages.get(message.from_user.id, 'ru')
    bot.send_message(
        message.chat.id,
        strings[lang]['choose_lang'],
        reply_markup=get_lang_keyboard(),
    )


@bot.message_handler(content_types=['text'])
def handle_text(message):
    lang = user_languages.get(message.from_user.id, 'ru')
    text = message.text

    if text in [strings[lang]['btn_report'], "/rates"]:
        m = bot.send_message(message.chat.id, strings[lang]['loading'], parse_mode='Markdown')
        bot.edit_message_text(
            generate_forex_report(lang),
            message.chat.id, m.message_id,
            parse_mode='Markdown',
        )

    elif text in [strings[lang]['btn_crypto'], "/crypto"]:
        m = bot.send_message(message.chat.id, strings[lang]['loading'], parse_mode='Markdown')
        bot.edit_message_text(
            generate_crypto_report(lang),
            message.chat.id, m.message_id,
            parse_mode='Markdown',
        )

    elif text == strings[lang]['btn_support']:
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton(
            "💳 Донат", url="https://send.monobank.ua/XXXXX"
        ))
        bot.send_message(
            message.chat.id,
            "❤️ Поддержать проект:",
            reply_markup=markup,
        )


def morning_broadcast():
    for uid, lang in user_languages.items():
        try:
            report = generate_forex_report(lang) + "\n\n" + generate_crypto_report(lang)
            bot.send_message(uid, f"🌅 *Доброе утро!*\n\n{report}", parse_mode='Markdown')
        except Exception:
            pass


def run_scheduler():
    schedule.every().day.at("09:00").do(morning_broadcast)
    while True:
        schedule.run_pending()
        time.sleep(30)


if __name__ == "__main__":
    print("💹 Financial Syndicate Terminal started...")
    threading.Thread(target=run_scheduler, daemon=True).start()
    bot.polling(none_stop=True)
