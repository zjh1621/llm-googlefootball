# player_roles_6_12.py

import math
import numpy as np
from typing import Dict, List

from wrappers import PlayerObservationWrapper, ObservationWrapper
from .constants import *
from .utils import *
from . import pass_action
from . import holding_action
from . import off_ball_movement
from . import utils as U




# --- Helper Functions ---

def apply_spacing_adjustment(obs: PlayerObservationWrapper, target_pos):
    """Adjusts target position to move away from crowded teammates."""
    adjusted_pos = np.array(target_pos)
    separation_radius = 0.08  # How close is "too close"
    repulsion_strength = 0.04 # How much to push away

    for mate_obs in obs.wrapper.player_observations:
        if mate_obs.active_player == obs.active_player:
            continue
        
        dist = get_distance(obs.player_position, mate_obs.player_position)
        if dist < separation_radius:
            away_vec = np.array(obs.player_position) - np.array(mate_obs.player_position)
            if np.linalg.norm(away_vec) > 0:
                 adjusted_pos += (away_vec / np.linalg.norm(away_vec)) * repulsion_strength
    
    return adjusted_pos

def clamp_position_to_field(position):
    """Ensures the target position is within the valid field boundaries."""
    pos = np.array(position)
    pos[0] = np.clip(pos[0], FIELD_X_LIMITS[0], FIELD_X_LIMITS[1])
    pos[1] = np.clip(pos[1], FIELD_Y_LIMITS[0], FIELD_Y_LIMITS[1])
    return pos

def get_offside_line(obs: PlayerObservationWrapper):
    """Gets the X-coordinate of the second-to-last opponent."""
    opponent_x_positions = sorted([p[0] for p in obs.right_team_positions])
    # If less than 2 opponents, offside is not possible in a typical sense,
    # so we can consider the halfway line as a fallback.
    if len(opponent_x_positions) < 2:
        return 0.0
    return opponent_x_positions[1]

def is_position_offside(obs: PlayerObservationWrapper, position):
    """Checks if a given position is offside."""
    x, y = position
    offside_line_x = get_offside_line(obs)
    ball_x = obs.ball_position[0]
    
    # A player is in an offside position if they are nearer to the opponents'
    # goal line than both the ball and the second-to-last opponent.
    return x > ball_x and x > offside_line_x

def has_space_to_run_into(obs: PlayerObservationWrapper):
    """Checks if there's open space in front of the player to dribble/sprint into."""
    my_pos = np.array(obs.player_position)
    my_dir = np.array(obs.player_direction)
    
    # If player is not moving, assume they want to move towards opponent goal.
    if np.linalg.norm(my_dir) < 0.01:
        my_dir = np.array([1, 0])

    # Define a cone in front of the player
    search_dist = 0.2  # How far to look ahead
    search_angle = np.pi / 4 # 45-degree cone width
    
    for opp_pos_arr in obs.right_team_positions:
        opp_pos = np.array(opp_pos_arr)
        vec_to_opp = opp_pos - my_pos
        dist_to_opp = np.linalg.norm(vec_to_opp)
        
        if 0 < dist_to_opp < search_dist:
            # Check if opponent is within the forward-facing cone
            if np.linalg.norm(my_dir) > 0 and np.linalg.norm(vec_to_opp) > 0:
                dot_product = np.dot(my_dir, vec_to_opp)
                norm_product = np.linalg.norm(my_dir) * np.linalg.norm(vec_to_opp)
                # Clip to avoid domain errors with arccos
                angle_to_opp = np.arccos(np.clip(dot_product / norm_product, -1.0, 1.0))
                if abs(angle_to_opp) < search_angle:
                    return False # Opponent is in the path
    return True

def find_best_offensive_pass(obs: PlayerObservationWrapper):
    """Finds the best forward-thinking pass."""
    my_pos = np.array(obs.player_position)
    best_target_obs = None
    max_score = -1e9

    for mate_obs in obs.wrapper.player_observations:
        if mate_obs.active_player == obs.active_player:
            continue

        mate_pos = np.array(mate_obs.player_position)
        if mate_pos[0] < my_pos[0] - 0.05: # Heavily penalize backward passes
            continue
        if is_position_offside(obs, mate_pos):
            continue

        dist_to_opp, _ = find_closest_opponent(mate_obs)
        # Score is a mix of how far forward they are and how open they are.
        score = (mate_pos[0] * 1.5) + dist_to_opp
        if score > max_score:
            max_score = score
            best_target_obs = mate_obs
            
    return best_target_obs

