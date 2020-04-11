import discord,json

client = discord.Client()

with open("Config/config.json") as json_data_file:
    configs = json.load(json_data_file)
    
@client.event
async def on_ready():
    print('We have logged in as {0.user}'.format(client))

@client.event
async def on_message(message):
    if message.author == client.user:
        return
client.run(configs["bottoken"])