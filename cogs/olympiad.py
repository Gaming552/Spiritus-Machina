import discord
from discord.ext import commands, tasks
import asyncio
from random import *
import math
import json
import os
import time
from typing import Optional
from operator import itemgetter
import traceback

async def win_leaderboard(self):
    guild = await self.bot.fetch_guild(self.bot.global_config['guild_id'])

    timestamp = int(time.time())

    with open('levels.json', 'r') as f:
        data = json.load(f)

    user_data = [(user_id, user['wins']) for user_id, user in data.items()]
    sorted_data = sorted(user_data, key=itemgetter(1), reverse=True)

    msg = f'__**Classement Victoires (mis Ă  jour <t:{timestamp}:R>) :**__\n'
    for k, (user_id, wins) in enumerate(sorted_data[:10]):
        member = await guild.fetch_member(user_id)

        if data[user_id]['loses'] > 0 and data[user_id]['wins'] > 0: 
            KD_ratio = round(data[user_id]['wins'] / data[user_id]['loses'],2)
        elif data[user_id]['loses'] == 0 and data[user_id]['wins'] > 0:
            KD_ratio = data[user_id]['wins']
        else: KD_ratio = 0

        position = str(k+1).zfill(2)
        wins=str(wins).zfill(2)
        loses=str(data[user_id]['loses']).zfill(2)
        KD_ratio = str(KD_ratio)
        elo = data[user_id]['elo']

        position_column = f"{position} :"
        member_column = f"{(member.display_name)}"
        elo_column = f"ELO : {str(elo)}"
        wins_column = f"Victoires : {wins}"
        loses_column = f"DĂŠfaites : {loses}"
        kd_column = f"K/D ratio : {KD_ratio}"

        msg += f"{position_column} {member_column} - {wins_column} - {loses_column} - {kd_column} - {elo_column}\n"
    
    return msg

async def elo_leaderboard(self):
    guild = await self.bot.fetch_guild(self.bot.global_config['guild_id'])

    timestamp = int(time.time())

    with open('levels.json', 'r') as f:
        data = json.load(f)

    user_data = [(user_id, user['elo']) for user_id, user in data.items()]
    sorted_data = sorted(user_data, key=itemgetter(1), reverse=True)

    msg = f'__**Classement ELO (mis Ă  jour <t:{timestamp}:R>) :**__\n'
    for k, (user_id, elo) in enumerate(sorted_data[:10]):
        member = await guild.fetch_member(user_id)

        if data[user_id]['loses'] > 0 and data[user_id]['wins'] > 0: 
            KD_ratio = round(data[user_id]['wins'] / data[user_id]['loses'],2)
        elif data[user_id]['loses'] == 0 and data[user_id]['wins'] > 0:
            KD_ratio = data[user_id]['wins']
        else: KD_ratio = 0

        position = str(k+1).zfill(2)
        wins=str(data[user_id]['wins']).zfill(2)
        loses=str(data[user_id]['loses']).zfill(2)
        KD_ratio = str(KD_ratio)

        position_column = f"{position} :"
        member_column = f"{(member.display_name)}"
        elo_column = f"ELO : {str(elo)}"
        wins_column = f"Victoires : {wins}"
        loses_column = f"DĂŠfaites : {loses}"
        kd_column = f"K/D ratio : {KD_ratio}"

        msg += f"{position_column} {member_column} - {elo_column} - {wins_column} - {loses_column} - {kd_column}\n"
    
    return msg

async def leaderboard(self):
    leaderboard_channel = self.bot.get_channel(self.bot.global_config['leaderboard_channel'])
    if not os.path.exists('leaderboard.json'):
        with open('leaderboard.json', 'w') as f:
            json.dump({}, f)

    with open('leaderboard.json', 'r') as f:
        data = json.load(f)

    if data:
        elo_msg = data['elo_msg']
        win_msg = data['win_msg']

        message = await leaderboard_channel.fetch_message(elo_msg)
        msg = await elo_leaderboard(self)
        await message.edit(content=msg)

        message = await leaderboard_channel.fetch_message(win_msg)
        msg = await win_leaderboard(self)
        await message.edit(content=msg)

    else:
        msg = await elo_leaderboard(self)
        elo_msg =await leaderboard_channel.send(msg)
        msg = await win_leaderboard(self)
        win_msg = await leaderboard_channel.send(msg)

        data['elo_msg'] = elo_msg.id
        data['win_msg'] = win_msg.id

        with open('leaderboard.json', 'w') as f:
            json.dump(data, f)

