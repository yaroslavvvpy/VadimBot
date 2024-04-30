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

url = "https://discord.com/api/v10/applications/1224781491003719821/commands"

lesson_json = {
    "name": "урок",
    "type": 1,
    "description": "Начинает или заканчивает урок",
    "options": [
        {
            "name": "опция",
            "description": "Выберите опцию",
            "type": 3,
            "required": True,
            "choices": [
                {
                    "name": "начать",
                    "value": "начать"
                },
                {
                    "name": "закончить",
                    "value": "закончить"
                }
            ]
        }
    ]
}

voice_list_json = {
    'name': 'voice_list',
    'type': 1,
    'description': 'Отправляет список людей в голосовом канале'
}

lessons_json = {
    'name': 'уроки',
    'type': 1,
    'description': 'Отправляет список доступных уроков'
}

commands_json = {
    'name': 'команды',
    'type': 1,
    'description': 'Отправляет список команд бота'
}

split_json = {
    'name': 'деление',
    'type': 1,
    'description': 'Делит на группы'
}

headers = {
    "Authorization": "Bot MTIyNDc4MTQ5MTAwMzcxOTgyMQ.GFFhzd.z6Mgbnfov6NLNyqVStGCjT1qMJE7FI70PV1YHk"
}

r = requests.post(url, headers=headers, json=lesson_json)
r1 = requests.post(url, headers=headers, json=voice_list_json)
r2 = requests.post(url, headers=headers, json=lessons_json)
r3 = requests.post(url, headers=headers, json=split_json)
r4 = requests.post(url, headers=headers, json=commands_json)

TOKEN = 'MTIyNDc4MTQ5MTAwMzcxOTgyMQ.GFFhzd.z6Mgbnfov6NLNyqVStGCjT1qMJE7FI70PV1YHk'
OPENAI_API_KEY = 'sk-proj-DDLZDXLSs1CY24w2VxwUT3BlbkFJkRot6LWVQzJ7B2efrler'

bot1 = commands.Bot(command_prefix='!', intents=discord.Intents.all())
bot = discord.Client(intents=discord.Intents.all())
tree_cls = app_commands.CommandTree(bot)

lessons_start = {}

openai.api_key = OPENAI_API_KEY

db_config = {
    'user': 'root',
    'password': 'root',
    'host': 'localhost',
    'database': 'vadimbot',
    'raise_on_warnings': True
}
conn = mysql.connector.connect(**db_config)
cursor = conn.cursor()


def summarize_text(input_text, max_tokens=1500):
    response = openai.Completion.create(
        engine="gpt-3.5-turbo-instruct",  # Используйте актуальную версию модели
        prompt=f"Суммаризируйте следующий текст коротко и ясно:\n\n{input_text}",
        max_tokens=max_tokens,
        temperature=0.5  # Настройте параметр, чтобы контролировать креативность ответа
    )
    return response.choices[0].text.strip()


async def list_lessons(ctx):
    cursor.execute("SELECT lesson_name FROM lessons")
    lessons = cursor.fetchall()
    if lessons:
        # Создание объекта Embed с заголовком и синим цветом границы
        embed = discord.Embed(title=":bank: **Доступные уроки** :bank:", description="",
                              color=0x3498db)  # Синий цвет границы

        # Нумерация для каждого урока с добавлением смайлика книжки
        for index, lesson in enumerate(lessons, start=1):
            # Декодируем значение из байтов или используем его напрямую
            lesson_name = lesson[0].decode('utf-8') if isinstance(lesson[0], bytearray) else lesson[0]
            # Добавляем нумерацию, имя урока и смайлик книжки в качестве имени поля
            embed.add_field(name=f"📚{index}. **{lesson_name[0:-4]}** ", value=f"/выслать урок#{index}",
                            inline=False)

        await ctx.response.send_message(embed=embed)
    else:
        await ctx.response.send_message("Уроки не найдены.")


