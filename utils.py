import json

def GetCardData(id, cards=None):
    # In the future i would like to avoid having to read card data for each call
    if (cards is None):
        try:
            with open("json-data/bg-cards.json") as file:
                cards = json.load(file)
        except FileNotFoundError:
            print("Card data file not found. Try running download-info.py in the json-data folder")
    
    for card in cards:
        if (card["id"] == id):
            return card
    
    return None
    

