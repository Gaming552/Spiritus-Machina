import os
from dotenv import load_dotenv
import asyncio
import json

import discord
from discord.ext import commands
from discord.ext.commands import has_permissions, MissingPermissions
from discord.utils import get
from discord.ui import Button, View

from typing import Optional

load_dotenv()

intents = discord.Intents.default()
intents.message_content = True
intents.members = True
intents.reactions = True
intents.voice_states = True

bot = commands.Bot(intents=intents, command_prefix='!')

bot.global_config = []


def load_config():
    with open("config.json", "r") as f:
        bot.global_config = json.load(f)

#
# parameters ctx = commands.Context
# action = str: load|unload|reload
# name = str name of the extension e.g level or reactions (without .py extension)
#
async def handleExtension(action, name):
    bot_channel : discord.TextChannel = bot.get_channel(bot.global_config['bot_channel'])

    try:
        match action:
            case "load":
                await bot.load_extension(f'cogs.{name}')
                await bot_channel.send(f"extension **{name}** loaded successfully")
                return True
            case "unload":
                await bot.unload_extension(f'cogs.{name}')
                await bot_channel.send(f"extension **{name}** unloaded successfully")
                return True
            case "reload":
                await bot.reload_extension(f'cogs.{name}')
                await bot_channel.send(f"extension **{name}** reloaded successfully")
                return True
    except commands.ExtensionAlreadyLoaded:
        await bot_channel.send(f"**{name}** extension is already loaded")
    except commands.ExtensionNotFound:
        await bot_channel.send(f"extension **{name}** not found or not loaded")
    except:
        if action == 'unload':
            await bot_channel.send(f"extension **{name}** not found or not loaded")    
        else:
            await bot_channel.send(f"Unexpected error with **{action} {name}** command")
    
    return False
        
@bot.event
async def on_ready():
    # On ready, print some details to standard out
    print(f"-----\nLogged in as: {bot.user.name} : {bot.user.id}\n-----\nMy current prefix is: {bot.command_prefix}\n-----")

@bot.command(name="reload")
@commands.has_permissions(administrator=True)
async def reload(ctx):
    bot_channel : discord.TextChannel = bot.get_channel(bot.global_config['bot_channel'])
    if ctx.channel.id == bot_channel.id:
        load_config()
        await bot_channel.send("config reloaded successfully")

@bot.command(name="extension")
@commands.has_permissions(administrator=True)
async def extension(ctx: commands.Context, action: str = None, name: str = None):
    bot_channel : discord.TextChannel = bot.get_channel(bot.global_config['bot_channel'])
    
    if ctx.channel.id == bot_channel.id:
        if action is None or name is None:
            await bot_channel.send("Error: Synthax error e.g **!load_extension load|unload|reload extension_name**")
            return
        handle = await handleExtension(action, name)

async def load_extensions():
    #to load the cogs from ./cogs folder
    for filename in os.listdir('./cogs'):
        if filename.endswith('.py'):
            await bot.load_extension(f'cogs.{filename[:-3]}')

async def main():
    load_config()
    await load_extensions()
    await bot.start(os.getenv('TOKEN'))

asyncio.run(main())
