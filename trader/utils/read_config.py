# coding=utf-8
#
# Copyright 2016 timercrack
#
# Licensed under the Apache License, Version 2.0 (the "License"); you may
# not use this file except in compliance with the License. You may obtain
# a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations
# under the License.
import sys
import os
import xml.etree.ElementTree as ET
import configparser
from appdirs import AppDirs
from trader import version as app_ver
from pathlib import Path

config_example = """# trader configuration file
[MSG_CHANNEL]
request_pattern = MSG:CTP:REQ:*
request_format = MSG:CTP:REQ:{}
trade_response_prefix = MSG:CTP:RSP:TRADE:
trade_response_format = MSG:CTP:RSP:TRADE:{}:{}
market_response_prefix = MSG:CTP:RSP:MARKET:
market_response_format = MSG:CTP:RSP:MARKET:{}:{}
weixin_log = MSG:LOG:WEIXIN

[TRADE]
command_timeout = 5
ignore_inst = WH,bb,JR,RI,RS,LR,PM,im

[REDIS]
host = 127.0.0.1
port = 6379
db = 0
encoding = utf-8

[MYSQL]
host = 127.0.0.1
port = 3306
db = QuantDB
user = quant
password = 123456

[QuantDL]
api_key = 123456

[Tushare]
token = 123456

[LOG]
level = DEBUG
format = %(asctime)s %(name)s [%(levelname)s] %(message)s
weixin_format = [%(levelname)s] %(message)s
"""

app_dir = AppDirs('trader')
config_file = os.path.join(app_dir.user_config_dir, 'config.ini')
if not os.path.exists(config_file):
    if not os.path.exists(app_dir.user_config_dir):
        os.makedirs(app_dir.user_config_dir)
    with open(config_file, 'wt') as f:
        f.write(config_example)
    print('create config file:', config_file)

config = configparser.ConfigParser(interpolation=None)
config.read(config_file)

# 获取配置文件路径
config_dir = os.path.expanduser('~/.trader')
if not os.path.exists(config_dir):
    os.makedirs(config_dir)

config_path = os.path.join(config_dir, 'config.ini')
if not os.path.exists(config_path):
    print(f'create config file: {config_path}')
    with open(config_path, 'w') as f:
        f.write('''[TRADE]
broker_id = 9999
investor_id = test001
password = test123
command_timeout = 10
ignore_inst = WH,bb,JR,RI,RS,LR,PM,im

[MSG_CHANNEL]
market_response_format = MSG:CTP:RSP:MARKET:{}:{}
trade_response_format = MSG:CTP:RSP:TRADE:{}:{}
request_format = MSG:CTP:REQ:{}

[LOG]
level = DEBUG
format = %%(asctime)s %%(levelname)s %%(message)s
''')

# 读取配置文件
config = configparser.ConfigParser()
config.read(config_path)

# 读取错误码
current_dir = os.path.dirname(os.path.abspath(__file__))
ctp_xml_path = os.path.join(current_dir, 'error.xml')
ctp_errors = {}
for error in ET.parse(ctp_xml_path).getroot():
    error_id = error.get('id')
    try:
        error_id = int(error_id)
    except ValueError:
        continue  # 跳过非数字的id
    ctp_errors[error_id] = error.get('value')
