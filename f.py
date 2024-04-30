import discord
from discord import app_commands
from discord.ext import commands
from datetime import datetime
import pyaudio
import wave
import asyncio
import openai
from io import BytesIO
import requests
import mysql.connector
from mysql.connector import Error
import speech_recognition as sr


TOKEN = ''
OPENAI_API_KEY = ''

intents = discord.Intents.default()
intents.members = True
intents.message_content = True
intents.voice_states = True

bot1 = commands.Bot(command_prefix='!', intents=intents)

lessons_start = {}

openai.api_key = OPENAI_API_KEY

db_config = {
    'user': 'root',
    'password': 'root',
    'host': 'localhost',
    'database': 'vadimbot1',
    'raise_on_warnings': True
}
conn = mysql.connector.connect(**db_config)
cursor = conn.cursor()


def summarize_text(input_text, max_tokens=1500):
    response = openai.Completion.create(
        engine="gpt-3.5-turbo-instruct",  # Используйте актуальную версию модели
        prompt=f"Сделай конспект текста, убрав лишние слова:\n\n{input_text}",
        max_tokens=max_tokens,
        temperature=0.5  # Настройте параметр, чтобы контролировать креативность ответа
    )
    return response.choices[0].text.strip()


async def list_lessons(ctx):
    cursor.execute("SELECT lesson_name FROM lessons")
    lessons = cursor.fetchall()
    if lessons:
        embed = discord.Embed(title=":bank: **Доступные уроки** :bank:", color=0x3498db)
        for index, lesson in enumerate(lessons, start=1):
            lesson_name = lesson[0].decode('utf-8') if isinstance(lesson[0], bytearray) else lesson[0]
            embed.add_field(name=f"📚{index}. **{lesson_name}**", value=f"Используйте `!выслать урок#{index}` для получения", inline=False)
        await ctx.send(embed=embed)
    else:
        await ctx.send("Уроки не найдены.")


async def send_lesson(ctx, lesson_index):
    lesson_index1 = lesson_index[(lesson_index.index("#") + 1):]
    print(lesson_index1)
    cursor.execute("SELECT extracted_text FROM audio_texts WHERE id = %s", (lesson_index1,))
    text_data = cursor.fetchone()
    if text_data:
        extracted_text = summarize_text(text_data[0])

        # Проверка на длину текста и возможное разбиение на части, если текст слишком длинный
        if len(extracted_text) > 2000:  # Discord ограничивает длину сообщения 2000 символами
            parts = [extracted_text[i:i + 2000] for i in range(0, len(extracted_text), 2000)]
            for part in parts:
                await ctx.send(part)  # Использование ctx.send для отправки сообщения
        else:
            await ctx.send(extracted_text)  # Использование ctx.send для отправки сообщения
    else:
        await ctx.send("Урок не найден или текст урока не доступен.")


