import gamelib

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

        self.basic_template = {'filters': all_filters}
        gamelib.debug_write("Beautiful")
        gamelib.debug_write(self.basic_template['filters'])

    def on_game_start(self, config):
        self.config = config;
        global FILTER, ENCRYPTOR, DESTRUCTOR, PING, EMP, SCRAMBLER, UNIT_TO_ID
        FILTER, ENCRYPTOR, DESTRUCTOR, PING, EMP, SCRAMBLER = [config['unitInformation'][idx]["shorthand"] for idx in range(6)]

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
                gamelib.debug_write(f"{firewall_unit} deployed at {loc}")
                game_state._player_resources[0]['cores'] -= game_state.type_cost(firewall_unit)[0]

            elif not game_state.contains_stationary_unit(loc):
                return False

        return True

    def defense(self, game_state):
        filters = self.basic_template['filters']
        if not self.build_defenses(filters, FILTER, game_state):
            return

        row = 11
        destructors = [2, 25, 6, 21, 11, 16]
        if not self.build_defenses(destructors, DESTRUCTOR, game_state, row=row):
            return

        # filters = [3, 24, 4, 23, 5, 22, 7, 20, 8, 19, 9]
        # if not self.build_defenses(filters, FILTER, game_state, row=row):
        #     return

    def attack(self, game_state):
        pass


if __name__ == "__main__":
    algo = FirstAlgo()
    algo.start()
