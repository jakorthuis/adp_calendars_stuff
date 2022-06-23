
def adpAsync(url):
    asyncheaders = {}
    asyncheaders["Prefer"] = "respond-async"
    asyncheaders["Authorization"] = token
    asyncRequest = requests.get(url,headers=asyncheaders,cert=(certz))
    waitfor = int(asyncRequest.headers["retry-after"])
    r2url = "https://api.adp.com" + asyncRequest.headers['link'].split('<')[1].split(">")[0]
    sleep(waitfor)
    return adpRequest(r2url)

def adpRequest(url):
    requestResponse = requests.get(url,headers=requestHeader,cert=(certz))
    return requestResponse