# def speech_recognitor(file):
#     recognizer = sr.Recognizer()
#     audio_file = file
#
#     try:
#         # Подключение к базе данных
#         connection = mysql.connector.connect(
#             host='localhost',
#             database='vadimbot1',
#             user='root',
#             password='root'
#         )
#         cursor = connection.cursor()
#
#         with sr.AudioFile(audio_file) as source:
#             audio_data = recognizer.record(source)
#             try:
#                 text = recognizer.recognize_google(audio_data, language="ru-RU")
#                 print("Извлеченный текст из аудио:", text)
#                 # Сохраняем текст в базу данных
#                 query = "INSERT INTO audio_texts (extracted_text) VALUES (%s)"
#                 cursor.execute(query, (text,))
#                 connection.commit()
#                 print("Текст успешно сохранен в базу данных.")
#             except sr.UnknownValueError:
#                 print("Google Speech Recognition не смог понять аудио")
#             except sr.RequestError as e:
#                 print(f"Не удалось запросить результаты у службы Google Speech Recognition; {e}")
#
#     except Error as e:
#         print("Ошибка при подключении к MySQL", e)
#     finally:
#         if connection.is_connected():
#             cursor.close()
#             connection.close()
#             print("Соединение с MySQL закрыто")
#
#
# @bot1.command(name='уроки')
# async def уроки(ctx):
#     if ctx.guild is None:
#         await ctx.send('Бот работает только на сервере "Яндекс Лавка"')
#         return
#
#     if str(ctx.guild.id) != '1028293393245286440':
#         await ctx.send('Бот работает только на сервере "Яндекс Лавка"')
#         return
#     await list_lessons(ctx)
#
#
# @bot1.command(name='выслать')
# async def send_lesson_command(ctx, *, text):
#     if ctx.guild is None:
#         await ctx.send('Бот работает только на сервере "Яндекс Лавка"')
#         return
#
#     if str(ctx.guild.id) != '1028293393245286440':
#         await ctx.send('Бот работает только на сервере "Яндекс Лавка"')
#         return
#     await send_lesson(ctx, text)
#
#
# @bot1.command(name='команды')
# async def commands_list(ctx):
#     if ctx.guild is None:
#         await ctx.send('Бот работает только на сервере "Яндекс Лавка"')
#         return
#
#     if str(ctx.guild.id) != '1028293393245286440':
#         await ctx.send('Бот работает только на сервере "Яндекс Лавка"')
#         return
#     # Создание встроенного сообщения с заголовком и цветом
#     embed = discord.Embed(title='Команды', color=0xFF5733)
#     # Добавление полей
#     embed.add_field(name='!запрос', value='Отвечает на любые запросы', inline=False)
#     embed.add_field(name='!генерация', value='Генерирует картинку по запросу', inline=False)
#     embed.add_field(name='!выслать', value='Высылает конспект урока', inline=False)
#     embed.add_field(name='!урок начать', value='Начинает урок', inline=False)
#     embed.add_field(name='!урок закончить', value='Заканчивает урок', inline=False)
#     embed.add_field(name='!уроки', value='Отправляет список доступных уроков', inline=False)
#     embed.add_field(name='!группа1', value='Лист 1 группы', inline=False)
#     embed.add_field(name='!группа2', value='Лист 2 группы', inline=False)
#     embed.add_field(name='!отсутствующие', value='отправляет список отсутсвующих', inline=False)
#
#     # Отправка встроенного сообщения в канал
#     await ctx.send(embed=embed)
#
#
# def save_voice_file_to_db(file_path):
#     try:
#         connection = mysql.connector.connect(
#             host='localhost',
#             database='vadimbot1',
#             user='root',
#             password='root'
#         )
#         cursor = connection.cursor()
#
#         with open(file_path, 'rb') as file:
#             binary_data = file.read()
#
#         query = "INSERT INTO audio_files (filename, audio_data) VALUES (%s, %s)"
#         current_date = datetime.now().strftime("%d.%m.%Y")
#         cursor.execute(query, (f"Урок Я.Л - {current_date}.wav", binary_data))
#         connection.commit()
#         print("Файл успешно сохранен в базе данных.")
#     except Error as e:
#         print(f"Ошибка при сохранении файла в БД: {e}")
#     finally:
#         if connection.is_connected():
#             cursor.close()
#             connection.close()
#
#
# def save_file2():
#     connection = None
#     cursor = None
#     try:
#         # Установка соединения с базой данных
#         connection = mysql.connector.connect(
#             host='localhost',
#             database='vadimbot1',
#             user='root',
#             password='root'
#         )
#         cursor = connection.cursor()
#
#         # Создание SQL запроса
#         query = "INSERT INTO lessons (lesson_name) VALUES (%s)"
#         current_date = datetime.now().strftime("%d.%m.%Y")
#         lesson_name = f"Урок Я.Л - {current_date}"
#
#         # Выполнение запроса
#         cursor.execute(query, (lesson_name,))
#
#         # Фиксация изменений в базе данных
#         connection.commit()
#         print("Файл успешно сохранен в базе данных.")
#     except Error as e:
#         print(f"Ошибка при сохранении файла в БД: {e}")
#     finally:
#         # Закрытие соединения с базой данных
#         if connection and connection.is_connected():
#             cursor.close()
#             connection.close()
#             print("Соединение с базой данных закрыто.")
#
#
# def generate_image(text):
#     response = openai.Image.create(
#         model="dall-e-3",
#         prompt=str(text),
#         n=1,
#         size="1024x1024"
#     )
#     image_url = response.data[0].url
#     response = requests.get(image_url)
#     image_bytes = BytesIO(response.content)
#     return image_bytes
#
#
# def generate_text(prompt, max_tokens=1500):
#     # Запрос к GPT API для генерации текста
#     response = openai.Completion.create(
#         engine="gpt-3.5-turbo-instruct",
#         prompt=prompt,
#         max_tokens=max_tokens
#     )
#     return response.choices[0].text.strip()
#
#
# @bot1.command()
# async def генерация(ctx, *, text):
#     if ctx.guild is None:
#         await ctx.send('Бот работает только на сервере "Яндекс Лавка"')
#         return
#
#     if str(ctx.guild.id) != '1028293393245286440':
#         await ctx.send('Бот работает только на сервере "Яндекс Лавка"')
#         return
#     image_bytes = generate_image(text)
#     # Отправляем в чат текст после команды !генерация
#     await ctx.channel.send(file=discord.File(fp=image_bytes, filename='image.png'))
#
#
# @bot1.command()
# async def запрос(ctx, *, text):
#     if ctx.guild is None:
#         await ctx.send('Бот работает только на сервере "Яндекс Лавка"')
#         return
#
#     if str(ctx.guild.id) != '1028293393245286440':
#         await ctx.send('Бот работает только на сервере "Яндекс Лавка"')
#         return
#     response_text = generate_text(text)
#     max_length = 2000
#     if len(response_text) <= max_length:
#         await ctx.send(response_text)
#     else:
#         for i in range(0, len(response_text), max_length):
#             await ctx.send(response_text[i:i + max_length])

