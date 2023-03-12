from discord import File
from discord.ext import commands

class Voice(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
    
    @commands.Cog.listener()
    async def on_ready(self):
        print("Voice Cog Ready!")

    @commands.Cog.listener()
    async def on_voice_state_update(self, member, before, after):
        
        if (after.channel is not None and after.channel.category_id == self.bot.global_config['hub_category']):
            if (after.channel.id == self.bot.global_config['voice_channel']):
                guild = await self.bot.fetch_guild(self.bot.global_config['guild_id'])
                category = after.channel.category
                new_voice_channel = await guild.create_voice_channel(name=member.name, position=1, category=category)
                await member.move_to(new_voice_channel)

        if (before.channel is not None):
            if (before.channel.id != self.bot.global_config['voice_channel'] and before.channel.category_id == self.bot.global_config['hub_category']):
                if not before.channel.members: await before.channel.delete()

async def setup(client):
  await client.add_cog(Voice(client))
