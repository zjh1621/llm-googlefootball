### **Goalkeeper (Role ID: 0)**

```
function goalkeeper_actions(obs):
```

代码段

```
// Role: Prevent goals and distribute the ball from the back.

switch (obs.game_mode):
    case KickOff:
        return move_to(center_of_goal_area) // Stay in position
    case Corner, FreeKick, Penalty: // Defensive set pieces
        return move_to(optimal_position_on_goal_line_based_on_ball_position)
    case Normal:
        // IF I have the ball
        if obs.ball_owned_player == my_index AND obs.ball_owned_team == 0:
            // Find a safe pass or clear the ball
            teammate_to_pass = get_best_pass_target()
            if teammate_to_pass is far_and_open:
                return action_high_pass
            else:
                return action_long_pass // Safest option is to clear the danger
        
        // IF my team has the ball (but not me)
        elif obs.ball_owned_team == 0:
            // Act as a safe passing option
            return move_to(edge_of_penalty_box)

        // IF the opponent has the ball
        elif obs.ball_owned_team == 1:
            // If ball is far, stay central in the goal
            if distance(my_position, obs.ball_position) > 0.4:
                return move_to(center_of_goal_area)
            // If ball is close, adjust to block the shooting angle
            else:
                return move_to(position_between_ball_and_center_of_goal)
        
        // IF the ball is free
        else:
            // Only go for the ball if it's inside the penalty box and safe to get
            if is_ball_in_my_penalty_box and distance(my_position, obs.ball_position) < 0.15:
                return move_towards(obs.ball_position)
            else:
                return move_to(center_of_goal_area)
```

------

### **Centre Back (Role ID: 1)**

```
function centre_back_actions(obs):
```

代码段

```
// Role: Defend the central area, mark opposing strikers, and clear the ball.

switch (obs.game_mode):
    case KickOff:
        return move_to(my_defensive_position_in_own_half)
    case Corner (Attacking):
        return stay_back_near_halfway_line // Prevent counter-attacks
    case Corner (Defensive):
        return mark_closest_opponent_in_penalty_box
    case Normal:
        // IF I have the ball
        if obs.ball_owned_player == my_index AND obs.ball_owned_team == 0:
            // Avoid risks. Pass to a midfielder or clear it.
            teammate_to_pass = find_teammate_in_midfield()
            if teammate_to_pass:
                return action_short_pass
            else:
                return action_long_pass

        // IF my team has the ball
        elif obs.ball_owned_team == 0:
            // Move up with the play but maintain the defensive line, staying behind the ball
            return move_to(defensive_position_behind_ball)
        
        // IF the opponent has the ball
        elif obs.ball_owned_team == 1:
            // Primary job: defend. Mark the striker and block paths to goal.
            if distance(my_position, obs.ball_position) < 0.1:
                return press_ball_carrier() // Close down attacker
            else:
                return move_to(position_between_opponent_striker_and_goal)
        
        // IF the ball is free
        else:
            // If the ball is in my half, I must try to win it
            if obs.ball_position.x < 0:
                return move_towards(obs.ball_position)
            else:
                return move_to(my_defensive_position)
```

------

### **Left Back / Right Back (Role ID: 2 & 3)**

`function left_back_actions(obs):` // (Right back logic is mirrored)

代码段

```
// Role: Defend the flanks and support attacks with overlapping runs.

switch (obs.game_mode):
    case Normal:
        // IF I have the ball
        if obs.ball_owned_player == my_index AND obs.ball_owned_team == 0:
            // Look to pass up the wing to the midfielder or forward
            teammate_to_pass = find_teammate_on_my_flank()
            if teammate_to_pass:
                return action_short_pass
            else:
                // If no pass is on, dribble forward along the touchline
                return action_dribble + move_forward_on_flank()
        
        // IF my team has the ball
        elif obs.ball_owned_team == 0:
            // If the ball is ahead of me on my flank, make an overlapping run
            if obs.ball_position.x > my_position.x:
                return action_sprint + move_forward_on_flank_into_open_space()
            else:
                // Provide a safe passing option
                return move_to(support_position_on_flank)

        // IF the opponent has the ball
        elif obs.ball_owned_team == 1:
            // My priority is to get back and defend my flank.
            return action_sprint + move_to(my_defensive_flank_position)
        
        // IF the ball is free
        else:
            // If ball is on my side of the pitch, try to win it.
            if is_ball_on_my_flank(obs.ball_position):
                return move_towards(obs.ball_position)
            else:
                return move_to(my_defensive_flank_position)
```

------

### **Defence Midfielder (Role ID: 4)**

```
function defence_midfielder_actions(obs):
```

代码段

```
// Role: Shield the defense, win the ball in midfield, and start attacks with simple passes.

switch (obs.game_mode):
    case Normal:
        // IF I have the ball
        if obs.ball_owned_player == my_index AND obs.ball_owned_team == 0:
            // Distribute to a more creative player.
            teammate_to_pass = find_open_central_or_attacking_midfielder()
            return action_short_pass

        // IF my team has the ball
        elif obs.ball_owned_team == 0:
            // Stay in the central space between defense and midfield, available for a pass.
            return move_to(central_position_behind_ball)

        // IF the opponent has the ball
        elif obs.ball_owned_team == 1:
            // Aggressively press the opponent's midfielder who has the ball.
            return move_towards(obs.ball_position) + action_sprint

        // IF the ball is free
        else:
            // Contest any loose ball in the center of the park.
            if distance(my_position, obs.ball_position) < 0.3:
                return move_towards(obs.ball_position)
            else:
                return move_to(central_defensive_midfield_position)
```

