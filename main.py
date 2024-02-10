from datetime import datetime
from urllib.parse import urlencode
import subprocess

import xmltodict
import json
from prettytable import PrettyTable

from dataclasses import dataclass
from typing import List

@dataclass
class SpItem:
    sp1: str
    sp1_v: str
    sp2: str
    sp2_v: str
    sp3: str
    sp3_v: str

@dataclass
class Item:
    no: str
    host: str
    hostFull: str
    guest: str
    guestFull: str
    endTime: str
    drawed: str
    handicap: str
    halfsoccer: str
    soccer: str
    leagueName: str
    leagueColor: str
    matchandstate: str
    matchstopstate: str
    spitem: SpItem
    DateTime: str
    DownTime: str
    DownTime_True: str
    matchcupDesc: str
    gameTypeName: str
    gameTypeColor: str
    rangDanWei: str
    _no: str

@dataclass
class MatchElem:
    item: List[Item]

@dataclass
class MatchData:
    matchTime: str
    matchelem: MatchElem

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
            sp1 = round(float(item['spitem']['sp1']) , 4)
            sp2 = round(float(item['spitem']['sp2']), 4)
            sp3 = round(float(item['spitem']['sp3']), 4)
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
            gameInfo = GameInfo(precise_time, host, guest, odds_list, odds_list)
            gameInfo.Handicap_num = int(item['handicap'])
            # 0代表不让球
            if item['handicap'] == '0':
                no_handi_gamesInfoList.append(gameInfo)
                # print(game_date, ' ', host, ' ', guest, ' ', odds_list[0], ' ', odds_list[1], ' ', odds_list[2])
            else:
                handi_games_list.append(gameInfo)

    return no_handi_gamesInfoList, handi_games_list

class CompanyOdds:
    def __init__(self, CompanyName, Odds: List[float]):
        self.CompanyName = CompanyName
        self.Odds = Odds
def find_max_odd_from_website(listOdds):
    company_odds_list = []
    for odd in listOdds:
        if "WIN" in odd and "SAME" in odd and "LOST" in odd:
            company_odds_list.append(CompanyOdds(odd["COMPANY_NAME"], [odd["WIN"], odd["SAME"], odd["LOST"]]))
    # 找到胜平负最大的赔率和对应的公司名字
    max_win_company_odds = CompanyOdds('', [-1, -1, -1])
    max_same_company_odds = CompanyOdds('', [-1, -1, -1])
    max_lost_company_odds = CompanyOdds('', [-1, -1, -1])
    for company_odds in company_odds_list:
        if company_odds.Odds[0] > max_win_company_odds.Odds[0]:
            max_win_company_odds = company_odds
        if company_odds.Odds[1] > max_same_company_odds.Odds[1]:
            max_same_company_odds = company_odds
        if company_odds.Odds[2] > max_lost_company_odds.Odds[2]:
            max_lost_company_odds = company_odds
    return [max_win_company_odds, max_same_company_odds, max_lost_company_odds]
#date格式 2024-02-07
def get_data_from_website(date: str):
    strs = ''
    for i in range(1, 7):
        strs += str(i) + ','
    companys = urlencode(strs)
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
            if "WIN" not in data['listOdds'][0] or "SAME" not in data['listOdds'][0] or "LOST" not in data['listOdds'][0]:
                continue
            list_odds.append(data["listOdds"][0]["WIN"])
            list_odds.append(data["listOdds"][0]["SAME"])
            list_odds.append(data["listOdds"][0]["LOST"])
            handi_cap_num = float(data["listOdds"][0]["HANDICAP"])
            handi_host_odd = data["listOdds"][0]["HOST"]
            handi_guest_odd = data["listOdds"][0]["GUEST"]
            game_info = GameInfo(date, host, guest, list_odds, [handi_host_odd, handi_guest_odd], '网站')
            game_info.Handicap_num = handi_cap_num
            gamesInfoList.append(game_info)
    return gamesInfoList

def is_same_game(game1: GameInfo, game2: GameInfo):
    if (game1.Host in game2.Host or game2.Host in game1.Host) and (game1.Guest == game2.Guest or game2.Guest == game1.Guest):
        return True
    return False

# odd1是bd
def get_best_solution(odd1, odd2, odd3):
    all_cnt = int(100 * round(odd1, 2)) - 100
    for cnt in range(all_cnt):
        j = (odd3 / (odd2 + odd3)) * cnt
        k = (odd2 / (odd3 + odd2)) * cnt
        cost = cnt + 100
        if j * odd2 > cost and k * odd3 > cost:
            print(cnt + 100, ' ', odd1 * 100,' ',odd2 * j, ' ', odd3 * k)

    # print(cnt + 100, ' ', odd1 * 100,' ',odd2 * j, ' ', odd3 * k)
    # if odd1 <= 2:
    #     return -1
    # # 要保证
    # # 1. 100A - 100 > 0
    # # 2. -100 + x*b + (100-x)*c > 0
    # max_profit = 0
    # profit_choice_j = -1
    # profit_choice_k = -1
    # # 枚举x
    # # A胜利时最多拿到的利润
    # cnt = int(100 * round(odd1,2)) - 100
    # for j in range(cnt):
    #     k = cnt - j
    #     val1 = -100 - k - j + j*odd2
    #     val2 = -100 - k - j + k*odd3
    #     val = min(val1, val2)
    #     if val > max_profit:
    #         max_profit = val
    #         profit_choice_j = j
    #         profit_choice_k = k

    return 100, round(j,2), round(k,2)

