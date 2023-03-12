import pandas
import requests
from bs4 import BeautifulSoup
import numpy
import os
import time
import numpy as np


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

key = {'ATL':'AtlantaHawks', 'BOS':'BostonCeltics', 'BRK':'BrooklynNets','CHO':'CharlotteHornets','CHI':'ChicagoBulls','CLE':'ClevelandCavaliers','DAL':'DallasMavericks','DEN':'DenverNuggets','DET':'DetroitPistons',
           'GSW':'GoldenStateWarriors','HOU':'HoustonRockets','IND':'IndianaPacers','LAC':'LAClippers','LAL':'LosAngelesLakers','MEM':'MemphisGrizzlies','MIA':'MiamiHeat','MIL':'MilwaukeeBucks','MIN':'MinnesotaTimberwolves',
           'NOP':'NewOrleansPelicans','NYK':'NewYorkKnicks','OKC':'OklahomaCityThunder','ORL':'OrlandoMagic','PHI':'Philadelphia76ers','PHO':'PhoenixSuns','POR':'PortlandTrailBlazers','SAC':'SacramentoKings','SAS':'SanAntonioSpurs','TOR':'TorontoRaptors',
           'UTA':'UtahJazz','WAS':'WashingtonWizards'}
key_2 = {value: key for key, value in key.items()}


player_list = {
    'ATL': ['Saddiq Bey', 'Clint Capela', 'John Collins', 'Jarrett Culver', 'Trent Forrest', 'AJ Griffin', 'Aaron Holiday', 'Justin Holiday', "De'Andre Hunter", 'Jalen Johnson', 'Frank Kaminsky', 'Dejounte Murray', 'Onyeka Okongwu', 'Trae Young'],
    'BOS': ['Malcolm Brogdon', 'Jaylen Brown', 'Blake Griffin', 'Al Horford', 'Mfiondu Kabengele', 'Luke Kornet','Mike Muscala','Payton Pritchard', 'Marcus Smart', 'Jayson Tatum', 'Noah Vonleh', 'Derrick White', 'Grant Williams'],
    'BRK': ['Mikal Bridges','Nic Claxton', 'Seth Curry','Spencer Dinwiddie','Joe Harris', 'Cam Johnson','Dorian Finney-Smith','Spencer Dinwiddie','Patty Mills', "Royce O'Neale", 'Ben Simmons', 'Edmond Sumner', 'Cam Thomas', 'Yuta Watanabe'],
    'CHO': ['LaMelo Ball','James Bouknight','Gordon Hayward','Kai Jones','Theo Maledon','Cody Martin','Kelly Oubre Jr.','Nick Richards','Terry Rozier','Dennis Smith Jr.','PJ Washington'],
    'CHI': ['Patrick Beverley','Tony Bradley','Alex Caruso','DeMar DeRozan','Goran Dragic','Andre Drummond','Javonte Green','Derrick Jones Jr.','Zach LaVine','Marko Simonovic','Nikola Vucevic','Coby White','Patrick Williams'],
    'CLE': ['Jarrett Allen','Mamadi Diakite','Darius Garland','Caris LeVert','Robin Lopez','Kevin Love','Donovan Mitchell','Evan Mobley','Raul Neto','Isaac Okoro','Lamar Stevens','Dean Wade'],
    'DAL': ['Davis Bertans','Reggie Bullock','Luka Doncic','Tyler Dorsey','Josh Green','Tim Hardaway Jr.','Jaden Hardy','Kyrie Irving','JaVale McGee','Markieff Morris','Dwight Powell','Christian Wood'],
    'DEN': ['Bruce Brown','Thomas Bryant','Kentavious Caldwell-Pope','Vlatko Cancar','Aaron Gordon','Jeff Green','Reggie Jackson','Nikola Jokic','DeAndre Jordan','Jamal Murray','Zeke Nnaji','Michael Porter Jr.','Ish Smith'],
    'DET': ['Marvin Bagley III','Bojan Bogdanovic','Alec Burks','Cade Cunningham','Hamidou Diallo','Jalen Duren','Killian Hayes','Jaden Ivey','Cory Joseph','Isaiah Livers','Rodney McGruder','Isaiah Stewart','James Wiseman'],
    'GSW': ['Stephen Curry','Donte DiVincenzo','Draymond Green','JaMychal Green','Ty Jerome','Jonathan Kuminga','Anthony Lamb','Kevon Looney','Moses Moody','Jordan Poole','Klay Thompson','Andrew Wiggins'],
    'HOU': ['Josh Christopher','Tari Eason','Bruno Fernando','Usman Garuba','Jalen Green','Boban Marjanovic','Kenyon Martin Jr.','Garrison Mathews','Kevin Porter Jr.','Alperen Sengun','Jabari Smith Jr.',"JaeSean Tate",'TyTy Washington Jr.'],
    'IND': ['Goga Bitadze','Oshae Brissett','Chris Duarte','Tyrese Haliburton','Buddy Hield','George Hill','Serge Ibaka','Isaiah Jackson','James Johnson','Bennedict Mathurin','TJ McConnell','Andrew Nembhard','Aaron Nesmith','Jordan Nwora','Jalen Smith','Myles Turner'],
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
    'PHI': ['Joel Embiid','James Harden','Montrezl Harrell','Tobias Harris','Furkan Korkmaz','Tyrese Maxey','Jalen McDaniels',"De'Anthony Melton",'Shake Milton','Georges Niang','Paul Reed','PJ Tucker'],
    'PHO': ['Deandre Ayton','Darius Bazley','Bismack Biyombo','Devin Booker','Torrey Craig','Kevin Durant','Jock Landale','Damion Lee','Josh Okogie','Chris Paul','Cameron Payne','Landry Shamet','TJ Warren'],
    'POR': ['Drew Eubanks','Jerami Grant','Keon Johnson','Kevin Knox','Damian Lillard','Nassir Little','Jusuf Nurkic','Cam Reddish','Shaedon Sharpe','Anfernee Simons','Matisse Thybulle','Trendon Watford','Justise Winslow'],
    'SAC': ['Harrison Barnes','Terence Davis','Matthew Dellavedova','Keon Ellis',"De'Aaron Fox",'Richaun Holmes','Kevin Huerter','Alex Len','Trey Lyles','Chimezie Metu','Davion Mitchell','Malik Monk','Keegan Murray','KZ Okpala','Domantas Sabonis'],
    'SAS': ['Charles Bassey','Keita Bates-Diop','Malaki Branham','Zach Collins','Gorgui Dieng',"Devonta Graham",'Keldon Johnson','Tre Jones','Romeo Langford','Doug McDermott','Isaiah Roby','Jeremy Sochan','Devin Vassell','Blake Wesley'],
    'TOR': ['Precious Achiuwa','OG Anunoby','Dalano Banton','Scottie Barnes','Chris Boucher','Malachi Flynn','Christian Koloko','Jakob Poeltl','Otto Porter Jr','Pascal Siakam','Gary Trent Jr.','Fred VanVleet','Thaddeus Young'],
    'UTA': ['Nickeil Alexander-Walker','Jordan Clarkson','Rudy Gay','Talen Horton-Tucker','Walker Kessler','Lauri Markkanen','Kelly Olynyk','Collin Sexton'],
    'WAS': ['Deni Avdija','Will Barton','Bradley Beal','Daniel Gafford','Taj Gibson','Anthony Gill','Kendrick Nunn','Corey Kispert','Kyle Kuzma','Monte Morris','Kristaps Porzingis','Delon Wright']
}