def find_safest_back_pass(obs: PlayerObservationWrapper):
    """Finds the safest, closest back pass target."""
    my_pos = np.array(obs.player_position)
    back_pass_roles = [ROLE_CB, ROLE_DM, ROLE_GK, ROLE_LB, ROLE_RB]
    best_target_obs = None
    min_dist = float('inf')

    for mate_obs in obs.wrapper.player_observations:
        mate_role = mate_obs.player_role
        mate_pos = np.array(mate_obs.player_position)
        
        if mate_obs.active_player == obs.active_player or mate_pos[0] >= my_pos[0] or mate_role not in back_pass_roles:
            continue

        dist_to_opp, _ = find_closest_opponent(mate_obs)
        # Must be very safe to be a back pass option
        if dist_to_opp > 0.2:
            dist_to_me = get_distance(my_pos, mate_pos)
            if dist_to_me < min_dist:
                min_dist = dist_to_me
                best_target_obs = mate_obs
    
    return best_target_obs

def find_opponent_to_mark(obs: PlayerObservationWrapper):
    """Finds the most dangerous, unmarked opponent in the player's vicinity."""
    my_pos = np.array(obs.player_position)
    best_opponent_to_mark = None
    min_dist = float('inf')

    for opp_pos_arr in obs.right_team_positions:
        opp_pos = np.array(opp_pos_arr)
        
        # Simple threat assessment: closer to our goal is more dangerous.
        # We only care about opponents in our half.
        if opp_pos[0] > -0.1:
            continue
            
        is_marked = False
        # Check if another teammate is closer to this opponent
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

def get_formation_base_position(obs: PlayerObservationWrapper):
    formation_plan = FORMATION_POSITIONS.get(TacticalConfig.CURRENT_FORMATION)
    if not formation_plan:
        return np.array(obs.player_position) # Fallback

    role = obs.player_role
    base_pos_template = formation_plan.get(role)
    if base_pos_template is None:
        return np.array(obs.player_position) # Fallback

    base_pos = np.array(base_pos_template)

    # For paired roles, one player takes the negative Y position.
    if role in PAIRED_ROLES:
        teammates_with_same_role = find_teammate_by_role(obs, role)
        if len(teammates_with_same_role) == 1: # This means there are two such players in total
            # Simple check to differentiate: the one with the higher initial Y takes the positive Y role.
            if obs.player_position[1] > teammates_with_same_role[0].player_position[1]:
                 base_pos[1] *= -1 # This player is on the right/bottom side of the pair

    return base_pos

def get_distance(pos1, pos2):
    return np.linalg.norm(np.array(pos1) - np.array(pos2))

def find_closest_opponent(obs: PlayerObservationWrapper):
    min_dist = 10
    closest_opp = None
    for opp_pos in obs.right_team_positions:
        dist = get_distance(obs.player_position, opp_pos)
        if dist < min_dist:
            min_dist = dist
            closest_opp = opp_pos
    return min_dist, closest_opp

def find_teammate_by_role(obs: PlayerObservationWrapper, role: int) -> List[PlayerObservationWrapper]:
    teammates = []
    for player_obs in obs.wrapper.player_observations:
        if player_obs.player_role == role:
            teammates.append(player_obs)
    return teammates

def find_safest_teammate_for_pass(obs: PlayerObservationWrapper, roles: List[int]):
    best_teammate = None
    max_safety_score = -1

    for teammate_obs in obs.wrapper.player_observations:
        if teammate_obs.player_role in roles and teammate_obs.active_player != obs.active_player:
            # Skip teammates who are in an offside position
            if is_position_offside(obs, teammate_obs.player_position):
                continue

            # Simple safety check: teammate furthest from any opponent
            min_dist_to_opp = 10
            for opp_pos in obs.right_team_positions:
                dist = get_distance(teammate_obs.player_position, opp_pos)
                if dist < min_dist_to_opp:
                    min_dist_to_opp = dist
            
            # Prioritize closer teammates who are safe
            safety_score = min_dist_to_opp / (get_distance(obs.player_position, teammate_obs.player_position) + 0.1)

            if safety_score > max_safety_score:
                max_safety_score = safety_score
                best_teammate = teammate_obs
    
    return best_teammate

def is_in_penalty_box(pos, side='my'):
    x, y = pos
    if side == 'my': # Left team's box
        return -1 <= x < -0.65 and abs(y) < 0.25
    else: # Right team's box
        return 0.65 < x <= 1 and abs(y) < 0.25

