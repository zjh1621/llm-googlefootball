# Player Roles Advanced Decision Logic (Pro-Level Tactics)

本文档中的伪代码在之前的基础上进行了战术升级，旨在模拟职业足球比赛中更复杂和动态的决策。新增的逻辑重点关注攻防转换、空间利用和根据比赛状态调整策略。

### **通用战术思路 (全局决策覆盖)**

在每个球员决策之前，应先考虑当前的比赛宏观状态。这可以作为一个高优先级的决策覆盖层。

代码段

```
// 宏观战术决策
IF (我方领先一球 AND 比赛剩余时间 < 15%) THEN
    // **战术: 保住胜果 (Parking the Bus/Control Possession)**
    // 控球为主，降低风险，向角旗区带球消耗时间
    set_global_tactic("PROTECT_LEAD") 
ELSE IF (我方落后 AND 比赛剩余时间 < 20%) THEN
    // **战术: 全力进攻 (All-out Attack)**
    // 后卫线前压，增加前场人数，更激进地射门和传球
    set_global_tactic("ALL_OUT_ATTACK")
ELSE
    // 常规战术
    set_global_tactic("NORMAL")
END IF
```

------

### `goalkeeper_actions(obs)`

**战术角色**: 门将不仅是防守的最后一道屏障，也是进攻的发起者。决策需根据对手的压迫程度来选择长传或短传，以规避风险并发起进攻。

代码段

```
// ... (获取 my_pos, ball_pos, i_have_ball 等变量)

IF i_have_ball THEN
    // 检查我方后卫是否被对手高位逼抢
    is_defense_under_pressure = check_opponent_pressure_on_teammates(roles=[CB, LB, RB], pressure_radius=0.15)

    IF is_defense_under_pressure OR global_tactic is "ALL_OUT_ATTACK" THEN
        // **战术: 长传越过对手逼抢线**
        // 寻找中锋(CF)或边锋(LM/RM)作为长传目标，直接发动进攻
        target_teammate = find_best_long_pass_target(roles=[CF, LM, RM])
        set_pass_direction(target_teammate.pos)
        RETURN ACTION_LONG_PASS
    ELSE
        // **战术: 短传组织**
        // 安全地将球传给最近且最开阔的后卫
        open_teammate = find_open_teammate(obs, min_dist_from_opp=0.1)
        IF open_teammate is found THEN
            set_pass_direction(open_teammate.pos)
            RETURN ACTION_SHORT_PASS
        ELSE
             // 如果短传也不安全，则大脚解围
            RETURN ACTION_LONG_PASS
        END IF
    END IF
ELSE // 没有球权
    // ... (防守逻辑与之前版本类似，核心是保持在球和球门之间)
    // 根据球的位置微调站位，封锁角度
    target_pos_y = map_y_position(ball_pos[1], goal_span_y)
    target_pos = [my_pos[0], target_pos_y]
    RETURN move_towards(my_pos, target_pos)
END IF
```

------

### `centre_back_actions(obs)`

**战术角色**: 防守核心和后场组织者。在无压迫时耐心组织，与队友进行横向调度，寻找向前的最佳出球线路。

代码段

```
// ... (获取 my_pos, ball_pos, i_have_ball 等变量)

IF i_have_ball THEN
    // 如果身前没有好的出球点，或者全局战术要求控球
    IF (not find_clear_forward_pass(roles=[DM, CM, AM])) OR (global_tactic is "PROTECT_LEAD") THEN
        // **战术: 后场控球/横向调度**
        // 与另一名中后卫或边后卫进行安全传球，吸引对手移动，创造空间
        safe_teammate = find_safest_teammate(roles=[CB, LB, RB])
        set_pass_direction(safe_teammate.pos)
        RETURN ACTION_SHORT_PASS
    ELSE
        // **战術: 向前出球**
        // 寻找防守型中场(DM)或中前卫(CM)作为第一出球点
        open_midfielder = find_open_teammate(obs, roles=[DM, CM])
        set_pass_direction(open_midfielder.pos)
        RETURN ACTION_SHORT_PASS
    END IF
ELSE // 没有球权
    // **战术: 保持防线完整性**
    // 除非进攻球员已进入直接威胁区域，否则优先保持阵型，而不是贸然上抢
    opponent_with_ball = obs.right_team[obs.ball_owned_player]
    IF (opponent_with_ball.pos[0] < -0.4 AND distance(my_pos, opponent_with_ball.pos) < 0.1) THEN
        // 只有当对手带球深入危险区域时才上抢
        RETURN move_towards(my_pos, opponent_with_ball.pos)
    ELSE
        // 否则，保持防守位置，与防线平齐
        RETURN move_towards(my_pos, [defensive_line_x, my_pos[1]])
    END IF
END IF
```

------

### `left_back_actions(obs)` & `right_back_actions(obs)`

**战术角色**: 现代边后卫。防守时保护边路，进攻时提供宽度，并根据边前卫的跑位决定是“下底传中”还是“套边插上”。

代码段

```
// ... (获取变量, my_flank_y 是该边后卫所在侧的y坐标)
winger_on_my_side = get_teammate_by_role(LM or RM) // 获取同侧的边前卫

IF i_have_ball THEN
    // 传给同侧边前卫或中场
    // ... (逻辑与之前类似)

ELSE IF obs.ball_owned_team == 0 AND obs.left_team[winger_on_my_side.id].has_ball THEN
    // **战术: 套边插上 (Overlapping Run)**
    // 如果我方边前卫拿球并有内切趋势，则从他身后高速插上，创造2打1机会
    IF winger_on_my_side.is_dribbling_inward() THEN
        sprint_if_not_sprinting(obs)
        overlap_pos = [winger_on_my_side.pos[0] + 0.1, my_flank_y]
        RETURN move_towards(my_pos, overlap_pos)
    END IF

ELSE // 防守逻辑
    // **战术: 内收协防 (Tuck In)**
    // 当球在另一侧时，向中路收缩，保护中后卫身旁的空当，防止对手直塞
    IF ball_pos.side is OPPOSITE_SIDE THEN
        cover_pos = [defensive_pos_x, my_pos[1] / 2] // 向中路收缩
        RETURN move_towards(my_pos, cover_pos)
    ELSE
        // 在自己的一侧防守
        RETURN move_towards(my_pos, ball_pos)
    END IF
END IF
```