cor_cols = ['G','MP', 'FG',
               'FGA', '3P', '3PA', 'FT', 'FTA', 'ORB', 'DRB',
               'TRB', 'AST', 'STL', 'BLK', 'TOV', 'PF', 'PTS', 'GmSc', 'PlusMinus',
               'Margin', 'PTSREBAST', 'PTSREB', 'PTSAST', 'REBAST']

values = [['Player',''],['MP', 'FG'], ['MP', 'FGA'], ['MP', '3P'], ['MP', '3PA'], ['MP', 'FT'], ['MP', 'FTA'], ['MP', 'ORB'], ['MP', 'DRB'], ['MP', 'TRB'], ['MP', 'AST'], ['MP', 'STL'], ['MP', 'BLK'], ['MP', 'TOV'], ['MP', 'PF'], ['MP', 'PTS'], ['MP', 'GmSc'], ['MP', 'PlusMinus'], ['MP', 'Margin'], ['MP', 'PTSREBAST'], ['MP', 'PTSREB'], ['MP', 'PTSAST'], ['MP', 'REBAST'], ['FG', 'FGA'], ['FG', '3P'], ['FG', '3PA'], ['FG', 'FT'], ['FG', 'FTA'], ['FG', 'ORB'], ['FG', 'DRB'], ['FG', 'TRB'], ['FG', 'AST'], ['FG', 'STL'], ['FG', 'BLK'], ['FG', 'TOV'], ['FG', 'PF'], ['FG', 'PTS'], ['FG', 'GmSc'], ['FG', 'PlusMinus'], ['FG', 'Margin'], ['FG', 'PTSREBAST'], ['FG', 'PTSREB'], ['FG', 'PTSAST'], ['FG', 'REBAST'], ['FGA', '3P'], ['FGA', '3PA'], ['FGA', 'FT'], ['FGA', 'FTA'], ['FGA', 'ORB'], ['FGA', 'DRB'], ['FGA', 'TRB'], ['FGA', 'AST'],
 ['FGA', 'STL'], ['FGA', 'BLK'], ['FGA', 'TOV'], ['FGA', 'PF'], ['FGA', 'PTS'], ['FGA', 'GmSc'], ['FGA', 'PlusMinus'], ['FGA', 'Margin'], ['FGA', 'PTSREBAST'], ['FGA', 'PTSREB'], ['FGA', 'PTSAST'], ['FGA', 'REBAST'], ['3P', '3PA'], ['3P', 'FT'], ['3P', 'FTA'], ['3P', 'ORB'], ['3P', 'DRB'], ['3P', 'TRB'], ['3P', 'AST'], ['3P', 'STL'], ['3P', 'BLK'], ['3P', 'TOV'], ['3P', 'PF'], ['3P', 'PTS'], ['3P', 'GmSc'], ['3P', 'PlusMinus'], ['3P', 'Margin'], ['3P', 'PTSREBAST'], ['3P', 'PTSREB'], ['3P', 'PTSAST'], ['3P', 'REBAST'], ['3PA', 'FT'], ['3PA', 'FTA'], ['3PA', 'ORB'], ['3PA', 'DRB'], ['3PA', 'TRB'], ['3PA', 'AST'], ['3PA', 'STL'], ['3PA', 'BLK'], ['3PA', 'TOV'], ['3PA', 'PF'], ['3PA', 'PTS'], ['3PA', 'GmSc'], ['3PA', 'PlusMinus'], ['3PA', 'Margin'], ['3PA', 'PTSREBAST'], ['3PA', 'PTSREB'], ['3PA', 'PTSAST'], ['3PA', 'REBAST'], ['FT', 'FTA'], ['FT', 'ORB'], ['FT', 'DRB'], ['FT', 'TRB'], ['FT', 'AST'], ['FT', 'STL'], ['FT', 'BLK'], ['FT', 'TOV'], ['FT', 'PF'], ['FT', 'PTS'], ['FT', 'GmSc'], ['FT', 'PlusMinus'], ['FT', 'Margin'], ['FT', 'PTSREBAST'], ['FT', 'PTSREB'], ['FT', 'PTSAST'], ['FT', 'REBAST'], ['FTA', 'ORB'], ['FTA', 'DRB'], ['FTA', 'TRB'], ['FTA', 'AST'], ['FTA', 'STL'], ['FTA', 'BLK'], ['FTA', 'TOV'], ['FTA', 'PF'], ['FTA', 'PTS'], ['FTA', 'GmSc'], ['FTA', 'PlusMinus'], ['FTA', 'Margin'], ['FTA', 'PTSREBAST'], ['FTA', 'PTSREB'], ['FTA', 'PTSAST'], ['FTA', 'REBAST'],
 ['ORB', 'DRB'], ['ORB', 'TRB'], ['ORB', 'AST'], ['ORB', 'STL'], ['ORB', 'BLK'], ['ORB', 'TOV'], ['ORB', 'PF'], ['ORB', 'PTS'], ['ORB', 'GmSc'], ['ORB', 'PlusMinus'], ['ORB', 'Margin'], ['ORB', 'PTSREBAST'], ['ORB', 'PTSREB'], ['ORB', 'PTSAST'], ['ORB', 'REBAST'], ['DRB', 'TRB'], ['DRB', 'AST'], ['DRB', 'STL'], ['DRB', 'BLK'], ['DRB', 'TOV'], ['DRB', 'PF'], ['DRB', 'PTS'], ['DRB', 'GmSc'], ['DRB', 'PlusMinus'], ['DRB', 'Margin'], ['DRB', 'PTSREBAST'], ['DRB', 'PTSREB'], ['DRB', 'PTSAST'], ['DRB', 'REBAST'], ['TRB', 'AST'], ['TRB', 'STL'], ['TRB', 'BLK'], ['TRB', 'TOV'], ['TRB', 'PF'], ['TRB', 'PTS'], ['TRB', 'GmSc'], ['TRB', 'PlusMinus'], ['TRB', 'Margin'], ['TRB', 'PTSREBAST'], ['TRB', 'PTSREB'], ['TRB', 'PTSAST'], ['TRB', 'REBAST'], ['AST', 'STL'], ['AST', 'BLK'], ['AST', 'TOV'], ['AST', 'PF'], ['AST', 'PTS'], ['AST', 'GmSc'], ['AST', 'PlusMinus'], ['AST', 'Margin'], ['AST', 'PTSREBAST'], ['AST', 'PTSREB'], ['AST', 'PTSAST'], ['AST', 'REBAST'], ['STL', 'BLK'], ['STL', 'TOV'], ['STL', 'PF'], ['STL', 'PTS'], ['STL', 'GmSc'], ['STL', 'PlusMinus'], ['STL', 'Margin'], ['STL', 'PTSREBAST'], ['STL', 'PTSREB'], ['STL', 'PTSAST'], ['STL', 'REBAST'], ['BLK', 'TOV'], ['BLK', 'PF'], ['BLK', 'PTS'], ['BLK', 'GmSc'], ['BLK', 'PlusMinus'], ['BLK', 'Margin'], ['BLK', 'PTSREBAST'], ['BLK', 'PTSREB'], ['BLK', 'PTSAST'], ['BLK', 'REBAST'], ['TOV', 'PF'],
 ['TOV', 'PTS'], ['TOV', 'GmSc'], ['TOV', 'PlusMinus'], ['TOV', 'Margin'], ['TOV', 'PTSREBAST'], ['TOV', 'PTSREB'], ['TOV', 'PTSAST'], ['TOV', 'REBAST'], ['PF', 'PTS'], ['PF', 'GmSc'], ['PF', 'PlusMinus'], ['PF', 'Margin'], ['PF', 'PTSREBAST'], ['PF', 'PTSREB'], ['PF', 'PTSAST'], ['PF', 'REBAST'], ['PTS', 'GmSc'], ['PTS', 'PlusMinus'], ['PTS', 'Margin'],
 ['PTS', 'PTSREBAST'], ['PTS', 'PTSREB'], ['PTS', 'PTSAST'], ['PTS', 'REBAST'], ['GmSc', 'PlusMinus'], ['GmSc', 'Margin'], ['GmSc', 'PTSREBAST'], ['GmSc', 'PTSREB'], ['GmSc', 'PTSAST'], ['GmSc', 'REBAST'], ['PlusMinus', 'Margin'], ['PlusMinus', 'PTSREBAST'], ['PlusMinus', 'PTSREB'], ['PlusMinus', 'PTSAST'], ['PlusMinus', 'REBAST'], ['Margin', 'PTSREBAST'], ['Margin', 'PTSREB'], ['Margin', 'PTSAST'], ['Margin', 'REBAST'], ['PTSREBAST', 'PTSREB'], ['PTSREBAST', 'PTSAST'], ['PTSREBAST', 'REBAST'], ['PTSREB', 'PTSAST'], ['PTSREB', 'REBAST'], ['PTSAST', 'REBAST']]


