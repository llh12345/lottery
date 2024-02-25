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
    # eight_hours_after = current_time + timedelta(hours=8)

    # 检查日期是否在最近8小时内
    return  current_time <= date_object <= eight_hours_after




import smtplib
from email.mime.text import MIMEText

# SMTP服务器配置
smtp_server = 'smtp.qq.com'
smtp_port = 587  # 根据你的服务器配置更改
smtp_username = '814768750@qq.com'
smtp_password = 'frskdgqzwpzwbefi'

# 电子邮件内容
from_address = '814768750@qq.com'

def send_email(subject, body, to_address):
    # 建立与SMTP服务器的连接
    with smtplib.SMTP(smtp_server, smtp_port) as server:
        # 如果使用安全连接，请启动TLS
        server.starttls()

        # 使用你的凭据登录SMTP服务器
        server.login(smtp_username, smtp_password)
        # 创建MIMEText对象
        msg = MIMEText(body)
        msg['Subject'] = subject
        msg['From'] = from_address
        msg['To'] = to_address
        # 发送邮件
        server.sendmail(from_address, to_address, msg.as_string())


