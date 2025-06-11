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
    my_pos = get_my_pos(obs)
    ball_pos = obs.ball_position
    center_of_goal_area = [-0.95, 0]
    edge_of_penalty_box = [-0.8, 0]

    game_mode = obs.game_mode
    if game_mode == GAME_MODE_KICKOFF:
        return move_towards(my_pos, center_of_goal_area)
    if game_mode in [GAME_MODE_CORNER, GAME_MODE_FREEKICK, GAME_MODE_PENALTY]:
        target_y = np.clip(ball_pos[1], -0.2, 0.2)
        return move_towards(my_pos, [-1.0, target_y])

    if obs.ball_owned_team == 0 and obs.ball_owned_player == obs.active_player:
        teammate_idx = find_open_teammate(obs, 0.2)
        if teammate_idx != -1:
            teammate_pos = obs.left_team_positions[teammate_idx]
            if np.linalg.norm(np.array(my_pos) - np.array(teammate_pos)) > 0.4:
                return ACTION_HIGH_PASS
            else:
                return ACTION_SHORT_PASS
        return ACTION_LONG_PASS

    elif obs.ball_owned_team == 0:
        return move_towards(my_pos, edge_of_penalty_box)

    elif obs.ball_owned_team == 1:
        if np.linalg.norm(np.array(my_pos) - np.array(ball_pos)) > 0.4:
            return move_towards(my_pos, center_of_goal_area)
        else:
            target_pos = (np.array(ball_pos) + np.array([-1, 0])) / 2.0
            target_pos[0] = -0.95
            return move_towards(my_pos, target_pos)

    else:
        in_box = ball_pos[0] < -0.85 and abs(ball_pos[1]) < 0.3
        if in_box and np.linalg.norm(np.array(my_pos) - np.array(ball_pos)) < 0.15:
            return move_towards(my_pos, ball_pos)
        else:
            return move_towards(my_pos, center_of_goal_area)
            
    return ACTION_IDLE

def centre_back_actions(obs):
    my_pos = get_my_pos(obs)
    ball_pos = obs.ball_position
    my_defensive_position = [-0.7, 0.0]

    game_mode = obs.game_mode
    if game_mode == GAME_MODE_KICKOFF:
        return move_towards(my_pos, [-0.5, 0.0])
    if game_mode == GAME_MODE_CORNER:
        if obs.ball_position[0] > 0:
            return move_towards(my_pos, [0.0, 0.0])
        else:
            opp_in_box = [opp for opp in obs.right_team_positions if opp[0] < -0.7 and abs(opp[1]) < 0.4]
            if opp_in_box:
                closest_opp = min(opp_in_box, key=lambda p: np.linalg.norm(np.array(my_pos) - np.array(p)))
                return move_towards(my_pos, closest_opp)
            return move_towards(my_pos, [-0.8, 0])

    if obs.ball_owned_team == 0 and obs.ball_owned_player == obs.active_player:
        midfielder_indices = [i for i, role in enumerate(obs.observation['left_team_roles']) if role in [5, 6, 7, 8]]
        if midfielder_indices:
            return ACTION_SHORT_PASS
        else:
            return ACTION_LONG_PASS
            
    elif obs.ball_owned_team == 0:
        target_x = min(my_defensive_position[0], ball_pos[0] - 0.1)
        return move_towards(my_pos, [target_x, my_pos[1]])
        
    elif obs.ball_owned_team == 1:
        if np.linalg.norm(np.array(my_pos) - np.array(ball_pos)) < 0.1:
            return ACTION_SLIDING
        else:
            strikers = [obs.right_team_positions[i] for i, role in enumerate(obs.observation['right_team_roles']) if role == 9]
            if strikers:
                target_pos = (np.array(strikers[0]) + np.array([-1,0])) / 2.0
                return move_towards(my_pos, target_pos)
            else:
                return move_towards(my_pos, my_defensive_position)

    else:
        if ball_pos[0] < 0:
            return move_towards(my_pos, ball_pos)
        else:
            return move_towards(my_pos, my_defensive_position)
            
    return ACTION_IDLE