class OddInfo:
    def __init__(self, odd, success_type, platform):
        self.odd = odd
        # 胜 平 负
        self.success_type = success_type
        # 平台
        self.platform = platform
dict = {
    0: "胜",
    1: "平",
    2: "负",
}
# 只针对不让球的比赛
def best_invest(game1: GameInfo, game2: GameInfo):
    odd_list = []
    for i in range(3):
        if game1.Odds[i] > game2.Odds[i]:
            odd_list.append(OddInfo(game1.Odds[i], dict[i],'北单'))
        else:
            odd_list.append(OddInfo(game2.Odds[i], dict[i], '网站'))
    for i in range(3):
        for j in range(3):
            for k in range(3):
                if i == j or j == k or i == k:
                    continue
                if odd_list[i].platform != '北单':
                    continue
                profit_choice_i, profit_choice_j, profit_choice_k = get_best_solution(odd_list[i].odd, odd_list[j].odd, odd_list[k].odd)
                # if profit_choice_j == -1:
                #     continue
                # print(game1.Host, ' ', game1.Guest, ' ', '最佳投资方案: ',
                #       odd_list[i].success_type,f'({odd_list[i].odd};{odd_list[i].platform})',profit_choice_i,' ',
                #       odd_list[j].success_type, f'({odd_list[j].odd};{odd_list[j].platform})', profit_choice_j, ' ',
                #       odd_list[k].success_type,f'({odd_list[k].odd};{odd_list[k].platform})', profit_choice_k)
def convert_to_red(val):
    return "\033[1;31m" + str(val) + "\033[0m"

if __name__ == '__main__':
    # 执行curl命令
    no_handi_games_info_list_bd, handi_games_info_list_bd = get_data_from_bd()
    games_info_list_website = get_data_from_website('')
    # for game in games_info_list_bd:
    #     print(game.Host, ' ', game.Guest, ' ', game.Odds)
    handi_table = PrettyTable()
    handi_table.field_names = ["时间", "主队", "客队", "类型", "让球", "主胜", "平局", "客胜"]
    for game in handi_games_info_list_bd:
        for game2 in games_info_list_website:
            if is_same_game(game, game2):
                minVal = game.Odds[0]
                maxVal = game.Odds[0]
                for odd in game.Odds:
                    minVal = min(minVal, odd)
                    maxVal = max(maxVal, odd)
                if maxVal - minVal > 2.5 :
                    handi_table.add_row([game.matchTime, game.Host, game.Guest, convert_to_red("北单"), str(game.Handicap_num), str(game.Odds[0]), str(game.Odds[1]), str(game.Odds[2])])
                    handi_table.add_row([game2.matchTime, game2.Host, game2.Guest, "欧指", "无", str(game2.Odds[0]), str(game2.Odds[1]), str(game2.Odds[2])])
                    handi_table.add_row([game2.matchTime, game2.Host, game2.Guest, "让球", game2.Handicap_num, str(game2.Handicap_Odds[0]), "无", str(game2.Handicap_Odds[1])])
    no_handi_table = PrettyTable()
    no_handi_table.field_names = ["时间", "主队", "客队", "类型", "让球", "主胜", "平局", "客胜"]
    for game in no_handi_games_info_list_bd:
        for game2 in games_info_list_website:
            if is_same_game(game, game2):
                if (game.Odds[0] / game2.Odds[0] > 1.7) or (game.Odds[1]/game2.Odds[1] > 1.7) or (game.Odds[2]/game2.Odds[2] > 1.7):
                    if game.Odds[0] / game2.Odds[0] > 1.7:
                        game.Odds[0] = convert_to_red(game.Odds[0])
                    if game.Odds[1] / game2.Odds[1] > 1.7:
                        game.Odds[1] = convert_to_red(game.Odds[1])
                    if game.Odds[2] / game2.Odds[2] > 1.7:
                        game.Odds[2] = convert_to_red(game.Odds[2])
                    no_handi_table.add_row(
                        [game.matchTime, game.Host, game.Guest, convert_to_red("北单"), str(game.Handicap_num), str(game.Odds[0]),
                         str(game.Odds[1]), str(game.Odds[2])])
                    no_handi_table.add_row(
                        [game2.matchTime, game2.Host, game2.Guest, "欧指", "无", str(game2.Odds[0]), str(game2.Odds[1]),
                         str(game2.Odds[2])])
                    no_handi_table.add_row([game2.matchTime, game2.Host, game2.Guest, "让球", game2.Handicap_num,
                                   str(game2.Handicap_Odds[0]), "无", str(game2.Handicap_Odds[1])])
    print(handi_table)
    print(no_handi_table)


