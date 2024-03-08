import mysql.connector
import entity
import util
# 填写数据库连接信息
host = "localhost"
user = "remote"
password = "YX2021@greendog"
database = "lottery"
from datetime import datetime, timedelta
import logging
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')

# 创建连接
conn = mysql.connector.connect(
    host=host,
    user=user,
    password=password,
    database=database
)

def insert_buy_decision(buy_decision:entity.BuyDecision):
    if not util.is_after(buy_decision.game, 5):
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
    odd_diff = -1
    expect_diff = -1
    try:
        if buy_decision.handi_diff is not None:
            handi_diff = buy_decision.handi_diff
        if buy_decision.odd_diff is not None:
            odd_diff = buy_decision.odd_diff
        if buy_decision.expect_diff is not None:
            expect_diff = buy_decision.expect_diff
    except Exception as e:
        print(e)
    sql = f"INSERT INTO buy" + f"(match_time, host, guest, website_type, handicap_num, amount, created_at,odd,guess,game_type, handi_diff, odd_diff, expect_diff, league, hot_value, strategy) " + \
                   f"VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s) "
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
                      odd_diff,
                      expect_diff,
                      buy_decision.game.League,
                      buy_decision.Hot_Value,
                      buy_decision.Strategy)
    print("%s %s" % (sql, data_to_insert))
    cursor.execute(sql, data_to_insert)
    conn.commit()

def update_game_result(game_info:entity.GameInfo, result: str):
    print(game_info.matchTime, game_info.Host, game_info.Guest, game_info.host_goal, game_info.guest_goal, result)
    sql = "UPDATE buy SET result = %s, host_goal = %s, guest_goal = %s WHERE DATE(match_time) = %s and host = %s and guest = %s and match_time <= SUBTIME(CURRENT_TIMESTAMP, '2:20:0')"
    cursor = conn.cursor()
    cursor.execute(sql, (result, game_info.host_goal, game_info.guest_goal,game_info.matchTime, game_info.Host, game_info.Guest))
    conn.commit()

# 查找某个日期前所有未有结果的比赛
def query_no_result_game(date_before) -> list[entity.GameInfo]:
    # import datetime
    # date_before_str = '2024-02-24 20:00:00'
    # date_before = datetime.strptime(date_before_str, '%Y-%m-%d %H:%M:%S')

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

def calculate_suiccess_rate(start_date, end_date):
    sql1 = '''
    select sum(odd) as r from (
    select sum(odd) as odd FROM lottery.buy 
    where match_time >= %s and match_time <= %s and result like '赢'
    union
    select sum(odd/2) as odd from lottery.buy
    where match_time >= %s and match_time <= %s and result like '赢半') as f
    '''
    cursor = conn.cursor()
    cursor.execute(sql1,[start_date, end_date, start_date, end_date])
    result = cursor.fetchall()
    success=result[0][0]


    sql2 = '''
    select sum(odd) as r from (
    select sum(1) as odd FROM lottery.buy 
    where match_time > %s and match_time <= %s and result like '输'
    union
    select sum(0.5) as odd from lottery.buy
    where match_time > %s and match_time <= %s and result like '输半') as f
    '''
    cursor = conn.cursor()
    cursor.execute(sql2,[start_date, end_date, start_date, end_date])
    result = cursor.fetchall()
    lost=result[0][0]
    return success-lost

def select_last_7days_game(start_date, end_date):
    sql = '''
    select res1 + res2 as res, %s as start_date, %s as end_date from(
    select sum(odd) as res1 from (
    select sum(odd) as odd FROM lottery.buy 
    where match_time > %s and match_time < %s and result like '赢'
    union
    select sum(odd/2) as odd from lottery.buy
    where match_time > %s and match_time < %s and result like '赢半') as f) as f1,

    (select -sum(odd) as res2 from (
    select sum(1) as odd FROM lottery.buy 
    where match_time > %s and match_time < %s and result like '输'
    union
    select sum(0.5) as odd from lottery.buy
    where match_time > %s and match_time < %s and result like '输半') as f) as f2;
    '''
    cursor = conn.cursor()
    cursor.execute(sql,[start_date, end_date, start_date, end_date, start_date, end_date, start_date, end_date,start_date, end_date])
    result = cursor.fetchall()
    res=result[0][0]
    start_date=result[0][1]
    end_date=result[0][2]
    return res, start_date, end_date