#purge banned users in levels.json
async def purge(guild):

    with open('levels.json', 'r') as f:
            data = json.load(f)

    data_new = {}

    for k,v in enumerate(data):
        try:
            member = await guild.fetch_member(v)
        except discord.NotFound:
            pass
        else:
            data_new[v] = {}
            for elem in data[v]:
                data_new[v][elem] = data[v][elem]


    with open('levels.json', 'w') as f:
        json.dump(data_new, f)

def get_lvl(stats_lvl):
    return stats_lvl.get('lvl')

def get_score(list_players):
    return list_players.get('score')

def create_pairings(list_players):
    sorted_players = sorted(list_players, key=get_score, reverse=True)

    if len(sorted_players) % 2 == 1:
        for k,v in enumerate(list_players):
            if v['id'] == sorted_players[-1]['id'] : list_players[k]['score'] += 1
        del sorted_players[-1]

    number = int(len(sorted_players)/2)
    pairings = [(sorted_players[i], sorted_players[i+number]) for i in range(0, number, 1)]

    return pairings

def calculate_elo_change(player_elo, opponent_elo, result, k=32):
  probability = 1 / (1 + 10**((opponent_elo - player_elo) / 400))
  return k * (result - probability)

def calculate_elo_loss(player_elo, opponent_elo, k=32):
  probability = 1 / (1 + 10**((opponent_elo - player_elo) / 400))
  return k * (0 - probability)

def calculate_gain(winner_level, loser_level):
    diff_level = winner_level - loser_level
    gain = 50 - diff_level
    return gain

def dyn_msg(event_name = None, attacker = None, defender = None, damage = None):
    if event_name is None : return ''

    with open('messages.json', 'r', encoding='utf-8') as f:
        msg_data = json.load(f)

    msg_roll = randint(0, len(msg_data[event_name])-1)
    msg = msg_data[event_name][msg_roll]

    if attacker is not None:
        msg = msg.replace('{atk}', attacker)
    if defender is not None:
        msg = msg.replace('{def}', defender)
    if damage is not None:
        dagger_emoji = ":dagger:"
        boom_emoji = ":boom:"

        if int(damage) == 2:
            damage = f"{damage}{dagger_emoji}"
            msg = msg.replace('{dmg}', damage)
        elif int(damage) >= 3:
            damage = f"{damage}{boom_emoji}"
            msg = msg.replace('{dmg}', damage)
        else:
            msg = msg.replace('{dmg}', damage)

    return msg

