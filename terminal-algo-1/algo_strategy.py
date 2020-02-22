import gamelib
import random
import math
import warnings
from sys import maxsize
import json

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

    def on_game_start(self, config):
        self.config = config;
        global FILTER, ENCRYPTOR, DESTRUCTOR, PING, EMP, SCRAMBLER, UNIT_TO_ID
        FILTER, ENCRYPTOR, DESTRUCTOR, PING, EMP, SCRAMBLER = [config['unitInformation'][idx]["shorthand"] for idx in range(6)]
        self.scored_on_locations = []

    def on_turn(self, turn_state):
        game_state = gamelib.GameState(self.config, turn_state)
        game_state.enable_warnings = False

        self.defense(game_state)
        self.offensive_strategy(game_state)

        game_state.submit_turn()

    def build_defenses(self, location_list, firewall_unit, game_state, row=None):
        for loc in location_list:
            if not type(loc) == list:
                loc = [loc, row]

            if game_state.can_spawn(firewall_unit, loc):
                game_state.attempt_spawn(firewall_unit, loc)
                gamelib.debug_write(f"{firewall_unit} deployed at {loc}")
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

    def offensive_strategy(self, game_state):
        our_resources, enemy_resources = game_state.get_resources(player_index=0), game_state.get_resources(
            player_index=1)

        # Switch focus to "defensive" offensive
        if enemy_resources[1] >= 10:
            start_locs = [[13, 0], [14, 0]]
            for i in range(math.ceil(enemy_resources[1] / 5) - 1):
                game_state.attempt_spawn(game_state.SCRAMBLER, start_locs[i % 2])
        else:
            prob = random.random()
            if prob <= 0.1:
                return

            attack_positions_left = self.filter_blocked_locations([[i, 13 - i] for i in range(14)], game_state)
            attack_positions_right = self.filter_blocked_locations([[i + 14, i] for i in range(14)], game_state)

            # Evaluate defensive rating
            attack_rating_single = []
            attack_rating_double = []
            for attack_pos in attack_positions_left + attack_positions_right:
                hit_profit, damage, i = [0], 0, 0
                path = game_state.find_path_to_edge(attack_pos)
                path_length = len(path)
                for loc in path:
                    encounters = self.game_map.get_locations_in_range(loc, game_state.EMP.get('attackRange', 0))
                    offensive_hits = len([game_state.contains_stationary_unit(unit) for unit in encounters])
                    defensive_hits = game_state.get_attackers(loc, 1)
                    if defensive_hits + damage <= 2:
                        hit_profit.append((offensive_hits - defensive_hits + hit_profit[i]))
                        damage += defensive_hits
                        i += 1
                        if damage >= 1:
                            attack_rating_single.append((attack_pos, max(hit_profit), path_length))
                    else:
                        break
                attack_rating_double.append((attack_pos, max(hit_profit), path_length))
            attack_rating_single.sort(key=lambda x: x[1], reverse=True)
            attack_rating_double.sort(key=lambda x: x[1], reverse=True)
            top_pos_single, top_pos_double = attack_rating_single[:2], attack_rating_double[:2]

            num_emp = game_state.number_affordable(game_state.EMP)
            emp_deployed = 0
            total_hits = 0
            if game_state.turn_number < 30:
                for i in range(2):
                    if attack_rating_double[i][1] >= 1.5 * attack_rating_single[0][1]:
                        if num_emp >= 2 and prob > 0.5:
                            game_state.attempt_spawn(game_state.EMP, top_pos_double[i], num=2)
                            num_emp -= 2
                            emp_deployed += 2
                            total_hits += attack_rating_double[i][1]
                    elif attack_rating_single[i][1] >= 7:
                        if num_emp >= 2 and prob > 0.33:
                            game_state.attempt_spawn(game_state.EMP, top_pos_single[i], num=2)
                            num_emp -= 2
                            emp_deployed += 2
                            total_hits += attack_rating_single[i][1]

                if emp_deployed > 0:
                    cost = our_resources[1] - emp_deployed
                    if total_hits >= 15:
                        game_state.attempt_spawn(game_state.PING, sorted(attack_rating_single, key=lambda x: x[2])[0],
                                                 num=cost)
            else:
                game_state.attempt_spawn(game_state.EMP, top_pos_double[0], num=num_emp)


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
