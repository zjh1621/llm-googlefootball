from . import utils
import numpy as np

# --- Helper functions for passing, specific to this module ---

def find_best_pass_target(obs, role_list, check_offside=False):
    """Finds the best open teammate, a generic helper."""
    return utils.find_open_teammate(obs, role_list=role_list, check_offside=check_offside)

def can_cross_to_striker(obs):
    """Check if a cross to the striker is a good option."""
    striker = utils.find_teammate_with_role(obs, utils.ROLE_CF)
    if striker is None:
        return False
    
    striker_pos = obs.left_team_positions[striker]
    # Check if striker is in a good position to receive a cross
    return utils.is_in_opponent_penalty_box(striker_pos)

def can_shoot(obs, min_dist=0.7, max_dist=0.98):
    """Check if the player is in a good shooting position."""
    player_pos = obs.player_position
    # Check if player is in shooting range (X-axis)
    if not (min_dist < player_pos[0] < max_dist):
        return False
    # Check if player has a clear shot (Y-axis not too wide)
    if abs(player_pos[1]) > 0.3:
        return False
    return True

# --- Pass decision logic for each role ---

def _decide_pass_type(obs, target_idx):
    """
    Decides the type of pass (Short, Long, High) based on distance and tactical context.
    """
    player_pos = obs.player_position
    target_pos = obs.left_team_positions[target_idx]
    distance = utils.get_distance(player_pos, target_pos)

    # Rule 1: Short distance is always a short pass
    if distance < utils.SHORT_PASS_DISTANCE_MAX:
        return utils.ACTION_SHORT_PASS

    # Rule 2: For long distances, decide between a driven pass (LONG) or a lobbed pass (HIGH)
    
    # Context A: Crossing from a wide position
    is_winger_pos = utils.is_on_flank(player_pos) and utils.is_in_attacking_third(player_pos)
    target_is_striker_in_box = (obs.observation['left_team_roles'][target_idx] == utils.ROLE_CF and 
                                utils.is_in_opponent_penalty_box(target_pos))
    if is_winger_pos and target_is_striker_in_box:
        return utils.ACTION_HIGH_PASS

    # Context B: Clearing from deep under high pressure
    is_defender = obs.player_role in [utils.ROLE_GK, utils.ROLE_CB, utils.ROLE_LB, utils.ROLE_RB]
    pressure = utils.get_pressure_level(obs)
    if is_defender and utils.is_in_defensive_third(player_pos) and pressure == '高':
        return utils.ACTION_HIGH_PASS

    # Context C: Lobbed through-ball over the defense
    target_is_forward = obs.observation['left_team_roles'][target_idx] in [utils.ROLE_CF, utils.ROLE_AM]
    if target_is_forward and utils.is_pass_interceptable(obs, target_pos):
        return utils.ACTION_HIGH_PASS

    # Default long-range pass: A driven long pass for switching play, etc.
    return utils.ACTION_LONG_PASS

def decide_pass_GK(obs):
    pressure = utils.get_pressure_level(obs)
    target = None
    if pressure == '高':
        # Under high pressure, look for any forward player to clear the ball to.
        target = find_best_pass_target(obs, [utils.ROLE_CF, utils.ROLE_LM, utils.ROLE_RM, utils.ROLE_AM])
    else:
        # Low pressure, build up from the back
        target = find_best_pass_target(obs, [utils.ROLE_CB, utils.ROLE_LB, utils.ROLE_RB, utils.ROLE_DM])
    
    if target is not None:
        return _decide_pass_type(obs, target)

    # If absolutely no one is open, clear it long and forward.
    return utils.ACTION_SHOT


def decide_pass_CB(obs):
    # Look for a forward pass first, then sideways/back
    target = find_best_pass_target(obs, [utils.ROLE_DM, utils.ROLE_CM, utils.ROLE_AM], check_offside=True)
    if target is None:
        target = find_best_pass_target(obs, [utils.ROLE_LB, utils.ROLE_RB, utils.ROLE_GK])
    
    if target is not None:
        return _decide_pass_type(obs, target)
    
    # Last resort: Safe, forward clearance
    return utils.ACTION_SHOT


def decide_pass_LB_RB(obs):
    # Find best pass target based on position
    if utils.is_in_attacking_third(obs.player_position):
        target = find_best_pass_target(obs, [utils.ROLE_LM, utils.ROLE_RM, utils.ROLE_AM, utils.ROLE_CM, utils.ROLE_CF], check_offside=True)
    else:
        target = find_best_pass_target(obs, [utils.ROLE_CB, utils.ROLE_DM, utils.ROLE_CM])

    if target is not None:
        return _decide_pass_type(obs, target)

    # Last resort: Safe, forward clearance
    return utils.ACTION_SHOT


def decide_pass_DM(obs):
    # Determine pass based on pressure
    target = None
    if utils.get_pressure_level(obs) in ['高', '中']:
        target = find_best_pass_target(obs, [utils.ROLE_CB, utils.ROLE_LB, utils.ROLE_RB])
    else:
        # Low pressure, look for forward options first, then try to switch play
        target = find_best_pass_target(obs, [utils.ROLE_CM, utils.ROLE_AM, utils.ROLE_LM, utils.ROLE_RM], check_offside=True)
        if target is None:
            target = find_best_pass_target(obs, [utils.ROLE_LM, utils.ROLE_RM], check_offside=True)

    if target is not None:
        return _decide_pass_type(obs, target)
    
    # Last resort: Safe clearance if in own half, otherwise short pass
    if obs.player_position[0] < 0:
        return utils.ACTION_SHOT
    return utils.ACTION_SHORT_PASS


def decide_pass_CM_LM_RM_AM(obs):
    # Determine the best pass target based on field position
    target = None
    if utils.is_in_attacking_third(obs.player_position):
        # Look for through ball to striker first
        target = find_best_pass_target(obs, [utils.ROLE_CF], check_offside=True)
        # If no through ball, try a short combination pass
        if target is None:
            target = find_best_pass_target(obs, [utils.ROLE_AM, utils.ROLE_CM, utils.ROLE_LM, utils.ROLE_RM], check_offside=True)
    else: # In mid/defensive third
        # Try to advance the ball
        target = find_best_pass_target(obs, [utils.ROLE_AM, utils.ROLE_CF, utils.ROLE_LM, utils.ROLE_RM], check_offside=True)
        if target is None:
            # Or circulate possession safely
            target = find_best_pass_target(obs, [utils.ROLE_DM, utils.ROLE_CM, utils.ROLE_LB, utils.ROLE_RB])

    if target is not None:
        return _decide_pass_type(obs, target)
            
    return utils.ACTION_LONG_PASS


def decide_pass_CF(obs):
    # CF's primary goal is to shoot, but if passing, lay off to a teammate.
    target = find_best_pass_target(obs, [utils.ROLE_AM, utils.ROLE_CM], check_offside=True)
    if target is None:
        target = find_best_pass_target(obs, [utils.ROLE_LM, utils.ROLE_RM], check_offside=True)

    if target is not None:
        return _decide_pass_type(obs, target)

    return utils.ACTION_DRIBBLE # If no good pass, hold the ball 