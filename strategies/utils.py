import numpy as np
import math
from typing import List

# Forward declaration to resolve circular import, assuming PlayerObservationWrapper will be available at runtime.
# A better solution might be to move PlayerObservationWrapper to its own file if it's used across many modules.
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from wrappers import PlayerObservationWrapper

# This function was already in utils.py based on the import in player_roles_6_12.py
def get_movement_action(player_pos, target_pos):
    """Calculates the movement action to get from player_pos to target_pos."""
    player_pos = np.array(player_pos)
    target_pos = np.array(target_pos)
    direction = target_pos - player_pos
    if np.linalg.norm(direction) < 0.03: # Threshold to avoid jittering
        return 0 # ACTION_IDLE

    angle = math.atan2(direction[1], direction[0]) / math.pi * 180
    if angle < 0:
        angle += 360

    if 22.5 <= angle < 67.5: return 2 # ACTION_TOP_LEFT
    if 67.5 <= angle < 112.5: return 3 # ACTION_TOP
    if 112.5 <= angle < 157.5: return 4 # ACTION_TOP_RIGHT
    if 157.5 <= angle < 202.5: return 5 # ACTION_RIGHT
    if 202.5 <= angle < 247.5: return 6 # ACTION_BOTTOM_RIGHT
    if 247.5 <= angle < 292.5: return 7 # ACTION_BOTTOM
    if 292.5 <= angle < 337.5: return 8 # ACTION_BOTTOM_LEFT
    return 1 # ACTION_LEFT

# --- Helper Functions moved from player_roles_6_12.py ---

def get_distance(pos1, pos2):
    return np.linalg.norm(np.array(pos1) - np.array(pos2))

def clamp_position_to_field(position, field_x_limits, field_y_limits):
    """Ensures the target position is within the valid field boundaries."""
    pos = np.array(position)
    pos[0] = np.clip(pos[0], field_x_limits[0], field_x_limits[1])
    pos[1] = np.clip(pos[1], field_y_limits[0], field_y_limits[1])
    return pos

def get_offside_line(obs: 'PlayerObservationWrapper'):
    """Gets the X-coordinate of the second-to-last opponent."""
    opponent_x_positions = sorted([p[0] for p in obs.right_team_positions])
    if len(opponent_x_positions) < 2:
        return 0.0
    return opponent_x_positions[1]

def is_position_offside(obs: 'PlayerObservationWrapper', position):
    """Checks if a given position is offside."""
    x, y = position
    offside_line_x = get_offside_line(obs)
    ball_x = obs.ball_position[0]
    return x > ball_x and x > offside_line_x

def has_space_to_run_into(obs: 'PlayerObservationWrapper'):
    """Checks if there's open space in front of the player to dribble/sprint into."""
    my_pos = np.array(obs.player_position)
    my_dir = np.array(obs.player_direction)

    if np.linalg.norm(my_dir) < 0.01:
        my_dir = np.array([1, 0])

    search_dist = 0.2
    search_angle = np.pi / 4

    for opp_pos_arr in obs.right_team_positions:
        opp_pos = np.array(opp_pos_arr)
        vec_to_opp = opp_pos - my_pos
        dist_to_opp = np.linalg.norm(vec_to_opp)

        if 0 < dist_to_opp < search_dist:
            if np.linalg.norm(my_dir) > 0 and np.linalg.norm(vec_to_opp) > 0:
                dot_product = np.dot(my_dir, vec_to_opp)
                norm_product = np.linalg.norm(my_dir) * np.linalg.norm(vec_to_opp)
                angle_to_opp = np.arccos(np.clip(dot_product / norm_product, -1.0, 1.0))
                if abs(angle_to_opp) < search_angle:
                    return False
    return True

def find_closest_opponent(obs: 'PlayerObservationWrapper'):
    min_dist = 10
    closest_opp = None
    for opp_pos in obs.right_team_positions:
        dist = get_distance(obs.player_position, opp_pos)
        if dist < min_dist:
            min_dist = dist
            closest_opp = opp_pos
    return min_dist, closest_opp

