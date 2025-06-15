# 谷歌足球环境中守门员（Goalkeeper）的决策伪代码

本文档为谷歌足球环境中的守门员（Goalkeeper, GK, `role_id=0`）提供了一套决策树伪代码。该伪代码旨在根据当前的战术设定、比赛场景 (`game_mode`) 以及实时的观测数据 (`observation`)，为守门员选择最合适的动作 (`action`)。

## 一、 核心决策原则

在深入伪代码细节之前，我们先提炼出守门员决策的核心原则，这些原则贯穿所有战术和场景：

1. **安全第一 (Safety First)**：守门员的首要任务是保护球门。在任何情况下，避免不必要的风险，优先选择最能保障球门安全的行动。
2. **位置是关键 (Positioning is Key)**：在无球状态下，守门员的大部分决策都与位置选择有关。一个好的站位可以极大简化后续的扑救和拦截动作。
3. **进攻的发起者 (Initiator of Attack)**：在现代足球中，守门员是进攻的第一环。拿到球后，需要根据战术要求和场上局势，快速、准确地将球传出，发动进攻。
4. **场景适应性 (Context-Aware)**：守门员的行为必须根据当前的 `game_mode` 做出巨大调整。例如，在角球（Corner）时的站位和在点球（Penalty）时的策略是完全不同的。

## 二、 战术适应性说明

根据《球员角色在不同战术下的职责划分.md》文档，守门员在各种主流阵型（4-4-2, 4-3-3, 3-5-2, 4-2-3-1）中的核心职责是相似的，但侧重点略有不同：

- **通用职责**：保护球门、指挥防线、处理回传球、发动进攻。
- **战术微调**：
  - 在 **控球型战术（如部分4-3-3）** 中，更强调守门员的**脚下技术**和**短传**能力，作为后场稳定的出球点。
  - 在 **防守反击或长传冲吊战术** 中，更强调守门员的**长传**能力，要求其能直接找到前场攻击手。

为了在伪代码中体现这一点，我们将引入一个假设的变量 `CURRENT_TACTIC_STYLE`，它可以是 `'possession'` (控球) 或 `'direct'` (直接)。

## 三、 伪代码

```
// =================================================================
// Goalkeeper (GK) Decision Logic
// =================================================================

// -----------------------------------------------------------------
// 主决策函数
// -----------------------------------------------------------------
FUNCTION Goalkeeper_Main_Decision(observation, my_index):
    // 检查我（守门员）是否为当前受控球员
    IF observation.active == my_index THEN
        // 检查我是否持球
        IF observation.ball_owned_player == my_index THEN
            RETURN Handle_Ball_Possession(observation)
        ELSE
            RETURN Handle_Without_Ball(observation)
        END IF
    ELSE
        // 如果不是受控球员，则执行内置AI
        RETURN action_builtin_ai
    END IF
END FUNCTION


// -----------------------------------------------------------------
// 1. 持球状态下的决策
// -----------------------------------------------------------------
FUNCTION Handle_Ball_Possession(observation):
    // 检查是否有对方球员逼近造成威胁
    nearest_opponent_dist = find_nearest_opponent_distance(observation.right_team)
    
    // 如果受到紧逼，必须立即出球
    IF nearest_opponent_dist < DANGER_ZONE_RADIUS THEN
        // 优先选择长传或高球解围
        RETURN action_high_pass
    ELSE
        // 在安全情况下，根据战术风格和场上情况做决策
        
        // 控球战术：优先寻找安全的短传机会
        IF CURRENT_TACTIC_STYLE == 'possession' THEN
            safe_teammate = find_safest_teammate_for_pass(observation.left_team, 'short')
            IF safe_teammate IS NOT NULL THEN
                // 朝向该队友并短传
                look_towards(safe_teammate.position)
                RETURN action_short_pass
            END IF
        END IF

        // 直接战术或短传不安全时：尝试长传
        forward_teammate = find_best_teammate_for_pass(observation.left_team, 'long')
        IF forward_teammate IS NOT NULL THEN
            look_towards(forward_teammate.position)
            RETURN action_long_pass
        ELSE
            // 如果没有好的传球目标，向边路大脚解围
            RETURN action_high_pass
        END IF
    END IF
END FUNCTION


// -----------------------------------------------------------------
// 2. 无球状态下的决策
// -----------------------------------------------------------------
FUNCTION Handle_Without_Ball(observation):
    // 根据比赛模式（game_mode）进行决策
    SWITCH observation.game_mode:
        CASE e_GameMode_Normal:
            RETURN Handle_Normal_Play(observation)
        
        CASE e_GameMode_KickOff:
            // 开球时，保持在球门线上中心位置
            move_to(MY_GOAL_LINE_CENTER)
            RETURN action_idle

        CASE e_GameMode_GoalKick:
            // 如果是我方球门球，我将是持球者，此逻辑由 Handle_Ball_Possession 处理
            // 如果是对方球门球，保持警惕
            move_to(MY_GOAL_LINE_CENTER)
            RETURN action_idle
            
        CASE e_GameMode_FreeKick:
            RETURN Handle_FreeKick(observation)
            
        CASE e_GameMode_Corner:
            RETURN Handle_Corner(observation)

        CASE e_GameMode_ThrowIn:
            RETURN Handle_ThrowIn(observation)

        CASE e_GameMode_Penalty:
            // 如果是我方点球，无事可做
            // 如果是对方点球
            IF is_opponent_penalty(observation) THEN
                 // 在罚球瞬间随机选择一个方向扑救
                 // 这是简化策略，更高级的可以分析对手习惯
                 RETURN CHOOSE_RANDOMLY(action_left, action_right, action_idle)
            ELSE
                 RETURN action_idle
            END IF
            
        DEFAULT:
            RETURN action_idle
    END SWITCH
END FUNCTION


// -----------------------------------------------------------------
// 2.1. 细分场景：常规比赛 (Normal Play)
// -----------------------------------------------------------------
FUNCTION Handle_Normal_Play(observation):
    ball_pos = observation.ball
    
    // CASE A: 对方持球
    IF observation.ball_owned_team == OPPONENT_TEAM THEN
        // 如果球在禁区附近或内部，进入战斗状态
        IF is_ball_in_my_penalty_area(ball_pos) OR is_ball_near_my_penalty_area(ball_pos) THEN
            // 移动到球和球门中心的连线上，准备扑救
            target_pos = get_position_to_block_shot(ball_pos, MY_GOAL_CENTER)
            move_to(target_pos)
            
            // 如果判断对方即将射门，可以尝试滑铲封堵（高风险高回报）
            IF opponent_is_preparing_shot(observation) THEN
                RETURN action_sliding
            END IF
            RETURN get_move_action_towards(target_pos) // 返回移动指令
        ELSE
            // 球在远处，调整基础站位
            // 站位在球与球门柱形成的夹角平分线上，稍微靠前
            optimal_pos = get_optimal_default_position(ball_pos)
            move_to(optimal_pos)
            RETURN get_move_action_towards(optimal_pos)
        END IF

    // CASE B: 我方持球
    ELSE IF observation.ball_owned_team == MY_TEAM THEN
        // 稍微前移，为队友提供一个安全的回传点
        // 但要确保始终在禁区内
        safe_passback_pos = find_safe_passback_position()
        move_to(safe_passback_pos)
        RETURN get_move_action_towards(safe_passback_pos)
        
    // CASE C: 无人持球 (Loose Ball)
    ELSE
        // 如果球在禁区内且无人控制，并且我距离最近
        IF is_ball_in_my_penalty_area(ball_pos) AND i_am_closest_to_ball(observation) THEN
            // 冲刺去拿球
            run_towards(ball_pos)
            RETURN action_sprint
        ELSE
            // 否则，回归基础防守站位
            optimal_pos = get_optimal_default_position(ball_pos)
            move_to(optimal_pos)
            RETURN get_move_action_towards(optimal_pos)
        END IF
    END IF
END FUNCTION

// -----------------------------------------------------------------
// 2.2. 细分场景：任意球 (Free Kick)
// -----------------------------------------------------------------
FUNCTION Handle_FreeKick(observation):
    // 如果是对方在我方半场的危险任意球
    IF is_opponent_dangerous_freekick(observation) THEN
        // 根据人墙位置和球的位置，选择最佳站位封堵角度
        target_pos = calculate_freekick_save_position(observation)
        move_to(target_pos)
        RETURN get_move_action_towards(target_pos)
    ELSE
        // 其他情况，保持中心站位
        move_to(MY_GOAL_LINE_CENTER)
        RETURN action_idle
    END IF
END FUNCTION


// -----------------------------------------------------------------
// 2.3. 细分场景：角球 (Corner)
// -----------------------------------------------------------------
FUNCTION Handle_Corner(observation):
    // 如果是对方角球
    IF is_opponent_corner(observation) THEN
        // 站位靠近近门柱，准备出击
        target_pos = calculate_corner_save_position(observation)
        move_to(target_pos)

        // 判断球的落点，如果可控，尝试出击拿球
        IF ball_is_high_and_reachable_for_gk(observation) THEN
            // 移动向落点
            move_to(predicted_ball_landing_pos)
            // 在接触球的瞬间，执行短传（代表击球/摘球）
            RETURN action_short_pass 
        END IF
        RETURN get_move_action_towards(target_pos)
    ELSE
        // 我方角球，留在后场防止反击
        move_to(EDGE_OF_PENALTY_AREA_CENTER)
        RETURN action_idle
    END IF
END FUNCTION

// -----------------------------------------------------------------
// 2.4. 细分场景：界外球 (Throw-In)
// -----------------------------------------------------------------
FUNCTION Handle_ThrowIn(observation):
    // 如果是对方在我方防守区域的界外球
    IF is_opponent_throw_in_in_my_third(observation) THEN
        // 根据发球点调整在门线上的位置
        target_pos = adjust_position_for_throw_in(observation)
        move_to(target_pos)
        RETURN get_move_action_towards(target_pos)
    ELSE
        // 其他情况，保持中心站位
        move_to(MY_GOAL_LINE_CENTER)
        RETURN action_idle
    END IF
END FUNCTION


// 注：以上伪代码中的辅助函数 (如 find_nearest_opponent_distance, is_ball_in_my_penalty_area 等)
// 需要根据 observation.md 中提供的数据进行具体实现。例如：
// - is_ball_in_my_penalty_area 可以通过判断 observation.ball 的 x, y 坐标是否在禁区范围内实现。
//   (左侧球门x坐标为-1，禁区x坐标大概在 -1 到 -0.83 之间，y坐标在 -0.2 到 0.2 之间)
// - find_safest_teammate_for_pass 需要计算每个队友周围是否有对方球员，以及传球路线上是否可能被拦截。
```

# 谷歌足球环境中中后卫（Centre Back）的决策伪代码

本文档为谷歌足球环境中的中后卫（Centre Back, CB, `role_id=1`）提供了一套决策树伪代码。该伪代码旨在根据当前的战术阵型、比赛场景 (`game_mode`) 以及实时的观测数据 (`observation`)，为中后卫选择最合适的动作 (`action`)。

## 一、 核心决策原则

中后卫是防线的核心和领袖，其决策直接关系到球队的防守稳固性。以下是中后卫行动的核心原则：

1. **防守第一 (Defense First)**：首要职责是防止对方进球。盯人、补位、拦截和封堵是常规操作。在“防守”与“参与进攻”之间选择时，除非有明确的战术安排，否则永远优先考虑防守。
2. **位置纪律 (Positional Discipline)**：保持防线的完整和紧凑至关重要。不轻易被对方前锋的跑位吸引而失位，与防线上的其他球员（另一名中后卫、边后卫）保持适当距离。
3. **预判与拦截 (Anticipation & Interception)**：优秀的中后卫依靠预判而非速度。通过阅读比赛，预测对方的传球路线和进攻意图，提前移动到关键位置进行拦截。
4. **果断处理 (Decisive Action)**：在关键时刻，无论是上抢、滑铲还是头球解围，都必须果断。犹豫不决是防守大忌。
5. **由守转攻的枢纽 (Build-up Play)**：在现代足球中，中后卫是组织进攻的起点。在安全的情况下，通过精准的短传或长传，将球权转化为一次有效的进攻。

## 二、 战术适应性说明

根据《球员角色在不同战术下的职责划分.md》，中后卫的职责根据阵型有显著区别：

