from . import utils
from . import off_ball_movement
from . import holding_action
from . import pass_action

# --- Role-based action functions ---

def decide_on_ball_action(obs):
    """
    Decides the action for a player who has the ball, based on their role.
    This function routes to the appropriate logic in holding_action.
    """
    role = obs.player_role
    
    if role == utils.ROLE_GK:
        return holding_action.decide_holding_action_GK(obs)
    elif role == utils.ROLE_CB:
        return holding_action.decide_holding_action_CB(obs)
    elif role in [utils.ROLE_LB, utils.ROLE_RB]:
        return holding_action.decide_holding_action_LB_RB(obs)
    elif role == utils.ROLE_DM:
        return holding_action.decide_holding_action_DM(obs)
    elif role in [utils.ROLE_CM, utils.ROLE_LM, utils.ROLE_RM, utils.ROLE_AM]:
        return holding_action.decide_holding_action_CM_LM_RM_AM(obs)
    elif role == utils.ROLE_CF:
        action = holding_action.decide_holding_action_CF(obs)
        return action
    
    return utils.ACTION_IDLE # Default case

def decide_off_ball_action(obs):
    """
    Decides the action for a player who does not have the ball, based on their role.
    This function routes to the appropriate logic in off_ball_movement.
    """
    role = obs.player_role

    if role == utils.ROLE_GK:
        return off_ball_movement.decide_GK_off_ball_move(obs)
    elif role == utils.ROLE_CB:
        return off_ball_movement.decide_CB_off_ball_move(obs)
    elif role in [utils.ROLE_LB, utils.ROLE_RB]:
        return off_ball_movement.decide_LB_RB_off_ball_move(obs)
    elif role == utils.ROLE_DM:
        return off_ball_movement.decide_DM_off_ball_move(obs)
    elif role in [utils.ROLE_CM, utils.ROLE_LM, utils.ROLE_RM]:
        return off_ball_movement.decide_CM_LM_RM_off_ball_move(obs)
    elif role == utils.ROLE_AM:
        return off_ball_movement.decide_AM_off_ball_move(obs)
    elif role == utils.ROLE_CF:
        return off_ball_movement.decide_CF_off_ball_move(obs)
        
    return utils.ACTION_IDLE # Default case

def decide_set_piece_action(obs):
    """Handles actions for specific game modes (set pieces)."""
    game_mode = obs.game_mode
    player_pos = obs.player_position

    # Corner Kick
    if game_mode == utils.GAME_MODE_CORNER:
        if obs.is_ball_owned_by_player():
            return utils.ACTION_HIGH_PASS # Cross the ball
        else: # Other players run into the box
            target_pos = [utils.OPPONENT_PENALTY_BOX_X_MIN + 0.1, 0]
            return utils.get_direction_action(player_pos, target_pos)

    # Goal Kick
    if game_mode == utils.GAME_MODE_GOALKICK:
        if obs.player_role == utils.ROLE_GK:
            return holding_action.decide_holding_action_GK(obs) # Decide long/short pass
        else: # Players get open
            return off_ball_movement.decide_CB_off_ball_move(obs)

    # Free Kick
    if game_mode == utils.GAME_MODE_FREEKICK:
        if obs.is_ball_owned_by_player():
            if player_pos[0] > 0.65: # Close enough to shoot
                return utils.ACTION_SHOT
            return utils.ACTION_HIGH_PASS # Otherwise, cross
        else: # Run into box
            target_pos = [utils.OPPONENT_PENALTY_BOX_X_MIN + 0.1, 0]
            return utils.get_direction_action(player_pos, target_pos)

    # Kick Off
    if game_mode == utils.GAME_MODE_KICKOFF:
        if obs.is_ball_owned_by_player():
            return pass_action.decide_pass_CM_LM_RM_AM(obs) # Simple pass
        else:
            return utils.ACTION_IDLE # Hold position

    # Throw-in
    if game_mode == utils.GAME_MODE_THROWIN:
        if obs.is_ball_owned_by_player():
            return utils.ACTION_SHORT_PASS
        else: # Get open
            return off_ball_movement.decide_LB_RB_off_ball_move(obs)

    # Penalty
    if game_mode == utils.GAME_MODE_PENALTY:
        return utils.ACTION_SHOT if obs.is_ball_owned_by_player() else utils.ACTION_IDLE

    return None # Not a set piece we handle, proceed with normal logic

# --- Main Decision Function ---

def player_action(obs):
    """
    The main entry point for player action decisions.
    It checks game_mode, then if the player has the ball and calls the appropriate handler.
    """
    if obs.game_mode != utils.GAME_MODE_NORMAL:
        set_piece_action = decide_set_piece_action(obs)
        if set_piece_action is not None:
            return set_piece_action

    if obs.is_ball_owned_by_player():
        return decide_on_ball_action(obs)
    else:
        return decide_off_ball_action(obs)

# This dictionary can be used by an external runner to dispatch actions.
# For example: action = player_role_to_action[obs.player_role](obs)
# However, the single entry point `player_action` is cleaner.
player_role_to_action = {
    utils.ROLE_GK: player_action,
    utils.ROLE_CB: player_action,
    utils.ROLE_LB: player_action,
    utils.ROLE_RB: player_action,
    utils.ROLE_DM: player_action,
    utils.ROLE_CM: player_action,
    utils.ROLE_LM: player_action,
    utils.ROLE_RM: player_action,
    utils.ROLE_AM: player_action,
    utils.ROLE_CF: player_action,
} 