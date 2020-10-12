import discord,json,os,re,httplib2,time,datetime,hashlib,io,requests
import numpy as np
from apiclient import discovery
from google.oauth2 import service_account

intents = discord.Intents.none()
intents.guilds = True
#intents.members = True - Cannot turn this on, blame diamond
intents.messages = True

client = discord.Client(intents=intents)

with open("Config/token.json") as token_file:
    tokens = json.load(token_file)
    
with open("Config/config.json") as config_file:
    config = json.load(config_file);

with open("Config/help.json") as help_file:
    helpdata = json.load(help_file)

prefix = config["prefix"]

startactivity = discord.Game(name="Type {}help to get started!".format(prefix))

scopes = ["https://www.googleapis.com/auth/spreadsheets"]
secret_file = "Config/client_secret.json"
credentials = service_account.Credentials.from_service_account_file(secret_file, scopes=scopes)
service = discovery.build('sheets','v4',credentials=credentials)
    
warninglogid = tokens["warninglogid"]
verifylogid = tokens["verifylogid"]
twowsheetid = tokens["twowsheetid"]

twoweventroleid = 757702654339055736

cookietestlink = "http://api.roblox.com/incoming-items/counts"
csrftokenendpoint = "https://auth.roblox.com/v1/logout"
cookie = tokens["robloxverifybotcookie"]
cookies = {".ROBLOSECURITY": cookie}
headers = {'User-Agent': 'Role Updating Bot'}
updategrouproleendpoint = "https://groups.roblox.com/v1/groups/{groupid}/users/{userid}"
groupid = "2735831"
csrftoken = None
ranktoiddict = {239: 18383972, 240: 18383966}

def validatecookie():
    resp = requests.get(cookietestlink, cookies = cookies, headers = headers)
    if (resp.status_code == 403):
        return False
    else:
        return True

def getcsrftoken():
    resp = requests.post(csrftokenendpoint, cookies = cookies, headers = headers)
    csrftoken = resp.headers["X-CSRF-Token"]
    return csrftoken

def updategrouprole(user,role,noloop = False): # Return possibilities: 0 -> Token Failure, 1 -> Success, 2 -> User has higher role than role that will be updated to [UNUSED], 3 -> User has higher role position than bot, 4 -> 503 error, 5 -> User Invalid, 6 -> Two runs of repeated invalid CSRF token, 7 -> Invalid role / role not supported, 8 -> Other error
    if (validatecookie):
        global csrftoken
        if (csrftoken is None):
            csrftoken = getcsrftoken()
        lclheaders = dict(headers)
        lclheaders["X-CSRF-Token"] = csrftoken
        lclendpoint = updategrouproleendpoint.format(groupid = groupid, userid = str(user))
        try:
            reqroleid = ranktoiddict[int(role)]
        except KeyError:
            return 7
        payload = {"roleId": reqroleid}
        response = requests.patch(lclendpoint, cookies = cookies, json = payload, headers = lclheaders)
        if (response.status_code == 200):
            return 1
        responsejson = response.json()
        code = responsejson["errors"][0]["code"]
        if (response.status_code == 403):
            if (code == 0): #Invalid csrf token
                if (noloop): #Previous run also had invalid csrf token, return 6
                    return 6
                csrftoken = response.headers["X-CSRF-Token"]
                newrsp = updategrouprole(user,role,True)
                return newrsp
            if (code == 4):
                return 3
            else:
                return 8
        if (response.status_code == 401):
            return 0
        if (response.status_code == 503):
            return 4
        if (response.status_code == 400):
            if (code == 3):
                return 5
        return 8
    else:
        return 0

def role_exec(robloxid):
    response = updategrouprole(robloxid,240)
    if (response == 1):
        return ([True,"Your Roblox account also had its role automatically updated to Executive Passenger, thank you for purchasing a premium ticket."])
    else:
        return ([False,response])
    
def get_warnings():
    global warninglogid
    response = service.spreadsheets().values().get(spreadsheetId = warninglogid, range = "Warnings!A2:H", majorDimension="ROWS", valueRenderOption = "UNFORMATTED_VALUE").execute()
    return response["values"]

def get_kicks():
    global warninglogid
    response = service.spreadsheets().values().get(spreadsheetId = warninglogid, range = "Kicks!A2:G", majorDimension="ROWS", valueRenderOption = "UNFORMATTED_VALUE").execute()
    return response["values"]

def get_bans():
    global warninglogid
    response = service.spreadsheets().values().get(spreadsheetId = warninglogid, range = "Bans!A2:G", majorDimension="ROWS", valueRenderOption = "UNFORMATTED_VALUE").execute()
    return response["values"]

def wordcount(response):
	response = re.sub(r"""[ \t][!"\#$%&'()*+,\-./:;<=>?@\[\\\]^_‘{|}~][ \t]"""," ",response)
	splitrsp = response.split(' ')
	wordcount = 0
	for word in splitrsp:
		if (word != ''):
			wordcount += 1
	return wordcount

def get_twow_event_config(): # Config order: Line 0 (A2:B2) - screensize; Line 1 (A3:B3) - status [0 -> nothing, 1 -> signups, 2 -> responding, 3 -> voting]
    global twowsheetid
    response = service.spreadsheets().values().get(spreadsheetId = twowsheetid, range = "Config!A2:B", majorDimension="ROWS", valueRenderOption = "UNFORMATTED_VALUE").execute()
    return response["values"]

def get_vote_response_data():
    global twowsheetid
    responsesinforesponse = service.spreadsheets().values().get(spreadsheetId = twowsheetid, range = "VoteMatrix!D1:5", majorDimension="ROWS", valueRenderOption = "UNFORMATTED_VALUE").execute()
    responsesinforesponsevalues = responsesinforesponse["values"]
    responsescount = len(responsesinforesponsevalues[0])
    responsesinfo = [responsesinforesponsevalues[0],responsesinforesponsevalues[1],responsesinforesponsevalues[2][0:responsescount],responsesinforesponsevalues[3][0:responsescount],responsesinforesponsevalues[4][0:responsescount]]
    return responsesinfo
    
