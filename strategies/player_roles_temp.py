import math
import numpy as np

# Action constants 
ACTION_IDLE = 0
ACTION_LEFT = 1
ACTION_TOP_LEFT = 2
ACTION_TOP = 3
ACTION_TOP_RIGHT = 4
ACTION_RIGHT = 5
ACTION_BOTTOM_RIGHT = 6
ACTION_BOTTOM = 7
ACTION_BOTTOM_LEFT = 8
ACTION_LONG_PASS = 9
ACTION_HIGH_PASS = 10
ACTION_SHORT_PASS = 11
ACTION_SHOT = 12
ACTION_SPRINT = 13
ACTION_RELEASE_DIRECTION = 14
ACTION_RELEASE_SPRINT = 15
ACTION_SLIDING = 16
ACTION_DRIBBLE = 17
ACTION_RELEASE_DRIBBLE = 18

# Role constants 
ROLE_GK = 0
ROLE_CB = 1
ROLE_LB = 2
ROLE_RB = 3
ROLE_DM = 4
ROLE_CM = 5
ROLE_LM = 6
ROLE_RM = 7
ROLE_AM = 8
ROLE_CF = 9

# Indices for sticky actions 
STICKY_LEFT = 0
STICKY_TOP_LEFT = 1
STICKY_TOP = 2
STICKY_TOP_RIGHT = 3
STICKY_RIGHT = 4
STICKY_BOTTOM_RIGHT = 5
STICKY_BOTTOM = 6
STICKY_BOTTOM_LEFT = 7
STICKY_SPRINT = 8
STICKY_DRIBBLE = 9



# --- Role Implementations ---

def goalkeeper_actions(obs):
    pass

def centre_back_actions(obs):
    pass

def left_back_actions(obs):
    pass

def right_back_actions(obs):
    pass

def defence_midfielder_actions(obs):
    pass

def central_midfielder_actions(obs):
    pass

def left_midfielder_actions(obs):
    pass

def right_midfielder_actions(obs):
    pass

def attack_midfielder_actions(obs):
    pass

def central_forward_actions(obs):
    pass

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