def has_clear_shot_angle(obs: PlayerObservationWrapper):
    # Simplified: check if there's an opponent directly between player and goal center
    goal_pos = np.array([1, 0])
    player_pos = np.array(obs.player_position)
    direction_to_goal = goal_pos - player_pos
    
    for opp_pos in obs.right_team_positions:
        direction_to_opp = np.array(opp_pos) - player_pos
        if np.dot(direction_to_goal, direction_to_opp) > 0:
            # Check if opponent is in the path
            dist_to_goal = np.linalg.norm(direction_to_goal)
            dist_to_opp = np.linalg.norm(direction_to_opp)
            if dist_to_opp < dist_to_goal:
                 # Calculate perpendicular distance
                perp_dist = np.linalg.norm(np.cross(direction_to_goal, direction_to_opp)) / dist_to_goal
                if perp_dist < 0.05: # threshold for being "in the way"
                    return False
    return True

def should_i_slide(obs: PlayerObservationWrapper) -> bool:
    """Decides if a slide tackle is a good action, reducing unnecessary slides."""
    # Rule 1: Only consider sliding if an opponent has the ball nearby.
    if obs.ball_owned_team != 1 or obs.distance_to_ball > 0.15:
        return False

    # Rule 2: Get the opponent ball carrier's position.
    opponent_ball_owner_idx = obs.ball_owned_player
    if opponent_ball_owner_idx >= len(obs.right_team_positions):
        return False  # Safeguard.

    opponent_pos = obs.right_team_positions[opponent_ball_owner_idx]

    # Rule 3: Only slide if we are very close to the actual ball carrier.
    distance_to_carrier = get_distance(obs.player_position, opponent_pos)
    if distance_to_carrier < 0.08:
        return True
        
    return False

def execute_pass_action(obs: PlayerObservationWrapper, target_obs: PlayerObservationWrapper):
    """
    Checks if player is facing the pass target. If yes, pass. If not, turn towards them.
    This makes passing more deliberate and accurate.
    """
    my_pos = np.array(obs.player_position)
    my_dir = np.array(obs.player_direction)
    if np.linalg.norm(my_dir) < 0.01:
        my_dir = np.array([1, 0]) # Assume facing forward if still

    target_pos = np.array(target_obs.player_position)
    vec_to_target = target_pos - my_pos
    
    if np.linalg.norm(vec_to_target) > 0:
        dot_product = np.dot(my_dir, vec_to_target)
        norm_product = np.linalg.norm(my_dir) * np.linalg.norm(vec_to_target)
        angle_to_target = np.arccos(np.clip(dot_product / norm_product, -1.0, 1.0))
        
        # If facing within a 45-degree cone, it's a good angle to pass.
        if abs(angle_to_target) < (np.pi / 4):
            dist = get_distance(my_pos, target_pos)
            if dist > 0.35:
                return ACTION_LONG_PASS
            elif dist > 0.2:
                return ACTION_HIGH_PASS
            else:
                return ACTION_SHORT_PASS
    
    # If not facing the target, the action is to turn towards them.
    return get_movement_action(my_pos, target_pos)

# --- Role Implementations ---

def goalkeeper_actions(obs: PlayerObservationWrapper):
    my_pos = np.array(obs.player_position)
    ball_pos = np.array(obs.ball_position)
    my_goal_center = np.array([-1.0, 0.0])

    # 1. With Ball: Find a safe pass or clear it.
    if obs.is_ball_owned_by_player():
        pass_decision = pass_action.decide_pass_action(obs)
        if pass_decision is not None:
            return pass_decision
        
        # Fallback if no pass is found
        return ACTION_HIGH_PASS

    # 2. Without Ball: Positioning is key.
    target_pos = my_pos # Default to staying put
    
    # Define a safe area within the penalty box for the keeper to operate in.
    gk_safe_area = {'x': (-1.0, -0.8), 'y': (-0.3, 0.3)}

    # A) If there's a loose ball in the box, decide whether to claim it.
    if obs.is_ball_free() and is_in_penalty_box(ball_pos, 'my'):
        # Only go for the ball if it's close and safe.
        if get_distance(my_pos, ball_pos) < 0.25:
            # The target is the ball, but clamped to the safe area.
            target_pos = ball_pos
            
    # B) Default positioning: stay between the ball and the goal.
    else:
        ideal_pos = my_goal_center + 0.15 * (ball_pos - my_goal_center) # Come out toward the ball
        
        # If our team has the ball, provide a pass-back option.
        if obs.is_ball_owned_by_team(0) and ball_pos[0] < -0.4:
            ideal_pos = ball_pos + np.array([-0.2, 0])
        
        # Special case for opponent corners.
        if obs.game_mode == 4 and obs.ball_owned_team == 1:
            ideal_pos = np.array([-0.95, 0.15 if ball_pos[1] < 0 else -0.15]) # Near post
        
        target_pos = ideal_pos

    # *** CRUCIAL: Clamp the final target position to the GK's safe area. ***
    target_pos[0] = np.clip(target_pos[0], gk_safe_area['x'][0], gk_safe_area['x'][1])
    target_pos[1] = np.clip(target_pos[1], gk_safe_area['y'][0], gk_safe_area['y'][1])

    if get_distance(my_pos, target_pos) < 0.03:
        return ACTION_IDLE # Already in a good position

    return get_movement_action(my_pos, target_pos)

