def is_same_team(team1, team2):
    common_characters = 0
    for char in team1:
        if char in team2:
            common_characters += 1
    return common_characters >= 2