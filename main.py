# Imports
import discord, os, json
from discord.ext import commands
from discord import app_commands

import mysql.connector
from datetime import date
from decimal import Decimal
from datetime import datetime
from dotenv import load_dotenv

# Globals
load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
HOST = os.getenv("HOST")
PORT = os.getenv("PORT")
USER = os.getenv("USER")
PASSWORD = os.getenv("PASSWORD")
DATABASE = os.getenv("DATABASE")
EMBED_COLOR = int(os.getenv("EMBED_COLOR"))

bot = commands.Bot(command_prefix="!", intents=discord.Intents.all())

# Events
@bot.event
async def on_ready():
    print(f"🟢 | Bot is live")


    await bot.tree.sync()
    print(f"🟢 | Bot tree synced")

# Functions
def hltv_jsonify(all_data: list[tuple]):
    formatted = []

    for row in all_data:
        formatted.append({
            "match_url": row[0],
            "event": row[1],
            "date": row[2],
            "map": row[3],
            "map_number": row[4],
            "team": row[5],
            "team_url": row[6],
            "opponent": row[7],
            "opponent_url": row[8],
            "player_name": row[9],
            "player_url": row[10],
            "team_score": row[11],
            "opponent_score": row[12],
            "kills": row[13],
            "headshots": row[14],
            "assists": row[15],
            "deaths": row[16],
            "kast": row[17],
            "k_d_diff": row[18],
            "adr": row[19],
            "fk_diff": row[20],
            "rating": row[21]
        })
    
    return formatted


def db_connection():
    conn = mysql.connector.connect(
        host=HOST,
        port=PORT,
        user=USER,
        password=PASSWORD,
        database=DATABASE
    )

    return conn

def grab_user_stats(player: str, map: str, last: int, versus: str, company: str):
    with db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(f"""
            SELECT 
                *
            FROM
                hltv_cs
            JOIN
                {company}_lines
            WHERE
                hltv_cs.player_name = '{player}'
            AND
                hltv_cs.opponent = '{versus}'
            ORDER BY
                hltv_cs.date ASC
            LIMIT
                {last}

        """)

        return cursor.fetchall()
    
def grab_team_stats():
    ...
    

async def display_stats(interaction: discord.Interaction, stats_data: list):
    for each_list in stats_data:
        for key, value in each_list.items():
            if isinstance(value, date):
                each_list[key] = value.isoformat()
            if isinstance(value, Decimal):
                each_list[key] = float(value)
    """Display player stats in an organized embed format"""
    print(json.dumps(stats_data , indent=4))
    # Create embed
    embed = discord.Embed(
        title="📊 CS:GO Player Statistics",
        color=EMBED_COLOR,
        timestamp=datetime.now()
    )
    
    # Add match info header
    embed.add_field(
        name="🏆 Match Info",
        value=f"**{stats_data[0]['team']}** vs **{stats_data[0]['opponent']}**\n"
              f"**Map:** {stats_data[0]['map']} | **Date:** {stats_data[0]['date']}",
        inline=False
    )
    
    # Process and group players by team
    teams = {}
    for player in stats_data:
        team = player['team']
        if team not in teams:
            teams[team] = []
        teams[team].append(player)
    
    # Add stats for each team
    for team_name, players in teams.items():
        team_text = []
        
        for player in sorted(players, key=lambda x: x['rating'], reverse=True):
            # Format individual player stats
            player_line = (
                f"🔹 **{player['player_name']}**\n"
                f"• K/D: {player['kills']}/{player['deaths']} ({player['k_d_diff']:+})\n"
                f"• Rating: {player['rating']:.2f} | ADR: {player['adr']}\n"
                f"• HS%: {player['headshots']}% | KAST: {player['kast']}%\n"
                f"• FK Diff: {player['fk_diff']:+}\n"
            )
            team_text.append(player_line)
        
        embed.add_field(
            name=f"🧩 {team_name}",
            value="\n".join(team_text),
            inline=True
        )
    
    # Add footer with additional info
    embed.set_footer(
        text=f"Requested by {interaction.user.name}"
    )
    
    # Add thumbnail
    embed.set_thumbnail(url="https://images-wixmp-ed30a86b8c4ca887773594c2.wixmp.com/f/3e50fc94-a1de-4734-b30c-23be84b8b0b5/ddci66q-9aff9f04-42da-4c5f-a612-007d738caa02.png/v1/fill/w_1280,h_1535/cs_go_icon_by_starkevan_ddci66q-fullview.png?token=eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJzdWIiOiJ1cm46YXBwOjdlMGQxODg5ODIyNjQzNzNhNWYwZDQxNWVhMGQyNmUwIiwiaXNzIjoidXJuOmFwcDo3ZTBkMTg4OTgyMjY0MzczYTVmMGQ0MTVlYTBkMjZlMCIsIm9iaiI6W1t7ImhlaWdodCI6Ijw9MTUzNSIsInBhdGgiOiJcL2ZcLzNlNTBmYzk0LWExZGUtNDczNC1iMzBjLTIzYmU4NGI4YjBiNVwvZGRjaTY2cS05YWZmOWYwNC00MmRhLTRjNWYtYTYxMi0wMDdkNzM4Y2FhMDIucG5nIiwid2lkdGgiOiI8PTEyODAifV1dLCJhdWQiOlsidXJuOnNlcnZpY2U6aW1hZ2Uub3BlcmF0aW9ucyJdfQ.OKQTNbSlN9bzcINL0iaWrF2oGw_Fbp2VhE0M6-sqQU4")  # CS:GO logo
    
    await interaction.followup.send(embed=embed)

# Commands
@bot.tree.command(name="stats", description="A command to display stats of user based on previous matches")
@app_commands.choices(map=[
    app_commands.Choice(name="Map1", value="map1"),
    app_commands.Choice(name="Map1-2", value="map1-2"),
    app_commands.Choice(name="Map1-3", value="map1-3"),
])
@app_commands.choices(company=[
    app_commands.Choice(name="Prizepicks", value="prizepicks"),
    app_commands.Choice(name="Underdog", value="underdog")
])
async def stats(interaction: discord.Interaction, player: str, map: str, last: int, versus: str, company: str):
    ...
    await interaction.response.defer()
    
    # Get raw stats from database
    raw_stats = grab_user_stats(player=player, map=map, last=last, versus=versus, company=company)
    
    # Convert to dictionary format
    formatted_stats = hltv_jsonify(raw_stats)
    
    # Display using the new embed format
    await display_stats(interaction, formatted_stats)


# Execution
if __name__ == "__main__":
    bot.run(BOT_TOKEN)