## params :
## player1, player2 : fighting players
## list_players : object list with players stats
## self : bot environment
## channel : text channel where the bot send messages
## tournament : True if the duel is for a tournament, False if not
## return :
## updated list_players
async def duel(player1, player2, list_players, self, channel, tournament):
    guild = await self.bot.fetch_guild(self.bot.global_config['guild_id'])

    custom_emoji = await guild.fetch_emojis()

    for emoji in custom_emoji: 
        if emoji.name == 'roll': roll_emoji = emoji

    turn_emoji = ":arrows_counterclockwise:"
    shield_emoji = ":shield:"
    sword_emoji = ":crossed_swords:"
    dagger_emoji = ":dagger:"
    boom_emoji = ":boom:"
    headstone_emoji = ":headstone:"
    trophy_emoji = ":trophy:"

    for k,v in enumerate(list_players):
        if v['id'] == player1['id'] : P1_index = k
        if v['id'] == player2['id'] : P2_index = k
    
    #calculate stat P1
    list_players[P1_index]['pv'] = 4

    #calculate stat P2
    list_players[P2_index]['pv'] = 4

    #bonus
    bool_bonus = False
    lvl_gap = list_players[P1_index]['lvl'] - list_players[P2_index]['lvl']
    if lvl_gap == 0: player_bonus = 'no bonus'
    if lvl_gap < 0: player_bonus = P2_index
    if lvl_gap > 0: player_bonus = P1_index

    if player_bonus != 'no bonus':
        lvl_gap = abs(lvl_gap)
        match lvl_gap:
            case lvl_gap if 1 <= lvl_gap <= 5: 
                list_players[player_bonus]['touch_roll'] = 1
                list_players[player_bonus]['pv'] += 1
            case lvl_gap if 6 <= lvl_gap <= 10: 
                list_players[player_bonus]['touch_roll'] = 1
                list_players[player_bonus]['pv'] += 2
            case lvl_gap if 11 <= lvl_gap <= 15:
                list_players[player_bonus]['touch_roll'] = 2
                list_players[player_bonus]['pv'] += 3 
            case lvl_gap if 16 <= lvl_gap <= 20:
                list_players[player_bonus]['touch_roll'] = 3
                list_players[player_bonus]['pv'] += 4
            case lvl_gap if 21 <= lvl_gap <= 25:
                list_players[player_bonus]['touch_roll'] = 3
                list_players[player_bonus]['def_roll'] = 1
                list_players[player_bonus]['pv'] += 4
            case lvl_gap if 26 <= lvl_gap <= 30:
                list_players[player_bonus]['touch_roll'] = 3
                list_players[player_bonus]['def_roll'] = 1
                list_players[player_bonus]['atk_bonus'] = 1
                list_players[player_bonus]['pv'] += 5

    rand = randint(0, 1)

    if rand == 0 :
        attacker = P1_index
        defenser = P2_index
    else :
        attacker = P2_index
        defenser = P1_index

    fight_turn = 0

    atk_member = await guild.fetch_member(list_players[attacker]['id'])
    def_member = await guild.fetch_member(list_players[defenser]['id'])

    msg =  ''
    P1_msg = f"{atk_member.mention} (lvl : {list_players[attacker]['lvl']})"
    P2_msg = f"{def_member.mention} (lvl : {list_players[defenser]['lvl']})"
    msg += f"--------------------------------------------------\n"
    
    dynamic_msg = dyn_msg(event_name = 'introduction', attacker = P1_msg, defender = P2_msg)
    msg += f"**{dynamic_msg}\n**"

    msg += f"\nRapport de bataille\n"
    msg += f"--------------------------------------------------\n"
    await channel.send(msg)

    while list_players[attacker]['pv'] > 0 or list_players[defenser]['pv'] > 0:
        atk_member = await guild.fetch_member(list_players[attacker]['id'])
        def_member = await guild.fetch_member(list_players[defenser]['id'])

        msg = ''
        fight_turn += 1
        next_turn = False

        msg += f"{turn_emoji} **TOUR {fight_turn}** :\n"
        msg += f"{atk_member.display_name} (**{list_players[attacker]['pv']} pv**) {sword_emoji} {def_member.display_name} (**{list_players[defenser]['pv']} pv**)\n\n"
        #touch roll
        touch_roll = randint(1, 6)

        msg += f"{roll_emoji} {atk_member.display_name} lance un D6 de touche et fait {touch_roll}\n"
        if touch_roll == 1:
            if list_players[attacker]['touch_roll'] > 0: 
                touch_roll = randint(1, 6)
                list_players[attacker]['touch_roll'] -= 1
                msg += f"{roll_emoji} {atk_member.display_name} utilise une relance et fait cette fois {touch_roll}\n"
        
        if touch_roll == 1:
            dynamic_msg = dyn_msg(event_name = 'touch_fail', attacker = atk_member.display_name, defender = def_member.display_name)
            msg += f"\n*{dynamic_msg}*\n"
            next_turn = True

        #atk roll
        if next_turn == False:
            atk_roll = randint(1, 6)
            msg += f"{roll_emoji} {atk_member.display_name} lance un D6 de degats et fait {atk_roll}\n"

            if atk_roll == 1:
                dynamic_msg = dyn_msg(event_name = 'dmg_fail', attacker = atk_member.display_name, defender = def_member.display_name)
                msg += f"\n*{dynamic_msg}*\n"
                next_turn = True

        #def roll
        if next_turn == False:
            def_roll = randint(1, 6)
            msg += f"{roll_emoji} {def_member.display_name} lance un D6 de sauvegarde et fait {def_roll}\n"

            if def_roll == 1:
                if list_players[defenser]['def_roll'] > 0: 
                    def_roll = randint(1, 6)
                    list_players[defenser]['def_roll'] -= 1
                    msg += f"{roll_emoji} {def_member.display_name} utilise une relance et fait cette fois {def_roll}\n"
            
            if def_roll == 1:
                dynamic_msg = dyn_msg(event_name = 'save_fail', attacker = atk_member.display_name, defender = def_member.display_name)
                msg += f"\n*{dynamic_msg}*"

                if list_players[defenser]['pv'] <= (atk_roll + list_players[attacker]['atk_bonus']) :
                    dynamic_msg = dyn_msg(event_name = 'fatal_hit', attacker = atk_member.display_name, defender = def_member.display_name)
                    msg += f"\n*{dynamic_msg}* {headstone_emoji}\n" 
                    list_players[defenser]['pv'] = list_players[defenser]['pv'] - (atk_roll + list_players[attacker]['atk_bonus'])
                else :
                    list_players[defenser]['pv'] = list_players[defenser]['pv'] - (atk_roll + list_players[attacker]['atk_bonus'])

                    if atk_roll == 2: event_name = 'dmg_moderate'
                    elif atk_roll >= 3: event_name = 'dmg_heavy'
                    else: event_name = 'dmg_light'

                    damage = str(atk_roll + list_players[attacker]['atk_bonus'])
                    dynamic_msg = dyn_msg(event_name = event_name, attacker = atk_member.display_name, defender = def_member.display_name, damage=damage)
                    msg += f"\n*{dynamic_msg}*"

                    next_turn = True
            elif def_roll == 6:
                dynamic_msg = dyn_msg(event_name = 'save_success', attacker = atk_member.display_name, defender = def_member.display_name)
                msg += f"\n*{dynamic_msg}*\n"
                next_turn = True
            else:
                dgt_bonus = list_players[attacker]['atk_bonus']
                dgt = atk_roll-def_roll
                dgt_total = dgt + dgt_bonus

                if dgt <= 0:
                    dynamic_msg = dyn_msg(event_name = 'strength', attacker = atk_member.display_name, defender = def_member.display_name)
                    msg += f"\n*{dynamic_msg}* {shield_emoji}"
                    next_turn = True
                else:
                    if list_players[defenser]['pv'] <= dgt_total:
                        list_players[defenser]['pv'] = list_players[defenser]['pv'] - (dgt + list_players[attacker]['atk_bonus'])
                        dynamic_msg = dyn_msg(event_name = 'fatal_hit', attacker = atk_member.display_name, defender = def_member.display_name)
                        msg += f"\n*{dynamic_msg}* {headstone_emoji}" 
                    else:
                        match dgt_total:
                            case dgt_total if dgt_total == 1:
                                list_players[defenser]['pv'] = list_players[defenser]['pv'] - dgt_total
                                event_name = 'dmg_light'
                                next_turn = True
                            case dgt_total if dgt_total == 2:
                                list_players[defenser]['pv'] = list_players[defenser]['pv'] - dgt_total
                                event_name = 'dmg_moderate'
                                next_turn = True
                            case dgt_total if dgt_total >= 3:
                                list_players[defenser]['pv'] = list_players[defenser]['pv'] - dgt_total
                                event_name = 'dmg_heavy'
                            case _:
                                list_players[defenser]['pv'] = list_players[defenser]['pv'] - dgt_total
                                event_name = 'dmg_light'
                        
                        damage = str(dgt_total)
                        dynamic_msg = dyn_msg(event_name = event_name, attacker = atk_member.display_name, defender = def_member.display_name, damage=damage)
                        msg += f"\n*{dynamic_msg}*"       

                        next_turn = True

        if list_players[defenser]['pv'] <= 0:
            await channel.send(msg)
            break

        #next turn
        if attacker == P1_index:
            attacker = P2_index
            defenser = P1_index
        else:
            attacker = P1_index
            defenser = P2_index

        await channel.send(msg)
        time.sleep(10)
        
    #end fight
    winner = attacker
    loser = defenser

    winner_member = await guild.fetch_member(list_players[winner]['id'])
    loser_member = await guild.fetch_member(list_players[loser]['id'])

    if tournament == True:
        gain = calculate_gain(list_players[winner]['lvl'], list_players[loser]['lvl'])
        list_players[winner]['score'] += gain
        msg =  ''
        msg += f"{trophy_emoji} Victoire de {winner_member.display_name} (lvl : {list_players[winner]['lvl']})\n"
    else:
        #players ELO
        winner_ELO = list_players[winner]['elo']
        loser_ELO = list_players[loser]['elo']
        
        elo_change = int(calculate_elo_change(winner_ELO, loser_ELO, 1))
        elo_loss = int(calculate_elo_loss(loser_ELO, winner_ELO))
        gain = calculate_gain(list_players[winner]['lvl'], list_players[loser]['lvl'])

        with open('levels.json', 'r') as f:
            data = json.load(f)

        data[str(winner_member.id)]['elo'] += elo_change
        data[str(loser_member.id)]['elo'] += elo_loss

        data[str(winner_member.id)]['wins'] += 1
        data[str(loser_member.id)]['loses'] += 1

        if data[str(winner_member.id)]['level'] < 30:
            data[str(winner_member.id)]['xp'] += (gain+100)

        if data[str(loser_member.id)]['level'] < 30:
            data[str(loser_member.id)]['xp'] -= 50

        if data[str(loser_member.id)]['xp'] <= 0:
           data[str(loser_member.id)]['xp'] = 0 

        with open('levels.json', 'w') as f:
            json.dump(data, f)

        msg =  ''
        msg += f"{trophy_emoji} Victoire de {winner_member.mention} (lvl : {list_players[winner]['lvl']})\n"
        msg += f"\n{winner_member.display_name} gagne {(gain+100)} d'xp et {elo_change} de ELO\n"
        msg += f"{loser_member.display_name} perd 50 d'xp et {abs(elo_loss)} de ELO\n"
    await channel.send(msg)
    return list_players

