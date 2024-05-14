def convert_date_to_int(date_str):
    return int(date_str.replace('-', ''))

def normalize_name(name):
    return ''.join(e for e in name.lower() if e.isalnum())

import datetime
import os
import pandas as pd
import time
import strategies
from pybaseball import playerid_reverse_lookup
from pybaseball import get_splits
import json
import warnings
import unicodedata
import re
warnings.filterwarnings("ignore")

def search_player_or_team(directory, identifier):
    if len(identifier) == 3 or identifier in ['sd','SD']:  
        team_name = identifier.upper()
        return None, None, None, team_name
    else:
        identifier = normalize_name(identifier)
        for file in os.listdir(directory):
            if file.endswith('.csv') and not file.startswith('._'):
                player_name = '_'.join(file.split('_')[:-1])
                player_id = file.split('_')[-1].split('.')[0]
                if normalize_name(player_name) == identifier:
                    return player_name, player_id, os.path.join(directory, file), None
        return None, None, None, None

def calculate_stats(df, period):
    last_games = df.tail(period)
    hits = last_games['h'].sum()
    at_bats = last_games['ab'].sum()
    average = hits / at_bats if at_bats else 0
    return hits, at_bats, average

def analyze_team_performance(directory, team_name, periods):
    team_performance = {}
    for file in os.listdir(directory):
        if file.endswith('.csv') and not file.startswith('._'):
            player_name = '_'.join(file.split('_')[:-1])
            df = pd.read_csv(os.path.join(directory, file))
            team_in_file = df['team'].apply(normalize_name).iloc[-1]
            if team_in_file == normalize_name(team_name):
                performance_data = {}
                for period in periods:
                    hits, at_bats, average = calculate_stats(df, period)
                    performance_data[period] = {'hits': hits, 'at_bats': at_bats, 'average': average}
                team_performance[player_name] = performance_data
    return team_performance

def display_team_performance(team_performance, periods):
    for player, data in team_performance.items():
        report_lines = []
        if data[5]['at_bats'] > 4:
            print('\n')
            for period in periods:
                stats = data[period]
                report_lines.append(f"{player}: Last {period} games: Hits: {stats['hits']}, At Bats: {stats['at_bats']}, Average: {stats['average']:.3f}")
            print("\n".join(report_lines))

def extract_year_from_date(date_str):
    try:
        if '-' in date_str:
            return int(date_str.split('-')[0])
        elif '/' in date_str:
            return int(date_str.split('/')[0])
        else:
            raise ValueError("Date format not supported")
    except Exception as e:
        print(f"Error extracting year from date: {date_str} - {e}")
        return None

def get_rolling_year_range():
    today = datetime.datetime.now()
    one_year_ago = today - datetime.timedelta(days=365)
    today_str = today.strftime('%Y-%m-%d')
    one_year_ago_str = one_year_ago.strftime('%Y-%m-%d')
    return one_year_ago_str, today_str

def apply_filters(df, filters, year=None):
    rolling_average_start, rolling_average_end = get_rolling_year_range()

    for filter_crit in filters:
        key, operator, value = filter_crit.partition('=') if '=' in filter_crit else \
                               filter_crit.partition('>') if '>' in filter_crit else \
                               filter_crit.partition('<')
        key = key.strip()
        value = value.strip()

        if key == 'date':
            value = extract_year_from_date(value)  # Only convert date values for year extraction
            if value is None:
                continue  # Skip if year extraction fails
            # If year is provided and the value is valid, filter based on the rolling average or specified year
            if year and value:
                if year == '2023+':
                    df = df[df['date'].astype(str).between(rolling_average_start, rolling_average_end)]
                else:
                    df = df[df['date'].astype(str).str[:4] == str(year)]
            else:
                continue

        try:
            if operator == '=':
                if value.replace('.', '', 1).isdigit():  # Simple check for numeric values
                    value = float(value)
                if value == 'None':  # Check if value is 'None'
                    df = df[df[key].isna()]  # Filter for NaN values
                else:
                    df = df[df[key] == value]
            elif operator == '>':
                df = df[df[key] > float(value)]  # Safe to convert because '>' is a numeric operation
            elif operator == '<':
                df = df[df[key] < float(value)]  # Safe to convert because '<' is a numeric operation
        except KeyError:
            #print(f"Error: Column '{key}' not found in data. Please check your criteria.")
            continue
        except ValueError as e:
            print(f"Error processing filter '{filter_crit}': {e}")
            continue

    return df


