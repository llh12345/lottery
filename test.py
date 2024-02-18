from datetime import datetime
from urllib.parse import urlencode
import subprocess
import entity
import xmltodict
import json
from prettytable import PrettyTable
import sys
from dataclasses import dataclass
from typing import List

import store

BD_TAX = 0.65
NO_HANDI_FACTOR = 1.0
HANDI_FACTOR = 1.0

def get_data_from_bd():
    with open('yingchao.txt', 'r') as file:
        line = file.readline()
        words = line.split(' ')
        time = words[2]
        host = words[3]
        handicap_num = words[4]
        guest = words[5]
        result = words[6]
    return no_handi_gamesInfoList, handi_games_list


def find_max_odd_from_website(game_info_list: List[entity.GameInfo]):
    company_odds_list = []
    max_win_odds_game_info = entity.GameInfo('', '', '', [-1, -1, -1], [-1, -1], '')
    max_same_odds_game_info = entity.GameInfo('', '', '', [-1, -1, -1], [-1, -1], '')
    max_lost_odds_game_info = entity.GameInfo('', '', '', [-1, -1, -1], [-1, -1], '')
    max_handi_odds_game_info = entity.GameInfo('', '', '', [-1, -1, -1], [-1, -1], '')
    for game_info in game_info_list:
        if max_win_odds_game_info.Odds[0] < game_info.Odds[0]:
            max_win_odds_game_info = game_info
        if max_same_odds_game_info.Odds[1] < game_info.Odds[1]:
            max_same_odds_game_info = game_info
        if max_lost_odds_game_info.Odds[2] < game_info.Odds[2]:
            max_lost_odds_game_info = game_info
        if max_handi_odds_game_info.Handicap_Odds[0] < game_info.Handicap_Odds[0]:
            max_handi_odds_game_info = game_info
    return [max_win_odds_game_info, max_same_odds_game_info, max_lost_odds_game_info, max_handi_odds_game_info]
#date格式 2024-02-07
def get_data_from_website(date: str):
    from urllib.parse import quote
    companys = quote("1,2,3,4,5,6,7")
    command = f"curl 'https://odds.zgzcw.com/odds/oyzs_ajax.action' --data-raw 'type=bd&date={date}&companys=${companys}'"
    result = subprocess.run(command, shell=True, capture_output=True, text=True)
    out = result.stdout
    data_list = json.loads(out)
    gamesInfoList = []
    for data in data_list:
        host = data["HOST_NAME"]
        guest = data["GUEST_NAME"]
        date = data["MATCH_TIME"]
        # 去除date最后一个字符
        date = date[:len(date)-2]
        if len(data["listOdds"]) == 0:
            # print(host, ' ', guest, ' ', '无赔率数据')
            continue
        for odd in data["listOdds"]:
            if "WIN" not in odd or "SAME" not in odd or "LOST" not in odd:
                continue
            list_odds = []
            if "WIN" not in odd or "SAME" not in odd or "LOST" not in odd:
                continue
            list_odds.append(odd["WIN"])
            list_odds.append(odd["SAME"])
            list_odds.append(odd["LOST"])
            game_info = entity.GameInfo(date, host, guest, list_odds, [-1, -1], odd["COMPANY_NAME"])
            if "HANDICAP" in odd:
                handi_cap_num = float(odd["HANDICAP"])
                handi_host_odd = odd["HOST"]
                handi_guest_odd = odd["GUEST"]
                game_info.Handicap_Odds = [handi_host_odd, handi_guest_odd]
                game_info.Handicap_num = handi_cap_num
            gamesInfoList.append(game_info)
    return gamesInfoList

def trimspace(s):
    words = s.split()
    joined_text = ''.join(words)
    return joined_text
import util


def is_same_game(game1: entity.GameInfo, game2: entity.GameInfo):
    game1.Host = trimspace(game1.Host)
    game2.Host = trimspace(game2.Host)
    game1.Guest = trimspace(game1.Guest)
    game2.Guest = trimspace(game2.Guest)

    if util.is_same_team(game1.Host, game2.Host) and util.is_same_team(game1.Guest, game2.Guest):
        return True


    # 用单个空格连接单词
    return False

# odd1是bd

result_dict = {
    0: "胜",
    1: "平",
    2: "负",
}
def convert_to_red(val):
    return "\033[1;31m" + str(val) + "\033[0m"

def make_decision(game_info: entity.GameInfo):
    pass

#筛选之后8小时的比赛
def is_after(game_info:entity.GameInfo):
    from datetime import datetime, timedelta
    # 将字符串解析为datetime对象
    date_object = datetime.strptime(game_info.matchTime, '%Y-%m-%d %H:%M:%S')
    # 获取今天的日期

    current_time = datetime.now()

    # 计算8小时前的时间
    eight_hours_after = current_time + timedelta(minutes=10)

    # 检查日期是否在最近8小时内
    return   current_time <= date_object <= eight_hours_after


def handle_print_table(table, game:entity.GameInfo, game_list: List[entity.GameInfo]):
    table.add_row(
        [game.matchTime, game.Host, game.Guest, convert_to_red("北单"), str(game.Handicap_num), str(game.Odds[0]),
         str(game.Odds[1]), str(game.Odds[2])])

    table.add_row(
        [game_list[0].matchTime, game_list[0].Host, game_list[0].Guest,
         "欧指", "无",
         str(game_list[0].Odds[0]) + f"({game_list[0].Company})",
         str(game_list[1].Odds[1]) + f"({game_list[1].Company})",
         str(game_list[2].Odds[2]) + f"({game_list[2].Company})"])

    table.add_row(
        [game_list[3].matchTime,
         game_list[3].Host, game_list[3].Guest, "让球",
         game_list[3].Handicap_num,
         str(game_list[3].Handicap_Odds[0]) + f"({game_list[3].Company})", "无",
         str(game_list[3].Handicap_Odds[1]) + f"({game_list[3].Company})"])


