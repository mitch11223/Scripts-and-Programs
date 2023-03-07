#
# This is a Shiny web application. You can run the application by clicking
# the 'Run App' button above.
#
# Find out more about building applications with Shiny here:
#
#    http://shiny.rstudio.com/
#

library(shiny)
library(maps)
library(mapproj)
library(ggplot2)
library(dplyr)
library(tidyverse)
library(plotly)
library(DT)
library(MASS)
library(rpart)
library(stringr)

# Define UI for application that draws a histogram
ui <- fluidPage(
  
  # Application title
  titlePanel("Test NBA Charts"),
  
  sidebarLayout(
  sidebarPanel(
            selectInput(inputId = "Teams",
                label = 'Select Team:',
                choices = list(
                  'ATL','BOS','BRK','CHO','CHI','CLE','DAL','DEN','DET','GSW','HOU','IND','LAC','LAL','MEM',
                  'MIA','MIL','MIN','NOP','NYK','OKC','ORL','PHI','PHO','POR','SAC','SAS','TOR','UTA','WAS')),
            uiOutput("second_input"),
            
            selectInput(inputId = "teamstats",
                        label = 'Team/Opp Stat',
                        choices = list('NULL' = '','Tm','Opp','Team_FG','Team_FGA','Team_FGpct','Team_3P','Team_3PA','Team_3Ppct','Team_FT','Team_FTA','Team_FTpct','Team_ORB','Team_TRB','Team_AST','Team_STL','Team_BLK','Team_TOV','Team_PF',
                                       'Opp_FG','Opp_FGA','Opp_FGpct','Opp_3P','Opp_3PA','Opp_3Ppct','Opp_FT','Opp_FTA','Opp_FTpct','Opp_ORB','Opp_TRB','Opp_AST','Opp_STL','Opp_BLK','Opp_TOV','Opp_PF'),
                        selected = NULL),
           
            
            sliderInput('dates', 'Date Range:',
                min = as.Date('2022-10-19'),
                max = as.Date('2023-04-10'),
                value = c(as.Date('2022-10-19'), as.Date('2023-04-10'))),
           textInput('usrval','Draw Line Where(y-int):'),
    
           selectInput(
             "PlayerVariable1",
             h3("Variable"),
             choices = list(
               'NULL' = '',
               'Minutes' = 'MP',
               'FG' = 'FG',
               'FGA' = 'FGA',
               '3P' = 'X3P',
               '3PA' = 'X3PA',
               'FT' = 'FT',
               'FTA' = 'FTA',
               'ORB' = 'ORB',
               'DRB' = 'DRB',
               'TRB' = 'TRB',
               'AST' = 'AST',
               'STL' = 'STL',
               'BLK' = 'BLK',
               'TOV' = 'TOV',
               'Game Score' = 'GmSc',
               'PlusMinus' = "PlusMinus",
               'PTS' = 'PTS',
               'GameResult' = 'Margin',
               'GameStarted' = 'GS',
               'PersonalFouls' = 'PF',
               'PTS_REB_AST' = "PTSREBAST",
               'PTS_REB' = "PTSREB",
               'PTS_AST' = "PTSAST",
               'REB_AST' = "REBAST"),
             selected = 'PTS'),
           
           selectInput(
             "PlayerVariable2",
             h3("Variable(optional)"),
             choices = list(
               "NULL" = "",
               'Minutes' = 'MP',
               'FG' = 'FG',
               'FGA' = 'FGA',
               '3P' = 'X3P',
               '3PA' = 'X3PA',
               'FT' = 'FT',
               'FTA' = 'FTA',
               'ORB' = 'ORB',
               'DRB' = 'DRB',
               'TRB' = 'TRB',
               'AST' = 'AST',
               'STL' = 'STL',
               'BLK' = 'BLK',
               'TOV' = 'TOV',
               'Game Score' = 'GmSc',
               'PlusMinus' = "PlusMinus",
               'PTS' = 'PTS',
               'GameResult' = 'Margin',
               'GameStarted' = 'GS',
               'PersonalFouls' = 'PF',
               'PTS_REB_AST' = "PTSREBAST",
               'PTS_REB' = "PTSREB",
               'PTS_AST' = "PTSAST",
               'REB_AST' = "REBAST"),
                selected = NULL),
  ),
  
    mainPanel(
           plotOutput("corrMatrix"),
           
           column(10,
                  
           verbatimTextOutput("Var")),
            
    fluidRow(
      column(10,
             paste("Blue Vertical Line 2023-02-09 : Trade Deadline"))
      ),
      
    fluidRow(
      column(8,
             paste('DOTTED LINES == MISSED GAMES/DID NOT PLAY'),
             DTOutput('cor')),
      column(8,
             DT::dataTableOutput('PLYRTABLE'))
    )
  )
         
))


