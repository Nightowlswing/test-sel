import aiohttp
import asyncio
import json
import time


"""
id?
Идем на 'https://ua1xbet.com/LiveFeed/Get1x2_VZip?sports=1&count={   КОЛИЧЕСТВО МАТЧЕЙ   }&lng=en&mode=4&country=2&partner=25&getEmpty=true'
Берем j["Value"][{  НОМЕР   }]["I"]

score?
Идем на https://ua1xbet.com/LiveFeed/GetGameZip?id={   ИНДЕКС   }&lng=en&cfview=0&isSubGames=true&GroupEvents=true&allEventsGroupSubGames=true&countevents=250&partner=25&marketType=1
Берем ["Value"]["SC"][FS] - если команды в словаре нет, значит ноль

home?
Идем на https://ua1xbet.com/LiveFeed/GetGameZip?id={   ИНДЕКС   }&lng=en&cfview=0&isSubGames=true&GroupEvents=true&allEventsGroupSubGames=true&countevents=250&partner=25&marketType=1
Берем ["Value"]["O1"]

away?
Идем на https://ua1xbet.com/LiveFeed/GetGameZip?id={   ИНДЕКС   }&lng=en&cfview=0&isSubGames=true&GroupEvents=true&allEventsGroupSubGames=true&countevents=250&partner=25&marketType=1
Берем ["Value"]["O2"]

home?
Идем на https://ua1xbet.com/LiveFeed/GetGameZip?id={   ИНДЕКС   }&lng=en&cfview=0&isSubGames=true&GroupEvents=true&allEventsGroupSubGames=true&countevents=250&partner=25&marketType=1
Берем ["Value"]["O1"]

1X2 Regular time?
Идем на https://ua1xbet.com/LiveFeed/GetGameZip?id={   ИНДЕКС   }&lng=en&cfview=0&isSubGames=true&GroupEvents=true&allEventsGroupSubGames=true&countevents=250&partner=25&marketType=1
Берем ["Value"]["GE"][0]["E"][0][0]['C'], ["Value"]["GE"][0]["E"][1][0]['C'], ["Value"]["GE"][0]["E"][2][0]['C']

Both Teams To Score?
Идем на https://ua1xbet.com/LiveFeed/GetGameZip?id={   ИНДЕКС   }&lng=en&cfview=0&isSubGames=true&GroupEvents=true&allEventsGroupSubGames=true&countevents=250&partner=25&marketType=1
Берем ["Value"]["GE"][2]["E"][0][0]['C'], ["Value"]["GE"][2]["E"][1][0]['C']

"""

#Functuion used to get data from website as text response
async def fetch(session, url):
    async with session.get(url) as response:
        return await response.text()

#Function used to fetch actual match data using match id
async def fetch_by_matchId(id, result, matches_failed):

    async with aiohttp.ClientSession() as session:

        # Getting text data with matches to fetch id
        try:
            content = await fetch(session, f'https://ua1xbet.com/LiveFeed/GetGameZip?id={id}&lng=en&cfview=0&isSubGames=true&GroupEvents=true&allEventsGroupSubGames=true&countevents=250&partner=25&marketType=1')
            data = json.loads(content)
        except:
            print("Fetching data about unknown match failed")
            matches_failed.append("unknown")
            return 1

        # Fetching actual data from text
        try:
            score = data["Value"]["SC"]['FS']
            if not "S1" in score.keys():
                score["S1"] = 0
            if not "S2" in score.keys():
                score["S2"] = 0
            team_up_name = data["Value"]["O1"]
            team_down_name = data["Value"]["O2"]
            score_up = score["S1"]
            score_down = score["S2"]
        except:
            print("Data about unknown match is not correct", e)
            matches_failed.append("unknown")

        try:
            markers = [
                data["Value"]["GE"][0]["E"][0][0]['C'],
                data["Value"]["GE"][0]["E"][1][0]['C'],
                data["Value"]["GE"][0]["E"][2][0]['C'],
                data["Value"]["GE"][2]["E"][0][0]['C'],
                data["Value"]["GE"][2]["E"][1][0]['C']
            ]
        except Exception as e:
            markers = ["-","-","-","-","-"]
            team_up_name = data["Value"]["O1"]
            team_down_name = data["Value"]["O2"]
            print(f"Data about {team_up_name}:{team_down_name} has no bet info")

        #Creating resulting dictionary
        match_data = {
            "home":team_up_name,
            "away":team_down_name,
            "currentScore":f"{score_up}:{score_down}",
            "markers":[
                {
                "title":"1X2 Regular time",
                "outcomes":[
                    {
                        "odd":markers[0],
                        "type":"1"
                    },
                    {
                        "odd":markers[1],
                        "type":"X"
                    },
                    {
                        "odd":markers[2],
                        "type":"2"
                    }
                ]
                },
                {
                "title":"Both Teams To Score",
                "outcomes":[
                    {
                        "odd":markers[3],
                        "type":"Yes"
                    },
                    {
                        "odd":markers[4],
                        "type":"No"
                    }
                ]
                },
            ]
        }

        #Appending resulting dictionary to result match list
        result.append(match_data)
        print(f"{team_up_name}:{team_up_name} fetched successfully")
        return 0


async def main():

    #result match list, number of matches to fetch, titles of failed fetching mathces and timeout time
    result = []
    MATCH_NUMBER = 100
    matches_failed = []
    TIMEOUT_TIME = 10

    async with aiohttp.ClientSession() as session:

        print("Fetching data about matches ids...")

        #Fetching text data about all match (mainly to get ids)
        try:
            content = await fetch(session, f'https://ua1xbet.com/LiveFeed/Get1x2_VZip?sports=1&count={MATCH_NUMBER}&lng=en&mode=4&country=2&partner=25&getEmpty=true')
            matches = json.loads(content)["Value"]
            actual_match_number = len(matches)
            print(actual_match_number)
            print("Fetched!")
        except:
            print("Fetching failed!")
            return 1

        print("Fetching match data...")

        #Fetching data about every single match
        for m in matches:
            asyncio.ensure_future(fetch_by_matchId(m["I"], result, matches_failed))

        #Waiting 'till all the matches become fethced or timeout time ends
        try:
            start = time.time()
            not_timeout = True
            while len(result)!=actual_match_number-len(matches_failed) and not_timeout:
                await asyncio.sleep(1)
                if time.time()-start>TIMEOUT_TIME:
                    not_timeout=False
                    print("Timeout!")
                    print("Saving fetched data...")
        except:
            print("Some problems appeared waiting till data become fetched")
            return 1

    #Saving file
    try:
        with open('data.json', 'w') as outfile:
            json.dump(result, outfile)
        print("Fetched data save successfully")
    except:
        print("Error saving data")
        return 1

    return 0

if __name__ == '__main__':
    loop = asyncio.get_event_loop()
    loop.run_until_complete(main())
