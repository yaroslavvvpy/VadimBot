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
import os
from tempfile import NamedTemporaryFile

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

headers = {
    "Authorization": "Bot MTIyNDc4MTQ5MTAwMzcxOTgyMQ.GOfPsh.bwNudIhk7WZuZJ4AZorOqXLK5sP1N-8l_4uEtM"
}


r = requests.post(url, headers=headers, json=lesson_json)
r2 = requests.post(url, headers=headers, json=voice_list_json)
r3 = requests.post(url, headers=headers, json=lessons_json)
r4 = requests.post(url, headers=headers, json=commands_json)

TOKEN = 'MTIyNDc4MTQ5MTAwMzcxOTgyMQ.GOfPsh.bwNudIhk7WZuZJ4AZorOqXLK5sP1N-8l_4uEtM'
OPENAI_API_KEY = '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'

bot1 = commands.Bot(command_prefix='!', intents=discord.Intents.all())
bot = discord.Client(intents=discord.Intents.all())
tree_cls = app_commands.CommandTree(bot)

lessons_start = {}

openai.api_key = OPENAI_API_KEY

db_config = {
    'user': 'Nikita',
    'password': 'Drimak1981',
    'host': 'localhost',
    'database': 'discord',
    'raise_on_warnings': True
}
conn = mysql.connector.connect(**db_config)
cursor = conn.cursor()


async def list_lessons(ctx):
    cursor.execute("SELECT file_name FROM voice_files")
    lessons = cursor.fetchall()
    if lessons:
        lessons_list = '\n'.join(
            [lesson[0].decode('utf-8') if isinstance(lesson[0], bytearray) else lesson[0] for lesson in lessons])
        await ctx.response.send_message(f"Доступные уроки:\n{lessons_list}")
    else:
        await ctx.response.send_message("Уроки не найдены.")


async def send_lesson(ctx, lesson_name):
    cursor.execute("SELECT voice_data FROM voice_files WHERE file_name = %s", (lesson_name,))
    file_data = cursor.fetchone()
    if file_data:
        # Создаем временный файл для хранения бинарных данных
        with NamedTemporaryFile(delete=False) as tmp:
            tmp.write(file_data[0])
            tmp.seek(0)  # Перемещаем указатель в начало файла, чтобы его можно было прочитать для отправки

            # Отправляем файл в Discord
            await ctx.response.send_message(file=discord.File(tmp.name, filename=lesson_name))

            # удаление переменного файла
            os.unlink(tmp.name)
    else:
        await ctx.response.send_message("Урок не найден.")


@tree_cls.command(name='уроки')
async def lessons_command(interaction):
    await list_lessons(interaction)


@bot1.command(name='выслать')
async def send_lesson_command(ctx, *, text):
    await send_lesson(ctx, text)


@tree_cls.command(name='команды')
async def commands_list(interaction):
    embed = discord.Embed(title='Команды')
    embed.add_field(name='!запрос', value='Отвечает на любые запросы')
    embed.add_field(name='!генерация', value='Генерирует картинку по запросу')
    embed.add_field(name='!выслать', value='Высылает копспект урока')
    embed.add_field(name='/урок', value='Начинает или заканчивает урок')
    embed.add_field(name='/уроки', value='Отправляет список доступных уроков')
    embed.add_field(name='/voice_list', value='Отправляет список людей в голосовом канале')
    await interaction.response.send_message(embed=embed)

def save_voice_file_to_db(file_path):
    try:
        connection = mysql.connector.connect(
            host='localhost',
            database='Discord',
            user='Nikita',
            password='Drimak1981'
        )
        cursor = connection.cursor()

        with open(file_path, 'rb') as file:
            binary_data = file.read()

        query = "INSERT INTO voice_files (file_name, voice_data) VALUES (%s, %s)"
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


def generate_text(prompt, max_tokens=1000):
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

    save_voice_file_to_db(WAVE_OUTPUT_FILENAME)

    if vc:
        await vc.disconnect()
        vc = None
    zvyk = discord.File(WAVE_OUTPUT_FILENAME)
    # Отправка файла в чат не робит
    # await ctx.response.send_message("Аудиозапись сохранена и бот отключен от канала!", file=zvyk)


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


bot.run(TOKEN)
