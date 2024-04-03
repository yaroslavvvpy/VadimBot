import discord
from discord.ext import commands
from datetime import datetime

intents = discord.Intents.default()
intents.members = True
intents.message_content = True


TOKEN = 'MTIyNDc3MTczMjM0MzM2MTYwNg.GoyBcY.aM605ZxwwkD2HPVHbcdQz7lashlxvlUCQG2e-Q'

bot = commands.Bot(command_prefix='!', intents=intents)

lessons_start = {}


@bot.command()
async def урок(ctx, action: str):
    voice_channel_id = 1224776362238279766
    print(f"Получена команда: {action}")  # дебаг

    if action == "начать":
        if ctx.guild.id in lessons_start:
            await ctx.send("Урок уже начался!")
            return

        voice_channel = bot.get_channel(voice_channel_id)
        if voice_channel is None:
            await ctx.send("Голосовой канал не найден!")
            return

        try:
            await voice_channel.connect()
            lessons_start[ctx.guild.id] = datetime.now()
            print(f"Урок начат на сервере: {ctx.guild.id}")  # дебаг
            await ctx.send("Урок начался!")
        except Exception as e:
            await ctx.send(f"Не удалось подключиться к голосовому каналу: {e}")

    elif action == "закончить":
        print(f"Попытка завершить урок на сервере: {ctx.guild.id}")  #  для дебага
        if ctx.guild.id not in lessons_start:
            await ctx.send("Урок еще не начинался!")
            return

        lesson_duration = datetime.now() - lessons_start.pop(ctx.guild.id)
        minutes, seconds = divmod(lesson_duration.seconds, 60)

        voice_client = discord.utils.get(bot.voice_clients, guild=ctx.guild)
        if voice_client and voice_client.is_connected():
            await voice_client.disconnect()
            print(f"Урок завершен на сервере: {ctx.guild.id}")  # для дебага
            await ctx.send(f"Урок закончился! Продолжительность урока: {minutes} минут {seconds} секунд.")
        else:
            await ctx.send("Бот не был подключен к голосовому каналу.")


bot.run(TOKEN)
