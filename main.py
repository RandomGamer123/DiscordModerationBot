import discord,json

with open("Config/token.json") as token_file:
    tokens = json.load(token_file)
    
with open("Config/config.json") as config_file:
    config = json.load(config_file);

@client.event
async def on_ready():
    print('We have logged in as {0.user}'.format(client))

@client.event
async def on_message(message):
    if message.author == client.user:
        return
    if (message.content.startswith(config["prefix"])):
        return
    args = (message.content[1:]).split(" ")
    command = args.pop(0)
    if (command == "getsource") {
        message.channel.send("This bot is open source, the source code is at: <https://github.com/RandomGamer123/DiscordModerationBot>.")
    }
if getenv("BOTTOKEN"):
    bottoken = getenv("BOTTOKEN")
else: 
    bottoken = tokens["bottoken"]
client.run(bottoken)