- **双中卫体系 (如 4-4-2, 4-3-3, 4-2-3-1)**：两名中后卫需紧密协作，一人负责上抢，另一人负责补位。当边后卫前压助攻时，他们需要覆盖更广的横向区域。
- **三中卫体系 (如 3-5-2 / 5-3-2)**：
  - **居中中后卫**：通常扮演防线组织者的角色，负责指挥和补位，位置相对靠后。
  - **两侧中后卫**：防守职责更具侵略性，需要前提至中场协助防守，并协防翼卫（Wing-back）身后留下的空当。

为了在伪代码中体现这一点，我们将引入假设的变量 `CURRENT_FORMATION` (e.g., '4-4-2', '3-5-2') 和 `MY_CB_SPECIFIC_ROLE` (e.g., 'central_in_3cb', 'in_2cb_pair')。

## 三、 伪代码

```
// =================================================================
// Centre Back (CB) Decision Logic
// =================================================================

// -----------------------------------------------------------------
// 主决策函数
// -----------------------------------------------------------------
FUNCTION Centre_Back_Main_Decision(observation, my_index):
    // 检查我（中后卫）是否为当前受控球员
    IF observation.active == my_index THEN
        // 检查我是否持球
        IF observation.ball_owned_player == my_index THEN
            RETURN Handle_Ball_Possession(observation)
        ELSE
            RETURN Handle_Without_Ball(observation)
        END IF
    ELSE
        // 如果不是受控球员，则执行内置AI
        RETURN action_builtin_ai
    END IF
END FUNCTION


// -----------------------------------------------------------------
// 1. 持球状态下的决策
// -----------------------------------------------------------------
FUNCTION Handle_Ball_Possession(observation):
    // 检查是否有对方前锋逼近造成威胁
    nearest_opponent_dist = find_nearest_opponent_distance(observation.right_team)
    
    // 如果受到紧逼或在禁区内，优先保证安全
    IF nearest_opponent_dist < DANGER_ZONE_RADIUS OR is_in_my_penalty_area(my_position) THEN
        // 大脚解围
        RETURN action_high_pass
    ELSE
        // 在安全情况下，组织进攻
        // 优先寻找安全的短传给后腰(DM)、中前卫(CM)或边后卫(LB/RB)
        safe_midfielder = find_safest_teammate_for_pass(observation.left_team, 'short', [e_PlayerRole_DM, e_PlayerRole_CM])
        IF safe_midfielder IS NOT NULL THEN
            look_towards(safe_midfielder.position)
            RETURN action_short_pass
        END IF

        safe_fullback = find_safest_teammate_for_pass(observation.left_team, 'short', [e_PlayerRole_LB, e_PlayerRole_RB])
        IF safe_fullback IS NOT NULL THEN
            look_towards(safe_fullback.position)
            RETURN action_short_pass
        END IF
        
        // 如果没有好的短传选择，可以考虑长传找前锋(CF)，但这风险更高
        forward_teammate = find_best_teammate_for_pass(observation.left_team, 'long', [e_PlayerRole_CF])
        IF forward_teammate IS NOT NULL THEN
            look_towards(forward_teammate.position)
            RETURN action_long_pass
        END IF

        // 如果所有传球路线都不好，大脚解围
        RETURN action_high_pass
    END IF
END FUNCTION


// -----------------------------------------------------------------
// 2. 无球状态下的决策
// -----------------------------------------------------------------
FUNCTION Handle_Without_Ball(observation):
    // 根据比赛模式（game_mode）进行决策
    SWITCH observation.game_mode:
        CASE e_GameMode_Normal:
            RETURN Handle_Normal_Play(observation)
        
        CASE e_GameMode_KickOff:
            // 开球时，保持在自己的防守位置
            move_to(MY_INITIAL_DEFENSIVE_POSITION)
            RETURN action_idle

        CASE e_GameMode_GoalKick:
            // 我方球门球：散开，为门将提供短传选择
            IF is_my_team_goalkick(observation) THEN
                move_to(EDGE_OF_PENALTY_AREA_WIDE)
            ELSE // 对方球门球：前提到中线附近，准备争顶
                move_to(NEAR_HALFWAY_LINE)
            END IF
            RETURN action_idle
            
        CASE e_GameMode_FreeKick:
        CASE e_GameMode_Corner:
            RETURN Handle_Defensive_Set_Piece(observation)
            
        CASE e_GameMode_ThrowIn:
            // 根据掷球点位置，保持防线紧凑
            move_to(get_position_to_defend_throw_in(observation))
            RETURN action_idle

        CASE e_GameMode_Penalty:
            // 保持在禁区外
            move_to(OUTSIDE_PENALTY_ARC)
            RETURN action_idle
            
        DEFAULT:
            RETURN action_idle
    END SWITCH
END FUNCTION


// -----------------------------------------------------------------
// 2.1. 细分场景：常规比赛 (Normal Play)
// -----------------------------------------------------------------
FUNCTION Handle_Normal_Play(observation):
    ball_pos = observation.ball
    
    // CASE A: 对方持球
    IF observation.ball_owned_team == OPPONENT_TEAM THEN
        opponent_forward = find_opponent_forward_to_mark() // 找到需要盯防的对方前锋

        // 如果对方前锋在你附近且可能接球，紧密盯防
        IF distance(my_position, opponent_forward.position) < MARKING_DISTANCE AND is_threat(opponent_forward) THEN
             move_to(get_marking_position(opponent_forward.position))
             RETURN get_move_action_towards(get_marking_position(opponent_forward.position))
        END IF

        // 如果球正向你的防区传来，准备拦截
        IF is_ball_coming_towards_my_zone(observation) THEN
            move_to(get_interception_point(observation))
            // 如果判断可以抢断，执行滑铲
            IF can_i_make_a_tackle(observation) THEN
                RETURN action_sliding
            END IF
            RETURN get_move_action_towards(get_interception_point(observation))
        END IF
        
        // 核心职责：保持防守阵型和位置
        // 根据球的位置和队友位置，移动到最佳防守位置
        // 目标是始终保持在球和球门之间
        optimal_pos = calculate_optimal_defensive_position(observation, MY_CB_SPECIFIC_ROLE)
        move_to(optimal_pos)
        RETURN get_move_action_towards(optimal_pos)

    // CASE B: 我方持球
    ELSE IF observation.ball_owned_team == MY_TEAM THEN
        // 稍微拉开，为持球队友提供一个安全的回传或横传选择
        // 但不能牺牲防守位置
        safe_support_pos = find_safe_support_position()
        move_to(safe_support_pos)
        RETURN get_move_action_towards(safe_support_pos)
        
    // CASE C: 无人持球 (Loose Ball)
    ELSE
        // 如果球在危险区域且我距离最近，果断上抢
        IF is_ball_in_dangerous_zone(ball_pos) AND i_am_closest_to_ball(observation) THEN
            run_towards(ball_pos)
            RETURN action_sprint
        ELSE
            // 否则，保持防守位置
            optimal_pos = calculate_optimal_defensive_position(observation, MY_CB_SPECIFIC_ROLE)
            move_to(optimal_pos)
            RETURN get_move_action_towards(optimal_pos)
        END IF
    END IF
END FUNCTION

// -----------------------------------------------------------------
// 2.2. 细分场景：防守定位球 (角球/任意球)
// -----------------------------------------------------------------
FUNCTION Handle_Defensive_Set_Piece(observation):
    // 如果是对方在我方半场的危险定位球 (角球或任意球)
    IF is_opponent_dangerous_set_piece(observation) THEN
        // 1. 分配盯人任务
        target_opponent = find_tallest_opponent_to_mark_in_box()
        
        // 2. 移动到盯人位置，干扰对手
        IF target_opponent IS NOT NULL THEN
            marking_pos = get_marking_position_in_box(target_opponent.position)
            move_to(marking_pos)
        ELSE // 如果没有明确盯人目标，进行区域防守
            zonal_pos = get_zonal_defensive_position_in_box()
            move_to(zonal_pos)
        END IF

        // 3. 当球传来时，起跳争顶
        // 简化：如果球在高空向你飞来，使用高球长传动作来模拟头球解围
        IF is_ball_high_and_coming_to_me(observation) THEN
            RETURN action_high_pass
        END IF

        RETURN get_move_action_towards(my_target_position)

    ELSE IF is_our_set_piece_late_in_game_and_we_are_losing(observation) THEN
        // 如果是比赛最后时刻我方角球/任意球且落后，前压参与进攻
        move_to(OPPONENT_PENALTY_AREA)
        RETURN action_sprint
    ELSE
        // 其他情况 (如我方后场任意球)，保持位置或提供接应点
        RETURN action_idle
    END IF
END FUNCTION


// 注：以上伪代码中的辅助函数 (如 find_nearest_opponent_distance, calculate_optimal_defensive_position 等)
// 需要根据 observation.md 中提供的数据进行具体实现。
// - calculate_optimal_defensive_position 需要复杂逻辑，结合球的位置、队友位置、对手位置以及战术要求（如造越位）。
// - find_opponent_forward_to_mark 需要识别对方阵型中的前锋角色球员。
// - 争顶头球可以用 action_high_pass / action_short_pass 来模拟，取决于解围方向和力度。
```

# 谷歌足球环境中左后卫（Left Back）的决策伪代码

本文档为谷歌足球环境中的左后卫（Left Back, LB, `role_id=2`）提供了一套决策树伪代码。该伪代码旨在根据当前的战术阵型、比赛场景 (`game_mode`) 以及实时的观测数据 (`observation`)，为左后卫选择最合适的动作 (`action`)。

## 一、 核心决策原则

左后卫是球队攻防两端的重要棋子，连接着后防与中前场。其决策必须在防守稳固和进攻支援之间找到精妙的平衡。

1. **边路走廊的统治者 (Ruler of the Flank)**：左后卫的主要活动区域是左侧边路。首要任务是锁死对方在这一侧的进攻（通常是对方的右边锋/右中场），防止其突破和传中。
2. **进攻宽度的提供者 (Provider of Width)**：在进攻中，左后卫需要积极前插，拉开进攻宽度，为中场和前锋创造空间。适时的套边（Overlap）和精准的传中是其核心进攻手段。
3. **攻防转换的节拍器 (Rhythm of Transition)**：在由守转攻时，左后卫需要快速前插参与进攻；在由攻转守时，必须以最快速度回防到位，恢复防守阵型。体能和速度至关重要。
4. **与队友的协同 (Collaboration with Teammates)**：防守时需与左中后卫（LCB）保持紧密联系，共同保护肋部空当。进攻时需与左中场（LM）或左边锋（LW）形成默契配合。
5. **判断时机 (Judging the Moment)**：何时前插助攻，何时坚守阵地，是左后卫需要做出的最关键决策。这需要对比赛局势有深刻的阅读能力。

## 二、 战术适应性说明

根据《球员角色在不同战术下的职责划分.md》，左后卫的职责根据阵型有根本性的区别，这是其决策逻辑的核心分歧点：

- **四后卫体系 (4-back systems, e.g., 4-4-2, 4-3-3, 4-2-3-1)**：作为**传统左后卫 (Full-back)**，防守是第一要务。在保证防守位置的前提下，前插参与进攻。
- **三/五后卫体系 (3-5-2 / 5-3-2)**：作为**左翼卫 (Left Wing-back)**，角色更偏向于中场。需要覆盖整个左边路，对体能和综合能力要求极高，是球队进攻宽度的主要来源，同时防守时需回撤形成五人防线。

为了在伪代码中体现这一点，我们将引入假设的变量 `CURRENT_FORMATION` 和 `MY_LB_ROLE` (可设为 `'fullback'` 或 `'wingback'`)。

## 三、 伪代码

