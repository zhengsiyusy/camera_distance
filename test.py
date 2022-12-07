# / -*-codeing = utf-8  -*-
# TIME : 2022/12/5 16:57
# File : test
from datetime import datetime
import os
import sys
import sys

import time
from PySide2.QtWidgets import QApplication
from PySide2.QtUiTools import QUiLoader
from PySide2.QtCore import QFile
from PySide2.QtGui import *
import requests
import re
import json
from pprint import pprint
import os
import threading
from playsound import playsound  # 播放音频模块
from threading import Thread


class Stats:  # 定义类
    def __init__(self):  # 导入UI窗口
        # 从文件中加载UI界面
        qfle_stats = QFile('界面.ui')  # 导入UI界面固定写法
        qfle_stats.open(QFile.ReadOnly)  # 导入UI界面固定写法
        qfle_stats.close()  # 导入UI界面固定写法

        self.ui = QUiLoader().load(qfle_stats)  # 定义窗口
        self.ui.pushButton.clicked.connect(self.abc)  # 按纽点击函数 BUtton要与界面中的按纽名字一致
        self.ui.tableView.clicked.connect(self.table_left_click)  # 单击表格信table_left_click为ui预定义函数
        self.ui.pushButton_2.clicked.connect(self.bendi)  # 打开本地目录

    def table_left_click(self, item):  # ui右键单击的预定义信号item为我们点击的单元格

        行标 = item.row()  # 获取行标
        列标 = item.column()  # 获取列标
        print(列标)
        if 列标 == 4:

            歌名 = self.ui.model.item(行标, 0).text()  # 获取实列数据中的坐标数据
            CID = self.ui.model.item(行标, 1).text()  # 获取实列数据中的坐标数据
            ID = self.ui.model.item(行标, 2).text()  # 获取实列数据中的坐标数据
            print(歌名, CID, ID)
            t1 = threading.Thread(target=self.xiazai, args=(歌名, CID, ID,))  # 传递参数 args=参数后面加一个逗号
            t1.start()
            t1.join()
        elif 列标 == 5:
            歌名 = self.ui.model.item(行标, 0).text()
            CID = self.ui.model.item(行标, 1).text()
            ID = self.ui.model.item(行标, 2).text()
            print(歌名, CID, ID)
            t1 = threading.Thread(target=self.xiazai_yingyue, args=(歌名, CID, ID,))  # 传递参数 args=参数后面加一个逗号
            t1.start()
            t1.join()

    def abc(self):
        self.ui.label_3.setText(' ')
        url = self.ui.lineEdit.text()
        url2 = re.findall('https://www.bbbb.com/video/' + '(.*?)' + '(\?|/)', url)[0]
        url2 = url2[0]
        print(url2)
        url3 = 'https://api.bbbb.com/x/player/pagelist?bvid=%s&jsonp=jsonp' % url2
        # print(url3)

        headers = {

            'user-agent': 'Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/78.0.3904.108 Safari/537.36',
            'referer': 'https://www.bilibili.com/'
        }

        html_data = requests.get(url3, headers=headers).text

        video_data = json.loads(html_data)

        data5 = len(video_data['data'])
        print(data5)

        self.ui.model = QStandardItemModel(data5, 5)
        self.ui.model.setHorizontalHeaderLabels(['歌名', 'CID', 'ID', '图片', '下载视频', '下载音乐'])
        for i in range(data5):
            data1 = video_data['data'][i]['part']
            data1 = re.sub('[!@#$ ?<>(){}|,.。/.-]', '', data1)
            data2 = video_data['data'][i]['cid']  # Cid
            data3 = url2  # ID

            data6 = '下载'
            data7 = '下载'

            self.ui.model.setItem(i, 0, QStandardItem(str(data1)))
            self.ui.model.setItem(i, 1, QStandardItem(str(data2)))
            self.ui.model.setItem(i, 2, QStandardItem(str(data3)))

            self.ui.model.setItem(i, 4, QStandardItem(data6))  # 下载
            self.ui.model.setItem(i, 5, QStandardItem(data7))  # 下载

            print(i)

        self.ui.tableView.setModel(self.ui.model)

    def xiazai(self, 歌名, CID, ID):
        thread = Thread(target=xiazai1, args=(歌名, CID, ID))
        thread.start()

    def xiazai_yingyue(self, 歌名, CID, ID):
        thread = Thread(target=xiazai_yingyue1, args=(歌名, CID, ID))
        thread.start()

    def bendi(self):
        dir = os.getcwd()  # 获取当前目录
        os.startfile(dir)  # 打开当前目录

    def bofang(self):
        current_dir = os.getcwd()
        playsound(current_dir + '\下载成功声音.wav')


def xiazai1(歌名, CID, ID):  # 下载视频 耗时事件写在主程序外
    print('开始下载')

    tite = 歌名

    url4 = 'https://api.bbbb.com/x/player/playurl?cid=%s&qn=0&type=&otype=json&fourk=1&bvid=%s&fnver=0&fnval=976&session=864feb9802c23dd2b99e6505690b3b29' % (
    CID, ID)

    headers = {
        'user-agent': 'Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/78.0.3904.108 Safari/537.36',
        'referer': 'https://www.bbbb.com/'
    }

    Tdata = requests.get(url4, headers=headers).text

    Bdata = json.loads(Tdata)
    pprint(Bdata)
    audio = Bdata['data']['dash']['audio'][0]['backupUrl'][0]
    video = Bdata['data']['dash']['video'][0]['backupUrl'][0]
    print(audio, video)

    headers1 = {

        'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/92.0.4515.107 Safari/537.36'
    }

    audio_file = requests.get(audio, headers=headers1).content
    video_file = requests.get(video, headers=headers1).content
    with open('audio.mp3', 'wb') as f:
        f.write(audio_file)
    with open('vide.mp4', 'wb') as f:
        f.write(video_file)

    Stats.ui.label_3.setText(tite)
    name = tite + '.mp4'

    os.system(f'ffmpeg -y -i vide.mp4 -i audio.mp3 -c:v copy -c:a aac -strict experimental ' + name)
    print('视频下载成功')

    Stats.ui.label_3.setText('视频下载成功')

    Stats.bofang()
    time.sleep(1)
    os.remove('vide.mp4')
    os.remove('audio.mp3')
    print('删除缓存成功')


def xiazai_yingyue1(歌名, CID, ID):  # 下载音乐  耗时事件写在主程序外
    print('开始下载')
    tite = 歌名

    url4 = 'https://api.bbbb.com/x/player/playurl?cid=%s&qn=0&type=&otype=json&fourk=1&bvid=%s&fnver=0&fnval=976&session=864feb9802c23dd2b99e6505690b3b29' % (
    CID, ID)

    headers = {
        'user-agent': 'Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/78.0.3904.108 Safari/537.36',
        'referer': 'https://www.bbbb.com/'
    }

    Tdata = requests.get(url4, headers=headers).text

    Bdata = json.loads(Tdata)
    pprint(Bdata)
    audio = Bdata['data']['dash']['audio'][0]['backupUrl'][0]

    print(audio)

    headers1 = {

        'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/92.0.4515.107 Safari/537.36'
    }

    audio_file = requests.get(audio, headers=headers1).content

    name = tite + '.mp3'
    with open(name, 'wb') as f:
        f.write(audio_file)

    Stats.ui.label_3.setText(tite)

    print('音频下载成功')
    Stats.ui.label_3.setText('音频下载成功')

    Stats.bofang()


if "__main__" == __name__:
    app = QApplication([])
    Stats = Stats()
    Stats.ui.show()
    app.exec_()