def get_user_vote_index(requser): # Index is the row number in Google Sheets - 7 (so the first vote at row 7 would be 0), if user has no registered votes, returns -1
    global twowsheetid
    response = service.spreadsheets().values().get(spreadsheetId = twowsheetid, range = "VoteMatrix!B7:B", majorDimension="COLUMNS", valueRenderOption = "UNFORMATTED_VALUE").execute()
    if "values" in response:
        voteuseridlist = response["values"][0]
        for i in range(len(voteuseridlist)):
            if (str(voteuseridlist[i]) == str(requser)):
                return i
    return -1

def get_vote_data(voteindex): # Index is the row number in Google Sheets - 7 (so the first vote at row 7 would be 0)
    global twowsheetid
    response = service.spreadsheets().values().get(spreadsheetId = twowsheetid, range = "VoteMatrix!D{0}:{0}".format(voteindex+7), majorDimension="ROWS", valueRenderOption = "UNFORMATTED_VALUE").execute()
    return response["values"][0]

def get_vote_count_data(voteindex): # Index is the row number in Google Sheets - 7 (so the first vote at row 7 would be 0)
    global twowsheetid
    response = service.spreadsheets().values().get(spreadsheetId = twowsheetid, range = "VoteCountMatrix!D{0}:{0}".format(voteindex+7), majorDimension="ROWS", valueRenderOption = "UNFORMATTED_VALUE").execute()
    return response["values"][0]

def append_vote_data(username,userid,votedata,votecountdata):
    global twowsheetid
    response = service.spreadsheets().values().append(spreadsheetId = twowsheetid, range = "VoteMatrix!D7:AA8", valueInputOption = "RAW", insertDataOption = "OVERWRITE", body={"majorDimension": "ROWS","values":[votedata]}).execute()
    tablerange = response["updates"]["updatedRange"]
    firstunit = tablerange.split("!")[1].split(":")[0]
    voterow = re.findall(r'\d+', firstunit)[0]
    service.spreadsheets().values().update(spreadsheetId = twowsheetid, range = "VoteMatrix!A{0}:B{0}".format(voterow), valueInputOption = "RAW", body={"range":"VoteMatrix!A{0}:B{0}".format(voterow),"majorDimension": "ROWS","values":[[username,str(userid)]]}).execute()
    service.spreadsheets().values().update(spreadsheetId = twowsheetid, range = "VoteCountMatrix!D{0}:{0}".format(voterow), valueInputOption="RAW", body = {"range":"VoteCountMatrix!D{0}:{0}".format(voterow),"majorDimension":"ROWS","values":[votecountdata]}).execute()
    service.spreadsheets().values().update(spreadsheetId = twowsheetid, range = "VoteCountMatrix!A{0}:B{0}".format(voterow), valueInputOption = "RAW", body={"range":"VoteCountMatrix!A{0}:B{0}".format(voterow),"majorDimension": "ROWS","values":[[username,str(userid)]]}).execute()
    return

def update_vote_data(voteindex,votedata,votecountdata):
    global twowsheetid
    service.spreadsheets().values().update(spreadsheetId = twowsheetid, range = "VoteMatrix!D{0}:{0}".format(voteindex+7), valueInputOption="RAW", body = {"range":"VoteMatrix!D{0}:{0}".format(voteindex+7),"majorDimension":"ROWS","values":[votedata]}).execute()
    service.spreadsheets().values().update(spreadsheetId = twowsheetid, range = "VoteCountMatrix!D{0}:{0}".format(voteindex+7), valueInputOption="RAW", body = {"range":"VoteCountMatrix!D{0}:{0}".format(voteindex+7),"majorDimension":"ROWS","values":[votecountdata]}).execute()
    return

def get_contestants():
    global twowsheetid
    response = service.spreadsheets().values().get(spreadsheetId = twowsheetid, range = "Signup!A2:C", majorDimension="ROWS", valueRenderOption = "UNFORMATTED_VALUE").execute()
    return response["values"]

def get_responses():
    global twowsheetid
    response = service.spreadsheets().values().get(spreadsheetId = twowsheetid, range = "Responses!A2:E", majorDimension="ROWS", valueRenderOption = "UNFORMATTED_VALUE").execute()
    if "values" in response:
        return response["values"]
    return []

def get_allowed_response_count(requser):
    global twowsheetid
    response = service.spreadsheets().values().get(spreadsheetId = twowsheetid, range = "RspCount!A2:B", majorDimension="ROWS", valueRenderOption = "UNFORMATTED_VALUE").execute()
    if "values" in response:
        data = response["values"]
        for user in data:
            if (str(user[0]) == str(requser)):
                return int(user[1])
    return 1
    
def id_to_char(id):
    if (id < 26):
        return chr(id+65)
    if (id < 58):
        return chr(id+7)
    else: 
        return chr(id+33)
        
def char_to_id(char):
    ordnum = ord(char)
    if (ordnum < 64):
        return (ordnum-7)
    if (ordnum < 91):
        return (ordnum-65)
    else:
        return (ordnum-33)
        
def get_checksum(screen):
    m = hashlib.md5(screen.encode("UTF-8")).hexdigest()[-3:]
    id1 = (int(m[0],16)<<2)+(int(m[1],16)>>2)
    id2 = ((int(m[1],16)%4)<<4)+(int(m[2],16))
    checksum = str(id_to_char(id1))+str(id_to_char(id2))
    return checksum

def bracketremove(vote):
    if (vote[0] == '['):
        vote = vote[1:]
    if (vote[-1] == ']'):
        vote = vote[:-1]
    return vote