```
// =================================================================
// Left Back (LB) Decision Logic
// =================================================================

// -----------------------------------------------------------------
// 主决策函数
// -----------------------------------------------------------------
FUNCTION Left_Back_Main_Decision(observation, my_index):
    // 检查我（左后卫）是否为当前受控球员
    IF observation.active == my_index THEN
        // 检查我是否持球
        IF observation.ball_owned_player == my_index THEN
            RETURN Handle_Ball_Possession(observation)
        ELSE
            RETURN Handle_Without_Ball(observation)
        END IF
    ELSE
        // 如果不是受控球员，则执行内置AI
        RETURN action_builtin_ai
    END IF
END FUNCTION


// -----------------------------------------------------------------
// 1. 持球状态下的决策
// -----------------------------------------------------------------
FUNCTION Handle_Ball_Possession(observation):
    // 检查是否有对方球员逼近造成威胁
    nearest_opponent_dist = find_nearest_opponent_distance_on_my_flank(observation.right_team)
    
    // CASE A: 在我方防守三区且受压，优先安全
    IF is_in_my_defensive_third(my_position) AND nearest_opponent_dist < DANGER_ZONE_RADIUS THEN
        // 沿边线大脚解围
        look_towards(OPPONENT_CORNER_FLAG_ON_MY_SIDE)
        RETURN action_high_pass
    END IF

    // CASE B: 在中场或进攻三区，执行战术职责
    IF is_in_opponent_half(my_position) THEN
        // 寻找传中机会
        IF can_make_a_cross(observation) THEN
            // 高球传中
            RETURN action_high_pass
        END IF
        
        // 尝试与前场队友配合
        safe_forward_pass = find_safest_teammate_for_pass(observation.left_team, 'short', [e_PlayerRole_LM, e_PlayerRole_AM, e_PlayerRole_CF])
        IF safe_forward_pass IS NOT NULL THEN
            RETURN action_short_pass
        END IF
    END IF

    // CASE C: 推进
    // 如果前方有空间，带球推进
    IF has_space_to_run_into(observation) THEN
        RETURN action_sprint // 冲刺带球
    ELSE
        // 如果没有好机会，安全回传给中后卫或后腰
        safe_pass_back = find_safest_teammate_for_pass(observation.left_team, 'short', [e_PlayerRole_CB, e_PlayerRole_DM])
        IF safe_pass_back IS NOT NULL THEN
            RETURN action_short_pass
        END IF
        // 最后选择：大脚解围
        RETURN action_high_pass
    END IF
END FUNCTION


// -----------------------------------------------------------------
// 2. 无球状态下的决策
// -----------------------------------------------------------------
FUNCTION Handle_Without_Ball(observation):
    // 根据比赛模式（game_mode）进行决策
    SWITCH observation.game_mode:
        CASE e_GameMode_Normal:
            RETURN Handle_Normal_Play(observation)
        
        CASE e_GameMode_KickOff:
        CASE e_GameMode_GoalKick:
        CASE e_GameMode_Penalty:
            // 在这些静止球状态下，回归自己的初始防守位置
            move_to(MY_INITIAL_DEFENSIVE_POSITION)
            RETURN action_idle

        CASE e_GameMode_FreeKick:
        CASE e_GameMode_Corner:
            RETURN Handle_Set_Piece(observation)
            
        CASE e_GameMode_ThrowIn:
            RETURN Handle_ThrowIn(observation)
            
        DEFAULT:
            RETURN action_idle
    END SWITCH
END FUNCTION


// -----------------------------------------------------------------
// 2.1. 细分场景：常规比赛 (Normal Play)
// -----------------------------------------------------------------
FUNCTION Handle_Normal_Play(observation):
    ball_pos = observation.ball
    
    // CASE A: 对方持球
    IF observation.ball_owned_team == OPPONENT_TEAM THEN
        // 如果球在我的防区（左路），上前防守
        IF is_ball_on_my_flank(ball_pos) THEN
            opponent_on_wing = find_opponent_on_my_flank()
            // 移动到可以阻止对方下底或内切的位置
            move_to(get_position_to_block_opponent(opponent_on_wing))
            // 如果对方试图突破，尝试滑铲
            IF opponent_is_dribbling_at_me(opponent_on_wing) AND can_i_make_a_tackle(observation) THEN
                RETURN action_sliding
            END IF
            RETURN get_move_action_towards(get_position_to_block_opponent(opponent_on_wing))
        ELSE
            // 球在别处，保持防守阵型，向中路收缩，与中后卫保持距离
            tucked_in_pos = get_tucked_in_defensive_position(observation)
            move_to(tucked_in_pos)
            RETURN get_move_action_towards(tucked_in_pos)
        END IF

    // CASE B: 我方持球
    ELSE IF observation.ball_owned_team == MY_TEAM THEN
        // 根据我的角色（后卫 vs 翼卫）决定前插力度
        IF MY_LB_ROLE == 'wingback' THEN
            // 翼卫：积极前插，冲刺到对方半场，成为一个主要的进攻点
            attacking_pos = get_wingback_attacking_position()
            run_towards(attacking_pos)
            RETURN action_sprint
        ELSE // fullback
            // 后卫：前插更谨慎，主要为了支援和提供宽度
            // 判断是否应该套边（如果我方左前卫内切）
            left_midfielder = get_teammate_by_role(e_PlayerRole_LM) // or LW
            IF left_midfielder_is_cutting_in(left_midfielder) THEN
                 // 套边跑位
                 overlapping_pos = get_overlapping_position()
                 run_towards(overlapping_pos)
                 RETURN action_sprint
            ELSE
                 // 保持在侧翼支援位置
                 support_pos = get_support_position_on_flank()
                 move_to(support_pos)
                 RETURN get_move_action_towards(support_pos)
            END IF
        END IF
        
    // CASE C: 无人持球 (Loose Ball)
    ELSE
        // 如果无人控制的球在我的边路附近，且我能最先拿到
        IF is_ball_on_my_flank(ball_pos) AND i_am_closest_to_ball(observation) THEN
            run_towards(ball_pos)
            RETURN action_sprint
        ELSE
            // 否则，迅速回归防守位置
            move_to(MY_BASE_DEFENSIVE_POSITION)
            RETURN get_move_action_towards(MY_BASE_DEFENSIVE_POSITION)
        END IF
    END IF
END FUNCTION

// -----------------------------------------------------------------
// 2.2. 细分场景：定位球 (Set Piece)
// -----------------------------------------------------------------
FUNCTION Handle_Set_Piece(observation):
    // 对方在我方半场的危险定位球 (角球或任意球)
    IF is_opponent_dangerous_set_piece(observation) THEN
        // 通常职责是防守近门柱或者盯防禁区边缘的球员防止远射
        defensive_pos = get_set_piece_defensive_position()
        move_to(defensive_pos)
        RETURN get_move_action_towards(defensive_pos)
    // 我方在前场的定位球
    ELSE IF is_our_attacking_set_piece(observation) THEN
        // 留在后场，防止对方打反击
        move_to(NEAR_HALFWAY_LINE_ON_MY_SIDE)
        RETURN action_idle
    END IF
END FUNCTION

// -----------------------------------------------------------------
// 2.3. 细分场景：界外球 (Throw-In)
// -----------------------------------------------------------------
FUNCTION Handle_ThrowIn(observation):
    // 我方在我方半场的界外球，我可能是掷球者或接应者
    IF is_my_throw_in_in_my_half(observation) THEN
        // 如果我是最近的球员，靠近球去准备掷球 (游戏中可能自动分配)
        move_to(ball_pos)
        RETURN action_idle 
    // 对方在我方半场的界外球
    ELSE IF is_opponent_throw_in_in_my_half(observation) THEN
        // 紧逼离你最近的对方接球球员
        opponent_to_mark = find_nearest_opponent_to_throw_in_spot()
        move_to(get_marking_position(opponent_to_mark.position))
        RETURN get_move_action_towards(get_marking_position(opponent_to_mark.position))
    ELSE
        RETURN action_idle
    END IF
END FUNCTION

// 注：以上伪代码中的辅助函数 (如 is_ball_on_my_flank, get_tucked_in_defensive_position 等)
// 需要根据 observation.md 中提供的数据进行具体实现。
// - is_ball_on_my_flank: 可通过球的y坐标是否在左侧（如 y < -0.1）来判断。
// - get_tucked_in_defensive_position: 需要计算自己与左中卫之间的理想距离和位置。
// - can_make_a_cross: 需要判断自己是否在对方半场边路，且禁区内有我方队友。
```

# 谷歌足球环境中右后卫（Right Back）的决策伪代码

本文档为谷歌足球环境中的右后卫（Right Back, RB, `role_id=3`）提供了一套决策树伪代码。该伪代码旨在根据当前的战术阵型、比赛场景 (`game_mode`) 以及实时的观测数据 (`observation`)，为右后卫选择最合适的动作 (`action`)。

## 一、 核心决策原则

右后卫是球队攻防体系的右翼支点，其决策能力对于球队的整体平衡至关重要。

1. **右翼走廊的守护者 (Guardian of the Right Flank)**：右后卫的主要职责是镇守右侧边路，压制对方的左路进攻（通常是对方的左边锋/左中场），阻止其传中和内切。
2. **进攻宽度的创造者 (Creator of Width)**：在进攻时，右后卫需果断前插，利用球场宽度，为队友扯开空间。精准的传中和积极的套边（Overlap）是其关键的进攻武器。
3. **攻防转换的执行者 (Executor of Transition)**：攻防转换瞬间，右后卫必须快速响应。丢球时要迅速回防，得球后要快速前插，这对球员的体能、速度和比赛阅读能力提出了高要求。
4. **与队友的联动 (Synergy with Teammates)**：防守时与右中后卫（RCB）协同作战，保护防线间的空当。进攻时与右中场（RM）或右边锋（RW）形成配合，制造局部优势。
5. **时机的把握 (Mastery of Timing)**：精准判断前插助攻与坚守防线的时机，是顶级右后卫的标志。这一决策需要基于对比赛局势的全面理解。

## 二、 战术适应性说明

与左后卫相似，《球员角色在不同战术下的职责划分.md》明确了右后卫在不同阵型下的核心职责差异，这是其决策逻辑的关键：

- **四后卫体系 (4-back systems, e.g., 4-4-2, 4-3-3, 4-2-3-1)**：作为**传统右后卫 (Full-back)**，首要任务是防守。在确保防线稳固的基础上，伺机前插支援进攻。
- **三/五后卫体系 (3-5-2 / 5-3-2)**：作为**右翼卫 (Right Wing-back)**，其角色更贴近于中场球员。职责是覆盖整个右路走廊，是球队进攻时的主要宽度来源，同时在防守时必须迅速回撤，与后卫们组成五人防线。

为了在伪代码中体现这一点，我们将引入假设的变量 `CURRENT_FORMATION` 和 `MY_RB_ROLE` (可设为 `'fullback'` 或 `'wingback'`)。

## 三、 伪代码

