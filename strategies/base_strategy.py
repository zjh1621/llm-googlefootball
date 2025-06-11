class BaseStrategy:
    def __init__(self):
        pass

    def get_player_action(self, player_obs, obs_wrapper):
        raise NotImplementedError("Subclasses must implement this method")