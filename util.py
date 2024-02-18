import entity
def is_same_team(team1, team2):
    if ("红牛" in team1 or "红牛" in team2) and ("RB" in team1 or "RB" in team2):
        return True
    common_characters = 0
    for char in team1:
        if char in team2:
            common_characters += 1
    return common_characters >= 2

def is_after(game_info:entity.GameInfo, mins):
    from datetime import datetime, timedelta
    # 将字符串解析为datetime对象
    date_object = datetime.strptime(game_info.matchTime, '%Y-%m-%d %H:%M:%S')
    # 获取今天的日期

    current_time = datetime.now()

    # 计算8小时前的时间
    eight_hours_after = current_time + timedelta(minutes=mins)

    # 检查日期是否在最近8小时内
    return  current_time <= date_object <= eight_hours_after