```
// =================================================================
// Right Back (RB) Decision Logic
// =================================================================

// -----------------------------------------------------------------
// 主决策函数
// -----------------------------------------------------------------
FUNCTION Right_Back_Main_Decision(observation, my_index):
    // 检查我（右后卫）是否为当前受控球员
    IF observation.active == my_index THEN
        // 检查我是否持球
        IF observation.ball_owned_player == my_index THEN
            RETURN Handle_Ball_Possession(observation)
        ELSE
            RETURN Handle_Without_Ball(observation)
        END IF
    ELSE
        // 如果不是受控球员，则执行内置AI
        RETURN action_builtin_ai
    END IF
END FUNCTION


// -----------------------------------------------------------------
// 1. 持球状态下的决策
// -----------------------------------------------------------------
FUNCTION Handle_Ball_Possession(observation):
    // 检查是否有对方球员逼近造成威胁
    nearest_opponent_dist = find_nearest_opponent_distance_on_my_flank(observation.right_team)
    
    // CASE A: 在我方防守三区且受压，优先保证安全
    IF is_in_my_defensive_third(my_position) AND nearest_opponent_dist < DANGER_ZONE_RADIUS THEN
        // 沿边线大脚解围
        look_towards(OPPONENT_CORNER_FLAG_ON_MY_SIDE)
        RETURN action_high_pass
    END IF

    // CASE B: 在中场或进攻三区，执行战术职责
    IF is_in_opponent_half(my_position) THEN
        // 寻找传中机会
        IF can_make_a_cross(observation) THEN
            RETURN action_high_pass
        END IF
        
        // 尝试与前场队友配合
        safe_forward_pass = find_safest_teammate_for_pass(observation.left_team, 'short', [e_PlayerRole_RM, e_PlayerRole_AM, e_PlayerRole_CF])
        IF safe_forward_pass IS NOT NULL THEN
            RETURN action_short_pass
        END IF
    END IF

    // CASE C: 推进
    // 如果前方有空间，带球推进
    IF has_space_to_run_into(observation) THEN
        RETURN action_sprint // 冲刺带球
    ELSE
        // 如果没有好机会，安全回传给中后卫或后腰
        safe_pass_back = find_safest_teammate_for_pass(observation.left_team, 'short', [e_PlayerRole_CB, e_PlayerRole_DM])
        IF safe_pass_back IS NOT NULL THEN
            RETURN action_short_pass
        END IF
        // 最后选择：大脚解围
        RETURN action_high_pass
    END IF
END FUNCTION


// -----------------------------------------------------------------
// 2. 无球状态下的决策
// -----------------------------------------------------------------
FUNCTION Handle_Without_Ball(observation):
    // 根据比赛模式（game_mode）进行决策
    SWITCH observation.game_mode:
        CASE e_GameMode_Normal:
            RETURN Handle_Normal_Play(observation)
        
        CASE e_GameMode_KickOff:
        CASE e_GameMode_GoalKick:
        CASE e_GameMode_Penalty:
            // 在这些静止球状态下，回归自己的初始防守位置
            move_to(MY_INITIAL_DEFENSIVE_POSITION)
            RETURN action_idle

        CASE e_GameMode_FreeKick:
        CASE e_GameMode_Corner:
            RETURN Handle_Set_Piece(observation)
            
        CASE e_GameMode_ThrowIn:
            RETURN Handle_ThrowIn(observation)
            
        DEFAULT:
            RETURN action_idle
    END SWITCH
END FUNCTION


// -----------------------------------------------------------------
// 2.1. 细分场景：常规比赛 (Normal Play)
// -----------------------------------------------------------------
FUNCTION Handle_Normal_Play(observation):
    ball_pos = observation.ball
    
    // CASE A: 对方持球
    IF observation.ball_owned_team == OPPONENT_TEAM THEN
        // 如果球在我的防区（右路），上前防守
        IF is_ball_on_my_flank(ball_pos) THEN
            opponent_on_wing = find_opponent_on_my_flank()
            // 移动到可以阻止对方下底或内切的位置
            move_to(get_position_to_block_opponent(opponent_on_wing))
            // 如果对方试图突破，尝试滑铲
            IF opponent_is_dribbling_at_me(opponent_on_wing) AND can_i_make_a_tackle(observation) THEN
                RETURN action_sliding
            END IF
            RETURN get_move_action_towards(get_position_to_block_opponent(opponent_on_wing))
        ELSE
            // 球在别处，保持防守阵型，向中路收缩，与中后卫保持距离
            tucked_in_pos = get_tucked_in_defensive_position(observation)
            move_to(tucked_in_pos)
            RETURN get_move_action_towards(tucked_in_pos)
        END IF

    // CASE B: 我方持球
    ELSE IF observation.ball_owned_team == MY_TEAM THEN
        // 根据我的角色（后卫 vs 翼卫）决定前插力度
        IF MY_RB_ROLE == 'wingback' THEN
            // 翼卫：积极前插，冲刺到对方半场，成为一个主要的进攻点
            attacking_pos = get_wingback_attacking_position()
            run_towards(attacking_pos)
            RETURN action_sprint
        ELSE // fullback
            // 后卫：前插更谨慎，主要为了支援和提供宽度
            // 判断是否应该套边（如果我方右前卫内切）
            right_midfielder = get_teammate_by_role(e_PlayerRole_RM) // or RW
            IF right_midfielder_is_cutting_in(right_midfielder) THEN
                 // 套边跑位
                 overlapping_pos = get_overlapping_position()
                 run_towards(overlapping_pos)
                 RETURN action_sprint
            ELSE
                 // 保持在侧翼支援位置
                 support_pos = get_support_position_on_flank()
                 move_to(support_pos)
                 RETURN get_move_action_towards(support_pos)
            END IF
        END IF
        
    // CASE C: 无人持球 (Loose Ball)
    ELSE
        // 如果无人控制的球在我的边路附近，且我能最先拿到
        IF is_ball_on_my_flank(ball_pos) AND i_am_closest_to_ball(observation) THEN
            run_towards(ball_pos)
            RETURN action_sprint
        ELSE
            // 否则，迅速回归防守位置
            move_to(MY_BASE_DEFENSIVE_POSITION)
            RETURN get_move_action_towards(MY_BASE_DEFENSIVE_POSITION)
        END IF
    END IF
END FUNCTION

// -----------------------------------------------------------------
// 2.2. 细分场景：定位球 (Set Piece)
// -----------------------------------------------------------------
FUNCTION Handle_Set_Piece(observation):
    // 对方在我方半场的危险定位球 (角球或任意球)
    IF is_opponent_dangerous_set_piece(observation) THEN
        // 通常职责是防守近门柱或者盯防禁区边缘的球员防止远射
        defensive_pos = get_set_piece_defensive_position()
        move_to(defensive_pos)
        RETURN get_move_action_towards(defensive_pos)
    // 我方在前场的定位球
    ELSE IF is_our_attacking_set_piece(observation) THEN
        // 留在后场，防止对方打反击
        move_to(NEAR_HALFWAY_LINE_ON_MY_SIDE)
        RETURN action_idle
    END IF
END FUNCTION

// -----------------------------------------------------------------
// 2.3. 细分场景：界外球 (Throw-In)
// -----------------------------------------------------------------
FUNCTION Handle_ThrowIn(observation):
    // 我方在我方半场的界外球，我可能是掷球者或接应者
    IF is_my_throw_in_in_my_half(observation) THEN
        // 如果我是最近的球员，靠近球去准备掷球 (游戏中可能自动分配)
        move_to(ball_pos)
        RETURN action_idle 
    // 对方在我方半场的界外球
    ELSE IF is_opponent_throw_in_in_my_half(observation) THEN
        // 紧逼离你最近的对方接球球员
        opponent_to_mark = find_nearest_opponent_to_throw_in_spot()
        move_to(get_marking_position(opponent_to_mark.position))
        RETURN get_move_action_towards(get_marking_position(opponent_to_mark.position))
    ELSE
        RETURN action_idle
    END IF
END FUNCTION

// 注：以上伪代码中的辅助函数 (如 is_ball_on_my_flank, get_tucked_in_defensive_position 等)
// 需要根据 observation.md 中提供的数据进行具体实现。
// - is_ball_on_my_flank: 可通过球的y坐标是否在右侧（如 y > 0.1，因为y轴正方向向下）来判断。
// - get_tucked_in_defensive_position: 需要计算自己与右中卫之间的理想距离和位置。
// - can_make_a_cross: 需要判断自己是否在对方半场边路，且禁区内有我方队友。
```

# 谷歌足球环境中防守型中场（Defence Midfield）的决策伪代码

本文档为谷歌足球环境中的防守型中场（Defence Midfield, DM, `role_id=4`）提供了一套决策树伪代码。该伪代码旨在根据当前的战术阵型、比赛场景 (`game_mode`) 以及实时的观测数据 (`observation`)，为防守型中场选择最合适的动作 (`action`)。

## 一、 核心决策原则

防守型中场是连接后防与中场的战略枢纽，是球队攻防平衡的基石。

1. **防线屏障 (The Shield)**：首要职责是保护后防线，通过选位和拦截，切断对方中场与前锋之间的传球路线。是防守的第一道中场关卡。
2. **位置感是生命 (Positioning is Everything)**：必须时刻保持在球和本方球门之间的核心区域。不轻易被调动而离开中路防守要地，填补中后卫与中前卫之间的空当。
3. **进攻的破坏者 (The Disruptor)**：对对方的持球核心（通常是攻击型中场）进行压迫、骚扰和抢断。其主要任务是破坏对方的进攻节奏。
4. **由守转攻的起点 (The Starting Point of Attack)**：抢断成功后，不追求复杂的盘带，而是通过简洁、安全的传球，快速将球交给更具创造力的队友，发动进攻。
5. **比赛的节拍器 (The Metronome)**：通过控制球权和位置，调节球队的攻防节奏。在需要时放慢节奏，稳固控球；或通过快速一脚出球，加快反击速度。

## 二、 战术适应性说明

《球员角色在不同战术下的职责划分.md》明确指出，防守型中场的配置和职责在不同阵型中差异巨大：

- **单后腰体系 (Single Pivot, e.g., 4-3-3)**：防守覆盖范围极广，是防线前唯一的专职屏障。对球员的位置感、拦截能力和独立防守能力要求极高。
- **双后腰体系 (Double Pivot, e.g., 4-2-3-1)**：与另一名后腰搭档，共同分担防守职责。可以有更细致的分工，例如一人偏重拦截扫荡（Destroyer），另一人偏重组织调度（Deep-lying Playmaker）。两人需保持紧密协作。
- **无专职后腰体系 (e.g., 4-4-2, 部分3-5-2)**：其职责由中前卫（CM）分担。在这种情况下，本伪代码不完全适用，但其防守原则可供参考。

我们将引入假设的变量 `MY_DM_ROLE` (可设为 `'single_pivot'` 或 `'double_pivot'`) 以体现战术差异。

## 三、 伪代码

```
// =================================================================
// Defence Midfield (DM) Decision Logic
// =================================================================

// -----------------------------------------------------------------
// 主决策函数
// -----------------------------------------------------------------
FUNCTION Defence_Midfield_Main_Decision(observation, my_index):
    // 检查我（防守型中场）是否为当前受控球员
    IF observation.active == my_index THEN
        // 检查我是否持球
        IF observation.ball_owned_player == my_index THEN
            RETURN Handle_Ball_Possession(observation)
        ELSE
            RETURN Handle_Without_Ball(observation)
        END IF
    ELSE
        // 如果不是受控球员，则执行内置AI
        RETURN action_builtin_ai
    END IF
END FUNCTION


// -----------------------------------------------------------------
// 1. 持球状态下的决策
// -----------------------------------------------------------------
FUNCTION Handle_Ball_Possession(observation):
    // 防守型中场的首要原则是安全、快速地出球
    
    // 如果受到紧逼，立即寻找最安全的出球点
    nearest_opponent_dist = find_nearest_opponent_distance(observation.right_team)
    IF nearest_opponent_dist < DANGER_ZONE_RADIUS THEN
        safe_pass_back = find_safest_teammate_for_pass(observation.left_team, 'short', [e_PlayerRole_CB, e_PlayerRole_GK])
        IF safe_pass_back IS NOT NULL THEN
            RETURN action_short_pass
        ELSE
            RETURN action_high_pass // 实在不行就大脚解围
        END IF
    END IF

    // 在安全情况下，作为进攻发起点
    // 优先寻找向前或向侧翼的简单传球
    forward_pass_option = find_safest_teammate_for_pass(observation.left_team, 'short', [e_PlayerRole_CM, e_PlayerRole_AM])
    IF forward_pass_option IS NOT NULL THEN
        RETURN action_short_pass
    END IF
    
    side_pass_option = find_safest_teammate_for_pass(observation.left_team, 'short', [e_PlayerRole_LM, e_PlayerRole_RM, e_PlayerRole_LB, e_PlayerRole_RB])
    IF side_pass_option IS NOT NULL THEN
        RETURN action_short_pass
    END IF

    // 如果没有好的向前选择，则回传给中后卫重新组织
    safe_pass_back = find_safest_teammate_for_pass(observation.left_team, 'short', [e_PlayerRole_CB])
    IF safe_pass_back IS NOT NULL THEN
        RETURN action_short_pass
    END IF

    // 最后的选择是自己带球，但要非常谨慎
    RETURN action_dribble
END FUNCTION


// -----------------------------------------------------------------
// 2. 无球状态下的决策
// -----------------------------------------------------------------
FUNCTION Handle_Without_Ball(observation):
    // 根据比赛模式（game_mode）进行决策
    SWITCH observation.game_mode:
        CASE e_GameMode_Normal:
            RETURN Handle_Normal_Play(observation)
        
        CASE e_GameMode_KickOff:
        CASE e_GameMode_Penalty:
            // 在这些静止球状态下，回归自己的初始防守位置
            move_to(MY_INITIAL_CENTRAL_POSITION)
            RETURN action_idle

        CASE e_GameMode_GoalKick:
        CASE e_GameMode_FreeKick:
        CASE e_GameMode_Corner:
            RETURN Handle_Set_Piece(observation)
            
        CASE e_GameMode_ThrowIn:
            // 保持在中路核心区域，防止对方通过中路渗透
            move_to(get_central_position_to_defend_throw_in(observation))
            RETURN action_idle
            
        DEFAULT:
            RETURN action_idle
    END SWITCH
END FUNCTION


// -----------------------------------------------------------------
// 2.1. 细分场景：常规比赛 (Normal Play)
// -----------------------------------------------------------------
FUNCTION Handle_Normal_Play(observation):
    ball_pos = observation.ball
    
    // CASE A: 对方持球
    IF observation.ball_owned_team == OPPONENT_TEAM THEN
        // 找到对方核心进攻球员（通常是AM）进行盯防
        opponent_ playmaker = find_opponent_playmaker_to_mark()
        
        // 核心职责：保持在球和球门之间的位置，封锁传球路线
        shielding_pos = get_position_to_shield_defense(observation, opponent_playmaker)
        move_to(shielding_pos)
        
        // 如果对方 playmaker 在你的区域内拿球，立即上抢
        IF distance(my_position, opponent_playmaker.position) < PRESSING_DISTANCE AND opponent_playmaker.has_ball THEN
             run_towards(opponent_playmaker.position)
             // 如果时机合适，果断滑铲
             IF can_i_make_a_tackle(observation) THEN
                 RETURN action_sliding
             END IF
             RETURN action_sprint
        END IF

        // 如果传球路线被你封堵，而你又能抢先一步拿到球
        IF can_i_intercept_pass(observation) THEN
            move_to(get_interception_point(observation))
            RETURN action_sprint
        END IF
        
        RETURN get_move_action_towards(shielding_pos)

    // CASE B: 我方持球
    ELSE IF observation.ball_owned_team == MY_TEAM THEN
        // 不要轻易前插，保持在防线之前，为队友提供一个安全的回传点
        // 你的位置是防止对手反击的第一道屏障
        support_pos = get_safe_support_position_behind_ball()
        move_to(support_pos)
        RETURN get_move_action_towards(support_pos)
        
    // CASE C: 无人持球 (Loose Ball)
    ELSE
        // 如果无人控制的球在中圈弧附近的核心区域，且我能最先拿到
        IF is_ball_in_central_midfield(ball_pos) AND i_am_closest_to_ball(observation) THEN
            run_towards(ball_pos)
            RETURN action_sprint
        ELSE
            // 否则，迅速回归核心防守位置
            move_to(MY_BASE_DEFENSIVE_POSITION)
            RETURN get_move_action_towards(MY_BASE_DEFENSIVE_POSITION)
        END IF
    END IF
END FUNCTION

// -----------------------------------------------------------------
// 2.2. 细分场景：定位球 (Set Piece)
// -----------------------------------------------------------------
FUNCTION Handle_Set_Piece(observation):
    // 对方在我方半场的危险定位球 (角球或任意球)
    IF is_opponent_dangerous_set_piece(observation) THEN
        // 站在禁区弧顶位置，是第一道屏障
        // 主要职责：1. 拦截对方的战术短传 2. 封堵远射 3. 抢第二落点并发动反击
        defensive_pos = get_position_on_edge_of_box()
        move_to(defensive_pos)
        RETURN get_move_action_towards(defensive_pos)
        
    // 我方在前场的定位球
    ELSE IF is_our_attacking_set_piece(observation) THEN
        // 留在后场中圈附近，防止对方打反击
        move_to(NEAR_HALFWAY_LINE_CENTRAL)
        RETURN action_idle
    END IF
END FUNCTION

// 注：以上伪代码中的辅助函数 (如 get_position_to_shield_defense, find_opponent_playmaker_to_mark 等)
// 需要根据 observation.md 中提供的数据进行具体实现。
// - get_position_to_shield_defense: 核心逻辑，需要计算出能同时兼顾球、对方核心球员和本方球门的位置。
// - find_opponent_playmaker_to_mark: 需要识别对方阵中角色为 AM (e_PlayerRole_AM, id=8) 的球员。
// - get_safe_support_position_behind_ball: 总是移动到我方持球队友的斜后方，形成保护。
```

