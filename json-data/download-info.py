import requests
import json

url = r'https://api.hearthstonejson.com/v1/latest/itIT/cards.json'

response = requests.get(url)

if response.status_code == 200:
    t = json.loads(response.text)
    bg_cards = []
    for card in t:
        if card["set"] == "BATTLEGROUNDS":
            bg_cards.append(card)
    with open("json-data/bg-cards.json", "w") as file:
        file.write(json.dumps(bg_cards, indent=4))


