import discord
from discord.ext import commands
from datetime import datetime
import pyaudio
import wave
import asyncio
import openai
from io import BytesIO
import requests

intents = discord.Intents.default()
intents.members = True
intents.message_content = True
intents.voice_states = True

# Убедитесь, что вы используете ваш собственный токен
TOKEN = 'MTIyNDc3MTczMjM0MzM2MTYwNg.GKBU6l.eJbzt301wcgP08tbxSBbxUzM3NPJZGumZYkjhc'
OPENAI_API_KEY = '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'
bot = commands.Bot(command_prefix='!', intents=intents)

lessons_start = {}


openai.api_key = OPENAI_API_KEY
def generate_image(text):
    response = openai.Image.create(
        model="dall-e-3",  # Укажите модель, способную генерировать изображения (например, DALL·E)
        prompt=str(text),
        n=1,  # Количество изображений для генерации
        size="1024x1024"  # Размер изображения
    )
    image_url = response.data[0].url
    response = requests.get(image_url)
    image_bytes = BytesIO(response.content)
    return image_bytes

def generate_text(prompt, max_tokens=1000):
    # Запрос к GPT API для генерации текста
    response = openai.Completion.create(
      engine="gpt-3.5-turbo-instruct",  # Выбор модели GPT (можно выбрать другую, если нужно)
      prompt=prompt,               # Ваш запрос
      max_tokens=max_tokens       # Максимальное количество токенов для генерации
    )
    return response.choices[0].text.strip()

@bot.command()
async def генерация(ctx, *, text):
    image_bytes = generate_image(text)
    # Отправляем в чат текст после команды !запрос
    await ctx.channel.send(file=discord.File(fp=image_bytes, filename='image.png'))

# Обработчик команды запроса
@bot.command()
async def запрос(ctx, *, text):
    # Отправляем в чат текст после команды !запрос
    await ctx.send(generate_text(text))

@bot.command()
async def урок(ctx, action: str):
    voice_channel_id = 1224776362238279766  # ID голосового канала
    print(f"Получена команда: {action}")  # Для отладки

    if action == "начать":
        global vc
        if ctx.author.voice:
            voice_channel = ctx.author.voice.channel
            vc = await voice_channel.connect()
            lessons_start[ctx.guild.id] = datetime.now()
            print(f"Урок начат на сервере: {ctx.guild.id}")
            await ctx.send("Урок начался!")
            audio = pyaudio.PyAudio()
            await record_audio(ctx, audio)
        else:
            await ctx.send("Вы должны находиться в голосовом канале.")

    elif action == "закончить":
        global is_recording
        if is_recording:
            is_recording = False
            await ctx.send("Останавливаю запись...")
            if ctx.guild.id in lessons_start:
                lesson_duration = datetime.now() - lessons_start.pop(ctx.guild.id)
                minutes, seconds = divmod(lesson_duration.seconds, 60)
                await ctx.send(f"Урок закончился! Продолжительность урока: {minutes} минут {seconds} секунд.")
            else:
                await ctx.send("Урок не был начат на этом сервере.")
        else:
            await ctx.send("Запись не ведется.")


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

    # Отправка файла в чат
    await ctx.send("Аудиозапись сохранена и бот отключен от канала!", file=discord.File(WAVE_OUTPUT_FILENAME))


@bot.command()
async def voice_list(ctx):
    voice_channel_members = []
    for guild in bot.guilds:
        for channel in guild.voice_channels:
            for member in channel.members:
                voice_channel_members.append(member.name)
    if voice_channel_members:
        await ctx.send("Пользователи в голосовых каналах:")
        await ctx.send("\n".join(voice_channel_members))
    else:
        await ctx.send("Нет пользователей в голосовых каналах")


bot.run(TOKEN)
