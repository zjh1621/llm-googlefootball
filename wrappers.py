import numpy as np
import gfootball.env as football_env

class PlayerObservationWrapper:
    def __init__(self, observation, wrapper):
        self.wrapper = wrapper
        self.observation = observation

        # Ball information
        self.ball_position = observation['ball'][:2]  # x, y position of the ball
        self.ball_direction = observation['ball_direction'][:2]  # x, y direction of the ball
        self.ball_owned_team = observation['ball_owned_team']
        self.ball_owned_player = observation['ball_owned_player']

        # Player information
        self.active_player = observation['active']  # Index of the controlled player
        self.player_position = observation['left_team'][self.active_player]
        self.player_direction = observation['left_team_direction'][self.active_player]
        self.player_tired_factor = observation['left_team_tired_factor'][self.active_player]
        self.player_yellow_card = observation['left_team_yellow_card'][self.active_player]
        self.player_active = observation['left_team_active'][self.active_player]
        self.player_role = observation['left_team_roles'][self.active_player]

        # Team information
        self.left_team_positions = observation['left_team']
        self.left_team_directions = observation['left_team_direction']
        self.right_team_positions = observation['right_team']
        self.right_team_directions = observation['right_team_direction']

        # Game state
        self.game_mode = observation['game_mode']
        self.score = observation['score']
        self.steps_left = observation['steps_left']
        self.sticky_actions = observation['sticky_actions']

        # Precomputed distances
        self.distance_to_ball = self.compute_distance(self.player_position, self.ball_position)
        self.distances_to_teammates = [
            self.compute_distance(self.player_position, teammate_pos)
            for i, teammate_pos in enumerate(self.left_team_positions) if i != self.active_player
        ]
        self.distances_to_opponents = [
            self.compute_distance(self.player_position, opponent_pos)
            for opponent_pos in self.right_team_positions
        ]

    @staticmethod
    def compute_distance(a, b):
        return np.linalg.norm(np.array(a) - np.array(b))

    def is_ball_owned_by_player(self):
        return self.ball_owned_team == 0 and self.ball_owned_player == self.active_player

    def is_ball_owned_by_team(self, team=0):
        return self.ball_owned_team == team

    def is_ball_free(self):
        return self.ball_owned_team == -1


class ObservationWrapper:
    def __init__(self, observations):
        self.player_observations = [PlayerObservationWrapper(obs, self) for obs in observations]


class ActionWrapper:
    def __init__(self, env):
        self.env = env

    def step(self, actions):
        return self.env.step(actions)

    def write_dump(self):
        self.env.write_dump('shutdown')