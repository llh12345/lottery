def is_same_team(team1, team2):
    if ("红牛" in team1 or "红牛" in team2) and ("RB" in team1 or "RB" in team2):
        return True
    common_characters = 0
    for char in team1:
        if char in team2:
            common_characters += 1
    return common_characters >= 2