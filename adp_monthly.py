from calendar import weekday
from time import sleep
import requests
import json
import os
from datetime import datetime,timedelta,date

#from secrets import *
from localsecrets import *

global certz
certz = [os.getcwd()+'/ADP_Saturna Capital.pem', os.getcwd()+'/ADP_saturnacapital_auth.key']


def slackPost(header,text,slackContext):
    slackBlock = json.load(open('slackblock_monthly.json'))
    slackBlock['blocks'][0]['text']['text'] = header
    slackBlock['blocks'][1]['text']['text'] = text
    slackBlock['blocks'][2]['elements'][0]['text'] = slackContext
    slackPost = json.dumps(slackBlock)
    r = requests.post(slackURL,headers={'Content-Type': 'Content-Type/json'},data=slackPost) 


def summaryLookup(date1,date2):
    url =  "https://api.adp.com/time/v3/workers/%id%/time-off-request-summaries?$filter=requestStartdate eq " +date1+" and requestEndDate eq " +date2 + " $ordrby= approvedRequestQuantity asc&$orderby=approvedRequestQuantity desc"
    response = requests.get(url,headers=requestHeader,cert=(certz))
    return json.loads(response.text)["timeOffRequestSummaries"]

def adpToken():
    tokenbody = {} 
    tokenbody["grant_type"] = "client_credentials" 
    tokenbody["client_id"] = client_id
    tokenbody["client_secret"] = client_secret
    accesstokenrequest = requests.post('https://api.adp.com/auth/oauth/v2/token',data=tokenbody,cert=(certz))
    global token
    token = "Bearer " + json.loads(accesstokenrequest.text)["access_token"]
    print(token)
    return token

def sequenceFinder(name,numbers,dates):
    print("Sequence Finder is analyising: " + str(name))
    ###Build out weekend wrapping vacations
    #Edit these:
    summaryDays = 4 #the number of sequential days REQUIRED that will be added to final result

    listCount = -1
    newsequence = []
    sequenceResults = []
    for i in numbers:
        i = int(i)
        newsequence.append(int(i))
        listCount = listCount+1
        try: #wrapped in a try because the final iteration will fail due to array size.
            if int(i)+3 == int(numbers[listCount+1]):#if the next item is two days later
                print("Two day gap")
                print("Check friday : " + str(dates[listCount].weekday()))
                if dates[listCount].weekday() == 4: #if the days is a friday
                    newsequence.append(i+1)
                    newsequence.append(i+2)
        except:
            pass
    #finalResult is a string like "14,15,21 -> 27"
    finalResult = ""
    dayRange = []
    dayRange.append(newsequence[0])
    while len(newsequence) > 0:
        print("Top")
        i = 1
        rangeFinder = True
        origin = int(newsequence[0])
        newsequence.pop(0)
        while rangeFinder == True:
            try: #wrapped in a try because the final iteration will fail due to array size.
                if origin + i == int(newsequence[0]):
                    dayRange.append(newsequence[0])
                    newsequence.pop(0)
                    i = i +1
                else:
                    rangeFinder = False
            except:
                rangeFinder = False
        if len(dayRange) >= summaryDays:
            print("This date range is noteworthy")
            print(dayRange)
            finalResult = finalResult + str(dayRange[0]) + " -> " +str(dayRange[-1])
            dayRange = []
        else:
            dayRange = []
    print("Sequence Finder is returning: " + finalResult)
    return finalResult

def mySort(array):
    print("mySort is organizing the list alphabetically")
    list = []
    for x in array:
        list.append(x)
    sortedlist = sorted(list)
    newDic = {}
    for x in sortedlist:
        newDic[x] = array[x]
    return newDic


#########MAIN#########

today = datetime.today()
todayString = datetime.today().strftime('%Y-%m-%d')
firstofMonth = date(today.year, today.month, 1)
daysinMonth = (date(today.year, today.month+1, 1) - firstofMonth).days
endofMonth = firstofMonth + timedelta(days=daysinMonth)
full_month_name = today.strftime("%B")


adpToken()
global requestHeader
requestHeader = {}
requestHeader["Authorization"] = token
##Summary is a m-f period and it sorts by time off##
summary = summaryLookup(firstofMonth.strftime('%Y-%m-%d'),endofMonth.strftime('%Y-%m-%d'))
##

wantedAOID = {}
resultArray = {} #Result Array is the final list
resultArrayDateTime = {} # for doing date checks we will make a similar list but with datetime

#make an empty array to contain the dates
for personsummary in summary:
    if personsummary['requestStatusTotals'][1]['totalRequestQuantity'] >= 4:
        print(personsummary['requestorName']['givenName'] + " " + personsummary['requestorName']['familyName1'] + "more that 4 days")
        resultArray[personsummary['requestorName']['givenName'] + " " + personsummary['requestorName']['familyName1']] = []
        resultArrayDateTime[personsummary['requestorName']['givenName'] + " " + personsummary['requestorName']['familyName1']] = []

#X = whos global range
daterange = []
x = range(daysinMonth)
for n in x:
    daterange.append((firstofMonth + timedelta(days=n)))


for date in daterange:
    datestring = date.strftime('%Y-%m-%d')
    day = date.strftime('%d')
    print("Running summary report for date: " + datestring)
    timeoff = summaryLookup(datestring,datestring)
    for personOut in timeoff:
        if personOut['requestStatusTotals'][1]['totalRequestQuantity'] > 0:
            formattedName = personOut['requestorName']['givenName'] + " " + personOut['requestorName']['familyName1']
            if formattedName in resultArray.keys():
                resultArray[formattedName].append(day)
                resultArrayDateTime[formattedName].append(date)
                
           


#whos out is not empty. Continue
resultArray = mySort(resultArray)
slackHeader = full_month_name.upper() + " MONTHLY SUMMARY"
slackText = ""
slackContext = "This list only contains crew with 4 or more *sequential days off* as of " +todayString+ "\n"
for x in resultArray:
    #resultArray[x] = [1,2,3,4]
    #x = "Sonya J Luhm"
    if len(resultArray[x]) > 2: #do they have more than two days off
        resultArray[x] = sequenceFinder(x,resultArray[x],resultArrayDateTime[x])
        #numbers = resultArray['Deanna L Clemens']
        #dates = resultArrayDateTime['Deanna L Clemens']
    else:
        resultArray[x] = ",".join(resultArray[x])
    thistext = x +" [" +resultArray[x] + "]"
    slackText = slackText + thistext  +" \n"

# for x in resultArray:
#     joined_string = ",".join(resultArray[x])
#     thistext = resultArray[x] +" [" +joined_string + "]"
#     slackText = slackText + thistext  +" \n"
slackPost(slackHeader,slackText,slackContext)