def centre_back_actions(obs: PlayerObservationWrapper):
    base_pos = get_formation_base_position(obs)
    my_pos = np.array(obs.player_position)

    # --- Offensive Positioning (without ball) ---
    if obs.is_ball_owned_by_team(0) and obs.ball_position[0] > -0.5:
        target_x = max(base_pos[0], min(obs.ball_position[0] - 0.6, -0.2))
        target_pos = [target_x, base_pos[1]]
        if obs.game_mode == 0: # Normal game mode
             target_pos = apply_spacing_adjustment(obs, target_pos)
        return get_movement_action(my_pos, clamp_position_to_field(target_pos))

    # --- Ball Possession Logic ---
    if obs.is_ball_owned_by_player():
        # Priority 1: Dribble forward if space is available.
        if has_space_to_run_into(obs):
            return ACTION_SPRINT
        
        # Priority 2: Attempt to find and execute a pass.
        pass_decision = pass_action.decide_pass_action(obs)
        if pass_decision is not None:
            return pass_decision
            
        # Priority 3 (Fallback): Clear the ball if no other action is taken.
        return ACTION_HIGH_PASS
    
    # --- Defensive Logic ---
    if obs.is_ball_owned_by_team(1) or obs.is_ball_free():
        if should_i_slide(obs):
            return ACTION_SLIDING

        opponent_to_mark = find_opponent_to_mark(obs)
        if opponent_to_mark is not None:
            # Position between opponent and goal
            target_pos = opponent_to_mark + np.array([-0.05, 0])
            if obs.game_mode == 0:
                target_pos = apply_spacing_adjustment(obs, target_pos)
            return get_movement_action(my_pos, clamp_position_to_field(target_pos))

        # Fallback: Zonal defense between ball and goal
        target_pos = (np.array(obs.ball_position) + np.array([-1, 0])) / 2
        if obs.game_mode == 0:
            target_pos = apply_spacing_adjustment(obs, target_pos)
        return get_movement_action(my_pos, clamp_position_to_field(target_pos))
        
    target_pos = base_pos
    if obs.game_mode == 0:
        target_pos = apply_spacing_adjustment(obs, target_pos)
    return get_movement_action(obs.player_position, clamp_position_to_field(target_pos))

def left_back_actions(obs: PlayerObservationWrapper):
    base_pos = get_formation_base_position(obs)
    my_pos = np.array(obs.player_position)

    # --- Offensive Positioning ---
    if obs.is_ball_owned_by_team(0) and obs.ball_position[0] > -0.2:
        # Provide width higher up the pitch
        target_x = max(base_pos[0], obs.ball_position[0] - 0.3)
        if TacticalConfig.LB_ROLE == 'wingback':
            target_x = obs.ball_position[0] + 0.1 # Even more aggressive
        target_pos = [target_x, base_pos[1]]
        if obs.game_mode == 0:
            target_pos = apply_spacing_adjustment(obs, target_pos)
        return get_movement_action(my_pos, clamp_position_to_field(target_pos))

    # Ball Possession Logic
    if obs.is_ball_owned_by_player():
        if has_space_to_run_into(obs):
            return ACTION_SPRINT
        
        pass_decision = pass_action.decide_pass_action(obs)
        if pass_decision is not None:
            return pass_decision

        return ACTION_HIGH_PASS # Clear

    # Without Ball Logic
    if obs.is_ball_owned_by_team(1) or obs.is_ball_free():
        if should_i_slide(obs):
            return ACTION_SLIDING

        # Primarily mark opponent on the flank
        opponent_to_mark = find_opponent_to_mark(obs)
        if opponent_to_mark is not None and opponent_to_mark[1] < 0: # Opponent is on my (left) side
             target_pos = opponent_to_mark + np.array([-0.05, 0.05])
             if obs.game_mode == 0:
                target_pos = apply_spacing_adjustment(obs, target_pos)
             return get_movement_action(my_pos, clamp_position_to_field(target_pos))
        
        # If ball is on my flank, confront the carrier
        if obs.ball_position[1] < 0:
            return get_movement_action(obs.player_position, clamp_position_to_field(obs.ball_position))
        else: # Ball on other side, tuck in
            target_pos = [base_pos[0], -0.1]
            if obs.game_mode == 0:
                target_pos = apply_spacing_adjustment(obs, target_pos)
            return get_movement_action(obs.player_position, clamp_position_to_field(target_pos))
    
    target_pos = base_pos
    if obs.game_mode == 0:
        target_pos = apply_spacing_adjustment(obs, target_pos)
    return get_movement_action(obs.player_position, clamp_position_to_field(target_pos))

