# Imports
import discord, os, json
from discord.ext import commands
from discord import app_commands

import mysql.connector
from datetime import date
from decimal import Decimal
from datetime import datetime
from dotenv import load_dotenv
from fuzzywuzzy import process

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

# Database connection
def db_connection():
    conn = mysql.connector.connect(
        host=HOST,
        port=PORT,
        user=USER,
        password=PASSWORD,
        database=DATABASE
    )
    return conn

# Helper function for fuzzy matching
def fuzzy_match(input_value: str, options: list[str], threshold: int = 80):
    match, score = process.extractOne(input_value.lower(), options)
    return match if score >= threshold else None

# Helper function to format stats
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

# Fetch user stats
def grab_user_stats(player: str, map_filter: list[int], last: int, versus: str, company: str):
    with db_connection() as conn:
        cursor = conn.cursor()
        # Normalize inputs
        cursor.execute("SELECT DISTINCT player_name, opponent FROM hltv_cs")
        all_players, all_opponents = zip(*cursor.fetchall())
        player = fuzzy_match(player, all_players) or player
        versus = fuzzy_match(versus, all_opponents) or versus
        # Query with map_number filter
        map_condition = f"hltv_cs.map_number IN ({','.join(map(str, map_filter))})"
        cursor.execute(f"""
            SELECT 
                *
            FROM
                hltv_cs
            JOIN
                {company}_lines
            ON
                hltv_cs.player_name = {company}_lines.player_name
            WHERE
                LOWER(hltv_cs.player_name) = '{player.lower()}'
            AND
                {map_condition}
            AND
                LOWER(hltv_cs.opponent) = '{versus.lower()}'
            ORDER BY
                hltv_cs.date DESC
            LIMIT
                {last}
        """)
        return cursor.fetchall()

# Fetch team stats
def grab_team_stats(team: str, map_filter: list[int], last: int, versus: str):
    with db_connection() as conn:
        cursor = conn.cursor()
        # Normalize inputs
        cursor.execute("SELECT DISTINCT team, opponent FROM hltv_cs")
        all_teams, all_opponents = zip(*cursor.fetchall())
        team = fuzzy_match(team, all_teams) or team
        versus = fuzzy_match(versus, all_opponents) or versus
        # Query with map_number filter
        map_condition = f"hltv_cs.map_number IN ({','.join(map(str, map_filter))})"
        cursor.execute(f"""
            SELECT 
                *
            FROM
                hltv_cs
            WHERE
                LOWER(team) = '{team.lower()}'
            AND
                {map_condition}
            AND
                LOWER(opponent) = '{versus.lower()}'
            ORDER BY
                date DESC
            LIMIT
                {last}
        """)
        return cursor.fetchall()

# Helper function to display stats in embeds
async def display_stats(interaction: discord.Interaction, stats_data: list, title: str):
    embeds = []
    for i in range(0, len(stats_data), 5):
        embed = discord.Embed(
            title=title,
            color=EMBED_COLOR,
            timestamp=datetime.now()
        )
        for stat in stats_data[i:i+5]:
            embed.add_field(
                name=f"Match: {stat['event']} ({stat['date']})",
                value=(
                    f"**Map:** {stat['map']} | **Team:** {stat['team']} vs {stat['opponent']}\n"
                    f"**Player:** {stat['player_name']} | **K/D:** {stat['kills']}/{stat['deaths']} ({stat['k_d_diff']:+})\n"
                    f"**Rating:** {stat['rating']:.2f} | **ADR:** {stat['adr']}\n"
                    f"**HS%:** {stat['headshots']}% | **KAST:** {stat['kast']}%\n"
                    f"[Match Link]({stat['match_url']})"
                ),
                inline=False
            )
        embed.set_footer(text=f"Requested by {interaction.user.name}")
        embeds.append(embed)

    # Send all embeds in one message
    await interaction.followup.send(embeds=embeds)

# Commands
@bot.tree.command(name="user-stats", description="Display stats of a specific player")
@app_commands.choices(company=[
    app_commands.Choice(name="Prizepicks", value="prizepicks"),
    app_commands.Choice(name="Underdog", value="underdog")
], map=[
    app_commands.Choice(name="1", value="1"),
    app_commands.Choice(name="1-2", value="1-2"),
    app_commands.Choice(name="1-3", value="1-3")
])
async def user_stats(interaction: discord.Interaction, player: str, map: app_commands.Choice[str], last: int, versus: str, company: str):
    await interaction.response.defer()
    # Convert map choice to integer or range
    if map.value == "1":
        map_filter = [1]
    elif map.value == "1-2":
        map_filter = [1, 2]
    elif map.value == "1-3":
        map_filter = [1, 2, 3]
    else:
        map_filter = []

    raw_stats = grab_user_stats(player=player, map_filter=map_filter, last=last, versus=versus, company=company)
    if not raw_stats:
        await interaction.followup.send("No stats found. Please check your inputs.")
        return
    formatted_stats = hltv_jsonify(raw_stats)
    await display_stats(interaction, formatted_stats, title=f"📊 Stats for {player}")

@bot.tree.command(name="team-stats", description="Display stats of a specific team")
@app_commands.choices(map=[
    app_commands.Choice(name="1", value="1"),
    app_commands.Choice(name="1-2", value="1-2"),
    app_commands.Choice(name="1-3", value="1-3")
])
async def team_stats(interaction: discord.Interaction, team: str, map: app_commands.Choice[str], last: int, versus: str):
    await interaction.response.defer()
    # Convert map choice to integer or range
    if map.value == "1":
        map_filter = [1]
    elif map.value == "1-2":
        map_filter = [1, 2]
    elif map.value == "1-3":
        map_filter = [1, 2, 3]
    else:
        map_filter = []

    raw_stats = grab_team_stats(team=team, map_filter=map_filter, last=last, versus=versus)
    if not raw_stats:
        await interaction.followup.send("No stats found. Please check your inputs.")
        return
    formatted_stats = hltv_jsonify(raw_stats)
    await display_stats(interaction, formatted_stats, title=f"📊 Stats for Team {team}")

# Execution
if __name__ == "__main__":
    bot.run(BOT_TOKEN)