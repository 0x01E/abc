import os
import requests
import time
import schedule
import subprocess

def get_public_ip():
    return subprocess.check_output("curl -s ip.sb", shell=True).decode('utf-8')

def get_network_traffic(interface):
    for line in open('/proc/net/dev', 'r'):
        if interface in line:
            data = line.split('%s:' % interface)[1].split()
            rx_bytes, tx_bytes = (int(data[0]), int(data[8]))
            return rx_bytes, tx_bytes
    return None

def read_previous_traffic(filename):
    if os.path.exists(filename):
        with open(filename, "r") as file:
            rx_gb, tx_gb = map(float, file.read().split())
            return rx_gb, tx_gb
    return 0, 0

def write_current_traffic(filename, rx_gb, tx_gb):
    with open(filename, "w") as file:
        file.write(f"{rx_gb} {tx_gb}")

def send_telegram_message(bot_token, chat_id, message):
    url = f"https://api.telegram.org/bot{bot_token}/sendMessage?chat_id={chat_id}&text={message}"
    try:
        response = requests.get(url)
        response.raise_for_status()
    except requests.exceptions.RequestException as err:
        print (f"机器人推送消息失败: {err}")

def check_alert(total_gb, bot_token, chat_id, limit_gb, remark):
    alert_msg = []
    usage_percentage = total_gb / limit_gb * 100
    server_ip = get_public_ip()
    notice_message = f'''
         ⚠️ 警告
         服务器ID     : {remark}
         服务器IP     : {server_ip}
         已使用流量    : {total_gb} GB
    '''
    if usage_percentage >= 95:
        alert_msg.append(f"{notice_message} \n\n ❗❗❗流量已使用超过95%,即将执行关机!")
        os.system('shutdown -h now')

    elif usage_percentage >= 80:
        alert_msg.append(f"{notice_message} \n\n ❗流量已使用80%\n ")

    if alert_msg:
        send_telegram_message(bot_token, chat_id, '\n'.join(alert_msg))

def daily_report(bot_token, chat_id, filename, remark):
    total_rx_gb, total_tx_gb = read_previous_traffic(filename)
    total_gb = round(total_rx_gb + total_tx_gb, 2)
    server_ip = get_public_ip()
    notice_message = f'''
        📢 每日流量通报: 
         服务器ID     : {remark}
         服务器IP     : {server_ip}
         总使用流量    : {total_gb} GB
    '''
    send_telegram_message(bot_token, chat_id, notice_message)
    
def update_traffic():
    global total_rx_gb, total_tx_gb, total_gb
    previous_rx_gb, previous_tx_gb = read_previous_traffic(filename)   # 读取之前保存的流量数据
    traffic = get_network_traffic(interface)
   
    if traffic:
        rx_bytes, tx_bytes = traffic
        current_rx_gb = round(rx_bytes / (1024 ** 3), 2)
        current_tx_gb = round(tx_bytes / (1024 ** 3), 2)

        total_rx_gb = current_rx_gb if current_rx_gb >= previous_rx_gb else round(previous_rx_gb + current_rx_gb, 2)
        total_tx_gb = current_tx_gb if current_tx_gb >= previous_tx_gb else round(previous_tx_gb + current_tx_gb, 2)
        
        total_gb = round(total_rx_gb + total_tx_gb, 2)

        write_current_traffic(filename, total_rx_gb, total_tx_gb)

        check_alert(total_gb, bot_token, chat_id, limit_gb, remark)  # 检查是否超过限制

filename = 'traffic_data.txt'
interface = 'ens5'
limit_gb = 2048 #GB
remark = "remark"

previous_rx_gb, previous_tx_gb = read_previous_traffic(filename)
traffic = get_network_traffic(interface)

bot_token = "5352801828:AAH72RZcDzXyEAu3FMTRPqYgnqJ8fjx4tms"
chat_id = "-1002008553121"

total_rx_gb, total_tx_gb, total_gb = 0., 0., 0. # 初始化变量

if traffic:
    rx_bytes, tx_bytes = traffic
    current_rx_gb = round(rx_bytes / (1024 ** 3), 2)  # bytes转成GB
    current_tx_gb = round(tx_bytes / (1024 ** 3), 2)  # bytes转成GB

    total_rx_gb = current_rx_gb if current_rx_gb >= previous_rx_gb else round(previous_rx_gb + current_rx_gb, 2)
    total_tx_gb = current_tx_gb if current_tx_gb >= previous_tx_gb else round(previous_tx_gb + current_tx_gb, 2)
    
    total_gb = round(total_rx_gb + total_tx_gb, 2)
    server_ip = get_public_ip()
    startup_message = f'''
        🎉 服务启动成功通知:
         服务器ID   : {remark}
         服务器IP   : {server_ip}
         当前上传⏫  : {total_tx_gb} GB
         当前下载⏬  : {total_rx_gb} GB
    '''

    send_telegram_message(bot_token, chat_id, startup_message)  # 启动成功的通知

    write_current_traffic(filename, total_rx_gb, total_tx_gb)
    #print(f'当前下载流量: {total_rx_gb} GB')
    #print(f'当前上传流量: {total_tx_gb} GB')
    #print(f'当前总流量: {total_gb} GB')

    check_alert(total_gb, bot_token, chat_id, limit_gb, remark) # 检查是否超过限制

    schedule.every().day.at("00:00").do(daily_report, bot_token=bot_token, chat_id=chat_id, filename=filename, remark=remark)
    schedule.every(10).minutes.do(update_traffic)

    while True:
        schedule.run_pending()
        time.sleep(1)

else:
    print(f'找不到网卡: {interface}')