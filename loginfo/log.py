# / -*-codeing = utf-8  -*-
# TIME : 2022/12/5 12:01
# File : log.py
import logging
import os
import datetime
from time import strftime


def init_log():
    now = datetime.datetime.now()
    save_info = now.strftime("%Y%m%d-%H%M%S")
    save_info = str(save_info) + ".log"
    logging.basicConfig(  # 针对 basicConfig 进行配置(basicConfig 其实就是对 logging 模块进行动态的调整，之后可以直接使用)
        level=logging.INFO,  # INFO 等级以下的日志不会被记录
        format='%(asctime)s %(filename)s[line:%(lineno)d] %(levelname)s %(message)s',  # 日志输出格式
        filename=save_info,  # 日志存放路径(存放在当前相对路径)
        filemode='w',  # 输入模式；如果当前我们文件已经存在，可以使用 'a' 模式替代 'w' 模式
        # 与文件写入的模式相似，'w' 模式为没有文件时创建文件；'a' 模式为追加内容写入日志文件
    )

    return logging