async def send_lesson(ctx, lesson_index):
    lesson_index1 = lesson_index[(lesson_index.index("#") + 1):]
    print(lesson_index1)
    cursor.execute("SELECT extracted_text FROM audio_texts WHERE id = %s", (lesson_index1,))
    text_data = cursor.fetchone()
    if text_data:
        extracted_text = summarize_text(text_data[0])

        # Проверка на длину текста и возможное разбиение на части, если текст слишком длинный
        if len(extracted_text) > 2000:  # Discord ограничивает длину сообщения 2000 символами
            parts = [extracted_text[i:i+2000] for i in range(0, len(extracted_text), 2000)]
            for part in parts:
                await ctx.response.send_message(part)
        else:
            await ctx.response.send_message(extracted_text)
    else:
        await ctx.response.send_message("Урок не найден или текст урока не доступен.")


def speech_recognitor(file):
    recognizer = sr.Recognizer()
    audio_file = file

    try:
        # Подключение к базе данных
        connection = mysql.connector.connect(
            host='localhost',
            database='vadimbot',
            user='root',
            password='root'
        )
        cursor = connection.cursor()

        with sr.AudioFile(audio_file) as source:
            audio_data = recognizer.record(source)
            try:
                text = recognizer.recognize_google(audio_data, language="ru-RU")
                print("Извлеченный текст из аудио:", text)
                # Сохраняем текст в базу данных
                query = "INSERT INTO audio_texts (extracted_text) VALUES (%s)"
                cursor.execute(query, (text,))
                connection.commit()
                print("Текст успешно сохранен в базу данных.")
            except sr.UnknownValueError:
                print("Google Speech Recognition не смог понять аудио")
            except sr.RequestError as e:
                print(f"Не удалось запросить результаты у службы Google Speech Recognition; {e}")

    except Error as e:
        print("Ошибка при подключении к MySQL", e)
    finally:
        if connection.is_connected():
            cursor.close()
            connection.close()
            print("Соединение с MySQL закрыто")


@tree_cls.command(name='уроки')
async def lessons_command(interaction):
    await list_lessons(interaction)


@bot1.command(name='выслать')
async def send_lesson_command(ctx, *, text):
    await send_lesson(ctx, text)


@tree_cls.command(name='команды')
async def commands_list(interaction):
    embed = discord.Embed(title='Команды', color=0xFF5733)
    embed.add_field(name='!запрос', value='Отвечает на любые запросы')
    embed.add_field(name='!генерация', value='Генерирует картинку по запросу')
    embed.add_field(name='!выслать', value='Высылает копспект урока')
    embed.add_field(name='/урок', value='Начинает или заканчивает урок')
    embed.add_field(name='/уроки', value='Отправляет список доступных уроков')
    embed.add_field(name='/деление', value='Делит на группы')
    embed.add_field(name='/voice_list', value='Отправляет список людей в голосовом канале')
    await interaction.response.send_message(embed=embed)


def save_voice_file_to_db(file_path):
    try:
        connection = mysql.connector.connect(
            host='localhost',
            database='vadimbot',
            user='root',
            password='root'
        )
        cursor = connection.cursor()

        with open(file_path, 'rb') as file:
            binary_data = file.read()

        query = "INSERT INTO audio_files (filename, audio_data) VALUES (%s, %s)"
        current_date = datetime.now().strftime("%d.%m.%Y")
        cursor.execute(query, (f"Урок Я.Л - {current_date}.wav", binary_data))
        connection.commit()
        print("Файл успешно сохранен в базе данных.")
    except Error as e:
        print(f"Ошибка при сохранении файла в БД: {e}")
    finally:
        if connection.is_connected():
            cursor.close()
            connection.close()