def find_opponent_to_mark(obs: 'PlayerObservationWrapper'):
    """Finds the most dangerous, unmarked opponent in the player's vicinity."""
    my_pos = np.array(obs.player_position)
    best_opponent_to_mark = None
    min_dist = float('inf')

    for opp_pos_arr in obs.right_team_positions:
        opp_pos = np.array(opp_pos_arr)

        if opp_pos[0] > -0.1:
            continue

        is_marked = False
        for mate_obs in obs.wrapper.player_observations:
            if mate_obs.active_player != obs.active_player:
                if get_distance(mate_obs.player_position, opp_pos) < get_distance(my_pos, opp_pos):
                    is_marked = True
                    break

        if not is_marked:
            dist = get_distance(my_pos, opp_pos)
            if dist < min_dist:
                min_dist = dist
                best_opponent_to_mark = opp_pos

    return best_opponent_to_mark

def find_teammate_by_role(obs: 'PlayerObservationWrapper', role: int) -> List['PlayerObservationWrapper']:
    teammates = []
    for player_obs in obs.wrapper.player_observations:
        if player_obs.player_role == role:
            teammates.append(player_obs)
    return teammates

def is_in_penalty_box(pos, side='my'):
    x, y = pos
    if side == 'my': # Left team's box
        return -1 <= x < -0.65 and abs(y) < 0.25
    else: # Right team's box
        return 0.65 < x <= 1 and abs(y) < 0.25

def has_clear_shot_angle(obs: 'PlayerObservationWrapper'):
    goal_pos = np.array([1, 0])
    player_pos = np.array(obs.player_position)
    direction_to_goal = goal_pos - player_pos

    for opp_pos in obs.right_team_positions:
        direction_to_opp = np.array(opp_pos) - player_pos
        if np.dot(direction_to_goal, direction_to_opp) > 0:
            dist_to_goal = np.linalg.norm(direction_to_goal)
            dist_to_opp = np.linalg.norm(direction_to_opp)
            if dist_to_opp < dist_to_goal:
                perp_dist = np.linalg.norm(np.cross(direction_to_goal, direction_to_opp)) / dist_to_goal
                if perp_dist < 0.05:
                    return False
    return True

def should_i_slide(obs: 'PlayerObservationWrapper') -> bool:
    """Decides if a slide tackle is a good action."""
    if obs.ball_owned_team != 1 or obs.distance_to_ball > 0.15:
        return False

    opponent_ball_owner_idx = obs.ball_owned_player
    if opponent_ball_owner_idx >= len(obs.right_team_positions):
        return False

    opponent_pos = obs.right_team_positions[opponent_ball_owner_idx]

    distance_to_carrier = get_distance(obs.player_position, opponent_pos)
    if distance_to_carrier < 0.08:
        return True

    return False

def apply_spacing_adjustment(obs: 'PlayerObservationWrapper', target_pos):
    """Adjusts target position to move away from crowded teammates."""
    adjusted_pos = np.array(target_pos)
    separation_radius = 0.08
    repulsion_strength = 0.04

    for mate_obs in obs.wrapper.player_observations:
        if mate_obs.active_player == obs.active_player:
            continue

        dist = get_distance(obs.player_position, mate_obs.player_position)
        if dist < separation_radius:
            away_vec = np.array(obs.player_position) - np.array(mate_obs.player_position)
            if np.linalg.norm(away_vec) > 0:
                 adjusted_pos += (away_vec / np.linalg.norm(away_vec)) * repulsion_strength

    return adjusted_pos 

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

# Field dimensions and coordinates
FIELD_X_MIN, FIELD_X_MAX = -1.0, 1.0
FIELD_Y_MIN, FIELD_Y_MAX = -0.42, 0.42
GOAL_Y_MIN, GOAL_Y_MAX = -0.044, 0.044
OWN_PENALTY_BOX_X_MAX = -0.835
OPPONENT_PENALTY_BOX_X_MIN = 0.835
PENALTY_BOX_Y_MIN, PENALTY_BOX_Y_MAX = -0.25, 0.25
ATTACKING_THIRD_X = 1.0 / 3.0
DEFENSIVE_THIRD_X = -1.0 / 3.0
PENALTY_AREA_X = 0.65
PENALTY_AREA_Y = 0.25

# Game mode constants
GAME_MODE_NORMAL = 0
GAME_MODE_KICKOFF = 1
GAME_MODE_GOALKICK = 2
GAME_MODE_FREEKICK = 3
GAME_MODE_CORNER = 4
GAME_MODE_THROWIN = 5
GAME_MODE_PENALTY = 6

# Pass distance thresholds
SHORT_PASS_DISTANCE_MAX = 0.3 # Corresponds to roughly 30 yards

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


# --- General Helper Functions ---

def compute_distance(pos1, pos2):
    """Computes euclidean distance between two points."""
    return np.linalg.norm(np.array(pos1) - np.array(pos2))