def last_guess_game(num):
    sql = '''
    select match_time, host, guest, website_type, handicap_num, guess, odd, league, result, hot_value, strategy
    from buy
    ORDER BY match_time desc limit %s
    ''' 
    cursor = conn.cursor()
    cursor.execute(sql,[num])
    result = cursor.fetchall()
    buy_decision_list = []
    for row in result:
        match_time = row[0]
        host = row[1]
        guest = row[2]
        website_type = row[3]
        handicap_num = row[4]
        guess = row[5]
        odd = row[6]
        league = row[7]
        result = row[8]
        hot_value = row[9]
        strategy = row[10]
        game_info = entity.GameInfo(match_time, host, guest, [], [], website_type)
        game_info.Handicap_num = handicap_num
        game_info.League = league
        game_info.guess = guess
        buy_decision = entity.BuyDecision(game_info,0, odd, guess)
        if result == None or result == '':
            result = '未知'
        buy_decision.Result = result
        buy_decision.Hot_Value = hot_value
        buy_decision.Strategy = strategy
        buy_decision_list.append(buy_decision)
    return buy_decision_list

if __name__ == '__main__':
    # current_time = datetime.now()
    # previous_day = current_time - timedelta(days=1)
    # formatted_time = previous_day.strftime("%Y-%m-%d %H:%M:%S")
    # calculate_suiccess_rate(formatted_time)
    from datetime import datetime, timedelta
    import csv

    # 设定起始日期和结束日期
    current_date = datetime.now()
    with open('tongji.csv', 'w', newline='') as csv_file:
        csv_writer = csv.writer(csv_file)
        csv_writer.writerow(['value', 'timestamp'])
        for i in range(20):
            start_date = current_date -  timedelta(days=i)
            next_date = start_date + timedelta(days=1)
            res = select_last_7days_game(start_date, next_date)
            timestamp_format = '%Y-%m-%d %H:%M:%S.%f'

            # print(res[1])
            # date_object = datetime.strptime(res[1], timestamp_format)
            # t = str(date_object.month)+ "." + str(date_object.day)
            t = res[1]
            if res[0] == None:
                res = (0, t)
            csv_writer.writerow([res[0], t])
    # # 遍历每一天
    # with open('tongji.csv', 'w', newline='') as csv_file:
    #     csv_writer = csv.writer(csv_file)
    #     csv_writer.writerow(['value', 'timestamp'])
    #     current_date = start_date
    #     while current_date <= end_date:
    #         next_date = current_date + timedelta(days=1)
    #         res  = select_last_7days_game(current_date.date(), next_date.date())
    #         if res[0] == None:
    #             res = (0, res[1])
            
    #         csv_writer.writerow([res[0], res[1]])
    #         current_date = next_date
    
    import pandas as pd
    import matplotlib.pyplot as plt
    from datetime import datetime
    df = pd.read_csv('tongji.csv')

    df['timestamp'] = pd.to_datetime(df['timestamp'])

    df.set_index('timestamp', inplace=True)

    # 根据需要进行各种统计操作
    # 例如，计算每天的平均值
    daily_mean = df.resample('D').mean()

    # 绘制折线图
    plt.plot(daily_mean.index, daily_mean['value'], label='daily_avg')

    # 添加标题和标签
    plt.title('recent_lottery_status')
    plt.xlabel('date')
    plt.ylabel('win_odd')

    # 添加图例
    plt.legend()
    plt.savefig('line_chart.png')

    # 显示图形
    plt.show()