def signup(requser,requsername,configbypass):
    global twowsheetid
    configs = get_twow_event_config()
    status = configs[1][1]
    if (status != 1 and not configbypass):
        return (["405","02","Signups have ended, you may not sign up right now."])
    contestants = get_contestants()
    is_contestant = False
    for contestant in contestants:
        if (contestant[0] == str(requser)):
            is_contestant = True
    if (is_contestant):
        return(["403","01","You have previously already signed up for this event."])
    service.spreadsheets().values().append(spreadsheetId = twowsheetid, range = "Signup!A1:C2", valueInputOption = "RAW", insertDataOption = "OVERWRITE", body={"majorDimension": "ROWS","values":[[str(requser),requsername,time.time()]]}).execute()
    return (["200","02","You have been signed up, you may now view the event channel for more information."])

def respond(requser,requsername,response,edit,editnumber,configbypass):
    global twowsheetid 
    configs = get_twow_event_config()
    status = configs[1][1]
    if (status not in [1,2] and not configbypass):
        return (["405","03","The current status is not responding, so you may not respond right now."])
    signupstatus = 0 # 0 -> Normal responding; 1 -> Signed up user successfully; 2 -> Did not sign up user successfully as user was already signed up
    if (status == 1): # User is signing up at the same time
        signupresponse = signup(requser,requsername,configbypass)
        if (signupresponse[0] == "200"):
            signupstatus = 1
        else:
            signupstatus = 2
    if (status == 2): # Check if user is a contestant
        contestantslist = get_contestants()
        is_not_contestant = True
        for contestant in contestantslist:
            if (str(contestant[0]) == str(requser)):
                is_not_contestant = False
                break
        if (is_not_contestant):
            return (["403","03","Only contestants may submit responses at this time, and you are not a contestant."])
    if (len(response) > 120):
        return (["400","06","Your response must be less than or equal to 120 characters if submitted through the bot. If you wish to submit a response longer than this, please DM me to get it manually vetted."])
    curresponses = get_responses()
    if (edit):
        if (editnumber <= 0):
            return (["400","05","The response number that you wish to edit must be an integer greater than 0."])
        responserow = 0
        lclrow = 2
        if (len(curresponses) != 0):
            for rspcombo in curresponses:
                if (str(rspcombo[0]) == str(requser)):
                    if (int(rspcombo[4]) == int(editnumber)):
                        responserow = lclrow
                        break
                lclrow += 1
        if (responserow == 0):
            return (["405","04","You have not submitted a response with response number of {}.".format(editnumber)])
        updateresponse = service.spreadsheets().values().update(spreadsheetId = twowsheetid, range = "Responses!C{0}:D{0}".format(responserow), valueInputOption="RAW", body = {"range":"Responses!C{0}:D{0}".format(responserow),"majorDimension":"ROWS","values":[[time.time(),response]]}).execute()
        return (["200","06","Your old response with response number of {} has been edited to be:\n`{}`".format(editnumber,response)])
    responsecount = 0
    if (len(curresponses) != 0): # If there are submitted responses
        for rspcombo in curresponses:
            if (str(rspcombo[0]) == str(requser)):
                responsecount += 1
    maxresponsecount = get_allowed_response_count(requser)
    if (responsecount >= maxresponsecount):
        return (["403","02","You have already submitted {} responses, and the limit of responses you can submit is {}, so you cannot submit any more.\nTo edit your response, type in `{}respond -edit <response_number_to_edit> <new_response>`.\nExample command:`{}respond -edit 1 This will edit your first response to become this.`".format(responsecount,maxresponsecount,prefix,prefix)])
    service.spreadsheets().values().append(spreadsheetId = twowsheetid, range = "Responses!A1:E2", valueInputOption = "RAW", insertDataOption = "INSERT_ROWS", body={"majorDimension": "ROWS","values":[[str(requser),requsername,time.time(),response,(responsecount+1)]]}).execute()
    if (signupstatus == 0):
        return (["200","03","Your response:\n`{}`\nhas been submitted. This is response {} out of {} that you can submit this round.".format(response,(responsecount+1),maxresponsecount)])
    elif (signupstatus == 1):
        return (["200","04","Your response:\n`{}`\nhas been submitted. This is response {} out of {} that you can submit this round. You also have been signed up for the event.".format(response,(responsecount+1),maxresponsecount)])
    else: #signupstatus is 2
        return (["200","05","Your response:\n`{}`\nhas been submitted. This is response {} out of {} that you can submit this round.".format(response,(responsecount+1),maxresponsecount)])
        
def gen_screen(requser,configbypass):
    global twowsheetid
    configs = get_twow_event_config() # Config order: Line 0 (A2:B2) - screensize; Line 1 (A3:B3) - status [0 -> nothing, 1 -> signups, 2 -> responding, 3 -> voting]
    screensize = configs[0][1]
    status = configs[1][1]
    if (status != 3 and not configbypass):
        return (["405","01","The current status is not voting, so you may not vote right now."])
    uservoteindex = get_user_vote_index(requser)
    if (uservoteindex != -1): # User has previously voted
        uservotecountdata = get_vote_count_data(uservoteindex)
        uservotedata = get_vote_data(uservoteindex)
    responsesinfo = get_vote_response_data()
    responsesids = responsesinfo[1]
    responseindex = [-1] # Response index starts from 0 unlike the response number on the sheet which starts from 1
    for i in range(len(responsesids)):
        if (str(responsesids[i]) == str(requser)):
            if (responseindex[0] == -1):
                responseindex[0] = i
            else:
                responseindex.append(i)
    randomisecount = screensize
    userresponsetoinsert = ""
    userresponsetoinsertid = -1
    if (responseindex[0] != -1): # User has submitted responses
        if (uservoteindex == -1): # User has not voted
            randomisecount = (screensize - 1)
            userresponsetoinsert = responsesinfo[0][responseindex[0]]
            userresponsetoinsertid = responseindex[0] 
        else: # User has voted
            for response in responseindex:
                if (uservotecountdata[response] == 0): # This response has not been voted on by the user
                    randomisecount = (screensize - 1)
                    userresponsetoinsert = responsesinfo[0][response]
                    userresponsetoinsertid = (response) 
    responsenumberstorandomise = responsesinfo[2] # Note that response numbers start from 1
    responsenumbersweights = responsesinfo[3] 
    if (randomisecount != screensize):
        for i in range(len(responseindex)-1,-1,-1):
            responsenumberstorandomise.pop(responseindex[i])
            responsenumbersweights.pop(responseindex[i])
    responsenumbersweights = np.asarray(responsenumbersweights,dtype=np.float64)
    responsenumbersweights /= responsenumbersweights.sum()
    chosenresponsesnumbers = np.random.choice(responsenumberstorandomise,size=randomisecount,replace=False,p=responsenumbersweights) # Note that these numbers are indexed by 1
    chosenresponses = []
    screenname = ""
    if (randomisecount != screensize):
        chosenresponses.append(userresponsetoinsert)
        screenname = screenname + id_to_char(userresponsetoinsertid)
    for responsenumber in chosenresponsesnumbers:
        response = responsesinfo[0][responsenumber-1]
        chosenresponses.append(response)
        screenname = screenname + id_to_char(responsenumber-1)
    checksum = get_checksum(screenname)
    screenname = screenname + checksum
    return [chosenresponses,screenname]

