from store import insert_buy_decision, update_game_result, query_no_result_game
from entity import GameInfo, BuyDecision
import os
import subprocess
import json
from datetime import datetime, timedelta
import util

def get_game_result_by_date(date: str) :
    command = f'curl https://odds.zgzcw.com/odds/oyzs_ajax.action -d "type=bd&date={date}&companys=1" -compressed'
    result = subprocess.run(command, shell=True, capture_output=True, text=True)    # curl
    out = result.stdout
    game_info_list = []
    data_dict = json.loads(out)
    for data in data_dict:
        matchTime = data["MATCH_TIME"]
        matchTime = matchTime[:len(matchTime)-2]
        #只保留天数
        matchTime = datetime.strptime(matchTime, "%Y-%m-%d %H:%M:%S")
        matchTime = matchTime.strftime("%Y-%m-%d")
        host = data["HOST_NAME"]
        guest = data["GUEST_NAME"]
        host_goal = data["HOST_GOAL"]
        guest_goal = data["GUEST_GOAL"]
        game_info = GameInfo(matchTime, host, guest, [], [], "")
        game_info.host_goal = host_goal
        game_info.guest_goal = guest_goal
        game_info_list.append(game_info)

    return game_info_list

def update_result(game_list_no_result, game_result_list):
    for game_no_result in game_list_no_result:
        for game_result in game_result_list:
            # if game_result.Host == ""
            if game_no_result.matchTime == game_result.matchTime and util.is_same_team(game_no_result.Host, game_result.Host) and util.is_same_team(game_no_result.Guest, game_result.Guest):
                host_goal = game_result.host_goal
                guest_goal = game_result.guest_goal
                handi_cap_num = game_no_result.handicap_num
                guess = game_no_result.guess
                game_no_result.host_goal = host_goal
                game_no_result.guest_goal = guest_goal
                result = "输"
                if host_goal - guest_goal + handi_cap_num > 0 :
                    if guess == "胜":
                        result = "赢"
                        if host_goal - guest_goal + handi_cap_num == 0.25:
                            result = "赢半"
                    else:
                        result = "输"
                        if host_goal - guest_goal + handi_cap_num == 0.25:
                            result = "输半"
                elif host_goal - guest_goal + handi_cap_num < 0:
                    print(1231)
                    if guess == "负":
                        result = "赢"
                        if host_goal - guest_goal + handi_cap_num == -0.25:
                            result = "赢半"
                    else:
                        result = "输"
                        if host_goal - guest_goal + handi_cap_num == -0.25:
                            result = "输半"
                elif host_goal - guest_goal + handi_cap_num == 0:
                    result = "平"

                update_game_result(game_no_result, result)
if __name__ == '__main__':
    current_time = datetime.now()
    formatted_time = current_time.strftime("%Y-%m-%d %H:%M:%S")
    no_result_game_list = query_no_result_game(formatted_time)
    # 按每一天的比赛分组
    no_result_game_by_date = {}
    for game in no_result_game_list:
        game.matchTime = game.matchTime.strftime("%Y-%m-%d")
        if game.matchTime not in no_result_game_by_date:
            no_result_game_by_date[game.matchTime] = []
        no_result_game_by_date[game.matchTime].append(game)
    result_game_by_date = {}
    for date, no_result_game_list in no_result_game_by_date.items():
        #算出date的前一天
        date_before_1day = datetime.strptime(date, "%Y-%m-%d")
        date_before_1day = date_before_1day - timedelta(days=1)
        date_before_1day = date_before_1day.strftime("%Y-%m-%d")
        if date_before_1day not in result_game_by_date:
            game_result_list = get_game_result_by_date(date_before_1day)
            result_game_by_date[date_before_1day] = game_result_list
        if date not in result_game_by_date:
            game_result_list = get_game_result_by_date(date)
            result_game_by_date[date] = game_result_list
    for date, no_result_game_list in no_result_game_by_date.items():
        #查当天和前一天的结果
        game_result_list = result_game_by_date[date]
        #算出date的前一天
        date_before_1day = datetime.strptime(date, "%Y-%m-%d")
        date_before_1day = date_before_1day - timedelta(days=1)
        date_before_1day = date_before_1day.strftime("%Y-%m-%d")
        if date_before_1day in result_game_by_date:
            game_result_list.extend(result_game_by_date[date_before_1day])
        update_result(no_result_game_list, game_result_list)
    print("done")