from selenium.webdriver import Chrome
from selenium.webdriver.support.ui import WebDriverWait
import threading
import json
import time
BASE_LINK = "https://ua1xbet.com/en/live/Football/"

data = []

driver = Chrome()
driver.get(BASE_LINK)

#fetching element from parent element using xpath
def fetch_by_xpath(path, parent=driver, timeout=20, many=False):
    if many:
        finder = lambda d: parent.find_elements_by_xpath(path)
    else:
        finder = lambda d: parent.find_element_by_xpath(path)
    return WebDriverWait(parent, timeout).until(finder)

#creating dictionary with match data
def create_dict(team_up_name, team_down_name, score_up, score_down, markers):
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
                        "type":"1X"
                    },
                    {
                        "odd":markers[4],
                        "type":"12"
                    },
                    {
                        "odd":markers[5],
                        "type":"2X"
                    }
                ]
                },
            ]
        }

#fetching mathces from one cup and adding in data list
def fetch_from_cup(element):
    try:
        cup_title = fetch_by_xpath("div[1]/div[2]", parent=element).text#element.find_element_by_xpath("div[1]/div[2]").text
    except:
        return 1
    print(f"Loading cup {cup_title}...")
    matches_list = []
    matches_of_cup = fetch_by_xpath("div", parent=element, many=True)[1:]#element.find_elements_by_xpath("div")[1:]
    for m in matches_of_cup:
        try:
            teams_names = fetch_by_xpath("div/div[@class='c-events-scoreboard']/div[1]/a", parent=m)#m.find_element_by_xpath("div/div[@class='c-events-scoreboard']/div[1]/a")
            team_up_name = fetch_by_xpath("span/div[1]/div", parent=teams_names).text#teams_names.find_element_by_xpath("span/div[1]/div").text
            team_down_name = fetch_by_xpath("span/div[2]/div", parent=teams_names).text#teams_names.find_element_by_xpath("span/div[2]/div").text
            # print(team_up_name, team_down_name)
        except:
            print(f"troubles with team block. Cup - {cup_title}")
            continue
        try:
            score_block = fetch_by_xpath("div/div[@class='c-events-scoreboard']/div[1]/div", parent=m)#m.find_element_by_xpath("div/div[@class='c-events-scoreboard']/div[1]/div")
            score_up = fetch_by_xpath("div[1]/span[2]", parent=score_block).text#score_block.find_element_by_xpath("div[1]/span[2]").text
            score_down = fetch_by_xpath("div[2]/span[2]", parent=score_block).text#score_block.find_element_by_xpath("div[2]/span[2]").text
        except:
            print("troubles with score block")
            continue
        try:
            markers_data = fetch_by_xpath("div/div[@class='c-bets']/span", parent=m, many=True)#m.find_elements_by_xpath("div/div[@class='c-bets']/span")
            markers = []
            for md in markers_data:
                markers.append(md.text)
        except:
            print("troubles with markers block")
            continue

        match_data = create_dict(team_up_name, team_down_name, score_up, score_down, markers)

        matches_list.append(match_data)
    data.append({
        "cup":cup_title,
        "mathces":matches_list
    })
    print(f"Loading cup {cup_title} finished!")
#getting the page
matchBlock = fetch_by_xpath("//div[@id='games_content']/div/div[1]/div")
cups = fetch_by_xpath("*", parent=matchBlock, many=True)#matchBlock.find_elements_by_xpath("*")

print("Finish loading the page")

#list of threads
threads = []

#fetching data about all the mathces in different threads
for c in cups:
    t = threading.Thread(target = lambda: fetch_from_cup(c))
    threads.append(t)
    t.start()
for t in threads:
    t.join()

#writing data in json file
with open('data.json', 'w') as outfile:
    json.dump(data, outfile)

driver.quit()
