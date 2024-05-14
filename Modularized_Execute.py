#!/usr/local/bin/python3.11


import unicodedata
import os
import statsapi
import json
import time
import shutil

#THIS SCRIPT COLLECTS AND SAVES THE GAME JSONS

today = time.strftime('%Y-%m-%d')
#today = '2024-09-20'

def save_game_data(game_id, data):
    with open(f"games/2024/{game_id}_log.json", "w") as json_file:
        json.dump(data, json_file, indent=4)
    print(f"Data saved as games/2024/{game_id}_log.json")




def collect_game_data(start_date, end_date, team_id=None, opponent_id=None):
    saved_game_ids = set()
    saved_pitcher_ids = set()
    for filename in os.listdir("games/2024"):
        if '._' not in filename:
            if filename.endswith("_log.json"):
                print(filename)  # Print out the filename to understand its structure
                game_id = filename.split("_")[0]  # Adjust the index to match the game ID position in the filename
                saved_game_ids.add(int(game_id))

    games = statsapi.schedule(start_date=start_date, end_date=today, team=team_id, opponent=opponent_id)
    
    count = 0
    for game in games:
        count += 1
        game_id = game['game_id']
        if game_id not in saved_game_ids:
            game_data = statsapi.boxscore_data(game_id)
            if game_data['homePitchingTotals']['ip'] != "0.0":
                save_game_data(game_id, game_data)
            else:
                print(game_id,'passed')
    print(f'Total Games Played: {count}')




collect_game_data(start_date='2024-03-28', end_date=today, team_id="", opponent_id="")




#THIS SCRIPT CREATES THE ORIGINAL METADATA
import os
import json
import re

def normalize_name(name,t):
    name = unicodedata.normalize('NFD', name)
    name = name.encode('ascii', 'ignore').decode('ascii')
    if t == 'pitcher':
        name = re.sub(r"\W+", '', name.lower())
    return name

def load_game_data(filepath):
    with open(filepath, 'r') as file:
        return json.load(file)

def save_metadata(data, filename):
    with open(filename, "w") as file:
        json.dump(data, file, indent=4)
    print(f"Metadata saved as {filename}")

def collect_player_metadata(directory):
    pitcher_metadata = {}
    batter_metadata = {}
    
    # Iterate over each game file in the directory
    for filename in os.listdir(directory):
        if filename.endswith(".json") and not (filename.startswith('._') or filename.startswith('._')):
            game_data = load_game_data(os.path.join(directory, filename))
            
            # Process each team (home and away)
            for team_key in ['home', 'away']:
                team_data = game_data[team_key]
                
                # Process pitchers
                for pitcher_id in team_data['pitchers']:
                    if pitcher_id not in pitcher_metadata:
                        pitcher_metadata[pitcher_id] = game_data['playerInfo']['ID' + str(pitcher_id)]
                        pitcher_name = pitcher_metadata[pitcher_id]['fullName']
                        pitcher_name = normalize_name(pitcher_name,t='pitcher')
                        pitcher_metadata[pitcher_id]['fullName'] = pitcher_name
                
                # Process batters
                for batter_id in team_data['batters']:
                    if batter_id not in pitcher_metadata:
                        if batter_id not in batter_metadata:
                            batter_metadata[batter_id] = game_data['playerInfo']['ID' + str(batter_id)]
                            batter_name = batter_metadata[batter_id]['fullName']
                            batter_name_alt = normalize_name(batter_name,t='batter')
                            batter_name = normalize_name(batter_name,t='pitcher')
                            batter_metadata[batter_id]['fullName'] = batter_name
                            batter_metadata[batter_id]['fullNameAlt'] = batter_name_alt
                    

    # Save the collected metadata to JSON files
    save_metadata(pitcher_metadata, "players/2024/pitcher_metadata.json")
    save_metadata(batter_metadata, "players/2024/batter_metadata.json")

# Directory where the game data JSON files are stored
game_data_directory = "games/2024"
collect_player_metadata(game_data_directory)



#THIS SCRIPT ADDS THE PITCHINGHAND TO METDATA
import os
import json
import requests
import pandas as pd
from pybaseball import pitching_stats

def load_metadata(filepath):
    with open(filepath, 'r') as file:
        return json.load(file)

def save_metadata(data, filepath):
    with open(filepath, 'w') as file:
        json.dump(data, file, indent=4)
    print(f"Updated metadata saved to {filepath}")