def process_vote(vote,subuser,subusername,configbypass):
    global twowsheetid
    configs = get_twow_event_config() # Config order: Line 0 (A2:B2) - screensize; Line 1 (A3:B3) - status [0 -> nothing, 1 -> signups, 2 -> responding, 3 -> voting]
    screensize = configs[0][1]
    status = configs[1][1]
    if (status != 3 and not configbypass):
        return (["405","01","The current status is not voting, so you may not vote right now."])
    uservoteindex = get_user_vote_index(subuser)
    if (uservoteindex != -1): # User has previously voted
        uservotecountdata = get_vote_count_data(uservoteindex)
        uservotedata = get_vote_data(uservoteindex)
    responsesinfo = get_vote_response_data()
    vote = bracketremove(vote)
    votearr = vote.split(" ",1)
    screenpart = votearr[0]
    votepart = votearr[1]
    if (len(screenpart) != screensize+2):
        return (["400","01","Your screen name has an invalid length, please make sure it matches the one you were given exactly."])
    screenname = screenpart[:-2]
    screenchecksum = screenpart[-2:]
    if (get_checksum(screenname) != screenchecksum):
        return (["400","02","Your screen name is invalid due to a non-matching checksum value, please make sure it matches the one you were given exactly."])
    votedata = [None] * screensize
    voteerror = False
    extrachars = []
    reptchars = []
    charcount = 0
    if (len(votepart) != screensize):
        voteerror = True
    for char in votepart:
        charid = char_to_id(char)
        if (charid < 0):
            voteerror = True
            extrachars.append(char)
            charcount += 1
            continue
        if (charid >= screensize):
            voteerror = True
            extrachars.append(char)
            charcount += 1
            continue
        if (votedata[charid] is not None):
            voteerror = True
            reptchars.append(char)
            charcount += 1
            continue
        votedata[charid] = 1-(charcount/(screensize-1))
        charcount += 1
    if (voteerror):
        if ((len(votepart) - len(extrachars) - len(reptchars) - screensize) == 0): # There are no missing characters
            if (len(extrachars) == 0):
                extrachars = ["NA"]
            if (len(reptchars) == 0):
                reptchars = ["NA"]
            return (["400","03","Your vote contains invalid or repeated characters in it. Here are the characters in concern:\nInvalid / Extra Characters: {}\nRepeated Characters: {}".format(" ".join(extrachars)," ".join(reptchars))])
        else: # There are missing characters
            missingchars = []
            charidcounter = 0
            for charid in votedata:
                if (charid is None):
                    missingchars.append(id_to_char(charidcounter))
                charidcounter += 1
            if (len(extrachars) == 0):
                extrachars = ["NA"]
            if (len(reptchars) == 0):
                reptchars = ["NA"]
            return (["400","04","Your vote contains invalid, repeated, or missing characters in it. Here are the characters in concern:\nInvalid / Extra Characters: {}\nRepeated Characters: {}\nMissing Characters: {}".format(" ".join(extrachars)," ".join(reptchars)," ".join(missingchars))])
    totalresponsecount = len(responsesinfo[0])
    if (uservoteindex == -1):
        uservotecountdata = [0]*totalresponsecount
        uservotedata = [0]*totalresponsecount
    voteincrementer = 0
    for responsechar in screenname:
        responseid = char_to_id(responsechar)
        responsescore = votedata[voteincrementer]
        uservotedata[responseid] = uservotedata[responseid] + responsescore
        uservotecountdata[responseid] = uservotecountdata[responseid] + 1
        voteincrementer += 1
    if (uservoteindex == -1):
        append_vote_data(subusername,subuser,uservotedata,uservotecountdata)
    else:
        update_vote_data(uservoteindex,uservotedata,uservotecountdata)
    return (["200","01","Vote {} Recorded. To get a new screen, run {}twowevent vote.".format(vote,prefix)])


warnings = get_warnings()
kicks = get_kicks()
bans = get_bans()

@client.event
async def on_ready():
    global warnings
    warnings = get_warnings()
    print('We have logged in as {0.user}'.format(client))
    await client.change_presence(activity=startactivity)

