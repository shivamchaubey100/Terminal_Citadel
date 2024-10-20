import gamelib
from gamelib import GameMap
import random
import math
import warnings
from sys import maxsize
import json


"""
Most of the algo code you write will be in this file unless you create new
modules yourself. Start by modifying the 'on_turn' function.

Advanced strategy tips: 

  - You can analyze action frames by modifying on_action_frame function

  - The GameState.map object can be manually manipulated to create hypothetical 
  board states. Though, we recommended making a copy of the map to preserve 
  the actual current map state.
"""

class AlgoStrategy(gamelib.AlgoCore):
    def __init__(self):
        super().__init__()
        seed = random.randrange(maxsize)
        random.seed(seed)
        gamelib.debug_write('Random seed: {}'.format(seed))
        self.scored_on_regions = [False, False, False, False, False, False]
        

    def on_game_start(self, config):
        """ 
        Read in config and perform any initial setup here 
        """
        gamelib.debug_write('Configuring your custom algo strategy...')
        self.config = config
        global WALL, SUPPORT, TURRET, SCOUT, DEMOLISHER, INTERCEPTOR, MP, SP
        WALL = config["unitInformation"][0]["shorthand"]
        SUPPORT = config["unitInformation"][1]["shorthand"]
        TURRET = config["unitInformation"][2]["shorthand"]
        SCOUT = config["unitInformation"][3]["shorthand"]
        DEMOLISHER = config["unitInformation"][4]["shorthand"]
        INTERCEPTOR = config["unitInformation"][5]["shorthand"]
        MP = 1
        SP = 0
        # This is a good place to do initial setup
        self.scored_on_locations = []
        # self.scored_on_regions = [False, False, False, False, False, False]
        self.LEFT_HIGH = 0
        self.RIGHT_HIGH = 1
        self.LEFT_MID=2
        self.RIGHT_MID=3
        self.LEFT_LOW = 4
        self.RIGHT_LOW = 5

        self.first_wall = True

    def on_turn(self, turn_state):
        """
        This function is called every turn with the game state wrapper as
        an argument. The wrapper stores the state of the arena and has methods
        for querying its state, allocating your current resources as planned
        unit deployments, and transmitting your intended deployments to the
        game engine.
        """
        self.wall_remove = False
        game_state = gamelib.GameState(self.config, turn_state)
        gamelib.debug_write('Performing turn {} of your custom algo strategy'.format(game_state.turn_number))
        game_state.suppress_warnings(True)  #Comment or remove this line to enable warnings.

        self.starter_strategy(game_state)

        game_state.submit_turn()


    """
    NOTE: All the methods after this point are part of the sample starter-algo
    strategy and can safely be replaced for your custom algo.
    """

    def starter_strategy(self, game_state):
        """
        For defense we will use a spread out layout and some interceptors early on.
        We will place turrets near locations the opponent managed to score on.
        For offense we will use long range demolishers if they place stationary units near the enemy's front.
        If there are no stationary units to attack in the front, we will send Scouts to try and score quickly.
        """
        # first build reactive defenses based on where the enemy scored
        self.build_reactive_defense(game_state)
        # Now, place basic defenses
        self.build_defences(game_state)
        

        # If the turn is less than 5, stall with interceptors and wait to see enemy's base
        # if game_state.turn_number < 5:
        #     self.stall_with_interceptors(game_state)
        # else:
            # # Now let's analyze the enemy base to see where their defenses are concentrated.
            # # If they have many units in the front we can build a line for our demolishers to attack them at long range.
            # else:
            #     # They don't have many units in the front so lets figure out their least defended area and send Scouts there.

            #     # Only spawn Scouts every other turn
            #     # Sending more at once is better since attacks can only hit a single scout at a time
            #     if game_state.turn_number % 2 == 1:
            #         # To simplify we will just check sending them from back left and right
            #         scout_spawn_location_options = [[13, 0], [14, 0]]
            #         best_location = self.least_damage_spawn_location(game_state, scout_spawn_location_options)
            #         game_state.attempt_spawn(SCOUT, best_location, 1000)

            #     # Lastly, if we have spare SP, let's build some supports
            #     support_locations = [[13, 2], [14, 2], [13, 3], [14, 3]]
            #     game_state.attempt_spawn(SUPPORT, support_locations)
        # if(game_state.get_resource(MP, 0) > 8):
        #     self.stall_with_interceptors(game_state, 1)
        if(self.detect_enemy_unit(game_state, None, None, [14,15]) > 20):
            self.demolisher_line_strategy(game_state)
        elif self.detect_enemy_unit(game_state, unit_type=None, valid_x=None, valid_y=[14, 15]) > 25:
            self.demolisher_line_strategy(game_state)
        if(game_state.get_resource(MP,1) > 10):
            self.stall_with_interceptors(game_state, 2)
        if(game_state.get_resource(MP, 0) > 10):
            scout_spawn_location_options = [[7,6], [10, 3], [13, 0], [16,2], [20,6]]
            best_location = self.least_damage_spawn_location(game_state, scout_spawn_location_options)
            game_state.attempt_spawn(SCOUT, [13,0],100)

    def build_defences(self, game_state):
        """
        Build basic defenses using hardcoded locations.
        Remember to defend corners and avoid placing units in the front where enemy demolishers can attack them.
        """
        # Useful tool for setting up your base locations: https://www.kevinbai.design/terminal-map-maker
        # More community tools available at: https://terminal.c1games.com/rules#Download

        #Priority 1:

        # Place turrets that attack enemy units
        turret_locations = [[4,11], [23,11]]
        
        # attempt_spawn will try to spawn units if we have resources, and will check if a blocking unit is already there
        game_state.attempt_spawn(TURRET, turret_locations)

        # upgrade turrets so they soak more damage
        game_state.attempt_upgrade(turret_locations)

        # Place walls in front of turrets to soak up damage for them
        wall_locations = [[1,12],[3,12],[5,12],[26,12],[24,12],[22,12]]
        game_state.attempt_spawn(WALL, wall_locations)

        if self.first_wall:
            wall_locations = [[0,13],[2,13],[4,13],[6,13],[27,13],[25,13],[23,13],[21,13]]
            game_state.attempt_spawn(WALL, wall_locations)  
        #Priority 2:

        # Place walls in front of turrets to soak up damage for them
        wall_locations = [[12,11],[12,12],[13,12],[14,12],[15,12],[15,11]]
        game_state.attempt_spawn(WALL, wall_locations)

        # Place turrets that attack enemy units
        turret_locations = [[13,11]]
        # attempt_spawn will try to spawn units if we have resources, and will check if a blocking unit is already there
        game_state.attempt_spawn(TURRET, turret_locations)
        # upgrade turrets so they soak more damage
        game_state.attempt_upgrade(turret_locations)

        # Place turrets that attack enemy units
        turret_locations = [[14,11]]
        # attempt_spawn will try to spawn units if we have resources, and will check if a blocking unit is already there
        game_state.attempt_spawn(TURRET, turret_locations)
        # upgrade turrets so they soak more damage
        game_state.attempt_upgrade(turret_locations)
        
        #Priority 3:
        #first layer Supports 
        support_locations = [[13,10]]
        game_state.attempt_spawn(SUPPORT, support_locations)
        game_state.attempt_upgrade(support_locations)

        support_locations = [[14,10]]
        game_state.attempt_spawn(SUPPORT, support_locations)
        game_state.attempt_upgrade(support_locations)
      
        
        #turrets in the middle
        turret_locations = [[8,11]]
        game_state.attempt_spawn(TURRET, turret_locations)
        game_state.attempt_upgrade(turret_locations)
        
        turret_locations = [[19,11]]
        game_state.attempt_spawn(TURRET, turret_locations)
        game_state.attempt_upgrade(turret_locations)

        #second layer Supports
        support_locations = [[13,9]]
        game_state.attempt_spawn(SUPPORT, support_locations)
        game_state.attempt_upgrade(support_locations)
        
        support_locations = [[14,9]]
        game_state.attempt_spawn(SUPPORT, support_locations)
        game_state.attempt_upgrade(support_locations)
        
        
    
        # For sufficient SP>10
        i=0
        if(game_state.get_resource(SP, 0) > 10):
            
            turret_locations = [[10,6]]
            game_state.attempt_spawn(TURRET, turret_locations)
            game_state.attempt_upgrade(turret_locations)
            
            turret_locations = [[17,6]]
            game_state.attempt_spawn(TURRET, turret_locations)
            game_state.attempt_upgrade(turret_locations)
            
            support_locations = [[13,8]]
            game_state.attempt_spawn(SUPPORT, support_locations)
            game_state.attempt_upgrade(support_locations)
            
            support_locations = [[14,8]]
            game_state.attempt_spawn(SUPPORT, support_locations)
            game_state.attempt_upgrade(support_locations)

            wall_locations = [[12,10],[12,9],[15,10],[15,9]]
            game_state.attempt_spawn(WALL, wall_locations)

            wall_locations = [[0,13],[1,12],[2,13],[3,12],[4,13],[5,12],[6,13],[27,13],[26,12],[25,13],[24,12],[23,13],[22,12],[21,13]]
            game_state.attempt_upgrade(wall_locations)

    def build_reactive_defense(self, game_state):
        """
        This function builds reactive defenses based on where the enemy scored on us from.
        We can track where the opponent scored by looking at events in action frames 
        as shown in the on_action_frame function
        """
        # for location in self.scored_on_locations:
        #     # Build turret one space above so that it doesn't block our own edge spawn locations
        #     build_location = [location[0], location[1]+1]
        #     game_state.attempt_spawn(TURRET, build_location)

        #Build turrets where opponent last scored
        turret_locations = []
        if(self.scored_on_regions[self.LEFT_HIGH]):
            turret_locations.append([2,12])
        elif(self.scored_on_regions[self.LEFT_MID]):
            turret_locations.append([7,8])
        elif(self.scored_on_regions[self.LEFT_LOW]):
            turret_locations.append([13,2])
        elif(self.scored_on_regions[self.RIGHT_LOW]):
            turret_locations.append([14,2])
        elif(self.scored_on_regions[self.RIGHT_MID]):
            turret_locations.append([20,8])
        elif(self.scored_on_regions[self.RIGHT_HIGH]):
            turret_locations.append([25,12])
        for x in turret_locations:
            game_state.attempt_spawn(TURRET, [x])
            game_state.attempt_upgrade([x])

    def stall_with_interceptors(self, game_state, num_interceptors = 1):
        """
        Send out interceptors at random locations to defend our base from enemy moving units.
        """
        # We can spawn moving units on our edges so a list of all our edge locations
        friendly_edges = game_state.game_map.get_edge_locations(game_state.game_map.BOTTOM_LEFT) + game_state.game_map.get_edge_locations(game_state.game_map.BOTTOM_RIGHT)
        
        # Remove locations that are blocked by our own structures 
        # since we can't deploy units there.
        deploy_locations = self.filter_blocked_locations(friendly_edges, game_state)
        
        count = 0

        # While we have remaining MP to spend lets send out interceptors randomly.
        while game_state.get_resource(MP) >= game_state.type_cost(INTERCEPTOR)[MP] and len(deploy_locations) > 0 and count < num_interceptors:
            # Choose a random deploy location.
            deploy_index = random.randint(0, len(deploy_locations) - 1)
            deploy_location = deploy_locations[deploy_index]
            
            game_state.attempt_spawn(INTERCEPTOR, deploy_location)
            count += 1
            """
            We don't have to remove the location since multiple mobile 
            units can occupy the same space.
            """

    def demolisher_line_strategy(self, game_state):
        """
        Build a line of the cheapest stationary unit so our demolisher can attack from long range.
        """
        # First let's figure out the cheapest unit
        # We could just check the game rules, but this demonstrates how to use the GameUnit class
        # stationary_units = [WALL, TURRET, SUPPORT]
        # cheapest_unit = WALL
        # for unit in stationary_units:
        #     unit_class = gamelib.GameUnit(unit, game_state.config)
        #     if unit_class.cost[game_state.MP] < gamelib.GameUnit(cheapest_unit, game_state.config).cost[game_state.MP]:
        #         cheapest_unit = unit

        # Now let's build out a line of stationary units. This will prevent our demolisher from running into the enemy base.
        # Instead they will stay at the perfect distance to attack the front two rows of the enemy base.
        # for x in range(27, 5, -1):
        #     game_state.attempt_spawn(cheapest_unit, [x, 11])

        # Now spawn demolishers next to the line
        # By asking attempt_spawn to spawn 1000 units, it will essentially spawn as many as we have resources for
        holes = self.get_holes(game_state)
        side = -1
        for hole in holes:
            if(hole > 13 and side != 0):
                side = 1
            elif (hole < 14 and side != 1):
                side = 0
            else:
                side = 2
        if(side == 0):
            game_state.attempt_spawn(DEMOLISHER, [24,10], 2)
        elif(side == 1):
            game_state.attempt_spawn(DEMOLISHER, [3,10], 2)
            
    def least_damage_spawn_location(self, game_state, location_options):
        """
        This function will help us guess which location is the safest to spawn moving units from.
        It gets the path the unit will take then checks locations on that path to 
        estimate the path's damage risk.
        """
        damages = []
        # Get the damage estimate each path will take
        for location in location_options:
            path = game_state.find_path_to_edge(location)
            damage = 0
            for path_location in path:
                # Get number of enemy turrets that can attack each location and multiply by turret damage
                damage += len(game_state.get_attackers(path_location, 0)) * gamelib.GameUnit(TURRET, game_state.config).damage_i
            damages.append(damage)
        
        # Now just return the location that takes the least damage
        return location_options[damages.index(min(damages))]

    def detect_enemy_unit(self, game_state, unit_type=None, valid_x = None, valid_y = None):
        total_units = 0
        holes = []
        for location in game_state.game_map:
            if game_state.contains_stationary_unit(location):
                for unit in game_state.game_map[location]:
                    if unit.player_index == 1 and (unit_type is None or unit.unit_type == unit_type) and (valid_x is None or location[0] in valid_x) and (valid_y is None or location[1] in valid_y):
                        total_units += 1
        return total_units

    def get_holes(self, game_state):
        valid_y = [14,15,16]
        valid_x = {0,1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19,20,21,22,23,24,25,26,27}
        valid_x_new = set()
        for i in range(len(valid_y)-1):
            for x in valid_x:
                if type(x) == tuple:
                    orig = x[1]
                    x = x[0]
                else:
                    orig = x
                if (game_state.game_map.in_arena_bounds((x,valid_y[0])) and not game_state.contains_stationary_unit([x, valid_y[0]]) and not game_state.contains_stationary_unit([x, valid_y[0]+1]) ):
                    valid_x_new.add((x,orig))
                    valid_x_new.add((x-1,orig))
                    valid_x_new.add((x+1,orig))
            valid_x = valid_x_new
            valid_x_new = set()
        return [x[1] for x in valid_x]

        
    def filter_blocked_locations(self, locations, game_state):
        filtered = []
        for location in locations:
            if not game_state.contains_stationary_unit(location):
                filtered.append(location)
        return filtered

    def on_action_frame(self, turn_string):
        """
        This is the action frame of the game. This function could be called 
        hundreds of times per turn and could slow the algo down so avoid putting slow code here.
        Processing the action frames is complicated so we only suggest it if you have time and experience.
        Full doc on format of a game frame at in json-docs.html in the root of the Starterkit.
        """
        # Let's record at what position we get scored on
        state = json.loads(turn_string)
        events = state["events"]
        breaches = events["breach"]
        self.scored_on_regions = [False, False, False, False, False, False]
        for breach in breaches:
            location = breach[0]
            unit_owner_self = True if breach[4] == 1 else False
            # When parsing the frame data directly, 
            # 1 is integer for yourself, 2 is opponent (StarterKit code uses 0, 1 as player_index instead)
            if not unit_owner_self:
                gamelib.debug_write("Got scored on at: {}".format(location))
                self.scored_on_locations.append(location)
                if( location[0] < 4):
                    self.scored_on_regions[self.LEFT_HIGH] = True
                elif(location[0] < 10):
                    self.scored_on_regions[self.LEFT_MID] = True
                elif(location[0] < 14):
                    self.scored_on_regions[self.LEFT_LOW] = True
                elif(location[0] < 18):
                    self.scored_on_regions[self.RIGHT_LOW] = True
                elif(location[0] < 24):
                    self.scored_on_regions[self.RIGHT_MID] = True
                elif(location[0] < 28):
                    self.scored_on_regions[self.RIGHT_HIGH] = True

                gamelib.debug_write("All locations: {}".format(self.scored_on_locations))


if __name__ == "__main__":
    algo = AlgoStrategy()
    algo.start()
