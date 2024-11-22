class Packet:
    def __init__(self, timestamp, packet_type, command):
        self.timestamp = timestamp
        self.packet_type = packet_type
        self.command = command
    
    # Useful for debugging and in the analyzer
    def __repr__(self):
        return f"{self.command}"

def pair_tags(tags):
    pairs = list(zip(tags[::2], tags[1::2]))
    pairs = [(i[0][1], i[1][1]) for i in pairs]
    return pairs

class CreateGame(Packet):
    def __init__(self, timestamp, packet_type, command_name, GameEntity_il_tags, game_tags, player_1, player_1_tags, player_2, player_2_tags):
        super().__init__(timestamp, packet_type, command_name)

        # game entity info

        self.game_tags = {}
        self.game_tags[GameEntity_il_tags[0][0]] = GameEntity_il_tags[0][1]

        for tag, value in pair_tags(game_tags.as_list()):
            self.game_tags[tag] = value

        # player1 info

        self.p1_tags = {}
        for tag, value in player_1[1].as_list()[:-2]:   # skips the playerid tags. I have no idea what they mean and are not handled well by the parser
            self.p1_tags[tag] = value

        for tag, value in pair_tags(player_1_tags.as_list()):
            self.p1_tags[tag] = value
        
        # player2 info

        self.p2_tags = {}
        for tag, value in player_2[1].as_list()[:-2]:   # skips the playerid tags. I have no idea what they mean and are not handled well by the parser
            self.p2_tags[tag] = value

        for tag, value in pair_tags(player_2_tags.as_list()):
            self.p2_tags[tag] = value

    def __repr__(self):
        game_tags = [f"\t\t{tag} = {val}\n" for tag,val in zip(self.game_tags.keys(), self.game_tags.values())]
        p1_tags = [f"\t\t{tag} = {val}\n" for tag,val in zip(self.p1_tags.keys(), self.p1_tags.values())]
        p2_tags = [f"\t\t{tag} = {val}\n" for tag,val in zip(self.p2_tags.keys(), self.p2_tags.values())]

        return f"{self.command}:\n\tGame: \n{"".join(game_tags)}\tPlayer 1: \n{"".join(p1_tags)}\tPlayer 2: \n{"".join(p2_tags)}"

class FullEntity(Packet):
    def __init__(self, timestamp, packet_type, command, il_tags, tags):
        super().__init__(timestamp, packet_type, command)

        # inline tags are sometimes used to id the entity to act on (ex: if - Updating), other times just used to give more tag values
        # the plan is to check every time if an entity with the tags described exists and use this to understand how to handle the inline tags
        self.id_tags = {}
        for tag, value in il_tags.as_list():
            self.id_tags[tag] = value
        
        # these are the tags to give to the new entity/to set on an existing entity
        self.tags = {}
        for tag, value in pair_tags(tags.as_list()):
            self.tags[tag] = value
    
    def __repr__(self):
        id_tags = [f"\t\t{tag} = {val}\n" for tag,val in zip(self.id_tags.keys(), self.id_tags.values())]
        tags = [f"\t\t{tag} = {val}\n" for tag,val in zip(self.tags.keys(), self.tags.values())]

        return f"{self.command}:\n\tInline tags: \n{"".join(id_tags)}\tTags: \n{"".join(tags)}"

# Show entity packets can be handled the same as full entities
class ShowEntity(FullEntity):
    def __init__(self, timestamp, packet_type, command, il_tags, tags):
        super().__init__(timestamp, packet_type, command, il_tags, tags)

        self.tags["hidden"] = "0"

class TagChange(Packet):
    def __init__(self, timestamp, packet_type, command, tags):
        super().__init__(timestamp, packet_type, command)

        # these tags are used to id the entity to act on
        self.id_tags = {}
        for tag, value in tags.as_list()[:-2]:
            self.id_tags[tag] = value

        # these are the tags to change
        self.tags = {}
        for tag, value in pair_tags(tags.as_list()[-2:]):
            self.tags[tag] = value
    
    def __repr__(self):
        id_tags = [f"\t\t{tag} = {val}\n" for tag,val in zip(self.id_tags.keys(), self.id_tags.values())]
        tags = [f"\t\t{tag} = {val}\n" for tag,val in zip(self.tags.keys(), self.tags.values())]

        return f"{self.command}:\n\tID tags: \n{"".join(id_tags)}\tUpdated tags: \n{"".join(tags)}"

# Hide entity packets can be handled the same as tag changes
class HideEntity(TagChange):
    def __init__(self, timestamp, packet_type, command, tags):
        super().__init__(timestamp, packet_type, command, tags)

        self.tags["hidden"] = "1"

# Change entity is identical to tag change
class ChangeEntity(TagChange):
    def __init__(self, timestamp, packet_type, command, tags):
        super().__init__(timestamp, packet_type, command, tags)

class PlayerId(Packet):
    def __init__(self, timestamp, packet_type, command, id, name):
        super().__init__(timestamp, packet_type, command)
        self.id = id
        self.name = name
    
    def __repr__(self):
        return f"{self.command}\t{self.id}\t{self.name}\n"

# Convert parsed packet data to a list of packet objects
def GetPacketList(packet_data, dbg=False):
    packets = []

    for packet in packet_data:
        try:
            timestamp = packet["timestamp"]
            ptype = packet["packet_type"]
            command = packet["command_name"]
            
            if (command == "CREATE_GAME"):
                ge_il_tags = packet["GameEntity_il_tags"]
                game_tags = packet["game_tags"]
                p1 = packet["player_1"]
                p1_tags = packet["player_1_tags"]
                p2 = packet["player_2"]
                p2_tags = packet["player_2_tags"]

                packets.append(CreateGame(timestamp, ptype, command, ge_il_tags, game_tags, p1, p1_tags, p2, p2_tags))

            elif (command == "FULL_ENTITY"):
                il_tags = packet["il_tags"]
                tags = packet["tags"]

                packets.append(FullEntity(timestamp, ptype, command, il_tags, tags))

            elif (command == "SHOW_ENTITY"):
                il_tags = packet["il_tags"]
                tags = packet["tags"]

                packets.append(ShowEntity(timestamp, ptype, command, il_tags, tags))
            
            elif (command == "TAG_CHANGE"):
                tags = packet["tags"]

                packets.append(TagChange(timestamp, ptype, command, tags))

            elif (command == "HIDE_ENTITY"):
                tags = packet["tags"]

                packets.append(HideEntity(timestamp, ptype, command, tags))
            
            elif (command == "CHANGE_ENTITY"):
                tags = packet["tags"]

                packets.append(ChangeEntity(timestamp, ptype, command, tags))
            
            elif (command == "PlayerID"):
                id = packet["id"]
                name = packet["name"]

                packets.append(PlayerId(timestamp, ptype, command, id, name))

        # This catches packets not implemented in the parser
        except KeyError:
            if (dbg):
                print(f"Error on packet: {" ".join(packet.as_list())}")
            else:
                pass

    return packets
