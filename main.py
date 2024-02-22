import time
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
from flask import Flask, render_template
import multiprocessing


BD_TAX = 0.65
NO_HANDI_FACTOR = 1.0
HANDI_FACTOR = 3.0
HANDI_DIFF_FACTOR = 2.0
EXPECT_ODD_DIFF = 0.2
def get_data_from_bd():
    current_time = datetime.now()
    formatted_time = current_time.strftime('%a %b %d %Y %H:%M:%S GMT %z')
    timestamp = int(current_time.timestamp() * 1000)
    params = {'_':timestamp , 'dt': formatted_time}
    paramsEncoded = urlencode(params)
    command = f"curl 'https://bjlot.com/data/200ParlayGetGame.xml?{paramsEncoded}' --insecure"
    result = subprocess.run(command, shell=True, capture_output=True, text=True)
    if result.stdout == "":
        print(f"error {result.stderr}")
        sys.exit(1)
    ordered_dict = xmltodict.parse(result.stdout)

    # 将 OrderedDict 转换为 JSON 字符串
    json_data = json.dumps(ordered_dict, indent=2)
    data_dict = json.loads(json_data)
    data_dict = data_dict["info"]['matches']['matchInfo']
    no_handi_gamesInfoList = []
    handi_games_list = []
    # 判断data_dict是否是list
    if not isinstance(data_dict, list):
        data_dict = [data_dict]
    for items_with_date in data_dict:
        date = items_with_date['matchTime']
        items = items_with_date['matchelem']['item']
        game_date = date['#text']
        for item in items:
            try:
                host = item['host']
                guest = item['guest']
                sp1 = round(float(item['spitem']['sp1']) * BD_TAX , 4)
                sp2 = round(float(item['spitem']['sp2']) * BD_TAX, 4)
                sp3 = round(float(item['spitem']['sp3']) * BD_TAX, 4)
                odds_list = []
                odds_list.append(sp1)
                odds_list.append(sp2)
                odds_list.append(sp3)
                # 小于0代表已开奖
                if sp1 < 0 or sp2 < 0 or sp3 < 0:
                    # print(host, ' ', guest, ' ', item['spitem']['sp1'], ' ', item['spitem']['sp2'], ' ', item['spitem']['sp3'])
                    continue
                # 解析日期字符串为datetime对象
                if not game_date.startswith('20'):
                    game_date = '20' + game_date
                datetime_object = datetime.strptime(game_date, '%Y-%m-%d %H:%M:%S')
                # 格式化为只包含年、月、日的字符串
                formatted_date = datetime_object.strftime('%Y-%m-%d')
                precise_time = item['endTime']
                gameInfo = entity.GameInfo(precise_time, host, guest, odds_list, odds_list, " 北单")
                gameInfo.Handicap_num = int(item['handicap'])
                # 0代表不让球
                if item['handicap'] == '0':
                    no_handi_gamesInfoList.append(gameInfo)
                else:
                    handi_games_list.append(gameInfo)
            except Exception as e:
                print(e)
                continue

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
    companys = quote("1,2")
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
    # 将字符串解析为datetime对象
    dobj1 = datetime.strptime(game1.matchTime, '%Y-%m-%d %H:%M:%S')
    dobj2 = datetime.strptime(game2.matchTime, '%Y-%m-%d %H:%M:%S')
    if dobj1.timestamp() > dobj2.timestamp():
        return False
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
    # return "\033[1;31m" + str(val) + "\033[0m"
    return str(val)

def make_decision(game_info: entity.GameInfo):
    pass

