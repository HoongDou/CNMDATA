# new Env('CNMDATA_GZ')
# cron: * * * * *


import requests
import os
import json
from datetime import datetime, timedelta, timezone

os.makedirs('./Pull_GZ', exist_ok=True)

# 配置
SERVERCHAN_KEY = os.environ.get("SERVERCHAN_KEY", "")
STATUS_FILE = "./Pull_GZ/last_success.json"
TIMEOUT_MINUTES = 15


def load_last_success_time():
    """加载上次成功的时间"""
    try:
        if os.path.exists(STATUS_FILE):
            with open(STATUS_FILE, 'r') as f:
                data = json.load(f)
                return datetime.fromisoformat(data['last_success'])
    except:
        pass
    return None


def save_last_success_time():
    """保存当前时间为上次成功时间"""
    try:
        with open(STATUS_FILE, 'w') as f:
            json.dump({
                'last_success': datetime.now().isoformat()
            }, f)
    except Exception as e:
        print(f"保存状态文件失败: {e}")


def send_notification(title, content):
    """发送 ServerChan 通知"""
    if not SERVERCHAN_KEY:
        print("ServerChan SendKey 未配置，跳过通知")
        return
    try:
        url = f"https://sctapi.ftqq.com/{SERVERCHAN_KEY}.send"
        response = requests.post(url, data={
            "title": title,
            "desp": content
        }, timeout=10)
        result = response.json()
        if result.get("code") == 0:
            print("ServerChan 通知发送成功")
        else:
            print(f"ServerChan 通知发送失败: {result.get('message')}")
    except Exception as e:
        print(f"发送 ServerChan 通知时出错: {e}")


def check_timeout_and_notify():
    """检查是否超时并发送通知"""
    last_success = load_last_success_time()
    if last_success:
        time_diff = datetime.now() - last_success
        if time_diff > timedelta(minutes=TIMEOUT_MINUTES):
            title = "广州雷达图下载异常"
            content = f"已超过 {TIMEOUT_MINUTES} 分钟未成功下载广州雷达图，请检查！"
            send_notification(title, content)
            print(f"已发送超时通知: {content}")


# 主要逻辑
# 该站点使用北京时间，延迟约 6 分钟，可根据实际情况调整
local_now = datetime.now(timezone.utc) + timedelta(hours=8) - timedelta(minutes=6)
date_str = local_now.strftime("%Y%m%d")
time_str = local_now.strftime("%Y%m%d%H%M00")
url = f"http://www.tqyb.com.cn/data/swan/mcr/{date_str}/{time_str}_gz.png"
print(f"Downloading from URL: {url}")

try:
    response = requests.get(url, timeout=30)
    if response.status_code == 200:
        filename = f"./Pull_GZ/{local_now.strftime('%Y%m%d%H%M%S')}.png"
        try:
            with open(filename, "wb") as file:
                file.write(response.content)
            print(f"图片保存成功！文件名: {filename}")
            save_last_success_time()
        except Exception as e:
            print(f"保存文件时出错: {e}")
            check_timeout_and_notify()
    else:
        print(f"下载失败，可能当前图片未更新，属于正常情况。状态码: {response.status_code}")
        check_timeout_and_notify()

except requests.RequestException as e:
    print(f"请求异常: {e}")
    check_timeout_and_notify()
except Exception as e:
    print(f"其他异常: {e}")
    check_timeout_and_notify()
