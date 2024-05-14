from nba_api.stats.endpoints import playergamelog
from nba_api.stats.endpoints import leaguestandings
from nba_api.stats.endpoints import teamestimatedmetrics
from nba_api.stats.endpoints import boxscoreadvancedv3
from nba_api.stats.endpoints import commonplayerinfo
from nba_api.stats.endpoints import boxscoredefensivev2
from nba_api.stats.endpoints import boxscorehustlev2
from nba_api.stats.endpoints import boxscoremiscv3
from nba_api.stats.endpoints import boxscoreplayertrackv3
from nba_api.stats.endpoints import boxscoreusagev3
from nba_api.stats.endpoints import boxscorescoringv3
from nba_api.stats.endpoints import teamgamelog
from nba_api.stats.endpoints import leaguegamelog
from nba_api.stats.endpoints import boxscorematchupsv3
from nba_api.stats.endpoints import playbyplay
from nba_api.stats.endpoints import playbyplayv2
from nba_api.stats.endpoints import playbyplayv3
from nba_api.live.nba.endpoints import scoreboard
from nba_api.live.nba.endpoints import playbyplay as pbp_live


from json.decoder import JSONDecodeError
from requests.exceptions import ReadTimeout
from sklearn.preprocessing import StandardScaler
import numpy as np
import glob
import requests
import json
import re
import os
import time
import json
import pandas as pd
import fitz 
from scipy.stats import zscore
from datetime import datetime, timedelta
from bs4 import BeautifulSoup

