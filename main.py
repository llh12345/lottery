from datetime import datetime
from urllib.parse import urlencode
import subprocess

import xmltodict
import json
from prettytable import PrettyTable
import sys
from dataclasses import dataclass
from typing import List


BD_TAX = 0.65
NO_HANDI_FACTOR = 1.0
HANDI_FACTOR = 1.0
class GameInfo:
    def __init__(self, matchTime, Host, Guest, Odds: List[float], HandiCapOdds: List[float], Company: str):
        self.matchTime = matchTime
        self.Host = Host
        self.Guest = Guest
        self.Odds = Odds
        self.Handicap_num = 0.0
        # 北单的话，handiCapOdds和Odds相同
        self.Handicap_Odds = HandiCapOdds
        self.Company = Company
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
    data_dict = data_dict["info"]['matchesp']['matchInfo']
    print(data_dict[0]['matchTime'])
    no_handi_gamesInfoList = []
    handi_games_list = []
    for items_with_date in data_dict:
        date = items_with_date['matchTime']
        items = items_with_date['matchelem']['item']
        game_date = date['#text']
        for item in items:
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
            datetime_object = datetime.strptime(game_date, '%Y-%m-%d %H:%M:%S')
            # 格式化为只包含年、月、日的字符串
            formatted_date = datetime_object.strftime('%Y-%m-%d')
            precise_time = item['endTime']
            gameInfo = GameInfo(precise_time, host, guest, odds_list, odds_list, " 北单")
            gameInfo.Handicap_num = int(item['handicap'])
            # 0代表不让球
            if item['handicap'] == '0':
                no_handi_gamesInfoList.append(gameInfo)
                # print(game_date, ' ', host, ' ', guest, ' ', odds_list[0], ' ', odds_list[1], ' ', odds_list[2])
            else:
                handi_games_list.append(gameInfo)

    return no_handi_gamesInfoList, handi_games_list

class CompanyOdds:
    def __init__(self, CompanyName, Odds: List[float], handiCapNum):
        self.CompanyName = CompanyName
        self.Odds = Odds
        self.handiCapNum = handiCapNum
def find_max_odd_from_website(game_info_list: List[GameInfo]):
    company_odds_list = []
    max_win_odds_game_info = GameInfo('', '', '', [-1, -1, -1], [-1, -1], '')
    max_same_odds_game_info = GameInfo('', '', '', [-1, -1, -1], [-1, -1], '')
    max_lost_odds_game_info = GameInfo('', '', '', [-1, -1, -1], [-1, -1], '')
    max_handi_odds_game_info = GameInfo('', '', '', [-1, -1, -1], [-1, -1], '')
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
            game_info = GameInfo(date, host, guest, list_odds, [-1, -1], odd["COMPANY_NAME"])
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
def is_same_game(game1: GameInfo, game2: GameInfo):
    game1.Host = trimspace(game1.Host)
    game2.Host = trimspace(game2.Host)
    game1.Guest = trimspace(game1.Guest)
    game2.Guest = trimspace(game2.Guest)
    if (game1.Host in game2.Host or game2.Host in game1.Host) and (game1.Guest in game2.Guest or game2.Guest in game1.Guest):
        return True


    # 用单个空格连接单词
    return False

# odd1是bd

class OddInfo:
    def __init__(self, odd, success_type, platform):
        self.odd = odd
        # 胜 平 负
        self.success_type = success_type
        # 平台
        self.platform = platform
result_dict = {
    0: "胜",
    1: "平",
    2: "负",
}
def convert_to_red(val):
    return "\033[1;31m" + str(val) + "\033[0m"

def make_decision(game_info: GameInfo):
    pass
def is_today(game_info:GameInfo):
    from datetime import datetime
    # 将字符串解析为datetime对象
    date_object = datetime.strptime(game_info.matchTime, '%Y-%m-%d %H:%M:%S')
    # 获取今天的日期
    date_object_truncated = date_object.replace(hour=0, minute=0, second=0, microsecond=0)
    today_date = datetime.now().date()
    # 比较日期部分是否相等
    return date_object_truncated.date() == today_date


def handle_print_table(table, game:GameInfo, game_list: List[GameInfo]):
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


