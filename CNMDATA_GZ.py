"""
任务名称
name: CNMDATA_GZ
定时规则
cron: * * * * *
"""

import requests
import os
import json
from datetime import datetime, timedelta, timezone

os.makedirs('./Pull_GZ', exist_ok=True)

# 配置
SERVERCHAN_KEY = os.environ.get("SERVERCHAN_KEY", "")
STATUS_FILE = "./Pull_GZ/last_success.json"
TIMEOUT_MINUTES = 15
print(f"SERVERCHAN_KEY: {'已配置' if os.environ.get('SERVERCHAN_KEY') else '未配置'}")


def load_status():
    """加载状态文件"""
    try:
        if os.path.exists(STATUS_FILE):
            with open(STATUS_FILE, 'r') as f:
                return json.load(f)
    except:
        pass
    return None


def save_status(last_success_time, notified=False):
    """保存状态"""
    try:
        with open(STATUS_FILE, 'w') as f:
            json.dump({
                'last_success': last_success_time.isoformat(),
                'notified': notified
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
    """检查是否超时并发送通知（每次超时只通知一次）"""
    status = load_status()

    if status is None:
        # 首次运行，初始化状态文件，不发通知
        print("首次运行，已初始化状态文件")
        save_status(datetime.now(), notified=False)
        return

    last_success = datetime.fromisoformat(status['last_success'])
    already_notified = status.get('notified', False)
    time_diff = datetime.now() - last_success

    if time_diff > timedelta(minutes=TIMEOUT_MINUTES):
        if already_notified:
            print(f"已超时但通知已发送过，跳过重复通知（距上次成功: {int(time_diff.total_seconds() // 60)} 分钟）")
        else:
            title = "广州雷达图下载异常"
            content = f"已超过 {TIMEOUT_MINUTES} 分钟未成功下载广州雷达图，请检查！"
            send_notification(title, content)
            print(f"已发送超时通知: {content}")
            # 标记已通知，避免重复发送
            save_status(last_success, notified=True)
    else:
        print(f"距上次成功下载 {int(time_diff.total_seconds() // 60)} 分钟，未超时")


# 主要逻辑
# 该站点使用北京时间，延迟约 6 分钟，可根据实际情况调整
local_now = datetime.now(timezone.utc) + timedelta(hours=8) - timedelta(minutes=6)
date_str = local_now.strftime("%Y%m%d")
aligned_minute = (local_now.minute // 6) * 6
aligned_time = local_now.replace(minute=aligned_minute, second=0, microsecond=0)
time_str = aligned_time.strftime("%Y%m%d%H%M%S")
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
            # 下载成功，重置状态（清除已通知标记）
            save_status(datetime.now(), notified=False)
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
