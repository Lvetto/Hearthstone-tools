from pyparsing import (
    Word, alphas, nums, Combine, Suppress, Optional, Group, Keyword,
    OneOrMore, alphanums, quotedString, White, ZeroOrMore, restOfLine, Regex, Literal, printables, SkipTo
)
from time import time
from json import dump

class Parser:
    def __init__(self):
        # For readability purposes, the various rules are defined by methods that have to be called when the parser object is created
        self.basic_rules()
        self.tag_change_rule()
        self.create_game_rule()
        self.full_entity_rule()
        self.hide_entity_rule()
        self.show_entity_rule()
        self.change_entity_rule()
        self.block_start_rule()
        self.block_end_rule()
        self.playerId_rule()

        # Used as a catch-all for un-handled packets. Has to be last in the expression declaration
        generic_packet = self.line_start + SkipTo("\n")

        # The rules need to be combined to form an expression that can then be compared to the content of the text
        self.expr = self.create_game_packet | self.full_entity_packet | self.tag_change_packet | self.hide_entity_packet | self.show_entity_packet | self.change_entity_packet| self.block_start_packet | self.block_end_packet | self.playerId_packet | generic_packet

    # This method defines some basic patterns used to define more specific rules for the various commands. It is intended to be only called by the __init__
    # Currently this defines rules for: initial_char, timestamp, packet_type, separator, key_value pair, line_start
    def basic_rules(self):
        # Define a rule to recognise the initial character (almost always 'D')
        self.initial_char = Word(alphas, exact=1).setResultsName('initial_char')

        # Matches the timestamp in format HH:MM:SS.milliseconds
        self.timestamp = Combine(
            Word(nums, exact=2) + ':' +
            Word(nums, exact=2) + ':' +
            Word(nums, exact=2) + '.' +
            Word(nums)
        ).setResultsName('timestamp')

        # Matches the packet type, e.g., GameState.DebugPrintPower()
        self.packet_type = Combine(Word(alphas) + '.' + Word(alphas) + '()').setResultsName('packet_type')

        # Separator '-'
        self.separator = Suppress(ZeroOrMore(White(' \t')) + '-' + ZeroOrMore(White(' \t')))

        # Define a rule for key-value pairs
        key = Word(alphanums + '_')
        value = Regex(r'.*?(?=\s+\w+=|\]|$)') + Optional(Suppress("]"))| Word(alphanums + '_') + Optional(Suppress("]"))
        self.key_value = (Optional(Suppress("Entity=[")) + Optional(Suppress("[")) + Group(key('key') + Suppress('=') + value('value')) + Optional(Suppress("]")))#.set_results_name("key_vals")

        # Lines always start with the same pattern
        self.line_start = self.initial_char + self.timestamp + self.packet_type + self.separator

    def tag_change_rule(self):
        command_name = Keyword('TAG_CHANGE')('command_name')
        self.tag_change_packet = self.line_start + command_name + Group(OneOrMore(self.key_value))("tags")

    def create_game_rule(self):
        command_start = self.line_start + Literal("CREATE_GAME")('command_name')
        game_entity = Suppress(self.line_start) + Literal("GameEntity") + self.key_value("GameEntity_il_tags")
        tag_line = Suppress(self.line_start) + OneOrMore(self.key_value)
        player = Suppress(self.line_start) + Literal("Player") + Group(OneOrMore(self.key_value))

        self.create_game_packet = command_start + game_entity + Group(OneOrMore(tag_line))("game_tags") + player("player_1") + Group(OneOrMore(tag_line))("player_1_tags") + player("player_2") + Group(OneOrMore(tag_line))("player_2_tags")

    def full_entity_rule(self):
        command_start = self.line_start + Literal("FULL_ENTITY")('command_name') + self.separator + Word(alphas) + Group(OneOrMore(self.key_value))("il_tags")
        tag_line = Suppress(self.line_start) + OneOrMore(self.key_value)

        self.full_entity_packet = command_start + Group(OneOrMore(tag_line))("tags")

    def hide_entity_rule(self):
        command_name = Keyword("HIDE_ENTITY")('command_name')
        self.hide_entity_packet = self.line_start + command_name + self.separator + Group(OneOrMore(self.key_value))("tags")
    
    def show_entity_rule(self):
        command_name = Keyword("SHOW_ENTITY")('command_name')
        first_line = self.line_start + command_name + self.separator + Word(alphas)("type") + Group(OneOrMore(self.key_value))("il_tags")
        tag_line = Suppress(self.line_start) + OneOrMore(self.key_value)

        self.show_entity_packet = first_line + Group(OneOrMore(tag_line))("tags")

    def change_entity_rule(self):
        command_name = Keyword("CHANGE_ENTITY")('command_name')
        self.change_entity_packet = self.line_start + command_name + self.separator + Word(alphas)("type") + Group(OneOrMore(self.key_value))("tags")

    def block_start_rule(self):
        # This packet is not necessary and is usually only used for grouping other packets to create in-game animations
        # It can be useful to detect some actions related to these animations
        command_name = Keyword("BLOCK_START")('command_name')
        self.block_start_packet = self.line_start + command_name + Group(OneOrMore(self.key_value))("tags")
    
    def block_end_rule(self):
        # Also not necessary and only useful for animations
        command_name = Keyword("BLOCK_END")('command_name')
        self.block_end_packet = self.line_start + command_name
    
    def playerId_rule(self):
        command_name = Keyword("PlayerID")("command_name")
        self.playerId_packet = self.line_start + command_name + Suppress("=") + Word(alphanums)("id") + Suppress(",") + Suppress("PlayerName=") + Word(alphanums + "#")("name")

    def parse_str(self, string):
        return self.expr.search_string(string)

# Currently only used for testing
if __name__ == "__main__":
    filename = "test-data/test_files/" + "11-13_17-06-copy" + ".log"
    #filename = "test-data/test_files/" + "test" + ".log"

    p = Parser()

    with open(f"{filename}") as file:
        data = file.read()
    
    t0 = time()

    packet_data = p.parse_str(data)

    t1 = time()

    print(f"Parsing time: {t1 -t0:.2f}s")

    # Just for testing. Should be moved elsewhere

    from packets import *

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


        except KeyError:
            print(f"Error on packet: {" ".join(packet.as_list())}")
    
    from entities import *

    print(f"\n\n{"-" * 100} \n\n")

    t0 = time()

    t = get_entity_list(packets)

    t1 = time()
    print(f"Elaboration time: {t1-t0:.2f}s")