#筛选之后8小时的比赛



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
    # TODO 重构下面逻辑
    if int(game.Handicap_num) > 0 :
        # 客队是强队
        handi_cap_num_bd = float(game.Handicap_num) + 0.5
        handi_diff = abs(abs(handi_cap_num_bd) - abs(max_profit_game_list[3].Handicap_num))
        if handi_diff > HANDI_DIFF_FACTOR:
            print(game.Host, game.Guest, f"handi_diff is {handi_diff}")
            return
        if max_profit_game_list[3].Handicap_num < 0:
            return
        handi_diff = handi_cap_num_bd - float(max_profit_game_list[3].Handicap_num)
        expect_odd = handi_diff * 2 + max_profit_game_list[3].Handicap_Odds[1] + 1
        expect_diff = float(game.Odds[2]) / BD_TAX - expect_odd
        if expect_diff + EXPECT_ODD_DIFF < 0:
            odd_diff = float(game.Odds[2]) / BD_TAX - expect_odd
            handle_print_table(handi_table, game, max_profit_game_list)
            amount = 1000 / float(max_profit_game_list[3].Handicap_Odds[0])
            print("买", max_profit_game_list[3].matchTime, " ", max_profit_game_list[3].Host, " ",
                  f"{max_profit_game_list[3].Handicap_num} " + result_dict[0], " ", max_profit_game_list[3].Handicap_Odds[0], f"总额 {amount}")
            buy_decision = entity.BuyDecision(max_profit_game_list[3], amount, max_profit_game_list[3].Handicap_Odds[0], result_dict[0])
            buy_decision.handi_diff = handi_diff
            buy_decision.odd_diff = abs(odd_diff)
            buy_decision.expect_diff = expect_diff
            store.insert_buy_decision(buy_decision)
            return buy_decision
    elif int(game.Handicap_num) == 0:
        # 主队是强队，强队的期望赔率
        handicap_num = max_profit_game_list[3].Handicap_num
        handicap_odds = max_profit_game_list[3].Handicap_Odds
        if game.Odds[0] < game.Odds[2]:
            handi_diff = 0.5 + handicap_num
            expect_odd = (handicap_odds[0] + 1) + (handi_diff) * 2
            expect_diff = game.Odds[0] / BD_TAX  -  expect_odd
            if expect_diff + EXPECT_ODD_DIFF < 0:
                odd_diff = game.Odds[0] / BD_TAX - expect_odd
                handle_print_table(handi_table, game, max_profit_game_list)
                amount = 1000 / float(handicap_odds[1])
                print("买", max_profit_game_list[3].matchTime, " ", max_profit_game_list[3].Host, " ",
                      f"{max_profit_game_list[3].Handicap_num} " + result_dict[2], " ",
                      max_profit_game_list[3].Handicap_Odds[1], f"总额 {amount}")
                buy_decision = entity.BuyDecision(max_profit_game_list[3], amount, max_profit_game_list[3].Handicap_Odds[1], result_dict[2])
                buy_decision.handi_diff = handi_diff
                buy_decision.odd_diff = abs(odd_diff)
                buy_decision.expect_diff = expect_diff
                store.insert_buy_decision(buy_decision)
                return buy_decision
        else:
            # 客队是强队
            handi_diff = 0.5 - handicap_num
            handicap_num = max_profit_game_list[3].Handicap_num
            expect_odd = (handicap_odds[1] + 1) + (handi_diff) * 2
            expect_diff = game.Odds[2] / BD_TAX - expect_odd
            if  expect_diff + EXPECT_ODD_DIFF < 0:
                odd_diff = game.Odds[2] / BD_TAX - expect_odd
                handle_print_table(handi_table, game, max_profit_game_list)
                amount = 1000 / float(handicap_odds[0])
                print("买", max_profit_game_list[3].matchTime, " ", max_profit_game_list[3].Host, " ",
                      f"{max_profit_game_list[3].Handicap_num} " + result_dict[0], " ",
                      max_profit_game_list[3].Handicap_Odds[0], f"总额 {amount}")
                buy_decision = entity.BuyDecision(max_profit_game_list[3], amount, max_profit_game_list[3].Handicap_Odds[0], result_dict[0])
                buy_decision.handi_diff = handi_diff
                buy_decision.odd_diff = abs(odd_diff)
                buy_decision.expect_diff = expect_diff
                store.insert_buy_decision(buy_decision)
                return buy_decision
    else:
        # 主队是强队
        handi_cap_num_bd = float(game.Handicap_num) - 0.5
        if max_profit_game_list[3].Handicap_num > 0:
            return
        handi_diff = abs(abs(handi_cap_num_bd) - abs(float(max_profit_game_list[3].Handicap_num)))
        if handi_diff > HANDI_DIFF_FACTOR:
            print(game.Host, game.Guest, f"handi_diff is {handi_diff}")
            return
        expect_odd = handi_diff * 2 + max_profit_game_list[3].Handicap_Odds[0] + 1
        expect_diff = float(game.Odds[0]) / BD_TAX - expect_odd
        if expect_diff +  EXPECT_ODD_DIFF < 0:
            odd_diff = float(game.Odds[0]) / BD_TAX - expect_odd
            handle_print_table(handi_table, game, max_profit_game_list)
            amount = 1000 / float(max_profit_game_list[3].Handicap_Odds[1])
            print("买", max_profit_game_list[3].matchTime, " ", max_profit_game_list[3].Host, " ",
                  f"{max_profit_game_list[3].Handicap_num} " + result_dict[2], " ",
                  max_profit_game_list[3].Handicap_Odds[1], f"总额 {amount}")
            buy_decision = entity.BuyDecision(max_profit_game_list[3], amount, max_profit_game_list[3].Handicap_Odds[1], result_dict[2])
            buy_decision.handi_diff = handi_diff
            buy_decision.odd_diff = abs(odd_diff)
            buy_decision.expect_diff = expect_diff
            store.insert_buy_decision(buy_decision)
            return buy_decision