def right_back_actions(obs: PlayerObservationWrapper):
    base_pos = get_formation_base_position(obs)
    my_pos = np.array(obs.player_position)

    # --- Offensive Positioning ---
    if obs.is_ball_owned_by_team(0) and obs.ball_position[0] > -0.2:
        target_x = max(base_pos[0], obs.ball_position[0] - 0.3)
        if TacticalConfig.RB_ROLE == 'wingback':
            target_x = obs.ball_position[0] + 0.1
        target_pos = [target_x, base_pos[1]]
        if obs.game_mode == 0:
            target_pos = apply_spacing_adjustment(obs, target_pos)
        return get_movement_action(my_pos, clamp_position_to_field(target_pos))

    # Ball Possession Logic
    if obs.is_ball_owned_by_player():
        if has_space_to_run_into(obs):
            return ACTION_SPRINT
        
        pass_decision = pass_action.decide_pass_action(obs)
        if pass_decision is not None:
            return pass_decision

        return ACTION_HIGH_PASS

    # Without Ball Logic
    if obs.is_ball_owned_by_team(1) or obs.is_ball_free():
        if should_i_slide(obs):
            return ACTION_SLIDING

        opponent_to_mark = find_opponent_to_mark(obs)
        if opponent_to_mark is not None and opponent_to_mark[1] > 0: # Opponent is on my (right) side
             target_pos = opponent_to_mark + np.array([-0.05, -0.05])
             if obs.game_mode == 0:
                target_pos = apply_spacing_adjustment(obs, target_pos)
             return get_movement_action(my_pos, clamp_position_to_field(target_pos))

        if obs.ball_position[1] > 0: # Ball on my flank
            return get_movement_action(obs.player_position, clamp_position_to_field(obs.ball_position))
        else: # Ball on other side, tuck in
            target_pos = [base_pos[0], 0.1]
            if obs.game_mode == 0:
                target_pos = apply_spacing_adjustment(obs, target_pos)
            return get_movement_action(obs.player_position, clamp_position_to_field(target_pos))

    target_pos = base_pos
    if obs.game_mode == 0:
        target_pos = apply_spacing_adjustment(obs, target_pos)
    return get_movement_action(obs.player_position, clamp_position_to_field(target_pos))

def defence_midfielder_actions(obs: PlayerObservationWrapper):
    base_pos = get_formation_base_position(obs)
    my_pos = np.array(obs.player_position)

    if obs.is_ball_owned_by_player():
        if has_space_to_run_into(obs):
            return ACTION_SPRINT
        
        pass_decision = pass_action.decide_pass_action(obs)
        if pass_decision is not None:
            return pass_decision
            
        return ACTION_HIGH_PASS

    if obs.is_ball_owned_by_team(1) or obs.is_ball_free():
        if should_i_slide(obs):
            return ACTION_SLIDING

        opponent_to_mark = find_opponent_to_mark(obs)
        if opponent_to_mark is not None:
             target_pos = opponent_to_mark + np.array([-0.1, 0])
             if obs.game_mode == 0:
                target_pos = apply_spacing_adjustment(obs, target_pos)
             return get_movement_action(my_pos, clamp_position_to_field(target_pos))

        # Fallback: Shield the defense, stay between ball and goal
        target_pos = (np.array(obs.ball_position) - np.array([0.8, 0])) / 2
        if obs.game_mode == 0:
            target_pos = apply_spacing_adjustment(obs, target_pos)
        return get_movement_action(my_pos, clamp_position_to_field(target_pos))
    
    # When our team has the ball, be a safe option
    if obs.is_ball_owned_by_team(0):
        target_pos = np.array(obs.ball_position) + np.array([-0.25, 0])
        if obs.game_mode == 0:
            target_pos = apply_spacing_adjustment(obs, target_pos)
        return get_movement_action(my_pos, clamp_position_to_field(target_pos))
    
    target_pos = base_pos
    if obs.game_mode == 0:
        target_pos = apply_spacing_adjustment(obs, target_pos)
    return get_movement_action(obs.player_position, clamp_position_to_field(target_pos))

