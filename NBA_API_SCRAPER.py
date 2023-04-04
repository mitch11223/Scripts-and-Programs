import pandas
import requests
from bs4 import BeautifulSoup
import numpy as np
import os
import time
import numpy as np
import json
import nba_api.stats.endpoints as stats_endpoints
import nba_api.live.nba.endpoints as today_endpoints
import matplotlib.pyplot as plt
import matplotlib.patches as patches

hold = []
player_list = {
    'ATL': ['Saddiq Bey', 'Clint Capela', 'John Collins', 'Jarrett Culver', 'Trent Forrest', 'AJ Griffin', 'Aaron Holiday', 'Justin Holiday', "De'Andre Hunter",'Jalen Johnson', 'Frank Kaminsky', 'Dejounte Murray', 'Onyeka Okongwu', 'Trae Young'],
    'BOS': ['Malcolm Brogdon', 'Jaylen Brown', 'Blake Griffin', 'Al Horford', 'Mfiondu Kabengele', 'Luke Kornet','Mike Muscala','Payton Pritchard', 'Marcus Smart', 'Jayson Tatum', 'Derrick White', 'Grant Williams'],
    'BRK': ['Mikal Bridges','Nic Claxton', 'Seth Curry','Spencer Dinwiddie','Joe Harris','Cameron Johnson','Dorian Finney-Smith','Spencer Dinwiddie','Patty Mills', "Royce O'Neale", 'Ben Simmons', 'Edmond Sumner', 'Cam Thomas', 'Yuta Watanabe'],
    'CHO': ['LaMelo Ball','James Bouknight','Gordon Hayward','Kai Jones','Theo Maledon','Cody Martin','Kelly Oubre Jr.','Nick Richards','Terry Rozier','Dennis Smith Jr.','P.J. Washington'],
    'CHI': ['Patrick Beverley','Tony Bradley','Alex Caruso','DeMar DeRozan','Goran Dragic','Andre Drummond','Javonte Green','Derrick Jones Jr.','Zach LaVine','Marko Simonovic','Nikola Vucevic','Coby White','Patrick Williams'],
    'CLE': ['Jarrett Allen','Mamadi Diakite','Darius Garland','Caris LeVert','Robin Lopez','Kevin Love','Donovan Mitchell','Evan Mobley','Raul Neto','Isaac Okoro','Lamar Stevens','Dean Wade'],
    'DAL': ['Davis Bertans','Reggie Bullock','Luka Doncic','Tyler Dorsey','Josh Green','Tim Hardaway Jr.','Jaden Hardy','Kyrie Irving','JaVale McGee','Dwight Powell','Christian Wood'],
    'DEN': ['Bruce Brown','Thomas Bryant','Kentavious Caldwell-Pope','Vlatko Cancar','Aaron Gordon','Jeff Green','Reggie Jackson','Nikola Jokic','DeAndre Jordan','Jamal Murray','Zeke Nnaji','Michael Porter Jr.','Ish Smith'],
    'DET': ['Marvin Bagley III','Bojan Bogdanovic','Alec Burks','Cade Cunningham','Hamidou Diallo','Jalen Duren','Killian Hayes','Jaden Ivey','Cory Joseph','Isaiah Livers','Rodney McGruder','Isaiah Stewart','James Wiseman'],
    'GSW': ['Stephen Curry','Donte DiVincenzo','Draymond Green','JaMychal Green','Ty Jerome','Jonathan Kuminga','Anthony Lamb','Kevon Looney','Moses Moody','Jordan Poole','Klay Thompson','Andrew Wiggins'],
    'HOU': ['Josh Christopher','Tari Eason','Bruno Fernando','Usman Garuba','Jalen Green','Boban Marjanovic','Kenyon Martin Jr.','Garrison Mathews','Kevin Porter Jr.','Alperen Sengun','Jabari Smith Jr.',"Jae'Sean Tate",'TyTy Washington Jr.'],
    'IND': ['Goga Bitadze','Oshae Brissett','Chris Duarte','Tyrese Haliburton','Buddy Hield','George Hill','Serge Ibaka','Isaiah Jackson','James Johnson','Bennedict Mathurin','T.J. McConnell','Andrew Nembhard','Aaron Nesmith','Jordan Nwora','Jalen Smith','Myles Turner'],
    'LAC': ['Nicolas Batum','Moses Brown','Amir Coffey','Robert Covington','Paul George','Eric Gordon','Bones Hyland','Kawhi Leonard','Terance Mann','Marcus Morris','Mason Plumlee','Norman Powell','Russell Westbrook','Ivica Zubac'],
    'LAL': ['Mo Bamba','Malik Beasley','Troy Brown Jr.','Anthony Davis','Wenyen Gabriel','LeBron James','Damian Jones','Rui Hachimura','Austin Reaves',"D'Angelo Russell",'Dennis Schroder','Jarred Vanderbilt','Lonnie Walker IV'],
    'MEM': ['Steven Adams','Santi Aldama','Desmond Bane','Dillon Brooks','Brandon Clarke','Jaren Jackson Jr.','Tyus Jones','Luke Kennard','John Konchar','Jake LaRavia','Ja Morant','David Roddy','Xavier Tillman Sr.'],
    'MIA': ['Bam Adebayo','Jimmy Butler','Jamal Cain','Dewayne Dedmon','Udonis Haslem','Tyler Herro','Haywood Highsmith','Nikola Jovic','Kyle Lowry','Caleb Martin','Duncan Robinson','Victor Oladipo','Max Strus','Gabe Vincent'],
    'MIL': ['Grayson Allen','Giannis Antetokounmpo','MarJon Beauchamp','Jevon Carter','Pat Connaughton','Jae Crowder','Jrue Holiday','Brook Lopez','Wesley Matthews','Bobby Portis'],
    'MIN': ['Nickeil Alexander-Walker','Kyle Anderson','Mike Conley','Anthony Edwards','Bryn Forbes','Rudy Gobert','Jaden McDaniels','Jordan McLaughlin','Jaylen Nowell','Taurean Prince','Naz Reid','Austin Rivers','Karl-Anthony Towns'],
    'NOP': ['Jose Alvarado','Dyson Daniels','Jaxson Hayes','Willy Hernangomez','Brandon Ingram','Herbert Jones','Naji Marshall','CJ McCollum','Trey Murphy III','Larry Nance Jr.','Josh Richardson','Jonas Valanciunas','Zion Williamson'],
    'NYK': ['RJ Barrett','Jalen Brunson','Evan Fournier','Quentin Grimes','Josh Hart','Isaiah Hartenstein','Miles McBride','Immanuel Quickley','Julius Randle','Mitchell Robinson','Derrick Rose','Jericho Sims','Obi Toppin'],
    'OKC': ['Ousmane Dieng','Luguentz Dort','Josh Giddey','Shai Gilgeous-Alexander','Isaiah Joe','Tre Mann','Aleksej Pokusevski','Jeremiah Robinson-Earl','Dario Saric','Aaron Wiggins','Jalen Williams','Jaylin Williams','Kenrich Williams'],
    'ORL': ['Cole Anthony','Mo Bamba','Paolo Banchero','Bol Bol','Wendell Carter Jr.','Markelle Fultz','Gary Harris','Caleb Houstan','Chuma Okeke','Terrence Ross','Admiral Schofield','Jalen Suggs','Franz Wagner','Moritz Wagner'],
    'PHI': ['Joel Embiid','James Harden','Montrezl Harrell','Tobias Harris','Furkan Korkmaz','Tyrese Maxey','Jalen McDaniels',"De'Anthony Melton",'Shake Milton','Georges Niang','Paul Reed','P.J. Tucker'],
    'PHO': ['Deandre Ayton','Darius Bazley','Bismack Biyombo','Devin Booker','Torrey Craig','Kevin Durant','Jock Landale','Damion Lee','Josh Okogie','Chris Paul','Cameron Payne','Landry Shamet','T.J. Warren'],
    'POR': ['Drew Eubanks','Jerami Grant','Keon Johnson','Kevin Knox','Damian Lillard','Nassir Little','Jusuf Nurkic','Cam Reddish','Shaedon Sharpe','Anfernee Simons','Matisse Thybulle','Trendon Watford','Justise Winslow'],
    'SAC': ['Harrison Barnes','Terence Davis','Matthew Dellavedova','Keon Ellis',"De'Aaron Fox",'Richaun Holmes','Kevin Huerter','Alex Len','Trey Lyles','Chimezie Metu','Davion Mitchell','Malik Monk','Keegan Murray','KZ Okpala','Domantas Sabonis'],
    'SAS': ['Charles Bassey','Keita Bates-Diop','Malaki Branham','Zach Collins','Gorgui Dieng',"Devonta Graham",'Keldon Johnson','Tre Jones','Romeo Langford','Doug McDermott','Isaiah Roby','Jeremy Sochan','Devin Vassell','Blake Wesley'],
    'TOR': ['Precious Achiuwa','OG Anunoby','Dalano Banton','Scottie Barnes','Chris Boucher','Malachi Flynn','Christian Koloko','Jakob Poeltl','Otto Porter Jr.','Pascal Siakam','Gary Trent Jr.','Fred VanVleet','Thaddeus Young'],
    'UTA': ['Nickeil Alexander-Walker','Jordan Clarkson','Rudy Gay','Talen Horton-Tucker','Walker Kessler','Lauri Markkanen','Kelly Olynyk','Collin Sexton'],
    'WAS': ['Deni Avdija','Will Barton','Bradley Beal','Daniel Gafford','Taj Gibson','Anthony Gill','Kendrick Nunn','Corey Kispert','Kyle Kuzma','Monte Morris','Kristaps Porzingis','Delon Wright']
}

