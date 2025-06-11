#player_roles_6_11.py

import math
import numpy as np

# Action constants from observation.md and player_roles.py
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

# Role constants from observation.md
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

# Indices for sticky actions from player_roles.py
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

# --- Tactical Helper Functions (Optimized Logic) ---

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

def is_opponent_pressing_heavily(obs, role_id, threshold=0.2):
    """Tactic: 评估对方前锋压迫强度."""
    my_pos = obs.player_position
    for i, opp_pos in enumerate(obs.right_team_positions):
        # Check if opponent is a forward and close by
        if obs.observation['right_team_roles'][i] == role_id and np.linalg.norm(np.array(my_pos) - np.array(opp_pos)) < threshold:
            return True
    return False

def find_unstressed_teammate_in_defense(obs):
    """Tactic: 寻找未受压迫的后卫进行短传."""
    my_pos = obs.player_position
    for i, teammate_pos in enumerate(obs.left_team_positions):
        role = obs.observation['left_team_roles'][i]
        if role in [ROLE_CB, ROLE_LB, ROLE_RB]:
            # Check if this defender is far from any opponent
            closest_opp_dist = min([np.linalg.norm(np.array(teammate_pos) - np.array(opp_pos)) for opp_pos in obs.right_team_positions])
            if closest_opp_dist > 0.15: # Generous space
                return teammate_pos
    return None

def get_defensive_line_position(obs):
    """Tactic: 协同整条防线根据球的位置前移或后撤，保持紧凑."""
    my_pos = obs.player_position
    ball_pos = obs.ball_position
    # A simple dynamic defensive line that moves with the ball
    target_x = max(ball_pos[0] - 0.4, -0.8)
    # Maintain horizontal position unless threatened
    return [target_x, my_pos[1]]

def block_passing_lane_to_opponent_striker(obs):
    """Tactic: 首要任务不是盯人，而是切断给对方中锋的传球线路."""
    my_pos = obs.player_position
    ball_pos = obs.ball_position
    strikers = [obs.right_team_positions[i] for i, role in enumerate(obs.observation['right_team_roles']) if role == ROLE_CF]
    if strikers:
        # Position between the ball and the main striker
        target_pos = (np.array(ball_pos) + np.array(strikers[0])) / 2.0
        return target_pos
    # If no striker, hold the line
    return get_defensive_line_position(obs)

def is_ball_on_opposite_flank(my_pos, ball_pos):
    """Tactic: 防守时根据球的位置内收."""
    return my_pos[1] * ball_pos[1] < -0.01 # Ball is on the other side

def tuck_in_defensive_position(my_pos):
    """Tactic: 球在右路时，左后卫适当内收，保护中路."""
    # Move towards the center to cover space
    return [-0.7, my_pos[1] * 0.5]

def is_pressing_trigger_active(obs, threshold=0.1):
    """Tactic: 判断压迫时机."""
    if obs.ball_owned_team == 1:
        owner_idx = obs.ball_owned_player
        owner_dir = obs.right_team_directions[owner_idx]
        # Trigger if opponent is facing their own goal (a bad touch)
        if owner_dir[0] < -threshold:
            return True
    return False

def block_central_passing_lanes(obs):
    """Tactic: 保持位置，封锁向前的传球线路."""
    # Position between the ball and our goal's center
    target_pos = (np.array(obs.ball_position) + np.array([-1, 0])) / 2.0
    target_pos[0] = max(target_pos[0], -0.5) # Don't drop too deep
    return target_pos

def find_pocket_of_space_between_the_lines(obs):
    """Tactic: 主动跑入对方中场和后卫线之间的空当."""
    opponent_defenders_x = [p[0] for i,p in enumerate(obs.right_team_positions) if obs.observation['right_team_roles'][i] in [ROLE_CB, ROLE_LB, ROLE_RB]]
    if opponent_defenders_x:
        defensive_line_x = min(opponent_defenders_x)
        # Target a position just in front of their defense
        return [defensive_line_x - 0.1, np.clip(obs.ball_position[1], -0.2, 0.2)]
    return [0.5, obs.ball_position[1]] # Default attacking spot