is_recording = False
frames = []
vc = None


@bot1.command()
async def урок(ctx, *, option: str):
    if ctx.guild is None:
        await ctx.send('Бот работает только на сервере "Яндекс Лавка"')
        return

    if str(ctx.guild.id) != '1028293393245286440':
        await ctx.send('Бот работает только на сервере "Яндекс Лавка"')
        return
    if option == "начать":
        if ctx.author.voice:
            voice_channel = ctx.author.voice.channel
            global vc
            vc = await voice_channel.connect()
            lessons_start[ctx.guild.id] = datetime.now()
            print(f"Урок начат на сервере: {ctx.guild.id}")
            await ctx.send("Урок начался!")
            # Запись аудио, функция record_audio должна быть асинхронной
            audio = pyaudio.PyAudio()
            await record_audio(ctx, audio)
        else:
            await ctx.send("Вы должны находиться в голосовом канале.")

    elif option == "закончить":
        global is_recording
        if is_recording:
            if vc:
                await vc.disconnect()
                vc = None
            is_recording = False
            if ctx.guild.id in lessons_start:
                lesson_duration = datetime.now() - lessons_start.pop(ctx.guild.id)
                minutes, seconds = divmod(lesson_duration.seconds, 60)
                await ctx.send(f"Урок закончился! Продолжительность урока: {minutes} минут {seconds} секунд.")
            else:
                await ctx.send("Урок не был начат на этом сервере.")
        else:
            await ctx.send("Запись не ведется.")