def save_file2():
    connection = None
    cursor = None
    try:
        # Установка соединения с базой данных
        connection = mysql.connector.connect(
            host='localhost',
            database='vadimbot',
            user='root',
            password='root'
        )
        cursor = connection.cursor()

        # Создание SQL запроса
        query = "INSERT INTO lessons (lesson_name) VALUES (%s)"
        current_date = datetime.now().strftime("%d.%m.%Y")
        lesson_name = f"Урок Я.Л - {current_date}"

        # Выполнение запроса
        cursor.execute(query, (lesson_name,))

        # Фиксация изменений в базе данных
        connection.commit()
        print("Файл успешно сохранен в базе данных.")
    except Error as e:
        print(f"Ошибка при сохранении файла в БД: {e}")
    finally:
        # Закрытие соединения с базой данных
        if connection and connection.is_connected():
            cursor.close()
            connection.close()
            print("Соединение с базой данных закрыто.")


def generate_image(text):
    response = openai.Image.create(
        model="dall-e-3",
        prompt=str(text),
        n=1,
        size="1024x1024"
    )
    image_url = response.data[0].url
    response = requests.get(image_url)
    image_bytes = BytesIO(response.content)
    return image_bytes


def generate_text(prompt, max_tokens=1500):
    # Запрос к GPT API для генерации текста
    response = openai.Completion.create(
        engine="gpt-3.5-turbo-instruct",
        prompt=prompt,
        max_tokens=max_tokens
    )
    return response.choices[0].text.strip()


@bot1.command()
async def генерация(ctx, *, text):
    image_bytes = generate_image(text)
    # Отправляем в чат текст после команды !генерация
    await ctx.channel.send(file=discord.File(fp=image_bytes, filename='image.png'))


@bot1.command()
async def запрос(ctx, *, text):
    # Отправляем в чат текст после команды !запрос
    await ctx.send(generate_text(text))


@tree_cls.command()
async def урок(interaction):
    voice_channel_id = 1224776362238279766  # ID голосового канала

    if interaction.data['options'][0]['value'] == "начать":
        global vc
        if interaction.user.voice:
            voice_channel = interaction.user.voice.channel
            vc = await voice_channel.connect()
            lessons_start[interaction.guild.id] = datetime.now()
            print(f"Урок начат на сервере: {interaction.guild.id}")
            await interaction.response.send_message("Урок начался!")
            audio = pyaudio.PyAudio()
            await record_audio(interaction, audio)
        else:
            await interaction.response.send_message("Вы должны находиться в голосовом канале.")

    elif interaction.data['options'][0]['value'] == "закончить":
        global is_recording
        if is_recording:
            is_recording = False
            if interaction.guild.id in lessons_start:
                lesson_duration = datetime.now() - lessons_start.pop(interaction.guild.id)
                minutes, seconds = divmod(lesson_duration.seconds, 60)
                await interaction.response.send_message(f"Урок закончился! Продолжительность урока: "
                                                        f"{minutes} минут {seconds} секунд.")
                is_recording = False
            else:
                await interaction.response.send_message("Урок не был начат на этом сервере.")
        else:
            await interaction.response.send_message("Запись не ведется.")


is_recording = False
frames = []
vc = None


async def record_audio(ctx, audio):
    global is_recording, frames, vc
    is_recording = True
    frames = []
    FORMAT = pyaudio.paInt16
    CHANNELS = 1
    RATE = 44100
    CHUNK = 1024
    WAVE_OUTPUT_FILENAME = "output.wav"

    stream = audio.open(format=FORMAT, channels=CHANNELS,
                        rate=RATE, input=True,
                        frames_per_buffer=CHUNK)

    while is_recording:
        data = stream.read(CHUNK)
        frames.append(data)
        await asyncio.sleep(0)  # Позволяет другим задачам выполняться

    stream.stop_stream()
    stream.close()
    audio.terminate()

    wf = wave.open(WAVE_OUTPUT_FILENAME, 'wb')
    wf.setnchannels(CHANNELS)
    wf.setsampwidth(audio.get_sample_size(FORMAT))
    wf.setframerate(RATE)
    wf.writeframes(b''.join(frames))
    wf.close()

    if vc:
        await vc.disconnect()
        vc = None
    zvyk = discord.File(WAVE_OUTPUT_FILENAME)
    # Отправка файла в чат не робит
    # await ctx.response.send_message("Аудиозапись сохранена и бот отключен от канала!", file=zvyk)
    speech_recognitor(WAVE_OUTPUT_FILENAME)
    save_voice_file_to_db(WAVE_OUTPUT_FILENAME)
    save_file2()