def fetch_player_handness(person_id):
    url = f"https://statsapi.mlb.com/api/v1/people/{person_id}"
    response = requests.get(url)
    if response.status_code == 200:
        data = response.json()
        player_info = data['people'][0]
        pitching_hand = player_info.get('pitchHand', {}).get('description', '')
        player_name = player_info.get("fullName")
        return pitching_hand, player_name
    return '', '', ''

def update_pitcher_metadata(filepath):
    player_data = load_metadata(filepath)
    pitching_stats_2024 = pitching_stats(2024).set_index('Name')

    for player_id, details in player_data.items():
        pitching_hand, player_name = fetch_player_handness(player_id)
        details['PitchingHand'] = pitching_hand
        details['PlayerName'] = player_name



    save_metadata(player_data, filepath)

# Path to the metadata JSON file
json_filepath = 'players/2024/pitcher_metadata.json'
update_pitcher_metadata(json_filepath)


  
#THIS SCRIPT APPENDS TEH FANGRAPS DATA TO THE METDATA
import json
import pandas as pd
import numpy as np
from pybaseball import pitching_stats

def normalize_name(name):
    name = unicodedata.normalize('NFD', name)
    name = name.encode('ascii', 'ignore').decode('ascii')
    name = re.sub(r"\W+", '', name.lower())
    if name in ['Mike Soroka','mikesoroka']:
        name = 'michaelsoroka'
    if name in ['Luis L. Ortiz']:
        name = 'luislortiz'
    if name in ['j.p.france']:
        name = 'jpfrance'
        
    return name


def load_json(filename):
    with open(filename, 'r') as file:
        return json.load(file)

def save_json(data, filename):
    with open(filename, 'w') as file:
        # Convert any problematic types here before saving
        def convert(item):
            if isinstance(item, np.generic):
                return np.asscalar(item)
            raise TypeError
        json.dump(data, file, default=convert, indent=4)

def fetch_fangraphs_data(year, qual):
    df = pitching_stats(year, qual=qual)
    df = df[~((df['Name'] == 'Logan Allen') & (df['Team'] == 'ARI'))]
    df.to_csv(f'players/2024/dataframes/pitcher_{year}.csv')  # Save data for review
    return df



def append_stats_to_pitchers(json_file, year, cols, qual,option=False):
    data = load_json(json_file)
    pitching_stats_df = fetch_fangraphs_data(year, qual)
    pitching_stats_df['player_name'] = pitching_stats_df['Name'].apply(normalize_name)
    pitching_stats_df.set_index('player_name', inplace=True)

    for pitcher_id, pitcher_info in data.items():
        normalized_name = normalize_name(pitcher_info['PlayerName'])
        if normalized_name in pitching_stats_df.index:
            player_stats = pitching_stats_df.loc[normalized_name]
            if isinstance(player_stats, pd.DataFrame):
                player_stats = player_stats.iloc[0]  # Take the first row if there are multiple

            for col in cols:
                if col in player_stats and not pd.isna(player_stats[col]):
                    if option:
                        pitcher_info['statcast'][col] = float(player_stats[col]) if isinstance(player_stats[col], np.number) else player_stats[col]
                    else:
                        pitcher_info[col] = float(player_stats[col]) if isinstance(player_stats[col], np.number) else player_stats[col]
            if 'SI% (sc)' in pitcher_info:
                pitcher_info['SI%'] = pitcher_info.pop('SI% (sc)')
    save_json(data, json_file)


#these are the selected columns from dataframes/pitcher_year.csv to copy to the pitcher metadata
cols = [
    'ERA', 'xERA', 'IP','Location+', 'Stuff+', 'Pitching+', 'Contact%', 'K/9', 'BB/9', 'H/9','GB/FB',
    'Oppo%','Pull%','Soft%','Hard%','Zone%',
    'FBv', 'SLv', 'CTv', 'CBv', 'CHv','SFv', 'KNv',
    'wFB/C', 'wSL/C', 'wCT/C', 'wCB/C', 'wCH/C', 'wSF/C', 'wKN/C',
    'FB% 2', 'SL%', 'CT%', 'CB%', 'CH%', 'SF%', 'KN%','SI% (sc)',
    'Stf+ CH', 'Loc+ CH', 'Pit+ CH', 'Stf+ CU', 'Loc+ CU', 'Pit+ CU', 'Stf+ FA', 
    'Loc+ FA', 'Pit+ FA', 'Stf+ SI', 'Loc+ SI', 'Pit+ SI', 'Stf+ SL', 'Loc+ SL', 'Pit+ SL', 'Stf+ KC', 
    'Loc+ KC', 'Pit+ KC', 'Stf+ FC', 'Loc+ FC', 'Pit+ FC', 'Stf+ FS', 'Loc+ FS', 'Pit+ FS'
]