async def record_audio(ctx, audio):
    global is_recording, vc
    is_recording = True
    FORMAT = pyaudio.paInt16
    CHANNELS = 1
    RATE = 44100
    CHUNK = 1024
    WAVE_OUTPUT_FILENAME = "output.wav"

    stream = audio.open(format=FORMAT, channels=CHANNELS,
                        rate=RATE, input=True,
                        frames_per_buffer=CHUNK)
    frames = []

    while is_recording:
        data = stream.read(CHUNK)
        frames.append(data)

    stream.stop_stream()
    stream.close()
    audio.terminate()

    wf = wave.open(WAVE_OUTPUT_FILENAME, 'wb')
    wf.setnchannels(CHANNELS)
    wf.setsampwidth(audio.get_sample_size(FORMAT))
    wf.setframerate(RATE)
    wf.writeframes(b''.join(frames))
    wf.close()


#     zvyk = discord.File(WAVE_OUTPUT_FILENAME)
#     await ctx.speech_recognitor(WAVE_OUTPUT_FILENAME)
#     await ctx.save_voice_file_to_db(WAVE_OUTPUT_FILENAME)
#     await ctx.save_file2()
#     # Отправка файла в чат не робит
#     await ctx.response.send_message("Аудиозапись сохранена и бот отключен от канала!", file=zvyk)
#
#
# @bot1.command()
# async def voice_list(interaction):
#     voice_channel_members = []
#     for guild in bot1.guilds:
#         for channel in guild.voice_channels:
#             for member in channel.members:
#                 voice_channel_members.append(member.name)
#     if voice_channel_members:
#         await interaction.response.send_message("Пользователи в голосовых каналах:\n" +
#                                                 '\n'.join(voice_channel_members))
#     else:
#         await interaction.response.send_message("Нет пользователей в голосовых каналах")
#
#
# # Глобальная переменная для хранения ID сообщения
# message_id_for_reactions = None
#
#
# @bot1.command()
# async def регистрация(ctx):
#     if ctx.guild is None:
#         await ctx.send('Бот работает только на сервере "Яндекс Лавка"')
#         return
#
#     if str(ctx.guild.id) != '1028293393245286440':
#         await ctx.send('Бот работает только на сервере "Яндекс Лавка"')
#         return
#     # Отправка начального сообщения
#     message = await ctx.send("Выберите вашу группу:")
#
#     # Добавление реакций к сообщению для выбора группы
#     await message.add_reaction('1️⃣')
#     await message.add_reaction('2️⃣')
#
#     # Сохранение ID сообщения в глобальной переменной или в базе данных
#     global message_id_for_reactions
#     message_id_for_reactions = message.id
#
# # Создание слушателя для реакций
# @bot1.event
# async def on_reaction_add(reaction, user):
#     if reaction.message.id != message_id_for_reactions or user == bot1.user:
#         return
#
#     # Определение группы на основе эмодзи реакции
#     group_name = 'Группа 1' if str(reaction.emoji) == '1️⃣' else 'Группа 2'
#
#     # Просьба пользователю ввести имя и фамилию в чат
#     def check(m):
#         # Проверяем, что сообщение от того же пользователя и в том же канале
#         return m.author == user and m.channel == reaction.message.channel
#
#     # Ожидаем ввода имени и фамилии пользователя
#     await reaction.message.channel.send(f"{user.mention}, пожалуйста, введите вашу фамилию и имя.")
#     try:
#         response = await bot1.wait_for('message', timeout=60.0, check=check)
#     except asyncio.TimeoutError:
#         await reaction.message.channel.send("Время ожидания истекло, попробуйте ещё раз.")
#         return
#     else:
#         name = response.content
#         # Здесь можно добавить проверку на правильность введенных данных
#         discord_id = str(user.id)
#         await save_to_database(name, group_name, discord_id, user, reaction.message.channel)
#
#
# async def save_to_database(name, group_name, discord_id, user, channel):
#     try:
#         # Соединение с базой данных
#         connection = mysql.connector.connect(host='localhost', database='vadimbot1', user='root', password='root')
#         cursor = connection.cursor()
#
#         # Проверка на существование пользователя в базе данных
#         check_query = "SELECT * FROM participants WHERE name_discord = %s"
#         cursor.execute(check_query, (discord_id,))
#         result = cursor.fetchone()
#
#         if result:
#             await channel.send("Вы уже зарегистрированы")
#         else:
#             # SQL запрос для вставки данных
#             query = "INSERT INTO participants (name, group_name, name_discord) VALUES (%s, %s, %s)"
#             values = (name, group_name, discord_id)
#
#             cursor.execute(query, values)
#             connection.commit()
#
#             await channel.send(f"Участник {name} успешно зарегистрирован в {group_name}.")
#
#     except Exception as e:
#         await channel.send(f"Произошла ошибка при регистрации: {e}")
#     finally:
#         if connection.is_connected():
#             cursor.close()
#             connection.close()
#
#
# @bot1.event
# async def on_raw_reaction_add(payload: discord.RawReactionActionEvent):
#     # Проверка, что реакция добавлена к нужному сообщению
#     if payload.message_id != message_id_for_reactions:
#         return
#
#     # Получение объекта пользователя, сервера и канала
#     guild = bot1.get_guild(payload.guild_id)
#     channel = guild.get_channel(payload.channel_id)  # Получение объекта канала
#     member = guild.get_member(payload.user_id)
#
#     # Проверка добавленной реакции и назначение роли
#     if str(payload.emoji) == '1️⃣':
#         role = discord.utils.get(guild.roles, name="1 группа")
#         if role:
#             await member.add_roles(role)
#             await channel.send(f"{member.mention}, вы добавлены в 1 группу.")
#         else:
#             await channel.send("Роль '1 группа' не найдена.")
#     elif str(payload.emoji) == '2️⃣':
#         role = discord.utils.get(guild.roles, name="2 группа")
#         if role:
#             await member.add_roles(role)
#             await channel.send(f"{member.mention}, вы добавлены в 2 группу.")
#         else:
#             await channel.send("Роль '2 группа' не найдена.")
#
#
# @bot1.command(name='группа1')  # Используем нижнее подчеркивание, так как пробелы не допустимы в именах команд
# async def group_one(ctx):
#     if ctx.guild is None:
#         await ctx.send('Бот работает только на сервере "Яндекс Лавка"')
#         return
#
#     if str(ctx.guild.id) != '1028293393245286440':
#         await ctx.send('Бот работает только на сервере "Яндекс Лавка"')
#         return
#     # Параметры подключения к базе данных
#     db_config = {
#         'user': 'root',
#         'password': 'root',
#         'host': 'localhost',
#         'database': 'vadimbot1'
#     }
#     # Соединение с базой данных
#     try:
#         conn = mysql.connector.connect(**db_config)
#         cursor = conn.cursor()
#
#         # SQL запрос для получения имен участников из первой группы
#         query = "SELECT name FROM participants WHERE group_name = 'Группа 1'"
#         cursor.execute(query)
#
#         # Получение результатов запроса
#         participants = cursor.fetchall()
#         if participants:
#             # Формирование встраиваемого сообщения (embed) со списком участников
#             embed = discord.Embed(title="Участники 1 группы:", color=0xFF5733)
#             for index, participant in enumerate(participants, start=1):
#                 # Получение имени и фамилии участника
#                 full_name = participant[0].split()
#                 first_name = full_name[0].capitalize()
#                 last_name = full_name[1].capitalize() if len(full_name) > 1 else ""
#
#                 # Формирование строки вида "1. И. Фамилия"
#                 display_name = f"{index}. {first_name[0]}. {last_name}"
#                 embed.add_field(name=display_name, value="", inline=False)
#             await ctx.send(embed=embed)
#         else:
#             await ctx.send("Участников в 1 группе нет.")
#     except mysql.connector.Error as e:
#         await ctx.send(f"Ошибка базы данных: {e}")
#     finally:
#         if conn.is_connected():
#             cursor.close()
#             conn.close()
#
#
# @bot1.command(name='группа2')  # Используем нижнее подчеркивание, так как пробелы не допустимы в именах команд
# async def group_one(ctx):
#     if ctx.guild is None:
#         await ctx.send('Бот работает только на сервере "Яндекс Лавка"')
#         return
#
#     if str(ctx.guild.id) != '1028293393245286440':
#         await ctx.send('Бот работает только на сервере "Яндекс Лавка"')
#         return
#     # Параметры подключения к базе данных
#     db_config = {
#         'user': 'root',
#         'password': 'root',
#         'host': 'localhost',
#         'database': 'vadimbot1'
#     }
#     # Соединение с базой данных
#     try:
#         conn = mysql.connector.connect(**db_config)
#         cursor = conn.cursor()
#
#         # SQL запрос для получения имен участников из первой группы
#         query = "SELECT name FROM participants WHERE group_name = 'Группа 2'"
#         cursor.execute(query)
#
#         # Получение результатов запроса
#         participants = cursor.fetchall()
#         if participants:
#             # Формирование встраиваемого сообщения (embed) со списком участников
#             embed = discord.Embed(title="Участники 1 группы:", color=0xFF5733)
#             for index, participant in enumerate(participants, start=1):
#                 # Получение имени и фамилии участника
#                 full_name = participant[0].split()
#                 first_name = full_name[0].capitalize()
#                 last_name = full_name[1].capitalize() if len(full_name) > 1 else ""
#
#                 # Формирование строки вида "1. И. Фамилия"
#                 display_name = f"{index}. {first_name[0]}. {last_name}"
#                 embed.add_field(name=display_name, value="", inline=False)
#             await ctx.send(embed=embed)
#         else:
#             await ctx.send("Участников во 2 группе нет.")
#     except mysql.connector.Error as e:
#         await ctx.send(f"Ошибка базы данных: {e}")
#     finally:
#         if conn.is_connected():
#             cursor.close()
#             conn.close()
#
#
# async def get_missing_users_in_channel(voice_channel):
#     try:
#         # Соединение с базой данных
#         connection = mysql.connector.connect(host='localhost', database='vadimbot1', user='root', password='root')
#         cursor = connection.cursor()
#
#         # Получаем ID всех участников в голосовом канале
#         member_ids = [str(member.id) for member in voice_channel.members]
#
#         # SQL запрос для получения отсутствующих пользователей в голосовом канале
#         query = """
#                 SELECT name, group_name
#                 FROM participants
#                 WHERE name_discord NOT IN ({})
#                 """.format(','.join(['%s']*len(member_ids)))
#         cursor.execute(query, member_ids)
#
#         # Получение результатов запроса
#         missing_users = [(row[0], row[1]) for row in cursor.fetchall()]
#
#         return missing_users
#
#     except Exception as e:
#         print(f"Произошла ошибка при получении отсутствующих пользователей: {e}")
#         return []
#
#     finally:
#         if connection.is_connected():
#             cursor.close()
#             connection.close()
#
#
# @bot1.command()
# async def отсутствующие(ctx):
#     if ctx.guild is None:
#         await ctx.send('Бот работает только на сервере "Яндекс Лавка"')
#         return
#
#     if str(ctx.guild.id) != '1028293393245286440':
#         await ctx.send('Бот работает только на сервере "Яндекс Лавка"')
#         return
#     voice_channel = ctx.author.voice.channel
#     if voice_channel:
#         missing_users = await get_missing_users_in_channel(voice_channel)
#         if missing_users:
#             embed = discord.Embed(title="Отсутствующие пользователи:", color=discord.Color.red())
#             for i, (user, group) in enumerate(missing_users, start=1):
#                 embed.add_field(name=f"{i}. {user}", value=group, inline=False)
#             await ctx.send(embed=embed)
#         else:
#             await ctx.send("Все пользователи из базы данных присутствуют в голосовом канале.")
#     else:
#         await ctx.send("Вы должны находиться в голосовом канале, чтобы использовать эту команду.")
#
bot1.run(TOKEN)
