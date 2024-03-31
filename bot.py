from pyrogram.errors import InputUserDeactivated, FloodWait, UserIsBlocked
from pyrogram.enums import ParseMode
from pyrogram import Client, filters
from pyrogram.types import *
import asyncio, datetime, time
import sqlite3


API_ID = int("24294875")
API_HASH = "d1e356bde970f838cadc58fe47ff684b"
BOT_TOKEN = "6889108275:AAGbfgVeGhOA11opce89JaaEgsZO9UmQeYY"
ADMINS = [1952883393, 677265840]

def db_connect(db_name="database.db"):
    conn = sqlite3.connect(db_name, check_same_thread=False)
    return conn

def init_db(conn):
    cursor = conn.cursor()
    cursor.execute('''CREATE TABLE IF NOT EXISTS users
                      (id INTEGER PRIMARY KEY)''')
    conn.commit()

def add_user(conn, user_id):
    cursor = conn.cursor()
    cursor.execute('INSERT OR IGNORE INTO users (id) VALUES (?)', (user_id,))
    conn.commit()

def count_users(conn):
    cursor = conn.cursor()
    cursor.execute('SELECT COUNT(*) FROM users')
    (count,) = cursor.fetchone()
    return count

def remove_user(conn, user_id):
    cursor = conn.cursor()
    cursor.execute('DELETE FROM users WHERE id = ?', (user_id,))
    conn.commit()

def get_all_users(conn):
    cursor = conn.cursor()
    cursor.execute('SELECT id FROM users')
    return [row[0] for row in cursor.fetchall()]

conn = db_connect()
init_db(conn)

Bot = Client(name='AutoAcceptBot', api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)

@Bot.on_message(filters.command(["broadcast", "users"]) & filters.user(ADMINS))
async def broadcast(client, message):
    if message.command[0] == "users":
        total_users = count_users(conn)
        await message.reply(f"Total Users: {total_users}")
    else:
        if message.reply_to_message:
            b_msg = message.reply_to_message
            users = get_all_users(conn)
            total_users = len(users)
            done = 0
            failed = 0
            success = 0
            start_time = time.time()
            for user_id in users:
                try:
                    await b_msg.copy(chat_id=user_id)
                    success += 1
                except FloodWait as e:
                    await asyncio.sleep(e.x)
                    await b_msg.copy(chat_id=user_id)
                    success += 1
                except (InputUserDeactivated, UserIsBlocked):
                    remove_user(conn, user_id)
                    failed += 1
                except Exception as e:
                    failed += 1
                done += 1
                if not done % 20:
                    sts = await message.reply_text(f"Broadcast in progress:\n\nTotal Users {total_users}\nCompleted: {done} / {total_users}\nSuccess: {success}\nFailed: {failed}")
            time_taken = datetime.timedelta(seconds=int(time.time() - start_time))
            await message.reply_text(f"Broadcast Completed:\nCompleted in {time_taken} seconds.\n\nTotal Users {total_users}\nCompleted: {done} / {total_users}\nSuccess: {success}\nFailed: {failed}")

@Bot.on_chat_join_request()
async def req_accept(client, join_request):
    user_id = join_request.from_user.id
    chat_id = join_request.chat.id

    invitation_text = (
        "🎉 Привет, добро пожаловать в <b>Frolov I&R</b>! 🎉\n\n"
        "Мы рады, что ты хочешь присоединиться к нам. Прежде всего, давай подтвердим, что ты - человек. Это поможет нам создать лучшее сообщество для всех.\n\n"
        "Пожалуйста, <b>нажмите на кнопку ниже</b>."
    )

    
    button = InlineKeyboardMarkup([
        [InlineKeyboardButton("👤 Я человек", callback_data=f"confirm_{chat_id}_{user_id}")]
    ])

    try:
        await client.send_message(user_id, invitation_text, reply_markup=button, parse_mode = ParseMode.HTML)
    except Exception as e:
        print(e)


@Bot.on_callback_query()
async def callback_query_handler(client, callback_query):
    data = callback_query.data

    if data.startswith("confirm_"):
        _, chat_id, user_id = data.split("_")
        chat_id = int(chat_id)
        user_id = int(user_id)

        try:
            await client.approve_chat_join_request(chat_id, user_id)
            add_user(conn, user_id)
            welcome_message = (f"{callback_query.from_user.first_name}, добро пожаловать в <a href='https://t.me/+j3Nz5CUB-lQ0OTBk'>FrolovInR</a>!")
            await client.send_message(user_id, welcome_message, parse_mode=ParseMode.HTML)
        except pyrogram.errors.UserAlreadyParticipant:
            print("Пользователь уже является участником чата.")
        except Exception as e:
            print(f"Произошла ошибка: {e}")

        try:
            await callback_query.message.delete()
        except Exception as e:
            print(f"Ошибка при удалении сообщения: {e}")





Bot.run()