teamIDkey = {'ATL':'1610612737','BRK':'1610612751','BOS':'1610612738','CHO':'1610612766','CLE':'1610612739',
             'CHI':'1610612741', 'DAL':'1610612742', 'DEN':'1610612743', 'DET':'1610612765', 'GSW':'1610612744',
             'HOU':'1610612745', 'IND':'1610612754', 'LAC':'1610612746','LAL':'1610612747','MEM':'1610612763',
             'MIA':'1610612748', 'MIL':'1610612749', 'MIN':'1610612750', 'NYK':'1610612752', 'NOP':'1610612740',
             'OKC':'1610612760', 'ORL':'1610612753', 'PHI':'1610612755', 'PHO':'1610612756','POR':'1610612757',
             'SAS':'1610612759', 'SAC':'1610612758', 'TOR':'1610612761','UTA':'1610612762','WAS':'1610612764'}
team_list = ['ATL',
             'BOS',
             'BRK',
             'CHO',
            'CHI',
    'CLE',
    'DAL',
    'DEN',
    'DET',
    'GSW',
    'HOU',
    'IND',
    'LAC',
    'LAL',
    'MEM',
    'MIA',
    'MIL',
    'MIN',
    'NOP',
    'NYK',
    'OKC',
    'ORL',
    'PHI',
    'PHO',
    'POR',
    'SAC',
    'SAS',
    'TOR',
    'UTA',
    'WAS'] 