def run_into_channel(obs):
    """Tactic: 斜向插入对方中后卫和边后卫之间的"肋部"."""
    my_pos = obs.player_position
    # Simplified: a diagonal run towards goal from a wide position
    target_y_direction = -1 if my_pos[1] > 0 else 1
    target_pos = [0.8, my_pos[1] + target_y_direction * 0.2]
    return target_pos

# --- Optimized Role Implementations ---

def goalkeeper_actions(obs):
    my_pos = obs.player_position
    if obs.is_ball_owned_by_player():
        if is_opponent_pressing_heavily(obs, ROLE_CF):
            return ACTION_LONG_PASS
        else:
            safe_teammate = find_unstressed_teammate_in_defense(obs)
            if safe_teammate is not None:
                return ACTION_SHORT_PASS
            else:
                return ACTION_HIGH_PASS
    elif obs.is_ball_owned_by_team(0):
        # Act as a safe passing option
        return move_towards(my_pos, [-0.85, np.clip(obs.ball_position[1], -0.3, 0.3)])
    elif obs.is_ball_owned_by_team(1):
        # Block the angle
        target_pos = (np.array(obs.ball_position) + np.array([-1, 0])) / 2.0
        target_pos[0] = -0.95
        return move_towards(my_pos, target_pos)
    else: # Ball is free
        # Only claim if it's safe and inside the box
        in_box = obs.ball_position[0] < -0.85 and abs(obs.ball_position[1]) < 0.3
        if in_box and obs.distance_to_ball < 0.15:
            return move_towards(my_pos, obs.ball_position)
        return move_towards(my_pos, [-0.95, 0])

def centre_back_actions(obs):
    my_pos = obs.player_position
    if obs.is_ball_owned_by_player():
        # Tactic: Find DM for a line-breaking pass
        dm_player = [p for i,p in enumerate(obs.left_team_positions) if obs.observation['left_team_roles'][i] == ROLE_DM]
        if dm_player:
            return ACTION_SHORT_PASS
        return ACTION_LONG_PASS
    elif obs.is_ball_owned_by_team(0):
        # Tactic: Maintain compact defensive line
        return move_towards(my_pos, get_defensive_line_position(obs))
    elif obs.is_ball_owned_by_team(1):
        # Tactic: Block passing lane to striker
        return move_towards(my_pos, block_passing_lane_to_opponent_striker(obs))
    else:
        # Only go for the ball if in a dangerous zone and closest
        if obs.ball_position[0] < -0.4 and obs.distance_to_ball < 0.2:
            return move_towards(my_pos, obs.ball_position)
        return move_towards(my_pos, get_defensive_line_position(obs))

def left_back_actions(obs):
    my_pos = obs.player_position
    ball_pos = obs.ball_position
    if obs.is_ball_owned_by_player():
        # Tactic: Pass to a central player
        return ACTION_SHORT_PASS
    elif obs.is_ball_owned_by_team(0):
        # Tactic: Make an overlapping run on the flank
        if ball_pos[0] > my_pos[0] and ball_pos[1] > 0:
            if not obs.sticky_actions[STICKY_SPRINT]: return ACTION_SPRINT
            return move_towards(my_pos, [my_pos[0] + 0.3, my_pos[1]])
        return move_towards(my_pos, [ball_pos[0] - 0.2, 0.3])
    elif obs.is_ball_owned_by_team(1):
        if is_ball_on_opposite_flank(my_pos, ball_pos):
            # Tactic: Tuck in to maintain compactness
            return move_towards(my_pos, tuck_in_defensive_position(my_pos))
        else:
            # Press opponent on the flank
            if not obs.sticky_actions[STICKY_SPRINT]: return ACTION_SPRINT
            return move_towards(my_pos, [-0.6, 0.3])
    else:
        # Get ball if on my flank
        if ball_pos[1] > 0:
            return move_towards(my_pos, ball_pos)
        return move_towards(my_pos, [-0.6, 0.3])

