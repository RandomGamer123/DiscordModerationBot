import discord,json,os,httplib2
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
@client.event
async def on_ready():
    print('We have logged in as {0.user}'.format(client))

@client.event
async def on_message(message):
    if message.author == client.user:
        return
    if not (message.content.startswith(config["prefix"])):
        return
    args = (message.content[1:]).split(" ")
    command = args.pop(0)
    if message.author.id in [156390113654341632]: 
        perms = 12
    if (command == "getsource"):
        await message.channel.send("This bot is open source, the source code is at: <https://github.com/RandomGamer123/DiscordModerationBot>.")
    if (command == "testsheets" and perms >= 12):
        service.spreadsheets().values().append(spreadsheetId = warninglogid, range = "TestSheet!A1:B2", valueInputOption = "RAW", insertDataOption = "INSERT_ROWS", body = {"values":[["testing",message.id]]}).execute()
if os.getenv("BOTTOKEN"):
    bottoken = os.getenv("BOTTOKEN")
else: 
    bottoken = tokens["bottoken"]
client.run(bottoken)