def central_midfielder_actions(obs: PlayerObservationWrapper):
    base_pos = get_formation_base_position(obs)
    my_pos = np.array(obs.player_position)

    if obs.is_ball_owned_by_player():
        if obs.player_position[0] > 0.4 and has_clear_shot_angle(obs):
            return ACTION_SHOT
        
        if has_space_to_run_into(obs):
            return ACTION_SPRINT
        
        pass_decision = pass_action.decide_pass_action(obs)
        if pass_decision is not None:
            return pass_decision
            
        return ACTION_HIGH_PASS

    if obs.game_mode == 0:
        if obs.is_ball_owned_by_team(1): # Opponent has ball, press
            if should_i_slide(obs):
                return ACTION_SLIDING

            opponent_to_mark = find_opponent_to_mark(obs)
            if opponent_to_mark is not None:
                target_pos = opponent_to_mark
                if obs.game_mode == 0:
                    target_pos = apply_spacing_adjustment(obs, target_pos)
                return get_movement_action(my_pos, clamp_position_to_field(target_pos))
            
            # Fallback to pressing ball carrier
            return get_movement_action(my_pos, clamp_position_to_field(obs.ball_position))

        elif obs.is_ball_owned_by_team(0): # We have ball, get into space
            if TacticalConfig.CM_ROLE == 'attacking_8_in_433':
                # Find space between lines
                target_pos = [obs.ball_position[0] + 0.1, obs.player_position[1]]
                if obs.game_mode == 0:
                    target_pos = apply_spacing_adjustment(obs, target_pos)
                return get_movement_action(obs.player_position, clamp_position_to_field(target_pos))
            else: # Box to box
                target_pos = obs.ball_position
                if obs.game_mode == 0:
                    target_pos = apply_spacing_adjustment(obs, target_pos)
                return get_movement_action(obs.player_position, clamp_position_to_field(target_pos)) # follow the ball
    
    target_pos = base_pos
    if obs.game_mode == 0:
        target_pos = apply_spacing_adjustment(obs, target_pos)
    return get_movement_action(obs.player_position, clamp_position_to_field(target_pos))

def left_midfielder_actions(obs: PlayerObservationWrapper):
    base_pos = get_formation_base_position(obs)
    my_pos = np.array(obs.player_position)

    if obs.is_ball_owned_by_player():
        if obs.player_position[0] > 0.5 and obs.player_position[1] > -0.2: # Cut inside
             if has_clear_shot_angle(obs):
                return ACTION_SHOT
        
        if has_space_to_run_into(obs):
            return ACTION_SPRINT
        
        pass_decision = pass_action.decide_pass_action(obs)
        if pass_decision is not None:
            return pass_decision

        return ACTION_HIGH_PASS

    if obs.game_mode == 0:
        if obs.is_ball_owned_by_team(1):
            if should_i_slide(obs):
                return ACTION_SLIDING
            if TacticalConfig.LM_ROLE == 'attacking_winger':
                if obs.ball_position[0] < 0.5 and obs.ball_position[0] > -0.5:
                    return get_movement_action(obs.player_position, clamp_position_to_field(obs.ball_position))
            else: # Track back to defend
                opponent_to_mark = find_opponent_to_mark(obs)
                if opponent_to_mark is not None:
                    target_pos = opponent_to_mark + np.array([-0.05, 0])
                    if obs.game_mode == 0:
                        target_pos = apply_spacing_adjustment(obs, target_pos)
                    return get_movement_action(my_pos, clamp_position_to_field(target_pos))
                if obs.ball_position[0] < 0:
                    return get_movement_action(obs.player_position, clamp_position_to_field([obs.ball_position[0] - 0.1, base_pos[1]]))

        elif obs.is_ball_owned_by_team(0):
            # Get into attacking space, but stay onside
            target_pos = [get_offside_line(obs) - 0.03, base_pos[1]]
            if obs.game_mode == 0:
                target_pos = apply_spacing_adjustment(obs, target_pos)
            return get_movement_action(obs.player_position, clamp_position_to_field(target_pos))

    target_pos = base_pos
    if obs.game_mode == 0:
        target_pos = apply_spacing_adjustment(obs, target_pos)
    return get_movement_action(obs.player_position, clamp_position_to_field(target_pos))