# 谷歌足球环境中中前卫（Central Midfield）的决策伪代码

本文档为谷歌足球环境中的中前卫（Central Midfield, CM, `role_id=5`）提供了一套决策树伪代码。该伪代码旨在根据当前的战术阵型、比赛场景 (`game_mode`) 以及实时的观测数据 (`observation`)，为中前卫选择最合适的动作 (`action`)。

## 一、 核心决策原则

中前卫是球队的战术核心，连接着攻防两端，其决策直接影响比赛的走向。

1. **攻防枢纽 (The Engine)**：作为球队的发动机，必须在攻防两端不懈奔跑。既要回防到本方禁区前沿，也要前插到对方禁区制造威胁（Box-to-Box）。
2. **节奏掌控者 (The Tempo Controller)**：通过传球选择和跑位来控制比赛节奏。在需要时通过短传配合稳定局势，或通过快速直塞发动致命一击。
3. **空间创造与利用者 (Space Creator & Exploiter)**：通过无球跑动为队友拉开空间，并敏锐地寻找和利用对方防线间的空隙。
4. **进攻组织核心 (The Playmaker)**：负责组织和串联进攻，通过精准的传球为前锋和边锋输送炮弹。远射也是其重要的得分手段。
5. **中场绞肉机 (The Midfield Press)**：在防守时，积极参与中场逼抢和拦截，与防守型中场（DM）共同构建中场屏障，限制对方组织核心。

## 二、 战术适应性说明

《球员角色在不同战术下的职责划分.md》指出，中前卫的职责和自由度根据中场配置有很大不同：

- **双中前卫体系 (Two-man midfield, e.g., 4-4-2)**：与搭档共同承担攻防职责，对球员的综合能力和往返奔跑能力要求很高。两人需要有明确的分工和默契。
- **三中前卫体系 (Three-man midfield, e.g., 4-3-3, 3-5-2)**：通常有两名中前卫（CM/8号位）和一名防守型中场（DM/6号位）。在这种体系下，中前卫被解放出来，可以更多地前插参与进攻、支援边路和远射。
- **在4-2-3-1阵型中**：传统中前卫的职责被双后腰（DM）和攻击型中场（AM）分解，该阵型通常没有专职的中前卫角色。

我们将引入假设的变量 `MY_CM_ROLE_TYPE` (可设为 `'box_to_box_in_442'` 或 `'attacking_8_in_433'`) 以区分战术。

## 三、 伪代码

```
// =================================================================
// Central Midfield (CM) Decision Logic
// =================================================================

// -----------------------------------------------------------------
// 主决策函数
// -----------------------------------------------------------------
FUNCTION Central_Midfield_Main_Decision(observation, my_index):
    // 检查我（中前卫）是否为当前受控球员
    IF observation.active == my_index THEN
        // 检查我是否持球
        IF observation.ball_owned_player == my_index THEN
            RETURN Handle_Ball_Possession(observation)
        ELSE
            RETURN Handle_Without_Ball(observation)
        END IF
    ELSE
        // 如果不是受控球员，则执行内置AI
        RETURN action_builtin_ai
    END IF
END FUNCTION


// -----------------------------------------------------------------
// 1. 持球状态下的决策
// -----------------------------------------------------------------
FUNCTION Handle_Ball_Possession(observation):
    // 如果在对方半场且有射门机会，果断射门
    IF is_in_shooting_range(my_position) AND has_clear_shot_angle(observation) THEN
        RETURN action_shot
    END IF

    // 寻找向前传球的机会，这是首要选择
    // 尝试为前锋(CF)或攻击型中场(AM)送出直塞球
    IF can_make_through_pass(observation, [e_PlayerRole_CF, e_PlayerRole_AM]) THEN
        RETURN action_long_pass // 用长传模拟直塞
    END IF

    // 寻找给边路队友的安全传球
    side_pass_option = find_safest_teammate_for_pass(observation.left_team, 'short', [e_PlayerRole_LM, e_PlayerRole_RM])
    IF side_pass_option IS NOT NULL THEN
        RETURN action_short_pass
    END IF
    
    // 如果前方有空间，可以带球突破
    IF has_space_to_dribble_into(observation) THEN
        RETURN action_dribble
    END IF

    // 如果向前或侧向没有好的机会，则安全地回传给后腰(DM)或中后卫(CB)
    safe_pass_back = find_safest_teammate_for_pass(observation.left_team, 'short', [e_PlayerRole_DM, e_PlayerRole_CB])
    IF safe_pass_back IS NOT NULL THEN
        RETURN action_short_pass
    END IF

    // 最后的选择是转向另一侧，大范围转移球
    RETURN action_long_pass
END FUNCTION


// -----------------------------------------------------------------
// 2. 无球状态下的决策
// -----------------------------------------------------------------
FUNCTION Handle_Without_Ball(observation):
    // 根据比赛模式（game_mode）进行决策
    SWITCH observation.game_mode:
        CASE e_GameMode_Normal:
            RETURN Handle_Normal_Play(observation)
        
        CASE e_GameMode_KickOff:
        CASE e_GameMode_Penalty:
            // 在这些静止球状态下，回归自己的初始中圈位置
            move_to(MY_INITIAL_CENTRAL_POSITION)
            RETURN action_idle

        CASE e_GameMode_GoalKick:
        CASE e_GameMode_FreeKick:
        CASE e_GameMode_Corner:
            RETURN Handle_Set_Piece(observation)
            
        CASE e_GameMode_ThrowIn:
            // 移动到掷球点附近，提供接应点或压迫对方
            move_to(get_position_for_throw_in(observation))
            RETURN action_idle
            
        DEFAULT:
            RETURN action_idle
    END SWITCH
END FUNCTION


// -----------------------------------------------------------------
// 2.1. 细分场景：常规比赛 (Normal Play)
// -----------------------------------------------------------------
FUNCTION Handle_Normal_Play(observation):
    ball_pos = observation.ball
    
    // CASE A: 对方持球
    IF observation.ball_owned_team == OPPONENT_TEAM THEN
        // 压迫对方中场持球者
        opponent_midfielder = find_opponent_midfielder_with_ball()
        IF opponent_midfielder IS NOT NULL AND distance(my_position, opponent_midfielder.position) < PRESSING_DISTANCE THEN
             run_towards(opponent_midfielder.position)
             // 如果时机合适，果断滑铲
             IF can_i_make_a_tackle(observation) THEN
                 RETURN action_sliding
             END IF
             RETURN action_sprint
        END IF
        
        // 如果不在逼抢范围内，则回归防守位置，切断传球路线
        defensive_pos = get_midfield_defensive_position(observation)
        move_to(defensive_pos)
        RETURN get_move_action_towards(defensive_pos)

    // CASE B: 我方持球
    ELSE IF observation.ball_owned_team == MY_TEAM THEN
        // 根据战术角色决定跑位
        IF MY_CM_ROLE_TYPE == 'attacking_8_in_433' THEN
            // 8号位角色：积极前插，寻找对方后卫和中场之间的空当
            attacking_space = find_space_between_lines()
            move_to(attacking_space)
            RETURN action_sprint
        ELSE // 'box_to_box_in_442'
            // B2B角色：移动到可以接应持球队友的位置，保持阵型平衡
            support_pos = get_safe_support_position_for_teammate()
            move_to(support_pos)
            RETURN get_move_action_towards(support_pos)
        END IF
        
    // CASE C: 无人持球 (Loose Ball)
    ELSE
        // 中场是必争之地，如果无人控制的球在中场区域，必须去抢
        IF is_ball_in_central_midfield(ball_pos) AND i_am_closest_midfielder_to_ball(observation) THEN
            run_towards(ball_pos)
            RETURN action_sprint
        ELSE
            // 否则，迅速回归中场核心位置
            move_to(MY_BASE_MIDFIELD_POSITION)
            RETURN get_move_action_towards(MY_BASE_MIDFIELD_POSITION)
        END IF
    END IF
END FUNCTION

// -----------------------------------------------------------------
// 2.2. 细分场景：定位球 (Set Piece)
// -----------------------------------------------------------------
FUNCTION Handle_Set_Piece(observation):
    // 对方在我方半场的危险定位球 (角球或任意球)
    IF is_opponent_dangerous_set_piece(observation) THEN
        // 根据战术安排，可能进入禁区争顶，或在禁区外围保护第二落点
        defensive_pos = get_set_piece_defensive_assignment()
        move_to(defensive_pos)
        RETURN get_move_action_towards(defensive_pos)
        
    // 我方在前场的定位球
    ELSE IF is_our_attacking_set_piece(observation) THEN
        // 积极进入或靠近对方禁区，寻找机会
        // 可以是直接争顶，也可以是在外围等待远射机会
        attacking_pos = get_set_piece_attacking_assignment()
        move_to(attacking_pos)
        RETURN get_move_action_towards(attacking_pos)
    END IF
END FUNCTION

// 注：以上伪代码中的辅助函数 (如 can_make_through_pass, find_space_between_lines 等)
// 需要根据 observation.md 中提供的数据进行具体实现。
// - can_make_through_pass: 需要判断我方前锋是否有前插跑位，且传球路线上没有对方防守球员。
// - find_space_between_lines: 核心进攻跑位逻辑，需要找到对方后卫线和中场线之间的空当区域。
// - get_set_piece_attacking_assignment: 需要根据球员的具体属性（如身高、头球能力）来决定是进禁区还是在外围。
```

# 谷歌足球环境中左中场（Left Midfield）的决策伪代码

