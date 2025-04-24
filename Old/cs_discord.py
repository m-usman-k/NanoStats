import discord
from discord.ext import commands
import traceback
import json
import sys
import os

abspath = os.path.abspath(sys.argv[0])
dname = os.path.dirname(abspath)
os.chdir(dname)

print("+=================================================================+\n"
    "|    ┌─┐┬ ┬┌┬┐┌─┐┌┐ ┌─┐┌┬┐┌─┐                                     |\n"
    "|    └─┐│ │ │││ │├┴┐│ │ │ ┌─┘       AUTOMATING EVERYTHING         |\n"
    "|    └─┘└─┘─┴┘└─┘└─┘└─┘ ┴ └─┘                                     |\n"
    "+=================================================================+\n"
    "|                      >> Discord Alerts <<                       |\n"
    "+=================================================================+\n"
    "|                          CONTACTS                               |\n"
    "|           Fiverr  : https://fiverr.com/saifalimz                |\n"
    "|           Website : https://www.sudobotz.com                    |\n"
    "|           E-Mail  : contact@sudobotz.com                        |\n"
    "+=================================================================+\n")

with open('config.txt', 'r', encoding='utf-8') as f:
    configs = [line.rstrip('\n') for line in f]
    for config in configs:
        if 'discord_bot_token' in config:
            discord_bot_token = config.split('=')[1].strip()
        if 'footer_text' in config:
            footer_text = config.split('=')[1].strip()
            
def format_stats_to_embed(player_team_stats, rival_team_stats, playing_map, stat_type=10):
    if playing_map:
        embed = discord.Embed(title=f"Player Stats - {playing_map.title()}")
    else:
        embed = discord.Embed(title=f"Player Stats - Map Not Available")

    player_team_value = ""
    rival_team_value = ""

    for stat in player_team_stats:
        player_name, player_team, pp_line, hltv_stats, avg_kills = stat
        formatted_stats = ", ".join([f"**{k}**" if float(k) > float(pp_line) else f"_{k}_" for k in hltv_stats[:stat_type]])
        avg_diff = f"{float(avg_kills)-float(pp_line):.2f}"
        if '-' in avg_diff:
            avg_diff = f"_{avg_diff}_"
        else:
            avg_diff = f"**{avg_diff}**"
        
        player_team_value += f"**{player_name}** ({player_team})\nPrizePicks Line: {pp_line}\nKills: {formatted_stats}\nAverage: {avg_kills:.2f}\nAdd Difference: {avg_diff}\n\n"

    for stat in rival_team_stats:
        rival_name, rival_team, pp_line, hltv_stats, avg_kills = stat
        formatted_stats = ", ".join([f"**{k}**" if float(k) > float(pp_line) else f"_{k}_" for k in hltv_stats[:stat_type]])
        avg_diff = f"{float(avg_kills)-float(pp_line):.2f}"
        if '-' in avg_diff:
            avg_diff = f"_{avg_diff}_"
        else:
            avg_diff = f"**{avg_diff}**"
        
        rival_team_value += f"**{rival_name}** ({rival_team})\nPrizePicks Line: {pp_line}\nKills: {formatted_stats}\nAverage: {avg_kills:.2f}\nAdd Difference: {avg_diff}\n\n"

    embed.add_field(name="Player Team", value=player_team_value or "No stats available yet", inline=True)
    embed.add_field(name="Rival Team", value=rival_team_value or "No stats available yet", inline=True)
    
    # Set the footer text
    embed.set_footer(text=f"\n{footer_text}")

    return embed

def get_data_embed(player_name, stat_type=10):
    try:
        with open('data.json', 'r', encoding='utf-8') as f:
            players =  json.load(f)['data']
    except:
        players = []
        
    player_team = None
    rival_team = None
    playing_map = None
    for player in players:
        if player_name.lower() in player[0].lower():
            player_team = player[1]
            rival_team = player[3].replace("MAP 3", "").strip()
            playing_map = player[-1]
            break
        
    print(f"[+] Getting players data for map {playing_map}")
        
    pt_data = []
    rt_data = []
        
    if player_team:
        for player in players:
            if player_team == player[1]:
                if stat_type == 10:
                    del player[-1]
                    del player[3]
                    del player[-1]
                elif stat_type == 5:
                    del player[-1]
                    del player[3]
                    del player[-2]
                pt_data.append(player)
                
    if rival_team:
        for player in players:
            print(rival_team)
            player[1]
            if rival_team == player[1]:
                if stat_type == 10:
                    del player[-1]
                    del player[3]
                    del player[-1]
                elif stat_type == 5:
                    del player[-1]
                    del player[3]
                    del player[-2]
                rt_data.append(player)
                
    embed = format_stats_to_embed(pt_data, rt_data, playing_map, stat_type)
    return embed
                
intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(command_prefix="!", intents=intents)

@bot.event
async def on_ready():
    print(f'We have logged in as {bot.user}')

@bot.command(name='cs2')
async def send_stats(ctx, map_name: str, player_name: str, stat_type: str):
    try:
        if 'map3' in map_name:
            print(f"Received command: run {map_name} {player_name} {stat_type}")
            if '10' in stat_type:
                embed = get_data_embed(player_name, stat_type=10)
            else:
                embed = get_data_embed(player_name, stat_type=5)
                
            await ctx.send(embed=embed)
    except Exception as e:
        traceback.print_exc()
        await ctx.send(f"An error occurred: {str(e)}")

bot.run(discord_bot_token)