# Define server logic required to draw a histogram
server <- function(input, output,session) {
  output$second_input <- renderUI({
    
    
    if(input$Teams=='ATL'){
      selectInput(inputId = 'second',"Choose a Player",
                  choices = c('SaddiqBey','ClintCapela', 'JohnCollins', 'JarrettCulver', 'TrentForrest', 'AJGriffin', 'AaronHoliday', 'JustinHoliday', "De'AndreHunter", 'JalenJohnson', 'FrankKaminsky', 'DejounteMurray', 'OnyekaOkongwu', 'TraeYoung'))
    } else if(input$Teams =="BOS") {
      selectInput(inputId = 'second',"Choose a Player",
                  choices = c('MalcolmBrogdon', 'JaylenBrown', 'BlakeGriffin', 'AlHorford', 'MfionduKabengele', 'LukeKornet','MikeMuscala','PaytonPritchard', 'MarcusSmart', 'JaysonTatum', 'NoahVonleh', 'DerrickWhite', 'GrantWilliams'))
    } else if(input$Teams=='BRK'){
      selectInput(inputId = 'second',"Choose a Player",
                  choices = c('MikalBridges','NicClaxton', 'SethCurry','SpencerDinwiddie','JoeHarris', 'CamJohnson','DorianFinney-Smith','Spencer Dinwiddie','PattyMills', "RoyceO'Neale", 'BenSimmons', 'EdmondSumner', 'CamThomas', 'YutaWatanabe'))
    } else if(input$Teams=='CHO'){
      selectInput(inputId = 'second',"Choose a Player",
                  choices = c('LaMeloBall','JamesBouknight','GordonHayward','KaiJones','TheoMaledon','CodyMartin','KellyOubreJr','NickRichards','TerryRozier','DennisSmithJr','PJWashington'))
    } else if(input$Teams=='CHI'){
      selectInput(inputId = 'second',"Choose a Player",
                  choices = c('PatrickBeverley','TonyBradley','AlexCaruso','DeMarDeRozan','GoranDragic','AndreDrummond','JavonteGreen','DerrickJonesJr','ZachLaVine','MarkoSimonovic','NikolaVucevic','CobyWhite','PatrickWilliams'))
    } else if(input$Teams=='CLE'){
      selectInput(inputId = 'second',"Choose a Player",
                  choices = c('JarrettAllen','MamadiDiakite','DariusGarland','CarisLeVert','RobinLopez','KevinLove','DonovanMitchell','EvanMobley','RaulNeto','IsaacOkoro','LamarStevens','DeanWade'))
    } else if(input$Teams=='DAL'){
      selectInput(inputId = 'second',"Choose a Player",
                  choices = c('DavisBertans','ReggieBullock','LukaDoncic','TylerDorsey','JoshGreen','TimHardawayJr','JadenHardy','KyrieIrving','JaValeMcGee','MarkieffMorris','DwightPowell','ChristianWood'))
    } else if(input$Teams=='DEN'){
      selectInput(inputId = 'second',"Choose a Player",
                  choices = c('BruceBrown','ThomasBryant','KentaviousCaldwell-Pope','VlatkoCancar','AaronGordon','JeffGreen','ReggieJackson','NikolaJokic','DeAndreJordan','JamalMurray','ZekeNnaji','MichaelPorterJr','IshSmith'))
    } else if(input$Teams=='DET'){
      selectInput(inputId = 'second',"Choose a Player",
                  choices = c('MarvinBagleyIII','BojanBogdanovic','AlecBurks','CadeCunningham','HamidouDiallo','JalenDuren','KillianHayes','JadenIvey','CoryJoseph','IsaiahLivers','RodneyMcGruder','IsaiahStewart','JamesWiseman'))
    } else if(input$Teams=='GSW'){
      selectInput(inputId = 'second',"Choose a Player",
                  choices = c('StephenCurry','DonteDiVincenzo','DraymondGreen','JaMychalGreen','TyJerome','JonathanKuminga','AnthonyLamb','KevonLooney','MosesMoody','JordanPoole','KlayThompson','AndrewWiggins'))
    } else if(input$Teams=='HOU'){
      selectInput(inputId = 'second',"Choose a Player",
                  choices = c('JoshChristopher','TariEason','BrunoFernando','UsmanGaruba','JalenGreen','BobanMarjanovic','KenyonMartinJr','GarrisonMathews','KevinPorterJr','AlperenSengun','JabariSmithJr',"JaeSeanTate",'TyTyWashingtonJr'))
    } else if(input$Teams=='IND'){
      selectInput(inputId = 'second',"Choose a Player",
                  choices = c('GogaBitadze','OshaeBrissett','ChrisDuarte','TyreseHaliburton','BuddyHield','GeorgeHill','SergeIbaka','IsaiahJackson','JamesJohnson','BennedictMathurin','TJMcConnell','AndrewNembhard','AaronNesmith','JordanNwora','JalenSmith','MylesTurner'))
    } else if(input$Teams=='LAC'){
      selectInput(inputId = 'second',"Choose a Player",
                  choices = c('NicolasBatum','MosesBrown','AmirCoffey','RobertCovington','PaulGeorge','EricGordon','BonesHyland','KawhiLeonard','TeranceMann','MarcusMorris','MasonPlumlee','NormanPowell','RussellWestbrook','IvicaZubac'))
    } else if(input$Teams=='LAL'){
      selectInput(inputId = 'second',"Choose a Player",
                  choices = c('MoBamba','MalikBeasley','TroyBrownJr','AnthonyDavis','WenyenGabriel','LeBronJames','DamianJones','RuiHachimura','AustinReaves',"D'AngeloRussell",'DennisSchroder','JarredVanderbilt','LonnieWalkerIV'))
    } else if(input$Teams=='MEM'){
      selectInput(inputId = 'second',"Choose a Player",
                  choices = c('StevenAdams','SantiAldama','DesmondBane','DillonBrooks','BrandonClarke','JarenJacksonJr','TyusJones','LukeKennard','JohnKonchar','JakeLaRavia','JaMorant','DavidRoddy','XavierTillmanSr'))
    } else if(input$Teams=='MIA'){
      selectInput(inputId = 'second',"Choose a Player",
                  choices = c('BamAdebayo','JimmyButler','JamalCain','DewayneDedmon','UdonisHaslem','TylerHerro','HaywoodHighsmith','NikolaJovic','KyleLowry','CalebMartin','DuncanRobinson','VictorOladipo','MaxStrus','GabeVincent'))
    } else if(input$Teams=='MIL'){
      selectInput(inputId = 'second',"Choose a Player",
                  choices = c('GraysonAllen','GiannisAntetokounmpo','MarJonBeauchamp','JevonCarter','PatConnaughton','JaeCrowder','JrueHoliday','BrookLopez','WesleyMatthews','BobbyPortis'))
    } else if(input$Teams=='MIN'){
      selectInput(inputId = 'second',"Choose a Player",
                  choices = c('NickeilAlexander-Walker','KyleAnderson','MikeConley','AnthonyEdwards','BrynForbes','RudyGobert','JadenMcDaniels','JordanMcLaughlin','JaylenNowell','TaureanPrince','NazReid','AustinRivers','Karl-AnthonyTowns'))
    } else if(input$Teams=='NOP'){
      selectInput(inputId = 'second',"Choose a Player",
                  choices = c('JoseAlvarado','DysonDaniels','JaxsonHayes','WillyHernangomez','BrandonIngram','HerbertJones','NajiMarshall','CJMcCollum','TreyMurphyIII','LarryNanceJr','JoshRichardson','JonasValanciunas','ZionWilliamson'))
    } else if(input$Teams=='NYK'){
      selectInput(inputId = 'second',"Choose a Player",
                  choices = c('RJBarrett','JalenBrunson','EvanFournier','QuentinGrimes','JoshHart','IsaiahHartenstein','MilesMcBride','ImmanuelQuickley','JuliusRandle','MitchellRobinson','DerrickRose','JerichoSims','ObiToppin'))
    } else if(input$Teams=='OKC'){
      selectInput(inputId = 'second',"Choose a Player",
                  choices = c('OusmaneDieng','LuguentzDort','JoshGiddey','ShaiGilgeous-Alexander','IsaiahJoe','TreMann','AleksejPokusevski','JeremiahRobinson-Earl','DarioSaric','AaronWiggins','JalenWilliams','JaylinWilliams','KenrichWilliams'))
    } else if(input$Teams=='ORL'){
      selectInput(inputId = 'second',"Choose a Player",
                  choices = c('ColeAnthony','MoBamba','PaoloBanchero','BolBol','WendellCarterJr','MarkelleFultz','GaryHarris','CalebHoustan','ChumaOkeke','TerrenceRoss','AdmiralSchofield','JalenSuggs','FranzWagner','MoritzWagner'))
    } else if(input$Teams=='PHI'){
      selectInput(inputId = 'second',"Choose a Player",
                  choices = c('JoelEmbiid','JamesHarden','MontrezlHarrell','TobiasHarris','FurkanKorkmaz','TyreseMaxey','JalenMcDaniels',"De'AnthonyMelton",'ShakeMilton','GeorgesNiang','PaulReed','PJTucker'))
    } else if(input$Teams=='PHO'){
      selectInput(inputId = 'second',"Choose a Player",
                  choices = c('DeandreAyton','DariusBazley','BismackBiyombo','DevinBooker','TorreyCraig','KevinDurant','JockLandale','DamionLee','JoshOkogie','ChrisPaul','CameronPayne','LandryShamet','TJWarren'))
    } else if(input$Teams=='POR'){
      selectInput(inputId = 'second',"Choose a Player",
                  choices = c('DrewEubanks','JeramiGrant','KeonJohnson','KevinKnox','DamianLillard','NassirLittle','JusufNurkic','CamReddish','ShaedonSharpe','AnferneeSimons','MatisseThybulle','TrendonWatford','JustiseWinslow'))
    } else if(input$Teams=='SAC'){
      selectInput(inputId = 'second',"Choose a Player",
                  choices = c('HarrisonBarnes','TerenceDavis','MatthewDellavedova','KeonEllis',"De'AaronFox",'RichaunHolmes','KevinHuerter','AlexLen','TreyLyles','ChimezieMetu','DavionMitchell','MalikMonk','KeeganMurray','KZOkpala','DomantasSabonis'))
    } else if(input$Teams=='SAS'){
      selectInput(inputId = 'second',"Choose a Player",
                  choices = c('CharlesBassey','KeitaBates-Diop','MalakiBranham','ZachCollins','GorguiDieng',"DevontaGraham",'KeldonJohnson','TreJones','RomeoLangford','DougMcDermott','IsaiahRoby','JeremySochan','DevinVassell','BlakeWesley'))
    } else if(input$Teams=='TOR'){
      selectInput(inputId = 'second',"Choose a Player",
                  choices = c('PreciousAchiuwa','OGAnunoby','DalanoBanton','ScottieBarnes','ChrisBoucher','MalachiFlynn','ChristianKoloko','JakobPoeltl','OttoPorterJr','PascalSiakam','GaryTrentJr','FredVanVleet','ThaddeusYoung'))
    } else if(input$Teams=='UTA'){
      selectInput(inputId = 'second',"Choose a Player",
                  choices = c('NickeilAlexander-Walker','JordanClarkson','RudyGay','TalenHorton-Tucker','WalkerKessler','LauriMarkkanen','KellyOlynyk','CollinSexton'))
    } else if(input$Teams=='WAS'){
      selectInput(inputId = 'second',"Choose a Player",
                  choices = c('DeniAvdija','WillBarton','BradleyBeal','DanielGafford','TajGibson','AnthonyGill','KendrickNunn','CoreyKispert','KyleKuzma','MonteMorris','KristapsPorzingis','DelonWright'))
    }  
  })
  
  
  output$cor <- renderDT({
    file <- read.csv('Roster/corr_file.txt')
    column <- paste(input$PlayerVariable1,input$PlayerVariable2)
    column <- str_replace_all(column, fixed(" "), "")
    column2 <- paste(input$PlayerVariable2,input$PlayerVariable1)
    column2 <- str_replace_all(column2, fixed(" "), "")
    
    tryCatch({
      file[c('Player','MP',column),drop=FALSE]
    }, error=function(e) {
      file[c('Player','MP',column2),drop=FALSE]
    })
  })
  
  
  output$PLYRTABLE <- DT::renderDataTable ({
    filename <- paste('Roster/Players/',input$second,'.txt',sep="")
    file = read.csv(filename)
    datatable(file)
  })
  output$Var <- renderPrint({
    filename <- paste('Roster/Players/',input$second,'.txt',sep="")
    file = read.csv(filename)
    file <- file[which(file$Date >= input$dates[1] & file$Date <= input$dates[2]),]
    
    teamfilename <- paste('Roster/',input$Teams,'.txt',sep="")
    teamfile = read.csv(teamfilename)
    teamfile <- teamfile[which(teamfile$Date >= input$dates[1] & teamfile$Date <= input$dates[2]),]
    
    if (input$PlayerVariable1 != '' && input$PlayerVariable2 == "" && input$teamstats != '') {
      VAR_1 <- file[,input$PlayerVariable1]
      TEAM_VAR <- teamfile[,input$teamstats]
      Vector <- cbind(VAR_1,TEAM_VAR)
      Vector <- na.omit(Vector)
      print(cor(Vector))
      #Metrics
      summary(na.omit(VAR_1))
      summary(na.omit(TEAM_VAR))
    } else if (input$PlayerVariable1 != '' && input$PlayerVariable2 == '' && input$teamstats == '') {
      VAR_1 <- file[,input$PlayerVariable1]
      #Metrics
      summary(na.omit(VAR_1))
    } else if (input$PlayerVariable1 != '' && input$PlayerVariable2 != '' && input$teamstats == '') {
      VAR_1 <- file[,input$PlayerVariable1]
      VAR_2 <- file[,input$PlayerVariable2]
      Vector <- cbind(VAR_1,VAR_2)
      Vector <- na.omit(Vector)
      print(cor(Vector))
      
    } else if (input$teamstats != '' && input$PlayerVariable1 == '' && input$PlayerVariable2 == '') {
      T_VAR <- teamfile[,input$teamstats]
      summary(na.omit(T_VAR))
    }
  })
  
  output$corrMatrix <- renderPlot({
    
    filename <- paste('Roster/Players/',input$second,'.txt',sep="")
    file = read.csv(filename)
    file <- file[which(file$Date >= input$dates[1] & file$Date <= input$dates[2]),]
    
    teamfilename <- paste('Roster/',input$Teams,'.txt',sep="")
    teamfile = read.csv(teamfilename)
    teamfile <- teamfile[which(teamfile$Date >= input$dates[1] & teamfile$Date <= input$dates[2]),]

    
    if (input$PlayerVariable2 == "" && input$usrval == "" && input$teamstats == "" ) {
      ggplot(file,mapping = aes_string(x=as.Date(file$Date),y=input$PlayerVariable1)) + 
        geom_line(mapping = aes(group = 1),color="black",size=2) +
        geom_line(stat = 'summary', fun = "mean",linetype='twodash') +
        geom_smooth(mapping = aes_string(y = input$PlayerVariable1), method='lm',color="red") +
        geom_point(color = '#FFFFFF') +
        geom_vline(xintercept = as.Date('2023-02-09'),color='blue') +
        labs(x = 'Dates - 2022-2023',colour = "Legend Title")
    } else if (input$PlayerVariable1 == '' && input$PlayerVariable2 == '' && input$usrval == '' && input$teamstats != '') {
      ggplot(teamfile,mapping = aes_string(x=as.Date(teamfile$Date),y=input$teamstats)) +
        geom_line(mapping = aes(group = 1),color="black",size=2) +
        geom_line(stat = 'summary', fun = "mean",linetype='twodash') +
        geom_smooth(mapping = aes_string(y = input$teamstats), method='lm',color="red") +
        geom_point(color = '#FFFFFF') +
        geom_vline(xintercept = as.Date('2023-02-09'),color='blue') +
        labs(x = 'Dates - 2022-2023',colour = "Legend Title")
    } else if (input$PlayerVariable1 == '' && input$PlayerVariable2 == '' && input$usrval != '' && input$teamstats != '') {
      ggplot(teamfile,mapping = aes_string(x=as.Date(teamfile$Date),y=input$teamstats)) +
        geom_line(mapping = aes(group = 1),color="black",size=2) +
        geom_line(stat = 'summary', fun = "mean",linetype='twodash') +
        geom_smooth(mapping = aes_string(y = input$teamstats), method='lm',color="red") +
        geom_line(mapping = aes_string(y = input$usrval),color = 'blue',size = 2,linetype='longdash') +
        geom_point(color = '#FFFFFF') +
        geom_vline(xintercept = as.Date('2023-02-09'),color='blue') +
        labs(x = 'Dates - 2022-2023',colour = "Legend Title")
    } else if (input$PlayerVariable2 == "" && input$usrval != "" && input$teamstats == "" ) {
      ggplot(file,mapping = aes_string(x=as.Date(file$Date),y=input$PlayerVariable1)) + 
        geom_line(mapping = aes(group = 1),color="black",size=2) +
        geom_line(stat = 'summary', fun = "mean",linetype='twodash') +
        geom_smooth(mapping = aes_string(y = input$PlayerVariable1), method='lm',color="red") +
        geom_vline(xintercept = as.Date('2023-02-09'),color='blue') +
        geom_point(color = '#FFFFFF') +
        geom_line(mapping = aes_string(y = input$usrval),color = 'blue',size = 2,linetype='longdash') +
        labs(x = 'Dates - 2022-2023',colour = "Legend Title") 
    } else if (input$PlayerVariable2 != "" && input$usrval != "" && input$teamstats == "" ) {
      ggplot(file,mapping = aes_string(x=as.Date(file$Date),y=input$PlayerVariable1)) + 
        geom_line(mapping = aes(group = 1),color="black",size=2) +
        geom_line(mapping = aes_string(x=as.Date(file$Date),y=input$PlayerVariable2),color=("#509901"),size = 2) +
        geom_line(stat = 'summary', fun = "mean",linetype='twodash')  +
        geom_point(color = '#FFFFFF') +
        geom_vline(xintercept = as.Date('2023-02-09'),color='blue') +
        geom_line(mapping = aes_string(y = input$usrval),color = 'blue',size = 2,linetype='longdash') +
        labs(x = 'Dates - 2022-2023',colour = "Legend Title") +
        scale_color_manual("",values = c("black","red"))
    } else if (input$PlayerVariable2 != "" && input$usrval == "" && input$teamstats == "" ){
      ggplot(file,mapping = aes_string(x=as.Date(file$Date),y=input$PlayerVariable1)) + 
        geom_line(mapping = aes(group = 1),color="black",size=2) +
        geom_line(mapping = aes_string(x=as.Date(file$Date),y=input$PlayerVariable2),color=("#509901"),size = 2) +
        geom_line(stat = 'summary', fun = "mean",linetype='twodash')  +
        geom_point(color = '#FFFFFF') +
        geom_vline(xintercept = as.Date('2023-02-09'),color='blue') +
        labs(x = 'Dates - 2022-2023',colour = "Legend Title") +
        scale_color_manual("",values = c("black","red"))
    } else if (input$PlayerVariable2 == "" && input$usrval == "" && input$teamstats != ""){
      ggplot(file,mapping = aes_string(x=as.Date(file$Date),y=input$PlayerVariable1)) + 
        geom_line(mapping = aes(group = 1),color="black",size=2) +
        geom_line(teamfile,mapping = aes_string(x=as.Date(teamfile$Date),y=input$teamstats),color = 'green',size = 2,linetype='dotted') +
        geom_line(stat = 'summary', fun = "mean",linetype='twodash')  +
        geom_point(color = '#FFFFFF') +
        geom_vline(xintercept = as.Date('2023-02-09'),color='blue') +
        labs(x = 'Dates - 2022-2023',colour = "Legend Title") +
        scale_color_manual("",values = c("black","red","green"))
    } else if (input$PlayerVariable2 == "" && input$usrval != "" && input$teamstats != ""){
      ggplot(file,mapping = aes_string(x=as.Date(file$Date),y=input$PlayerVariable1)) + 
        geom_line(mapping = aes(group = 1),color="black",size=2) +
        geom_line(teamfile,mapping = aes_string(x=as.Date(teamfile$Date),y=input$teamstats),color = 'green',size = 2,linetype='dotted') +
        geom_line(stat = 'summary', fun = "mean",linetype='twodash')  +
        geom_line(mapping = aes_string(y = input$usrval),color = 'blue',size = 2,linetype='longdash') +
        geom_point(color = '#FFFFFF') +
        geom_vline(xintercept = as.Date('2023-02-09'),color='blue') +
        labs(x = 'Dates - 2022-2023',colour = "Legend Title") +
        scale_color_manual("",values = c("black","red","green"))
    } else if (input$PlayerVariable2 != "" && input$usrval != "" && input$teamstats != ""){
      ggplot(file,mapping = aes_string(x=as.Date(file$Date),y=input$PlayerVariable1)) + 
        geom_line(mapping = aes(group = 1),color="black",size=2) +
        geom_line(mapping = aes_string(x=as.Date(file$Date),y=input$PlayerVariable2),color=("#509901"),size = 2) +
        geom_line(teamfile,mapping = aes_string(x=as.Date(teamfile$Date),y=input$teamstats),color = 'green',size = 2,linetype='dotted') +
        geom_line(stat = 'summary', fun = "mean",linetype='twodash')  +
        geom_line(mapping = aes_string(y = input$usrval),color = 'blue',size = 2,linetype='longdash') +
        geom_point(color = '#FFFFFF') +
        geom_vline(xintercept = as.Date('2023-02-09'),color='blue') +
        labs(x = 'Dates - 2022-2023',colour = "Legend Title") +
        scale_color_manual("",values = c("black","red","green"))
    } else if (input$PlayerVariable2 != "" && input$usrval == "" && input$teamstats != ""){
      ggplot(file,mapping = aes_string(x=as.Date(file$Date),y=input$PlayerVariable1)) + 
        geom_line(mapping = aes(group = 1),color="black",size=2) +
        geom_line(mapping = aes_string(x=as.Date(file$Date),y=input$PlayerVariable2),color=("#509901"),size = 2) +
        geom_line(teamfile,mapping = aes_string(x=as.Date(teamfile$Date),y=input$teamstats),color = 'green',size = 2,linetype='dotted') +
        geom_line(stat = 'summary', fun = "mean",linetype='twodash')  +
        geom_point(color = '#FFFFFF') +
        geom_vline(xintercept = as.Date('2023-02-09'),color='blue') +
        labs(x = 'Dates - 2022-2023',colour = "Legend Title") +
        scale_color_manual("",values = c("black","red","green"))
    }
  })  
}

# Run the application 
shinyApp(ui = ui, server = server)
#rsconnect::deployApp("/Volumes/Backup/Server/TeamFiles/League/")