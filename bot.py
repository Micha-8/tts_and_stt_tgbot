import telebot
from telebot.types import Message

import db
from config import BOT_TOKEN, MAX_USERS, MAX_SYMBOLS_PER_USER, WARNING_SYMBOLS_PER_USER
from tts import text_to_speech
from utils import create_keyboard

bot = telebot.TeleBot(BOT_TOKEN)

db.create_db()
db.create_table()


@bot.message_handler(commands=["start"])
def start(message: Message):
    if not db.is_user_in_db(message.from_user.id):
        all_users = db.get_all_users_data()
        if len(all_users) < MAX_USERS:
            db.add_new_user(message.from_user.id)
        else:
            bot.send_message(
                message.from_user.id,
                "К сожалению, лимит пользователей исчерпан. "
                "Вы не сможете воспользоваться ботом:("
            )
            return

    bot.send_message(
        message.from_user.id,
        f"<b>Привет, {message.from_user.first_name}!</b>\n"
        f"Я бот-озвучкер напиши мне любой текст (до 100 символов) и я его озвучу, "
        f" также помни что всего ты можешь озвучить 100 символов.\n"
        f"Для этого напиши команду /tts",
        reply_markup=create_keyboard(["/tts"]),
        parse_mode='HTML'
    )


@bot.message_handler(commands=["tts"])
def start_tts(message: Message):
    symbols = db.get_user_data(message.from_user.id)["tts_symbols"]
    if symbols > MAX_SYMBOLS_PER_USER:
        bot.send_message(message.from_user.id, 'У тебя закончились символы, ты не сможешь воспользоваться ботом')
        return
    if symbols > WARNING_SYMBOLS_PER_USER:
        bot.send_message(message.from_user.id, 'У тебя осталось меньше 200 символов')

    if not db.is_user_in_db(message.from_user.id):
        if len(db.get_all_users_data()) < MAX_USERS:
            db.add_new_user(message.from_user.id)
        else:
            bot.send_message(
                message.from_user.id,
                "К сожалению, лимит пользователей исчерпан. "
                "Вы не сможете воспользоваться ботом:("
            )
            return

    bot.send_message(
        message.from_user.id,
        f"<b>Привет, {message.from_user.first_name}!</b>\n"
        f"Я вижу ты готов озвучить свой текст\n",
        parse_mode='HTML'
    )
    bot.register_next_step_handler(message, tts_func)


def tts_func(message: Message):
    if message.content_type == 'text':
        symbols = db.get_user_data(message.from_user.id)["tts_symbols"]
        message_symbols = len(message.text)
        symbols += message_symbols

        db.update_row(message.from_user.id, 'message', message.text)
        db.update_row(message.from_user.id, 'tts_symbols', symbols)

        if symbols > MAX_SYMBOLS_PER_USER:
            bot.send_message(message.from_user.id, 'У тебя закончились символы, ты не сможешь воспользоваться ботом')
            return

        status, content = text_to_speech(message.text)
        if status:
            bot.send_voice(message.from_user.id, content)
        else:
            bot.send_message(message.from_user.id, content)
    else:
        bot.send_message(message.from_user.id, 'Пришли пожалуйста текст')


bot.infinity_polling()
