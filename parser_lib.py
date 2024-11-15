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

        # Used as a catch-all for un-handled packets. Has to be last in the expression declaration
        generic_packet = self.line_start + SkipTo("\n")

        # The rules need to be combined to form an expression that can then be compared to the content of the text
        self.expr = self.create_game_packet | self.full_entity_packet | self.tag_change_packet | self.hide_entity_packet | self.show_entity_packet | self.change_entity_packet| self.block_start_packet | generic_packet

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
        self.key_value = (Optional(Suppress("Entity=[")) + Optional(Suppress("[")) + Group(key('key') + Suppress('=') + value('value')) + Optional(Suppress("]"))).set_results_name("key_vals")

        # Lines always start with the same pattern
        self.line_start = self.initial_char + self.timestamp + self.packet_type + self.separator

    def tag_change_rule(self):
        command_name = Keyword('TAG_CHANGE')('command_name')
        self.tag_change_packet = self.line_start + command_name + Group(OneOrMore(self.key_value))("tags")

    def create_game_rule(self):
        # Rules describing the lines that make up the packet
        command_start = self.line_start + Literal("CREATE_GAME")('command_name')
        game_entity = Suppress(self.line_start) + Literal("GameEntity") + self.key_value("GameEntity-tags")
        tag_line = Suppress(self.line_start) + OneOrMore(self.key_value)
        player = Suppress(self.line_start) + Literal("Player") + Group(OneOrMore(self.key_value))("Player-tags")

        # Rule for the actual command
        self.create_game_packet = command_start + game_entity + Group(OneOrMore(tag_line)) + player + Group(OneOrMore(tag_line)) + player + Group(OneOrMore(tag_line))

    def full_entity_rule(self):
        command_start = self.line_start + Literal("FULL_ENTITY")('command_name') + self.separator + Word(alphas) + Group(OneOrMore(self.key_value))
        tag_line = Suppress(self.line_start) + OneOrMore(self.key_value)

        self.full_entity_packet = command_start + Group(OneOrMore(tag_line))

    def hide_entity_rule(self):
        command_name = Keyword("HIDE_ENTITY")('command_name')
        self.hide_entity_packet = self.line_start + command_name + self.separator + Group(OneOrMore(self.key_value))
    
    def show_entity_rule(self):
        command_name = Keyword("SHOW_ENTITY")('command_name')
        first_line = self.line_start + command_name + self.separator + Word(alphas) + Group(OneOrMore(self.key_value))
        tag_line = Suppress(self.line_start) + OneOrMore(self.key_value)

        self.show_entity_packet = first_line + Group(OneOrMore(tag_line))

    def change_entity_rule(self):
        command_name = Keyword("CHANGE_ENTITY")('command_name')
        self.change_entity_packet = self.line_start + command_name + self.separator + Word(alphas) + Group(OneOrMore(self.key_value))

    def block_start_rule(self):
        # This packet is not necessary and is usually only used for grouping other packets to create in-game animations
        # It can be useful to detect some actions related to this animations
        command_name = Keyword("BLOCK_START")('command_name')
        self.block_start_packet = self.line_start + command_name + Group(OneOrMore(self.key_value))

    def parse_str(self, string):
        return self.expr.search_string(string)


if __name__ == "__main__":
    filename = "test-data/test_files/" + "2024-10-26-15-10" + ".log"
    filename = "test-data/test_files/" + "test" + ".log"

    p = Parser()

    with open(f"{filename}") as file:
        t = file.read()

    t0 = time()
    res = p.parse_str(t)
    t1 = time()

    print(f"Parsing time: {t1-t0:.2f}s")

    for i in res:
        try:
            print(i["command_name"])
        except:
            print(i.as_list())

    t = res.as_list()
    #t = [(i[1], i[3]) for i in t]

    with open("tout.json", "w") as file:
        dump(t, file, indent=4)