def get_closest_opponent(player_pos, opponent_positions):
    """Finds the closest opponent to the player."""
    min_dist = float('inf')
    closest_opp_pos = None
    for opp_pos in opponent_positions:
        dist = compute_distance(player_pos, opp_pos)
        if dist < min_dist:
            min_dist = dist
            closest_opp_pos = opp_pos
    return closest_opp_pos, min_dist


def get_pressure_level(player_pos, opponent_positions, high_pressure_threshold=0.1, medium_pressure_threshold=0.2):
    """Determines the pressure level based on the distance to the nearest opponent."""
    _, min_dist = get_closest_opponent(player_pos, opponent_positions)
    if min_dist < high_pressure_threshold:
        return '高'
    if min_dist < medium_pressure_threshold:
        return '中'
    return '低'


def is_in_attacking_third(player_pos):
    return player_pos[0] > ATTACKING_THIRD_X


def is_in_defensive_third(player_pos):
    return player_pos[0] < DEFENSIVE_THIRD_X


def is_in_penalty_area(player_pos):
    return player_pos[0] > PENALTY_AREA_X and abs(player_pos[1]) < PENALTY_AREA_Y


def is_on_flank(player_pos):
    return abs(player_pos[1]) > 0.3


def has_good_shooting_angle(player_pos):
    """Checks if the player is in a good position to shoot."""
    # Simplified: consider it a good angle if inside the penalty area or in a central position facing the goal
    return is_in_penalty_area(player_pos) or (player_pos[0] > 0.5 and abs(player_pos[1]) < 0.3)


# --- Teammate-related Helper Functions ---

def find_teammates_by_role(obs, roles):
    """Finds all teammates matching the given role(s)."""
    if not isinstance(roles, list):
        roles = [roles]
    teammates = []
    for i, role in enumerate(obs.observation['left_team_roles']):
        if role in roles and i != obs.active_player:
            teammates.append({
                'index': i,
                'position': obs.left_team_positions[i],
                'role': role,
                'direction': obs.left_team_directions[i]
            })
    return teammates


def find_closest_teammate(obs, roles=None):
    """Finds the closest teammate, optionally filtering by role."""
    min_dist = float('inf')
    closest_teammate = None
    
    for i, teammate_pos in enumerate(obs.left_team_positions):
        if i == obs.active_player:
            continue
        
        if roles:
            if obs.observation['left_team_roles'][i] not in roles:
                continue
        
        dist = compute_distance(obs.player_position, teammate_pos)
        if dist < min_dist:
            min_dist = dist
            closest_teammate = {
                'index': i,
                'position': teammate_pos,
                'role': obs.observation['left_team_roles'][i],
                'direction': obs.left_team_directions[i]
            }
    return closest_teammate


def find_open_teammates(obs, open_threshold=0.15):
    """Finds teammates who are not closely marked by opponents."""
    open_teammates = []
    for i, teammate_pos in enumerate(obs.left_team_positions):
        if i == obs.active_player:
            continue
        
        _, dist_to_closest_opp = get_closest_opponent(teammate_pos, obs.right_team_positions)
        if dist_to_closest_opp > open_threshold:
            open_teammates.append({
                'index': i,
                'position': teammate_pos,
                'role': obs.observation['left_team_roles'][i],
                'direction': obs.left_team_directions[i]
            })
    return open_teammates

# --- Movement Helper Functions ---

def direction_to_action(player_pos, target_pos):
    """Converts a vector from player to target into a directional move action."""
    delta = np.array(target_pos) - np.array(player_pos)
    # Avoid division by zero if already at target
    if np.linalg.norm(delta) < 0.01:
        return ACTION_IDLE
        
    angle = np.arctan2(delta[1], delta[0]) * 180 / np.pi

    if -22.5 <= angle < 22.5: return ACTION_RIGHT
    if 22.5 <= angle < 67.5: return ACTION_BOTTOM_RIGHT
    if 67.5 <= angle < 112.5: return ACTION_BOTTOM
    if 112.5 <= angle < 157.5: return ACTION_BOTTOM_LEFT
    if 157.5 <= angle or angle < -157.5: return ACTION_LEFT
    if -157.5 <= angle < -112.5: return ACTION_TOP_LEFT
    if -112.5 <= angle < -67.5: return ACTION_TOP
    if -67.5 <= angle < -22.5: return ACTION_TOP_RIGHT
    
    return ACTION_IDLE 

# --- Helper Functions ---

def get_active_player_role(obs):
    return obs.player_role