@tree_cls.command()
async def voice_list(interaction):
    voice_channel_members = []
    for guild in bot.guilds:
        for channel in guild.voice_channels:
            for member in channel.members:
                voice_channel_members.append(member.name)
    if voice_channel_members:
        await interaction.response.send_message("Пользователи в голосовых каналах:\n" +
                                                '\n'.join(voice_channel_members))
    else:
        await interaction.response.send_message("Нет пользователей в голосовых каналах")


# Глобальная переменная для хранения ID сообщения
message_id_for_reactions = None


@tree_cls.command()
async def деление(interaction: discord.Interaction):
    # Отправка начального сообщения
    await interaction.response.send_message("Выберите вашу группу:", ephemeral=False)

    # Получение только что отправленного сообщения
    message = await interaction.original_response()

    # Добавление реакций к сообщению для выбора группы
    await message.add_reaction('1️⃣')
    await message.add_reaction('2️⃣')

    # Сохранение ID сообщения в глобальной переменной или в базе данных
    global message_id_for_reactions
    message_id_for_reactions = message.id

    # Создание слушателя для реакций
    @bot.event
    async def on_reaction_add(reaction, user):
        if reaction.message_id != message_id_for_reactions or user == bot.user:
            return

        group_name = 'Группа 1' if str(reaction.emoji) == '1️⃣' else 'Группа 2'

        # Создание модального окна для ввода имени и фамилии
        modal = discord.ui.Modal(title="Регистрация участника")
        name_input = discord.ui.TextInput(label="Имя", placeholder="Введите ваше имя и фамилию", style=discord.TextStyle.short)

        modal.add_item(name_input)

        async def on_submit(self, interaction: discord.Interaction):
            # Соединение с базой данных
            connection = mysql.connector.connect(host='localhost', database='vadimbot', user='root',
                                                 password='root')
            cursor = connection.cursor()

            # SQL запрос для вставки данных
            query = "INSERT INTO participants (name, group_name) VALUES (%s, %s)"
            values = (self.children[0].value, self.children[1].value, group_name)

            cursor.execute(query, values)
            connection.commit()

            cursor.close()
            connection.close()

            # Отправка подтверждающего сообщения пользователю
            await interaction.followup.send(
                f"Участник {self.children[0].value} {self.children[1].value} успешно зарегистрирован в {group_name}",
                ephemeral=True)

        modal.on_submit = on_submit
        await interaction.response.send_modal(modal)

@bot.event
async def on_raw_reaction_add(payload: discord.RawReactionActionEvent):
    # Проверка, что реакция добавлена к нужному сообщению
    if payload.message_id != message_id_for_reactions:
        return

    # Получение объекта пользователя и сервера
    guild = bot.get_guild(payload.guild_id)
    member = guild.get_member(payload.user_id)

    # Проверка добавленной реакции и назначение роли
    if str(payload.emoji) == '1️⃣':
        role = discord.utils.get(guild.roles, name="1 группа")
        await member.add_roles(role)
        await member.send("Вы добавлены в 1 группу.")
    elif str(payload.emoji) == '2️⃣':
        role = discord.utils.get(guild.roles, name="2 группа")
        await member.add_roles(role)
        await member.send("Вы добавлены в 2 группу.")

bot.run(TOKEN)
