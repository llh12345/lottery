
from urllib.parse import quote

from datetime import datetime, timedelta
import urllib.parse

# 给定的时间字符串
time_str = "Thu Feb 08 2024 10:25:39 GMT+0800"

# 将时间字符串解析为datetime对象
parsed_time = datetime.strptime(urllib.parse.unquote(time_str), "%a %b %d %Y %H:%M:%S GMT")

# 减去10天
new_time = parsed_time - timedelta(days=10)

# 将新时间格式化为字符串并进行 URL 编码
new_time_str = urllib.parse.quote(new_time.strftime("%a %b %d %Y %H:%M:%S GMT%z (%Z)&_=%s"))

print(new_time_str)