本文档为谷歌足球环境中的左中场（Left Midfield, LM, `role_id=6`）提供了一套决策树伪代码。该伪代码旨在根据当前的战术阵型、比赛场景 (`game_mode`) 以及实时的观测数据 (`observation`)，为左中场选择最合适的动作 (`action`)。

## 一、 核心决策原则

左中场是球队在左翼的主要攻击手，其决策围绕着创造进攻机会和维持边路攻守平衡展开。

1. **边路爆点 (The Flank Breaker)**：核心任务是通过速度和技术在左路形成突破，撕开对方防线。无论是下底传中还是内切攻击，都应是其常规武器。
2. **进攻宽度维持者 (The Width Holder)**：在进攻中，通过占据边路位置，拉扯对方防线，为中路队友创造空间。
3. **机会创造者 (The Chance Creator)**：通过精准的传中、地面传球或内切后的分球，为前锋送出助攻。
4. **内切威胁 (The Inverted Threat)**：具备内切后直接射门的能力，增加进攻的突然性和多样性。
5. **第一道边路防线 (The First Line of Flank Defense)**：在由攻转守时，需要立即压迫对方的右后卫（RB），延缓其助攻。在必要时，需回防至本方半场，协助左后卫（LB）进行防守。

## 二、 战术适应性说明

《球员角色在不同战术下的职责划分.md》明确指出，左中场的角色根据阵型有本质区别，这是其决策逻辑的核心：

- **传统边前卫 (in 4-4-2)**：攻防职责较为均衡。需要频繁往返于两个底线之间，进攻时提供宽度和传中，防守时需回撤很深，与左后卫形成保护，构成中场四人防线。
- **攻击型边锋 (in 4-3-3, 4-2-3-1)**：位置更靠前，主要精力投入进攻。防守职责更侧重于前场逼抢，压迫对方后卫线，而不是深度回防。其进攻方式也更自由，可以频繁内切。
- **在3-5-2 / 5-3-2阵型中**：通常没有设置专职的左中场，其职责被左翼卫（LWB）和中前卫（CM）所吸收。

我们将引入假设的变量 `MY_LM_ROLE_TYPE` (可设为 `'traditional_midfielder'` 或 `'attacking_winger'`) 以体现战术差异。

## 三、 伪代码

```
// =================================================================
// Left Midfield (LM) Decision Logic
// =================================================================

// -----------------------------------------------------------------
// 主决策函数
// -----------------------------------------------------------------
FUNCTION Left_Midfield_Main_Decision(observation, my_index):
    // 检查我（左中场）是否为当前受控球员
    IF observation.active == my_index THEN
        // 检查我是否持球
        IF observation.ball_owned_player == my_index THEN
            RETURN Handle_Ball_Possession(observation)
        ELSE
            RETURN Handle_Without_Ball(observation)
        END IF
    ELSE
        // 如果不是受控球员，则执行内置AI
        RETURN action_builtin_ai
    END IF
END FUNCTION


// -----------------------------------------------------------------
// 1. 持球状态下的决策
// -----------------------------------------------------------------
FUNCTION Handle_Ball_Possession(observation):
    // CASE A: 在进攻三区，创造威胁
    IF is_in_attacking_third(my_position) THEN
        // 如果内切后有射门角度，果断射门
        IF has_clear_shot_angle_after_cutting_in(observation) THEN
            move_inwards_and_prepare_shot()
            RETURN action_shot
        END IF

        // 如果在边路且禁区内有队友，传中
        IF is_near_touchline(my_position) AND has_teammates_in_box(observation) THEN
            // 根据情况选择高球传中或地面短传
            RETURN CHOOSE_BETWEEN(action_high_pass, action_short_pass)
        END IF

        // 尝试与队友进行二过一配合或短传渗透
        pass_option = find_safest_teammate_for_pass(observation.left_team, 'short', [e_PlayerRole_CF, e_PlayerRole_AM, e_PlayerRole_LB])
        IF pass_option IS NOT NULL THEN
            RETURN action_short_pass
        END IF
    END IF
    
    // CASE B: 在中场，选择推进或转移
    // 如果前方边路有空间，冲刺带球
    IF has_space_to_run_into_on_flank(observation) THEN
        RETURN action_sprint
    END IF

    // 如果没有好的向前选择，安全回传或横传给中场队友
    safe_pass_central = find_safest_teammate_for_pass(observation.left_team, 'short', [e_PlayerRole_CM, e_PlayerRole_DM])
    IF safe_pass_central IS NOT NULL THEN
        RETURN action_short_pass
    END IF

    // 最后选择：回传给左后卫
    safe_pass_back = find_safest_teammate_for_pass(observation.left_team, 'short', [e_PlayerRole_LB])
    IF safe_pass_back IS NOT NULL THEN
        RETURN action_short_pass
    END IF
    
    RETURN action_dribble // 保持控球

END FUNCTION


// -----------------------------------------------------------------
// 2. 无球状态下的决策
// -----------------------------------------------------------------
FUNCTION Handle_Without_Ball(observation):
    // 根据比赛模式（game_mode）进行决策
    SWITCH observation.game_mode:
        CASE e_GameMode_Normal:
            RETURN Handle_Normal_Play(observation)
        
        CASE e_GameMode_KickOff:
        CASE e_GameMode_Penalty:
            move_to(MY_INITIAL_SIDE_POSITION)
            RETURN action_idle

        CASE e_GameMode_GoalKick:
        CASE e_GameMode_FreeKick:
        CASE e_GameMode_Corner:
            RETURN Handle_Set_Piece(observation)
            
        CASE e_GameMode_ThrowIn:
            RETURN Handle_ThrowIn(observation)
            
        DEFAULT:
            RETURN action_idle
    END SWITCH
END FUNCTION


// -----------------------------------------------------------------
// 2.1. 细分场景：常规比赛 (Normal Play)
// -----------------------------------------------------------------
FUNCTION Handle_Normal_Play(observation):
    ball_pos = observation.ball
    
    // CASE A: 对方持球
    IF observation.ball_owned_team == OPPONENT_TEAM THEN
        // 根据角色决定防守策略
        IF MY_LM_ROLE_TYPE == 'attacking_winger' THEN
            // 边锋角色：在前场压迫对方的右后卫
            opponent_rb = find_opponent_by_role(e_PlayerRole_RB)
            IF is_ball_on_their_side_of_field(ball_pos) AND opponent_rb.has_ball THEN
                run_towards(opponent_rb.position)
                RETURN action_sprint
            END IF
        ELSE // 'traditional_midfielder'
            // 传统边前卫：深度回防，协助左后卫，保持中场防线
            defensive_pos = get_deep_defensive_position_on_flank()
            move_to(defensive_pos)
            RETURN get_move_action_towards(defensive_pos)
        END IF

    // CASE B: 我方持球
    ELSE IF observation.ball_owned_team == MY_TEAM THEN
        // 积极前插，跑到空当处接球
        // 可以选择拉边要球，或内切到肋部空间
        attacking_space = find_attacking_space_on_my_side(observation)
        run_towards(attacking_space)
        RETURN action_sprint
        
    // CASE C: 无人持球 (Loose Ball)
    ELSE
        // 如果无人控制的球在我的活动区域，且我能最先拿到
        IF is_ball_on_my_flank(ball_pos) AND i_am_closest_to_ball(observation) THEN
            run_towards(ball_pos)
            RETURN action_sprint
        ELSE
            // 否则，回归基础的攻防转换位置
            move_to(MY_BASE_TRANSITION_POSITION)
            RETURN get_move_action_towards(MY_BASE_TRANSITION_POSITION)
        END IF
    END IF
END FUNCTION

// -----------------------------------------------------------------
// 2.2. 细分场景：定位球 (Set Piece)
// -----------------------------------------------------------------
FUNCTION Handle_Set_Piece(observation):
    // 对方在我方半场的危险定位球 (角球或任意球)
    IF is_opponent_dangerous_set_piece(observation) THEN
        // 回防到禁区边缘，参与防守人墙或保护第二落点
        defensive_pos = get_set_piece_defensive_assignment()
        move_to(defensive_pos)
        RETURN get_move_action_towards(defensive_pos)
        
    // 我方在前场的定位球
    ELSE IF is_our_attacking_set_piece(observation) THEN
        // 移动到对方禁区附近，准备接应、传中或远射
        attacking_pos = get_position_around_opponent_box()
        move_to(attacking_pos)
        RETURN get_move_action_towards(attacking_pos)
    END IF
END FUNCTION


// -----------------------------------------------------------------
// 2.3. 细分场景：界外球 (Throw-In)
// -----------------------------------------------------------------
FUNCTION Handle_ThrowIn(observation):
    // 我方在前场的界外球
    IF is_my_throw_in_in_attacking_half(observation) THEN
        // 跑位接应，或拉开空间
        move_to(get_open_space_for_throw_in())
        RETURN action_idle 
    // 对方在我方半场的界外球
    ELSE IF is_opponent_throw_in_in_my_half(observation) THEN
        // 压迫对方准备接球的球员
        opponent_to_mark = find_nearest_opponent_to_throw_in_spot()
        move_to(get_marking_position(opponent_to_mark.position))
        RETURN get_move_action_towards(get_marking_position(opponent_to_mark.position))
    ELSE
        RETURN action_idle
    END IF
END FUNCTION


// 注：以上伪代码中的辅助函数 (如 has_clear_shot_angle_after_cutting_in, find_attacking_space_on_my_side 等)
// 需要根据 observation.md 中提供的数据进行具体实现。
// - has_clear_shot_angle_after_cutting_in: 需要模拟内切后的位置，并判断该位置与球门之间是否有防守球员阻挡。
// - find_attacking_space_on_my_side: 需要分析对方右后卫和右中卫之间的空当（肋部空间）。
// - get_deep_defensive_position_on_flank: 在4-4-2阵型中，这个位置应该与本方中前卫在同一水平线上，以维持防线整齐。
```

# 谷歌足球环境中右中场（Right Midfield）的决策伪代码

本文档为谷歌足球环境中的右中场（Right Midfield, RM, `role_id=7`）提供了一套决策树伪代码。该伪代码旨在根据当前的战术阵型、比赛场景 (`game_mode`) 以及实时的观测数据 (`observation`)，为右中场选择最合适的动作 (`action`)。

## 一、 核心决策原则

右中场是球队右翼进攻的发起者和执行者，其决策对球队的进攻宽度和穿透力有直接影响。

1. **右翼走廊突击手 (The Right Flank Attacker)**：核心职责是在右路利用速度和技术制造突破，为球队打开进攻通道。下底传中和内切射门是其必备技能。
2. **进攻宽度保障者 (The Width Guarantee)**：通过占据右边路，有效拉扯对方的防守阵型，为中路的队友创造和利用空间。
3. **机会输送者 (The Chance Supplier)**：通过高质量的传中球、地面配合或内切后的妙传，为禁区内的前锋提供得分机会。
4. **内切攻击点 (The Inverted Scorer)**：当战术需要时，具备从右路内切并用左脚完成射门的能力，是丰富进攻套路的关键。
5. **边路防守的第一道屏障 (The First Flank Defender)**：由攻转守时，必须第一时间对对方的左后卫（LB）施加压力，延缓其进攻。并根据战术要求，回防至本方半场，协同右后卫（RB）进行防守。

## 二、 战术适应性说明

《球员角色在不同战术下的职责划分.md》明确指出，右中场的角色和职责随阵型变化而显著不同：

- **传统边前卫 (in 4-4-2)**：攻防任务均衡。需要覆盖整个右路，进攻时提供宽度和传中，防守时必须回撤，与右后卫（RB）组成边路屏障，维持中场的四人防守链条。
- **攻击型边锋 (in 4-3-3, 4-2-3-1)**：场上位置更靠前，进攻任务更重。防守时更强调在前场对对方后卫的压迫，而非长距离回防。拥有更大的战术自由度，可以频繁内切攻击。
- **在3-5-2 / 5-3-2阵型中**：此阵型通常不设专职的右中场，其功能由更全能的右翼卫（RWB）和中前卫（CM）承担。

我们将引入假设的变量 `MY_RM_ROLE_TYPE` (可设为 `'traditional_midfielder'` 或 `'attacking_winger'`) 以体现战术差异。

## 三、 伪代码

