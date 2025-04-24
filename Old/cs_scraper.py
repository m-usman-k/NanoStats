import discord
from discord.ext import commands
from seleniumbase import SB
import traceback
import json
import cloudscraper
from bs4 import BeautifulSoup
import time
import sys
import os
from concurrent.futures import ThreadPoolExecutor, as_completed

abspath = os.path.abspath(sys.argv[0])
dname = os.path.dirname(abspath)
os.chdir(dname)

print("+=================================================================+\n"
      "|    ┌─┐┬ ┬┌┬┐┌─┐┌┐ ┌─┐┌┬┐┌─┐                                     |\n"
      "|    └─┐│ │ │││ │├┴┐│ │ │ ┌─┘       AUTOMATING EVERYTHING         |\n"
      "|    └─┘└─┘─┴┘└─┘└─┘└─┘ ┴ └─┘                                     |\n"
      "+=================================================================+\n"
      "|                  >> PizePicks|HLTV x Scraper <<                 |\n"
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
            
        if 'proxies' in config:
            proxy_gateway = config.split('=')[1].strip()

def get_response(url, delay=7, is_proxy=False):
    while True:
        try:
            print(f"Fetching URL: {url} with delay: {delay}")
            proxies = {"http": f"http://{proxy_gateway}", "https": f"http://{proxy_gateway}"}
            scraper = cloudscraper.create_scraper(
                browser={
                    'browser': 'chrome',
                    'platform': 'windows',
                    'desktop': True,
                    'delay': delay
                })
            if is_proxy:
                res_text = scraper.get(url, proxies=proxies).text
            else:
                res_text = scraper.get(url).text
            scraper.close()
            if res_text and "Attention Required! | Cloudflare" not in res_text:
                if "<title>Just a moment...</title>" in res_text:
                    if delay < 10:
                        delay += 1
                    else:
                        delay = 7
                else:
                    return res_text
            else:
                time.sleep(1)
        except Exception as e:
            print(f"Error fetching URL: {e}")
            time.sleep(1)

def get_m3_players():
    print("[+] Getting PrizePicks 'MAP 3 Kills' Players data...")
    pt_data = []

    res_text = get_response("https://api.prizepicks.com/projections?league_id=265&per_page=250&state_code=GA&single_stat=true&game_mode=pickem", delay=1)

    pricepicks_data = json.loads(res_text)['data']
    if pricepicks_data:
        pricepicks_includes = json.loads(res_text)['included']
        
        for data in pricepicks_data:
            if "MAP 3 Kills" == data['attributes']['stat_type']:
                player_id = data['relationships']['new_player']['data']['id']
                for pin in pricepicks_includes:
                    if player_id == pin['id']:
                        player_nam = pin['attributes']['name']
                        line_score = data['attributes']['line_score']
                        player_team = pin['attributes']['team']
                        rival_team = data['attributes']['description'].replace("MAP 3", "").strip()
                        pt_data.append([player_nam, player_team, line_score, rival_team])
                        break
                
    if len(pt_data) == 0:
        print("[-] No MAP 3 Data found...")
        return None
    else:
        return pt_data

def get_maps():
    print(f"[-] Getting map names...")
    maps = []
    
    res_text = get_response(f"https://www.hltv.org/matches")
    soup = BeautifulSoup(res_text, 'html.parser')
    
    for live_match in soup.find_all("div", class_="liveMatch-container"):
        teams = live_match.find_all("div", class_="matchTeamName text-ellipsis")
        map_name = live_match['data-maps'].split(',')[-1]
        for team in teams:
            maps.append([team.text, map_name])
    
    if len(maps) > 0:
        return maps
    else:
        return None

def get_hltv_player_data(player_name, map_name, stat_type=10):
    print(f"[-] Getting HLTV player data for player: {player_name}, map: {map_name}, stat_type: {stat_type}")
    res_text = get_response(f"https://www.hltv.org/search?term={player_name}")
    hltv_searchs = json.loads(res_text)

    hltv_player = None
    player_found = False
    for hltv_search in hltv_searchs:
        for player_res in hltv_search.get('players', []):
            if player_res['nickName'].lower() == player_name.lower():
                hltv_player = "https://www.hltv.org" + player_res['location']
                player_found = True
                break
        if player_found:
            break

    if hltv_player:
        stats = []

        res_text = get_response(f"https://www.hltv.org/stats/players/matches/{hltv_player.split('/player/')[1]}?maps=de_{map_name.lower()}")
        soup = BeautifulSoup(res_text, 'html.parser')

        table_rows = soup.find("table", class_="stats-table sortable-table stats-matches-table").find('tbody').find_all('tr')
        table_rows = table_rows[:stat_type]
        
        for table_row in table_rows:
            row_tds = table_row.find_all('td')
            kills = row_tds[4].text.split('-')[0].strip()
            
            stats.append(kills)

        return stats
    else:
        return None

def scrape_stats(first_loop=True):
    player_team = []
    all_players = []
    
    playing_maps = get_maps()
    pt_data = get_m3_players()
    if pt_data:
        print(f"[-] Scraping stats...")
        
        if not first_loop:
            if os.path.exists('data.json'):
                with open('data.json', 'r', encoding='utf-8') as json_file:
                    all_players = json.loads(json_file.read())['data']
            else:
                pass

        def fetch_player_data(ptd):
            if ptd[0] not in str(all_players):
                player_data = ptd
                
                playing_map = None
                for pmap in playing_maps:
                    if pmap[0] == ptd[1]:
                        playing_map = pmap[1]
                        break
                
                if playing_map:
                    hltv_stats = get_hltv_player_data(ptd[0], playing_map, stat_type=10)

                    if hltv_stats:
                        stats_average_10 = sum(map(float, hltv_stats)) / len(hltv_stats)
                        stats_average_5 = sum(map(float, hltv_stats[:5])) / len(hltv_stats[:5])
                        player_data.append(hltv_stats)
                        player_data.append(stats_average_10)
                        player_data.append(stats_average_5)
                        player_data.append(playing_map)
                        return player_data
                    else:
                        print(f"[-] No HLTV stats found for player {ptd[0]} on map {playing_map}")
            else:
                print(f"[-] Player data for {ptd[0]}, already exists, skipping...")
            return None

        with ThreadPoolExecutor(max_workers=4) as executor:
            future_to_player = {executor.submit(fetch_player_data, ptd): ptd for ptd in pt_data}
            for future in as_completed(future_to_player):
                result = future.result()
                if result:
                    player_team.append(result)

        for row in player_team:
            all_players.append(row)

        data = {
            "data": all_players
        }

        with open('data.json', 'w', encoding='utf-8') as json_file:
            json.dump(data, json_file, ensure_ascii=False, indent=4)

        return player_team
    else:
        return None

start_time = time.time()
first_loop = True
while True:
    try:
        if first_loop:
            scrape_stats(first_loop=True)
            first_loop = False
        else:
            scrape_stats(first_loop=False)
            
        print("\n[+] Rescanning stats in 5 minutes...")
        time.sleep(60 * 5)
        
        # Check if 3 hours have passed
        if time.time() - start_time >= 60 * 60 * 2:
            if os.path.exists("data.json"):
                os.remove("data.json")
                print("[+] data.json deleted")
            
            # Reset the start time
            start_time = time.time()

    except Exception as e:
        print(f"Error scraping stats: {e}")
        print("Retrying...")
        time.sleep(1)