def get_active_player_pos(obs):
    return obs.player_position

def is_in_attacking_third(player_pos):
    return player_pos[0] > FIELD_X_MAX / 3.0

def is_in_defensive_third(player_pos):
    return player_pos[0] < FIELD_X_MIN / 3.0

def is_in_penalty_area(player_pos):
    return player_pos[0] > PENALTY_AREA_X and abs(player_pos[1]) < PENALTY_AREA_Y

def is_on_flank(player_pos):
    return abs(player_pos[1]) > 0.3

def has_good_shooting_angle(player_pos):
    """Checks if the player is in a good position to shoot."""
    # Simplified: consider it a good angle if inside the penalty area or in a central position facing the goal
    return is_in_penalty_area(player_pos) or (player_pos[0] > 0.5 and abs(player_pos[1]) < 0.3)

def is_in_own_penalty_box(player_pos):
    return player_pos[0] < OWN_PENALTY_BOX_X_MAX and PENALTY_BOX_Y_MIN < player_pos[1] < PENALTY_BOX_Y_MAX

def is_in_opponent_penalty_box(player_pos):
    """Checks if a position is inside the opponent's penalty box."""
    return player_pos[0] > OPPONENT_PENALTY_BOX_X_MIN and abs(player_pos[1]) < PENALTY_BOX_Y_MAX

def get_pressure_level(obs, search_radius=0.2, high_pressure_dist=0.07):
    """
    Determines the pressure level on the active player based on the number 
    of opponents nearby and the distance to the closest one.
    """
    player_pos = obs.player_position
    opponent_positions = obs.right_team_positions
    
    opponents_nearby = []
    min_dist = float('inf')

    if opponent_positions is None or len(opponent_positions) == 0:
        return '低'

    for opp_pos in opponent_positions:
        dist = np.linalg.norm(np.array(player_pos) - np.array(opp_pos))
        if dist < search_radius:
            opponents_nearby.append(opp_pos)
        if dist < min_dist:
            min_dist = dist
            
    num_opponents_nearby = len(opponents_nearby)

    if num_opponents_nearby >= 2 or min_dist < high_pressure_dist:
        return '高'
    elif num_opponents_nearby == 1:
        return '中'
    else:
        return '低'

def has_space_to_dribble(obs, min_dist=0.1):
    if not obs.distances_to_opponents:
        return True
    return min(obs.distances_to_opponents) > min_dist

def is_pass_interceptable(obs, target_pos, intercept_margin=0.03):
    """
    Checks if a straight line pass to target_pos is likely to be intercepted.
    """
    passer_pos = np.array(obs.player_position)
    target_pos = np.array(target_pos)
    pass_vector = target_pos - passer_pos
    pass_length = np.linalg.norm(pass_vector)
    
    if pass_length == 0:
        return False

    pass_unit_vector = pass_vector / pass_length

    for opp_pos in obs.right_team_positions:
        opp_pos = np.array(opp_pos)
        vector_to_opp = opp_pos - passer_pos
        
        # Project opponent's position onto the pass vector
        projection = np.dot(vector_to_opp, pass_unit_vector)
        
        # Check if the opponent is between the passer and receiver
        if 0 < projection < pass_length:
            # Calculate the perpendicular distance of the opponent from the pass line
            dist_to_line = np.linalg.norm(vector_to_opp - projection * pass_unit_vector)
            if dist_to_line < intercept_margin:
                return True # Pass is likely to be intercepted
    return False

def count_opponents_in_our_half(obs):
    """Counts how many opponent players are in our half of the field."""
    return sum(1 for pos in obs.right_team_positions if pos[0] < 0)

def dribble_towards_opponent_goal(obs):
    """Returns a directional action towards the opponent goal, and may activate sprint."""
    if obs.sticky_actions[STICKY_SPRINT] == 0 and has_space_to_dribble(obs, min_dist=0.2):
         return ACTION_SPRINT
    
    opponent_goal_pos = [FIELD_X_MAX, 0]
    return get_direction_action(obs.player_position, opponent_goal_pos)

