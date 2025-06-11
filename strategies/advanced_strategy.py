# 
# strategies/advanced_strategy.py
from .player_roles_6_11 import *
import gfootball.env as football_env # 假设你需要访问角色常量

def advanced_strategy(obs_wrapper):
    actions = []
    # obs_wrapper.player_observations 是一个列表，包含每个球员的 PlayerObservationWrapper 实例
    for player_obs in obs_wrapper.player_observations:
        # 获取当前控制球员的角色 ID
        role = player_obs.player_role
        
        # 从 player_role_to_action 字典中获取对应的动作函数
        action_function = player_role_to_action.get(role)
        
        # 如果找到了对应的函数，则调用它来获取动作；否则，使用默认动作
        if action_function:
            action = action_function(player_obs)
        else:
            action = ACTION_IDLE  # 如果角色未在字典中定义，则执行默认的"空闲"动作

        actions.append(action)
    return actions