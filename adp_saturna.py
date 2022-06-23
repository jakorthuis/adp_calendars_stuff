#!python3
#https://github.com/O365/python-o365#calendar
#https://github.com/O365/python-o365/blob/master/O365/calendar.py
#https://portal.azure.com/#blade/Microsoft_AAD_RegisteredApps/ApplicationMenuBlade/Overview/quickStartType//sourceType/Microsoft_AAD_IAM/appId/9cc4d20c-69de-466d-bf83-f59f86ef7228/objectId/f85c47db-f96b-48d6-87ad-92c5c7d84851/isMSAApp//defaultBlade/Overview/appSignInAudience/AzureADMyOrg/servicePrincipalCreated/true

from calendar import weekday
from time import sleep
import requests
import json
import os
from datetime import datetime,timedelta,date
from dateutil import tz
from O365 import calendar
from O365 import Account


#from secrets import *
from localsecrets import *

global certz
certz = [os.getcwd()+'/ADP_Saturna Capital.pem', os.getcwd()+'/ADP_saturnacapital_auth.key']


#Calendar startup
myTZ = tz.gettz('UCT')

account = Account(credentials,main_resource="whosout@saturna.us",auth_flow_type="credentials",tenant_id="8562b5a0-d166-4ca9-99b2-c5722a679fd6")
account.authenticate()
schedule = account.schedule()
calendar = schedule.get_calendar(calendar_name="Testing")
#calendar = schedule.get_default_calendar()

def getEvents(startDate,endDate):
    schedule = account.schedule()
    calendar = schedule.get_default_calendar()
    #calendar = schedule.get_calendar(calendar_name="Testing")
    q = calendar.new_query('start').greater_equal(startDate)
    q.chain('and').on_attribute('end').less_equal(endDate)
    allevents = calendar.get_events(include_recurring=True,query=q,limit=10000)
    return allevents

def clearCalendar(startDate,endDate):
    schedule = account.schedule()
    #calendar = schedule.get_default_calendar()
    calendar = schedule.get_calendar(calendar_name="Testing")
    print("CLEARING CALENDAR")
    q = calendar.new_query('start').greater_equal(startDate)
    q.chain('and').on_attribute('end').less_equal(endDate)
    eventz = calendar.get_events(include_recurring=True,query=q,limit=10000)
    for event in eventz:
        print(event)
        event.delete()
        event.save()


def calendarWriter(summary,date):
    print("Function Calendar writer received: " + str(date))
    
    new_event = calendar.new_event(summary)
    
    new_event.is_reminder_on = False
    new_event.is_all_day = True
    if type(date) is list:
        print("dealing with a range")
        #date is a range
        print(summary + " start: " + str(date[0]) + "  END: "+ str(date[1]))
        #new_event.start = datetime.combine(datetime(2022, 4, 10, 0, 0,tzinfo =myTZ), datetime.min.time())
        new_event.start = datetime.combine(date[0], datetime.min.time())
        #new_event.end = datetime.combine(datetime(2022, 4, 14+1, 0, 0,tzinfo =myTZ),datetime.min.time())
        new_event.end = datetime.combine(date[1]+ timedelta(days=1), datetime.min.time())
        new_event.is_reminder_on = False
        new_event.is_all_day = True
        new_event.save()
        #new_event.delete()
    else:
        #make an all day event
        print("Single Day: " + str(date))
        new_event.start = date
        new_event.end = date + timedelta(hours=24)
        new_event.is_reminder_on = False
        new_event.is_all_day = True
        new_event.save()


    

def summaryLookup(date1,date2):
    url =  "https://api.adp.com/time/v3/workers/G5RZSMP5E9WEXDV5/time-off-request-summaries?$filter=requestStartdate eq " +date1+" and requestEndDate eq " +date2 + " $ordrby= approvedRequestQuantity asc&$orderby=approvedRequestQuantity desc"
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



def weekendFinder(name,dates):
    print("weekendFinder is analyising: " + str(name))
    ###Build out weekend wrapping vacations
    #Edit these:
    listCount = -1
    newsequence = []
    for date in dates:
        newsequence.append(date)
        listCount = listCount+1
        try: #wrapped in a try because the final iteration will fail due to array size.
            if date + timedelta(days=3) == dates[listCount+1]:#if the next item is two days later
                print("Two day gap")
                print("Check friday : " + str(date.weekday()))
                if date.weekday() == 4: #if the days is a friday
                    print("Must have been a friday!")
                    newsequence.append(date + timedelta(days=1))
                    newsequence.append(date + timedelta(days=2))
        except:
            pass
    return newsequence

def ranger(name,dates):
    finalResults = []
    summaryDays = 2
    dayRange = [] #this fills up with ranges util finished then resets
    while len(dates) > 0:
        dayRange.append(dates[0])
        print("Top")
        i = 1
        rangeFinder = True
        origin = dates[0]
        dates.pop(0)
        while rangeFinder == True:
            try: #wrapped in a try because the final iteration will fail due to array size.
                if origin + timedelta(days=i) == dates[0]:
                    dayRange.append(dates[0])
                    dates.pop(0)
                    i = i +1
                else:
                    rangeFinder = False
            except:
                rangeFinder = False
        if len(dayRange) >= summaryDays:
            print("This date range is noteworthy")
            finalResults.append([dayRange[0],dayRange[-1]])
            print(str(dayRange[0]) + " -> " +str(dayRange[-1]))
            dayRange = [] #reset the dayRange
        else:
            finalResults.append(dayRange[0])
            dayRange = []
    return finalResults



#########MAIN#########

today = datetime.combine(datetime.today(), datetime.min.time())
todayString = datetime.today().strftime('%Y-%m-%d')
firstofMonth = date(today.year, today.month, 1)
thirtyDaysAgo = today - timedelta(days=30)

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


#make an empty array to contain the dates
# for personsummary in summary:
#     if personsummary['requestStatusTotals'][1]['totalRequestQuantity'] >= 1:
#         print(personsummary['requestorName']['givenName'] + " " + personsummary['requestorName']['familyName1'] + "more that 4 days")
#         resultArray[personsummary['requestorName']['givenName'] + " " + personsummary['requestorName']['familyName1']] = []
        

#X = whos global range

daterange = []
x = range(30)
for n in x:
    daterange.append((thirtyDaysAgo + timedelta(days=n)))


for date in daterange:
    datestring = date.strftime('%Y-%m-%d')
    
    print("Running summary report for date: " + datestring)
    timeoff = summaryLookup(datestring,datestring)
    for personOut in timeoff:
        if personOut['requestStatusTotals'][1]['totalRequestQuantity'] > 0:
            formattedName = personOut['requestorName']['givenName'] + " " + personOut['requestorName']['familyName1']
            if formattedName in resultArray.keys():
                resultArray[formattedName].append(date)
            else:
                resultArray[formattedName] = []
                resultArray[formattedName].append(date)
               
                
           
calendar_events = getEvents(daterange[0],daterange[-1])
clearCalendar(daterange[0],daterange[-1])

#whos out is not empty. Continue
for x in resultArray:
    resultArray[x] = weekendFinder(x,resultArray[x])
    resultArray[x] = ranger(x,resultArray[x])
    print(x)
    print(resultArray[x])




for x in resultArray:
    for i in resultArray[x]:
        print(str(x) + " " + str(i))
        calendarWriter(str(x),i)

        #resultArray[x] = [1,2,3,4]
        #x = "Sonya J Luhm"