@client.event
async def on_message(message):
    global warnings
    global kicks
    global bans
    global warninglogid
    global verifylogid
    global prefix
    global helpdata
    if message.author == client.user:
        return
    if not (message.content.startswith(prefix)):
        return
    if (message.author.bot):
        if (message.author.id == 155149108183695360):
            await message.channel.send("Act your age, Dynosaur.")
        return
    args = (message.content[1:]).split(" ")
    if len(args) == 0:
        return
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
    if (command == "help" and perms >= 0):
        targetcmd = ""
        if len(args) == 0:
            targetcmd = "all"
        else:
            targetcmd = args[0]
        if targetcmd.startswith("!"):
            targetcmd = targetcmd[1:]
        if targetcmd.startswith(prefix):
            targetcmd = targetcmd[1:]
        output = ""
        if targetcmd == "all":
            for cmd,data in helpdata.items():
                if data["perms"] <= perms:
                    displaycmd = cmd + ' '
                    desc = data["description"]
                    if (desc[0:12] == "|subcommand|"):
                        displaycmd = ""
                        desc = desc[12:]
                    output += "`{0}{1}{2}`- {3}\n".format(prefix,displaycmd,data["usage"],desc)
            await message.channel.send(output+"Note that arguments encased in angle brackets (`<>`) are mandatory, while those encased in square brackets (`[]`) are optional.")
            return
        elif targetcmd in helpdata:
            data = helpdata[targetcmd]
            if data["perms"] <= perms:
                displaycmd = targetcmd + ' '
                desc = data["description"]
                if (desc[0:12] == "|subcommand|"):
                    displaycmd = ""
                    desc = desc[12:]
                await message.channel.send("`{0}{1}{2}`- {3}\n Note that arguments encased in angle brackets (`<>`) are mandatory, while those encased in square brackets (`[]`) are optional.".format(prefix,displaycmd,data["usage"],desc))
                return
            else:
                await message.channel.send("You cannot access the help for this command/subcommand.")
                return
        else:
            await message.channel.send("The command {}{} is not a command or subcommand.".format(prefix,targetcmd))
            return
    if (command == "getsource" and perms >= 0):
        await message.channel.send("This bot is open source, the source code is at: <https://github.com/RandomGamer123/DiscordModerationBot>.")
        return
    if (command == "twowevent" and perms >= 0):
        roleguild = client.get_guild(348398590051221505)
        participantrole = discord.utils.get(roleguild.roles, id=twoweventroleid)
        submittedrole = discord.utils.get(roleguild.roles, id=758481239236673566)
        if (len(args) == 0):
            subcommand = "info"
        else:
            subcommand = args.pop(0)
        cfgbypass = False
        if (subcommand == "-bypassstatus" and perms >= 30):
            cfgbypass = True
            if (len(args) == 0):
                subcommand = "info"
            else:
                subcommand = args.pop(0)
        if (subcommand == "info"):
            await message.channel.send("This module is for the integration of the bot with the TWOW side-event. To get help about this module, please run `{}help twowevent` for more info. This command must be used with a subcommand. Example subcommands include `signup`, `getresponses`, `respond`, or `vote`.\nTo get more information about how the event works, you can also read https://docs.google.com/document/u/2/d/1gYozaDz-neG4QB0gg39fYPX0oI7GBFjXAb2j_fDm3lk/edit".format(prefix))
        if (subcommand == "signup"):
            result = signup(message.author.id,message.author.name,cfgbypass)
            if ((message.guild is not None) and (message.guild.id == 348398590051221505)):
                userobj = message.author
            else:
                #userobj = roleguild.get_member(message.author.id)
                userobj = await roleguild.fetch_member(message.author.id)
            if ((userobj is not None) and result[0] != "405"):
                await userobj.add_roles(participantrole,reason="Signed up for event.")
            await message.channel.send(result[2])
        if (subcommand == "vote"):
            if (not isinstance(message.channel, discord.DMChannel)):
                await message.channel.send("This command must be done in DMs.")
                return
            if ((len(args) == 0) or (args[0] == "genscreen" and perms >= 30)): # No arguments, or force genscreen, so generate screen
                if (len(args) == 0):
                    requser = message.author.id
                else:
                    requser = args[1]
                screendata = gen_screen(requser,cfgbypass)
                if (screendata[0] == "405"): #Indicates current status is not voting, so you cannot call a voting related method
                    await message.channel.send(screendata[2])
                    return
                screenname = screendata[1]
                responses = screendata[0]
                rspstr = ""
                for i in range(len(responses)):
                    rspstr = rspstr + id_to_char(i) + ": " + responses[i] + " [WC: {}]\n".format(wordcount(responses[i]))
                howtovote = "How to vote?\nStart your vote with a square bracket `[`, then put the screen name, shown in the first line of this message. Then, order the responses from best to worst, with the left side being the best and the right side being the worst, then end the vote with another square bracket `]` and then DM it to the bot with the command `!twowevent vote <yourvote>` (Do not include the angle brackets.) An example vote would be: `!twowevent vote [YUASJDISIP JEDCHBFAIG]`.\nMore information can be found at the `Voting` section of the following document: https://docs.google.com/document/d/1gYozaDz-neG4QB0gg39fYPX0oI7GBFjXAb2j_fDm3lk/edit?usp=sharing"
                await message.channel.send("```md\nScreen {}\n{}```{}".format(screenname,rspstr,howtovote))
            else:
                if (len(args) == 1):
                    await message.channel.send("Your vote should include a space between the screen name and the vote. Please check your vote for errors.")
                else:
                    vote = " ".join(args)
                    if (len(vote) > 200):
                        await message.channel.send("Your vote should not be greater than 200 characters, please check your vote for errors, if you believe that your vote should actually be this long, please DM me.")
                    else:
                        statusresponse = process_vote(vote,message.author.id,message.author.name,cfgbypass)
                        await message.channel.send(statusresponse[2])
        if (subcommand == "getresponses"):
            if (not isinstance(message.channel, discord.DMChannel)):
                await message.channel.send("This command must be done in DMs.")
                return
            responselist = get_responses()
            if (len(responselist) == 0):
                await message.channel.send("There are no responses that you can view.")
                return
            dispresponses = "```\n"
            dispall = False
            requser = message.author.id
            if (len(args) != 0 and (args[0] == "-dispall" and perms >= 40)):
                dispall = True
            for response in responselist:
                if (dispall or (str(response[0]) == str(requser))):
                    dispresponses = dispresponses + response[3] + "\n"
            if (dispresponses == "```\n"):
                await message.channel.send("There are no responses that you can view.")
                return
            dispresponses = dispresponses + "```"
            if (len(dispresponses) > 1950):
                uploadfile = discord.File(fp = io.StringIO(dispresponses[4:-4]), filename = "retrieved_responses.txt")
                await message.channel.send(content = "Response list too large, it has been attached as a file.", file = uploadfile)
            else:
                await message.channel.send(dispresponses)
        if (subcommand == "respond"):
            if (not isinstance(message.channel, discord.DMChannel)):
                await message.channel.send("This command must be done in DMs.")
                return
            edit = False
            editnumber = 0
            if (len(args) != 0 and args[0] == "-edit"):
                edit = True
                if (len(args) < 2):
                    await message.channel.send("Missing edit number and response. Not enough arguments.\nCommand Format: `{0}twowevent respond [-edit] [editnumber] <response>`\nExample Command 1: `{0}twowevent respond This is a response.`\nExample Command 2 `{0}twowevent respond -edit 1 This will edit your first response to become this.`".format(prefix))
                editnumber = args.pop(1)
                try:
                    editnumber = int(editnumber)
                except:
                    await message.channel.send("Edit number must be integer. Not enough arguments.\nCommand Format: `{0}twowevent respond [-edit] [editnumber] <response>`\nExample Command 1: `{0}twowevent respond This is a response.`\nExample Command 2 `{0}twowevent respond -edit 1 This will edit your first response to become this.`".format(prefix))
                args.pop(0)
            if (len(args) == 0):
                await message.channel.send("Response not found in command. Not enough arguments.\nCommand Format: `{0}twowevent respond [-edit] [editnumber] <response>`\nExample Command 1: `{0}twowevent respond This is a response.`\nExample Command 2 `{0}twowevent respond -edit 1 This will edit your first response to become this.`".format(prefix))
                return
            response = " ".join(args)
            submitresponseresponse = respond(message.author.id,message.author.name,response,edit,editnumber,cfgbypass)
            if (submitresponseresponse[0] == "200" and (submitresponseresponse[1] in ["04","05"])):
                if ((message.guild is not None) and (message.guild.id == 348398590051221505)):
                    userobj = message.author
                else:
                    #userobj = roleguild.get_member(message.author.id)
                    userobj = await roleguild.fetch_member(message.author.id)
                if (userobj is not None):
                    await userobj.add_roles(participantrole,reason="Signed up for event.")
            await message.channel.send(submitresponseresponse[2])
            if (submitresponseresponse[0] == "200"):
                await message.channel.send("The word count of the response `{}` you just submitted is: `{}`.".format(response,wordcount(response)))
                if ((message.guild is not None) and (message.guild.id == 348398590051221505)):
                    userobj = message.author
                else:
                    #userobj = roleguild.get_member(message.author.id)
                    userobj = await roleguild.fetch_member(message.author.id)
                if (userobj is not None):
                    await userobj.add_roles(submittedrole,reason="Submitted a response for the event.")
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
        embed = discord.Embed(colour=discord.Colour(0xf0f05d), timestamp=datetime.datetime.utcfromtimestamp(time.time()))
        embed.set_footer(text="Case "+uniqueid)
        if message.guild:
            if message.guild.id == 295823905120190465:
                embed.add_field(name="**Notice of Warning**", value=reason)
            else: 
                embed.add_field(name="**Notice of Warning**", value="You have been warned in SWISS International Air Lines' Discord for reason: \n"+reason)
        else:
            embed.add_field(name="**Notice of Warning**", value="You have been warned in SWISS International Air Lines' Discord for reason: \n"+reason)
        try:
            await user.send(embed=embed)
        except:
            await message.channel.send("The bot cannot DM that user, no DM notification has been sent. The user will still be warned.")
        service.spreadsheets().values().append(spreadsheetId = warninglogid, range = "Warnings!A1:H2", valueInputOption = "RAW", insertDataOption = "INSERT_ROWS", body = {"values":[[str(user.id),username,uniqueid,"",reason,(mod+" (Warned via bot)"),str(round(time.time())),"Active"]]}).execute()
        await message.channel.send("User <@!"+str(user.id)+"> has been warned for reason: `"+reason+"` by moderator "+mod)
        warnings = get_warnings()
    if (command == "removewarning" and perms >=30):
        warnings = get_warnings()
        if len(args) < 1:
            await message.channel.send("You need at least 1 argument in this command.")
            return
        if args[0].startswith("W"):
            case = ""
            row = 1
            rept = 1
            for warning in warnings:
                if case == "":
                    row = row + 1
                    if warning[2] == args[0]:
                        case = warning
                if warning[2].startswith("R"):
                    if ((warning[2].split("-",1))[0])[1:] == args[0][1:]:
                        rept = rept + 1
            if case == "":
                await message.channel.send("Warning with case number "+args[0]+" cannot be found.")
                return
            if case[7] == "Removed":
                await message.channel.send("This warning has already been removed. To reinstate this warning, please use the {}editwarning command.".format(prefix))
                return
            uniqueid = "R"+(args[0][1:])
            args.pop(0)
            reason = " ".join(args)
            mod = message.author.name
            service.spreadsheets().values().update(spreadsheetId = warninglogid, range = "Warnings!H"+str(row), valueInputOption = "RAW", body = {"values":[["Removed"]]}).execute()
            service.spreadsheets().values().append(spreadsheetId = warninglogid, range = "Warnings!A1:H2", valueInputOption = "RAW", insertDataOption = "INSERT_ROWS", body = {"values":[[case[0],case[1],uniqueid+"-"+str(rept),"",reason,(mod+" (Warning removed via bot)"),str(round(time.time())),"NA"]]}).execute()
            await message.channel.send("Warning W"+(uniqueid[1:])+" has been marked as removed by "+mod+" for reason:\n"+reason)
        else:
            await message.channel.send("Warning case number must start with W.")
            return
    if (command == "warningssheet" and perms >=30):
        await message.channel.send("Link to warning sheet: <https://docs.google.com/spreadsheets/d/1OM14Up7i-XurecAYqg6JLTxeGoGnabogz-6fE7ffJHI/edit#gid=0> (Ask Random to give you editing permissions.)")
        return
    if (command == "editwarning" and perms >=30):
        await message.channel.send("This command is still WIP, please directly edit the warnings sheet at <https://docs.google.com/spreadsheets/d/1OM14Up7i-XurecAYqg6JLTxeGoGnabogz-6fE7ffJHI/edit#gid=0> instead. (Ask Random to give you editing permissions.)")
        return
    if (command == "warnings" and perms >=30):
        warnings = get_warnings()
        if len(args) < 1:
            await message.channel.send("You need at least 1 argument in this command.")
            return
        if (args[0] == "all"):
            msgstring = ""
            for warning in warnings:
                if len(args) < 2:
                    if warning[7] == "Removed":
                        continue
                    if warning[2].startswith("R"):
                        continue
                elif args[1] != "-removed": 
                    if warning[7] == "Removed":
                        continue
                    if warning[2].startswith("R"):
                        continue
                if msgstring != "":
                    msgstring = msgstring+"\n"
                if warning[6] == "NA":
                    evttime = "an unknown time"
                else:
                    evttime = datetime.datetime.fromtimestamp(int(warning[6])).strftime('%Y-%m-%d %H:%M:%S')
                if warning[2].startswith("R"):
                    msgstring = msgstring+"Case "+warning[2]+": User "+warning[1]+" ("+warning[0]+") has had warning W"+str(warning[2][1:])+" removed by "+warning[5]+" at "+evttime+" for reason: \n"+warning[4]
                    continue
                if warning[7] == "Removed":
                    msgstring = msgstring+"[WARNING HAS BEEN REMOVED] Case "+warning[2]+": User "+warning[1]+" ("+warning[0]+") has been warned by "+warning[5]+" at "+evttime+" for reason: \n"+warning[4]
                    continue 
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
                if len(args) < 2:
                    if warning[7] == "Removed":
                        continue
                    if warning[2].startswith("R"):
                        continue
                elif args[1] != "-removed": 
                    if warning[7] == "Removed":
                        continue
                    if warning[2].startswith("R"):
                        continue
                if str(warning[0]) == str(searchid):
                    if msgstring != "":
                        msgstring = msgstring+"\n"
                    if warning[6] == "NA":
                        evttime = "an unknown time"
                    else:
                        evttime = datetime.datetime.fromtimestamp(int(warning[6])).strftime('%Y-%m-%d %H:%M:%S')
                    if warning[2].startswith("R"):
                        msgstring = msgstring+"Case "+warning[2]+": User "+warning[1]+" ("+warning[0]+") has had warning W"+str(warning[2][1:])+" removed by "+warning[5]+" at "+evttime+" for reason: \n"+warning[4]
                        continue
                    if warning[7] == "Removed":
                        msgstring = msgstring+"[WARNING HAS BEEN REMOVED] Case "+warning[2]+": User "+warning[1]+" ("+warning[0]+") has been warned by "+warning[5]+" at "+evttime+" for reason: \n"+warning[4]
                        continue 
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
        embed = discord.Embed(colour=discord.Colour(0xff0000), timestamp=datetime.datetime.utcfromtimestamp(time.time()))
        embed.set_footer(text="Case "+uniqueid)
        if message.guild:
            if message.guild.id == 295823905120190465:
                embed.add_field(name="**Notice of Kicking**", value=reason)
            else: 
                embed.add_field(name="**Notice of Kicking**", value="You have been kicked from SWISS International Air Lines' Discord for reason: \n"+reason+"\n You can rejoin the server using the link: <https://discord.gg/SFr5f6D>.")
        else:
            embed.add_field(name="**Notice of Kicking**", value="You have been kicked from SWISS International Air Lines' Discord for reason: \n"+reason+"\n You can rejoin the server using the link: <https://discord.gg/SFr5f6D>.")
        try:
            await user.send(embed=embed)
        except:
            await message.channel.send("The bot cannot DM that user, no DM notification has been sent. The user will still be kicked.")
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
        embed = discord.Embed(colour=discord.Colour(0xff0000), timestamp=datetime.datetime.utcfromtimestamp(time.time()))
        embed.set_footer(text="Case "+uniqueid)
        if message.guild:
            if message.guild.id == 295823905120190465:
                embed.add_field(name="**Notice of Banning**", value=reason)
            else: 
                embed.add_field(name="**Notice of Banning**", value="You have been banned from SWISS International Air Lines' Discord for reason: \n"+reason)
        else:
            embed.add_field(name="**Notice of Banning**", value="You have been banned from SWISS International Air Lines' Discord for reason: \n"+reason)
        try:
            await user.send(embed=embed)
        except:
            await message.channel.send("The bot cannot DM that user, no DM notification has been sent. The user will still be banned.")
        service.spreadsheets().values().append(spreadsheetId = warninglogid, range = "Bans!A1:G2", valueInputOption = "RAW", insertDataOption = "INSERT_ROWS", body = {"values":[[str(user.id),username,uniqueid,"",reason,(mod+" (Banned via bot)"),str(round(time.time()))]]}).execute()
        await message.guild.ban(user,reason=reason)
        await message.channel.send("User <@!"+str(user.id)+"> has been banned for reason: `"+reason+"` by moderator "+mod)
        bans = get_bans()         
    if (command == "verify" and perms >=0):
        if len(args) == 0:
            await message.channel.send("Verification instructions: Visit <https://www.roblox.com/games/4890252160/SWISS-Verification-Game> to get a verification code valid for 5 minutes. Then input your code and Roblox username in Discord using the command `!verify <code> <username>`. Do not include the brackets.")
            return
        if len(args) < 2:
            await message.channel.send("You need at least 2 arguments for this command. Command format: !verify <code> <username>. Do not include the brackets. Visit <https://www.roblox.com/games/4890252160/SWISS-Verification-Game> to get the verification code.")
            return
        code = args.pop(0)
        name = " ".join(args)
        if (code[0] == "<" or code[-1] == ">"):
            await message.channel.send("Do not include the angle brackets with the code or username, please try again.")
            return
        verifycodes = (service.spreadsheets().values().get(spreadsheetId = verifylogid, range = "RobloxCodePairs!A2:F", majorDimension="ROWS", valueRenderOption = "UNFORMATTED_VALUE").execute())["values"]
        grouprank = -1
        newcodelist = verifycodes[:]
        emptyvals = 0
        boughtclass = "EC"
        rename = ""
        userrobloxid = 0
        for i in range(len(verifycodes)):
            codepair = verifycodes[i]
            if codepair[3] < time.time():
                newcodelist.remove(codepair)
                emptyvals = emptyvals + 1
            else:
                if codepair[2] == code:
                    if codepair[0] == name:
                        grouprank = codepair[4]
                        boughtclass = codepair[5]
                        emptyvals = emptyvals + 1
                        newcodelist.remove(codepair)
                        rename = codepair[0]
                        userrobloxid = codepair[1]
        if (grouprank == -1):
            await message.channel.send("A matching code and username combination cannot be found or your code has expired. Please generate a new code.")
            return
        if isinstance(message.channel, discord.abc.GuildChannel):
            roleguild = message.guild
        else:
            roleguild = client.get_guild(348398590051221505)
        if ((message.guild is not None) and (message.guild.id == 348398590051221505)):
            userobj = message.author
        else:
            #userobj = roleguild.get_member(message.author.id)
            userobj = await roleguild.fetch_member(message.author.id)
        await userobj.edit(nick=rename)
        if (grouprank == 0):
            notingrouprole = discord.utils.get(roleguild.roles, name="NOT IN GROUP")
            if message.guild.id == 348398590051221505:
                verifiedrole = discord.utils.get(roleguild.roles, name="Verified")
                await userobj.remove_roles(verifiedrole)
            await userobj.add_roles(notingrouprole,reason="User is not in the group.")
            await message.channel.send("You are not in the group. Please submit a request to join the group and wait until you are accepted, then request a new code and reverify. The related roles have been given.")
        if (grouprank > 0):
            verifiedrole = discord.utils.get(roleguild.roles, name="Verified")
            passengersrole = discord.utils.get(roleguild.roles, name="Passengers")
            await userobj.add_roles(verifiedrole,reason="User is in the group.")
            await userobj.add_roles(passengersrole,reason="User is in the group.")
            if message.guild.id == 348398590051221505:
                notingrouprole = discord.utils.get(roleguild.roles, name="NOT IN GROUP")
                if grouprank == 241:
                    traineerole = discord.utils.get(roleguild.roles, name="Trainee")
                    await userobj.add_roles(traineerole)
                if grouprank > 242:
                    staffrole = discord.utils.get(roleguild.roles, name="Staff Members")
                    await userobj.add_roles(staffrole)
                    traineerole = discord.utils.get(roleguild.roles, name="Trainee")
                    await userobj.remove_roles(traineerole)
                if boughtclass == "GI":
                    execpass = discord.utils.get(roleguild.roles, name="Executive Passengers")
                    classrole = discord.utils.get(roleguild.roles, name="Gold Investors")
                    await userobj.add_roles(execpass)
                    await userobj.add_roles(classrole)
                if boughtclass == "SI":
                    execpass = discord.utils.get(roleguild.roles, name="Executive Passengers")
                    classrole = discord.utils.get(roleguild.roles, name="Silver Investors")
                    await userobj.add_roles(execpass)
                    await userobj.add_roles(classrole)
                if boughtclass == "FC":
                    execpass = discord.utils.get(roleguild.roles, name="Executive Passengers")
                    classrole = discord.utils.get(roleguild.roles, name="First Class")
                    await userobj.add_roles(execpass)
                    await userobj.add_roles(classrole)
                if boughtclass == "BC":
                    execpass = discord.utils.get(roleguild.roles, name="Executive Passengers")
                    classrole = discord.utils.get(roleguild.roles, name="Business Class")
                    await userobj.add_roles(execpass)
                    await userobj.add_roles(classrole)
                if boughtclass in ["GI","SI","FC","BC"]:
                    if (grouprank == 239): #If user has group rank 239 -> Their rank is verified passenger
                        role_update_status = role_exec(userrobloxid)
                        if (role_update_status[0]):
                            await message.channel.send(role_update_status[1])
                        else:
                            await message.channel.send("We attempted to update your role in the Roblox Group to Executive Passengers, however, an error occurred in the process, please DM <@156390113654341632> with the following error code: {}".format(role_update_status[1]))
                await userobj.remove_roles(notingrouprole)
            await message.channel.send("Verification complete.")
        clearcommand = (service.spreadsheets().values().clear(spreadsheetId = verifylogid, range = "RobloxCodePairs!A2:F")).execute()
        response = (service.spreadsheets().values().update(spreadsheetId = verifylogid, range = "RobloxCodePairs!A2:F", valueInputOption="RAW", body = {"range":"RobloxCodePairs!A2:F","majorDimension":"ROWS","values":newcodelist})).execute()
if os.getenv("BOTTOKEN"):
    bottoken = os.getenv("BOTTOKEN")
else: 
    bottoken = tokens["bottoken"]
client.run(bottoken)