def right_midfielder_actions(obs: PlayerObservationWrapper):
    base_pos = get_formation_base_position(obs)
    my_pos = np.array(obs.player_position)

    if obs.is_ball_owned_by_player():
        if obs.player_position[0] > 0.5 and obs.player_position[1] < 0.2: # Cut inside
             if has_clear_shot_angle(obs):
                return ACTION_SHOT
                
        if has_space_to_run_into(obs):
            return ACTION_SPRINT

        pass_decision = pass_action.decide_pass_action(obs)
        if pass_decision is not None:
            return pass_decision

        return ACTION_HIGH_PASS

    if obs.game_mode == 0:
        if obs.is_ball_owned_by_team(1):
            if should_i_slide(obs):
                return ACTION_SLIDING
            if TacticalConfig.RM_ROLE == 'attacking_winger':
                if obs.ball_position[0] < 0.5 and obs.ball_position[0] > -0.5:
                    return get_movement_action(obs.player_position, clamp_position_to_field(obs.ball_position))
            else:
                opponent_to_mark = find_opponent_to_mark(obs)
                if opponent_to_mark is not None:
                    target_pos = opponent_to_mark + np.array([-0.05, 0])
                    if obs.game_mode == 0:
                        target_pos = apply_spacing_adjustment(obs, target_pos)
                    return get_movement_action(my_pos, clamp_position_to_field(target_pos))
                if obs.ball_position[0] < 0:
                    return get_movement_action(obs.player_position, clamp_position_to_field([obs.ball_position[0] - 0.1, base_pos[1]]))

        elif obs.is_ball_owned_by_team(0):
            target_pos = [get_offside_line(obs) - 0.03, base_pos[1]]
            if obs.game_mode == 0:
                target_pos = apply_spacing_adjustment(obs, target_pos)
            return get_movement_action(obs.player_position, clamp_position_to_field(target_pos))

    target_pos = base_pos
    if obs.game_mode == 0:
        target_pos = apply_spacing_adjustment(obs, target_pos)
    return get_movement_action(obs.player_position, clamp_position_to_field(target_pos))

def attack_midfielder_actions(obs: PlayerObservationWrapper):
    base_pos = get_formation_base_position(obs)
    my_pos = np.array(obs.player_position)

    if obs.is_ball_owned_by_player():
        if obs.player_position[0] > 0.5 and has_clear_shot_angle(obs):
            return ACTION_SHOT
            
        if has_space_to_run_into(obs):
            return ACTION_SPRINT
            
        pass_decision = pass_action.decide_pass_action(obs)
        if pass_decision is not None:
            return pass_decision
        
        return ACTION_HIGH_PASS

    if obs.game_mode == 0:
        if obs.is_ball_owned_by_team(1): # Opponent has ball
            if should_i_slide(obs):
                return ACTION_SLIDING
            # Press opponent's DM
            opp_dm_pos = None
            for i, role in enumerate(obs.observation['right_team_roles']):
                if role == ROLE_DM:
                    opp_dm_pos = obs.right_team_positions[i]
                    break
            if opp_dm_pos is not None:
                target_pos = opp_dm_pos
                if obs.game_mode == 0:
                    target_pos = apply_spacing_adjustment(obs, target_pos)
                return get_movement_action(obs.player_position, clamp_position_to_field(target_pos))
            return get_movement_action(obs.player_position, clamp_position_to_field(obs.ball_position))
        
        elif obs.is_ball_owned_by_team(0): # We have ball
            # Find space between the lines
            offside_line = get_offside_line(obs)
            target_x = (obs.ball_position[0] + offside_line) / 2.0
            target_pos = [target_x, obs.ball_position[1]*0.5]
            if obs.game_mode == 0:
                target_pos = apply_spacing_adjustment(obs, target_pos)
            return get_movement_action(obs.player_position, clamp_position_to_field(target_pos))

    target_pos = base_pos
    if obs.game_mode == 0:
        target_pos = apply_spacing_adjustment(obs, target_pos)
    return get_movement_action(obs.player_position, clamp_position_to_field(target_pos))