json_filepath = 'players/2024/pitcher_metadata.json'

append_stats_to_pitchers(json_filepath, 2024, cols, 3)

#This scipr adds in consitency and talent ratings
import os
import pandas as pd
import numpy as np
import json
from scipy.stats import zscore

directory = 'players/2024/pitcher_gamelogs'
metadata_file = 'players/2024/pitcher_metadata.json'
with open(metadata_file, 'r') as f:
    metadata = json.load(f)
    
std_devs = {}

for filename in os.listdir(directory):
    if filename.endswith(".csv"):
        if not filename.startswith('._'):
            df = pd.read_csv(os.path.join(directory, filename))
            df['er'] = pd.to_numeric(df['er'], errors='coerce')
            df['k'] = pd.to_numeric(df['k'], errors='coerce')
            df['h'] = pd.to_numeric(df['h'], errors='coerce')
            
            er_std_dev = round(df['er'].std(), 3)
            k_std_dev = round(df['k'].std(), 3)
            h_std_dev = round(df['h'].std(), 3)
            
            pitcher_id = filename[:-4][-6:]
            
            try:
                er_talent = metadata[pitcher_id]['ERA']
                k_talent = metadata[pitcher_id]['K/9']
                h_talent = metadata[pitcher_id]['H/9']
                if not any(pd.isna(val) for val in [er_std_dev, k_std_dev, h_std_dev]):
                    std_devs[pitcher_id] = {
                        'er_std_dev': er_std_dev,
                        'k_std_dev': k_std_dev,
                        'h_std_dev': h_std_dev,
                        'er_talent': er_talent,
                        'k_talent': k_talent,
                        'h_talent': h_talent
                    }
            except KeyError:
                pass

std_devs = {k: std_devs[k] for k in sorted(std_devs)}
print(std_devs)  # This dictionary now contains standard deviations tied to pitcher IDs

er_z_scores = zscore([std_devs[pitcher_id]['er_std_dev'] for pitcher_id in std_devs])
k_z_scores = zscore([std_devs[pitcher_id]['k_std_dev'] for pitcher_id in std_devs])
h_z_scores = zscore([std_devs[pitcher_id]['h_std_dev'] for pitcher_id in std_devs])
ert_z_scores = zscore([std_devs[pitcher_id]['er_talent'] for pitcher_id in std_devs])
kt_z_scores = zscore([std_devs[pitcher_id]['k_talent'] for pitcher_id in std_devs])
ht_z_scores = zscore([std_devs[pitcher_id]['h_talent'] for pitcher_id in std_devs])

er_var = np.var([std_devs[pitcher_id]['er_std_dev'] for pitcher_id in std_devs])
k_var = np.var([std_devs[pitcher_id]['k_std_dev'] for pitcher_id in std_devs])
h_var = np.var([std_devs[pitcher_id]['h_std_dev'] for pitcher_id in std_devs])
ert_var = np.var([std_devs[pitcher_id]['er_talent'] for pitcher_id in std_devs])
kt_var = np.var([std_devs[pitcher_id]['k_talent'] for pitcher_id in std_devs])
ht_var = np.var([std_devs[pitcher_id]['h_talent'] for pitcher_id in std_devs])



er_z_scores_adjusted = er_z_scores / np.sqrt(er_var)
k_z_scores_adjusted = k_z_scores / np.sqrt(k_var)
h_z_scores_adjusted = h_z_scores / np.sqrt(h_var)
ert_z_scores_adjusted = ert_z_scores / np.sqrt(ert_var)
kt_z_scores_adjusted = kt_z_scores / np.sqrt(kt_var)
ht_z_scores_adjusted = ht_z_scores / np.sqrt(ht_var)


def map_to_consistency(z_scores, variance):
    mean_z_score = np.mean(z_scores)
    return {pitcher_id: round((z - mean_z_score) / np.sqrt(variance), 3) for pitcher_id, z in zip(std_devs.keys(), z_scores)}

def map_to_talent(z_scores, variance, attribute):
    print(attribute,np.median(z_scores))
    if attribute in ['K/9']:
        median_z_score = np.median(z_scores)
        return {pitcher_id: round(((z - median_z_score) / np.sqrt(variance))*10, 3) for pitcher_id, z in zip(std_devs.keys(), z_scores)}
    elif attribute in ['ERA','H/9']:
        median_z_score = np.median(z_scores)
        return {pitcher_id: round(((median_z_score - z) / np.sqrt(variance))*10, 3) for pitcher_id, z in zip(std_devs.keys(), z_scores)}
    else:
        raise ValueError("Unsupported attribute for talent mapping")