def calculate_hit_record(df):
    if df.empty:
        return 0, 0, 0  # If DataFrame is empty, return zero stats
    df = df[df['ab'] >= 2]  # Ensure 'ab' is at least 2
    hits = len(df[df['h'] >= 1])
    no_hits = len(df[df['h'] == 0])
    hit_percentage = hits / (hits + no_hits) if hits + no_hits > 0 else 0
    return hits, no_hits, hit_percentage

def save_player_strategy(player_id, player_name, team, strategy, results, year_option):
    strategy_file = 'strategies/player_strategies.csv'
    if not os.path.exists(strategy_file):
        with open(strategy_file, 'w') as file:
            file.write("Player ID,Player Name,Team,Strategy,Date,Cron,")
            file.write("Hits 2023,No Hits 2023,Hit Percentage 2023,Hits 2024,No Hits 2024,Hit Percentage 2024\n")
    with open(strategy_file, 'a') as file:
        file.write(f"{player_id},{normalize_name(player_name)},{team},{'|'.join(strategy)},{time.strftime('%Y-%m-%d')},{year_option},")
        # Add stats for 2023
        if '2023' in results:
            file.write(f"{results['2023']['hits']},{results['2023']['no_hits']},{results['2023']['hit_percentage']:.2%},")
        else:
            file.write(",,,")

        # Add stats for 2024
        if '2024' in results:
            file.write(f"{results['2024']['hits']},{results['2024']['no_hits']},{results['2024']['hit_percentage']:.2%}\n")
        else:
            file.write(",,\n")

    print("Strategy and performance data saved for all years.")


def read_strategies(filepath):
    try:
        strategies_df = pd.read_csv(filepath)
        for index, row in strategies_df.iterrows():
            print(f"Player ID: {row['Player ID']}")
            print(f"Player Name: {row['Player Name']}")
            print(f"Team: {row['Team']}")
            print(f"Strategy: {row['Strategy']}")
            print(f"Date: {row['Date']}")
            print(f"Time Frame: {row['Cron']}")
            for year in ['2023', '2024']:
                if f"Hits {year}" in row and f"No Hits {year}" in row and f"Hit Percentage {year}" in row:
                    print(f"Hits {year}: {row[f'Hits {year}']}")
                    print(f"No Hits {year}: {row[f'No Hits {year}']}")
                    print(f"Hit Percentage {year}: {row[f'Hit Percentage {year}']}")
            
            print("-" * 40)  # Separator for readability

    except FileNotFoundError:
        print("The file was not found. Please check the filepath.")
    except Exception as e:
        print(f"An error occurred: {e}")


#This is for choice 4
def calculate_batting_average(hits, at_bats):
    return hits / at_bats if at_bats else 0

def find_hottest_hitters(directory, periods):
    min_ab = {3: 5, 5: 10, 7: 15}
    player_stats = {}
    for file in os.listdir(directory):
        if file.endswith('.csv') and not file.startswith('._'):
            player_name = '_'.join(file.split('_')[:-1])
            df = pd.read_csv(os.path.join(directory, file))
            team = df['team'].iloc[-1]
            for period in periods:
                last_games = df.tail(period)
                hits = last_games['h'].sum()
                at_bats = last_games['ab'].sum()
                average = calculate_batting_average(hits, at_bats)
                if at_bats >= min_ab[period]:
                    if player_name not in player_stats:
                        player_stats[player_name] = {}

                    if period not in player_stats[player_name]:
                        player_stats[player_name][period] = {}

                    player_stats[player_name][period] = {
                        'team': team,
                        'hits': hits,
                        'at_bats': at_bats,
                        'average': average
                    }

    # Print the top 30 players for each period
    for period in periods:
        sorted_players = sorted(player_stats.items(), key=lambda x: x[1].get(period, {'average': 0})['average'], reverse=True)

        print(f"\n\nTop 30 Hitters over the Last {period} Days:\n")
        print("Team\tPlayer Name\t\tAverage\t\tHits\tAt-Bats")
        print("-------------------------------------------------------")
        for i, (player, stats) in enumerate(sorted_players[:30], start=1):
            stats_for_period = stats.get(period, {'team': 0, 'average': 0, 'hits': 0, 'at_bats': 0})
            print(f"{stats_for_period['team']}\t{player.ljust(25)}{stats_for_period['average']:.3f}\t\t{stats_for_period['hits']}\t{stats_for_period['at_bats']}")