def central_forward_actions(obs: PlayerObservationWrapper):
    base_pos = get_formation_base_position(obs)
    my_pos = np.array(obs.player_position)

    if obs.is_ball_owned_by_player():
        # Priority 1: Shoot if in a good position.
        if is_in_penalty_box(obs.player_position, 'opponent') or obs.player_position[0] > 0.6:
            if has_clear_shot_angle(obs):
                return ACTION_SHOT
        
        # Priority 2: Dribble if space is available.
        if has_space_to_run_into(obs):
            return ACTION_SPRINT
        
        # Priority 3: Try to pass.
        pass_decision = pass_action.decide_pass_action(obs)
        if pass_decision is not None:
            return pass_decision
        
        # Priority 4 (Fallback): If in doubt, shoot.
        return ACTION_SHOT
    
    if obs.game_mode == 0:
        if obs.is_ball_owned_by_team(0): # We have ball
            if TacticalConfig.CF_ROLE == 'false_nine':
                # Drop deep to receive ball
                target_pos = [obs.ball_position[0] - 0.15, obs.ball_position[1]]
                if obs.game_mode == 0:
                    target_pos = apply_spacing_adjustment(obs, target_pos)
                return get_movement_action(my_pos, clamp_position_to_field(target_pos))
            else: # poacher/pivot
                # Run to just behind the offside line, looking for a through ball
                target_pos = [get_offside_line(obs) - 0.03, (my_pos[1] + obs.ball_position[1])/2]
                if obs.game_mode == 0:
                    target_pos = apply_spacing_adjustment(obs, target_pos)
                return get_movement_action(my_pos, clamp_position_to_field(target_pos))

        elif obs.is_ball_owned_by_team(1): # Opponent has ball
            if should_i_slide(obs):
                return ACTION_SLIDING
            # Press the CBs
            if obs.ball_position[0] < -0.4:
                return get_movement_action(obs.player_position, clamp_position_to_field(obs.ball_position))
    
    # Offensive Set Pieces
    if obs.game_mode in [3, 4] and obs.ball_owned_team == 0:
        if obs.distance_to_ball < 0.1:
            return ACTION_SHOT # Head it
        return get_movement_action(obs.player_position, clamp_position_to_field([0.85, 0]))

    target_pos = base_pos
    if obs.game_mode == 0:
        target_pos = apply_spacing_adjustment(obs, target_pos)
    return get_movement_action(obs.player_position, clamp_position_to_field(target_pos))

# --- Main Strategy Function ---

player_role_to_action = {
    ROLE_GK: goalkeeper_actions,
    ROLE_CB: centre_back_actions,
    ROLE_LB: left_back_actions,
    ROLE_RB: right_back_actions,
    ROLE_DM: defence_midfielder_actions,
    ROLE_CM: central_midfielder_actions, 
    ROLE_LM: left_midfielder_actions, 
    ROLE_RM: right_midfielder_actions,
    ROLE_AM: attack_midfielder_actions,
    ROLE_CF: central_forward_actions,
}

def player_action_decision(obs):
    """
    Main decision-making function for a single player.

    Args:
        obs: A PlayerObservationWrapper object containing the state for the active player.

    Returns:
        An integer representing the action to take.
    """
    
    # --- Game Mode Checks ---
    # In certain game modes, the logic might be simpler.
    # For now, we use the same logic for all modes, but this is a place for future expansion.
    game_mode = obs.game_mode
    if game_mode != 0: # If not in normal play (e.g., KickOff, FreeKick, etc.)
        # A simple logic for set pieces: if we have the ball, pass; otherwise, move to ball.
        if obs.is_ball_owned_by_team(0):
            # On set pieces, a short pass is often a safe and effective start.
            return U.ACTION_SHORT_PASS
        else:
            # If opponent has the ball on a set piece, adopt a defensive position.
            return off_ball_movement.decide_off_ball_movement(obs)

    # --- Main Logic: On-ball vs Off-ball ---
    
    # Check if the active player has the ball.
    if obs.is_ball_owned_by_player():
        # If player has the ball, decide on the holding action (shoot, pass, dribble).
        return holding_action.decide_holding_action(obs)
    else:
        # If player does not have the ball, decide on off-ball movement.
        return off_ball_movement.decide_off_ball_movement(obs)

# This structure allows for easy expansion. For instance, you could have a team-level
# strategy function that calls `player_action_decision` for each player,
# possibly passing in team-wide tactical instructions.