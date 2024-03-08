import pandas as pd
import matplotlib.pyplot as plt
from datetime import datetime
import store


# 读取CSV文件，假设有两列：'timestamp' 和 'value'
df = pd.read_csv('your_data.csv')

# 将字符串时间戳转换为 datetime 对象
df['timestamp'] = pd.to_datetime(df['timestamp'])

# 设置时间戳为索引
df.set_index('timestamp', inplace=True)

# 根据需要进行各种统计操作
# 例如，计算每天的平均值
daily_mean = df.resample('D').mean()

# 绘制折线图
plt.plot(daily_mean.index, daily_mean['value'], label='daily_avg')

# 添加标题和标签
plt.title('daily_avg')
plt.xlabel('date')
plt.ylabel('value')

# 添加图例
plt.legend()
plt.savefig('line_chart.png')

# 显示图形
plt.show()