er_consistency_scores = map_to_consistency(er_z_scores, er_var)
k_consistency_scores = map_to_consistency(k_z_scores, k_var)
h_consistency_scores = map_to_consistency(h_z_scores, h_var)
ert_consistency_scores = map_to_talent(ert_z_scores, ert_var, 'ERA')
kt_consistency_scores = map_to_talent(kt_z_scores, kt_var, 'K/9')
ht_consistency_scores = map_to_talent(ht_z_scores, ht_var, 'H/9')


for pitcher_id in metadata:
    if pitcher_id in std_devs:
        metadata[pitcher_id]['er_consistency'] = er_consistency_scores.get(pitcher_id, 0)
        metadata[pitcher_id]['k_consistency'] = k_consistency_scores.get(pitcher_id, 0)
        metadata[pitcher_id]['h_consistency'] = h_consistency_scores.get(pitcher_id, 0)
        
        metadata[pitcher_id]['er_talent'] = ert_consistency_scores.get(pitcher_id, 0)
        metadata[pitcher_id]['k_talent'] = kt_consistency_scores.get(pitcher_id, 0)
        metadata[pitcher_id]['h_talent'] = ht_consistency_scores.get(pitcher_id, 0)

with open(metadata_file,'w') as f:
    json.dump(metadata,f)


'''I need to make sure the new pith type columns are propelry copied'''

#THIS PART CREATES THE year GAMELOGS

import json
import pandas as pd
import os

def load_json(filename):
    with open(filename, 'r') as file:
        return json.load(file)

def save_csv(df, filename):
    df.to_csv(filename, index=False)

def parse_weather_info(game_data):
    for info in game_data['gameBoxInfo']:
        if info['label'] == "Weather":
            weather_data = info['value']
            temperature = None
            weather = None
            try:
                temperature_info, weather = weather_data.split(', ')
                temperature = int(temperature_info.split(' ')[0])
                if ',' in weather:
                    weather = weather.split(', ')[0]
            except ValueError:
                # Handle cases where the weather data might be in a different format
                print(f"Weather data not in expected format: {weather_data}")
            return temperature, weather
    return None, None

def collect_game_logs(game_data_dir, batters_metadata, pitcher_metadata_path, output_dir):
    batters = load_json(batters_metadata)
    pitchers = load_json(pitcher_metadata_path)
    
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    player_game_logs = {str(batter_id): [] for batter_id in batters}
    pitcher_game_logs = {str(pitcher_id): [] for pitcher_id in pitchers}

    for game_file in os.listdir(game_data_dir):
        if game_file.endswith(".json") and not game_file.startswith('._'):
            file_path = os.path.join(game_data_dir, game_file)
            with open(file_path, 'r') as file:
                game_data = json.load(file)
                game_date = game_data["gameId"][0:10]
                home_team = game_data["teamInfo"]["home"]["abbreviation"]
                away_team = game_data["teamInfo"]["away"]["abbreviation"]

                for team_key in ['home', 'away']:
                    team = game_data["teamInfo"][team_key]["abbreviation"]
                    opponent_team_key = 'away' if team_key == 'home' else 'home'
                    opponent = game_data["teamInfo"][opponent_team_key]["abbreviation"]
                    opponent_pitchers = game_data[opponent_team_key + 'Pitchers'][1:]
                    temperature, weather = parse_weather_info(game_data)
                    
                    
                    for player_info in game_data[f'{team_key}Pitchers'][1:]:
                        player_id = str(player_info['personId'])
                        if player_id in pitcher_game_logs:
                            stats = {
                                "date": game_date,
                                "opponent": opponent,
                                "team": team,
                                "location": team_key,  # Indicates whether the player was at home or away
                                "weather": weather,
                                "temp": temperature,
                                **{key: player_info.get(key, '') for key in [
                                    'ip', 'h', 'r', 'er', 'bb', 'k', 'hr', 'era'
                                ]}
                            }
                            pitcher_game_logs[player_id].append(stats)
                            
                    for player_info in game_data[f'{team_key}Batters'][1:]:
                        player_id = str(player_info['personId'])
                        position = player_info['position']
                        
                        if player_id in player_game_logs:
                            opposing_pitcher = opponent_pitchers[0]
                            opposing_pitcher_id = str(opposing_pitcher['personId'])
                            pitcher_data = pitchers.get(opposing_pitcher_id, {})

                            stats = {
                                "date": game_date,
                                "opponent": opponent,
                                "team": team,
                                "location": team_key,  # Indicates whether the player was at home or away
                                "weather": weather,
                                "temp": temperature,
                                "opposingPitcherId": opposing_pitcher_id,
                                "position": position,
                                **{key: player_info.get(key, '') for key in [
                                    'ab', 'r', 'h', 'doubles', 'triples', 'hr', 'rbi',
                                    'sb', 'bb', 'k', 'lob', 'avg', 'obp', 'slg', 'ops'
                                ]},
                                **pitcher_data
                            }
                            player_game_logs[player_id].append(stats)

    for player_id, games in player_game_logs.items():
        if games:
            df = pd.DataFrame(games)
            if df['ab'].astype(int).sum() > 1:
                player_name = batters[player_id]['fullNameAlt'].replace(' ', '_')
                save_csv(df, os.path.join(output_dir, f"{player_name}_{player_id}.csv"))
                
    for player_id, games in pitcher_game_logs.items():
        if games:
            df = pd.DataFrame(games)
            player_name = pitchers[player_id]['PlayerName'].replace(' ', '_')
            save_csv(df, os.path.join('players/2024/pitcher_gamelogs', f"{player_name}_{player_id}.csv"))