------

### `defence_midfielder_actions(obs)`

**战术角色**: 防守屏障和节拍器。主要职责是破坏对手进攻组织，并由守转攻时进行长传调度（转移球）。

代码段

```
// ...

IF i_have_ball THEN
    // **战术: 调度转移 (Switch Play)**
    // 观察球场两侧，如果一侧人员密集，则长传转移到空旷的另一侧
    IF is_flank_congested(my_pos.side) THEN
        weak_side_winger = find_teammate_on_opposite_flank(roles=[LM, RM])
        set_pass_direction(weak_side_winger.pos)
        RETURN ACTION_LONG_PASS
    ELSE
        // 安全地传给身前的中场
        open_midfielder = find_open_teammate(obs, roles=[CM, AM])
        set_pass_direction(open_midfielder.pos)
        RETURN ACTION_SHORT_PASS
    END IF
ELSE // 没有球权
    // **战术: 切断传球路线 (Cut Passing Lanes)**
    // 优先移动到对手持球人与对方前锋(CF, AM)之间，破坏他们的联系
    opponent_forward = find_most_dangerous_opponent()
    opponent_ball_carrier = obs.right_team[obs.ball_owned_player]
    intercept_pos = calculate_midpoint(opponent_ball_carrier.pos, opponent_forward.pos)
    RETURN move_towards(my_pos, intercept_pos)
END IF
```

------

### `central_midfielder_actions(obs)`

**战术角色**: B2B中场（Box-to-Box）。攻防俱佳，防守时协助DM，进攻时积极前插，利用后排插上的时机完成射门或创造机会。

代码段

```
// ...

IF i_have_ball THEN
    // ... (逻辑与之前类似，寻找向前传球或远射机会)

ELSE IF obs.ball_owned_team == 0 AND ball_pos[0] > 0.3 THEN
    // **战术: 后排插上 (Late Run into the Box)**
    // 当进攻发展到对方三十米区域时，从中场开始无球冲刺，进入禁区抢点
    sprint_if_not_sprinting(obs)
    run_target = [opponent_goal_pos[0] - 0.2, 0] // 目标：点球点附近
    RETURN move_towards(my_pos, run_target)
ELSE IF obs.ball_owned_team == 1 THEN
    // **战术: 回防支援**
    // 积极回防，与DM组成第一道防线
    defensive_pos = [central_pivot_pos[0] - 0.1, my_pos[1]]
    RETURN move_towards(my_pos, defensive_pos)
END IF
```

------

### `attack_midfielder_actions(obs)`

**战术角色**: 机会创造者（Playmaker）。在对手防线和中场间的“十号位”区域活动，寻求致命直塞或与前锋进行“二过一”配合。

代码段

```
// ...

IF i_have_ball THEN
    // **战术: 直塞球 (Through Ball)**
    // 寻找前锋(CF)的跑动路线，并预判传球，将球送到他前方的空当
    cf_player = get_teammate_by_role(CF)
    IF cf_player.is_making_forward_run() THEN
        through_ball_target = cf_player.pos + cf_player.direction * 5 // 传一个提前量
        set_pass_direction(through_ball_target)
        RETURN ACTION_LONG_PASS // 用长传模拟直塞
    ELSE
        // 其他情况，可以射门或短传
        IF distance_to_goal < 0.35 THEN RETURN ACTION_SHOT
    END IF
ELSE IF (obs.ball_owned_team == 0 AND obs.ball_owned_player == CF_ID) THEN
    // **战术: 二过一配合 (Give-and-Go)**
    // 当球传给中锋后，立即前插准备接应回传球
    sprint_if_not_sprinting(obs)
    RETURN move_towards(my_pos, opponent_goal_pos)
END IF
```

------

### `central_forward_actions(obs)`

**战术角色**: 进攻终结者和支点。首要任务是射门，但在背身拿球时，也能作为支点，将球回做给后排插上的队友。

代码段

```
// ...

IF i_have_ball THEN
    // **战术: 支点作用 (Hold-up Play)**
    // 如果背对球门且被紧逼，难以转身射门
    IF is_facing_backwards() AND is_under_pressure() THEN
        // 寻找插上的中场队友(AM, CM)
        onrushing_midfielder = find_onrushing_teammate(roles=[AM, CM])
        IF onrushing_midfielder is found THEN
            // 将球回做给他们
            set_pass_direction(onrushing_midfielder.pos)
            RETURN ACTION_SHORT_PASS
        END IF
    END IF
    
    // **首要任务: 射门**
    // 只要有机会，就果断射门
    IF my_pos[0] > 0.6 THEN
        RETURN ACTION_SHOT
    ELSE
        // 带球靠近球门
        sprint_if_not_sprinting(obs)
        RETURN move_towards(my_pos, opponent_goal_pos)
    END IF
ELSE // 没有球权
    // **战术: 拉扯空间 (Stretching the Defense)**
    // 在对方中后卫和边后卫之间的空隙（肋部）跑动，拉扯对方防线，为队友创造空间
    run_target = [opponent_defensive_line_x + 0.1, flank_y] // 在肋部活动
    RETURN move_towards(my_pos, run_target)
END IF
```