def search_player(directory, identifier):
    identifier = normalize_name(identifier)
    for file in os.listdir(directory):
        if file.endswith('.csv') and not file.startswith('._'):
            player_name = '_'.join(file.split('_')[:-1])
            player_id = file.split('_')[-1].split('.')[0]
            if normalize_name(player_name) == identifier:
                return player_name, player_id, os.path.join(directory, file)
    return None, None, None

#This method creates a baseball reference key, for a player name
def create_player_key(name):
    if isinstance(name,str):
        name = normalize_name_key(name)
    parts = name.split('_')
    parts = [part for part in parts if part.lower() not in ['jr.','jr']]
    first_name = parts[0].capitalize()
    last_name = parts[-1].capitalize()
    player_key = (last_name[:5] + first_name[:2] + '01').lower()

    return player_key

def create_player_key_alt(name):
    parts = name.split(' ')
    parts = [part for part in parts if part.lower() not in ['jr.','jr']]
    first_name = parts[0].capitalize()
    last_name = parts[-1].capitalize()
    player_key = (last_name[:5] + first_name[:2] + '01').lower()
    return player_key

def normalize_name_key(name):
    name = unicodedata.normalize('NFD', name)
    name = name.encode('ascii', 'ignore').decode('ascii')
    name = re.sub(r"\W+", '', name.lower())
    return name

def get_team_players(directory, team_name):
    team_players = {}
    team_name_normalized = normalize_name(team_name)
    for file in os.listdir(directory):
        if file.endswith('.csv') and not file.startswith('._'):
            df = pd.read_csv(os.path.join(directory, file))
            # Check if the last entry (most recent game) is for the specified team
            if df.empty or normalize_name(df.iloc[-1]['team']) != team_name_normalized:
                continue
            player_name = '_'.join(file.split('_')[:-1])
            player_id = file.split('_')[-1].split('.')[0]
            team_players[normalize_name(player_name)] = player_id
    return team_players

def apply_and_display_filters(df, filters):
    # Splitting the dataset by year
    years = ['2023', '2024']
    results = {}
    for year in years:
        df_year = df[df['date'].str.contains(year)]
        df_filtered = apply_filters(df_year, filters, year)
        if df_filtered.empty:
            results[year] = "Error applying filters or no data matched the criteria."
        else:
            hits, no_hits, hit_percentage = calculate_hit_record(df_filtered)
            results[year] = f"Hits: {hits}, No Hits: {no_hits}, Hit Record: {hit_percentage:.2%}"

    for year, result in results.items():
        print(f"{year} - {result}")