corr_filename = 'TeamFiles/League/Roster/corr_file.txt'
os.makedirs(os.path.dirname(corr_filename), exist_ok=True)
corfile = open(corr_filename,'w+')
corfile.write('MP,')
for var in values:
    corfile.write(var[0] + var[1] + ',')
corfile.write('\n')
corfile.close()
TNT = pandas.read_csv('TeamFiles/League/TNT_Schedule.txt')


def playerlog():
    corrdf  = pandas.DataFrame()
    for team in team_list:
        #Create file to write to
        team_filename = str('TeamFiles/League/Roster/' + str(team) + '.txt')
        os.makedirs(os.path.dirname(team_filename), exist_ok=True)
        
        #Get webpage to scrape
        team_url = f'https://www.basketball-reference.com/teams/{team}/2023/gamelog/'
        html = requests.get(team_url).content
        # parse html and load dataframe
        soup = BeautifulSoup(html, 'html.parser')
        team_df = pandas.read_html(team_url)
        team_df = team_df[0]
        
        
        #find location
        loc = team_df['Unnamed: 3_level_0']
        loc = loc.drop(loc[loc['Unnamed: 3_level_1'] == 'Unnamed: 3_level_1'].index, inplace=False)
        loc.rename(mapper = {'Unnamed: 3_level_1': 'Loc'}, axis = 1, inplace = True)
        loc.fillna(value = 10, inplace = True)
        loc.replace(to_replace = '@', value = -10, inplace = True)
        
        #split to unnamed team and opponent and clean dataset        
        dates = team_df['Unnamed: 2_level_0']
        dates = dates.dropna(subset = ['Date'])
        dates = dates.drop(dates[dates['Date'] == 'Date'].index, inplace=False)
        
        
        tmscor = team_df['Unnamed: 6_level_0']
        tmscor = tmscor.dropna(subset = ['Tm'])
        tmscor = tmscor.drop(tmscor[tmscor['Tm'] == 'Tm'].index, inplace=False)
        
        
        oppscor = team_df['Unnamed: 7_level_0']
        oppscor = oppscor.dropna(subset = ['Opp'])
        oppscor = oppscor.drop(oppscor[oppscor['Opp'] == 'Opp'].index, inplace=False)
        
        
        team_ = team_df['Team']
        team_ = team_.drop(team_[team_['3P'] == 'Team'].index, inplace = False)
        team_ = team_.drop(team_[team_['3P'] == '3P'].index, inplace = False)
        team_.rename(columns={col: 'Team_' + col for col in team_.columns}, inplace=True)      
        team_.rename(columns={'Team_FG%':'Team_FGpct','Team_3P%':'Team_3Ppct','Team_FT%':'Team_FTpct'},inplace=True)
        
        
        opp = team_df['Opponent']
        opp = opp.drop(opp[opp['3P'] == 'Opponent'].index, inplace = False)
        opp = opp.drop(opp[opp['3P'] == '3P'].index, inplace = False)
        opp.rename(columns={col: 'Opp_' + col for col in opp.columns}, inplace=True)
        opp.rename(columns={'Opp_FG%':'Opp_FGpct','Opp_3P%':'Opp_3Ppct','Opp_FT%':'Opp_FTpct'},inplace=True)
        
        
        #Recreate original dataframe
        full_df = pandas.concat([dates,loc,tmscor,oppscor,team_,opp],axis = 1)
        full_df[['Team_FGpct','Team_3Ppct','Team_FTpct','Opp_FGpct','Opp_3Ppct','Opp_FTpct']] = full_df[['Team_FGpct','Team_3Ppct','Team_FTpct','Opp_FGpct','Opp_3Ppct','Opp_FTpct']].astype(str).apply(lambda x: x.str.replace('.', ''))
        # Remove last character from all entries 
        full_df[['Team_FGpct','Team_3Ppct','Team_FTpct','Opp_FGpct','Opp_3Ppct','Opp_FTpct']] = full_df[['Team_FGpct','Team_3Ppct','Team_FTpct','Opp_FGpct','Opp_3Ppct','Opp_FTpct']].astype(str).apply(lambda x: x.str[:-1])
        full_df.dropna(subset = ['Team_FG'], inplace = True)
        
        
        
        full_df = full_df.to_csv(index=False)
        team_file = open(team_filename,'w+')
        team_file.write(full_df)
        team_file.close()
        
        #start players
        
        roster = player_list[team]
        for player in roster:
            time.sleep(1)
            if player == 'Gary Trent Jr.':
                playersuffix = '/players/t/trentga02.html'
            if player == 'Clint Capela':
                playersuffix = '/players/c/capelca01.html'
            if player == 'AJ Griffin' :
                playersuffix = '/players/g/griffaj01.html'
            if player == 'Nic Claxton' :
                playersuffix = '/players/c/claxtni01.html'
            if player == 'Jaylen Brown':
                playersuffix == '/players/b/brownja02.html'
            if player == "Royce O'Neale":
                playersuffix = '/players/o/onealro01.html'
            if player == "P.J. Washington":
                playersuffix = '/players/w/washipj01.html'
            if player == "Ayo Dosunmu":
                playersuffix = '/players/d/dosunay01.html'
            if player == "Cedi Osman":
                playersuffix = '/players/o/osmance01.html'
            if player == "Tim Hardaway Jr.":
                playersuffix = '/players/h/hardati02.html'
            if player == "Maxi Kleber":
                playersuffix = '/players/k/klebema01.html'
            if player == "T.J. McConnell":
                playersuffix = '/players/m/mccontj01.html'
            if player == "Jabari Smith Jr.":
                playersuffix = '/players/s/smithja05.html'
            if player == "Jaren Jackson Jr.":
                playersuffix = '/players/j/jacksja02.html'
            if player == "D'Angelo Russell":
                playersuffix = '/players/r/russeda01.html'
            if player == "Larry Nance Jr.":
                playersuffix = '/players/n/nancela02.html'
            if player == "Otto Porter Jr.":
                playersuffix = '/players/p/porteot02.html'
            if player == "Gary Trent Jr.":
                playersuffix = '/players/t/trentga02.html'
            if player == "Gary Trent Jr.":
                playersuffix = '/players/t/trentga02.html'
            if player == "P.J. Tucker":
                playersuffix = '/players/t/tuckepj01.html'
            if player == 'Wendell Carter':
                playersuffix = '/players/c/cartewe02.html'
            if player == 'Jaylin Williams':
                playersuffix = '/players/w/willija07.html'
            else:
                playersuffix = str('/players/' + player[player.find(' ')+1].lower() + '/' + player[player.rfind(' ')+1:player.rfind(' ')+6].lower() + player[0:2].lower() + '01.html')
            
            print(player)
            if playersuffix == '/players/c/capelcl01.html':
                playersuffix = '/players/c/capelca01.html'
            if playersuffix == '/players/b/brownja01.html':
                playersuffix = '/players/b/brownja02.html'
            if playersuffix == "/players/o/o'nearo01.html":
                playersuffix = '/players/o/onealro01.html'
            if playersuffix == '/players/o/jr.ke01.html':
                playersuffix = '/players/o/oubreke01.html'
            if playersuffix == '/players/j/jr.de01.html':
                playersuffix = '/players/j/jonesde01.html'
            if playersuffix == '/players/s/jr.de01.html':
                playersuffix = '/players/s/smithde03.html'
            if playersuffix == '/players/w/waship.01.html':
                playersuffix = '/players/w/washiP.J.01.html'
            if playersuffix == '/players/h/jr.ti01.html':
                playersuffix = '/players/h/hardati02.html'
            if playersuffix == '/players/p/jr.mi01.html':
                playersuffix = '/players/p/portemi01.html'
            if playersuffix == '/players/p/jr.ke01.html':
                playersuffix = '/players/p/porteke02.html'
            if playersuffix == '/players/t/jr.ga01.html':
                playersuffix = '/players/t/trentga02.html'
            if playersuffix == '/players/b/iiima01.html':
                playersuffix = '/players/b/baglema01.html'
            if playersuffix == '/players/m/jr.ke01.html':
                playersuffix = '/players/m/martike04.html'
            if playersuffix == '/players/s/jr.ja01.html':
                playersuffix = '/players/s/smithja05.html'
            if playersuffix == '/players/w/jr.ty01.html':
                playersuffix = '/players/w/washity02.html'
            if playersuffix == '/players/m/mccont.01.html':
                playersuffix = '/players/m/mcconT.J.01.html'
            if playersuffix == '/players/c/jr.we01.html':
                playersuffix = '/players/c/cartewe01.html'
            if playersuffix == '/players/b/jr.tr01.html':
                playersuffix = '/players/b/browntr01.html'
            if playersuffix == '/players/w/ivlo01.html':
                playersuffix = '/players/w/walkelo01.html'
            if playersuffix == '/players/j/jr.ja01.html':
                playersuffix = '/players/j/jacksja02.html'
            if playersuffix == '/players/t/sr.xa01.html':
                playersuffix = '/players/t/tillmxa01.html'
            if playersuffix == "/players/r/russed'01.html":
                playersuffix = '/players/r/russeda01.html'
            if playersuffix == '/players/m/iiitr01.html':
                playersuffix = '/players/m/murphtr01.html'
            if playersuffix == '/players/n/jr.la01.html':
                playersuffix = '/players/n/nancela02.html'
            if playersuffix == '/players/t/tuckep.01.html':
                playersuffix = '/players/t/tuckeP.J.01.html'
            if playersuffix == '/players/p/jrot01.html':
                playersuffix = '/players/p/porteot01.html'
            
            print(playersuffix)
            
            
            playersuffix = playersuffix[:-5]
            
            try:
                player_url = str('https://www.basketball-reference.com' + str(playersuffix) + '/gamelog/2023')
                print(player_url)
                html = requests.get(player_url).content
                # parse html
                soup = BeautifulSoup(html, 'html.parser')                       
                #clean data
                player_df = pandas.read_html(player_url)
            except ValueError:
                try:
                    playersuffix = playersuffix[:-2]
                    playersuffix = str(playersuffix + '02')
                    player_url = str('https://www.basketball-reference.com' + str(playersuffix) + '/gamelog/2023')
                    print(player_url)
                    html = requests.get(player_url).content
                    # parse html
                    soup = BeautifulSoup(html, 'html.parser')
                    #clean data
                    player_df = pandas.read_html(player_url)
                except ValueError:
                    try:
                        playersuffix = playersuffix[:-2]
                        playersuffix = str(playersuffix + '03')
                        player_url = str('https://www.basketball-reference.com' + str(playersuffix) + '/gamelog/2023')
                        print(player_url)
                        html = requests.get(player_url).content
                        # parse html
                        soup = BeautifulSoup(html, 'html.parser')
                        #clean data
                        player_df = pandas.read_html(player_url)
                    except ValueError:
                        try:
                            playersuffix = playersuffix[:-2]
                            playersuffix = str(playersuffix + '04')
                            player_url = str('https://www.basketball-reference.com' + str(playersuffix) + '/gamelog/2023')
                            print(player_url)
                            html = requests.get(player_url).content
                            # parse html
                            soup = BeautifulSoup(html, 'html.parser')
                            #clean data
                            player_df = pandas.read_html(player_url)
                        except ValueError:
                            try:
                                playersuffix = playersuffix[:-2]
                                playersuffix = str(playersuffix + '05')
                                player_url = str('https://www.basketball-reference.com' + str(playersuffix) + '/gamelog/2023')
                                print(player_url)
                                html = requests.get(player_url).content
                                # parse html
                                soup = BeautifulSoup(html, 'html.parser')
                                #clean data
                                player_df = pandas.read_html(player_url)
                            except ValueError:
                                try:
                                    playersuffix = playersuffix[:-2]
                                    playersuffix = str(playersuffix + '06')
                                    player_url = str('https://www.basketball-reference.com' + str(playersuffix) + '/gamelog/2023')
                                    print(player_url)
                                    html = requests.get(player_url).content
                                    # parse html
                                    soup = BeautifulSoup(html, 'html.parser')
                                    #clean data
                                    player_df = pandas.read_html(player_url)
                                except ValueError:
                                    pass

                
            
            
            
            
            player_df = player_df[7]
            player_df = player_df.drop(player_df[player_df['PTS'] == 'PTS'].index, inplace = False)     
            player_df = player_df.drop(player_df[player_df['MP'] == numpy.nan].index, inplace = False)
            player_df = player_df.replace(['Inactive','Did Not Dress','Did Not Play', 'Not With Team', 'Player Suspended'],numpy.nan)
            player_df['GS'] = player_df['GS'].replace({numpy.nan:'-10','1':'10'})
            player_df['GS'] = player_df['GS'].replace('0','-10')
            player_df['3P'] = player_df['3P'].replace(numpy.nan,'0')
            player_df = player_df.rename(columns={'Unnamed: 5':'Location','Unnamed: 7':'Result','+/-':'PlusMinus'})
            player_df['Location'] = player_df['Location'].replace(numpy.nan,'vs')
            player_df['City'] = ''
            player_df['Margin'] = ''
            player_df['PTSREBAST'] = ''
            player_df['PTSREB'] = ''
            player_df['PTSAST'] = ''
            player_df['REBAST'] = ''
            
            
            for index,row in player_df.iterrows():

                #write out game margin as new column
                row['Margin'] = row['Result'].split('(')[1].split(')')[0]
                try:
                    row['PTSREBAST'] = (int(row['PTS'])+int(row['TRB'])+int(row['AST']))
                    row['PTSREB'] = (int(row['PTS'])+int(row['TRB']))
                    row['PTSAST'] = (int(row['PTS'])+int(row['AST']))
                    row['REBAST'] = (int(row['AST'])+int(row['TRB']))
                except ValueError:
                    row['PTSREBAST'] = numpy.nan
                    row['PTSREB'] = numpy.nan
                    row['PTSAST'] = numpy.nan
                    row['REBAST'] = numpy.nan
                
                #set value of column to first two carachters in row - 38:22 is now 38
                try:
                    if row['MP'][1]==':':
                        player_df.loc[index,'MP'] = '0' + row['MP'][:1]
                    player_df.loc[index,'MP']=row['MP'][:2]
                    
                    if row['Location']=='vs':
                        player_df.at[index,'City']=row['Tm']
                    elif row['Location']=='@':
                        player_df.at[index,'City']=row['Opp']
                except TypeError:
                    pass
            player_df['Location'] = player_df['Location'].replace({'@':'-10','vs':'10'})
            player_df = player_df.drop(player_df.columns[7],axis=1)
            
            #player_df['Match'] = player_df.apply(lambda x: 'Yes' if x['Date'] == TNT['Date'].any() and x['Tm'] == TNT['Team2'].any() else 'No', axis=1)
            #print(player_df['Match'])
            #datacleaned
            
            
            #COR MATRIX
            corrdf = player_df[cor_cols]           
            corrdf = corrdf.dropna(subset = ['MP'])
            for index,row in corrdf.iterrows():
                if row['MP'][1]==':':
                    corrdf.loc[index,'MP'] = '0' + row['MP'][:1]
                corrdf.loc[index,'MP']=row['MP'][:2]
                
            
            corrdf['3P'] = corrdf['3P'].replace(numpy.nan,'0')
            #convert the categorical variables to integers using the pandas to_numeric() method
            corrdf = corrdf.replace(numpy.nan, '0')
            corrdf = corrdf.apply(pandas.to_numeric)
            
            totalMP = str(sum(corrdf['MP']))
            
            #create a list of all possible correlations
            my_list = []
            for i in range(len(['MP', 'FG',
                           'FGA', '3P', '3PA', 'FT', 'FTA', 'ORB', 'DRB',
                           'TRB', 'AST', 'STL', 'BLK', 'TOV', 'PF', 'PTS', 'GmSc', 'PlusMinus',
                           'Margin', 'PTSREBAST', 'PTSREB', 'PTSAST', 'REBAST'])):
                for j in range(i+1, len(['MP', 'FG',
                           'FGA', '3P', '3PA', 'FT', 'FTA', 'ORB', 'DRB',
                           'TRB', 'AST', 'STL', 'BLK', 'TOV', 'PF', 'PTS', 'GmSc', 'PlusMinus',
                           'Margin', 'PTSREBAST', 'PTSREB', 'PTSAST', 'REBAST'])):
                    my_list.append([['MP', 'FG',
                           'FGA', '3P', '3PA', 'FT', 'FTA', 'ORB', 'DRB',
                           'TRB', 'AST', 'STL', 'BLK', 'TOV', 'PF', 'PTS', 'GmSc', 'PlusMinus',
                           'Margin', 'PTSREBAST', 'PTSREB', 'PTSAST', 'REBAST'][i],['MP', 'FG',
                           'FGA', '3P', '3PA', 'FT', 'FTA', 'ORB', 'DRB',
                           'TRB', 'AST', 'STL', 'BLK', 'TOV', 'PF', 'PTS', 'GmSc', 'PlusMinus',
                           'Margin', 'PTSREBAST', 'PTSREB', 'PTSAST', 'REBAST'][j]])
            
           
            r_df = []
            r_df.append([player,','])
            #calculate covariance
            for comb in my_list:
                cov_xy = np.cov(corrdf[comb[0]], corrdf[comb[1]])[0][1]

                #calculate standard deviation
                std_x = np.std(corrdf[comb[0]])
                std_y = np.std(corrdf[comb[1]])

                #calculate r value
                try:
                    r = cov_xy / (std_x * std_y)
                except RuntimeWarning:
                    r = '0'
                
                
                #print results
                
                r_df.append([r,','])

   
            
            if '.' in player:
                player = player.replace('.','')
            
            filename = 'TeamFiles/League/Roster/Players/' + str(player.replace(' ','') + '.txt')
            print(filename)
            os.makedirs(os.path.dirname(filename), exist_ok=True)
            teamcsv = player_df.to_csv(index=False)
            file = open(filename,'w+')
            file.write(teamcsv)
            file.close()
            
            
            
            
            corfile = open(corr_filename,'a+')
            corfile.write(totalMP + ',')
            for element in r_df:
                for unit in element:
                    corfile.write(str(unit))
            corfile.write('\n')
            corfile.close()
            
        