def left_back_actions(obs):
    my_pos = get_my_pos(obs)
    ball_pos = obs.ball_position
    my_flank_y = 0.25 # Assume left back operates on y > 0
    my_defensive_flank_position = [-0.6, my_flank_y]
    
    if obs.ball_owned_team == 0 and obs.ball_owned_player == obs.active_player:
        teammates_on_flank = [i for i, pos in enumerate(obs.left_team_positions) if i != obs.active_player and pos[1] > 0]
        if teammates_on_flank:
             return ACTION_SHORT_PASS
        else:
             if not obs.sticky_actions[STICKY_DRIBBLE]:
                 return ACTION_DRIBBLE
             return move_towards(my_pos, [my_pos[0] + 0.2, my_pos[1]])

    elif obs.ball_owned_team == 0:
        if ball_pos[0] > my_pos[0] and my_pos[1] * ball_pos[1] > 0:
            if not obs.sticky_actions[STICKY_SPRINT]: return ACTION_SPRINT
            return move_towards(my_pos, [my_pos[0] + 0.3, my_pos[1]])
        else:
            return move_towards(my_pos, [ball_pos[0] - 0.1, my_flank_y])
            
    elif obs.ball_owned_team == 1:
        if not obs.sticky_actions[STICKY_SPRINT]: return ACTION_SPRINT
        return move_towards(my_pos, my_defensive_flank_position)
        
    else: # free ball
        if ball_pos[1] > 0: # Ball on my flank
            return move_towards(my_pos, ball_pos)
        else:
            return move_towards(my_pos, my_defensive_flank_position)
            
    return ACTION_IDLE

def right_back_actions(obs):
    my_pos = get_my_pos(obs)
    ball_pos = obs.ball_position
    my_flank_y = -0.25 # Assume right back operates on y < 0
    my_defensive_flank_position = [-0.6, my_flank_y]
    
    if obs.ball_owned_team == 0 and obs.ball_owned_player == obs.active_player:
        teammates_on_flank = [i for i, pos in enumerate(obs.left_team_positions) if i != obs.active_player and pos[1] < 0]
        if teammates_on_flank:
             return ACTION_SHORT_PASS
        else:
             if not obs.sticky_actions[STICKY_DRIBBLE]:
                 return ACTION_DRIBBLE
             return move_towards(my_pos, [my_pos[0] + 0.2, my_pos[1]])

    elif obs.ball_owned_team == 0:
        if ball_pos[0] > my_pos[0] and my_pos[1] * ball_pos[1] > 0:
            if not obs.sticky_actions[STICKY_SPRINT]: return ACTION_SPRINT
            return move_towards(my_pos, [my_pos[0] + 0.3, my_pos[1]])
        else:
            return move_towards(my_pos, [ball_pos[0] - 0.1, my_flank_y])
            
    elif obs.ball_owned_team == 1:
        if not obs.sticky_actions[STICKY_SPRINT]: return ACTION_SPRINT
        return move_towards(my_pos, my_defensive_flank_position)
        
    else: # free ball
        if ball_pos[1] < 0: # Ball on my flank
            return move_towards(my_pos, ball_pos)
        else:
            return move_towards(my_pos, my_defensive_flank_position)
            
    return ACTION_IDLE

def defence_midfielder_actions(obs):
    my_pos = get_my_pos(obs)
    ball_pos = obs.ball_position
    central_defensive_midfield_position = [-0.3, 0]

    if obs.ball_owned_team == 0 and obs.ball_owned_player == obs.active_player:
        attacker_indices = [i for i, r in enumerate(obs.observation['left_team_roles']) if r in [5, 8, 9]]
        if attacker_indices:
            return ACTION_SHORT_PASS
        else:
            return ACTION_LONG_PASS

    elif obs.ball_owned_team == 0:
        return move_towards(my_pos, [ball_pos[0] - 0.15, ball_pos[1]])

    elif obs.ball_owned_team == 1:
        if not obs.sticky_actions[STICKY_SPRINT]: return ACTION_SPRINT
        return move_towards(my_pos, ball_pos)

    else:
        if np.linalg.norm(np.array(my_pos) - np.array(ball_pos)) < 0.3:
            return move_towards(my_pos, ball_pos)
        else:
            return move_towards(my_pos, central_defensive_midfield_position)
            
    return ACTION_IDLE

def central_midfielder_actions(obs):
    my_pos = get_my_pos(obs)
    ball_pos = obs.ball_position

    if obs.ball_owned_team == 0 and obs.ball_owned_player == obs.active_player:
        attacker_indices = [i for i, r in enumerate(obs.observation['left_team_roles']) if r in [8, 9]]
        if attacker_indices:
            return ACTION_SHORT_PASS
        else:
            if not obs.sticky_actions[STICKY_DRIBBLE]: return ACTION_DRIBBLE
            return move_towards(my_pos, [0.8, 0]) # Move towards opponent goal

    elif obs.ball_owned_team == 0:
        return move_towards(my_pos, [ball_pos[0], ball_pos[1]]) # Find open space near ball

    elif obs.ball_owned_team == 1:
        return move_towards(my_pos, [ball_pos[0] - 0.1, ball_pos[1]])
    
    else:
        return move_towards(my_pos, ball_pos)
        
    return ACTION_IDLE

