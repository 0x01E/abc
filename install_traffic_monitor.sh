#!/bin/bash

mkdir -p /root/traffic
wget -O /root/traffic/get_traffic.py https://raw.githubusercontent.com/0x01E/abc/main/get_traffic.py

if [ $? -ne 0 ]; then
    echo "无法下载get_traffic.py文件"
    exit 1
fi

apt install -y python3 python3-pip
python_version=$(python3 -c "import sys; print('.'.join(map(str, sys.version_info[:3])))")
echo "Detected Python version: $python_version"

if [[ "$python_version" > "3.9.6" ]]; then
    python3 -m pip install schedule requests time subprocess --break-system-packages
else
    python3 -m pip install schedule requests time subprocess
    
fi


if [ $? -ne 0 ]; then
    echo "无法安装所需的模块"
    exit 1
fi

read -p "请输入remark：" remark

sed -i "s/remark = \"remark\"/remark = \"$remark\"/g" /root/traffic/get_traffic.py

# 创建守护进程配置文件
cat << EOF > /etc/systemd/system/traffics.service
[Unit]
Description=Network Traffic Monitor

[Service]
WorkingDirectory=/root/traffic
ExecStart=/usr/bin/python3 /root/traffic/get_traffic.py
Restart=always

[Install]
WantedBy=multi-user.target
EOF


systemctl daemon-reload

systemctl start traffics.service
systemctl enable traffics.service

echo "安装和配置完成！"
