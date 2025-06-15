import math
import numpy as np

# Action constants
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

# Role constants
ROLE_GK = 0
ROLE_CB = 1
ROLE_LB = 2
ROLE_RB = 3
ROLE_DM = 4
ROLE_CM = 5
ROLE_LM = 6
ROLE_RM = 7
ROLE_AM = 8
ROLE_CF = 9

# Field dimensions
FIELD_X_MIN, FIELD_X_MAX = -1, 1
FIELD_Y_MIN, FIELD_Y_MAX = -0.42, 0.42
CENTER_X, CENTER_Y = 0, 0
PENALTY_AREA_X_MIN, PENALTY_AREA_X_MAX = 0.65, 1.0 # Approximate
PENALTY_AREA_Y_MIN, PENALTY_AREA_Y_MAX = -0.25, 0.25 # Approximate


# --- Helper Functions ---

def get_distance(pos1, pos2):
    return np.linalg.norm(np.array(pos1) - np.array(pos2))

def get_player(obs, role):
    for i, r in enumerate(obs.observation['left_team_roles']):
        if r == role and obs.observation['left_team_active'][i]:
            return {'pos': obs.observation['left_team'][i], 'dir': obs.observation['left_team_direction'][i], 'role': r, 'index': i}
    return None

def get_teammates(obs, roles=None):
    teammates = []
    for i, r in enumerate(obs.observation['left_team_roles']):
        if i == obs.active_player:
            continue
        if obs.observation['left_team_active'][i]:
            if roles is None or r in roles:
                teammates.append({'pos': obs.observation['left_team'][i], 'dir': obs.observation['left_team_direction'][i], 'role': r, 'index': i})
    return teammates

def get_opponents(obs):
    opponents = []
    for i, active in enumerate(obs.observation['right_team_active']):
        if active:
            opponents.append({'pos': obs.observation['right_team'][i], 'dir': obs.observation['right_team_direction'][i], 'index': i})
    return opponents

def get_closest_opponent_distance(player_pos, opponents):
    if not opponents:
        return float('inf')
    return min(get_distance(player_pos, opp['pos']) for opp in opponents)

def get_pressure_level(player_pos, opponents, high_thresh=0.1, medium_thresh=0.2):
    dist = get_closest_opponent_distance(player_pos, opponents)
    if dist < high_thresh:
        return '高'
    if dist < medium_thresh:
        return '中'
    return '低'

def is_in_defensive_third(player_pos):
    return player_pos[0] < -1/3

def is_in_middle_third(player_pos):
    return -1/3 <= player_pos[0] <= 1/3

def is_in_attacking_third(player_pos):
    return player_pos[0] > 1/3

def is_in_penalty_box(player_pos):
    return PENALTY_AREA_X_MIN < player_pos[0] < PENALTY_AREA_X_MAX and PENALTY_AREA_Y_MIN < player_pos[1] < PENALTY_AREA_Y_MAX

def find_open_teammates(obs, roles=None):
    teammates = get_teammates(obs, roles)
    opponents = get_opponents(obs)
    open_teammates = []
    for tm in teammates:
        closest_opp_dist = get_closest_opponent_distance(tm['pos'], opponents)
        if closest_opp_dist > 0.15: # Unmarked if opponent is further than this
            open_teammates.append(tm)
    return open_teammates

def find_best_pass_target(obs, open_teammates):
    if not open_teammates:
        return None
    
    # Simple logic: find the most forward-positioned open teammate
    best_target = None
    max_x = -2 # well outside the field
    for tm in open_teammates:
        if tm['pos'][0] > max_x:
            max_x = tm['pos'][0]
            best_target = tm
    return best_target


def get_move_action_to_target(player_pos, target_pos):
    dx = target_pos[0] - player_pos[0]
    dy = target_pos[1] - player_pos[1]
    
    # Remember: Y axis is inverted in google football env (down is positive)
    if abs(dx) > 2 * abs(dy):
        return ACTION_RIGHT if dx > 0 else ACTION_LEFT
    elif abs(dy) > 2 * abs(dx):
        return ACTION_BOTTOM if dy > 0 else ACTION_TOP
    else:
        if dx > 0 and dy > 0:
            return ACTION_BOTTOM_RIGHT
        elif dx > 0 and dy < 0:
            return ACTION_TOP_RIGHT
        elif dx < 0 and dy > 0:
            return ACTION_BOTTOM_LEFT
        else: # dx < 0 and dy < 0
            return ACTION_TOP_LEFT
    return ACTION_IDLE

def has_shooting_angle(player_pos):
    # Simplified: can shoot if in attacking third and reasonably central
    return is_in_attacking_third(player_pos) and abs(player_pos[1]) < 0.2

def can_dribble(obs):
    # Can dribble if there is some space ahead
    opponents = get_opponents(obs)
    future_pos = obs.player_position + obs.player_direction * 5
    return get_closest_opponent_distance(future_pos, opponents) > 0.1

def get_movement_action(current_pos, target_pos):
    direction = np.array(target_pos) - np.array(current_pos)
    # The Y-axis in the gfootball environment is inverted (positive is down).
    # We must invert the y-component of the direction vector for np.arctan2
    # to correctly map angles to standard Cartesian coordinates (Y-up).
    angle = np.arctan2(-direction[1], direction[0])

    if -np.pi / 8 <= angle < np.pi / 8:
        return 5  # action_right
    elif np.pi / 8 <= angle < 3 * np.pi / 8:
        return 4  # action_top_right
    elif 3 * np.pi / 8 <= angle < 5 * np.pi / 8:
        return 3  # action_top
    elif 5 * np.pi / 8 <= angle < 7 * np.pi / 8:
        return 2  # action_top_left
    elif 7 * np.pi / 8 <= angle or angle < -7 * np.pi / 8:
        return 1  # action_left
    elif -7 * np.pi / 8 <= angle < -5 * np.pi / 8:
        return 8  # action_bottom_left
    elif -5 * np.pi / 8 <= angle < -3 * np.pi / 8:
        return 7  # action_bottom
    elif -3 * np.pi / 8 <= angle < -np.pi / 8:
        return 6  # action_bottom_right
    else:
        return 0  # action_idle