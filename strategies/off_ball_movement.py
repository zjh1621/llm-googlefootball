from . import utils
import numpy as np

# --- Off-ball movement logic for each role ---

# Defines how close an opponent must be for a defender to leave their position and press.
ENGAGEMENT_RADIUS = 0.3 

def decide_GK_off_ball_move(obs):
    player_pos = obs.player_position
    # If opponent has the ball, guard the goal
    if obs.is_ball_owned_by_team(team=1):
        ball_pos = obs.ball_position
        # Target position is on the goal line, between the ball and center of goal
        goal_center_y = 0
        target_y = player_pos[1] + 0.2 * (ball_pos[1] - player_pos[1])
        # Clamp to goal posts
        target_y = np.clip(target_y, utils.GOAL_Y_MIN, utils.GOAL_Y_MAX)
        target_pos = [utils.FIELD_X_MIN, target_y]
    
    # If our team has the ball, provide a safe back-pass option within the penalty box
    elif obs.is_ball_owned_by_team(team=0):
        ball_owner_pos = obs.left_team_positions[obs.ball_owned_player]
        # Move to create a safe passing lane, but stay near the goal
        target_pos = [player_pos[0], ball_owner_pos[1] * 0.5]
    else: # Ball is free
        target_pos = [utils.FIELD_X_MIN + 0.1, 0]

    # Ensure the keeper stays within the penalty box
    target_pos[0] = np.clip(target_pos[0], utils.FIELD_X_MIN, utils.OWN_PENALTY_BOX_X_MAX)
    target_pos[1] = np.clip(target_pos[1], utils.PENALTY_BOX_Y_MIN, utils.PENALTY_BOX_Y_MAX)
    
    return utils.get_direction_action(player_pos, target_pos)


def decide_CB_off_ball_move(obs):
    player_pos = obs.player_position
    
    if obs.is_ball_owned_by_team(team=1):
        carrier_pos, carrier_dir = utils.get_opponent_ball_carrier_info(obs)
        if carrier_pos is not None:
            distance_to_carrier = utils.get_distance(player_pos, carrier_pos)
            if distance_to_carrier < ENGAGEMENT_RADIUS:
                future_pos = utils.predict_future_position(carrier_pos, carrier_dir)
                return utils.get_direction_action(player_pos, future_pos)
        
        target_x = utils.DEFENSIVE_THIRD_X
        target_y = np.clip(player_pos[1], -0.2, 0.2)
        target_pos = [target_x, target_y]
    
    elif obs.is_ball_owned_by_team(team=0):
        ball_owner_pos = obs.left_team_positions[obs.ball_owned_player]
        target_x = min(player_pos[0] + 0.02, 0)
        target_x = min(target_x, ball_owner_pos[0] - 0.15)
        target_y = np.clip(player_pos[1], -0.25, 0.25)
        target_pos = [target_x, target_y]
    
    else: # Ball is free, hold defensive line
        target_x = utils.DEFENSIVE_THIRD_X
        target_y = np.clip(player_pos[1], -0.2, 0.2)
        target_pos = [target_x, target_y]
    
    return utils.get_direction_action(player_pos, target_pos) if not np.array_equal(player_pos, target_pos) else utils.ACTION_IDLE


def decide_LB_RB_off_ball_move(obs):
    player_pos = obs.player_position
    
    if obs.is_ball_owned_by_team(team=1):
        carrier_pos, carrier_dir = utils.get_opponent_ball_carrier_info(obs)
        if carrier_pos is not None:
            distance_to_carrier = utils.get_distance(player_pos, carrier_pos)
            if distance_to_carrier < ENGAGEMENT_RADIUS:
                future_pos = utils.predict_future_position(carrier_pos, carrier_dir)
                return utils.get_direction_action(player_pos, future_pos)

        ball_pos = obs.ball_position.copy()
        if np.sign(ball_pos[1]) == np.sign(player_pos[1]):
            target_pos = [player_pos[0], player_pos[1]]
        else:
            target_pos = [player_pos[0], player_pos[1] * 0.5]
        target_pos[0] = np.clip(target_pos[0], utils.FIELD_X_MIN, 0.1)

    elif obs.is_ball_owned_by_team(team=0):
        # NEW LOGIC: Find open space to provide width and an attacking option.
        target_pos = utils.find_best_open_space(obs)
        if target_pos is None: # Fallback to old logic if space finding fails
            target_pos = [player_pos[0] + 0.1, player_pos[1]]
    
    else: # Ball is free, move towards the ball
        target_pos = obs.ball_position.copy()

    return utils.get_direction_action(player_pos, target_pos) if not np.array_equal(player_pos, target_pos) else utils.ACTION_SPRINT