def get_safe_dribble_action(obs, boundary_margin=0.05):
    """Checks if the player is near a boundary and returns an action to turn away."""
    player_pos = obs.player_position
    
    # Near top sideline (y = -0.42)
    if player_pos[1] < FIELD_Y_MIN + boundary_margin:
        return ACTION_BOTTOM # Move away from top edge
        
    # Near bottom sideline (y = 0.42)
    if player_pos[1] > FIELD_Y_MAX - boundary_margin:
        return ACTION_TOP # Move away from bottom edge

    # Near own goal line (x = -1.0)
    if player_pos[0] < FIELD_X_MIN + boundary_margin and obs.player_role != ROLE_GK:
        return ACTION_RIGHT # Move away from own goal line

    # Near opponent goal line (byline)
    if player_pos[0] > FIELD_X_MAX - boundary_margin:
        if abs(player_pos[1]) > GOAL_Y_MAX: # If on the byline past the goal
             # Turn towards the goal to prepare for a pass/cross
             if player_pos[1] > 0: # bottom side of field
                 return ACTION_TOP_LEFT
             else: # top side of field
                 return ACTION_BOTTOM_LEFT

    return None # No immediate danger

def is_teammate_offside(obs, teammate_index):
    teammate_pos = obs.left_team_positions[teammate_index]
    
    # Offside rule only applies in the opponent's half.
    if teammate_pos[0] < 0:
        return False

    # Find the x-coordinate of the second to last opponent.
    opponent_x_positions = sorted([p[0] for p in obs.right_team_positions])
    # The keeper is usually last, so the second to last is opponent_x_positions[-2]
    # But to be safe, we check if there are at least two opponents.
    if len(opponent_x_positions) < 2:
        return False
    second_last_opponent_x = opponent_x_positions[-2]

    ball_pos = obs.ball_position
    
    # A player is offside if they are in front of the ball AND in front of the second-to-last defender.
    if teammate_pos[0] > ball_pos[0] and teammate_pos[0] > second_last_opponent_x:
        return True
    
    return False

def find_open_teammate(obs, role_list=None, min_dist_from_opponent=0.1, check_offside=False):
    best_teammate = None
    max_dist_to_opponent = -1

    for i, teammate_pos in enumerate(obs.left_team_positions):
        if i == obs.active_player:
            continue
        
        if check_offside and is_teammate_offside(obs, i):
            continue
            
        if is_pass_interceptable(obs, teammate_pos):
            continue

        teammate_role = obs.observation['left_team_roles'][i]
        if role_list and teammate_role not in role_list:
            continue

        # Find the closest opponent to this teammate
        min_opponent_dist = float('inf')
        for opponent_pos in obs.right_team_positions:
            dist = np.linalg.norm(np.array(teammate_pos) - np.array(opponent_pos))
            if dist < min_opponent_dist:
                min_opponent_dist = dist
        
        # Check if the teammate is open and better than the last one found
        if min_opponent_dist >= min_dist_from_opponent and min_opponent_dist > max_dist_to_opponent:
            max_dist_to_opponent = min_opponent_dist
            best_teammate = i

    return best_teammate

def get_direction_action(player_pos, target_pos):
    dx = target_pos[0] - player_pos[0]
    dy = target_pos[1] - player_pos[1]
    
    if abs(dx) < 0.01 and abs(dy) < 0.01:
        return ACTION_IDLE

    angle = math.atan2(dy, dx)
    
    # Normalize angle to [0, 2*pi]
    if angle < 0:
        angle += 2 * math.pi

    # Map angle to one of 8 directions
    if angle >= 15 * math.pi / 8 or angle < math.pi / 8:
        return ACTION_RIGHT
    if angle >= math.pi / 8 and angle < 3 * math.pi / 8:
        return ACTION_BOTTOM_RIGHT
    if angle >= 3 * math.pi / 8 and angle < 5 * math.pi / 8:
        return ACTION_BOTTOM
    if angle >= 5 * math.pi / 8 and angle < 7 * math.pi / 8:
        return ACTION_BOTTOM_LEFT
    if angle >= 7 * math.pi / 8 and angle < 9 * math.pi / 8:
        return ACTION_LEFT
    if angle >= 9 * math.pi / 8 and angle < 11 * math.pi / 8:
        return ACTION_TOP_LEFT
    if angle >= 11 * math.pi / 8 and angle < 13 * math.pi / 8:
        return ACTION_TOP
    if angle >= 13 * math.pi / 8 and angle < 15 * math.pi / 8:
        return ACTION_TOP_RIGHT

    return ACTION_IDLE

def get_defensive_line_height(obs):
    """Returns the average X position of the defenders."""
    defenders_x = [
        pos[0] for i, pos in enumerate(obs.left_team_positions)
        if obs.observation['left_team_roles'][i] in [ROLE_CB, ROLE_LB, ROLE_RB]
    ]
    return np.mean(defenders_x) if defenders_x else FIELD_X_MIN / 2