def left_midfielder_actions(obs):
    my_pos = get_my_pos(obs)
    my_flank_y = 0.25
    base_position = [0.2, my_flank_y]
    
    if obs.ball_owned_team == 0 and obs.ball_owned_player == obs.active_player:
        if my_pos[0] > 0.5 and my_pos[1] > 0:
            return ACTION_HIGH_PASS # Cross
        else:
            if not obs.sticky_actions[STICKY_SPRINT]: return ACTION_SPRINT
            if not obs.sticky_actions[STICKY_DRIBBLE]: return ACTION_DRIBBLE
            return move_towards(my_pos, [0.8, my_flank_y]) # Dribble down the wing

    elif obs.ball_owned_team == 0:
        return move_towards(my_pos, [0.6, my_flank_y])

    elif obs.ball_owned_team == 1:
        return move_towards(my_pos, [-0.4, my_flank_y]) # Track back

    else:
        if obs.ball_position[1] > 0: # Ball on my flank
            return move_towards(my_pos, obs.ball_position)
        else:
            return move_towards(my_pos, base_position)

    return ACTION_IDLE

def right_midfielder_actions(obs):
    my_pos = get_my_pos(obs)
    my_flank_y = -0.25
    base_position = [0.2, my_flank_y]

    if obs.ball_owned_team == 0 and obs.ball_owned_player == obs.active_player:
        if my_pos[0] > 0.5 and my_pos[1] < 0:
            return ACTION_HIGH_PASS # Cross
        else:
            if not obs.sticky_actions[STICKY_SPRINT]: return ACTION_SPRINT
            if not obs.sticky_actions[STICKY_DRIBBLE]: return ACTION_DRIBBLE
            return move_towards(my_pos, [0.8, my_flank_y]) # Dribble down the wing

    elif obs.ball_owned_team == 0:
        return move_towards(my_pos, [0.6, my_flank_y])

    elif obs.ball_owned_team == 1:
        return move_towards(my_pos, [-0.4, my_flank_y]) # Track back

    else:
        if obs.ball_position[1] < 0: # Ball on my flank
            return move_towards(my_pos, obs.ball_position)
        else:
            return move_towards(my_pos, base_position)

    return ACTION_IDLE

def attack_midfielder_actions(obs):
    my_pos = get_my_pos(obs)
    ball_pos = obs.ball_position
    base_position = [0.4, 0]
    
    if obs.ball_owned_team == 0 and obs.ball_owned_player == obs.active_player:
        dist_to_goal = np.linalg.norm(np.array(my_pos) - np.array([1, 0]))
        if dist_to_goal < 0.4:
            return ACTION_SHOT
        else:
            cf_indices = [i for i, r in enumerate(obs.observation['left_team_roles']) if r == 9]
            if cf_indices:
                return ACTION_SHORT_PASS
            else:
                if not obs.sticky_actions[STICKY_DRIBBLE]: return ACTION_DRIBBLE
                return move_towards(my_pos, [0.8, 0])

    elif obs.ball_owned_team == 0:
        return move_towards(my_pos, [ball_pos[0] + 0.1, ball_pos[1]])

    elif obs.ball_owned_team == 1:
        if obs.ball_owned_player != -1:
             ball_owner_pos = obs.right_team_positions[obs.ball_owned_player]
             return move_towards(my_pos, ball_owner_pos)
        return move_towards(my_pos, ball_pos)

    else:
        if ball_pos[0] > 0:
            return move_towards(my_pos, ball_pos)
        else:
            return move_towards(my_pos, base_position)

    return ACTION_IDLE

def central_forward_actions(obs):
    my_pos = get_my_pos(obs)
    ball_pos = obs.ball_position

    if obs.game_mode == GAME_MODE_KICKOFF:
        return ACTION_SHORT_PASS

    if obs.ball_owned_team == 0 and obs.ball_owned_player == obs.active_player:
        dist_to_goal = np.linalg.norm(np.array(my_pos) - np.array([1, 0]))
        if dist_to_goal < 0.3:
            return ACTION_SHOT
        else:
            if not obs.sticky_actions[STICKY_DRIBBLE]: return ACTION_DRIBBLE
            return move_towards(my_pos, [1, 0])

    elif obs.ball_owned_team == 0:
        # A simple logic to stay ahead of the ball and near the last defender
        opponent_defenders = [p for i,p in enumerate(obs.right_team_positions) if obs.observation['right_team_roles'][i] in [1,2,3]]
        if opponent_defenders:
            last_defender_x = min([p[0] for p in opponent_defenders])
            target_x = last_defender_x - 0.05
            return move_towards(my_pos, [target_x, 0])
        return move_towards(my_pos, [0.7, 0])


    elif obs.ball_owned_team == 1:
        if obs.ball_owned_player != -1:
            owner_role = obs.observation['right_team_roles'][obs.ball_owned_player]
            if owner_role in [1,2,3]: # Is a defender
                return move_towards(my_pos, obs.right_team_positions[obs.ball_owned_player])
        return move_towards(my_pos, [0.3, 0])

    else:
        if ball_pos[0] > 0:
            return move_towards(my_pos, ball_pos)
        else:
            return move_towards(my_pos, [0.5, 0])
            
    return ACTION_IDLE