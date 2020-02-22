import gamelib
import json
from array import *

class FirstAlgo(gamelib.AlgoCore):

    def __init__(self):
        # Stores the initial template

        # Corners of the filters in the basic template
        corners = [[0, 13], [2, 13], [8, 7], [12, 7], [12, 13]]
        all_filters = []

        # Adds all the locations in between the above corners to all_filters
        for i in range(len(corners) - 1):
            if corners[i+1][0] - corners[i][0] > 0:
                x_increment = 1
            elif corners[i+1][0] - corners[i][0] < 0:
                x_increment = -1
            else:
                x_increment = 0
            if corners[i+1][1] - corners[i][1] > 0:
                y_increment = 1
            elif corners[i+1][1] - corners[i][1] < 0:
                y_increment = -1
            else:
                y_increment = 0

            x = corners[i][0]
            y = corners[i][1]
            while x != corners[i+1][0] or y != corners[i+1][1]:
                all_filters.append([x, y])
                all_filters.append([27 - x, y])
                x += x_increment
                y += y_increment

        self.basic_template = {'filters': all_filters, 'destructors': [[11, 12], [16, 12], [1, 12], [26, 12], [12, 5], [15, 5]]}
        gamelib.debug_write("Beautiful")
        gamelib.debug_write(self.basic_template['filters'])

    def build(self, game_state, lst):
        priority = lst[0]
        unit = lst[1]
        position = lst[2]
        build = lst[3]

        if lst[3]:
            return game_state.attempt_spawn(unit, position)
        else:
            return game_state.attempt_upgrade(position)

    def build_funnel(self, game_state):
        firewalls = {
            0: FILTER,
            1: DESTRUCTOR,
            2: ENCRYPTOR
        }

        pqueue = []

        for x in range(3):
            pqueue.append([100, FILTER, [10 - x + 2, 13], True])
            pqueue.append([100, FILTER, [15 + x, 13], True])
        for x in range(3):
            for y in range(12, 7, -1):
                pqueue.append([50 + y, firewalls[x], [10 - x + 2, y], True])
                pqueue.append([50 + y, firewalls[x], [15 + x, y], True])

        for x in range(3):
            for y in range(13, 10, -1):
                pqueue.append([10 + y, None, [10 - x + 2, y], False])
                pqueue.append([10 + y, None, [15 + x, y], False])

        pqueue = sorted(pqueue, key = lambda x: x[0], reverse = True)

        for item in pqueue:
            self.build(game_state, item)

    def on_game_start(self, config):
        self.config = config;
        global FILTER, ENCRYPTOR, DESTRUCTOR, PING, EMP, SCRAMBLER, UNIT_TO_ID
        FILTER, ENCRYPTOR, DESTRUCTOR, PING, EMP, SCRAMBLER = [config['unitInformation'][idx]["shorthand"] for idx in range(6)]
        self.scored_on_locations = []
        #self.init_funnel()


    def on_turn(self, turn_state):
        game_state = gamelib.GameState(self.config, turn_state)
        game_state.enable_warnings = False

        self.defense(game_state)
        self.attack(game_state)

        game_state.submit_turn()

    def build_defenses(self, location_list, firewall_unit, game_state, row=None):
        for loc in location_list:
            if not type(loc) == list:
                loc = [loc, row]

            if game_state.can_spawn(firewall_unit, loc):
                game_state.attempt_spawn(firewall_unit, loc)
                gamelib.debug_write("{firewall_unit} deployed at {loc}")
                game_state._player_resources[0]['cores'] -= game_state.type_cost(firewall_unit)[0]

            elif not game_state.contains_stationary_unit(loc):
                return False

        return True

    def defense(self, game_state):


        if not self.build_defenses(self.basic_template['filters'][:len(self.basic_template['filters']) // 2], FILTER, game_state):
            return

        if not self.build_defenses(self.basic_template['destructors'], DESTRUCTOR, game_state):
            return

        if not self.build_defenses(self.basic_template['filters'][len(self.basic_template['filters']) // 2:], FILTER, game_state):
            return

        row = 11
        destructors = [2, 25, 6, 21, 11, 16]
        if not self.build_defenses(destructors, DESTRUCTOR, game_state, row=row):
            return

        if not self.build_funnel(game_state):
            return

        # filters = [3, 24, 4, 23, 5, 22, 7, 20, 8, 19, 9]
        # if not self.build_defenses(filters, FILTER, game_state, row=row):
        #     return

    def reactive_defense(self, game_state):
        for loc in self.scored_on_locations:
            gamelib.debug_write("updating most important filters")
            if 0 < loc[0] < 8:
                self.basic_template['filters'].insert(0, self.basic_template['filters'].pop(self.basic_template['filters'].index([loc[0] + 1, loc[1] + 1])))
            elif 27 > loc[0] > 19:
                self.basic_template['filters'].insert(0, self.basic_template['filters'].pop(self.basic_template['filters'].index([loc[0] - 1, loc[1] + 1])))


    def attack(self, game_state):
        pass

    def on_action_frame(self, turn_string):
        """
        This is the action frame of the game. This function could be called
        hundreds of times per turn and could slow the algo down so avoid putting slow code here.
        Processing the action frames is complicated so we only suggest it if you have time and experience.
        Full doc on format of a game frame at: https://docs.c1games.com/json-docs.html
        """
        # Let's record at what position we get scored on
        state = json.loads(turn_string)
        events = state["events"]
        breaches = events["breach"]
        for breach in breaches:
            location = breach[0]
            unit_owner_self = True if breach[4] == 1 else False
            # When parsing the frame data directly,
            # 1 is integer for yourself, 2 is opponent (StarterKit code uses 0, 1 as player_index instead)
            if not unit_owner_self:
                gamelib.debug_write("Got scored on at: {}".format(location))
                self.scored_on_locations.append(location)
                gamelib.debug_write("All locations: {}".format(self.scored_on_locations))


if __name__ == "__main__":
    algo = FirstAlgo()
    algo.start()