#to include meta
# Paths
game_data_directory = 'games/2024'
batters_metadata = 'players/2024/batter_metadata.json'
pitchers_metadata = 'players/2024/pitcher_metadata.json'
output_directory = 'players/2024/batter_gamelogs'


collect_game_logs(game_data_directory, batters_metadata, pitchers_metadata, output_directory)



#THIS PART CREATES THE 2023+ GAMELOGS

#this method simply removes (pi) from the json
def process_json_remove_pi_suffix(file_path='players/2024/pitcher_metadata.json'):
    with open(file_path, 'r') as file:
        data = json.load(file)
    
    updated_data = {}
    for player_id, stats in data.items():
        new_stats = {key.replace(' (pi)', ''): value for key, value in stats.items()}
        updated_data[player_id] = new_stats
    
    save_json(updated_data,file_path)
process_json_remove_pi_suffix()





import pandas as pd
import os

def load_gamelogs(year, directory_path):
    year_path = os.path.join(directory_path, str(year), 'batter_gamelogs')
    all_data = {}
    if os.path.exists(year_path):
        for file in os.listdir(year_path):
            if file.endswith(".csv") and not file.startswith('._'):
                file_path = os.path.join(year_path, file)
                df = pd.read_csv(file_path)
                player_id = file.split('_')[-1].split('.')[0]  # Extract the player ID from the filename
                player_name = '_'.join(file.split('_')[:-1])  # Extract the player name from the filename
                player_key = f"{player_name}_{player_id}"
                if player_key in all_data:
                    all_data[player_key] = pd.concat([all_data[player_key], df])
                else:
                    all_data[player_key] = df
                print(f"Loaded {file} for year {year}")
    else:
        print(f"Directory {year_path} not found.")
    return all_data

def combine_and_save_gamelogs(directory_path, output_path):
    combined_data = {}
    years = [2023, 2024]
    for year in years:
        yearly_data = load_gamelogs(year, directory_path)
        for key, df in yearly_data.items():
            if key in combined_data:
                combined_data[key] = pd.concat([combined_data[key], df])
            else:
                combined_data[key] = df
            print(f"Combining data for {key}")

    if not os.path.exists(output_path):
        os.makedirs(output_path)
        print(f"Created directory {output_path}")

    for key, df in combined_data.items():
        df['date'] = pd.to_datetime(df['date'])  # Ensure 'date' is datetime type
        df.set_index('date', inplace=True)  # Set 'date' as index
        

        output_file_path = os.path.join(output_path, f"{key}.csv")
        df.to_csv(output_file_path)
        print(f"Saved {output_file_path}")

# Paths and parameters
directory_path = 'players'
output_path = 'players/2023+/batter_gamelogs'

# Combine and save the gamelogs
combine_and_save_gamelogs(directory_path, output_path)

print("Gamelogs combined and saved in the 'players/2023+/batter_gamelogs' directory.")


#THIS SCRIPT CREATES THE BATTER GAMELOGS

#for player in players/2024/pitcher_metadata.json
#we need to look at their pitch specific info
#for each pitch, the velocity, efficiceny and frequency are all tracked
#we need to categorize each pitch, and then calculate the weigthed averages for each category
#we will have hard, breaking and offspeed
#for each of these we calculate teh weighted average velocity, efficiency and frequency based off the pitches under each umbrella
#hard will be the weighted avereages of FA,FC,FS, SI
#breaking is CL, CUR, KN
#offspeed is CH,SP
#you must look at the json, and identify how each attributed is constrcuted specifically