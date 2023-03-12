from discord.ext import commands
import random
import os
import openai
import json

def check_permissions(self, ctx):
    allowed_roles = [
        self.bot.global_config['moderator_chief_role'], 
        self.bot.global_config['moderators_role'], 
        self.bot.global_config['Maitre_Archiviste'], 
        self.bot.global_config['Librio_Adeptus']
    ]
    user_roles = [role.id for role in ctx.author.roles]
    if not (set(allowed_roles).intersection(user_roles) or ctx.author.guild_permissions.administrator):
        return False
    else:
        return True

class Citations(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
    
    @commands.Cog.listener()
    async def on_ready(self):
        print("Citations Cog Ready!")

    @commands.command(name="citation_IA")
    async def gpt3_quote(self, ctx): 
        GPT3_API_KEY = os.getenv('GPT3_API_KEY') 

        # Utilisez votre clĂŠ d'API pour initialiser la bibliothĂ¨que
        openai.api_key = GPT3_API_KEY

        # Posez la question Ă  l'API
        response = openai.Completion.create(
            engine="text-davinci-002",
            prompt=(f"Donne moi une citation liĂŠ exclusivement Ă  l'univers de Warhammer 40000"),
            max_tokens=1024,
        )

        # RĂŠcupĂŠrez la rĂŠponse de l'API
        answer = response.choices[0].text

        # Affichez la rĂŠponse
        await ctx.send(f"{answer}")

    @commands.command(name="citation")
    @commands.has_permissions(administrator=True)
    async def quote(self, ctx):
        with open("citations.json", "r") as file:
            try:
                data = json.load(file)
            except json.decoder.JSONDecodeError:
                await ctx.send("Aucune citation disponible")
                return
        if len(data) == 0:
            await ctx.send("Aucune citation disponible")
            return
        citation = random.choice(data)
        await ctx.send(f"{citation}")

    @commands.command(name="citation_add")
    async def quote_add(self, ctx, *, citation: str):
        allowed = check_permissions(self, ctx)

        if allowed == False: 
            await ctx.send("Tu n'as pas les permissions nĂŠcessaires pour utiliser cette commande.")
            return

        try:
            with open("citations.json", "r+") as file:
                try:
                    data = json.load(file)
                except json.decoder.JSONDecodeError:
                    data = []
                data.append(citation)
                file.seek(0)
                json.dump(data, file)
                file.truncate()
        except FileNotFoundError:
            open("citations.json", "w").close()
            data = [citation]
            with open("citations.json", "w") as file:
                json.dump(data, file)
        await ctx.send(f"La citation a ĂŠtĂŠ ajoutĂŠe:\n{citation}")

    @commands.command(name="citation_list")
    async def quote_list(self, ctx):
        allowed = check_permissions(self, ctx)

        if allowed == False: 
            await ctx.send("Tu n'as pas les permissions nĂŠcessaires pour utiliser cette commande.")
            return

        with open("citations.json", "r") as file:
            try:
                data = json.load(file)
            except json.decoder.JSONDecodeError:
                await ctx.send("Aucune citation disponible")
                return
        for index, citation in enumerate(data):
            await ctx.send(f"[{index+1}] : {citation}")

    @commands.command(name="citation_del")
    async def quote_del(self, ctx, index: int):
        allowed = check_permissions(self, ctx)

        if allowed == False: 
            await ctx.send("Tu n'as pas les permissions nĂŠcessaires pour utiliser cette commande.")
            return

        with open("citations.json", "r+") as file:
            try:
                data = json.load(file)
                del data[index-1]
                file.seek(0)
                json.dump(data, file)
                file.truncate()
                await ctx.send(f"La citation Ă  l'index {index} a ĂŠtĂŠ supprimĂŠe.")
            except json.decoder.JSONDecodeError:
                await ctx.send("Aucune citation disponible")
            except IndexError:
                await ctx.send(f"L'index {index} n'est pas valide.")

async def setup(client):
  await client.add_cog(Citations(client))