def decide_DM_off_ball_move(obs):
    player_pos = obs.player_position
    target_pos = None

    if obs.is_ball_owned_by_team(team=1):
        carrier_pos, carrier_dir = utils.get_opponent_ball_carrier_info(obs)
        if carrier_pos is not None:
            distance_to_carrier = utils.get_distance(player_pos, carrier_pos)
            if distance_to_carrier < ENGAGEMENT_RADIUS:
                future_pos = utils.predict_future_position(carrier_pos, carrier_dir, steps=6)
                return utils.get_direction_action(player_pos, future_pos)

        target_pos = (np.array(obs.ball_position.copy()) + np.array([utils.DEFENSIVE_THIRD_X, 0])) / 2
        target_pos[0] = np.clip(target_pos[0], utils.FIELD_X_MIN, 0)

    elif obs.is_ball_owned_by_team(team=0):
        # NEW LOGIC: Find a pocket of space to act as a pivot.
        target_pos = utils.find_best_open_space(obs)
        if target_pos is None: # Fallback
             target_pos = [player_pos[0] - 0.1, player_pos[1]]

    else: # Ball is free, move towards it
        target_pos = obs.ball_position.copy()

    if target_pos is not None:
        return utils.get_direction_action(player_pos, target_pos) if not np.array_equal(player_pos, target_pos) else utils.ACTION_IDLE
    return utils.ACTION_IDLE


def decide_CM_LM_RM_off_ball_move(obs):
    player_pos = obs.player_position
    target_pos = None
    
    if obs.is_ball_owned_by_team(team=1):
        carrier_pos, carrier_dir = utils.get_opponent_ball_carrier_info(obs)
        if carrier_pos is not None:
            distance_to_carrier = utils.get_distance(player_pos, carrier_pos)
            if distance_to_carrier < ENGAGEMENT_RADIUS - 0.1:
                future_pos = utils.predict_future_position(carrier_pos, carrier_dir, steps=10)
                return utils.get_direction_action(player_pos, future_pos)

        target_pos = obs.ball_position.copy()
        target_pos[0] = np.clip(target_pos[0], -0.5, 0.5)

    elif obs.is_ball_owned_by_team(team=0):
        # NEW LOGIC: Find space between the lines or on the flank.
        target_pos = utils.find_best_open_space(obs)
        if target_pos is None: # Fallback
            target_pos = [player_pos[0] + 0.1, player_pos[1]]
    
    else: # Ball is free
        target_pos = obs.ball_position.copy()
    
    role = obs.player_role
    if role in [utils.ROLE_LM, utils.ROLE_RM]:
        y_corridor = (0.1, utils.FIELD_Y_MAX) if player_pos[1] > 0 else (utils.FIELD_Y_MIN, -0.1)
        target_pos[1] = np.clip(target_pos[1], y_corridor[0], y_corridor[1])
    else:
        target_pos[1] = np.clip(target_pos[1], -0.35, 0.35)

    if target_pos is not None:
        return utils.get_direction_action(player_pos, target_pos) if not np.array_equal(player_pos, target_pos) else utils.ACTION_SPRINT
    return utils.ACTION_IDLE


def decide_AM_off_ball_move(obs):
    player_pos = obs.player_position
    target_pos = None
    
    if obs.is_ball_owned_by_team(team=1):
        carrier_pos, carrier_dir = utils.get_opponent_ball_carrier_info(obs)
        if carrier_pos is not None:
            future_pos = utils.predict_future_position(carrier_pos, carrier_dir, steps=12)
            return utils.get_direction_action(player_pos, future_pos)
            
        target_pos = obs.ball_position.copy()

    elif obs.is_ball_owned_by_team(team=0):
        # NEW LOGIC: Find space in the hole behind the striker.
        target_pos = utils.find_best_open_space(obs)
        if target_pos is None: # Fallback
            target_pos = [utils.OPPONENT_PENALTY_BOX_X_MIN - 0.1, 0]
    
    else: # Ball is free
        target_pos = obs.ball_position.copy()
    
    if target_pos is not None:
        return utils.get_direction_action(player_pos, target_pos) if not np.array_equal(player_pos, target_pos) else utils.ACTION_SPRINT
    return utils.ACTION_IDLE


def decide_CF_off_ball_move(obs):
    player_pos = obs.player_position
    target_pos = None
    
    if obs.is_ball_owned_by_team(team=1):
        carrier_pos, _ = utils.get_opponent_ball_carrier_info(obs)
        if carrier_pos is not None and carrier_pos[0] > 0.5:
             opponent_cbs = [pos for i, pos in enumerate(obs.right_team_positions)
                        if obs.observation['right_team_roles'][i] == utils.ROLE_CB]
             if opponent_cbs:
                target_pos = min(opponent_cbs, key=lambda p: np.linalg.norm(np.array(player_pos) - np.array(p)))
             else:
                target_pos = carrier_pos
        else:
            target_pos = [0.4, player_pos[1]] 

    elif obs.is_ball_owned_by_team(team=0):
        # NEW LOGIC: Find space to run in behind the defense.
        target_pos = utils.find_best_open_space(obs)
        if target_pos is None: # Fallback
            opponent_deepest_defender_x = max([p[0] for p in obs.right_team_positions]) if len(obs.right_team_positions) > 0 else 0.8
            target_pos = [opponent_deepest_defender_x + 0.05, np.random.uniform(-0.2, 0.2)]

    else: # Ball is free
        target_pos = obs.ball_position.copy()

    if target_pos is not None:
      target_pos[1] = np.clip(target_pos[1], -0.3, 0.3)
      return utils.get_direction_action(player_pos, target_pos) if not np.array_equal(player_pos, target_pos) else utils.ACTION_SPRINT
    
    return utils.ACTION_IDLE 