key = {'ATL':'AtlantaHawks', 'BRK':'BrooklynNets', 'BOS':'BostonCeltics', 'CHO':'CharlotteHornets','CHI':'ChicagoBulls','CLE':'ClevelandCavaliers','DAL':'DallasMavericks','DEN':'DenverNuggets','DET':'DetroitPistons',
           'GSW':'GoldenStateWarriors','HOU':'HoustonRockets','IND':'IndianaPacers','LAC':'LosAngelesClippers','LAL':'LosAngelesLakers','MEM':'MemphisGrizzlies','MIA':'MiamiHeat','MIL':'MilwaukeeBucks','MIN':'MinnesotaTimberwolves',
           'NOP':'NewOrleansPelicans','NYK':'NewYorkKnicks','OKC':'OklahomaCityThunder','ORL':'OrlandoMagic','PHI':'Philadelphia76ers','PHO':'PhoenixSuns','POR':'PortlandTrailBlazers','SAC':'SacramentoKings','SAS':'SanAntonioSpurs','TOR':'TorontoRaptors',
           'UTA':'UtahJazz','WAS':'WashingtonWizards'}
key_2 = {value: key for key, value in key.items()}




def get_gameids_team(teamid):
        log = stats_endpoints.teamgamelogs.TeamGameLogs(team_id_nullable = teamid, season_nullable = '2022-23')
        log = log.get_dict()
        log = log['resultSets']
        log = log[0]
        headers = log['headers']
        data = log['rowSet']
        df = pandas.DataFrame(data,columns = headers)
        new = df['GAME_ID'].to_list()
        return new