def splits(user_input,directory,year_opt,t):
    periods = [3, 5, 7]
    years = [2024]
    with open(f'players/{year_opt}/batter_metadata.json','r') as bf:
        batters = json.load(bf)
    with open(f'players/{year_opt}/pitcher_metadata.json','r') as pf:
        pitchers = json.load(pf)
    with open('players/ids.json','r') as file:
        saved_ids = json.load(file)
    codes = ['01','02','03','04','05']
    index = 0
    
    player_name, player_id, file_path = search_player(directory, user_input)
    player_name_normalized = user_input.lower().replace(' ','')
    try:
        bbref = saved_ids[player_name_normalized]
    except KeyError:
        try:
            if isinstance(player_name,str):
                bbref = create_player_key(player_name)
            else:
                bbref = create_player_key_alt(user_input)
        except AttributeError:
            bbref = create_player_key_alt(user_input)
    
    if t == 'batter':
        splits_found = False
        for code in codes:
            if splits_found == True:
                break
            try:
                for year in years:
                    player_splits = get_splits(bbref.replace('01',code),year=year,pitching_splits=False)
                    platoon = player_splits.loc[[('Platoon Splits', 'vs RHP'), ('Platoon Splits', 'vs LHP')]]
                    platoon = platoon.iloc[:, [2,3,5,8,13,14,15,16]]
                    platoon['H/PA'] = round(platoon['H'] / platoon['PA'], 3)
                    print(f'{year}\n',platoon)
                splits_found = True
            except KeyError:
                pass
            except IndexError:
                pass
    elif t == 'pitcher':
        splits_found = False
        for code in codes:
            if splits_found == True:
                break
            #currently does h/a 2023, splits 24
            try:
                for year in years:
                    player_splits = get_splits(bbref.replace('01',code),year=year,pitching_splits=True)
                    platoon = player_splits[0]
                    platoon['ERA'] = round(platoon['R'] / 9, 3)
                    platoon = platoon.iloc[[5,6], [1,2,4,7,11,13,14,15]]
                    platoon['H/PA'] = round(platoon['H'] / platoon['PA'], 3)
                    print(f'\n\n{year}\n',platoon)
                splits_found = True
            except IndexError:
                index += 1
                print("First time entries must be in complete format")
                
        for pitcher_id, pitcher_data in pitchers.items():
            if pitcher_data.get('fullName','').lower() == player_name_normalized:
                pitcher = pitcher_data
        print('\n')
        keys = f"ERA: {pitcher['ERA']}   GB/FB: {pitcher['GB/FB']}   BB/9: {pitcher['BB/9']}"
        print(keys,'\n')
        
        #SIv, FBv (FAv), wSI/C, wFB/C, Pit+ CT (FC), Pit+ CB(CU)
        for key, value in pitcher.items():
            if '%' in key and key not in ['Contact%', 'Oppo%', 'Hard%', 'Pull%', 'Soft%', 'Zone%']:
                pitch_type = key.replace('%', '').replace('2', '').replace(' ', '')
                pitch_type_display = pitch_type if 'SI' not in pitcher else pitch_type.replace('FB', 'FA')
                pitch_percent = f"{round(value, 3):.3f}".ljust(6)
                pitch_type_internal = pitch_type.replace(' ', '')
                pitch_v = f"{pitcher.get(f'{pitch_type_internal}v', 0):.1f}".ljust(6)
                pitch_w_type = 'FB' if 'FB' in pitch_type else pitch_type
                pitch_w = f"{pitcher.get(f'w{pitch_w_type}/C', 0):.2f}".ljust(6)
                pitch_pit_type = 'FC' if 'CT' in pitch_type else 'CU' if 'CB' in pitch_type else 'FA' if 'FB' in pitch_type else 'FS' if 'SF' in pitch_type else pitch_type
                pitch_pit = f"{pitcher.get(f'Pit+ {pitch_pit_type}', 0):.1f}"
                print(f"{pitch_type_display}% {pitch_percent} {pitch_type_display}v {pitch_v} w{pitch_w_type}/C {pitch_w} Pit+ {pitch_pit_type} {pitch_pit}")


    if file_path:
        performance_data = {}
        df = pd.read_csv(file_path)
        print(df['team'].iloc[-1])
        for period in periods:
            hits, at_bats, average = calculate_stats(df, period)
            performance_data[period] = {'hits': hits, 'at_bats': at_bats, 'average': average}
        display_team_performance({player_name: performance_data}, periods)
        
    if index == 0:
        saved_ids[player_name_normalized] = bbref
        with open('players/ids.json','w') as file:
            json.dump(saved_ids,file)

          

