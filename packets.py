class Packet:
    def __init__(self, timestamp, packet_type, command):
        self.timestamp = timestamp
        self.packet_type = packet_type
        self.command = command

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

# Show entity packets can be handled the same as tag changes
class HideEntity(TagChange):
    def __init__(self, timestamp, packet_type, command, tags):
        super().__init__(timestamp, packet_type, command, tags)

        self.tags["hidden"] = "1"

# Change entity is identical to tag change
class ChangeEntity(TagChange):
    def __init__(self, timestamp, packet_type, command, tags):
        super().__init__(timestamp, packet_type, command, tags)
