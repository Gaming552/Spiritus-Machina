import discord
from discord.ext import commands
from discord.utils import get
from discord import File
import json

# parameters :
# self : discord's @commands.Cog.listener() variable
# payload : variable of the on_raw_reaction_add|remove discord event
# bool : True for add role, False for remove role
async def handleReactions(self, payload, bool):
    guild = await self.bot.fetch_guild(payload.guild_id)
    member = await guild.fetch_member(payload.user_id)

    with open("reactions.json", "r") as f:
        data = json.load(f)
    
    for k,v in enumerate(data):
        if payload.message_id == v['msg_id']:

            if bool == 1 and v['multiple'] == 0 :
                channel = await self.bot.fetch_channel(payload.channel_id)
                message = await channel.fetch_message(payload.message_id)

                for r in message.reactions:

                    if payload.emoji.is_custom_emoji():
                        payload_emoji = str(payload.emoji).lower()
                    else:
                        payload_emoji = str(payload.emoji)

                    if r.is_custom_emoji():
                        r_emoji = str(r).lower()
                    else:
                        r_emoji = str(r)

                    # checks the reactant isn't a bot and the emoji isn't the one they just reacted with
                    #if payload.member in await r.users().flatten() and not payload.member.bot and str(r) != str(payload.emoji):
                    if r_emoji != payload_emoji:
                        # removes the reaction
                        await message.remove_reaction(r.emoji, payload.member)

            for i,j in enumerate(v['reactions']):
                if(payload.emoji.id == None):
                    #native emoji
                    msg_emoji = 'U+{:X}'.format(ord(payload.emoji.name))
                    emoji = j['emoji']
                else:
                    #custom emoji
                    msg_emoji = payload.emoji.name.lower()
                    emoji = j['emoji'].lower()  
                
                if msg_emoji == emoji:
                    for a, b in enumerate(j['role']):
                        role = get(guild.roles, id=b)
                        if bool == 1:
                            await member.add_roles(role)
                        if bool == 0:
                            await member.remove_roles(role)

class Buttons(discord.ui.View):
    def __init__(self, member_role,role_channel, timeout = None):
        self.member_role = member_role
        self.role_channel = role_channel
        super().__init__(timeout=timeout)

    @discord.ui.button(label="J'accepte le rĂ¨glement",style=discord.ButtonStyle.green)
    async def green_button(self,interaction: discord.Interaction, button: discord.Button):
        role_channel = discord.utils.get(interaction.guild.channels, id=self.role_channel)
        role = discord.utils.get(interaction.guild.roles, id=self.member_role)

        if role not in interaction.user.roles:
            await interaction.user.add_roles(role)
            await interaction.response.send_message(f"Merci d'avoir acceptĂŠ le rĂ¨glement\nN'hĂŠsite pas Ă  aller choisir ta faction dans {role_channel.mention}", ephemeral = True)
        else: await interaction.response.send_message(f"Tu as dĂŠjĂ  acceptĂŠ le rĂ¨glement", ephemeral = True)

async def verify(self):
    codex_channel = self.bot.get_channel(self.bot.global_config['codex_channel'])

    await codex_channel.purge(limit=1,check=lambda message: message.author.bot)
    await codex_channel.send('',view=Buttons(member_role=self.bot.global_config['member_role'],role_channel=self.bot.global_config['role_channel']))
    

class Reactions(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_ready(self):
        await verify(self)
        print("Reactions Cog Ready!")

    @commands.Cog.listener()
    async def on_member_join(self, member):
        moderators_role = member.guild.get_role(self.bot.global_config['moderators_role'])
        codex_channel: discord.TextChannel = self.bot.get_channel(self.bot.global_config['codex_channel'])        
        welcome_channel: discord.TextChannel = self.bot.get_channel(self.bot.global_config['welcome_channel'])
        
        with open('messages.json', 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        welcome_msg = data['welcome_msg']
        welcome_msg = welcome_msg.replace('{codex_channel}', codex_channel.mention)
        welcome_msg = welcome_msg.replace('{member}', member.mention)
        welcome_msg = welcome_msg.replace('{moderators_role}', moderators_role.name)

        await welcome_channel.send(content=welcome_msg)
    
    @commands.Cog.listener()
    async def on_raw_reaction_add(self, payload):
        role_channel : discord.TextChannel = self.bot.get_channel(self.bot.global_config['role_channel'])

        channel = await self.bot.fetch_channel(payload.channel_id)
        message = await channel.fetch_message(payload.message_id)

        if payload.message_id in self.bot.global_config['no_reaction_msgs']:
            await message.clear_reactions() 
            return

        if payload.channel_id == role_channel.id:
            await handleReactions(self, payload, True)

    @commands.Cog.listener()
    async def on_raw_reaction_remove(self, payload):
        role_channel : discord.TextChannel = self.bot.get_channel(self.bot.global_config['role_channel'])
        if payload.channel_id == role_channel.id:
            await handleReactions(self, payload, False)
    
    @commands.command(name="verify")
    @commands.has_permissions(administrator=True)
    async def call_verify(self, ctx):
        bot_channel : discord.TextChannel = self.bot.get_channel(self.bot.global_config['bot_channel'])
        if ctx.channel.id == bot_channel.id:
            await verify(self)

async def setup(client):
  await client.add_cog(Reactions(client))
