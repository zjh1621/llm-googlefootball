from . import utils
from . import pass_action

# --- Holding (dribble/shoot) decision logic for each role ---

def has_space_to_dribble(obs, min_dist=0.1):
    """Helper function to check for dribbling space."""
    if not obs.distances_to_opponents:
        return True
    return min(obs.distances_to_opponents) > min_dist

def decide_holding_action_GK(obs):
    """Goalkeepers don't dribble; they look for a pass immediately."""
    return pass_action.decide_pass_GK(obs)

def decide_holding_action_CB(obs):
    """CBs prioritize safety, dribbling only when clearly safe and forward."""
    safe_action = utils.get_safe_dribble_action(obs)
    if safe_action is not None:
        return safe_action

    # More aggressive in opponent's half
    if obs.player_position[0] > 0.1:
        if pass_action.can_shoot(obs, min_dist=0.6):
            return utils.ACTION_SHOT
        if has_space_to_dribble(obs, min_dist=0.08):
            return utils.dribble_towards_opponent_goal(obs)

    # In own half, only dribble if safe
    if has_space_to_dribble(obs, min_dist=0.15):
        return utils.dribble_towards_opponent_goal(obs)
    
    return pass_action.decide_pass_CB(obs)

def decide_holding_action_LB_RB(obs):
    """Full-backs dribble down the wing if space allows, otherwise cross or pass."""
    safe_action = utils.get_safe_dribble_action(obs)
    if safe_action is not None:
        return safe_action

    player_pos = obs.player_position
    # In attacking third, look to cross, shoot, or dribble
    if utils.is_in_attacking_third(player_pos):
        if pass_action.can_shoot(obs, min_dist=0.7):
            return utils.ACTION_SHOT
        if has_space_to_dribble(obs, min_dist=0.06):
            return utils.dribble_towards_opponent_goal(obs) # Dribble into space/towards goal
        return pass_action.decide_pass_LB_RB(obs) # Looks for cross/pass

    # In other areas, dribble if space is available
    if has_space_to_dribble(obs, min_dist=0.1):
        return utils.dribble_towards_opponent_goal(obs)

    return pass_action.decide_pass_LB_RB(obs)

def decide_holding_action_DM(obs):
    """DMs are cautious, dribbling to advance play but prioritizing possession."""
    safe_action = utils.get_safe_dribble_action(obs)
    if safe_action is not None:
        return safe_action
        
    # In opponent's half, consider a long shot or dribble
    if obs.player_position[0] > 0.2:
        if pass_action.can_shoot(obs, min_dist=0.5):
            return utils.ACTION_SHOT
        if has_space_to_dribble(obs, min_dist=0.08):
            return utils.dribble_towards_opponent_goal(obs)
            
    return pass_action.decide_pass_DM(obs)

def decide_holding_action_CM_LM_RM_AM(obs):
    """Attacking midfielders are the primary creative force."""
    safe_action = utils.get_safe_dribble_action(obs)
    if safe_action is not None:
        return safe_action

    player_pos = obs.player_position
    # In attacking areas, the priority is Shoot > Dribble > Pass
    if player_pos[0] > 0.3:
        if pass_action.can_shoot(obs, min_dist=0.5):
            return utils.ACTION_SHOT
        if has_space_to_dribble(obs, min_dist=0.06):
            return utils.dribble_towards_opponent_goal(obs)

    # If further back, dribble if there's space
    if has_space_to_dribble(obs, min_dist=0.08):
        return utils.dribble_towards_opponent_goal(obs)
    
    return pass_action.decide_pass_CM_LM_RM_AM(obs)

def decide_holding_action_CF(obs):
    """Strikers are selfish: their main goal is to shoot."""
    safe_action = utils.get_safe_dribble_action(obs)
    if safe_action is not None:
        return safe_action

    player_pos = obs.player_position
    # High priority to shoot
    if player_pos[0] > 0.6:
        if pass_action.can_shoot(obs, min_dist=0.6):
            return utils.ACTION_SHOT
    
    # Dribble to get into a shooting position
    if has_space_to_dribble(obs, min_dist=0.04):
        return utils.dribble_towards_opponent_goal(obs)
        
    # If cannot shoot or dribble, lay off the ball
    return pass_action.decide_pass_CF(obs) 