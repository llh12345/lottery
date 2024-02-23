import mysql.connector

import entity
import util
# 填写数据库连接信息
host = "localhost"
user = "remote"
password = "YX2021@greendog"
database = "lottery"

# 创建连接
conn = mysql.connector.connect(
    host=host,
    user=user,
    password=password,
    database=database
)

def insert_buy_decision(buy_decision:entity.BuyDecision):
    if not util.is_after(buy_decision.game, 15):
        return
    cursor = conn.cursor()
    from datetime import datetime
    t = datetime.now()
    select_query = "SELECT * FROM buy where match_time =%s and host = %s and guest = %s"
    cursor.execute(select_query, (buy_decision.game.matchTime, buy_decision.game.Host, buy_decision.game.Guest))
    result = cursor.fetchall()
    if len(result) > 0:
        return
    handi_diff = 0
    if buy_decision.handi_diff is not None:
        handi_diff = buy_decision.handi_diff
    odd_diff = -1
    if buy_decision.odd_diff is not None:
        odd_diff = buy_decision.odd_diff
    sql = f"INSERT INTO buy" + f"(match_time, host, guest, website_type, handicap_num, amount, created_at,odd,guess,game_type, handi_diff, odd_diff) " + \
                   f"VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s) "
    data_to_insert = (buy_decision.game.matchTime,
                      buy_decision.game.Host,
                      buy_decision.game.Guest,
                      buy_decision.game.Company,
                      buy_decision.game.Handicap_num,
                      buy_decision.amount,
                      t,
                      buy_decision.odd,
                      buy_decision.guess,
                      "让球",
                      handi_diff,
                      odd_diff
                      )
    print("%s %s" % (sql, data_to_insert))
    cursor.execute(sql, data_to_insert)
    conn.commit()

def update_game_result(game_info:entity.GameInfo, result: str):
    print(game_info.matchTime, game_info.Host, game_info.Guest, game_info.host_goal, game_info.guest_goal, result)
    sql = "UPDATE buy SET result = %s, host_goal = %s, guest_goal = %s WHERE DATE(match_time) = %s and host = %s and guest = %s"
    cursor = conn.cursor()
    cursor.execute(sql, (result, game_info.host_goal, game_info.guest_goal,game_info.matchTime, game_info.Host, game_info.Guest))
    conn.commit()

# 查找某个日期前所有未有结果的比赛
def query_no_result_game(date_before) -> list[entity.GameInfo]:
    sql = "SELECT match_time, host, guest, website_type, handicap_num, guess FROM buy WHERE (result is NULL or result = '') and match_time < %s"
    cursor = conn.cursor()
    cursor.execute(sql, [date_before])
    result = cursor.fetchall()
    game_info_list = []
    for row in result:
        match_time = row[0]
        host = row[1]
        guest = row[2]
        website_type = row[3]
        game_info = entity.GameInfo(match_time, host, guest, [], [], website_type)
        game_info.handicap_num = row[4]
        game_info.guess = row[5]
        game_info_list.append(game_info)
    return game_info_list


if __name__ == '__main__':
    game_info = entity.GameInfo("2023-01-01 00:00:00", "host", "guest", [1.0, 2.0, 3.0], [1.0, 2.0, 3.0], "company")
    buy_decision = entity.BuyDecision(game_info, 1.0, 2.0, "win")
    buy_decision.handi_diff = 0.75
    buy_decision.odd_diff = 0.75

    insert_buy_decision(buy_decision)
    conn.commit()
    conn.close()
    pass