def right_back_actions(obs):
    # Mirrored logic of the left back
    my_pos = obs.player_position
    ball_pos = obs.ball_position
    if obs.is_ball_owned_by_player():
        return ACTION_SHORT_PASS
    elif obs.is_ball_owned_by_team(0):
        if ball_pos[0] > my_pos[0] and ball_pos[1] < 0:
            if not obs.sticky_actions[STICKY_SPRINT]: return ACTION_SPRINT
            return move_towards(my_pos, [my_pos[0] + 0.3, my_pos[1]])
        return move_towards(my_pos, [ball_pos[0] - 0.2, -0.3])
    elif obs.is_ball_owned_by_team(1):
        if is_ball_on_opposite_flank(my_pos, ball_pos):
            return move_towards(my_pos, tuck_in_defensive_position(my_pos))
        else:
            if not obs.sticky_actions[STICKY_SPRINT]: return ACTION_SPRINT
            return move_towards(my_pos, [-0.6, -0.3])
    else:
        if ball_pos[1] < 0:
            return move_towards(my_pos, ball_pos)
        return move_towards(my_pos, [-0.6, -0.3])

def defence_midfielder_actions(obs):
    my_pos = obs.player_position
    ball_pos = obs.ball_position
    if obs.is_ball_owned_by_player():
        # Tactic: Act as pivot, pass forward
        return ACTION_SHORT_PASS
    elif obs.is_ball_owned_by_team(0):
        # Tactic: Provide a safe option behind the ball
        return move_towards(my_pos, [ball_pos[0] - 0.15, ball_pos[1]])
    elif obs.is_ball_owned_by_team(1):
        if is_pressing_trigger_active(obs):
            if not obs.sticky_actions[STICKY_SPRINT]: return ACTION_SPRINT
            return move_towards(my_pos, ball_pos)
        else:
            # Tactic: Screen the defense, block lanes
            return move_towards(my_pos, block_central_passing_lanes(obs))
    else:
        return move_towards(my_pos, ball_pos)

def attack_midfielder_actions(obs):
    my_pos = obs.player_position
    if obs.is_ball_owned_by_player():
        # Tactic: Shoot if in a good position, else find forward
        if my_pos[0] > 0.6 and abs(my_pos[1]) < 0.3:
            return ACTION_SHOT
        return ACTION_SHORT_PASS
    elif obs.is_ball_owned_by_team(0):
        # Tactic: Find pockets of space between the lines
        return move_towards(my_pos, find_pocket_of_space_between_the_lines(obs))
    elif obs.is_ball_owned_by_team(1):
        # Tactic: Initial press on opponent's midfielder
        if not obs.sticky_actions[STICKY_SPRINT]: return ACTION_SPRINT
        return move_towards(my_pos, obs.ball_position)
    else:
        return move_towards(my_pos, obs.ball_position)

def central_forward_actions(obs):
    my_pos = obs.player_position
    if obs.is_ball_owned_by_player():
        if my_pos[0] > 0.7 and abs(my_pos[1]) < 0.2:
            return ACTION_SHOT
        else:
            # Tactic: Small dribble to create better angle
            if not obs.sticky_actions[STICKY_DRIBBLE]: return ACTION_DRIBBLE
            return move_towards(my_pos, [1.0, np.clip(my_pos[1], -0.1, 0.1)])
    elif obs.is_ball_owned_by_team(0):
        # Tactic: Make diagonal runs into channels
        return move_towards(my_pos, run_into_channel(obs))
    elif obs.is_ball_owned_by_team(1):
        # Tactic: Press the defender, but block the easy pass
        if obs.ball_owned_player != -1:
            owner_pos = obs.right_team_positions[obs.ball_owned_player]
            # Move to a spot between the owner and their likely pass target (goalie)
            target_pos = (np.array(owner_pos) + np.array([-1, 0])) / 2.0
            return move_towards(my_pos, target_pos)
        return move_towards(my_pos, [0.4, 0])
    else:
        # Only chase ball in attacking half
        if obs.ball_position[0] > 0:
            return move_towards(my_pos, obs.ball_position)
        return move_towards(my_pos, [0.5, 0])

# Assign functions to roles, assuming CM and LM/RM use AM logic for simplicity
player_role_to_action = {
    ROLE_GK: goalkeeper_actions,
    ROLE_CB: centre_back_actions,
    ROLE_LB: left_back_actions,
    ROLE_RB: right_back_actions,
    ROLE_DM: defence_midfielder_actions,
    ROLE_CM: defence_midfielder_actions, # Using AM logic for more attacking CM
    ROLE_LM: attack_midfielder_actions, # Using AM logic for more attacking Wingers
    ROLE_RM: attack_midfielder_actions,
    ROLE_AM: attack_midfielder_actions,
    ROLE_CF: central_forward_actions,
}