print('done')





def json(URL):
    resp = requests.get(URL)
    resp = resp.json()
    return resp


def turn_json_to_pandas(dataframe):   
    df = dataframe.get_dict()
    df = df['resultSets']
    df = df[0]
    headers = df['headers']
    data = df['rowSet']
        
    df = pandas.DataFrame(data,columns = headers)
    return df


playerids_df = pandas.read_csv('TeamFiles/League/Roster/playerids/playerids.csv')
#playerids_df = dict(zip(playerids_df.Player, playerids_df.ID))


class Static():
    
    def __init__(self):
        pass
    def pull_boxscoreplayertrack(self,gameid,player):
        self.gameid = gameid
        self.player = player
        
        #Find row of player
        self.df = stats_endpoints.boxscoreplayertrackv2.BoxScorePlayerTrackV2(game_id = self.gameid)
        self.df = turn_json_to_pandas(self.df)
        
        self.player_row = self.df.loc[self.df['PLAYER_NAME'] == self.player]
        
        return self.player_row
    
    def pull_boxscoreadvanced(self,gameid,player):
        self.gameid = gameid
        self.player = player
        self.df = stats_endpoints.boxscoreadvancedv2.BoxScoreAdvancedV2(game_id = self.gameid)
        self.df = turn_json_to_pandas(self.df)
        
        self.player_row = self.df.loc[self.df['PLAYER_NAME'] == self.player]
        
        return self.player_row
    
    
    
    
    def BoxScoreCombine_stats(self,player):
        self.playerid = playerids_df.loc[playerids_df['Player'] == player,'ID']
        for ID in self.playerid:
            self.playerid = str(ID)
    
        for team,players in player_list.items():       #find the team to which the player plays to get its teamid
            if player in players:
                teamid = teamIDkey[team]
                teamgames = get_gameids_team(team)
                
            
        #playerid, teamgames list and teamid are available now
        #FIND THE GAMES THAT PLAYER PLAYED IN
        self.BoxScorePlayerTrack = stats_endpoints.playergamelog.PlayerGameLog(player_id = self.playerid)
        self.BoxScorePlayerTrack = turn_json_to_pandas(self.BoxScorePlayerTrack)
        #this is a list of the gameids that a player played in
        self.playergames_id = self.BoxScorePlayerTrack['Game_ID']
        
    
    
        #FIND THE STATISTICS OF THE GAMES PLAYER PLAYED IN
        
        df = pandas.DataFrame()
        for gameID in self.playergames_id:
            self.BoxScorePlayerTrack = self.pull_boxscoreplayertrack(gameID,player)     #BoxScorePlayerTrack
            self.BoxScoreAdvanced = self.pull_boxscoreadvanced(gameID,player)
            row = pandas.concat([self.BoxScorePlayerTrack, self.BoxScoreAdvanced], axis=1)
            df = pandas.concat([df, row], axis=0, ignore_index=True)
    
        df = df.loc[:,~df.columns.duplicated()].copy()
    
        return df 
    
    
 

    
    

