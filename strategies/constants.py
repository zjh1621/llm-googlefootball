# strategies/constants.py

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
ACTION_BUILTIN_AI = 19


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

# --- Tactical Configuration ---
# You can modify these settings to change the team's behavior
class TacticalConfig:
    # e.g., '4-4-2', '4-3-3', '3-5-2', '4-2-3-1'
    CURRENT_FORMATION = '4-2-3-1'

    # Goalkeeper style: 'possession' or 'direct'
    GK_STYLE = 'possession'

    # Full-back roles: 'fullback' (defensive) or 'wingback' (attacking)
    LB_ROLE = 'fullback'
    RB_ROLE = 'fullback'

    # Defensive Midfielder role: 'single_pivot' or 'double_pivot'
    DM_ROLE = 'double_pivot'

    # Central Midfielder role: 'box_to_box_in_442' or 'attacking_8_in_433'
    CM_ROLE = 'attacking_8_in_433'

    # Winger roles: 'traditional_midfielder' or 'attacking_winger'
    LM_ROLE = 'attacking_winger'
    RM_ROLE = 'attacking_winger'

    # Central Forward role: 'pivot_striker', 'poacher', or 'false_nine'
    CF_ROLE = 'pivot_striker'

# --- Formation Definitions ---
FORMATION_POSITIONS = {
    '4-4-2': {
        ROLE_LB: [-0.6, -0.3], ROLE_RB: [-0.6, 0.3],
        ROLE_CB: [-0.7, -0.15],
        ROLE_LM: [-0.1, -0.3], ROLE_RM: [-0.1, 0.3],
        ROLE_CM: [-0.2, -0.1],
        ROLE_CF: [0.7, -0.1],
    },
    '4-2-3-1': {
        ROLE_LB: [-0.6, -0.35], ROLE_RB: [-0.6, 0.35],
        ROLE_CB: [-0.7, -0.15],
        ROLE_DM: [-0.4, -0.1],
        ROLE_LM: [0.2, -0.3], ROLE_RM: [0.2, 0.3],
        ROLE_AM: [0.3, 0.0],
        ROLE_CF: [0.7, 0.0],
    },
    '4-3-3': {
        ROLE_LB: [-0.6, -0.35], ROLE_RB: [-0.6, 0.35],
        ROLE_CB: [-0.7, -0.15],
        ROLE_DM: [-0.4, 0.0],
        ROLE_CM: [-0.1, -0.2],
        ROLE_LM: [0.5, -0.3], # Left Winger
        ROLE_RM: [0.5, 0.3],  # Right Winger
        ROLE_CF: [0.7, 0.0],
    }
}
# Roles that are paired and need their Y-position mirrored
PAIRED_ROLES = {ROLE_CB, ROLE_CM, ROLE_DM, ROLE_CF}

# --- Field Constants ---
FIELD_X_LIMITS = (-1.0, 1.0)
FIELD_Y_LIMITS = (-0.42, 0.42)
GOAL_Y_LIMITS = (-0.044, 0.044) 