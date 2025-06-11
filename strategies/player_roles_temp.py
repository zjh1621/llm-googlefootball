import math
import numpy as np

# Action constants from observation.md
ACTION_IDLE = 0
ACTION_LEFT = 1
ACTION_TOP_LEFT = 2
ACTION_TOP = 3
ACTION_TOP_RIGHT = 4
ACTION_RIGHT = 5
ACTION_BOTTOM_RIGHT = 6
ACTION_BOTTOM = 7
ACTION_BOTTOM_LEFT = 8
ACTION_LONG_PASS = 9
ACTION_HIGH_PASS = 10
ACTION_SHORT_PASS = 11
ACTION_SHOT = 12
ACTION_SPRINT = 13
ACTION_RELEASE_DIRECTION = 14
ACTION_RELEASE_SPRINT = 15
ACTION_SLIDING = 16
ACTION_DRIBBLE = 17
ACTION_RELEASE_DRIBBLE = 18

# GameMode constants
GAME_MODE_NORMAL = 0
GAME_MODE_KICKOFF = 1
GAME_MODE_GOALKICK = 2
GAME_MODE_FREEKICK = 3
GAME_MODE_CORNER = 4
GAME_MODE_THROWIN = 5
GAME_MODE_PENALTY = 6

# Indices for sticky actions
STICKY_LEFT = 0
STICKY_TOP_LEFT = 1
STICKY_TOP = 2
STICKY_TOP_RIGHT = 3
STICKY_RIGHT = 4
STICKY_BOTTOM_RIGHT = 5
STICKY_BOTTOM = 6
STICKY_BOTTOM_LEFT = 7
STICKY_SPRINT = 8
STICKY_DRIBBLE = 9

# --- Helper Functions ---

def get_my_pos(obs):
    """Returns the position of the active player."""
    return obs.player_position

def move_towards(my_pos, target_pos):
    """Returns a discrete move action to get closer to target_pos."""
    my_pos = np.array(my_pos)
    target_pos = np.array(target_pos)
    direction = target_pos - my_pos
    
    if np.linalg.norm(direction) < 0.03:
        return ACTION_IDLE

    if abs(direction[0]) > 2 * abs(direction[1]):
        if direction[0] > 0: return ACTION_RIGHT
        else: return ACTION_LEFT
    elif abs(direction[1]) > 2 * abs(direction[0]):
        if direction[1] > 0: return ACTION_BOTTOM
        else: return ACTION_TOP
    else:
        if direction[0] > 0 and direction[1] > 0: return ACTION_BOTTOM_RIGHT
        elif direction[0] > 0 and direction[1] < 0: return ACTION_TOP_RIGHT
        elif direction[0] < 0 and direction[1] > 0: return ACTION_BOTTOM_LEFT
        elif direction[0] < 0 and direction[1] < 0: return ACTION_TOP_LEFT
        else: return ACTION_IDLE

def find_open_teammate(obs, min_dist_from_opp=0.1):
    """Finds the best teammate to pass to."""
    my_pos = get_my_pos(obs)
    best_teammate_idx = -1
    max_open_dist = -1

    for i, teammate_pos in enumerate(obs.left_team_positions):
        if i == obs.active_player or not obs.observation['left_team_active'][i]:
            continue

        closest_opp_dist = min([np.linalg.norm(np.array(teammate_pos) - np.array(opp_pos)) for opp_pos in obs.right_team_positions])
        
        if closest_opp_dist > min_dist_from_opp:
            if closest_opp_dist > max_open_dist:
                max_open_dist = closest_opp_dist
                best_teammate_idx = i

    return best_teammate_idx

# --- Role Implementations ---

def goalkeeper_actions(obs):
    pass

def centre_back_actions(obs):
    pass

def left_back_actions(obs):
    pass

def right_back_actions(obs):
    pass

def defence_midfielder_actions(obs):
    pass

def central_midfielder_actions(obs):
    pass

def left_midfielder_actions(obs):
    pass

def right_midfielder_actions(obs):
    pass

def attack_midfielder_actions(obs):
    pass

def central_forward_actions(obs):
    pass