def team_splits():
    for team in team_list:
        team_filename = str('TeamFiles/League/Roster/TeamSplits/' + team + '.txt')
        os.makedirs(os.path.dirname(team_filename), exist_ok=True)
        
        # condense code
        team_url = str('https://www.basketball-reference.com/teams/' + team + '/2023/splits/')
        html = requests.get(team_url).content
        soup = BeautifulSoup(html, 'html.parser')
        full_df = pandas.read_html(team_url)[0]

        # Create dataframes for names, teams, and opponents
        names_df = full_df['Unnamed: 1_level_0'].drop(full_df['Unnamed: 1_level_0'][full_df['Unnamed: 1_level_0']['Value'] == 'Value'].index)
        games_df = full_df['Unnamed: 2_level_0'].drop(full_df['Unnamed: 2_level_0'][full_df['Unnamed: 2_level_0']['G'] == 'G'].index)
        wins_df = full_df['Unnamed: 3_level_0'].drop(full_df['Unnamed: 3_level_0'][full_df['Unnamed: 3_level_0']['W'] == 'W'].index)
        losses_df = full_df['Unnamed: 4_level_0'].drop(full_df['Unnamed: 4_level_0'][full_df['Unnamed: 4_level_0']['L'] == 'L'].index)
        team_df = full_df['Team'].drop(full_df['Team'][full_df['Team']['PTS'] == 'PTS'].index)
        team_df = team_df.rename(columns = lambda x: f'Team{x}')
        opp_df = full_df['Opponent'].drop(full_df['Opponent'][full_df['Opponent']['PTS'] == 'PTS'].index)
        opp_df = opp_df.rename(columns = lambda x: f'Opp{x}')

        #concatenate all dataframes
        concat_dfs = pandas.concat([names_df, games_df, wins_df, losses_df, team_df, opp_df], axis = 1)
        
        #print the concatenated dataframe
        print(concat_dfs)
        
        #save to csv and file
        concat_dfs = concat_dfs.to_csv(index=False)
        file = open(team_filename,'w+')
        file.write(concat_dfs)
        file.close()