```
// =================================================================
// Right Midfield (RM) Decision Logic
// =================================================================

// -----------------------------------------------------------------
// 主决策函数
// -----------------------------------------------------------------
FUNCTION Right_Midfield_Main_Decision(observation, my_index):
    // 检查我（右中场）是否为当前受控球员
    IF observation.active == my_index THEN
        // 检查我是否持球
        IF observation.ball_owned_player == my_index THEN
            RETURN Handle_Ball_Possession(observation)
        ELSE
            RETURN Handle_Without_Ball(observation)
        END IF
    ELSE
        // 如果不是受控球员，则执行内置AI
        RETURN action_builtin_ai
    END IF
END FUNCTION


// -----------------------------------------------------------------
// 1. 持球状态下的决策
// -----------------------------------------------------------------
FUNCTION Handle_Ball_Possession(observation):
    // CASE A: 在进攻三区，创造威胁
    IF is_in_attacking_third(my_position) THEN
        // 如果内切后有射门角度，果断射门
        IF has_clear_shot_angle_after_cutting_in(observation) THEN
            move_inwards_and_prepare_shot()
            RETURN action_shot
        END IF

        // 如果在边路且禁区内有队友，传中
        IF is_near_touchline(my_position) AND has_teammates_in_box(observation) THEN
            // 根据情况选择高球传中或地面短传
            RETURN CHOOSE_BETWEEN(action_high_pass, action_short_pass)
        END IF

        // 尝试与队友进行二过一配合或短传渗透
        pass_option = find_safest_teammate_for_pass(observation.left_team, 'short', [e_PlayerRole_CF, e_PlayerRole_AM, e_PlayerRole_RB])
        IF pass_option IS NOT NULL THEN
            RETURN action_short_pass
        END IF
    END IF
    
    // CASE B: 在中场，选择推进或转移
    // 如果前方边路有空间，冲刺带球
    IF has_space_to_run_into_on_flank(observation) THEN
        RETURN action_sprint
    END IF

    // 如果没有好的向前选择，安全回传或横传给中场队友
    safe_pass_central = find_safest_teammate_for_pass(observation.left_team, 'short', [e_PlayerRole_CM, e_PlayerRole_DM])
    IF safe_pass_central IS NOT NULL THEN
        RETURN action_short_pass
    END IF

    // 最后选择：回传给右后卫
    safe_pass_back = find_safest_teammate_for_pass(observation.left_team, 'short', [e_PlayerRole_RB])
    IF safe_pass_back IS NOT NULL THEN
        RETURN action_short_pass
    END IF
    
    RETURN action_dribble // 保持控球

END FUNCTION


// -----------------------------------------------------------------
// 2. 无球状态下的决策
// -----------------------------------------------------------------
FUNCTION Handle_Without_Ball(observation):
    // 根据比赛模式（game_mode）进行决策
    SWITCH observation.game_mode:
        CASE e_GameMode_Normal:
            RETURN Handle_Normal_Play(observation)
        
        CASE e_GameMode_KickOff:
        CASE e_GameMode_Penalty:
            move_to(MY_INITIAL_SIDE_POSITION)
            RETURN action_idle

        CASE e_GameMode_GoalKick:
        CASE e_GameMode_FreeKick:
        CASE e_GameMode_Corner:
            RETURN Handle_Set_Piece(observation)
            
        CASE e_GameMode_ThrowIn:
            RETURN Handle_ThrowIn(observation)
            
        DEFAULT:
            RETURN action_idle
    END SWITCH
END FUNCTION


// -----------------------------------------------------------------
// 2.1. 细分场景：常规比赛 (Normal Play)
// -----------------------------------------------------------------
FUNCTION Handle_Normal_Play(observation):
    ball_pos = observation.ball
    
    // CASE A: 对方持球
    IF observation.ball_owned_team == OPPONENT_TEAM THEN
        // 根据角色决定防守策略
        IF MY_RM_ROLE_TYPE == 'attacking_winger' THEN
            // 边锋角色：在前场压迫对方的左后卫
            opponent_lb = find_opponent_by_role(e_PlayerRole_LB)
            IF is_ball_on_their_side_of_field(ball_pos) AND opponent_lb.has_ball THEN
                run_towards(opponent_lb.position)
                RETURN action_sprint
            END IF
        ELSE // 'traditional_midfielder'
            // 传统边前卫：深度回防，协助右后卫，保持中场防线
            defensive_pos = get_deep_defensive_position_on_flank()
            move_to(defensive_pos)
            RETURN get_move_action_towards(defensive_pos)
        END IF

    // CASE B: 我方持球
    ELSE IF observation.ball_owned_team == MY_TEAM THEN
        // 积极前插，跑到空当处接球
        // 可以选择拉边要球，或内切到肋部空间
        attacking_space = find_attacking_space_on_my_side(observation)
        run_towards(attacking_space)
        RETURN action_sprint
        
    // CASE C: 无人持球 (Loose Ball)
    ELSE
        // 如果无人控制的球在我的活动区域，且我能最先拿到
        IF is_ball_on_my_flank(ball_pos) AND i_am_closest_to_ball(observation) THEN
            run_towards(ball_pos)
            RETURN action_sprint
        ELSE
            // 否则，回归基础的攻防转换位置
            move_to(MY_BASE_TRANSITION_POSITION)
            RETURN get_move_action_towards(MY_BASE_TRANSITION_POSITION)
        END IF
    END IF
END FUNCTION

// -----------------------------------------------------------------
// 2.2. 细分场景：定位球 (Set Piece)
// -----------------------------------------------------------------
FUNCTION Handle_Set_Piece(observation):
    // 对方在我方半场的危险定位球 (角球或任意球)
    IF is_opponent_dangerous_set_piece(observation) THEN
        // 回防到禁区边缘，参与防守人墙或保护第二落点
        defensive_pos = get_set_piece_defensive_assignment()
        move_to(defensive_pos)
        RETURN get_move_action_towards(defensive_pos)
        
    // 我方在前场的定位球
    ELSE IF is_our_attacking_set_piece(observation) THEN
        // 移动到对方禁区附近，准备接应、传中或远射
        attacking_pos = get_position_around_opponent_box()
        move_to(attacking_pos)
        RETURN get_move_action_towards(attacking_pos)
    END IF
END FUNCTION


// -----------------------------------------------------------------
// 2.3. 细分场景：界外球 (Throw-In)
// -----------------------------------------------------------------
FUNCTION Handle_ThrowIn(observation):
    // 我方在前场的界外球
    IF is_my_throw_in_in_attacking_half(observation) THEN
        // 跑位接应，或拉开空间
        move_to(get_open_space_for_throw_in())
        RETURN action_idle 
    // 对方在我方半场的界外球
    ELSE IF is_opponent_throw_in_in_my_half(observation) THEN
        // 压迫对方准备接球的球员
        opponent_to_mark = find_nearest_opponent_to_throw_in_spot()
        move_to(get_marking_position(opponent_to_mark.position))
        RETURN get_move_action_towards(get_marking_position(opponent_to_mark.position))
    ELSE
        RETURN action_idle
    END IF
END FUNCTION


// 注：以上伪代码中的辅助函数 (如 has_clear_shot_angle_after_cutting_in, find_attacking_space_on_my_side 等)
// 需要根据 observation.md 中提供的数据进行具体实现。
// - is_ball_on_my_flank: 可通过球的y坐标是否在右侧（如 y > 0.1，因为y轴正方向向下）来判断。
// - find_attacking_space_on_my_side: 需要分析对方左后卫和左中卫之间的空当（肋部空间）。
// - get_deep_defensive_position_on_flank: 在4-4-2阵型中，这个位置应该与本方中前卫在同一水平线上，以维持防线整齐。
```

# 谷歌足球环境中攻击型中场（Attack Midfield）的决策伪代码

本文档为谷歌足球环境中的攻击型中场（Attack Midfield, AM, `role_id=8`）提供了一套决策树伪代码。该伪代码旨在根据当前的战术阵型、比赛场景 (`game_mode`) 以及实时的观测数据 (`observation`)，为攻击型中场选择最合适的动作 (`action`)。

## 一、 核心决策原则

攻击型中场是球队的进攻大脑，是连接中场与锋线的关键人物，其决策以创造性和致命性为核心。

1. **机会创造者 (The Ultimate Creator)**：首要任务是为前锋和其他攻击手创造得分机会。送出精准的直塞球（Through Ball）和关键传球是其最高优先级。
2. **空间操纵者 (The Space Operator)**：核心活动区域是在对方后卫线与中场线之间的“空当”（The Hole）。必须通过聪明的无球跑位，持续在该区域寻找和利用空间，接球并组织进攻。
3. **双重得分威胁 (The Dual Goal Threat)**：不仅是助攻者，也是得分手。通过远射和后排插上，直接威胁对方球门。
4. **高位压迫的起点 (The Tip of the Press)**：在防守时，主要职责是在前场骚扰和压迫对方的后腰（DM），干扰其出球，是球队高位逼抢的第一道屏障。通常不承担深度回防任务。
5. **进攻的串联者 (The Link-up Player)**：连接中场和前锋，通过背身拿球、短传配合，将全队的进攻捏合成一个整体。

## 二、 战术适应性说明

《球员角色在不同战术下的职责划分.md》指出，攻击型中场是一个高度专业化的角色，主要出现在特定阵型中：

- **核心角色 (in 4-2-3-1)**：这是最典型的“10号位”阵型。攻击型中场是绝对的进攻核心，拥有极高的战术自由度。本伪代码将主要围绕此阵型构建。
- **在其他阵型中体现**：
  - **4-4-2**: 无专职攻击型中场，其职责可能由一名回撤的前锋（Second Striker）或前插的中前卫承担。
  - **4-3-3**: 无专职攻击型中场，其创造职责由两名靠前的中前卫（CM/8号位）共同分担。
  - **3-5-2**: 在3-4-1-2的变体中，会设置一名专职前腰，其职责与4-2-3-1中的AM类似。

本伪代码假设球员扮演的是一个专职的攻击型中场角色。

## 三、 伪代码

