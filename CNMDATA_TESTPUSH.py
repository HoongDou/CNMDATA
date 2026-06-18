"""
任务名称
name: SERVERCHAN_TEST
定时规则
cron: 
"""

import requests
import os
from datetime import datetime

SERVERCHAN_KEY = os.environ.get("SERVERCHAN_KEY", "")

print(f"SERVERCHAN_KEY: {'已配置' if SERVERCHAN_KEY else '未配置'}")

if not SERVERCHAN_KEY:
    print("错误：SERVERCHAN_KEY 未配置，请在青龙面板的环境变量中添加")
    exit(1)

try:
    url = f"https://sctapi.ftqq.com/{SERVERCHAN_KEY}.send"
    now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    response = requests.post(url, data={
        "title": "ServerChan 推送测试",
        "desp": f"测试时间：{now_str}\n\n ServerChan 推送配置正常。"
    }, timeout=10)
    result = response.json()
    if result.get("code") == 0:
        print("推送成功！请确认消息通道是否收到通知")
    else:
        print(f"推送失败，错误信息：{result.get('message')}")
        print(f"完整返回：{result}")
except Exception as e:
    print(f"请求出错：{e}")