def team_splits_analysis():
    dataframes = {}
    cols = []
    for team in team_list:
        team_filename = str('TeamFiles/League/Roster/TeamSplits/' + team + '.txt')
        df = pandas.read_csv(team_filename)
        df = df.set_index('Value')
        df['TeamFGpct'] = df['TeamFG']/df['TeamFGA']
        df['OppFGpct'] = df['OppFG']/df['OppFGA']
        df['Winpct'] = df['W']/(df['W']+df['L'])
        dataframes[team] = df
        cols = []
        for e in df.columns:
            cols.append(e)
    print(cols)      
    
    
    #will contain all team column/row values (ie. OPPPTSFeburary or TEAMFGAtlanta)
    league_dict = {}
    for team in team_list:
        keys = {}
        for e in cols:
            df = dataframes[team]
            for i in range(len(df)):
                col = df.iloc[i]
                #print('col',col)
                val = col[e]               
                #val is the value per column of the 'col' row
               
                keyname = str(df.index[i] + e)
                #print(keyname)
               
                #assigns the team splits to its own dictionary
                keys[keyname] = val
                #print(e,df.index[i],val)
        #print(keys)
       
        #assign team dict to league dict
        league_dict[team] = keys    
        
    variable_names = [list(d.keys()) for d in league_dict.values()]
    common_variables = list(set.intersection(*map(set,variable_names)))
    data = {team: {var: league_dict[team][var] for var in common_variables} for team in league_dict}
    df = pandas.DataFrame(data).T
    df.columns = common_variables
    print(df)
    
    
    df = df.to_csv()
    league_filename = str('TeamFiles/League/Roster/TeamSplits/league_splits.txt')
    os.makedirs(os.path.dirname(league_filename), exist_ok=True)
    file = open(league_filename,'w')
    file.write(df)
    file.close()
    
    
 






#Call functions
def call_func():    
    playerlog()
    team_splits()
    team_splits_analysis()
    
call_func()















def playerids():
    from nba_api.stats.static import players
    player_ids = {}

    for team in team_list:
        roster = player_list[team]
        for player in roster:
            try:
                if player == 'OG Anunoby':
                    player = 'O.G. Anunoby'
                player_ids[player] = players.find_players_by_full_name(player)[0]['id']
                
            except IndexError:
                print(f'player error: {player}')
                


    player_ids['OG Anunoby'] = player_ids.pop('O.G. Anunoby')
    player_ids_df = pandas.DataFrame(list(player_ids.items()), columns=['Name', 'ID'])
    player_ids_df = player_ids_df.to_csv(index = False)
    team_filename = (f'TeamFiles/League/Roster/playerids/playerids.txt')
    os.makedirs(os.path.dirname(team_filename), exist_ok=True)
    file = open(team_filename,'w')
    file.write(player_ids_df)
    file.close()








