import requests
from requests.adapters import HTTPAdapter
from requests.packages.urllib3.poolmanager import PoolManager
import ssl

class SSLAdapter(HTTPAdapter):
    def init_poolmanager(self, connections, maxsize, block=False):
        self.poolmanager = PoolManager(
            num_pools=connections,
            maxsize=maxsize,
            block=block,
            ssl_version=ssl.PROTOCOL_TLS
        )

url = 'https://bjlot.com/data/200ParlayGetGame.xml'
params = {'dt': 'Thu Feb 08 2024 10:25:39 GMT+0800 (中国标准时间)', '_': '1707358418891'}

# 使用自定义的 SSLAdapter 来手动指定 SSL 版本
session = requests.Session()
session.mount('https://', SSLAdapter())

response = session.get(url, params=params)

print(response.text)
