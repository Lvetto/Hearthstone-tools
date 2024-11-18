class Entity:
    def __init__(self, tags):
        self.tags = {}
        for tag, value in tags:
            self.tags[tag] = value

        """self.id = self.tags["ENTITY_ID"]
        self.card_type = self.tags["CARDTYPE"]
        self.controller = self.tags["CONTROLLER"]
        self.zone = self.tags["ZONE"]
        self.creator = self.tags["CREATOR"]"""

    
    def change_tag(self, tag, value):
        self.tags[tag] = value

    def __getitem__(self, name):
        if (name in self.tags.keys()):
            return self.tags[name]
        else:
            return None

    def __setitem__(self, name, value):
        self.tags[name] = value


def FindByTags(tags, values, entities):
    out = []
    for n, entity in enumerate(entities):
        match = True
        for tag, value in zip(tags, values):
            if (entity[tag] != value):
                match = False
                break
        if (match):
            out.append((n, entity))
    return out


def CreateGame(packet):
    game_tags = packet.game_tags
    p1_tags = packet.p1_tags
    p2_tags = packet.p2_tags

    game = Entity(zip(game_tags.keys(), game_tags.values()))
    player1 = Entity(zip(p1_tags.keys(), p1_tags.values()))
    player2 = Entity(zip(p2_tags.keys(), p2_tags.values()))

    return (game, player1, player2)

def get_entity_list(packets, entities=[]):
    # for whatever reason, the game creates player entities and gives them ids, then searches for them by player-name which is given elsewhere
    ids = []
    names = []
    entities = []

    for packet in packets:
        command = packet.command

        # Handle the command that gives the player names and their ids
        if (command == "PlayerID"):
            ids.append(packet.id)
            names.append(packet.name)
        
        # Handle the command that starts the game
        elif (command == "CREATE_GAME"):
            game, player1, player2 = CreateGame(packet)

            # Set a few tags that are useful for finding the entities later
            if (player1["PLAYER_ID"] in ids):
                player1["Entity"] = names[ids.index(player1["PLAYER_ID"])]

            if (player2["PLAYER_ID"] in ids):
                player2["Entity"] = names[ids.index(player2["PLAYER_ID"])]
            
            game["Entity"] = "GameEntity"

            entities.append(player1)
            entities.append(player2)
            entities.append(game)
        
        elif (command == "FULL_ENTITY" or command == "SHOW_ENTITY"):
            id_tags = packet.id_tags
            tags = packet.tags

            if ("id" in id_tags.keys()):
                t = FindByTags(["ENTITY_ID"], [id_tags["id"]], entities)
            elif ("ID" in id_tags.keys()):
                t = FindByTags(["ENTITY_ID"], [id_tags["ID"]], entities)

            else:
                t = []
            
            if (len(t) > 0):
                entity = entities[t[0][0]]
                should_append = False
            else:
                entity = Entity([])
                should_append = True
            
            for tag, value in zip(id_tags.keys(), id_tags.values()):
                entity[tag] = value
            
            for tag, value in zip(tags.keys(), tags.values()):
                entity[tag] = value
            
            if (should_append):
                entities.append(entity)
        
        elif (command == "TAG_CHANGE" or command == "HIDE_ENTITY" or command == "CHANGE_ENTITY"):
            id_tags = packet.id_tags
            tags = packet.tags
            t = []
            if ("id" in id_tags.keys()):
                t = FindByTags(["ENTITY_ID"], [id_tags["id"]], entities)
            if (len(t) == 0) and ("ID" in id_tags.keys()):
                t = FindByTags(["ENTITY_ID"], [id_tags["ID"]], entities)
            if (len(t) == 0) and ("Entity" in id_tags.keys()):
                t = FindByTags(["Entity"], [id_tags["Entity"]], entities)
            if (len(t) == 0) and ("Entity" in id_tags.keys()):
                t = FindByTags(["ENTITY_ID"], [id_tags["Entity"]], entities)
            if (len(t) == 0) and ("Entity" in id_tags.keys()):
                t = FindByTags(["entityName"], [id_tags["Entity"]], entities)

            
            if (len(t) == 0):
                print(f"Error, entity not found from tags {" ".join(id_tags.keys())} with values {" ".join(id_tags.values())}")
            
            else:
                entity = entities[t[0][0]]

                for tag, value in zip(tags.keys(), tags.values()):
                    entity[tag] = value

            
    

    print(len(entities))



