from discord.ext import commands
from random import *
import json
from typing import List, Tuple

class Commands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
    
    @commands.Cog.listener()
    async def on_ready(self):
        print("Commands Cog Ready!")

    @commands.command(name="config")
    @commands.has_permissions(administrator=True)
    async def config(self, ctx):
        bot_channel = self.bot.get_channel(self.bot.global_config['bot_channel'])
        msg_config = ''
        if ctx.channel.id == bot_channel.id:
            for k,v in enumerate(self.bot.global_config):
                msg_config += f"{v} : {self.bot.global_config[v]}\n"
            
            await bot_channel.send(msg_config)
    
    @commands.command(name="toplvl")
    @commands.has_permissions(administrator=True)
    async def top10_by_level(self, ctx):
        guild = await self.bot.fetch_guild(self.bot.global_config['guild_id'])
        bot_channel = self.bot.get_channel(self.bot.global_config['bot_channel'])
        if ctx.channel.id != bot_channel.id: return

        with open("levels.json", "r") as file:
            data = json.load(file)
            members = [(int(k), v) for k, v in data.items()]
            members.sort(key=lambda x: x[1]["level"], reverse=True)
            top10 = members[:10]
            message = "\n".join([f"{i+1}. {(await guild.fetch_member(k)).display_name} niveau {v['level']}" for i, (k, v) in enumerate(top10)])
            await ctx.send(f"Top 10 des membres : \n{message}")

async def setup(client):
  await client.add_cog(Commands(client))
