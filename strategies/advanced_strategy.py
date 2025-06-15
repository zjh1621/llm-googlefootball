# 
# strategies/advanced_strategy.py
from .player_roles_6_13 import player_role_to_action
from wrappers import ObservationWrapper

# Action constant for fallback
ACTION_IDLE = 0

def advanced_strategy(obs_wrapper: ObservationWrapper):
    """
    Main strategy function that assigns an action to each of the 11 controlled players.
    """
    actions = []
    
    # obs_wrapper.player_observations contains an observation for each of our 11 players
    for obs in obs_wrapper.player_observations:
        player_role = obs.player_role
        
        # Look up the appropriate action function based on the player's role
        action_function = player_role_to_action.get(player_role)
        
        if action_function:
            # Call the role-specific function to get an action
            action = action_function(obs)
            actions.append(action)
        else:
            # If the role is somehow not found, default to doing nothing
            actions.append(ACTION_IDLE)
            
    return actions