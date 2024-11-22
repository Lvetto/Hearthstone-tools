from packets import GetPacketList
from entities import GetEntityList, FindByTags
from parser_lib import Parser
from pickle import dump, load
from time import time
import json
from utils import GetCardData

# Decorator used to time the execution of functions
def time_function(func):
    def wrapper(*args, **kwargs):
        t0 = time()
        res = func(*args, **kwargs)
        t1 = time()
        print(f"Time take by '{func.__name__}': {t1 - t0:.3f} s")
        return res
    return wrapper

filename = "test-data/test_files/" + "2024-10-26-15-10" + ".log"
#filename = "test-data/test_files/" + "test" + ".log"

with open(f"{filename}") as file:
    data = file.read()

p = Parser()

try:
    with open(filename.split(".")[0] + ".pickle", "br") as file:
        packet_data = load(file)
except FileNotFoundError:
    packet_data = p.parse_str(data)

    with open(filename.split(".")[0] + ".pickle", "bw") as file:
        dump(packet_data, file)

packets = time_function(GetPacketList)(packet_data)

entities = time_function(GetEntityList)(packets, dbg=False)

# EXAMPLE: extracting minions controlled by one player and displaying their type and name

players = FindByTags(["CARDTYPE"], ["PLAYER"], entities)
p_id = players[0][1]["PlayerID"]

minions_in_play = FindByTags(["ZONE", "CARDTYPE", "CONTROLLER"], ["PLAY", "MINION", p_id], entities)
minion_ids = [minion["cardId"] for n, minion in minions_in_play]

with open("json-data/bg-cards.json") as file:
    cards = json.load(file)

minion_data = [GetCardData(id, cards) for id in minion_ids]

print(f"Minion types: {", ".join([minion["CARDRACE"] for n, minion in minions_in_play])}")
print(f"Minion names: {", ".join([card["name"] for card in minion_data])}")

