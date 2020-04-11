import discord,json,os,re,httplib2,time,datetime
from apiclient import discovery
from google.oauth2 import service_account

client = discord.Client()

with open("Config/token.json") as token_file:
    tokens = json.load(token_file)
    
with open("Config/config.json") as config_file:
    config = json.load(config_file);

scopes = ["https://www.googleapis.com/auth/spreadsheets"]
secret_file = "Config/client_secret.json"
credentials = service_account.Credentials.from_service_account_file(secret_file, scopes=scopes)
service = discovery.build('sheets','v4',credentials=credentials)
    
warninglogid = tokens["warninglogid"]

def get_warnings():
    global warninglogid
    response = service.spreadsheets().values().get(spreadsheetId = warninglogid, range = "Warnings!A2:G", majorDimension="ROWS", valueRenderOption = "UNFORMATTED_VALUE").execute()
    return response["values"]

def get_kicks():
    global warninglogid
    response = service.spreadsheets().values().get(spreadsheetId = warninglogid, range = "Kicks!A2:G", majorDimension="ROWS", valueRenderOption = "UNFORMATTED_VALUE").execute()
    return response["values"]

def get_bans():
    global warninglogid
    response = service.spreadsheets().values().get(spreadsheetId = warninglogid, range = "Bans!A2:G", majorDimension="ROWS", valueRenderOption = "UNFORMATTED_VALUE").execute()
    return response["values"]
    
warnings = get_warnings()
kicks = get_kicks()
bans = get_bans()

@client.event
async def on_ready():
    global warnings
    warnings = get_warnings()
    print('We have logged in as {0.user}'.format(client))