def handle_handi_game(handi_table, game: entity.GameInfo, max_profit_game_list: [entity.GameInfo]):

    # 北单+1 相当于 对面-1.5（相当于+1.5）
    # 北单-1 相当于 -1.5
    if int(game.Handicap_num) > 0 :
        handi_cap_num_bd = float(game.Handicap_num) + 0.5
        if max_profit_game_list[3].Handicap_num < 0:
            return
        handi_diff = handi_cap_num_bd - float(max_profit_game_list[3].Handicap_num)
        expect_odd = handi_diff * 2 + max_profit_game_list[3].Handicap_Odds[1] + 1
        if float(game.Odds[2]) / BD_TAX < expect_odd - 0.2:
            handle_print_table(handi_table, game, max_profit_game_list)
            amount = 1000 / float(max_profit_game_list[3].Handicap_Odds[0])
            print("买", max_profit_game_list[3].matchTime, " ", max_profit_game_list[3].Host, " ",
                  f"{max_profit_game_list[3].Handicap_num} " + result_dict[0], " ", max_profit_game_list[3].Handicap_Odds[0], f"总额 {amount}")
            buy_decision = entity.BuyDecision(max_profit_game_list[3], amount, max_profit_game_list[3].Handicap_Odds[0], result_dict[0])
            store.insert_buy_decision(buy_decision)
    elif int(game.Handicap_num) == 0:
        handicap_num = max_profit_game_list[3].Handicap_num
        handicap_odds = max_profit_game_list[3].Handicap_Odds
        if game.Odds[0] < game.Odds[2]:
            # 主队是强队，强队的期望赔率
            expect_odd = (handicap_odds[0] + 1) + (0.5) * 2
            if game.Odds[0] / BD_TAX  <  expect_odd - 0.2:
                handle_print_table(handi_table, game, max_profit_game_list)
                amount = 1000 / float(handicap_odds[0])
                print("买", max_profit_game_list[3].matchTime, " ", max_profit_game_list[3].Host, " ",
                      f"{max_profit_game_list[3].Handicap_num} " + result_dict[2], " ",
                      max_profit_game_list[3].Handicap_Odds[0], f"总额 {amount}")
                buy_decision = entity.BuyDecision(max_profit_game_list[3], amount, max_profit_game_list[3].Handicap_Odds[0], result_dict[2])
                buy_decision.handi_diff = 0
                store.insert_buy_decision(buy_decision)
        else:
            # 客队是强队
            expect_odd = (handicap_odds[1] + 1) + (0.5) * 2
            if  game.Odds[2] / BD_TAX < expect_odd - 0.2:
                handle_print_table(handi_table, game, max_profit_game_list)
                amount = 1000 / float(handicap_odds[1])
                print("买", max_profit_game_list[3].matchTime, " ", max_profit_game_list[3].Host, " ",
                      f"{max_profit_game_list[3].Handicap_num} " + result_dict[0], " ",
                      max_profit_game_list[3].Handicap_Odds[1], f"总额 {amount}")
                buy_decision = entity.BuyDecision(max_profit_game_list[3], amount, max_profit_game_list[3].Handicap_Odds[1], result_dict[0])
                buy_decision.handi_diff = 0
                store.insert_buy_decision(buy_decision)
    else:
        handi_cap_num_bd = float(game.Handicap_num) - 0.5
        if max_profit_game_list[3].Handicap_num > 0:
            return
        handi_diff = abs(handi_cap_num_bd) - abs(float(max_profit_game_list[3].Handicap_num))
        expect_odd = handi_diff * 2 + max_profit_game_list[3].Handicap_Odds[1] + 1
        if float(game.Odds[0]) / BD_TAX < expect_odd - 0.2:
            handle_print_table(handi_table, game, max_profit_game_list)
            amount = 1000 / float(max_profit_game_list[3].Handicap_Odds[1])
            print("买", max_profit_game_list[3].matchTime, " ", max_profit_game_list[3].Host, " ",
                  f"{max_profit_game_list[3].Handicap_num} " + result_dict[2], " ",
                  max_profit_game_list[3].Handicap_Odds[1], f"总额 {amount}")
            buy_decision = entity.BuyDecision(max_profit_game_list[3], amount, max_profit_game_list[3].Handicap_Odds[1], result_dict[2])
            store.insert_buy_decision(buy_decision)



if __name__ == '__main__':
    handi_table = PrettyTable()
    handi_table.field_names = ["时间", "主队", "客队", "类型", "让球", "主胜", "平局", "客胜"]
    # 执行curl命令
    no_handi_games_info_list_bd, handi_games_info_list_bd = get_data_from_bd()
    games_info_list_website = get_data_from_website('')
    handi_games_info_list_bd.extend(no_handi_games_info_list_bd)
    # 处理让球的
    for game in handi_games_info_list_bd:
        website_games_list = []
        for game2 in games_info_list_website:
            if is_same_game(game, game2):
                website_games_list.append(game2)
        if len(website_games_list) == 0 or not is_after(website_games_list[0]):
            continue
        max_profit_game_list = find_max_odd_from_website(website_games_list)
        handle_handi_game(handi_table, game, max_profit_game_list)
    print(handi_table)
    print("不让球")


