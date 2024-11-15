import re
from time import time
import json
from datetime import datetime

# keeps track of all entities
entities = []

# used to represent entities as dictionaries of tags (similar to how the game does it)
class Entity:
    def __init__(self):
        self.tag_dict = {}
        entities.append(self)
    
    def set_tag(self, tag_name, tag_value):
        self.tag_dict[tag_name] = tag_value
        if (tag_name == "ID"):
            self.tag_dict["ENTITY_ID"] = tag_value
    
    def __getitem__(self, key):
        return self.tag_dict[key]

# creates an entity from the data given
def create_entity(tag_names=[], tag_values=[]):
    t = Entity()
    for tag_name, tag_value in zip(tag_names, tag_values):
        t.set_tag(tag_name, tag_value)
    return t

# finds an entity given some tag names and values. Saves results from previous searches to speed up things significantly
saved_results = {}
def entity_index_by_tags(tag_names, tag_values, use_saved=True):
    entity_index = None

    if (use_saved):
        try:
            entity_index = saved_results[f"{tag_names} | {tag_values}"]
            return entity_index
        except KeyError:
            pass

    for n,i in enumerate(entities):
        t = i.tag_dict
        match = True
        for tag, value in zip(tag_names, tag_values):
            try:
                if (t[tag] != value):
                    match = False
                    break
            except KeyError:
                pass
        
        if (match):
            entity_index = n
            #break  #penso sia meglio usare l'ultima copia in caso di duplicati? (vedi Player e GameEntity)
    if (entity_index is not None):
        saved_results[f"{tag_names} | {tag_values}"] = entity_index

    return entity_index

# FUNCTIONS TO INTERPRET COMMANDS AND APPLY THEM TO THE ENTITY LIST

# GAME ENTITY command is called on game start and creates a GAME-ENTITY that keeps track of some values related to the state of the game itself (i think turn number is in here for example)
def GameEntity(packet):
    t = create_entity()
    t.set_tag("Entity", "GameEntity")
    t.set_tag("EntityID", packet[0][1].split("=")[-1])

    for tag,value in packet[1:]:
        tag = tag.split("=")[-1]
        value = value.split("=")[-1]
        t.set_tag(tag, value)

# two player entities are created at the start of the game. One represents the actual player, the other is 'the opponent' and is changed to represent bob or actual opponents depending on game state
def Player(packet):
    t = create_entity()
    t.set_tag("Entity", "Player")
    t.set_tag("EntityID", packet[0][1].split("=")[-1])
    t.set_tag("PlayerID", packet[0][2].split("=")[-1])

    #print(f"{t.tag_dict["EntityID"]}    {t.tag_dict["PlayerID"]}")

    for tag,value in packet[1:]:
        tag = tag.split("=")[-1]
        value = value.split("=")[-1]
        t.set_tag(tag, value)
    
    # right now this is a hack to export the id associated with the player and opponent. This allows to distinguish cards in each part of the field for example
    global dummy_id, player_id
    try:
        t["BACON_DUMMY_PLAYER"]
        dummy_id = t["CONTROLLER"]
    except KeyError:
        player_id = t["CONTROLLER"]

# this command can create or edit an entity by specifying all its data tags
def FullEntity(packet):
    if (packet[0][1] == "Creating"):
        t = create_entity()
        for i in packet[0][2:]:
            tag,value = i.split("=")
            t.set_tag(tag, value)
        for tag,value in packet[1:]:
            tag = tag.split("=")[-1]
            value = value.split("=")[-1]
            t.set_tag(tag, value)
    elif (packet[0][1] == "Updating"):
        id = None
        for i in packet[0]:
            t = re.findall(r"(?<=id=)[a-zA-Z0-9]+", i)
            if len(t):
                id = t[0]
        index = entity_index_by_tags(["ENTITY_ID"], [id])
        if (index is None):
            create_entity()
            index = -1
        for tag,value in packet[1:]:
            tag = tag.split("=")[-1]
            value = value.split("=")[-1]
            entities[index].set_tag(tag, value)
    else:
        print(packet[0][1])

# this command changes a single data tag on a single entity.
def TagChange(packet):
    packet = packet[0]
    if not ("[" in packet[1]):
        id = packet[1].split("=")[-1]
    else:
        id = ""
        for i in packet:
            if ("id=" in i):
                id = i.split("=")[-1]
    index = entity_index_by_tags(["ENTITY_ID"], [id])
    if index is None:
        index = entity_index_by_tags(["Entity"], [id])
    
    tag = packet[-2].split("=")[-1]
    value = packet[-1].split("=")[-1]
    entities[index].set_tag(tag, value)

# this maps commands in packets to the functions implementing them
def handle_command(command):
    if command[0][0] == "GameEntity":
        GameEntity(command)
    if command[0][0] == "Player":
        Player(command)
    if command[0][0] == "FULL_ENTITY":
        FullEntity(command)
    if command[0][0] == "TAG_CHANGE":
        TagChange(command)
    if command[0][0] == "CHANGE_ENTITY":
        FullEntity(command)


t0 = time()

filename = "test-data/test_files/Power_2.log"
with open(filename, "r") as file:
    lines = file.readlines()

t1 = time()
print(f"File read in {t1 - t0:.2f}s")