------

### **Central Midfielder (Role ID: 5)**

```
function central_midfielder_actions(obs):
```

代码段

```
// Role: The engine room. Contribute to both defense and attack, linking up play.

switch (obs.game_mode):
    case Normal:
        // IF I have the ball
        if obs.ball_owned_player == my_index AND obs.ball_owned_team == 0:
            // Look for a forward pass to an attacker
            teammate_to_pass = find_attacking_midfielder_or_forward()
            if teammate_to_pass:
                return action_short_pass // A through-ball
            else:
                // If no forward pass, dribble to create space
                return action_dribble + move_towards(opponent_goal)

        // IF my team has the ball
        elif obs.ball_owned_team == 0:
            // Move into open space to be a passing option and support the attack
            return move_to(find_open_space_in_midfield())

        // IF the opponent has the ball
        elif obs.ball_owned_team == 1:
            // Help the DM win the ball back.
            return move_to(position_between_ball_and_my_goal)
        
        // IF the ball is free
        else:
            // Be proactive in winning loose balls in the midfield.
            return move_towards(obs.ball_position)
```

------

### **Left / Right Midfielder (Role ID: 6 & 7)**

`function left_midfielder_actions(obs):` // (Right midfielder logic is mirrored)

代码段

```
// Role: Provide width in attack, cross the ball, and track back to help defend.

switch (obs.game_mode):
    case Normal:
        // IF I have the ball
        if obs.ball_owned_player == my_index AND obs.ball_owned_team == 0:
            // If in a good crossing position (wide and in opponent's half)
            if my_position.x > 0.5 and is_on_my_flank(my_position):
                return action_high_pass // Cross the ball
            else:
                // Dribble down the wing towards the opponent's corner
                return action_sprint + action_dribble + move_forward_on_flank()

        // IF my team has the ball
        elif obs.ball_owned_team == 0:
            // Stay wide and make runs behind the opponent's defense
            return move_to(advanced_position_on_my_flank())

        // IF the opponent has the ball
        elif obs.ball_owned_team == 1:
            // Track back to help the full-back
            return move_to(defensive_midfield_position_on_my_flank)

        // IF the ball is free
        else:
            // If the ball is on my flank, go for it.
            if is_ball_on_my_flank(obs.ball_position):
                return move_towards(obs.ball_position)
            else:
                return move_to(my_base_position_on_flank)
```

------

### **Attack Midfielder (Role ID: 8)**

```
function attack_midfielder_actions(obs):
```

代码段

```
// Role: The playmaker. Create chances, shoot from distance, and find the killer pass.

switch (obs.game_mode):
    case Normal:
        // IF I have the ball
        if obs.ball_owned_player == my_index AND obs.ball_owned_team == 0:
            // If in shooting range, take the shot
            if distance_to_opponent_goal < 0.4 and angle_is_good:
                return action_shot
            else:
                // Look for a through ball to the striker
                teammate_to_pass = find_central_forward()
                if teammate_to_pass:
                    return action_short_pass
                else:
                    return action_dribble + move_towards(opponent_goal)
        
        // IF my team has the ball
        elif obs.ball_owned_team == 0:
            // Find pockets of space between opponent's defense and midfield
            return move_to(find_space_in_attacking_third())

        // IF the opponent has the ball
        elif obs.ball_owned_team == 1:
            // Be the first line of the press. Harass opponent's deep-lying midfielders.
            return press_opponent_ball_carrier_in_their_half()

        // IF the ball is free
        else:
            // Try to win the ball high up the pitch
            if obs.ball_position.x > 0:
                return move_towards(obs.ball_position)
            else:
                return move_to(base_attacking_midfield_position)
```

------

### **Central Forward (Role ID: 9)**

```
function central_forward_actions(obs):
```

代码段

```
// Role: Score goals. Be the focal point of the attack and press opposing defenders.

switch (obs.game_mode):
    case KickOff:
        // If it's our kickoff, maybe try a direct shot if that's a viable strategy.
        // Otherwise, pass back and start the play.
        return action_short_pass_to_midfielder
    case Normal:
        // IF I have the ball
        if obs.ball_owned_player == my_index AND obs.ball_owned_team == 0:
            // If I can shoot, SHOOT!
            if distance_to_opponent_goal < 0.3:
                return action_shot
            else:
                // Get into a better shooting position
                return action_dribble + move_towards(center_of_opponent_goal)

        // IF my team has the ball
        elif obs.ball_owned_team == 0:
            // Make runs to get behind the defense. Stay on the shoulder of the last defender.
            return move_to(find_space_behind_opponent_defense_line)

        // IF the opponent has the ball
        elif obs.ball_owned_team == 1:
            // Press the defender who has the ball to force a mistake
            opponent_to_press = find_opponent_defender_with_ball()
            if opponent_to_press:
                return move_towards(opponent_to_press_position)
            else:
                return move_to(central_position_to_cut_passing_lanes)

        // IF the ball is free
        else:
            // If the ball is in the attacking half, fight for it.
            if obs.ball_position.x > 0:
                return move_towards(obs.ball_position)
            else:
                // Don't track back too far, stay ready for a counter
                return move_to(halfway_line)
```