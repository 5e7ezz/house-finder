import telegram
from telegram.ext import Updater, CommandHandler

TELEGRAM_BOT_NAME = 'my_house_finder_bot'
TELEGRAM_BOT_TOKEN = '1162799956:AAEjxUJ3mVP7QD9B4VflfC33T3HGh-ZI4NI'

TELEGRAM_CHAT_ID_JAMES = 549970579
TELEGRAM_CHAT_ID_DAISY = 1133348584
TELEGRAM_CHAT_ID_MICHAEL = 623417355

def send_photo(chat_id, photo_url, title, button_text, button_link):
    bot = telegram.Bot(token=TELEGRAM_BOT_TOKEN)
    bot.send_photo(chat_id=chat_id,
                   photo=photo_url,
                   caption=title,
                   disable_notification=True,
                   timeout=120,
                   reply_markup=telegram.InlineKeyboardMarkup(
                       inline_keyboard=[[telegram.InlineKeyboardButton(text=button_text, url=button_link)]]))


def command_start(updater, context):
    print('chat_id = {}'.format(updater.message.from_user.id))


def start_polling():
    updater = Updater(TELEGRAM_BOT_TOKEN, use_context=True)
    updater.dispatcher.add_handler(CommandHandler('start', command_start))
    updater.start_polling()
    updater.idle()

start_polling()
