import discord
from discord.ext import commands
from datetime import datetime
import pyaudio
import wave
import asyncio

intents = discord.Intents.default()
intents.members = True
intents.message_content = True
intents.voice_states = True

# Убедитесь, что вы используете ваш собственный токен
TOKEN = 'MTIyNDc3MTczMjM0MzM2MTYwNg.GKBU6l.eJbzt301wcgP08tbxSBbxUzM3NPJZGumZYkjhc'

bot = commands.Bot(command_prefix='!', intents=intents)

lessons_start = {}


@bot.command()
async def урок(ctx, action: str):
    voice_channel_id = 1224776362238279766  # Пример ID голосового канала, используйте свой
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