def find_teammate_with_role(obs, role):
    for i, r in enumerate(obs.observation['left_team_roles']):
        if r == role and i != obs.active_player:
            return i
    return None

def get_second_last_opponent_x(obs):
    """Gets the X-coordinate of the second-to-last opponent, crucial for offside checks."""
    opponent_x_positions = sorted([p[0] for p in obs.right_team_positions if p[0] > obs.ball_position[0]], reverse=True)
    if len(opponent_x_positions) < 2:
        return None
    return opponent_x_positions[1]

def get_opponent_ball_carrier_info(obs):
    """
    Finds the position and direction of the opponent player carrying the ball.
    Returns (position, direction) or (None, None) if no opponent has the ball.
    """
    if obs.is_ball_owned_by_team(team=1):
        carrier_idx = obs.ball_owned_player
        if 0 <= carrier_idx < len(obs.right_team_positions):
            carrier_pos = obs.right_team_positions[carrier_idx]
            carrier_dir = obs.observation['right_team_direction'][carrier_idx]
            return carrier_pos, carrier_dir
    return None, None

def predict_future_position(position, direction, steps=8, speed_factor=0.01):
    """
    Predicts the future position of an object given its current position and direction.
    """
    if position is None or direction is None:
        return None
    return np.array(position) + np.array(direction) * steps * speed_factor

def is_position_offside(obs, position):
    """
    Checks if a given position [x, y] is in an offside position.
    """
    if position[0] <= 0:
        return False
    
    ball_pos = obs.ball_position
    # It is not an offence to be in an offside position if the player is behind the ball.
    if position[0] < ball_pos[0]:
        return False
        
    second_last_opponent_x = get_second_last_opponent_x(obs)
    if second_last_opponent_x is None:
        return False # Not offside if less than 2 opponents

    return position[0] > second_last_opponent_x 

# Defines the general search area for each role when looking for open space.
# (x_min, x_max, y_min, y_max)
ROLE_SEARCH_AREAS = {
    ROLE_CB: (-0.8, 0.0, -0.3, 0.3),
    ROLE_LB: (-0.7, 0.8, 0.2, 0.42),
    ROLE_RB: (-0.7, 0.8, -0.42, -0.2),
    ROLE_DM: (-0.6, 0.5, -0.4, 0.4),
    ROLE_CM: (-0.3, 0.8, -0.4, 0.4),
    ROLE_LM: (-0.2, 0.9, 0.1, 0.42),
    ROLE_RM: (-0.2, 0.9, -0.42, -0.1),
    ROLE_AM: (0.0, 0.9, -0.3, 0.3),
    ROLE_CF: (0.3, 1.0, -0.3, 0.3),
}

def find_best_open_space(obs):
    """
    Finds the best empty space for a player to run into, creating separation from teammates.
    This helps to spread out the formation during an attack.
    """
    player_pos = obs.player_position
    player_role = obs.player_role
    active_player_id = obs.observation['active']
    
    # Teammates, excluding the active player
    teammate_positions = [pos for i, pos in enumerate(obs.left_team_positions) if i != active_player_id]
    opponent_positions = obs.right_team_positions
    
    search_area = ROLE_SEARCH_AREAS.get(player_role)
    if not search_area:
        return None # No area defined for this role

    x_min, x_max, y_min, y_max = search_area
    
    # Generate a grid of candidate points to evaluate
    x_points = np.linspace(x_min, x_max, 10)
    y_points = np.linspace(y_min, y_max, 5)
    
    best_pos = None
    max_score = -np.inf
    
    for x in x_points:
        for y in y_points:
            candidate_pos = np.array([x, y])

            if is_position_offside(obs, candidate_pos):
                continue
            
            # Calculate minimum distance to any teammate
            if teammate_positions:
                min_dist_tm = min(np.linalg.norm(candidate_pos - tm) for tm in teammate_positions)
            else:
                min_dist_tm = 1.0 # Max distance

            # Calculate minimum distance to any opponent
            if opponent_positions.size > 0:
                min_dist_op = min(np.linalg.norm(candidate_pos - op) for op in opponent_positions)
            else:
                min_dist_op = 1.0 # Max distance
            
            # Scoring: we want to maximize distance to teammates and opponents, and also move forward.
            # Weight distance to teammates higher to ensure we spread out.
            score = 1.5 * min_dist_tm + 0.8 * min_dist_op + 0.5 * x
            
            if score > max_score:
                max_score = score
                best_pos = candidate_pos
                
    return best_pos 