import discord
import json
from easy_pil import Editor, load_image_async, Font

from discord import File
from discord.ext import commands
from typing import Optional

class Levelsys(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_ready(self):
        print("Levelsys Cog Ready!")

    @commands.Cog.listener()
    async def on_message(self, message):
        if not message.author.bot:
            for k,v in enumerate(message.author.roles):
                if self.bot.global_config['no_xp_role'] == v.id:
                    return
            
            with open('levels.json', 'r') as f:
                data = json.load(f)

            if str(message.author.id) in data:

                xp = data[str(message.author.id)]['xp']
                lvl = data[str(message.author.id)]['level']

                lvl_difficulty = self.bot.global_config['lvl_difficulty']

                if lvl == self.bot.global_config['lvl_max']: return

                strlen = len(message.content.replace(' ', ''))
                gain = 0
                match strlen:
                    case strlen if strlen >= 50: gain=25
                    case strlen if 25 <= strlen < 50: gain=12
                    case strlen if 12 <= strlen < 25: gain=6
                    case strlen if 6 <= strlen < 12: gain=3
                    case strlen if strlen < 6: gain=1


                increased_xp = xp+(gain/lvl_difficulty)
                new_level = increased_xp/100

                data[str(message.author.id)]['xp']=increased_xp

                with open("levels.json", "w") as f:
                    json.dump(data, f)
                
                if new_level > lvl:
                    next_level_xp = (lvl+1) * 100
                    xp_remaining = increased_xp-next_level_xp
                    lvl += 1
                    await message.channel.send(f"{message.author.mention} est maintenant niveau {lvl}!!!")

                    data[str(message.author.id)]['level']=lvl

                    if lvl == self.bot.global_config['lvl_max']:
                        data[str(message.author.id)]['xp']=0
                    else:
                        data[str(message.author.id)]['xp']=abs(xp_remaining)

                    with open("levels.json", "w") as f:
                        json.dump(data, f)
            else:
                data[str(message.author.id)] = {}
                data[str(message.author.id)]['xp'] = 0
                data[str(message.author.id)]['level'] = 1
                data[str(message.author.id)]['elo'] = 1000
                data[str(message.author.id)]['wins'] = 0
                data[str(message.author.id)]['loses'] = 0

                with open("levels.json", "w") as f:
                    json.dump(data, f)

    @commands.command(name="rank")
    async def rank(self, ctx: commands.Context, user: Optional[discord.Member]):
        member = user or ctx.author
        asset = member.display_avatar.replace(size=128)
        
        with open("levels.json", "r") as f:
            data = json.load(f)

        xp = int(data[str(member.id)]["xp"])
        lvl = data[str(member.id)]["level"]
        elo = data[str(member.id)]["elo"]
        wins = data[str(member.id)]["wins"]
        loses = data[str(member.id)]["loses"]

        if wins > 0 and loses > 0: kd_ratio = round(wins/loses,2)
        elif loses == 0 and wins > 0: kd_ratio = wins
        else : kd_ratio = 0

        next_level_xp = (lvl+1) * 100
        xp_need = next_level_xp
        xp_have = data[str(member.id)]["xp"]

        percentage = int(((xp_have * 100)/ xp_need))

        if percentage < 1:
            percentage = 0

        role_color = '#f0bc46' 
        bar_color = '#f0bc46' 
        role_name= ''

        ## Rank card
        bg_img = "rankCard.png"

        #if lvl >= self.bot.global_config['lvl_max']: 
        #    with open('legions.json', 'r') as f:
        #            data = json.load(f)
        #    for k,v in enumerate(data):
        #        role = ctx.guild.get_role(v['id'])
        #        for i,j in enumerate(member.roles):
        #            if role.id == j.id:
        #                bar_color=v['bar_color']
        #                bg_img=f"./Legions/{v['background']}"
        #                break

        background = Editor(bg_img)
        profile = await load_image_async(str(asset))

        profile = Editor(profile).resize((150, 150)).circle_image()
        
        poppins = Font().poppins(size=40)
        poppins_small = Font().poppins(size=30)
        background.paste(profile.image, (30, 30))
        
        background.rectangle((30, 220), width=650, height=40, fill="#fff", radius=20)
        background.bar(
            (30, 220),
            max_width=650,
            height=40,
            percentage=percentage,
            fill=bar_color,
            radius=20,
        )
        background.text((200, 8), str(role_name), font=poppins_small, color=str(role_color))
        background.text((200, 40), str(member.display_name), font=poppins, color="#fff")

        background.rectangle((200, 100), width=350, height=2, fill="#fff")
        background.text(
            (200, 130),
            f"Level : {lvl}   "
            + f" XP : {xp} / {(lvl+1) * 100}   "
            + f"ELO : {elo}"
            + f"\nVictoires : {wins}   "
            + f"DĂŠfaites : {loses}   "
            + f"K/D : {kd_ratio}",
            font=poppins_small,
            color="#fff",
        )

        card = File(fp=background.image_bytes, filename="zCARD.png")
        await ctx.send(file=card)


async def setup(client):
  await client.add_cog(Levelsys(client))