'''
Three runs
1.
gamelogs

2.
Just
append averages to dict \ savematchups

3.
matchup meta to gamelog append
'''
class DataGetter:
    def __init__(self,execution='normal_run'):       
            if execution == 'normal_run':
                self.date = time.strftime('%m-%d-%Y')
                self.script_directory = os.path.dirname(os.path.abspath(__file__))

                #METADATA
                
                self.players = self.read_players()
                self.rosters = self.read_rosters()
                self.teams = self.read_teams()
                self.game_ids = self.read_gameids()
                self.todays_games = self.get_todays_games()
                self.season = '2023-24'
                self.getInjuries()
                
                self.initTensorKeys = self.init_tensor_keys()
                
                
                
                #self.scrape_and_update_players()
                #self.scrapePlayByPlay()
                #self.parse_back_to_back_games(save=True)
                #self.scrape_ratings()
                #print(self.players['Kristaps Porzingis'])
                
                #self.append_weighted_averages_to_gamelogs()
           
                
            
            if execution == 'run1':                
                self.date = time.strftime('%m-%d-%Y')
                self.season = '2023-24'
            
                self.game_ids = self.get_gameids()
                #self.rosters = self.read_rosters()
                self.teams = self.read_teams()
                #self.players = self.read_players()
                
               
                #GAMELOGS
                self.get_data(player_info_meta = True) #fetches original gamelogs and saves to dir || set player_info_meta to be True for each season
                                  #creates and updates the player_info dict
                self.scrape_and_update_players()
                self.game_ids = self.get_gameids()
               
                #AVERAGES
                self.home_averages_output_folder = 'players/averages/home/'
                self.away_averages_output_folder = 'players/averages/away/'
                self.combined_averages_output_folder = 'players/averages/combined/'
                self.calc_save_averages()              
                #DVPOS
                self.api_base_url = "https://api.fantasypros.com/v2/json/nba/team-stats-allowed/"
                self.timeframes = ['7', '15', '30']
                self.acquire_dvpos()
                #MEDIANS
                self.acquire_medians()
                
                
                
                #TEAM_METRICS
                self.combine_team_dfs()
               
                
                #PLAYER AND TEAM METRIC MERGER
                self.merge_teamplayer_data()
                
                #NBA API
                self.accessNBA_API_boxscores()

                #Update Player Game Logs
                self.add_boxscoregamelog()
                
                #PROPS
                #self.props_filename = f"props/{self.date}.txt"
                #self.prop_api_key = 'T0RyrHY6WpXU4FYcIGthiwbtBHe0VUHgIdc2VyDO3g'
                #self.prop_markets = ["player_points_over_under", "player_rebounds_over_under", "player_assists_over_under"]
                #self.prop_data = []
                #self.acquire_props(force_update = False)
                
                #TEAM STATS 
                self.get_teamStats()
                self.add_team_boxscoregamelog()
                self.parse_back_to_back_games(save=True)
                
                
                
                
            elif execution == 'run2':
                print('\nrun2\n append_averages_to_dict')
                self.date = time.strftime('%m-%d-%Y')
                self.players = self.read_players()
                self.rosters = self.read_rosters()
                self.teams = self.read_teams()
                self.game_ids = self.read_gameids()
                self.season = '2023-24'
                self.append_averages_todict()
                self.processTeamMeta()
                self.scrape_and_update_players()
                self.saveMatchups(mode='offense')
                self.saveMatchups(mode='defense')
                
                #self.scrapePlayByPlay()
            
                
              
           


                
    '''
    START
    '''
    def calculate_weighted_averages(self, df, performance_columns):
        """Calculate and return the weighted averages for specified columns."""
        df['TotalPossessionsByGame'] = df.groupby('Game_Id')['partialPossessions'].transform('sum')
        for col in performance_columns:
            weighted_col_name = f'Weighted_{col}'
            weighted_col_name = weighted_col_name.replace(' ','')
            df[weighted_col_name] = df[col] * df['partialPossessions'] / df['TotalPossessionsByGame']
        
        return df.groupby('Game_Id')[[f'Weighted_{col}'.replace(' ','') for col in performance_columns]].sum().reset_index()

    def append_weighted_averages_to_gamelogs(self):
        """Append weighted averages to player game logs and save the updated logs."""
        base_dir = 'players/gameMicro'
        game_logs_dir = 'players/gamelogs'
        updated_logs_dir = 'players/gamelogsv2'
        os.makedirs(updated_logs_dir, exist_ok=True)
        
        for mode in ['offense']:
            performance_columns = {
                #'defense': ['Player OBPM', 'Player DBPM', 'Player Height', 'Player Weight','Player Speed','Player Wingspan'],
                'offense': ['Opponent OBPM', 'Opponent DBPM',  'Opponent Height', 'Opponent Weight','Opponent Speed','Opponent Wingspan']
            }[mode]

            for player_name in self.players:
                matchup_file = f'{base_dir}/{mode}/{player_name}_matchups.csv'
                game_log_file = f'{game_logs_dir}/{player_name}_log.csv'
                updated_log_file = f'{updated_logs_dir}/{player_name}_log.csv'

                if not os.path.isfile(matchup_file) or not os.path.isfile(game_log_file):
                    continue

                matchups_df = pd.read_csv(matchup_file)
                game_log_df = pd.read_csv(game_log_file)

                if not all(col in matchups_df for col in ['Game_Id', 'partialPossessions'] + performance_columns):
                    print(f"Required columns missing in file: {matchup_file}")
                    continue
                
                weighted_averages_df = self.calculate_weighted_averages(matchups_df, performance_columns)
                weighted_averages_df = weighted_averages_df.rename(columns={'Game_Id': 'Game_ID'})
                
                # Merge and create 'Weighted_OpponentLength'
                updated_game_log_df = pd.merge(game_log_df, weighted_averages_df, on='Game_ID', how='left')
                updated_game_log_df['Weighted_OpponentLength'] = updated_game_log_df['Weighted_OpponentWingspan'] + updated_game_log_df['Weighted_OpponentHeight']
                
                # Save the updated DataFrame
                updated_game_log_df.to_csv(updated_log_file, index=False)
                print(f"Updated game log saved for {player_name} in {mode} mode.")

    def normalize_player_name(self, name):
        replacements = {'ā': 'a', 'ć': 'c', '.': '', ' Jr': '', ' Jr.': '','č':'c',' Sr':'','Š':'S','ģ':'g','ū':'u','ö':'o','š':'s','é':'e','ņ':'n'}
        for src, target in replacements.items():
            name = name.replace(src, target)
        return name.strip()

    def match_player_name(self, name):
        if name in self.players:
            return name
        
        if name == 'GG Jackson II':
            return 'GG Jackson'
        if name == 'Kevin Knox':
            return 'Kevin Knox II'
        if name + ' Jr' in self.players:
            return name + ' Jr'
        if name + ' III' in self.players:
            return name + ' III'
        if name + ' Sr' in self.players:
            return name + ' Sr'
        if name.endswith(' Jr') and name[:-3] in self.players:
            return name[:-3]
        
        return None

    def scrape_and_update_players(self, year=2024):
        # Assuming advanced stats and play-by-play are processed separately
        self.process_advanced_stats(year)
        self.process_play_by_play(year)
        self.process_wingspans()
        self.decode_positions()
        self.save_players()
        print('Complete')

    def decode_positions(self):
        for player, stats in self.players.items():
            position = stats.get('POSITION')
            if position:
                if 'Guard' in position and 'Forward' not in position:
                    stats['POSITION'] = 'Guard'
                
                elif 'Center' in position or 'Center-Forward' in position or 'Forward-Center' in position:
                    stats['POSITION'] = 'Big'
                    
                elif 'Forward' in position or 'Guard-Forward' in position or 'Forward-Guard' in position:
                    stats['POSITION'] = 'Wing'
                

        

    def process_wingspans(self):
        response = requests.get('https://craftednba.com/player-traits/length')
        if response.status_code == 200:
            soup = BeautifulSoup(response.content, 'html.parser')
            rows = soup.select('table.table tbody tr')  # Adjust the selector if needed
            for row in rows:
                name_td = row.select_one('td:nth-child(2)')  # Adjust according to actual nth-child if necessary
                wingspan_td = row.select_one('td:nth-child(4)')  # Adjust according to actual nth-child if necessary
                if name_td and wingspan_td:
                    full_text = name_td.text.strip()
                    player_name_org = ' '.join(full_text.split()[:-2])
                    player_name = player_name_org[:-3]
                    wingspan_text = wingspan_td.text.strip()
                    wingspan = self.wingspan_to_cm(wingspan_text.split('"')[0])  # Assuming the wingspan is followed by a quote
                    normalized_name = self.normalize_player_name(player_name)
                    matched_name = self.match_player_name(normalized_name)
                    if matched_name:
                        self.players[matched_name]['WINGSPAN'] = wingspan
                    else:
                        try:
                            self.players[player_name_org]['WINGSPAN'] = wingspan
                        except KeyError:
                            print(f'{player_name} addition failed for wingspan')
        else:
            print(f"Failed to retrieve wingspan data, status code: {response.status_code}")




    def process_advanced_stats(self, year):
        print('Advanced Stats0.0')
        url = f'https://www.basketball-reference.com/leagues/NBA_{year}_advanced.html'
        response = requests.get(url)
        if response.status_code == 200:
            soup = BeautifulSoup(response.content, 'html.parser')
            players = soup.select('#advanced_stats tbody tr[class!="thead"]')
            for player in players:
                player_name = self.normalize_player_name(player.select_one('[data-stat="player"]').text)
                obpm = float(player.select_one('[data-stat="obpm"]').text) 
                dbpm = float(player.select_one('[data-stat="dbpm"]').text)
                trb_pct = float(player.select_one('[data-stat="trb_pct"]').text)
                
                matched_name = self.match_player_name(player_name)
                if matched_name:
                    self.players[matched_name].update({'OBPM': obpm, 'DBPM': dbpm})
                else:
                    print(f"Name mismatch or not found in players: {player_name}")


    def process_play_by_play(self, year):
        print('Play By Play0.1')
        url = f'https://www.basketball-reference.com/leagues/NBA_{year}_play-by-play.html'
        response = requests.get(url)
        if response.status_code == 200:
            soup = BeautifulSoup(response.content, 'html.parser')
            players = soup.select('#pbp_stats tbody tr[class!="thead"]')
            for player in players:
                player_name = self.normalize_player_name(player.select_one('[data-stat="player"]').text)
                shooting_fouls = int(player.select_one('[data-stat="fouls_shooting"]').text)
                shooting_fouls_drawn = int(player.select_one('[data-stat="drawn_shooting"]').text)
                pts_generated_byast = int(player.select_one('[data-stat="astd_pts"]').text)
                and1 = int(player.select_one('[data-stat="and1s"]').text)
                mp = int(player.select_one('[data-stat="mp"]').text)
                g = int(player.select_one('[data-stat="g"]').text)
                
                shootingFouls_min = round(shooting_fouls / mp,2)
                ptsGenAst_min = round(pts_generated_byast / mp,2)
                
                
                matched_name = self.match_player_name(player_name)
                if matched_name:
                    self.players[matched_name].update({'and1_total':and1,'shotFoulsCommited_total':shooting_fouls,'shotFoulsDrawn_total':shooting_fouls_drawn,'shotFoulsCommited_min': shootingFouls_min,'ptsGeneratedByAst_min':ptsGenAst_min})
                else:
                    print(f"Name mismatch or not found in players: {player_name}")


    def save_players(self):
        file_path = 'players/player_json/player_info.json'
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        with open(file_path, 'w') as file:
            json.dump(self.players, file, indent=4)

               
    def wingspan_to_cm(self, wingspan):
        feet, inches = map(float, wingspan.replace('"', '').split("'"))
        return round((feet * 30.48) + (inches * 2.54), 2)
               
               

    def get_todays_games(self):
        return scoreboard.ScoreBoard().games.get_dict()
    
    def read_players(self,backup=False):
        dir_path = os.path.dirname(os.path.realpath(__file__))
        if backup != True:
            json_path = os.path.join(dir_path, 'players/player_json/player_info.json')
            with open(json_path) as json_file:
                file = json.load(json_file)
                return file
        else:
            json_path = os.path.join(dir_path, 'players/player_json/backup_player_info.json')
            with open(json_path) as json_file:
                file = json.load(json_file)
                return file

    def read_gameids(self):
        game_ids = []
        file_path = 'games/metadata/game_ids.txt'
        try:
            with open(file_path, 'r') as file:
                for line in file:
                    game_id = line.strip()
                    game_ids.append(game_id)
        except FileNotFoundError:
            print(f"Error: File '{file_path}' not found.")
        except Exception as e:
            print(f"An error occurred: {e}")

        return game_ids
        
    def get_gameids(self):
        game_ids = []
        for filename in os.listdir('players/gamelogs/'):
            file_path = f'players/gamelogs/{filename}'
            if '._' not in file_path:
                try:
                    player_df = pd.read_csv(file_path,delimiter=',')
                    # Use extend to add all Game_ID values to the game_ids list
                    game_ids.extend(player_df['Game_ID'])
                except KeyError:
                    try:
                        player_df = pd.read_csv(file_path,delimiter = '\t')
                        # Use extend to add all Game_ID values to the game_ids list
                        game_ids.extend(player_df['Game_ID'])
                    except KeyError:
                        pass
        
        #game_ids contains every unique Game_ID
        game_ids = list(set(game_ids))
        with open('games/metadata/game_ids.txt','w') as f:
            for item in game_ids:
                f.write(f'{item}\n')
                
        return game_ids
    
    
    
    
    
    def read_rosters(self):
        team_rosters = {}

        for player_name, player_info in self.players.items():
            player_id = player_info['id']
            team_abbreviation = player_info['TEAM_ABBREVIATION']
            team_id = player_info['TEAM_ID']
            position = player_info['POSITION']

            if team_abbreviation:
                player_data = {
                    'id': player_id,
                    'TEAMID': team_id,
                    'POSITION': position
                }

                # Add the player to the corresponding team in the team_rosters dictionary
                if team_abbreviation not in team_rosters:
                    team_rosters[team_abbreviation] = {}
                team_rosters[team_abbreviation][player_name] = player_data

        with open('teams/metadata/rosters/team_rosters.json', 'w') as file:
            json.dump(team_rosters, file)

        return team_rosters
    
    '''
    GAMELOGS (1)
    '''
    
    def build_player_dict(self):
        directory = 'games/2023-24/'
        player_dict = {}
        print('building player dict')
        for filepath in glob.glob(os.path.join(directory, '**/player_BoxScores.csv'), recursive=True):
            df = pd.read_csv(filepath)
            for _, row in df.iterrows():
                player_id = row['personId']
                full_name = f"{row['firstName']} {row['familyName']}"
                full_name = full_name.replace('.','')
                
                if full_name not in player_dict or player_dict[full_name]['id'] != player_id:
                    player_dict[full_name] = {"id": player_id}

        # Save the dictionary to a file
        with open('players/player_json/player_info.json', 'w') as file:
            json.dump(player_dict, file)
        
        return player_dict

    def player_meta(self, build_player_dict=True):
        if build_player_dict:  # only when updaing player_info json
            self.players = self.build_player_dict()
        else:
            self.players = self.read_players()

        retry_count = 3
        retry_delay = 5
        length = len(self.players)
        count = 0

        for player, attr in self.players.items():
            count += (1/length)
            print(f"{count*100:.2f} % -player meta")
            player_id = attr['id']

            for attempt in range(retry_count):
                try:
                    player_info = commonplayerinfo.CommonPlayerInfo(player_id)
                    break
                except ReadTimeout:
                    if attempt < retry_count - 1:
                        print(f"Timeout for {player}. Retrying {attempt + 1}/{retry_count} after {retry_delay} seconds...")
                        time.sleep(retry_delay)
                    else:
                        print(f"Failed to retrieve data for {player} after {retry_count} attempts.")
                        continue  # Skip to the next player after all retries

            meta = player_info.common_player_info.get_data_frame()
            selected_columns = ['HEIGHT', 'WEIGHT', 'BIRTHDATE', 'SEASON_EXP', 'TEAM_ID', 'TEAM_ABBREVIATION', 'POSITION', 'ROSTERSTATUS']
            for column in selected_columns:
                value = str(meta[column].iloc[0])
                try:
                    if column == 'HEIGHT':
                        feet, inches = value.split('-')
                        value = int(feet) * 30.48 + int(inches) * 2.54  # Convert to cm
                        value = round(value, 2)
                    if column == 'WEIGHT':
                        value = float(value)
                    if column == 'BIRTHDATE' and 'T' in str(value):
                        value = value.split('T')[0]
                except ValueError:
                    pass
                attr[column] = value


            time.sleep(1)  # Delay between processing each player

        with open('players/player_json/player_info.json', 'w') as file:
            json.dump(self.players, file)            
        with open('players/player_json/backup_player_info.json', 'w') as file:
            json.dump(self.players, file)
            

        print('Player meta completed (0)')
        return self.players

    
    def fetch_player_game_logs(self, player_id, season):
        try:
            game_logs = playergamelog.PlayerGameLog(player_id=player_id, season=season)
            logs_df = game_logs.get_data_frames()[0]
            logs_df = logs_df.rename(columns={'FG3M': '3PM'})
            return logs_df
        except Exception as e:
            return f"Error: {e}"
        
        
    def get_data(self, player_info_meta = False):
        if player_info_meta == True:
            self.players = self.player_meta()
        else:
            self.players = self.read_players()
        
        print('(1) getting gamelogs')
        percentage = 0
        for player, info in self.players.items():
            player_id = info['id']
            time.sleep(0.5)  # Be cautious with using time.sleep in production code
            result = self.fetch_player_game_logs(player_id, '2023-24')
            
            if isinstance(result, pd.DataFrame):
                self.create_cols(result)
                result.to_csv(f"players/gamelogs/{player}_log.csv", sep='\t', index=False)
                percentage += (1/len(self.players))
                print(round(percentage,4),' % - gamelog getter')
            else:
                print(f"Error fetching data for {player}: {result}")
        self.scrape_and_update_players()
        print('Finished player_game_log getter and scraped box+-(1)')
        
    def create_cols(self,result):
        result[['Team', 'Location', 'Opponent']] = result['MATCHUP'].str.extract(r'([A-Z]+) ([@vs.]+) ([A-Z]+)')
        result['PR'] = result['PTS'] + result['REB']
        result['PA'] = result['PTS'] + result['AST']
        result['AR'] = result['AST'] + result['REB']
        result['PRA'] = result['PTS'] + result['REB'] + result['AST']
        return result
    
    '''
    AVERAGES (2)
    '''
    
    def calculate_and_save_averages(self, file_path, game_type):
       
        current_data = pd.read_csv(file_path, delimiter='\t')
        selected_columns = ['MIN', 'FGM', 'FGA', '3PM', 'FG3A', 'FTM', 'FTA', 'REB', 'AST', 'STL', 'BLK', 'PTS', 'PLUS_MINUS']

        if game_type == 'home':
            filtered_data = current_data[current_data['MATCHUP'].str.contains('vs.')]
            output_folder = 'players/averages/home/'
        elif game_type == 'away':
            filtered_data = current_data[current_data['MATCHUP'].str.contains('@')]
            output_folder = 'players/averages/away/'
        else:
            filtered_data = current_data  # For combined, use all data
            output_folder = 'players/averages/combined/'

        column_averages = filtered_data[selected_columns].mean().round(2)
        averages_df = pd.DataFrame([column_averages], columns=selected_columns)
        averages_output_file_path = os.path.join(output_folder, os.path.basename(file_path))
        averages_df.to_csv(averages_output_file_path, index=False)

    def calc_save_averages(self):
        print('average getter')
        for filename in os.listdir('players/gamelogs/'):
            file_path = f'players/gamelogs/{filename}'
            if '._' not in file_path:
                try:
                    self.calculate_and_save_averages(file_path, 'home')
                    self.calculate_and_save_averages(file_path, 'away')
                    self.calculate_and_save_averages(file_path, 'combined')
                except TypeError:
                    pass
                except KeyError:
                    pass
        print('Player home, away, and combined averages calculation complete (2)')
        
    def append_averages_todict(self): #Appends player attributes to themselves
        players_to_remove = []
        
        
        #STATIC Attributes
        for player, attr in self.players.items():
            try:
                df = pd.read_csv(f'players/gamelogs/{player}_log.csv')
                
                
               
                # meta
                self.players[player]['AVG_MIN'] = round(df['MIN'].mean(), 2)
                self.players[player]['AVG_PACE'] = round(df['pace'].mean(), 2)
                self.players[player]['AVG_SPEED'] = round(df['speed'].mean(), 2)
                self.players[player]['AVG_DISTANCE'] = round(df['distance'].mean(), 2)
                self.players[player]['AVG_POSSESSIONS'] = round(df['possessions'].mean(), 2)
                self.players[player]['AVG_REB_PCT'] = round(df['reboundPercentage'].mean(), 2)
                self.players[player]['AVG_REB_CHANCES'] = round(df['reboundChancesTotal'].mean(), 2)
                self.players[player]['AVG_REB'] = round(df['REB'].mean(), 2)
                
                self.players[player]['POSS_REB_CHANCES'] = round((df['reboundChancesTotal'] / df['possessions']).mean(), 2)
                self.players[player]['OFF_AVG_PTS'] = round(df['PTS'].mean(), 2)
                self.players[player]['OFF_AVG_AST'] = round(df['AST'].mean(), 2)
                self.players[player]['OFF_AVG_FGA'] = round(df['FGA'].mean(), 2)
                self.players[player]['OFF_AVG_3PA'] = round(df['FG3A'].mean(), 2)
                self.players[player]['OFF_AVG_OREB_PCT'] = round(df['offensiveReboundPercentage'].mean(), 2)
                self.players[player]['OFF_AVG_PTS_PAINT'] = round(df['pointsPaint'].mean(), 2)
                self.players[player]['OFF_AVG_OFF_RATING'] = round(df['offensiveRating'].mean(), 2)
                self.players[player]['OFF_AVG_USG_PCT'] = round(df['estimatedUsagePercentage'].mean(), 2)
                self.players[player]['OFF_AVG_TOUCHES'] = round(df['touches'].mean(), 2)
                self.players[player]['OFF_AVG_PASSES'] = round(df['passes'].mean(), 2)
                self.players[player]['OFF_AVG_TOV'] = round(df['TOV'].mean(), 2)
                
                self.players[player]['OFF_POSS_PTS'] = round((df['PTS'] / df['possessions']).mean(), 2)
                self.players[player]['OFF_POSS_AST'] = round((df['AST'] / df['possessions']).mean(), 2)
                self.players[player]['OFF_POSS_REB'] = round((df['REB'] / df['possessions']).mean(), 2)
              
                self.players[player]['DEF_AVG_PTS'] = round(df['oppPoints'].mean(),2)
                self.players[player]['DEF_POSS_PTS'] = round((df['oppPoints'] / df['possessions']).mean(),2)
                self.players[player]['DEF_AVG_AST'] = round((df['matchupAssists'] / df['possessions']).mean(),2)
                
                
            except FileNotFoundError:
                print(player,'File N/A Error')
        
            except KeyError:
                print(player,'Key Error..Removed')
                players_to_remove.append(player)
        
        
        
                
        for player, stats in self.players.items():
            excluded_keys = ['HEIGHT', 'WEIGHT', 'BIRTHDATE', 'SEASON_EXP','TEAM_ID','TEAM_ABBREVIATION','POSITION','ROSTERSTATUS']  # Add any keys you don't want to change
            inf_values = {key: value if (np.isreal(value) and not np.isinf(value)) or key in excluded_keys else 0 for key, value in stats.items()}
            self.players[player] = inf_values
                
        for player_to_remove in players_to_remove:
            del self.players[player_to_remove]
        
                
        with open('players/player_json/player_info.json', 'w') as file:
            json.dump(self.players, file)
            
            #again, ir pd read csv, player meta
            #which has the players custom ratings. Ie player total score, offense/defense score, matchup vs bigger/smaller and lighter/heavier opponents, score
        
        
    '''
    DEFENSE VS POSITION
    '''
    
    def fetch_and_save_dvpos(self, timeframe):
        filename = f"players/defense_vpos/team_defense_vpos_{timeframe}.json"
        params = {'range': timeframe}
        dvpos_headers = {
            'x-api-key': 'CHi8Hy5CEE4khd46XNYL23dCFX96oUdw6qOt1Dnh'  # Be cautious with API keys in code
        }
        response = requests.get(self.api_base_url, headers=dvpos_headers, params=params)

        if response.status_code == 200:
            with open(filename, 'w') as file:
                json.dump(response.json(), file, indent=4)
            #print(f"Data for timeframe {timeframe} saved to {filename}.")
        else:
            print(f"Failed to fetch data for timeframe {timeframe}. Status code: {response.status_code}")

    def acquire_dvpos(self):
        for timeframe in self.timeframes:
            self.fetch_and_save_dvpos(timeframe)
        print("team defense v pos complete (3)")
    
    '''
    MEDIANS (4)
    '''

    def calculate_and_save_medians(self, file_path, game_type):
        current_data = pd.read_csv(file_path, delimiter='\t')
        selected_columns = ['MIN', 'FGM', 'FGA', '3PM', 'FG3A', 'FTM', 'FTA', 'REB', 'AST', 'STL', 'BLK', 'PTS', 'PLUS_MINUS']
        try:
            if game_type == 'home':
                filtered_data = current_data[current_data['MATCHUP'].str.contains('vs.')]
                output_folder = 'players/medians/home/'
            elif game_type == 'away':
                filtered_data = current_data[current_data['MATCHUP'].str.contains('@')]
                output_folder = 'players/medians/away/'
            else:
                filtered_data = current_data  # For combined, use all data
                output_folder = 'players/medians/combined/'

            column_medians = filtered_data[selected_columns].median().round(2)
            medians_df = pd.DataFrame([column_medians], columns=selected_columns)
            medians_output_file_path = os.path.join(output_folder, os.path.basename(file_path))
            medians_df.to_csv(medians_output_file_path, index=False)
        except KeyError:
            pass

    def acquire_medians(self):
        for filename in os.listdir('players/gamelogs/'):
            file_path = f'players/gamelogs/{filename}'
            if '._' not in file_path:
                try:
                    self.calculate_and_save_medians(file_path, 'home')
                    self.calculate_and_save_medians(file_path, 'away')
                    self.calculate_and_save_medians(file_path, 'combined')
                except TypeError:
                    pass
        print('Player home, away, and combined medians calculation complete (4)')

    '''
    PROPS (5)
    '''

    def fetch_game_ids_for_props(self):
        api_date = time.strftime("%Y-%m-%d")
        
        game_endpoint = f"https://api.prop-odds.com/beta/games/nba?date={api_date}&tz=America/New_York&api_key={self.prop_api_key}"
        response = requests.get(game_endpoint)
        if response.status_code == 200:
            data = response.json()
            game_ids = [game["game_id"] for game in data["games"]]
            with open('props/game_ids.txt', 'w') as file:
                json.dump(game_ids, file)  # Provide the file pointer as the first argument
            return game_ids
        else:
            print(f"Failed to fetch game IDs. Status code: {response.status_code}")
            return []


    def fetch_prop_data_for_game(self, game_id):
        for market in self.prop_markets:
            market_endpoint = f'https://api.prop-odds.com/beta/odds/{game_id}/{market}?api_key={self.prop_api_key}'
            resp = requests.get(market_endpoint)
            if resp.status_code == 200:
                market_data = resp.json()['sportsbooks'][2]['market']
                self.prop_data.append(market_data)

    def save_data_to_file(self):
        with open(self.props_filename, 'w') as file:
            json.dump(self.prop_data, file, indent=4)

    def acquire_props(self, force_update=False):
        if not os.path.exists(self.props_filename) or force_update:
            game_ids = self.fetch_game_ids_for_props()
            for game_id in game_ids:
                self.fetch_prop_data_for_game(game_id)
            if self.prop_data:
                self.save_data_to_file()
                print(f"Prop data saved to {self.props_filename}")
            print('Props acquisition complete (5)')
        else:
            print(f"Odds file already exists: {self.props_filename}")
        
    '''
    TEAM METRICS (7)
    '''
    
    def get_team_standings(self):
        standings = leaguestandings.LeagueStandings().get_data_frames()[0]
        standings['TEAM_NAME'] = standings['TeamCity'] + ' ' + standings['TeamName']
        standings = standings.loc[:, ['TEAM_NAME','Conference','Division','WinPCT','HOME','ROAD','PointsPG','OppPointsPG','DiffPointsPG']]
        cols_to_zscore = ['WinPCT','PointsPG','OppPointsPG','DiffPointsPG']
        standings[cols_to_zscore] = zscore(standings[cols_to_zscore])
        
        return standings

    def get_team_metrics(self):
        team_metrics = teamestimatedmetrics.TeamEstimatedMetrics().get_data_frames()[0]
        team_metrics = team_metrics.loc[:, ['TEAM_NAME','W_PCT','E_OFF_RATING','E_DEF_RATING','E_NET_RATING','E_PACE','E_REB_PCT','E_TM_TOV_PCT']]    
        cols_to_zscore = ['W_PCT','E_OFF_RATING','E_DEF_RATING','E_NET_RATING','E_PACE','E_REB_PCT','E_TM_TOV_PCT']
        team_metrics[cols_to_zscore] = zscore(team_metrics[cols_to_zscore])
        team_metrics['E_DEF_RATING'] = -1 * team_metrics['E_DEF_RATING']      
        
        return team_metrics


    def combine_team_dfs(self):
        team_standings = self.get_team_standings()
        team_metrics = self.get_team_metrics()  
        team_data = pd.merge(team_standings, team_metrics, on = 'TEAM_NAME')
        self.abbreviation(team_data)
        team_data.to_csv('teams/metadata/team_data_zscore.csv', index=False)
        print('Team Metrics complete (7)')
    
    def abbreviation(self, df):
        key = {
            'ATL': 'Atlanta Hawks', 'BOS': 'Boston Celtics', 'BKN': 'Brooklyn Nets', 'CHA': 'Charlotte Hornets',
            'CHI': 'Chicago Bulls', 'CLE': 'Cleveland Cavaliers', 'DAL': 'Dallas Mavericks', 'DEN': 'Denver Nuggets',
            'DET': 'Detroit Pistons', 'GSW': 'Golden State Warriors', 'HOU': 'Houston Rockets', 'IND': 'Indiana Pacers',
            'LAC': 'LA Clippers', 'LAL': 'Los Angeles Lakers', 'MEM': 'Memphis Grizzlies', 'MIA': 'Miami Heat',
            'MIL': 'Milwaukee Bucks', 'MIN': 'Minnesota Timberwolves', 'NOP': 'New Orleans Pelicans', 'NYK': 'New York Knicks',
            'OKC': 'Oklahoma City Thunder', 'ORL': 'Orlando Magic', 'PHI': 'Philadelphia 76ers', 'PHX': 'Phoenix Suns',
            'POR': 'Portland Trail Blazers', 'SAC': 'Sacramento Kings', 'SAS': 'San Antonio Spurs', 'TOR': 'Toronto Raptors',
            'UTA': 'Utah Jazz', 'WAS': 'Washington Wizards'
        }
        df['Team'] = df['TEAM_NAME'].map({v: k for k, v in key.items()})
        return df
    
    '''
    PLAYER AND TEAM METRIC MERGER (8)
    '''
    def merge_teamplayer_data(self):
        team_metrics = pd.read_csv('teams/metadata/team_data_zscore.csv')
        for filename in os.listdir('players/gamelogs/'):
            file_path = os.path.join('players/gamelogs/', filename)
            if '._' or '_.' not in filepath:
                try:
                    player_log = pd.read_csv(file_path,delimiter='\t')
                    for index, row in player_log.iterrows():
                        team_data = team_metrics[team_metrics['Team'] == row['Opponent']] 
                        for col in ['W_PCT','E_OFF_RATING','E_DEF_RATING','E_NET_RATING','E_PACE','E_REB_PCT']:
                            if not team_data.empty:
                                player_log.at[index, col] = team_data.iloc[0][col]
            
                    player_log.to_csv(file_path, index=False)

                    
                except UnicodeDecodeError:
                    pass
                
                except KeyError as e:
                    try:
                        player_log = pd.read_csv(file_path)
                        for index, row in player_log.iterrows():
                            team_data = team_metrics[team_metrics['Team'] == row['Opponent']] 
                            for col in ['W_PCT','E_OFF_RATING','E_DEF_RATING','E_NET_RATING','E_PACE','E_REB_PCT']:
                                if not team_data.empty:
                                    player_log.at[index, col] = team_data.iloc[0][col]
                
                        player_log.to_csv(file_path, index=False)
                        print('option 2 complete')
                        
                    except UnicodeDecodeError:
                        pass
                    except KeyError as e:
                        print(f'error{filename} {e}')
                
           
        print('Player and Team Metric Merger complete (8)')


    
    
    '''
    NBA API (9)
    '''
    
    def clean_df(self, df, t):
        columns_to_drop = [col for col in df.columns if '_x' in col or '_y' in col or '_x_x' in col or '_y_x' in col or '_x_y' in col or '_y_y' in col]
        dataframe = df.drop(columns=columns_to_drop)
        dataframe.rename(columns={'playerPoints': 'oppPoints'}, inplace=True)
        
        if t == 'player_df':
            for index, row in dataframe.iterrows():
                player_name = (dataframe.loc[index, 'firstName'] + ' ' + dataframe.loc[index, 'familyName']).replace('.', '')
                dataframe.loc[index, 'Player Name'] = player_name
                
                # Set default values before trying to update them
                dataframe.loc[index, 'Player Height'] = 0
                dataframe.loc[index, 'Player Weight'] = 0
                dataframe.loc[index, 'True Position'] = '0'
                
                # Attempt to update values if player_name exists in self.players
                dataframe['True Position'] = dataframe['True Position'].astype('string')
                player_info = self.players.get(player_name, {})
                dataframe.loc[index, 'Player Height'] = player_info.get('HEIGHT', 0)
                dataframe.loc[index, 'Player Weight'] = player_info.get('WEIGHT', 0)
                dataframe.loc[index, 'True Position'] = player_info.get('POSITION', '0')
                    
        return dataframe
                
        
    def accessNBA_API_boxscores(self):
        file_path = 'games/2023-24'
        retry_count = 3
          
        count = 0
        games_failed = 0
        
        for gameid in self.game_ids:
            gameid = f'00{gameid}'
            retry_delay = 3
            if os.path.exists(f'{file_path}/{gameid}'):
                print('Access NBAAPI boxscores Game exists: ',gameid, 'Count: ',count)
                count += (1/len(self.game_ids))
                pass
            else:
                for attempt in range(retry_count):
                    try:
                        count += (1/len(self.game_ids))
                        time.sleep(0.5)  # Increasing the delay
                        
                        HUSTLE = boxscorehustlev2.BoxScoreHustleV2(game_id = gameid)
                        DEFENSIVE = boxscoredefensivev2.BoxScoreDefensiveV2(game_id = gameid)
                        ADVANCED = boxscoreadvancedv3.BoxScoreAdvancedV3(game_id=gameid)
                        MISC = boxscoremiscv3.BoxScoreMiscV3(game_id=gameid)
                        TRACK = boxscoreplayertrackv3.BoxScorePlayerTrackV3(game_id=gameid)
                        USAGE = boxscoreusagev3.BoxScoreUsageV3(game_id=gameid)
                        SCORING = boxscorescoringv3.BoxScoreScoringV3(game_id=gameid)
                
                        player_hustle_stats = HUSTLE.player_stats.get_data_frame()
                        player_defensive_stats = DEFENSIVE.player_stats.get_data_frame()
                        player_advanced_stats = ADVANCED.player_stats.get_data_frame()
                        player_misc_stats = MISC.player_stats.get_data_frame()
                        player_track_stats = TRACK.player_stats.get_data_frame()
                        player_usage_stats = USAGE.player_stats.get_data_frame()
                        player_scoring_stats = SCORING.player_stats.get_data_frame()
                        team_hustle_stats = HUSTLE.team_stats.get_data_frame()
                        team_advanced_stats = ADVANCED.team_stats.get_data_frame()
                        team_misc_stats = MISC.team_stats.get_data_frame()
                        team_track_stats = TRACK.team_stats.get_data_frame()
                        team_usage_stats = USAGE.team_stats.get_data_frame()
                        team_scoring_stats = SCORING.team_stats.get_data_frame()
                        
                        
                        player_df1 = pd.merge(player_hustle_stats,player_defensive_stats, on = 'personId',how = 'outer')
                        player_df2 = pd.merge(player_advanced_stats,player_misc_stats, on = 'personId',how = 'outer')
                        player_df3 = pd.merge(player_track_stats,player_usage_stats, on = 'personId',how = 'outer')
                        player_df = pd.merge(player_df1,player_scoring_stats, on = 'personId',how = 'outer')
                        player_df = pd.merge(player_df,player_df2, on = 'personId',how = 'outer')
                        player_df = pd.merge(player_df,player_df3, on = 'personId',how = 'outer')
                        team_df1 = pd.merge(team_hustle_stats,team_advanced_stats, on = 'teamId',how='outer')
                        team_df2 = pd.merge(team_misc_stats,team_track_stats, on = 'teamId',how='outer')
                        team_df3 = pd.merge(team_usage_stats, team_scoring_stats, on = 'teamId',how='outer')
                        team_df = pd.merge(team_df1, team_df2, on = 'teamId',how='outer')
                        team_df = pd.merge(team_df, team_df3, on = 'teamId',how='outer')
                        
                        
                        print(gameid)
                        player_df = self.clean_df(player_df,t='player_df')
                        team_df = self.clean_df(team_df,t='team_df')
                        
                        
                        
                        os.makedirs(os.path.join(file_path, gameid), exist_ok=True)
                        if player_df is not dict:
                            with open(f'{file_path}/{gameid}/player_BoxScores.csv', 'w') as playerdf_file:
                                player_df.to_csv(playerdf_file, index=False)
                        
                        if team_df is not dict:
                            with open(f'{file_path}/{gameid}/team_BoxScores.csv', 'w') as teamdf_file:
                                team_df.to_csv(teamdf_file, index=False)
                          
                        print(f'{gameid}: ',count,'Success!')
                        break
                    
                    except ReadTimeout:
                        print(f"Timeout for game ID {gameid}, attempt {attempt + 1}/{retry_count}. Retrying after {retry_delay} seconds...")
                        time.sleep(retry_delay)
                    except AttributeError as e:
                        games_failed += 1
                        print('Game_ID failed: ',gameid,e)
                    except JSONDecodeError:
                        pass
                    
                    
                    
                    
                    
                
        print('Games Failed',games_failed)
        print('Game boxscores saved (9)')

    def add_boxscoregamelog(self):
        print('Concatenating player gamelogs and boxscores')
        for filename in os.listdir('players/gamelogs/'):
            file_path = os.path.join('players/gamelogs/', filename)
            if '._' or '_.' not in filepath:
                try:
                    all_rows = []
                    player_log = pd.read_csv(file_path)
                    for index, row in player_log.iterrows():
                        gameid = row['Game_ID']
                        gameid = f'00{gameid}'
                        playerid = row['Player_ID']
                        
                        game_path = f'games/2023-24/{gameid}/player_BoxScores.csv'
                        if os.path.exists(game_path):
                            game = pd.read_csv(game_path)
                            matching_game_row = game[game['personId'] == playerid]

                            if not matching_game_row.empty:
                                merged_row = pd.merge(row.to_frame().T, matching_game_row, left_on='Player_ID', right_on='personId', how='left')
                                all_rows.append(merged_row)
                            else:
                                print(f"No matching row for Player_ID {playerid} in game {gameid}")
                        else:
                            #print(f"Game file not found: {game_path}")
                            pass

                    if all_rows:
                        final_df = pd.concat(all_rows, ignore_index=True)
                        final_df.to_csv(file_path,index=False)
                    else:
                        print(f"No data to concatenate for file {filename}")

                except TypeError as e:
                    print(f"KeyError processing file {filename}: {e}")
                except UnicodeDecodeError:
                    pass
        print('Gamelog and box scores concatenated! (10)')
        
    def read_teams(self):
        dir_path = os.path.dirname(os.path.realpath(__file__))
        json_path = os.path.join(dir_path, 'teams/metadata/NBA_TeamIds.json')
        with open(json_path) as json_file:
            return json.load(json_file)
        
    def get_teamStats(self):
        directory = 'teams/games/gamelogs'
        if not os.path.exists(directory):
            os.makedirs(directory)
            
        league_gamelog = leaguegamelog.LeagueGameLog(season=self.season).league_game_log.get_data_frame()

        time.sleep(0.5)
        for team, attr in self.teams.items():
            teamid = attr['id']
            team_abbreviation = team
            time.sleep(0.5)
            team_gamelog = teamgamelog.TeamGameLog(season=self.season, team_id=teamid).get_data_frames()[0]
            league_gamelog_filtered = league_gamelog[league_gamelog['TEAM_ABBREVIATION'] != team_abbreviation]
            merged_gamelog = team_gamelog.merge(league_gamelog_filtered, left_on='Game_ID', right_on='GAME_ID', suffixes=('', '_opponent'))

            merged_gamelog['Point_Diff'] = merged_gamelog['PTS'].astype(int) - merged_gamelog['PTS_opponent'].astype(int)
            merged_gamelog['Blowout'] = merged_gamelog['Point_Diff'].apply(lambda x: abs(x) >= 15)
            
            blowout_games = merged_gamelog['Blowout'].sum()
            total_games = len(merged_gamelog)
            blowout_rate = round(((blowout_games / total_games)*100),2)
            

            
            filename = f"{directory}/{team}.csv"
            merged_gamelog.to_csv(filename, index=False)
           

    def add_cols(self,df):
        df['TCHS_MIN'] = (df['touches'] / df['MIN'])
        df['PASSES_MIN'] = (df['passes'] / df['MIN'])
        df['REB_CHANCES_MIN'] = (df['reboundChancesTotal'] / df['MIN'])
        df['POSS_MIN'] = (df['possessions'] / df['MIN'])
        df['PTSPAINT_MIN'] = (df['pointsPaint'] / df['MIN'])
        
        df['opp_PTSPAINT_MIN'] = (df['oppPointsPaint'] / df['MIN'])
        
        return df
    
    def add_team_boxscoregamelog(self):
        print('Concatenating team gamelogs and boxscores')
        for filename in os.listdir('teams/games/gamelogs/'):
            file_path = os.path.join('teams/games/gamelogs/', filename)
            if '._' or '_.' not in filepath:
                try:
                    all_rows = []
                    team_log = pd.read_csv(file_path)
                    for index, row in team_log.iterrows():
                        gameid = row['Game_ID']
                        gameid = f'00{gameid}'
                        teamid = row['Team_ID']
                        
                        game_path = f'games/2023-24/{gameid}/team_BoxScores.csv'
                        if os.path.exists(game_path):
                            game = pd.read_csv(game_path)
                            matching_game_row = game[game['teamId'] == teamid]

                            if not matching_game_row.empty:
                                merged_row = pd.merge(row.to_frame().T, matching_game_row, left_on='Team_ID', right_on='teamId', how='left')
                                all_rows.append(merged_row)
                            else:
                                print(f"No matching row for Team_ID {teamid} in game {gameid}")
                        else:
                            print(f"Game file not found: {game_path}")
                            pass

                    if all_rows:
                        final_df = pd.concat(all_rows, ignore_index=True)
                        final_df = self.add_cols(final_df)
                        
                        final_df.to_csv(file_path,index=False)
                    else:
                        print(f"No data to concatenate for file {filename}")

                except TypeError as e:
                    print(f"KeyError processing file {filename}: {e}")
                except UnicodeDecodeError:
                    pass
        print('Gamelog and box scores concatenated! (11)')
    
    def getInjuries(self):
        site_url = 'https://www.rotowire.com/basketball/tables/injury-report.php'
        params = {'team': 'ALL', 'pos': 'ALL'}
        site_response = requests.get(site_url, params=params)
        inj_json = site_response.json()

        for player in inj_json:
            original_player_name = player['player']
            team, injury, status = player['team'], player['injury'], player['status']

            clean_player_name = original_player_name.replace('.', '')
            if team in self.rosters and clean_player_name in self.rosters[team]:
                if 'Out' in status:
                    self.rosters[team].pop(clean_player_name)
            else:
                player_name_with_jr = original_player_name + ' Jr'
                if team in self.rosters and player_name_with_jr in self.rosters[team]:
                    if 'Out' in status:
                        self.rosters[team].pop(player_name_with_jr)

    def determine_opp_method(self, partial_possessions):
        if partial_possessions > 25:
            return '1'
        elif 10 <= partial_possessions <= 24:
            return '2'
        else:
            return '3'
        
    
    def saveMatchups(self, mode='offense'):
        print('selfMatchups Starting')
        all_matchups_df = pd.DataFrame()
        count = 0
        retry_count = 3
        retry_delay = 3
       
       
        for game_id in self.game_ids:
            game_id = f'00{game_id}'
            success = False
            count += 1
            print(('saveMatchups',count/len(self.game_ids)))
            for attempt in range(retry_count):
                try:
                    time.sleep(0.5)
                    play_by_play = playbyplay.PlayByPlay(game_id=game_id).play_by_play.get_data_frame()
                    play_by_play.to_csv(f'games/2023-24/{game_id}/play_by_play.csv')
                    play_by_playv2 = playbyplayv2.PlayByPlayV2(game_id=game_id).play_by_play.get_data_frame()
                    play_by_playv2.to_csv(f'games/2023-24/{game_id}/play_by_playv2.csv')
                    play_by_playv3 = playbyplayv3.PlayByPlayV3(game_id=game_id).play_by_play.get_data_frame()
                    play_by_playv3.to_csv(f'games/2023-24/{game_id}/play_by_playv3.csv')
                    
                
                    
                    
                    game = boxscorematchupsv3.BoxScoreMatchupsV3(game_id=game_id)
                    game_player_stats = game.player_stats.get_data_frame()
                    player_stats_df = self.save_and_print_player_metrics(game_player_stats)
                    all_matchups_df = pd.concat([all_matchups_df, player_stats_df], ignore_index=True)
                    success = True
                   
                    break
                except ReadTimeout:
                    print(f"Timeout for game ID {game_id}, attempt {attempt + 1}/{retry_count}. Retrying after {retry_delay} seconds...")
                    time.sleep(retry_delay)
                except IndexError as e:
                    print(f'error {e}')
                except JSONDecodeError as e:
                    print(f'error{game_id} as {e}')
                except OSError:
                    print(f'error{game_id} OS Error')

            if not success:
                print(f"Failed to retrieve data for game ID {game_id} after {retry_count} attempts.")
                


        missing_players_info = set()  # Track players with missing information

        try:
            for index, row in all_matchups_df.iterrows():
                player_name = row['Player Name']
                opponent_name = row['Opponent']

                # Initialize variables to store player and opponent information
                player_info = self.players.get(player_name, {})
                opponent_info = self.players.get(opponent_name, {})
                
                # Check if essential information is available, otherwise use default values
                player_height = player_info.get('HEIGHT', 'N/A')
                player_position = player_info.get('POSITION', 'N/A')
                player_weight = player_info.get('WEIGHT', 'N/A')
                player_obpm = player_info.get('OBPM', 0)
                player_dbpm = player_info.get('DBPM', 0)
                player_team = player_info.get('TEAM_ABBREVIATION', 'N/A')
                player_wingspan = player_info.get('WINGSPAN', 'N/A')
                player_speed = player_info.get('AVG_SPEED', 'N/A')
                average_passes_per_poss = player_info.get('OFF_POSS_PASSES', 0)
                player_poss_rebchances = player_info.get('POSS_REB_CHANCES', 'N/A')
      
                
                
                opponent_height = opponent_info.get('HEIGHT', 'N/A')
                opponent_position = opponent_info.get('POSITION', 'N/A')
                opponent_weight = opponent_info.get('WEIGHT', 'N/A')
                opponent_minutes = opponent_info.get('AVG_MIN', 0)
                opponent_obpm = opponent_info.get('OBPM', 0)
                opponent_dbpm = opponent_info.get('DBPM', 0)
                opponent_team = opponent_info.get('TEAM_ABBREVIATION', 'N/A')
                opponent_wingspan = opponent_info.get('WINGSPAN', 'N/A')
                opponent_speed = opponent_info.get('AVG_SPEED', 'N/A')
                opponent_poss_rebchances = opponent_info.get('POSS_REB_CHANCES', 'N/A')
                
                

                # Check for missing player information and log
                if player_info == {}:
                    missing_players_info.add(player_name)
                if opponent_info == {}:
                    missing_players_info.add(opponent_name)

                # Update all_matchups_df with player and opponent information
                all_matchups_df.at[index, 'Player Position'] = player_position
                all_matchups_df.at[index, 'Player Team'] = player_team
                all_matchups_df.at[index, 'Player OBPM'] = player_obpm
                all_matchups_df.at[index, 'Player DBPM'] = player_dbpm
                all_matchups_df.at[index, 'Player Height'] = player_height
                all_matchups_df.at[index, 'Player Weight'] = player_weight
                all_matchups_df.at[index, 'Average Passes per Poss'] = average_passes_per_poss
                all_matchups_df.at[index, 'Player Wingspan'] = player_wingspan if player_wingspan is not None else 200
                all_matchups_df.at[index, 'Player Speed'] = player_speed
                all_matchups_df.at[index, 'Player REB Chance per Poss'] = player_poss_rebchances
              
                

                # Update with opponent information
                all_matchups_df.at[index, 'Opponent Position'] = opponent_position
                all_matchups_df.at[index, 'Opponent Team'] = opponent_team
                all_matchups_df.at[index, 'Opponent Height'] = opponent_height
                all_matchups_df.at[index, 'Opponent Weight'] = opponent_weight
                all_matchups_df.at[index, 'Opponent OBPM'] = opponent_obpm
                all_matchups_df.at[index, 'Opponent DBPM'] = opponent_dbpm
                all_matchups_df.at[index, 'Avg Min Opp'] = opponent_minutes
                all_matchups_df.at[index, 'Opponent Wingspan'] = opponent_wingspan if opponent_wingspan is not None else 200
                all_matchups_df.at[index, 'Opponent Speed'] = opponent_speed
                all_matchups_df.at[index, 'Opponent REB Chance per Poss'] = player_poss_rebchances

        except KeyError as e:
            print(f"Key error: {e}")

        # Log missing player information
        if missing_players_info:
            print("Missing information for players/opponents:", missing_players_info)
            
        #all_matchups_df['Player Height'] = self.players[all_matchups_df['Player Name']]['Player Height']
        all_matchups_df['Matchup Minutes'] = all_matchups_df['Matchup Minutes'].apply(lambda x: round(int(x.split(':')[0]) + int(x.split(':')[1]) / 60, 2) if isinstance(x, str) else x)
        all_matchups_df['Player Height'] = pd.to_numeric(all_matchups_df['Player Height'], errors='coerce')
        all_matchups_df['Player Weight'] = pd.to_numeric(all_matchups_df['Player Weight'], errors='coerce')
        all_matchups_df['Opponent Height'] = pd.to_numeric(all_matchups_df['Opponent Height'], errors='coerce')
        all_matchups_df['Opponent Weight'] = pd.to_numeric(all_matchups_df['Opponent Weight'], errors='coerce')
        all_matchups_df['player_ppp'] = all_matchups_df['Player Points'] / all_matchups_df['partialPossessions']
        all_matchups_df['team_ppp'] = all_matchups_df['Team Points'] / all_matchups_df['partialPossessions']

        

        player_grouped = all_matchups_df.groupby('Player Name')
        all_matchups_df = all_matchups_df.replace(np.inf, np.nan)
        all_matchups_df.to_csv('players/matchups/data/orig_matchup.csv', index=False)

        player_metrics = {}
        for player in self.players:
            # Filter data for the player
            player_df = all_matchups_df[all_matchups_df['Player Name'] == player]
            opponent_df = all_matchups_df[all_matchups_df['Opponent'] == player]

            total_matchup_mins = player_df['Matchup Minutes'].sum()
            total_possessions = player_df['partialPossessions'].sum()
            total_player_points = player_df['Player Points'].sum()

            total_matchup_mins_opp = opponent_df['Matchup Minutes'].sum()
            total_possessions_opp = opponent_df['partialPossessions'].sum()
            total_player_points_opp = opponent_df['Player Points'].sum()

            offRtg = total_player_points / total_possessions if total_possessions != 0 else 0
            defRtg = total_player_points_opp / total_possessions_opp if total_possessions_opp != 0 else 0

            # average size and weight of people guarded
            height_guarded = sum(
                (opponent_df['partialPossessions'] / total_possessions_opp) * opponent_df['Player Height'])
            weight_guarded = sum(
                (opponent_df['partialPossessions'] / total_possessions_opp) * opponent_df['Player Weight'])

            try:
                player_id = self.players[player]['id']
                player_height = round(float(self.players[player]['HEIGHT']),2)
                player_weight = round(float(self.players[player]['WEIGHT']),2)
                position = self.players[player]['POSITION']
                #add points/game and ast per game
                Avg_Min = self.players[player]['AVG_MIN']
                Avg_Pts = self.players[player]['OFF_AVG_PTS']
                Avg_Ast = self.players[player]['OFF_AVG_AST']

                team = self.players[player]['TEAM_ABBREVIATION']

                player_metrics[player] = {
                    'Player ID': player_id,
                    'Player Team': team,
                    'Position': position,
                    'Avg Min': Avg_Min,
                    'Avg Pts':Avg_Pts,
                    'Avg Ast':Avg_Ast,
                    'Offensive Rating': round(offRtg, 2),
                    'Defensive Rating': round(defRtg, 2),
                    'Player Height': player_height,
                    'Player Weight': player_weight,
                }
                

                if mode == 'defense':
                    for index, row in opponent_df.iterrows():
                        opponent_name = row['Player Name']
                        # Use opponent's 'AVG_MIN' for defensive dataframe
                        #defense should be average stat/game as well as average stat/min, 
                        opponent_df.loc[index, 'Avg Min'] = self.players[opponent_name]['AVG_MIN']
                        opponent_df.loc[index, 'Avg Pts'] = self.players[opponent_name]['OFF_AVG_PTS']
                        opponent_df.loc[index, 'Avg Ast'] = self.players[opponent_name]['OFF_AVG_AST']
                        #opponent_df.loc[index, 'Off Talent'] = self.players[opponent_name]['
                elif mode == 'offense':
                    for index,row in player_df.iterrows():
                        opponent_name = row['Opponent']
                        player_df.loc[index, 'Defender Avg Min'] = self.players[opponent_name]['AVG_MIN']
                        player_df.loc[index, 'Defender Avg Pts Against'] = self.players[opponent_name]['DEF_AVG_PTS']
                        player_df.loc[index, 'Defender Poss Pts Against'] = self.players[opponent_name]['DEF_POSS_PTS']
                        player_df.loc[index, 'Defender Avg Ast Against'] = self.players[opponent_name]['DEF_AVG_AST']

            except ValueError:
                pass
            
            except KeyError:
                print(player, 'Error')
            

            if mode == 'offense':
                player_df.to_csv(f'players/matchups/data/{mode}/{player}_matchups.csv', index=False)
            else:
                opponent_df.to_csv(f'players/matchups/data/{mode}/{player}_matchups.csv', index=False)

        # Convert the dictionary to a DataFrame
        player_metrics_df = pd.DataFrame.from_dict(player_metrics, orient='index')
        player_metrics_df = player_metrics_df.dropna()

        # Save the DataFrame to a CSV file
        player_metrics_df.to_csv('players/matchups/metadata/player_matchups.csv', index_label='Player Name')
        
        
        
    def determine_opp_method(self,partial_possessions):
        if partial_possessions > 25:
            return '1'
        elif 10 <= partial_possessions <= 24:
            return '2'
        else:
            return '3'
        
    def save_and_print_player_metrics(self, game_data):
        if not isinstance(game_data, pd.DataFrame):
            raise ValueError("game_data must be a pandas DataFrame")

        columns = ['Game_Id','Player Name', 'Player Position','playerId', 'Opponent', 'Opponent Position','opponentId', 'Matchup Minutes', "partialPossessions", 
                   'Player Points', 'Team Points','player_ppp','team_ppp', 'Matchup Assists', 
                   'matchupThreePointersAttempted', 'matchupThreePointersMade', 'matchupFreeThrowsAttempted', 
                   'matchupFieldGoalsMade', 'matchupFieldGoalsAttempted', 'matchupFieldGoalsPercentage', 
          "matchupFreeThrowsMade","shootingFouls",'Player Height','Player Weight','Opponent Height','Opponent Weight']
        new_rows = []

        for index, record in game_data.iterrows():
            #print(record)
            player_name = f"{record['firstNameOff']} {record['familyNameOff']}"
            player_name = player_name.replace('.','')
            opponent = f"{record['firstNameDef']} {record['familyNameDef']}"
            opponent = opponent.replace('.', '')
            #add team and opponent team names
            new_row = {
                'Game_Id': record['gameId'],
                'Player Name': player_name,
                'playerId': record['personIdOff'],
                'Opponent': opponent,
                'opponentId': record['personIdDef'],
                'Matchup Minutes': record['matchupMinutes'],
                'partialPossessions': record["partialPossessions"],
                'Player Points': record['playerPoints'],
                'Team Points': record['teamPoints'],
                'Matchup Assists': record['matchupAssists'],
                'matchupThreePointersAttempted': record['matchupThreePointersAttempted'],
                'matchupThreePointersMade': record['matchupThreePointersMade'],
                'matchupFreeThrowsAttempted': record['matchupFreeThrowsAttempted'],
                'matchupFieldGoalsMade': record['matchupFieldGoalsMade'],
                'matchupFieldGoalsAttempted': record['matchupFieldGoalsAttempted'],
                'matchupFieldGoalsPercentage': record['matchupFieldGoalsPercentage'],
                "shootingFouls" : record["shootingFouls"],
                'matchupFreeThrowsMade' : record['matchupFreeThrowsMade']
            }

            new_rows.append(new_row)

        player_stats_df = pd.DataFrame(new_rows, columns=columns)
        return player_stats_df
    
    def fantasy_df_creation(self):
        fantasy_meta = pd.DataFrame()
        cols = ['Team','MIN','FGM','FGA','FTM','FTA','3PM','REB','AST','STL','BLK','TOV','PTS']

        for player in self.players:
            df = pd.read_csv(f'players/gamelogs/{player}_log.csv')
            df = df[cols]
            df['Avg Espn Fpts'] = (df['FGM'] * 2) + (df['FGA'] * -1) + df['FTM'] - df['FTA'] + df['3PM'] + df['REB'] + (df['AST'] * 2) + (df['STL'] * 4) + (df['BLK'] * 4) + (df['TOV'] * -2) + df['PTS']
            
            # Calculate mean, variance, total minutes, and Avg Espn Fpts per minute
            avg_espn_fpts_mean = round(df['Avg Espn Fpts'].mean(),2)
            avg_espn_fpts_variance = round(df['Avg Espn Fpts'].std(),2)
            total_minutes = round(df['MIN'].sum(),2)
            minutes = round(df['MIN'].mean(),2)
            df['Team'] = df.apply(lambda row: row.iloc[0], axis=1)
            avg_espn_fpts_per_minute = round(avg_espn_fpts_mean / minutes,2)
            
            # Create a row for the player in the fantasy_meta DataFrame
            player_meta = pd.DataFrame({
                'Player': [player],
                'Avg Min':[minutes],
                'Avg Espn Fpts Mean': [avg_espn_fpts_mean],
                'Avg Espn Fpts Variance': [avg_espn_fpts_variance],
                'Total Minutes': [total_minutes],
                'Avg Espn Fpts per Minute': [avg_espn_fpts_per_minute]
            })
            
            # Concatenate the player_meta DataFrame to the fantasy_meta DataFrame
     
            fantasy_meta = pd.concat([fantasy_meta, player_meta])

        # Display the fantasy_meta DataFrame
        fantasy_meta.to_csv('fantasy/fantasy_meta.csv',index=False)
        print(fantasy_meta)
        
        
            
    
    def processTeamMeta(self):
        for team_name in self.rosters:
            df = pd.read_csv(f'teams/games/gamelogs/{team_name}.csv')
            
            #calculate team correlations
            col1 = 'pointsPaint'
            col2 = 'PTS'
            correlation = df[col1].corr(df[col2])
            print(f"{team_name} correlation between {col1} and {col2}: {correlation}")
            
            col3 = 'FG3M'
            correlation = df[col3].corr(df[col2])
            
            print(f"{team_name} correlation between {col3} and {col2}: {correlation}\n")
        
    


    def calculate_metric(self, player_file, columns, operation='mean'):
        if not player_file.empty:
            if len(columns) == 2:
                result = player_file.apply(lambda row: row[columns[0]] / row[columns[1]] if row[columns[1]] != 0 else np.nan, axis=1)
                result = result[result <= 70] 
            elif len(columns) == 1:
                result = player_file[columns[0]]
            else:
                print("Invalid number of columns provided.")
                return None
            return getattr(result, operation)()
        else:
            return None

    def process_players(self, columns, operation='mean', threshold=None, print_method='ascending'):
        selected_players = []

        for player_name in self.players:
            try:
                player_file = pd.read_csv(f'players/gamelogsv2/{player_name}_log.csv')
                result_metric = self.calculate_metric(player_file, columns, operation)
                result_std = self.calculate_metric(player_file, columns, 'std')

                if result_metric is not None:
                    if result_metric is not None and not np.isnan(result_metric) and not np.isinf(result_metric) and (player_file['MIN'].mean() > threshold[0] or len(player_file) > threshold[1]):
                        selected_players.append({'name': player_name, f'{str(columns)}': result_metric, 'std':result_std})
            except FileNotFoundError:
                print(f'{player_name} has no gamelog file')
                
        if print_method == 'ascending':
            selected_players = sorted(selected_players, key=lambda x: x[f'{str(columns)}'])
            for i in selected_players:
                print(i)
                
            
        elif print_method == 'descending':
            selected_players = sorted(selected_players, key=lambda x: x[f'{str(columns)}'], reverse=True)
            for i in selected_players:
                print(i)

        df = pd.DataFrame(selected_players)

        #df.rename(columns={"['estimatedUsagePercentage']": 'estimatedUsagePercentage'}, inplace=True)

        df.to_csv(f'players/data_getter_outputs/{columns}.csv',index = False)
        return selected_players
                    
                    
    def init_tensor_keys(self):
        with open('keys/init_tensor_keys.txt', 'r') as file:
            return [line.strip() for line in file]
        
        

    def identify_back_to_back_games(self, dataset):
        dataset['GAME_DATE'] = pd.to_datetime(dataset['GAME_DATE']).dt.date
        dataset.sort_values(by='GAME_DATE', inplace=True)
        dataset['Back_to_Back'] = 0
        dataset['Away_Game'] = dataset['MATCHUP'].apply(lambda x: '@' in x).astype(int)

        for i in range(len(dataset) - 1):
            if (dataset.iloc[i + 1]['GAME_DATE'] - dataset.iloc[i]['GAME_DATE']).days == 1:
                dataset.at[i - 1, 'Back_to_Back'] = 2  
                dataset.at[i, 'Back_to_Back'] = 1  

        dataset['First_Home_After_Road'] = 0
        consecutive_away = 0
        for i in range(1, len(dataset)):
            if dataset.iloc[i]['Away_Game'] == 1:
                consecutive_away += 1
            elif consecutive_away >= 3:  # It's a home game following 3+ away games
                dataset.at[i, 'First_Home_After_Road'] = 1
                consecutive_away = 0  # Reset counter
            else:  # It's a home game but not following 3+ away games
                consecutive_away = 0  # Reset counter

        dataset.drop(['Away_Game'], axis=1, inplace=True)
        return dataset




    def merge_team_player_logs(self,player_log, team_log):
        return player_log.merge(team_log[['Game_ID', 'Back_to_Back', 'First_Home_After_Road']], on='Game_ID', how='left')


    
    def parse_back_to_back_games(self,save=False):       
        print('TEAMS\n\n\n\n\n')
        for team in self.teams:
            print(team)
            team_file = pd.read_csv(f'teams/games/gamelogs/{team}.csv')
            team_file_b2b = self.identify_back_to_back_games(team_file)
            if save == True:
                team_file_b2b.to_csv(f'teams/games/gamelogs/{team}.csv',index=False)
               
        print('PLAYERS\n\n\n\n\n')        
        for player in self.players:
            team_name = self.players[player]['TEAM_ABBREVIATION']
            try:
                player_file = pd.read_csv(f'players/gamelogs/{player}_log.csv')
                team_file = pd.read_csv(f'teams/games/gamelogs/{team_name}.csv')
                player_file_b2b = self.merge_team_player_logs(player_file,team_file)

                if save == True:
                    player_file_b2b.to_csv(f'players/gamelogs/{player}_log.csv',index=False)
            except FileNotFoundError:
                print(f'{player}, FNF Error')
            
    
                
            
    def scrape_ratings(self):
        print(self.players)
        
        
    def calculate_weighted_average(self, df, value_column, weight_column):
        """Calculate weighted averages for a DataFrame."""
        weighted_sum = (df[value_column] * df[weight_column]).sum()
        total_weight = df[weight_column].sum()
        return weighted_sum / total_weight if total_weight else 0

    def process_player(self, player_name, metrics):
        """Process offense and defense game logs and save weighted averages."""
        offense_path = f'{self.base_path}/offense/{player_name}_matchups.csv'
        defense_path = f'{self.base_path}/defense/{player_name}_matchups.csv'
        
        if not os.path.exists(offense_path) or not os.path.exists(defense_path):
            print(f"Game logs for {player_name} not found.")
            return

        offense_df = pd.read_csv(offense_path)
        defense_df = pd.read_csv(defense_path)

        results = []

        for game_id, group in offense_df.groupby('Game_Id'):
            game_results = {'Game_Id': game_id}
            metrics = ['Opponent Height','Opponent Weight']
            for metric in metrics:
                game_results[f'Offense {metric}'] = self.calculate_weighted_average(group, metric, 'partialPossessions')
            results.append(game_results)

        for game_id, group in defense_df.groupby('Game_Id'):
            for result in results:
                if result['Game_Id'] == game_id:
                    for metric in metrics:
                        result[f'Defense {metric}'] = self.calculate_weighted_average(group, metric, 'partialPossessions')

        results_df = pd.DataFrame(results)
        results_df.to_csv(f'{self.base_path}/metadata/{player_name}_weighted_averages.csv', index=False)
        print(f"Processed and saved data for {player_name}.")
        
                    
                     
