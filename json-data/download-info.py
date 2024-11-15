import requests
import json

url = r'https://api.hearthstonejson.com/v1/latest/itIT/cards.json'

response = requests.get(url)

if response.status_code == 200:
    t = json.loads(response.text)
    out = []
    names = []
    for i in t:
        try:
            if (i["isBattlegroundsPoolMinion"]):
                out.append(i)
                names.append(i["name"])
        except:
            if (i["name"] in names) and ("BG" in i["id"]):
                out.append(i)

    with open('minions.json', 'w', encoding='utf-8') as file:
        file.write(json.dumps(out, indent=4))
    
    with open('all-cards.json', 'w', encoding='utf-8') as file:
        file.write(json.dumps(t, indent=4))