def main():
    last_filters = []  # Variable to store the last entered filter criteria
    while True:
        year_option = input("Enter 'rolling' or nothing for a 1-year rolling average, 2023, 2024, 'last7' for the last 7 games, 'last30' for the last 30 games, or 'all' for all games: ")
        if year_option.lower() in ['rolling', 'last7', 'last30', 'all']:
            year = '2023+'
            break
        elif year_option.lower() in ['2023','2024']:
            year = year_option
            break
        elif year_option == '':
            year = '2023+'
            year_option = 'rolling'
            break
        else:
            print("Invalid option. Please enter 'rolling', 'last7', 'last30', or 'all'.")

    print("Selected year option:", year)

    directory = 'players/2023+/batter_gamelogs/' if year == '2023+' else f'players/{year}/batter_gamelogs/'
    player_records = {}
    rows = 150
    periods = [3, 5, 7]
    if year == '2023+':
        year_opt = '2024'
    else:
        year_opt = year
    with open(f'players/{year_opt}/batter_metadata.json','r') as bf:
        batters = json.load(bf)
    with open(f'players/{year_opt}/pitcher_metadata.json','r') as pf:
        pitchers = json.load(pf)
        
    while True:
        choice = input("\n1: Analyze player strategies\n2: Search and manage players\n3: Check strategies for today\n4: Hottest Hitters Tool\nc: Clear\nq: Quit: ")
        if choice == '1':
            files = [file for file in os.listdir(directory) if file.endswith('.csv') and not file.startswith('._')or file.startswith('_.')]
            team_option = input("(option) filter by team abbrv:")
            team_option = team_option.upper()
            while True:
                if team_option.lower() not in ['','all']:
                    team_players = get_team_players(directory, team_option)
                    files = [file for file in os.listdir(directory) if file.split('_')[-1].split('.')[0] in team_players.values()]
                else:
                    files = [file for file in os.listdir(directory) if file.endswith('.csv') and not file.startswith('._')]
               
                user_input = input("\n\nEnter filter criteria (e.g., 'position=C', 'xERA>5', separate by comma) or 'break' to exit: ")
                if user_input.lower() in ['break',' ','q','b']:
                    print("Exiting the program.")
                    break  # Exit the loop and end the program

                filters = [f.strip().replace('"', '').replace("'", "") for f in user_input.split(',')]

                for file in files:
                    if not file.startswith('._'):
                        if not file.startswith('_.'):
                            df = pd.read_csv(directory + file)
                            if year_option.lower() == 'rolling':
                                # Apply rolling 365-day date filter
                                df = df[df['date'].astype(str).apply(extract_year_from_date) >= (datetime.datetime.now() - datetime.timedelta(days=365)).year]
                            elif year_option.lower() == 'last7':
                                df = df.tail(7)
                            elif year_option.lower() == 'last30':
                                df = df.tail(30)
                            if df['ab'].sum() < 10: 
                                continue

                            try:
                                df_filtered = apply_filters(df, filters, year)
                                hits, no_hits, hit_percentage = calculate_hit_record(df_filtered)
                                player_name = '_'.join(file.split('_')[:-1])  # Get the full name
                                player_id = file.split('_')[-1].split('.')[0]
                                player_records[player_name] = {
                                    'player_id': player_id,
                                    'hits': hits,
                                    'no_hits': no_hits,
                                    'hit_percentage': hit_percentage
                                }
                            except KeyError as e:
                                print(f"Column {e} not found in file {file}. Skipping file.")
                                continue

                top_hit_sorted = sorted(player_records.items(), key=lambda item: item[1]['hits'], reverse=True)[:rows]
                final_sorted_by_percentage = sorted(top_hit_sorted, key=lambda item: item[1]['hit_percentage'], reverse=True)

                print("Players with the best hit records:\n\n")
                for name, record in final_sorted_by_percentage:
                    print(f"{name} : Hits: {record['hits']}, No Hits: {record['no_hits']}, Hit Record: {record['hit_percentage']:.2%}")

                last_filters = filters
                
        elif choice == '2':
            while True:
                user_input = input("\nSearch a player to see splits/strategies(ex. Luis Arraez): ")
                player_name_normalized = user_input.lower().replace(' ','')
                if user_input in ['break','b','Break','B','','q']:
                    break     
                if any(player['fullName'] == player_name_normalized for player in pitchers.values()):
                    splits(user_input,directory,year_opt,t='pitcher')
                elif any(player['fullName'] == player_name_normalized for player in batters.values()):
                    splits(user_input,directory,year_opt,t='batter')
                    player_name, player_id, file_path = search_player(directory, user_input)
                    while True:
                        strategy_input = input("\nEnter filter criteria for the player strategy or type 'q' to quit, 's' to save previous entry: ")
                        if strategy_input in ['','q']:
                            break
                        else:
                            if file_path:
                                df = pd.read_csv(file_path)
                                team = df.iloc[-1]['team']  # Get the latest team                            
                                if strategy_input.lower() == 's':
                                    if last_filters:
                                        results = {}
                                        for year in ['2023', '2024']:
                                            df_year = df[df['date'].str.contains(year)]
                                            df_filtered = apply_filters(df_year, last_filters, year)
                                            if not df_filtered.empty:
                                                hits, no_hits, hit_percentage = calculate_hit_record(df_filtered)
                                                results[year] = {
                                                    'hits': hits,
                                                    'no_hits': no_hits,
                                                    'hit_percentage': hit_percentage
                                                }
                                        
                                        if results:
                                            save_player_strategy(player_id, player_name, team, last_filters, results, year_option)
                                            print("Strategy saved for multiple years.")
                                        else:
                                            print("No valid data to save.")
                                    else:
                                        print("No strategy data to save. Apply a strategy first.")
                                    break  # Exit after saving or acknowledging the need for filters
                                else:
                                    filters = [f.strip().replace('"', '').replace("'", "") for f in strategy_input.split(',')]
                                    last_filters = filters
                                    apply_and_display_filters(df, filters)
                            else:
                                print("Player or team not found.")
                                
                        
        elif choice =='3':
            strategies.main()
            
        if choice == '4':
            directory = 'players/2024/batter_gamelogs'
            periods = [3, 5, 7]
            find_hottest_hitters(directory, periods)
                                
                  
        elif choice =='c':
            os.system('clear')
            
        elif choice == 'q':
            print("Exiting the program.")
            break
        elif choice == '':
            print("Exiting the program.")
            break



if __name__ == "__main__":
    main()

