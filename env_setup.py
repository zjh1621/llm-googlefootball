import gfootball.env as football_env

def create_football_env(formation='4-3-3'):
    """
    Creates the Google Football environment with a customizable formation.
    
    Args:
        formation (str): The formation for the left team (e.g., '4-4-2', '4-3-3').
    """
    env = football_env.create_environment(
        env_name='11_vs_11_easy_stochastic',
        stacked=False,
        representation='raw',
        rewards='scoring',
        write_goal_dumps=False,
        write_full_episode_dumps=False,
        write_video=False,
        logdir="dump",
        render=True,
        number_of_left_players_agent_controls=11,
        number_of_right_players_agent_controls=0,
        other_config_options={
            'action_set': 'full',
            'formations': {
                'hometeam': formation,
                'awayteam': '4-4-2'  # Keep the opponent's formation fixed for now
            }
        }
    )
    return env