dtypes = ["GameState.DebugPrintPowerList", "GameState.DebugPrintPower", "GameState.DebugPrintGame", "PowerTaskList.DebugDump", "PowerTaskList.DebugPrintPower", "PowerProcessor.PrepareHistoryForCurrentTaskList",
          "GameState.DebugPrintEntityChoices", "PowerProcessor.EndCurrentTaskList", "GameState.SendChoices", "GameState.DebugPrintEntitiesChosen", "ChoiceCardMgr.WaitThenShowChoices",
          "ChoiceCardMgr.WaitThenHideChoicesFromPacket", "GameState.DebugPrintOptions", "GameState.SendOption", "PowerProcessor.DoTaskListForCard", "PowerSpellController"]

filter_types = [dtypes[1], dtypes[4]]
types_regex = [re.compile(rf".*({i}).*$") for i in filter_types]

# filter and split lines, then make a list of timestamps
filtered_lines = []
splitted_lines = []
timestamps = []
for line in lines:
    t = [i.match(line) != None for i in types_regex]
    if (True in t):
        line = line.strip()

        timestamp = re.findall(r"\b\d{1,2}:\d{2}:\d{2}\.\d{1,7}\b", line)[0]

        t = ""
        for i in line.split("-")[1:]:
            t += i
        line = t[1:]

        splitted_line = re.findall(r"\S+", line)

        filtered_lines.append(line)
        splitted_lines.append(splitted_line)
        timestamps.append(timestamp)

splitted_lines.append(["-----"])
t2 = time()
print(f"Filtered in {t2 - t1:.2f}s")

ignored_commands = ["CREATE_GAME", "BLOCK_START", "BLOCK_END", "SUB_SPELL_START", "SUB_SPELL_END"]
processed_commands = ["GameEntity", "Player", "FULL_ENTITY", "TAG_CHANGE", "HIDE_ENTITY", "SHOW_ENTITY", "META_DATA", "CHANGE_ENTITY"]

# group packets to complete the commands
grouped_lines = []
unhandled = []
grouped_timestamps = []
count = 0
while True:
    current = splitted_lines[count]

    if ("Count" in current[0]):
        count += 1 
        pass

    elif (current[0] in ignored_commands):
        count += 1
        pass

    elif (current[0] in processed_commands) and (count < len(splitted_lines)):
        grouped_timestamps.append(timestamps[count])
        grouped_lines.append([current])
        count += 1
        current = splitted_lines[count]
        while (current[0][:3] == "tag"):
            grouped_lines[-1].append(current)
            count += 1
            if (count >= len(splitted_lines)):
                break
            current = splitted_lines[count]

    else:
        unhandled.append(current + [f"line={count + 1}"])
        count += 1 
        #if (not "tag" in current[0]):
            #print(f"Unhandled packet at line: {count} \t {current}")

    if (count >= len(splitted_lines)):
        break

t3 = time()
print(f"Grouped in {t3 - t2:.2f}s")

# OUTPUT DATA TO HUMAN/PROGRAM READABLE FILES

#print(len(grouped_lines))
#print([i[0] for i in grouped_lines[1]])
boardstates = []
current_timestamp = grouped_timestamps[0]
for timestamp, command in zip(grouped_timestamps, grouped_lines):
    handle_command(command)

    if (timestamp != current_timestamp):
        current_timestamp = timestamp
        t = []
        for entity in entities:
            try:
                if (entity["CARDTYPE"] == "MINION"):
                    if (entity["ZONE"] == "PLAY"):
                        t.append([entity["CardID"], entity["ATK"], entity["HEALTH"], entity["CONTROLLER"]])
    
            except KeyError:
                pass
        boardstates.append(t)

t4 = time()
print(f"Interpreted in {t4 - t3:.2f}s")
print(f"Total time: {t4 - t0:.2f}s")
print(f"Number of lines in original file: {len(lines)}")
print(f"Number of commands: {len(grouped_lines)}")
print(f"Number of entities: {len(entities)}")

cardtypes = []

with open("test-data/out/Entities.log", "w") as file:
    for n,entity in enumerate(entities):
        t = entity.tag_dict
        if True:#("CARDTYPE" in t.keys()):
            #if (t["CARDTYPE"] not in cardtypes):
            #    cardtypes.append(t["CARDTYPE"])
            #if (t["CARDTYPE"] != ""):# and t["ZONE"] == "PLAY"):
                file.write(f"{n+1})\n")
                for tag, value in t.items():
                    file.write(f"\t\t{tag} = {value}\n")
                file.write("\n")
print(cardtypes)
with open("test-data/out/tout2.log", "w") as file:
    #t = [i[0] + "\n" for i in splitted_lines]
    #file.writelines(t)
    for n, i in enumerate(grouped_lines):
        if (len(i) > 0):
            file.write(f"{n}) {grouped_timestamps[n]}: {i[0][0]}:\n")
            for j in i:
                file.write(f"\t\t{j}\n")
            file.write("\n")

with open("test-data/out/unhandled.log", "w") as file:
    for i in unhandled:
        file.write(f"{i}\n")

with open("test-data/out/boardstates.json", "w") as file:
    json.dump([player_id, dummy_id] + boardstates, file, indent=4)

format_str = "%H:%M:%S.%f"
deltas = []
for n, _ in enumerate(grouped_timestamps[:-1]):
    t1 = datetime.strptime(grouped_timestamps[n][:-1], format_str)
    t2 = datetime.strptime(grouped_timestamps[n+1][:-1], format_str)
    delta = t2 - t1
    deltas.append(delta.total_seconds())

from matplotlib import pyplot as plt
from statistics import stdev, mean

print(f"Average time between blocks of packets: {mean(deltas):.4f}+-{stdev(deltas):.4f}")
print(f"Maximum time between blocks of packets: {max(deltas):.4f}")
print(f"Minimum time between blocks of packets: {min(deltas):.4f}")

plt.plot(deltas)
plt.show()

