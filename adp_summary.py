from time import sleep
import requests
import json
import os
from datetime import datetime
from secrets import *

def slackPost(text):
    slackPOST = {}
    slackPOST['text'] = text
    slackPOST['type'] = "mrkdwn"
    slackPOST['unfurl_links'] = "true"
    #slackPOST['attachments'] = attachments
    slackJSON = json.dumps(slackPOST, sort_keys=False,indent=2)
    print("Returning this!")
    print(slackJSON)
    r = requests.post(slackURL,headers={'Content-Type': 'Content-Type/json'},data=slackJSON) 

today = datetime.today()
todayString = datetime.today().strftime('%Y-%m-%d')
tokenbody = {} 
tokenbody["grant_type"] = "client_credentials" 
tokenbody["client_id"] = client_id
tokenbody["client_secret"] = client_secret

accesstokenrequest = requests.post('https://api.adp.com/auth/oauth/v2/token',data=tokenbody,cert=(os.getcwd()+'/ADP_Saturna Capital.pem', os.getcwd()+'/ADP_saturnacapital_auth.key'))
token = "Bearer " + json.loads(accesstokenrequest.text)["access_token"]
print(token)


reqheaders = {}
reqheaders["Authorization"] = token

whosOUT = []

r3url =  "https://api.adp.com/time/v3/workers/%id%/time-off-request-summaries?$filter=requestStartdate eq " +todayString+" and requestEndDate eq " +todayString + " $ordrby= approvedRequestQuantity asc&$orderby=approvedRequestQuantity desc"
#r3 = requests.get(r3url,headers=reqheaders,cert=('/Users/jak/.ssh/ADP_Saturna Capital.pem', '/Users/jak/.ssh/ADP_saturnacapital_auth.key'))
r3 = requests.get(r3url,headers=reqheaders,cert=(os.getcwd()+'/ADP_Saturna Capital.pem', os.getcwd()+'/ADP_saturnacapital_auth.key'))
timeoff = json.loads(r3.text)["timeOffRequestSummaries"]
for personOut in timeoff:
    if personOut['requestStatusTotals'][1]['totalRequestQuantity'] > 0:
        
        formattedName = personOut['requestorName']['givenName'] + " " + personOut['requestorName']['familyName1']
        print(formattedName + " is out Today")
        whosOUT.append(formattedName)

if whosOUT != []:
    #whos out is not empty. Continue
    slacktext = "*Crew scheduled out for " + todayString + "* \n"
    for x in whosOUT:
        slacktext = slacktext + x  +" \n"
    slackPost(slacktext)