def handle_handi_game(handi_table, game: GameInfo, website_games_list: [GameInfo]):
    # 北单+1 相当于 对面-1.5（相当于+1.5）
    # 北单-1 相当于 -1.5
    if int(game.Handicap_num) > 0 :
        handi_cap_num_bd = float(game.Handicap_num) + 0.5
        if website_games_list[3].Handicap_num < 0:
            return
        handi_diff = handi_cap_num_bd - float(website_games_list[3].Handicap_num)
        odd_diff = float(game.Odds[2]) / BD_TAX - float(website_games_list[3].Handicap_Odds[1]) - 1

        if odd_diff > handi_diff * 2:
            handle_print_table(handi_table, game, website_games_list)
            amount = 1000 / float(game.Odds[2])
            print("买", website_games_list[3].matchTime, " ", website_games_list[3].Host, " ",
                  f"{website_games_list[3].Handicap_num} " + result_dict[2], " ", website_games_list[3].Odds[2], f"总额 {amount}")

    else:
        handi_cap_num_bd = float(game.Handicap_num) - 0.5
        if website_games_list[3].Handicap_num > 0:
            return
        handi_diff = abs(handi_cap_num_bd) - abs(float(website_games_list[3].Handicap_num))
        odd_diff = float(game.Odds[0]) / BD_TAX - float(website_games_list[3].Handicap_Odds[0]) - 1
        if odd_diff > handi_diff * 2:
            handle_print_table(handi_table, game, website_games_list)
            amount = 1000 / float(game.Odds[0])
            print("买", website_games_list[3].matchTime, " ", website_games_list[3].Host, " ",
                  f"{website_games_list[3].Handicap_num} " + result_dict[0], " ", website_games_list[3].Odds[0], f"总额 {amount}")


if __name__ == '__main__':
    handi_table = PrettyTable()
    handi_table.field_names = ["时间", "主队", "客队", "类型", "让球", "主胜", "平局", "客胜"]
    # 执行curl命令
    no_handi_games_info_list_bd, handi_games_info_list_bd = get_data_from_bd()
    games_info_list_website = get_data_from_website('')


    # 处理让球的
    for game in handi_games_info_list_bd:
        website_games_list = []
        for game2 in games_info_list_website:
            if is_same_game(game, game2):
                website_games_list.append(game2)
        if len(website_games_list) == 0 or not is_today(website_games_list[0]):
            continue
        handle_handi_game(handi_table, game, website_games_list)
    print(handi_table)
    print("不让球")
    no_handi_table = PrettyTable()
    no_handi_table.field_names = ["时间", "主队", "客队", "类型", "让球", "主胜", "平局", "客胜"]
    for game in no_handi_games_info_list_bd:
        website_games_list = []
        for game2 in games_info_list_website:
            if is_same_game(game, game2):
                website_games_list.append(game2)
        if len(website_games_list) == 0 or not is_today(website_games_list[0]):
            continue
        game_list = find_max_odd_from_website(website_games_list)
        # 不让球的筛选条件
        if (game.Odds[0] - game_list[0].Odds[0] > NO_HANDI_FACTOR) or \
                (game.Odds[1] - game_list[1].Odds[1] > NO_HANDI_FACTOR) or \
                (game.Odds[2] - game_list[2].Odds[2] > NO_HANDI_FACTOR):
            if game.Odds[0] - game_list[0].Odds[0] > NO_HANDI_FACTOR:
                amount = str(float(1000)/float(game.Odds[0]))
                game.Odds[0] = convert_to_red(game.Odds[0])
                print("买", " ", game_list[0].matchTime, " ", game.Host, " ",  f"{game.Handicap_num} 赢", " " + game.Odds[0], f"总额 {amount}")
            if game.Odds[1] / game_list[1].Odds[1] > NO_HANDI_FACTOR:
                amount = str(float(1000)/float(game.Odds[1]))
                game.Odds[1] = convert_to_red(game.Odds[1])
                print("买", " ", game_list[0].matchTime, " ", game.Host, " ",  f"{game.Handicap_num} 平", " " + game.Odds[1], f"总额 {amount}")
            if game.Odds[2] / game_list[2].Odds[2] > NO_HANDI_FACTOR:
                amount = str(float(1000)/float(game.Odds[2]))
                game.Odds[2] = convert_to_red(game.Odds[2])
                print("买", " ", game_list[0].matchTime, " ", game.Host, " ",  f"{game.Handicap_num} 负", " " + game.Odds[2], f"总额 {amount}")

            handle_print_table(no_handi_table, game, game_list)

    print(no_handi_table)


