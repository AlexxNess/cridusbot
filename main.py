import discord
from discord.ext import commands, tasks
import os
import json
import asyncio
import random
import time
import logging

intents = discord.Intents.default()
bot = commands.Bot(command_prefix="!", intents=intents)
STATUS_FILE = "Data/mainfiles/list.txt"
COGS_DIR = "Cogs"
TOKEN_FILE = "secret.txt"

logging.basicConfig(level=logging.INFO)

def read_token():
    try:
        with open(TOKEN_FILE, "r") as f:
            return f.read().strip()
    except FileNotFoundError:
        logging.critical("secret.txt not found. Please create it with your bot token.")
        exit(1)

def ensure_options_json(cog_folder):
    options_path = os.path.join(COGS_DIR, cog_folder, "options.json")
    if not os.path.exists(options_path):
        with open(options_path, "w") as f:
            json.dump({"active": True}, f, indent=4)
        logging.info(f"Created default options.json for {cog_folder}")
    return options_path

def is_cog_active(options_path):
    try:
        with open(options_path, "r") as f:
            options = json.load(f)
        return options.get("active", False), options
    except json.JSONDecodeError:
        logging.error(f"Invalid JSON in {options_path}")
        return False, {}

async def load_cogs():
    print("Checking Cogs directory...\n")
    for folder in os.listdir(COGS_DIR):
        folder_path = os.path.join(COGS_DIR, folder)
        if os.path.isdir(folder_path):
            options_path = ensure_options_json(folder)
            active, options = is_cog_active(options_path)

            cog_path = f"Cogs.{folder}.{folder.lower()}"
            start = time.perf_counter()
            try:
                if active:
                    await bot.load_extension(cog_path)
                    elapsed = time.perf_counter() - start
                    print(f"[+] Loaded {folder} in {elapsed:.2f}s [ACTIVE]")
                else:
                    print(f"[ ] Skipped {folder} [INACTIVE]")
            except Exception as e:
                elapsed = time.perf_counter() - start
                print(f"[!] Failed to load {folder} in {elapsed:.2f}s - Error: {e}")

@tasks.loop(seconds=60)
async def change_status():
    try:
        with open(STATUS_FILE, "r", encoding="utf-8") as f:
            statuses = [line.strip() for line in f if line.strip()]
        if not statuses:
            return
        status = random.choice(statuses)
        if status.startswith("playing "):
            await bot.change_presence(activity=discord.Game(name=status[8:]))
        elif status.startswith("watching "):
            await bot.change_presence(activity=discord.Activity(type=discord.ActivityType.watching, name=status[9:]))
        elif status.startswith("listening "):
            await bot.change_presence(activity=discord.Activity(type=discord.ActivityType.listening, name=status[10:]))
        elif status.startswith("competing "):
            await bot.change_presence(activity=discord.Activity(type=discord.ActivityType.competing, name=status[10:]))
        else:
            await bot.change_presence(activity=discord.Game(name=status))  # default to Game
    except Exception as e:
        logging.error(f"Error changing status: {e}")

@bot.event
async def on_ready():
    print(f"Bot connected as {bot.user}")
    change_status.start()

async def main():
    await load_cogs()
    token = read_token()
    await bot.start(token)

if __name__ == "__main__":
    asyncio.run(main())