class Olympiad(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
    
    @commands.Cog.listener()
    async def on_ready(self):
        print("Commands Cog Ready!")

    async def cog_load(self):
        self.reset_duel_count.start()

    async def cog_unload(self):
        self.reset_duel_count.stop()

    @tasks.loop(hours=24)
    async def reset_duel_count(self):
        with open('levels.json', 'r') as f:
            data = json.load(f)

        for elem in data:
            data[elem]['count'] = 0

        with open("levels.json", "w") as f:
            json.dump(data, f)

    @commands.Cog.listener()
    async def on_command_error(self,ctx,error):
        if isinstance(error, commands.CommandOnCooldown):

            member = ctx.author

            minutes, seconds = divmod(error.retry_after, 60)
            minutes = round(minutes)
            seconds = round(seconds)

            minutes_plural = 'minute'
            seconds_plural = 'seconde'

            if minutes > 1:
                minutes_plural = 'minutes'
            if seconds > 1:
                seconds_plural = 'secondes'

            if error.retry_after < 60 :
                msg = f"{member.display_name}, Tu dois attendre {seconds} {seconds_plural} avant de lancer un nouveau duel"
            else:
                msg = f"{member.display_name}, Tu dois attendre {minutes} {minutes_plural} et {seconds} {seconds_plural} avant de lancer un nouveau duel"
            await ctx.send(msg)

    @commands.command(name="duel")
    @commands.cooldown(1, 180, commands.BucketType.user)
    async def one_duel(self, ctx: commands.Context, user: Optional[discord.Member]):
        guild = await self.bot.fetch_guild(self.bot.global_config['guild_id'])
        arena_channel = self.bot.get_channel(self.bot.global_config['arena_channel'])

        member1 = ctx.author
        member2 = user

        if member2 is None: 
            await ctx.send("Tu dois choisir un adversaire pour un duel, exemple :\n!duel @Indomitus")
            return

        if member1 == member2: 
            await ctx.send("Tu ne pas pas te battre contre toi mĂŞme")
            return

        if member2.guild_permissions.administrator:
            await ctx.send(f"{member2.display_name} lĂ¨ve la main et lance une puissante attaque psychique contre {member1.display_name}, mettant fin Ă  sa vie en un instant.")
            return

        if member2 == self.bot.user:
            await ctx.send(f"{member1.display_name} n'a pas eu le temps de rĂŠagir lorsque {member2.display_name} a activĂŠ son canon Ă  plasma, vaporisant instantanĂŠment son corps et brĂťlant tout sur son passage.\nLe sol est jonchĂŠ de dĂŠbris fumants, tĂŠmoins silencieux de la puissance mortelle de la machine.")
            return
        
        roles = sorted(member2.roles, key=lambda x: x.position, reverse=True)

        for k,v in enumerate(roles):
            if self.bot.global_config['moderator_chief_role'] == v.id:
                    await ctx.send(f"{member2.display_name} abat avec dĂŠtermination sa Lance Gardienne acĂŠrĂŠe, faisant virevolter la tĂŞte de {member1.display_name}")
                    return
                    
            if self.bot.global_config['no_xp_role'] == v.id:
                await ctx.send(f"Tu n'es pas habilitĂŠ Ă  te battre contre {member2.display_name}")
                return

        with open('levels.json', 'r') as f:
            data = json.load(f)

        list_players = []
        list_ID = []
        for k,v in enumerate(data):
            stat_lvl = data[v]['level']
            elo = data[v]['elo']
            pv = 4
            touch_roll = 0
            atk_bonus = 0
            def_roll = 0
            PD = 0
            if int(v) == member1.id or int(v) == member2.id:
                list_players.append({'id': v, 'score' : 0, 'lvl' : stat_lvl, 'elo' : elo, 'pv' : pv, 'touch_roll' : touch_roll, 'atk_bonus' : atk_bonus, 'def_roll' : def_roll, 'PD' : PD})
                list_ID.append(int(v))
        
        if member1.id not in list_ID :
            await ctx.send(f"Tu n'es pas habilitĂŠ Ă  faire des demandes de duel")
            return

        if member2.id not in list_ID :
            await ctx.send(f"{member2.name} n'est pas habilitĂŠ Ă  participer Ă  des duels")
            return
        
        max_duel_per_day = self.bot.global_config['max_duel_per_day']

        if data[str(member1.id)]['count'] >= max_duel_per_day:
            await ctx.send(f"Annulation de la procĂŠdure de duel\nRaison : {member1.display_name} a depassĂŠ la limite de duel quotidien (maximum : {max_duel_per_day})\nRĂŠinitialisation du cooldown")
            return
        
        if data[str(member2.id)]['count'] >= max_duel_per_day:
            await ctx.send(f"Annulation de la procĂŠdure de duel\nRaison : {member2.display_name} a depassĂŠ la limite de duel quotidien (maximum : {max_duel_per_day})\nRĂŠinitialisation du cooldown")
            return

        yes_emoji = 'â'
        no_emoji = 'â'
        message = await ctx.send(f"{member2.display_name} (niveau {data[str(member2.id)]['level']}), {member1.display_name} (niveau {data[str(member1.id)]['level']}) te provoque en duel\nAcceptes-tu de le combattre ?")
        await message.add_reaction(yes_emoji)
        await message.add_reaction(no_emoji)

        def check(reaction, user):
            return user == member2 and str(reaction.emoji) in [yes_emoji, no_emoji]

        try:
            reaction, user = await self.bot.wait_for('reaction_add', timeout=30.0, check=check)
        except asyncio.TimeoutError:
            ctx.command.reset_cooldown(ctx)
            await ctx.send('Annulation de la procĂŠdure de duel\nRaison : Temps de rĂŠponse depassĂŠ\nRĂŠinitialisation du cooldown')
            return

        if str(reaction.emoji) == yes_emoji:
            await ctx.send(f"Lancement de la procĂŠdure de duel\nCe dernier commencera dans 5 secondes dans le canal {arena_channel.mention}")
            time.sleep(5)
            try:
                await duel(list_players[0], list_players[1], list_players, self, arena_channel, False)
            except Exception:
                print("--------------------------------")
                traceback.print_exc()

            with open('levels.json', 'r') as f:
                data = json.load(f)

            data[str(member1.id)]['count'] += 1
            data[str(member2.id)]['count'] += 1

            with open('levels.json', 'w') as f:
                json.dump(data, f)

            await leaderboard(self)

        elif str(reaction.emoji) == no_emoji:
            ctx.command.reset_cooldown(ctx)
            await ctx.send('Annulation de la procĂŠdure de duel\nRaison : Refus\nRĂŠinitialisation du cooldown')
            return

    @commands.command(name="olympiad")
    @commands.has_permissions(administrator=True)
    async def olympiad(self, ctx):
        guild = await self.bot.fetch_guild(self.bot.global_config['guild_id'])
        olympiad_channel = self.bot.get_channel(self.bot.global_config['olympiad_channel'])
        if ctx.channel.id != olympiad_channel.id: return

        list_players = []
        entry_lvl = self.bot.global_config['entry_lvl']

        await purge(guild)

        with open('levels.json', 'r') as f:
            data = json.load(f)

        for k,v in enumerate(data):
            stat_lvl = data[v]['level']
            elo = stat_lvl * 0.5
            pv = 4
            touch_roll = 0
            atk_bonus = 0
            def_roll = 0
            PD = 0
            if stat_lvl >= entry_lvl:
                list_players.append({'id': v, 'score' : 0, 'lvl' : stat_lvl, 'elo' : elo, 'pv' : pv, 'touch_roll' : touch_roll, 'atk_bonus' : atk_bonus, 'def_roll' : def_roll, 'PD' : PD})
        
        nb_players = len(list_players)
        nb_turns = int(math.log(nb_players,2))
        turn = 1

        shuffle(list_players)

        while turn <= nb_turns:
            pairings = create_pairings(list_players)

            for (player1, player2) in pairings:
                list_players = await duel(player1, player2, list_players, self, olympiad_channel, True)

            turn += 1

        list_players.sort(key=get_score, reverse=True)
        msg =  "**Classement final :**\n"
        msg += "--------------------------------------------------\n"
        for k,v in enumerate(list_players):
            member = await guild.fetch_member(v['id'])
            if k == 0: msg_winner = f"Le gagnant est : {member.display_name}, fĂŠlicitation !"
            msg += f"{k+1:02d} : {member.display_name} | lvl {v['lvl']:02d} | Score : {round(v['score']):02d}\n" 
        
        await olympiad_channel.send(msg)
        await olympiad_channel.send(msg_winner)
        
    @commands.command(name="leaderboard")
    @commands.has_permissions(administrator=True)
    async def leaderboard_command(self, ctx):
        bot_channel = self.bot.get_channel(self.bot.global_config['bot_channel'])
        if ctx.channel.id != bot_channel.id: return

        await leaderboard(self)

    @commands.command(name="purge")
    @commands.has_permissions(administrator=True)
    async def purge_command(self, ctx):
        bot_channel = self.bot.get_channel(self.bot.global_config['bot_channel'])
        guild = await self.bot.fetch_guild(self.bot.global_config['guild_id'])
        if ctx.channel.id != bot_channel.id: return

        await purge(guild)

async def setup(client):
  await client.add_cog(Olympiad(client))
