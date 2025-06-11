import logging
from concurrent.futures import ProcessPoolExecutor

from env_setup import create_football_env
from wrappers import ObservationWrapper, ActionWrapper
from strategies.advanced_strategy import advanced_strategy

def run_match():
    env = create_football_env()
    action_wrapper = ActionWrapper(env)
    observations = env.reset()
    obs_wrapper = ObservationWrapper(observations)
    left_reward = right_reward = 0
    while True:
        actions = advanced_strategy(obs_wrapper)
        observations, rewards, dones, infos = action_wrapper.step(actions)
        obs_wrapper = ObservationWrapper(observations)
        if rewards[0] == 1:
            left_reward += 1
        elif rewards[0] == -1:
            right_reward += 1
        if dones:
            break
    return left_reward, right_reward

if __name__ == '__main__':
    # Suppress INFO level logs from gfootball library
    football_logger = logging.getLogger('gfootball')
    football_logger.setLevel(logging.WARNING)
    # Run the main function in parallel using ProcessPoolExecutor
    with ProcessPoolExecutor() as executor:
        futures = [executor.submit(run_match) for _ in range(10)]
        for future in futures:
            left_reward, right_reward = future.result()
            print(f"left_reward:{left_reward}, right_reward:{right_reward}")