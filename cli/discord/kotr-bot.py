#!/usr/bin/env python3
"""KOTR project Discord bot. Separate identity/token from Gir.
Coordinates KOTR build/debug across desktop+laptop and can talk to the Gir bot."""
import os, socket, discord
from discord.ext import commands

TOKEN = os.environ.get("KOTR_BOT_TOKEN")
if not TOKEN:
    raise SystemExit("Set KOTR_BOT_TOKEN in cli/discord/.env (see .env.example)")

HOST = socket.gethostname()
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)

@bot.event
async def on_ready():
    print(f"KOTR bot online as {bot.user} on {HOST}")
    for g in bot.guilds:
        for ch in g.text_channels:
            if ch.name in ("machine-bridge", "kotr"):
                await ch.send(f"KOTR bot online on **{HOST}**.")
                return

@bot.command()
async def status(ctx):
    await ctx.send(f"KOTR bot up on {HOST}. Ready for build/debug commands.")

@bot.command()
async def ping(ctx):
    await ctx.send("pong")

@bot.event
async def on_message(msg):
    if msg.author == bot.user:
        return
    # cross-bot: acknowledge the Gir bot so the two backends can coordinate
    if msg.author.bot and "gir" in str(msg.author).lower():
        if "kotr" in msg.content.lower():
            await msg.channel.send("KOTR bot ack: picking up KOTR task.")
    await bot.process_commands(msg)

bot.run(TOKEN)
