import numpy as np


def get_movement_action(current_pos, target_pos):
    direction = target_pos - current_pos
    angle = np.arctan2(direction[1], direction[0])

    if -np.pi / 8 <= angle < np.pi / 8:
        return 5  # action_right
    elif np.pi / 8 <= angle < 3 * np.pi / 8:
        return 4  # action_top_right
    elif 3 * np.pi / 8 <= angle < 5 * np.pi / 8:
        return 3  # action_top
    elif 5 * np.pi / 8 <= angle < 7 * np.pi / 8:
        return 2  # action_top_left
    elif 7 * np.pi / 8 <= angle or angle < -7 * np.pi / 8:
        return 1  # action_left
    elif -7 * np.pi / 8 <= angle < -5 * np.pi / 8:
        return 8  # action_bottom_left
    elif -5 * np.pi / 8 <= angle < -3 * np.pi / 8:
        return 7  # action_bottom
    elif -3 * np.pi / 8 <= angle < -np.pi / 8:
        return 6  # action_bottom_right
    else:
        return 0  # action_idle