#data = DataGetter()
#data.process_players( ['oppPoints','partialPossessions'], operation = 'mean',threshold = [22.5,80], print_method = 'descending')
            
            
            
#static usg%  -> project player matchups -> from player matchups -> predict dynamic usage %


#predict totl possesions for a player ina  game, and divide up, 


class Plyrs(DataGetter):
    def __init__(self):
        super().__init__()

    def convert_to_feet_inches(self, height_cm):
        # Convert height from centimeters to feet and inches
        inches = height_cm / 2.54
        feet = int(inches // 12)
        remaining_inches = round(inches % 12, 2)
        return feet, remaining_inches

    def create_players_df(self, team1, team2):
        player_info_dict = {}
        team1 = self.rosters[team1]
        team2 = self.rosters[team2]

        data = {'Position': [], 'Height': [], 'Weight': [], 'Team': [], 'Speed': [], 'Pts_Paint_Min': [], 'Pts_Paint': []}

        for team in [team1, team2]:
            print('team\n')
            for player, attributes in team.items():
                plyr_min = self.players[player]['AVG_MIN']
                try:
                    if plyr_min >= 15:              
                        print(player,self.players[player]['HEIGHT'],self.players[player]['WEIGHT'],self.players[player]['WINGSPAN'],'DBPM',self.players[player]['DBPM'],'OBPM',self.players[player]['OBPM'])
                        
                except ValueError:
                    print('ValueError in: player, attributes in team.items() iterative')
                except KeyError:
                    print(player, ' passed')

        players_df = pd.DataFrame(data, index=player_info_dict.keys())
        return players_df
    
    
   
    
#x = Plyrs()
#print(x.create_players_df('LAL','TOR'))

#iterate through offense or defense matchups

#save each unique player and their attributes?

#insert into something to display graph
#like R