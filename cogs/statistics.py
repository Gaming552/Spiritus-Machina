import discord
from discord.ext import commands, tasks
from discord.utils import get
import os
import requests
import unicodedata

def convert_to_MATHEMATICAL_BOLD(string):
    msg= ''

    numbers = {
        "0": "zero",
        "1": "one",
        "2": "two",
        "3": "three",
        "4": "four",
        "5": "five",
        "6": "six",
        "7": "seven",
        "8": "eight",
        "9": "nine",
    }

    for char in string:
        category = unicodedata.category(char)
        if category in ("Ll"): 
            msg += unicodedata.lookup(f"MATHEMATICAL BOLD SMALL {char}")
        elif category in ("Lu"): 
            msg += unicodedata.lookup(f"MATHEMATICAL BOLD CAPITAL {char}")
        elif char.isdigit(): 
            msg += unicodedata.lookup(f"MATHEMATICAL BOLD DIGIT {numbers.get(char)}")
        else: 
            msg += char

    return msg

class Statistics(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_ready(self):
        print("Statistics Cog Ready!")
        self.update_statistics.start()

    async def cog_load(self):
        self.update_statistics.start()

    async def cog_unload(self):
        self.update_statistics.stop()

    @tasks.loop(hours=12)
    async def update_statistics(self):
        guild = self.bot.get_guild(self.bot.global_config['guild_id'])

        members_stat_channel = self.bot.get_channel(self.bot.global_config['members_stat_channel'])
        youtube_stat_channel = self.bot.get_channel(self.bot.global_config['youtube_stat_channel'])
        twitter_stat_channel = self.bot.get_channel(self.bot.global_config['twitter_stat_channel'])

        member_count = guild.member_count

        string = f"Discord : {member_count}"
        msg = convert_to_MATHEMATICAL_BOLD(string)

        await members_stat_channel.edit(name=msg)

        YT_API_KEY = os.getenv('YT_API_KEY')
        YT_CHANNEL_ID = self.bot.global_config['YT_CHANNEL_ID']

        channel = f"https://www.googleapis.com/youtube/v3/channels?part=statistics&id={YT_CHANNEL_ID}&key={YT_API_KEY}"
        response = requests.get(channel)
        
        if response.status_code == 200:
            response = response.json()
            subscriber_count = int(response["items"][0]["statistics"]["subscriberCount"])
            
            string = f"Youtube : {subscriber_count}"
            msg = convert_to_MATHEMATICAL_BOLD(string)

            await youtube_stat_channel.edit(name=msg)

        TWITTER_BEARER_TOKEN = os.getenv('TWITTER_BEARER_TOKEN')
        TWITTER_ID = self.bot.global_config['TWITTER_ID']

        url = f"https://api.twitter.com/2/users?ids={TWITTER_ID}&user.fields=public_metrics"
        headers = {
            "Authorization": f"Bearer {TWITTER_BEARER_TOKEN}",
        }

        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            data = response.json()
            follower_count = data["data"][0]["public_metrics"]["followers_count"]

            string = f"Twitter : {follower_count}"
            msg = convert_to_MATHEMATICAL_BOLD(string)

            await twitter_stat_channel.edit(name=msg)


async def setup(client):
  await client.add_cog(Statistics(client))