@client.event
async def on_message(message):
    global warnings
    global kicks
    global bans
    if message.author == client.user:
        return
    if not (message.content.startswith(config["prefix"])):
        return
    args = (message.content[1:]).split(" ")
    command = args.pop(0)
    #perms means the permission the user has: developer -> 40, has admin rights (ie csuite+ and admin+) -> 31, moderator -> 30, Other HRs -> 20, verified members -> 11, message sent in DM -> 10, all users -> 0
    perms = 0
    if message.author.id in [156390113654341632,463016897110343690,676596209627955231]: 
        perms = 40 
    elif isinstance(message.channel, discord.abc.GuildChannel):
        if message.author.guild_permissions.administrator:
            perms = 31
        else:
            for role in message.author.roles:
                if role.id == 348722815903596545 and perms < 30:
                    perms = 30
                if role.id == 436418888704720896 and perms < 20:
                    perms = 20
                if role.id == 359604396276973570 and perms < 11:
                    perms = 11
    else:
        perms = 10
    if (command == "getsource" and perms >= 0):
        await message.channel.send("This bot is open source, the source code is at: <https://github.com/RandomGamer123/DiscordModerationBot>.")
        return
    if (command == "testsheets" and perms >= 30):
        service.spreadsheets().values().append(spreadsheetId = warninglogid, range = "TestSheet!A1:B2", valueInputOption = "RAW", insertDataOption = "INSERT_ROWS", body = {"values":[["testing",message.id]]}).execute()
    if (command == "print" and perms >= 40):
        print(" ".join(args))
    if (command == "warn" and perms >= 30):
        warnings = get_warnings()
        if len(args) < 1:
            await message.channel.send("You need at least 1 argument in this command.")
            return
        if (args[0].isnumeric()):
            id = args[0]
        else:
            pingmatch = re.compile("<@![0-9]{6,19}>");
            if pingmatch.match(args[0]):
                id = args[0][3:-1]
            else:
                await message.channel.send("Argument 1 of this command must be a user id or mention.")
                return
        user = client.get_user(int(id))
        username = user.name+" #"+user.discriminator
        mod = message.author.name
        uniqueid = "W"+str(len(warnings)+1)
        args.pop(0)
        reason = " ".join(args)
        service.spreadsheets().values().append(spreadsheetId = warninglogid, range = "Warnings!A1:G2", valueInputOption = "RAW", insertDataOption = "INSERT_ROWS", body = {"values":[[str(user.id),username,uniqueid,"",reason,(mod+" (Warned via bot)"),str(round(time.time()))]]}).execute()
        await message.channel.send("User <@!"+str(user.id)+"> has been warned for reason: `"+reason+"` by moderator "+mod)
        warnings = get_warnings()
    if (command == "warnings" and perms >=30):
        warnings = get_warnings()
        if len(args) < 1:
            await message.channel.send("You need at least 1 argument in this command.")
            return
        if (args[0] == "all"):
            msgstring = ""
            for warning in warnings:
                if msgstring != "":
                    msgstring = msgstring+"\n"
                if warning[6] == "NA":
                    evttime = "an unknown time"
                else:
                    evttime = datetime.datetime.fromtimestamp(int(warning[6])).strftime('%Y-%m-%d %H:%M:%S')
                msgstring = msgstring+"Case "+warning[2]+": User "+warning[1]+" ("+warning[0]+") has been warned by "+warning[5]+" at "+evttime+" for reason: \n"+warning[4]
            for i in range(0,len(msgstring),1994):
                await message.channel.send("```"+msgstring[i:i+1994]+"```")
        else:
            if (args[0].isnumeric()):
                searchid = args[0]
            else:
                pingmatch = re.compile("<@![0-9]{6,19}>");
                if pingmatch.match(args[0]):
                    searchid = args[0][3:-1]
                else:
                    await message.channel.send("Argument 1 of this command must be a user id or mention.")
                    return
            msgstring = ""
            for warning in warnings:
                if str(warning[0]) == str(searchid):
                    if msgstring != "":
                        msgstring = msgstring+"\n"
                    if warning[6] == "NA":
                        evttime = "an unknown time"
                    else:
                        evttime = datetime.datetime.fromtimestamp(int(warning[6])).strftime('%Y-%m-%d %H:%M:%S')
                    msgstring = msgstring+"Case "+warning[2]+": User "+warning[1]+" ("+warning[0]+") has been warned by "+warning[5]+" at "+evttime+" for reason: \n"+warning[4]
            if (msgstring == ""):
                await message.channel.send("This user has no warnings.")
            else:
                for i in range(0,len(msgstring),1994):
                    await message.channel.send("```"+msgstring[i:i+1994]+"```")
    if (command == "kick" and perms >= 30):
        kicks = get_kicks()
        if len(args) < 1:
            await message.channel.send("You need at least 1 argument in this command.")
            return
        if (args[0].isnumeric()):
            id = args[0]
        else:
            pingmatch = re.compile("<@![0-9]{6,19}>");
            if pingmatch.match(args[0]):
                id = args[0][3:-1]
            else:
                await message.channel.send("Argument 1 of this command must be a user id or mention.")
                return
        user = client.get_user(int(id))
        if (user.id == message.author.id):
            await message.channel.send("You cannot kick yourself.")
            return
        username = user.name+" #"+user.discriminator
        mod = message.author.name
        uniqueid = "K"+str(len(kicks)+1)
        args.pop(0)
        reason = " ".join(args)
        service.spreadsheets().values().append(spreadsheetId = warninglogid, range = "Kicks!A1:G2", valueInputOption = "RAW", insertDataOption = "INSERT_ROWS", body = {"values":[[str(user.id),username,uniqueid,"",reason,(mod+" (Kicked via bot)"),str(round(time.time()))]]}).execute()
        await message.guild.kick(user,reason=reason)
        await message.channel.send("User <@!"+str(user.id)+"> has been kicked for reason: `"+reason+"` by moderator "+mod)
        kicks = get_kicks()
    if (command == "ban" and perms >= 30):
        bans = get_bans()
        if len(args) < 1:
            await message.channel.send("You need at least 1 argument in this command.")
            return
        if (args[0].isnumeric()):
            id = args[0]
        else:
            pingmatch = re.compile("<@![0-9]{6,19}>");
            if pingmatch.match(args[0]):
                id = args[0][3:-1]
            else:
                await message.channel.send("Argument 1 of this command must be a user id or mention.")
                return
        user = client.get_user(int(id))
        if (user.id == message.author.id):
            await message.channel.send("You cannot ban yourself.")
            return
        username = user.name+" #"+user.discriminator
        mod = message.author.name
        uniqueid = "B"+str(len(bans)+1)
        args.pop(0)
        reason = " ".join(args)
        service.spreadsheets().values().append(spreadsheetId = warninglogid, range = "Bans!A1:G2", valueInputOption = "RAW", insertDataOption = "INSERT_ROWS", body = {"values":[[str(user.id),username,uniqueid,"",reason,(mod+" (Banned via bot)"),str(round(time.time()))]]}).execute()
        await message.guild.ban(user,reason=reason)
        await message.channel.send("User <@!"+str(user.id)+"> has been banned for reason: `"+reason+"` by moderator "+mod)
        bans = get_bans()           
if os.getenv("BOTTOKEN"):
    bottoken = os.getenv("BOTTOKEN")
else: 
    bottoken = tokens["bottoken"]
client.run(bottoken)