def start_to_get_solution():
    buy_decisions = []
    handi_table = PrettyTable()
    handi_table.field_names = ["时间", "主队", "客队", "类型", "让球", "主胜", "平局", "客胜"]
    # 执行curl命令
    no_handi_games_info_list_bd, handi_games_info_list_bd = get_data_from_bd()
    games_info_list_website = get_data_from_website('')
    handi_games_info_list_bd.extend(no_handi_games_info_list_bd)
    # 处理让球的
    handi_games_info_list_bd = sorted(handi_games_info_list_bd, key=lambda x: x.matchTime, reverse=False)
    for game in handi_games_info_list_bd:
        website_games_list = []
        for game2 in games_info_list_website:
            if is_same_game(game, game2):
                website_games_list.append(game2)
        if len(website_games_list) == 0 or not util.is_after(website_games_list[0], 60 * 24):
            continue
        max_profit_game_list = find_max_odd_from_website(website_games_list)
        buy_decision = handle_handi_game(handi_table, game, max_profit_game_list)
        if buy_decision is not None:
            buy_decisions.append(buy_decision)
    print(handi_table)
    return buy_decisions, handi_table

import os

app = Flask(__name__, template_folder=os.path.join(os.path.dirname(__file__), 'templates'))
@app.route('/test')
def test():
    # 示例数据，实际中可以从数据库或其他来源获取
    buy_decisions, handi_table = start_to_get_solution()

    return render_template('table_template.html', data=buy_decisions)
@app.route('/index')
def index():
    # 示例数据，实际中可以从数据库或其他来源获取

    return "hello world"
def crontab():
    print("start crontab")
    while True:
        print(datetime.now())
        buy_decisions, handi_tables = start_to_get_solution()
        result_str = ''
        for buy_decision in buy_decisions:
            result_str = result_str + f"{buy_decision.game.matchTime} {buy_decision.game.Host} {buy_decision.game.Guest} {buy_decision.odd} {buy_decision.guess} \n"
        print("start to send email")
        time.sleep(60 * 10)
if __name__ == '__main__':
    process1 = multiprocessing.Process(target=crontab)
    process1.start()
    app.run(host='0.0.0.0', port=9191)
    


