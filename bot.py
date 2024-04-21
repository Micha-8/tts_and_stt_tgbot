import telebot
from telebot.types import Message
import math

import db
from config import (BOT_TOKEN, MAX_USERS, MAX_SYMBOLS_PER_USER, WARNING_SYMBOLS_PER_USER, MAX_USER_STT_BLOCKS,
                    WARNING_STT_BLOCKS, MAX_SECONDS_FOR_AUDIO, SECONDS_PER_ONE_BLOCK)
from tts_and_stt import text_to_speech, speech_to_text
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
        f"Я бот, который может озвучить или разобрать из аудио текст\n"
        f"Также помни, что есть ограничения для ознакомления используй команду /limits\n"
        f"Для озвучки текста используй команду /tts, а для перевода из аудио в текст /stt",
        reply_markup=create_keyboard(["/tts", "/stt"]),
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
            bot.send_voice(message.from_user.id, content, reply_to_message_id=message.id)
        else:
            bot.send_message(message.from_user.id, content)
    else:
        bot.send_message(message.from_user.id, 'Пришли пожалуйста текст', reply_to_message_id=message.id)


@bot.message_handler(commands=["stt"])
def start_stt(message: Message):
    blocks = db.get_user_data(message.from_user.id)["stt_blocks"]
    if blocks > MAX_USER_STT_BLOCKS:
        bot.send_message(message.from_user.id, 'У тебя закончились аудио блоки, ты не сможешь воспользоваться ботом')
        return
    if blocks > WARNING_STT_BLOCKS:
        bot.send_message(message.from_user.id, 'У тебя осталось меньше 3 блоков аудио')

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
        f"Я вижу ты готов разобрать аудио\n",
        parse_mode='HTML'
    )
    bot.register_next_step_handler(message, stt_func)


def stt_func(message: Message):
    if not message.voice:
        bot.send_message(message.from_user.id, 'Пришли пожалуйста аудио', reply_to_message_id=message.id)
        return

    user_blocks = db.get_user_data(message.from_user.id)["stt_blocks"]
    duration = message.voice.duration

    message_audio_blocks = math.ceil(duration / SECONDS_PER_ONE_BLOCK)
    user_blocks += message_audio_blocks

    if duration >= MAX_SECONDS_FOR_AUDIO:
        bot.send_message(message.from_user.id, 'Пришли аудио короче 30 секунд')
        return

    if user_blocks >= MAX_USER_STT_BLOCKS:
        bot.send_message(message.from_user.id, 'У тебя закончились аудио блоки, ты не сможешь воспользоваться ботом')
        return

    file_id = message.voice.file_id
    file_info = bot.get_file(file_id)
    file = bot.download_file(file_info.file_path)

    status, text = speech_to_text(file)

    if status:
        db.update_row(message.from_user.id, 'stt_blocks', user_blocks)
        db.update_row(message.from_user.id, 'message', text)

        bot.send_message(message.from_user.id, text, reply_to_message_id=message.id)
    else:
        bot.send_message(message.from_user.id, text)


@bot.message_handler(commands=["limits"])
def show_limits(message: Message):
    bot.send_message(message.from_user.id, '<b>Лимиты бота на 1 пользователя</b>\n'
                                           f'На озвучку текста ты можешь потратить всего {MAX_SYMBOLS_PER_USER}\n'
                                           f'На расшифровку аудио у тебя есть всего {MAX_USER_STT_BLOCKS} блоков, '
                                           f'в 1 блоке 15 секунд твоего аудио, '
                                           f'если аудио длится 1 секунду то это все равно 1 блок',
                     parse_mode='HTML')


bot.infinity_polling()