```
// =================================================================
// Attack Midfield (AM) Decision Logic
// =================================================================

// -----------------------------------------------------------------
// 主决策函数
// -----------------------------------------------------------------
FUNCTION Attack_Midfield_Main_Decision(observation, my_index):
    // 检查我（攻击型中场）是否为当前受控球员
    IF observation.active == my_index THEN
        // 检查我是否持球
        IF observation.ball_owned_player == my_index THEN
            RETURN Handle_Ball_Possession(observation)
        ELSE
            RETURN Handle_Without_Ball(observation)
        END IF
    ELSE
        // 如果不是受控球员，则执行内置AI
        RETURN action_builtin_ai
    END IF
END FUNCTION


// -----------------------------------------------------------------
// 1. 持球状态下的决策
// -----------------------------------------------------------------
FUNCTION Handle_Ball_Possession(observation):
    // 核心区域：在对方禁区前沿
    IF is_in_zone_14(my_position) THEN // Zone 14 是指禁区前沿的黄金区域
        // 优先级1：为前锋送出致命直塞
        IF can_make_through_pass(observation, [e_PlayerRole_CF]) THEN
            RETURN action_long_pass // 使用长传模拟直塞
        END IF

        // 优先级2：如果出现空档，直接射门
        IF has_clear_shot_angle(observation) THEN
            RETURN action_shot
        END IF
        
        // 优先级3：分球给侧翼的队友
        side_pass_option = find_safest_teammate_for_pass(observation.left_team, 'short', [e_PlayerRole_LM, e_PlayerRole_RM])
        IF side_pass_option IS NOT NULL THEN
            RETURN action_short_pass
        END IF
    END IF
    
    // 如果没有直接创造威胁的机会，选择盘带或传球来调整
    // 尝试带球突破，吸引防守
    IF has_space_to_dribble_into(observation) THEN
        RETURN action_dribble
    END IF

    // 安全地传球给侧翼或后方的队友，重新组织
    safe_pass_option = find_safest_teammate_for_pass(observation.left_team, 'short', [e_PlayerRole_CM, e_PlayerRole_DM])
    IF safe_pass_option IS NOT NULL THEN
        RETURN action_short_pass
    END IF
    
    RETURN action_dribble // 保持控球，等待机会

END FUNCTION


// -----------------------------------------------------------------
// 2. 无球状态下的决策
// -----------------------------------------------------------------
FUNCTION Handle_Without_Ball(observation):
    // 根据比赛模式（game_mode）进行决策
    SWITCH observation.game_mode:
        CASE e_GameMode_Normal:
            RETURN Handle_Normal_Play(observation)
        
        CASE e_GameMode_KickOff:
        CASE e_GameMode_Penalty:
            move_to(MY_INITIAL_ATTACKING_POSITION)
            RETURN action_idle

        CASE e_GameMode_GoalKick:
        CASE e_GameMode_FreeKick:
        CASE e_GameMode_Corner:
            RETURN Handle_Set_Piece(observation)
            
        CASE e_GameMode_ThrowIn:
            // 在前场移动，为掷球队友提供一个向前的接应点
            move_to(get_open_space_for_throw_in_forward())
            RETURN action_idle
            
        DEFAULT:
            RETURN action_idle
    END SWITCH
END FUNCTION


// -----------------------------------------------------------------
// 2.1. 细分场景：常规比赛 (Normal Play)
// -----------------------------------------------------------------
FUNCTION Handle_Normal_Play(observation):
    ball_pos = observation.ball
    
    // CASE A: 对方持球
    IF observation.ball_owned_team == OPPONENT_TEAM THEN
        // 主要防守职责：压迫对方后腰
        opponent_dm = find_opponent_by_role(e_PlayerRole_DM)
        IF opponent_dm IS NOT NULL AND opponent_dm.has_ball THEN
            // 如果对方后腰拿球，立即上抢
            run_towards(opponent_dm.position)
            RETURN action_sprint
        ELSE
            // 否则，保持在前场位置，切断对方后卫和后腰的联系，准备反击
            stay_high_and_block_passing_lanes()
            RETURN action_idle
        END IF

    // CASE B: 我方持球
    ELSE IF observation.ball_owned_team == MY_TEAM THEN
        // 核心无球任务：寻找并移动到空当区域
        attacking_space = find_space_between_lines(observation)
        run_towards(attacking_space)
        RETURN action_sprint
        
    // CASE C: 无人持球 (Loose Ball)
    ELSE
        // 如果无人控制的球在对方半场，积极争抢
        IF is_ball_in_opponent_half(ball_pos) AND i_am_closest_to_ball(observation) THEN
            run_towards(ball_pos)
            RETURN action_sprint
        ELSE
            // 否则，回归到基础的攻击位置
            move_to(MY_BASE_ATTACKING_POSITION)
            RETURN get_move_action_towards(MY_BASE_ATTACKING_POSITION)
        END IF
    END IF
END FUNCTION

// -----------------------------------------------------------------
// 2.2. 细分场景：定位球 (Set Piece)
// -----------------------------------------------------------------
FUNCTION Handle_Set_Piece(observation):
    // 对方在我方半场的危险定位球 (角球或任意球)
    IF is_opponent_dangerous_set_piece(observation) THEN
        // 留在中线附近，不参与本方禁区防守，准备发动快速反击
        stay_near_halfway_line_for_counter_attack()
        RETURN action_idle
        
    // 我方在前场的定位球
    ELSE IF is_our_attacking_set_piece(observation) THEN
        // 移动到对方禁区弧顶附近
        // 职责：1. 接应战术短传 2. 等待第二落点进行远射 3. 组织二次进攻
        attacking_pos = get_position_on_edge_of_opponent_box()
        move_to(attacking_pos)
        RETURN get_move_action_towards(attacking_pos)
    END IF
END FUNCTION

// 注：以上伪代码中的辅助函数 (如 can_make_through_pass, find_space_between_lines 等)
// 需要根据 observation.md 中提供的数据进行具体实现。
// - find_space_between_lines: 核心跑位逻辑，需要分析并找到对方后卫线和中场线之间的最佳无人盯防区域。
// - is_in_zone_14: 需要定义禁区前沿中心地带的坐标范围。
// - stay_high_and_block_passing_lanes: 移动到可以同时威胁对方中后卫和后腰的位置。
```

# 谷歌足球环境中中锋（Central Front）的决策伪代码

本文档为谷歌足球环境中的中锋（Central Front, CF, `role_id=9`）提供了一套决策树伪代码。该伪代码旨在根据当前的战术阵型、比赛场景 (`game_mode`) 以及实时的观测数据 (`observation`)，为中锋选择最合适的动作 (`action`)。

## 一、 核心决策原则

中锋是球队进攻的矛头，其所有决策最终都应服务于“进球”这一核心目标。

1. **射门是天职 (Shooting is the Mission)**：在任何合理的情况下，射门是第一选择。接到球后，应迅速调整姿态，寻找起脚机会。
2. **无球跑位决定一切 (Off-the-ball Movement is Everything)**：优秀的中锋用跑位创造机会。核心任务是在对方防线的肩上游走，随时准备反越位前插，接应直塞球。
3. **进攻支点 (The Offensive Pivot)**：作为前场的支点，需要具备背身拿球、倚住后卫的能力，然后为后插上的队友（如AM, CM）做球，或分给侧翼的搭档。
4. **防守的第一线 (The First Line of Defense)**：在由攻转守时，立即就地对对方持球的中后卫或门将施压，干扰其出球，延缓对方的进攻组织。
5. **空间牵扯者 (The Space Decoy)**：通过横向或纵向的跑动，吸引并带走防守球员，为其他队友（特别是边锋和攻击型中场）创造进攻空间。

## 二、 战术适应性说明

《球员角色在不同战术下的职责划分.md》明确了中锋在不同体系下的多样性，这是其决策逻辑的关键：

- **单中锋体系 (in 4-3-3, 4-2-3-1)**：通常作为“进攻支点”，需要强大的身体和控球能力来背身拿球，并为内切的边锋和前插的中场做球。
- **双前锋体系 (in 4-4-2, 3-5-2)**：与另一名前锋搭档。组合多样，可以是一高一快的“站桩-抢点”组合，也可以是双快组合。需要与搭档形成默契，相互创造机会。
- **特殊角色：伪九号 (False Nine)**：一种特殊的战术安排。中锋会主动回撤到中场区域，目的是引出对方中后卫，为边锋或前插的中场创造其身后的空间，并参与进攻组织。

我们将引入假设的变量 `MY_CF_ROLE_TYPE` (可设为 `'pivot_striker'`, `'poacher'`, `'false_nine'`) 来体现战术差异。

## 三、 伪代码

```
// =================================================================
// Central Front (CF) Decision Logic
// =================================================================

// -----------------------------------------------------------------
// 主决策函数
// -----------------------------------------------------------------
FUNCTION Central_Front_Main_Decision(observation, my_index):
    // 检查我（中锋）是否为当前受控球员
    IF observation.active == my_index THEN
        // 检查我是否持球
        IF observation.ball_owned_player == my_index THEN
            RETURN Handle_Ball_Possession(observation)
        ELSE
            RETURN Handle_Without_Ball(observation)
        END IF
    ELSE
        // 如果不是受控球员，则执行内置AI
        RETURN action_builtin_ai
    END IF
END FUNCTION


// -----------------------------------------------------------------
// 1. 持球状态下的决策
// -----------------------------------------------------------------
FUNCTION Handle_Ball_Possession(observation):
    // 优先级1：射门！
    // 如果在禁区内或有清晰的射门线路，立即射门
    IF is_in_penalty_box(my_position) OR has_clear_shot_angle(observation) THEN
        RETURN action_shot
    END IF

    // 优先级2：与队友配合
    // 如果背身拿球且受到压迫，快速做球给后插上的队友
    IF is_facing_away_from_goal() AND is_under_pressure() THEN
        layoff_option = find_safest_teammate_for_pass(observation.left_team, 'short', [e_PlayerRole_AM, e_PlayerRole_CM])
        IF layoff_option IS NOT NULL THEN
            RETURN action_short_pass
        END IF
    END IF
    
    // 寻找另一名前锋搭档或边锋
    partner_option = find_safest_teammate_for_pass(observation.left_team, 'short', [e_PlayerRole_CF, e_PlayerRole_LM, e_PlayerRole_RM])
    IF partner_option IS NOT NULL THEN
        RETURN action_short_pass
    END IF

    // 优先级3：盘带
    // 仅在前方有明确空间可以突入禁区时选择带球
    IF has_space_to_dribble_towards_goal(observation) THEN
        RETURN action_dribble
    END IF
    
    // 如果以上皆不可行，保护球权，等待支援
    RETURN action_dribble // 使用盘带动作护球

END FUNCTION


// -----------------------------------------------------------------
// 2. 无球状态下的决策
// -----------------------------------------------------------------
FUNCTION Handle_Without_Ball(observation):
    // 根据比赛模式（game_mode）进行决策
    SWITCH observation.game_mode:
        CASE e_GameMode_Normal:
            RETURN Handle_Normal_Play(observation)
        
        CASE e_GameMode_KickOff:
            // 准备前插
            move_to(MY_INITIAL_ATTACKING_POSITION)
            RETURN action_idle

        CASE e_GameMode_GoalKick:
        CASE e_GameMode_FreeKick:
        CASE e_GameMode_Corner:
            RETURN Handle_Set_Piece(observation)
            
        CASE e_GameMode_ThrowIn:
             // 移动到可以接应或牵制防守的位置
            move_to(get_position_for_throw_in_attack())
            RETURN action_idle
            
        CASE e_GameMode_Penalty:
            // 如果是我方罚点球，留在禁区外准备补射
            IF is_my_team_penalty(observation) THEN
                move_to(OUTSIDE_PENALTY_ARC)
            END IF
            RETURN action_idle

        DEFAULT:
            RETURN action_idle
    END SWITCH
END FUNCTION


// -----------------------------------------------------------------
// 2.1. 细分场景：常规比赛 (Normal Play)
// -----------------------------------------------------------------
FUNCTION Handle_Normal_Play(observation):
    // CASE A: 我方持球，执行进攻跑位
    IF observation.ball_owned_team == MY_TEAM THEN
        // 根据战术角色决定跑位
        SWITCH MY_CF_ROLE_TYPE:
            CASE 'false_nine':
                // 伪九号：回撤到中场，吸引中后卫
                move_to(find_space_between_lines(observation))
                RETURN get_move_action_towards(find_space_between_lines(observation))
            
            CASE 'poacher':
            CASE 'pivot_striker':
            DEFAULT:
                // 传统中锋/抢点者：在对方最后一名后卫附近游弋，寻找前插机会
                run_in_behind_defensive_line(observation)
                RETURN action_sprint
        END SWITCH

    // CASE B: 对方持球，执行高位压迫
    ELSE IF observation.ball_owned_team == OPPONENT_TEAM THEN
        // 压迫对方持球的中后卫
        opponent_cb_with_ball = find_opponent_cb_with_ball(observation)
        IF opponent_cb_with_ball IS NOT NULL THEN
            run_towards(opponent_cb_with_ball.position)
            RETURN action_sprint
        ELSE
             // 如果对方后卫无球，则切断他们与后腰的传球路线
            block_passing_lane_to_dm()
            RETURN action_idle
        END IF

    // CASE C: 无人持球 (Loose Ball)
    ELSE
        // 如果球在对方半场，且有机会抢到，积极拼抢
        IF is_ball_in_opponent_half(ball_pos) AND i_am_closest_to_ball(observation) THEN
            run_towards(ball_pos)
            RETURN action_sprint
        ELSE
            // 否则，回归到基础的中锋位置
            move_to(MY_BASE_ATTACKING_POSITION)
            RETURN get_move_action_towards(MY_BASE_ATTACKING_POSITION)
        END IF
    END IF
END FUNCTION

// -----------------------------------------------------------------
// 2.2. 细分场景：定位球 (Set Piece)
// -----------------------------------------------------------------
FUNCTION Handle_Set_Piece(observation):
    // 我方在前场的定位球 (角球/任意球)
    IF is_our_attacking_set_piece(observation) THEN
        // 冲入禁区，抢占有利位置准备头球攻门
        move_to(get_best_position_in_box_for_header())
        // 如果球向你飞来，执行射门（模拟头球）
        IF is_ball_coming_towards_me_for_header(observation) THEN
            RETURN action_shot
        END IF
        RETURN get_move_action_towards(get_best_position_in_box_for_header())
        
    // 对方在我方半场的定位球
    ELSE IF is_opponent_dangerous_set_piece(observation) THEN
        // 留在中线附近，准备发动快速反击
        stay_near_halfway_line_for_counter_attack()
        RETURN action_idle
    END IF
END FUNCTION

// 注：以上伪代码中的辅助函数 (如 run_in_behind_defensive_line, find_space_between_lines 等)
// 需要根据 observation.md 中提供的数据进行具体实现。
// - run_in_behind_defensive_line: 核心跑位逻辑，需要判断对方防线的平均x坐标，并向其前方移动，同时注意避免越位。
// - get_best_position_in_box_for_header: 通常是小禁区前沿或点球点附近。
// - is_ball_coming_towards_me_for_header: 判断球的z坐标较高，且落点是自己。
```