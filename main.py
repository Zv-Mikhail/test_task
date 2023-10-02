import os
import sqlite3
import telebot
from telebot.types import KeyboardButton, ReplyKeyboardMarkup
import pandas as pd
import requests

bot = telebot.TeleBot('6408229202:AAFMcIoLA5JlDD0aMRuulCKNi41v1B9UWt4')


conn = sqlite3.connect('parsing.db')
cursor = conn.cursor()
# Проверяем существование таблицы data_cup
cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='data_cup'")
table_exists = cursor.fetchone()

if not table_exists:
    cursor.execute('''CREATE TABLE data_cup
                      (link TEXT, color TEXT, price INTEGER)''')
    conn.commit()

def format_print(name_f):
    df = pd.read_excel(f"{name_f}")
    # Вывести таблицу в формате xlsx
    conn = sqlite3.connect('parsing.db')
    cursor = conn.cursor()

    strok = "Сайт:                        |Цвет:               |Цена: \n"
    # 14 18 3
    for index, row in df.iterrows():
        row_values = [str(value) for value in row.values]
        link = row_values[0]
        color = row_values[1]
        price = int(row_values[2])
        # Проверка наличия данных
        cursor.execute('SELECT * FROM data_cup WHERE link = ? AND color = ? AND price = ?', (link, color, price))
        existing_data = cursor.fetchall()
        if not existing_data:
            cursor.execute('INSERT INTO data_cup (link, color, price) VALUES (?, ?, ?)', (link, color, price))

        strok += (' |'.join(row_values)) + "\n"
        # strok += f'{link} {" "*(14-len(link))} {color} {price} \n'

    conn.commit()
    conn.close()

    return strok

def print_max(name_f):
    a ="Средняя цена за кружку на сайте:\n"
    df = pd.read_excel(f"{name_f}")
    avg_prices = df.groupby('Сайт')['Цена'].mean().reset_index()
    for index, row in avg_prices.iterrows():
        a += f"{row['Сайт']} составляет: {int(row['Цена'])} \n"

    return a
@bot.message_handler(commands=['start'])
def start(message):
    button = KeyboardButton('Загрузить файл 📎')
    markup = ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add(button)
    bot.send_message(message.chat.id, f'Привет {message.from_user.first_name}! \nНажми на кнопку "Загрузить файл 📎".', reply_markup=markup)


@bot.message_handler(func=lambda message: message.text == 'Загрузить файл 📎')
def attach_file(message):
    bot.send_message(message.chat.id, 'Чтобы прикрепить файл, нажмите на 📎 -> Файл, и выберите необходимый.')

# Функция для обработки сообщения с документом
@bot.message_handler(regexp=r'https?://[^\s]+')
def handle_link(message):
    url = message.text
    response = requests.get(url)

    with open('file2.xlsx', 'wb') as file:
        file.write(response.content)
    name_ff = 'file2.xlsx'

    try:
        bot.send_message(message.chat.id, format_print(name_ff))
        bot.send_message(message.chat.id, print_max(name_ff))
    except Exception as e:
        bot.reply_to(message, "Похоже ваш файл не удовлетворяет условию")
        os.remove(f"{name_ff}")
@bot.message_handler(content_types=['document'])
def handle_document(message):
    # Получаем информацию о файле
    file_info = bot.get_file(message.document.file_id)
    # Скачиваем файл
    downloaded_file = bot.download_file(file_info.file_path)
    # Сохраняем файл на диск
    with open(message.document.file_name, 'wb') as file:
        file.write(downloaded_file)
    name_file = message.document.file_name
    try:

        bot.send_message(message.chat.id, format_print(name_file))
        bot.send_message(message.chat.id, print_max(name_file))
    except Exception as e:
        bot.reply_to(message, "Похоже ваш файл не удовлетворяет условию")
        os.remove(f"{name_file}")


bot.polling(none_stop=True, interval=0)