#PBP
#live = pbp_live(0)
#live = live.pull_boxscore()
#print(live)

#BOXSCORE
#static = Static()
#static.pull_boxscoreplayertrack('0022201014','Andrew Wiggins')









def dbltrple():
    dbltrpl = pandas.DataFrame(columns = ['player', 'DBLDBL', 'TRPLDBL'])
    for team in team_list:
        for player in player_list[team]:
            player = str(player.replace(' ',''))
            if '.' in player:
                player = player.replace('.','')
            player_filename = f"TeamFiles/League/Roster/Players/BoxScores/{player}.txt"
            try:
                player_df = pandas.read_csv(player_filename)
                player_df['DBLDBL'] = np.where((player_df['PTS']>=10) & (player_df['AST_x']>=10) | (player_df['PTS']>=10) & (player_df['TRB']>=10) | (player_df['AST_x']>=10) & (player_df['TRB']>=10), 1, 0)
                player_df['TRPLDBL'] = np.where((player_df['PTS']>=10) & (player_df['AST_x']>=10) & (player_df['TRB']>=10), 1, 0)
                #dbltrpl['DBLDBL'] = dbltrpl['DBLDBL'].astype(int)
                #dbltrpl['TRPLDBL'] = dbltrpl['TRPLDBL'].astype(int)
                
                dbltrpl = dbltrpl.append(pandas.DataFrame([[player, player_df['DBLDBL'].mean(), player_df['TRPLDBL'].mean()]], columns = ['player', 'DBLDBL', 'TRPLDBL']))
                print(dbltrpl)
                
                
                file = open(player_filename,'w')
                player_df = player_df.to_csv()
                file.write(player_df)
                file.close()
                
                

            except FileNotFoundError:
                pass

    dbltrplfname = "TeamFiles/League/Roster/Players/TripleDouble/TripleDouble.txt"
    os.makedirs(os.path.dirname(dbltrplfname), exist_ok=True)
    file = open(dbltrplfname,'w')
    dbltrpl = dbltrpl.to_csv(index=False)
    file.write(dbltrpl)
    file.close()
    
#dbltrple()





def process_both_logs():
    players_passed = []
    for team in team_list:
        for player in player_list[team]:
            static = Static()
            try:
                BoxScore = static.BoxScoreCombine_stats(f"{player}")
                player = str(player.replace(' ',''))
                if '.' in player:
                    player = player.replace('.','')
                preboxscore = pandas.read_csv(f"TeamFiles/League/Roster/Players/{player}.txt")
                preboxscore = preboxscore.iloc[::-1].dropna(subset=['G'])
                bsgid = BoxScore['GAME_ID'].to_list()
                preboxscore['GAME_ID'] = bsgid

                #merge dataframes on 'GAME_ID' column
                BoxScore = pandas.merge(left = preboxscore, right = BoxScore,on='GAME_ID',)
                BoxScore = BoxScore.drop(['TEAM_ABBREVIATION','TEAM_CITY','PLAYER_ID','PLAYER_NAME','COMMENT','AST_y','START_POSITION','NICKNAME','Rk','Age','PF'], axis=1)       
                BoxScore = BoxScore.to_csv(index=False)
       
                team_filename = f"TeamFiles/League/Roster/Players/BoxScores/{player}.txt"
                os.makedirs(os.path.dirname(team_filename), exist_ok=True)
                file = open(team_filename,'w')
                file.write(BoxScore)
                file.close()
                print(f"Team:{team} Player:{player} Complete!")
            except ValueError:
                players_passed.append(player)
                print(f"Player passed {player}")
        
process_both_logs()