# / -*-codeing = utf-8  -*-
# TIME : 2022/11/22 10:16
# File : my_camera_mainwindow
import sys
import cv2
import math
import numpy as np
from datetime import datetime
from PyQt5 import QtCore, QtWidgets, QtGui
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QMainWindow, QLabel, QFileDialog, QApplication
from PyQt5.QtMultimedia import QCameraInfo
from log.log import init_log
from source.camera import Ui_camera
import platform

python_version = platform.python_version()
code_version = "0.0.1"
final_x = 0
final_y = 0


def crop_image(point_x, point_y):
    # 边缘点图像裁剪处理最终裁剪为64*48
    # 左上角点
    if point_x - 32 < 0 and point_y - 24 < 0:
        new_x = 0
        new_y = 0
        roi_w = 64
        roi_h = 48
    # 右上角点
    elif point_x + 32 > 640 and point_y - 24 < 0:
        new_x = 640 - 64
        new_y = 0
        roi_w = 640
        roi_h = 48
    # 左下角点
    elif point_x - 32 < 0 and point_y + 24 > 480:
        new_x = 0
        new_y = 480 - 48
        roi_w = 64
        roi_h = 480
    # 右下角点
    elif point_x + 32 > 640 and point_y + 24 > 480:
        new_x = 640 - 64
        new_y = 480 - 48
        roi_w = 640
        roi_h = 480
    # 上侧
    elif (point_x - 32 > 0 or point_x + 32 < 640) and point_y - 24 < 0:
        new_x = point_x - 32
        new_y = 0
        roi_w = point_x + 32
        roi_h = 48
    # 左侧
    elif point_x - 32 < 0 and (point_y - 24 > 0 or point_y + 24 < 480):
        new_x = 0
        new_y = point_y - 24
        roi_w = 64
        roi_h = point_y + 24
    # 下侧
    elif (point_x - 32 > 0 or point_x + 32 < 640) and point_y + 24 > 480:
        new_x = point_x - 32
        new_y = 480 - 48
        roi_w = point_x + 32
        roi_h = 480
    # 右侧
    elif point_x + 32 > 640 and (point_y - 24 > 0 or point_y + 24 < 480):
        new_x = 640 - 64
        new_y = point_y - 24
        roi_w = 640
        roi_h = point_y + 24
    # 其他中心区域
    else:
        new_x = point_x - 32
        new_y = point_y - 24
        roi_w = point_x + 32
        roi_h = point_y + 24
    return new_x, new_y, roi_w, roi_h


class QmyMainWindow(QMainWindow):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.timer_camera = QtCore.QTimer(self)  # 导入定时器
        self.ui = Ui_camera()  # 创建UI对象
        self.ui.setupUi(self)  # 构造UI界面
        self.cap = cv2.VideoCapture()  # 视频流
        self.CAM_NUM = 0  # 为0时表示视频流来自笔记本内置摄像头
        self.slot_init()  # 初始化槽函数
        self.setWindowTitle("参数校准工具")
        self.button_status()
        self.U = 0
        self.V = 0
        name = str("像素坐标：U:%.3f, V:%.3f " % (self.U, self.V))
        self.LabImagePOS = QLabel(name)
        self.ui.statusbar.addWidget(self.LabImagePOS)
        # 日志管理
        self.log = init_log()
        self.camera = None  # QCamera对象
        self.get_camera_info()
        self.roi = None
        self.index = 0

    '''初始化所有槽函数'''
    def slot_init(self):
        self.timer_camera.timeout.connect(self.show_camera)  # 若定时器结束，则调用show_camera()
        self.ui.open_cam.clicked.connect(self.open_camera)
        self.ui.save_para.clicked.connect(self.save_parameter)
        self.ui.get_image.clicked.connect(self.get_image)
        self.ui.calculate_camera.clicked.connect(self.calculate_camera_result)
        self.ui.calculate_position.clicked.connect(self.calculate_position_result)
        self.ui.calculate_distance.clicked['bool'].connect(self.mode_select)
        self.ui.calculate_angle.clicked['bool'].connect(self.mode_select)

    def get_camera_info(self):
        self.log.info("Python Version: %s" % python_version)
        self.log.info("Code Version: %s " % code_version)
        cameras = QCameraInfo.availableCameras()
        if len(cameras) > 0:
            camInfo = QCameraInfo.defaultCamera()
            info = camInfo.description()
            self.log.info("The camera image parameters are as follows:\n %s" % info)
            self.log.info("Camera preview image resolution: 320*240")
            self.log.info("Image resolution of shooting picture: 640*480")
        else:
            self.log.warning("The camera doesn't exist.")

    def open_camera(self):
        if not self.timer_camera.isActive():  # 若定时器未启动
            flag = self.cap.open(self.CAM_NUM)  # 参数是0，表示打开笔记本的内置摄像头，参数是视频文件路径则打开视频
            if not flag:  # flag表示open()成不成功
                msg = QtWidgets.QMessageBox.warning(self, '警告', "请检查相机与电脑是否连接正确", buttons=QtWidgets.QMessageBox.Ok)
                self.log.warning("Please check that the camera is properly connected to the computer")
            else:
                self.timer_camera.start(30)  # 定时器开始计时30ms，结果是每过30ms从摄像头中取一帧显示
                self.ui.open_cam.setText("关闭相机")
        else:
            self.timer_camera.stop()  # 关闭定时器
            self.cap.release()  # 释放视频流
            self.ui.frame1.clear()  # 清空视频显示区域
            self.ui.open_cam.setText("打开相机")

            self.ui.left_up_px_u.setValue(0)
            self.ui.left_up_px_v.setValue(0)
            self.ui.left_up_cm_x.setValue(0)
            self.ui.left_up_cm_y.setValue(0)

            self.ui.left_mid_px_u.setValue(0)
            self.ui.left_mid_px_v.setValue(0)
            self.ui.left_mid_cm_x.setValue(0)
            self.ui.left_mid_cm_y.setValue(0)

            self.ui.left_down_px_u.setValue(0)
            self.ui.left_down_px_v.setValue(0)
            self.ui.left_down_cm_x.setValue(0)
            self.ui.left_down_cm_y.setValue(0)

            self.ui.bottom_mid_px_u.setValue(0)
            self.ui.bottom_mid_px_v.setValue(0)
            self.ui.bottom_mid_cm_x.setValue(0)
            self.ui.bottom_mid_cm_y.setValue(0)

            self.ui.right_down_px_u.setValue(0)
            self.ui.right_down_px_v.setValue(0)
            self.ui.right_down_cm_x.setValue(0)
            self.ui.right_down_cm_y.setValue(0)

            self.ui.right_mid_px_u.setValue(0)
            self.ui.right_mid_px_v.setValue(0)
            self.ui.right_mid_cm_x.setValue(0)
            self.ui.right_mid_cm_y.setValue(0)

            self.ui.right_up_px_u.setValue(0)
            self.ui.right_up_px_v.setValue(0)
            self.ui.right_up_cm_x.setValue(0)
            self.ui.right_up_cm_y.setValue(0)

            self.ui.top_mid_px_u.setValue(0)
            self.ui.top_mid_px_v.setValue(0)
            self.ui.top_mid_cm_x.setValue(0)
            self.ui.top_mid_cm_y.setValue(0)

            self.ui.led1.setStyleSheet("color:black")
            self.ui.led2.setStyleSheet("color:black")
            self.ui.led3.setStyleSheet("color:black")
            self.ui.led4.setStyleSheet("color:black")
            self.ui.led5.setStyleSheet("color:black")
            self.ui.led6.setStyleSheet("color:black")
            self.ui.led7.setStyleSheet("color:black")
            self.ui.led8.setStyleSheet("color:black")
            cv2.destroyAllWindows()

    def save_parameter(self):
        now_time = datetime.strftime(datetime.now(), "%Y%m%d-%H%M%S")
        filename = './' + str(now_time) + ".cfg"
        # 前面是地址，后面是文件类型,得到输入地址的文件名和地址
        filepath, type = QFileDialog.getSaveFileName(self, "文件保存", filename, 'cfg(*.cfg)')
        if type:
            with open(filepath, 'w') as f_cfg:
                # 发送坐标信息方式
                f_cfg.write(str(self.px_u1_value))
                f_cfg.write('\n')
                f_cfg.write(str(self.px_v1_value))
                f_cfg.write('\n')
                f_cfg.write(str(self.px_u2_value))
                f_cfg.write('\n')
                f_cfg.write(str(self.px_v2_value))
                f_cfg.write('\n')
                f_cfg.write(str(self.px_u3_value))
                f_cfg.write('\n')
                f_cfg.write(str(self.px_v3_value))
                f_cfg.write('\n')
                f_cfg.write(str(self.px_u4_value))
                f_cfg.write('\n')
                f_cfg.write(str(self.px_v4_value))
                f_cfg.write('\n')

                f_cfg.write(str(self.px_u5_value))
                f_cfg.write('\n')
                f_cfg.write(str(self.px_v5_value))
                f_cfg.write('\n')
                f_cfg.write(str(self.px_u6_value))
                f_cfg.write('\n')
                f_cfg.write(str(self.px_v6_value))
                f_cfg.write('\n')
                f_cfg.write(str(self.px_u7_value))
                f_cfg.write('\n')
                f_cfg.write(str(self.px_v7_value))
                f_cfg.write('\n')
                f_cfg.write(str(self.px_u8_value))
                f_cfg.write('\n')
                f_cfg.write(str(self.px_v8_value))
                f_cfg.write('\n')

                f_cfg.write(str(self.cm_x1_value))
                f_cfg.write('\n')
                f_cfg.write(str(self.cm_y1_value))
                f_cfg.write('\n')
                f_cfg.write(str(self.cm_x2_value))
                f_cfg.write('\n')
                f_cfg.write(str(self.cm_y2_value))
                f_cfg.write('\n')
                f_cfg.write(str(self.cm_x3_value))
                f_cfg.write('\n')
                f_cfg.write(str(self.cm_y3_value))
                f_cfg.write('\n')
                f_cfg.write(str(self.cm_x4_value))
                f_cfg.write('\n')
                f_cfg.write(str(self.cm_y4_value))
                f_cfg.write('\n')
                f_cfg.write(str(self.cm_x5_value))
                f_cfg.write('\n')
                f_cfg.write(str(self.cm_y5_value))
                f_cfg.write('\n')
                f_cfg.write(str(self.cm_x6_value))
                f_cfg.write('\n')
                f_cfg.write(str(self.cm_y6_value))
                f_cfg.write('\n')
                f_cfg.write(str(self.cm_x7_value))
                f_cfg.write('\n')
                f_cfg.write(str(self.cm_y7_value))
                f_cfg.write('\n')
                f_cfg.write(str(self.cm_x8_value))
                f_cfg.write('\n')
                f_cfg.write(str(self.cm_y8_value))
                f_cfg.write('\n')
                f_cfg.close()
        else:
            return

    def get_image(self):
        if not self.timer_camera.isActive():  # 若定时器未启动
            msg = QtWidgets.QMessageBox.warning(self, '警告', "请先打开相机", buttons=QtWidgets.QMessageBox.Ok)
        else:
            QmyMainWindow.show_camera(self, "frame2")

    def show_camera(self, port="frame1"):
        flag, self.image = self.cap.read()  # 从视频流中读取
        if not flag:
            self.log.warning("read image failed.")
        else:
            if port == "frame1":
                # 把读到的帧的大小设置为 320x240
                show = cv2.resize(self.image, (320, 240))
                # 视频色彩转换回RGB，这样才是现实的颜色
                show = cv2.cvtColor(show, cv2.COLOR_BGR2RGB)
                # 把读取到的视频数据变成QImage形式
                showImage = QtGui.QImage(show.data, show.shape[1], show.shape[0], QtGui.QImage.Format_RGB888)
                self.ui.frame1.setPixmap(QtGui.QPixmap.fromImage(showImage))  # 往显示视频的Label里 显示QImage
            else:
                # 把读到的帧的大小重新设置为 640x480
                show = cv2.resize(self.image, (640, 480))
                self.roi = show
                # 视频色彩转换回RGB，这样才是现实的颜色
                show = cv2.cvtColor(show, cv2.COLOR_BGR2RGB)
                showImage = QtGui.QImage(show.data, show.shape[1], show.shape[0], QtGui.QImage.Format_RGB888)
                self.ui.frame2.setPixmap(QtGui.QPixmap.fromImage(showImage))  # 往显示视频的Label里 显示QImage

    def mouseMoveEvent(self, event):  # 鼠标移动事件
        self.ui.frame2.setMouseTracking(True)
        newPos = event.pos()
        # 返回鼠标相对于窗口的x轴坐标
        snapPosX = newPos.x()
        # 返回鼠标相对于窗口的y轴坐标
        snapPosY = newPos.y()
        snapPos = QtCore.QPointF(snapPosX, snapPosY)
        self.U = snapPos.x() - 636
        self.V = snapPos.y() - 288
        self.LabImagePOS.setText("像素坐标：U:%.3f, V:%.3f " % (self.U, self.V))

    def mousePressEvent(self, event):
        global final_x, final_y
        # click_count = 0
        self.ui.frame2.setMouseTracking(True)

        def click(event, x, y, flags, param):
            global final_x, final_y
            first_x = param[0]
            first_y = param[1]
            if event == cv2.EVENT_LBUTTONDOWN:
                # 左上角点
                if first_x - 32 < 0 and first_y - 24 < 0:
                    final_x = x / 10
                    final_y = y / 10
                # 右上角点
                elif first_x + 32 > 640 and first_y - 24 < 0:
                    final_x = 640 - 64 + x / 10
                    final_y = y / 10
                # 左下角点
                elif first_x - 32 < 0 and first_y + 24 > 480:
                    final_x = x / 10
                    final_y = 480 - 48 + y / 10
                # 右下角点
                elif first_x + 32 > 640 and first_y + 24 > 480:
                    final_x = 640 - 64 + x / 10
                    final_y = 480 - 48 + y / 10
                # 上侧
                elif (first_x - 32 > 0 or first_x + 32 < 640) and first_y - 24 < 0:
                    final_x = first_x - 32 + x / 10
                    final_y = y / 10
                # 左侧
                elif first_x - 32 < 0 and (first_y - 24 > 0 or first_y + 24 < 480):
                    final_x = x / 10
                    final_y = first_y - 24 + y / 10
                # 下侧
                elif (first_x - 32 > 0 or first_x + 32 < 640) and first_y + 24 > 480:
                    final_x = first_x - 32 + x / 10
                    final_y = 480 - 48 + y / 10
                # 右侧
                elif first_x + 32 > 640 and (first_y - 24 > 0 or first_y + 24 < 480):
                    final_x = 640 - 64 + x / 10
                    final_y = first_y - 24 + y / 10
                else:
                    final_x = first_x - 32 + x / 10
                    final_y = first_y - 24 + y / 10

        if event.button() == Qt.LeftButton:  # 如果鼠标左键点击
            if 636 < event.pos().x() < 1274 and 288 < event.pos().y() < 768:
                if self.roi is None:
                    QtWidgets.QMessageBox.warning(self, '警告', "图像为空，请先拍照！", buttons=QtWidgets.QMessageBox.Ok)
                    self.log.error("图像为空！")
                else:
                    if self.index == 0:
                        self.ui.led1.setStyleSheet("color:green")
                        self.ui.led2.setStyleSheet("color:black")
                        self.ui.led3.setStyleSheet("color:black")
                        self.ui.led4.setStyleSheet("color:black")
                        self.ui.led5.setStyleSheet("color:black")
                        self.ui.led6.setStyleSheet("color:black")
                        self.ui.led7.setStyleSheet("color:black")
                        self.ui.led8.setStyleSheet("color:black")
                        click_count = 0
                    elif self.index == 1:
                        self.ui.led1.setStyleSheet("color:black")
                        self.ui.led2.setStyleSheet("color:green")
                        self.ui.led3.setStyleSheet("color:black")
                        self.ui.led4.setStyleSheet("color:black")
                        self.ui.led5.setStyleSheet("color:black")
                        self.ui.led6.setStyleSheet("color:black")
                        self.ui.led7.setStyleSheet("color:black")
                        self.ui.led8.setStyleSheet("color:black")
                        click_count = 1
                    elif self.index == 2:
                        self.ui.led1.setStyleSheet("color:black")
                        self.ui.led2.setStyleSheet("color:black")
                        self.ui.led3.setStyleSheet("color:green")
                        self.ui.led4.setStyleSheet("color:black")
                        self.ui.led5.setStyleSheet("color:black")
                        self.ui.led6.setStyleSheet("color:black")
                        self.ui.led7.setStyleSheet("color:black")
                        self.ui.led8.setStyleSheet("color:black")
                        click_count = 2
                    elif self.index == 3:
                        self.ui.led1.setStyleSheet("color:black")
                        self.ui.led2.setStyleSheet("color:black")
                        self.ui.led3.setStyleSheet("color:black")
                        self.ui.led4.setStyleSheet("color:green")
                        self.ui.led5.setStyleSheet("color:black")
                        self.ui.led6.setStyleSheet("color:black")
                        self.ui.led7.setStyleSheet("color:black")
                        self.ui.led8.setStyleSheet("color:black")
                        click_count = 3
                    elif self.index == 4:
                        self.ui.led1.setStyleSheet("color:black")
                        self.ui.led2.setStyleSheet("color:black")
                        self.ui.led3.setStyleSheet("color:black")
                        self.ui.led4.setStyleSheet("color:black")
                        self.ui.led5.setStyleSheet("color:green")
                        self.ui.led6.setStyleSheet("color:black")
                        self.ui.led7.setStyleSheet("color:black")
                        self.ui.led8.setStyleSheet("color:black")
                        click_count = 4
                    elif self.index == 5:
                        self.ui.led1.setStyleSheet("color:black")
                        self.ui.led2.setStyleSheet("color:black")
                        self.ui.led3.setStyleSheet("color:black")
                        self.ui.led4.setStyleSheet("color:black")
                        self.ui.led5.setStyleSheet("color:black")
                        self.ui.led6.setStyleSheet("color:green")
                        self.ui.led7.setStyleSheet("color:black")
                        self.ui.led8.setStyleSheet("color:black")
                        click_count = 5
                    elif self.index == 6:
                        self.ui.led1.setStyleSheet("color:black")
                        self.ui.led2.setStyleSheet("color:black")
                        self.ui.led3.setStyleSheet("color:black")
                        self.ui.led4.setStyleSheet("color:black")
                        self.ui.led5.setStyleSheet("color:black")
                        self.ui.led6.setStyleSheet("color:black")
                        self.ui.led7.setStyleSheet("color:green")
                        self.ui.led8.setStyleSheet("color:black")
                        click_count = 6
                    elif self.index == 7:
                        self.ui.led1.setStyleSheet("color:black")
                        self.ui.led2.setStyleSheet("color:black")
                        self.ui.led3.setStyleSheet("color:black")
                        self.ui.led4.setStyleSheet("color:black")
                        self.ui.led5.setStyleSheet("color:black")
                        self.ui.led6.setStyleSheet("color:black")
                        self.ui.led7.setStyleSheet("color:black")
                        self.ui.led8.setStyleSheet("color:green")
                        click_count = 7

                    point_x = event.pos().x() - 636
                    point_y = event.pos().y() - 288
                    list_point = [point_x, point_y]
                    new_x, new_y, roi_w, roi_h = crop_image(point_x, point_y)
                    # 以点击坐标点为中心 裁剪图像64*32
                    img = self.roi[new_y:roi_h, new_x:roi_w]
                    if img is None:
                        self.log.error("crop image is empty!")
                    else:
                        # 将图像放大十倍
                        img1 = cv2.resize(img, (640, 480))
                        cv2.namedWindow("roi")
                        cv2.setMouseCallback("roi", click, list_point)
                        cv2.imshow("roi", img1)

                        if click_count == 0:
                            self.ui.top_mid_px_u.setValue(final_x)
                            self.ui.top_mid_px_v.setValue(final_y)
                            self.index += 1
                        elif click_count == 1:
                            self.ui.left_up_px_u.setValue(final_x)
                            self.ui.left_up_px_v.setValue(final_y)
                            self.index += 1
                        elif click_count == 2:
                            self.ui.left_mid_px_u.setValue(final_x)
                            self.ui.left_mid_px_v.setValue(final_y)
                            self.index += 1
                        if click_count == 3:
                            self.ui.left_down_px_u.setValue(final_x)
                            self.ui.left_down_px_v.setValue(final_y)
                            self.index += 1
                        elif click_count == 4:
                            self.ui.bottom_mid_px_u.setValue(final_x)
                            self.ui.bottom_mid_px_v.setValue(final_y)
                            self.index += 1
                        elif click_count == 5:
                            self.ui.right_down_px_u.setValue(final_x)
                            self.ui.right_down_px_v.setValue(final_y)
                            self.index += 1
                        elif click_count == 6:
                            self.ui.right_mid_px_u.setValue(final_x)
                            self.ui.right_mid_px_v.setValue(final_y)
                            self.index += 1
                        elif click_count == 7:
                            self.ui.right_up_px_u.setValue(final_x)
                            self.ui.right_up_px_v.setValue(final_y)
                            self.index = 0
                        cv2.waitKey()
                        cv2.destroyAllWindows()
            else:
                print("mouse not in range")

    def calculate_position_result(self):
        # position config
        # 左上角坐标
        px_u1_value = self.ui.left_up_px_u.value()
        self.px_u1_value = round(px_u1_value, 2)
        px_v1_value = self.ui.left_up_px_v.value()
        self.px_v1_value = round(px_v1_value, 2)
        cm_x1_value = self.ui.left_up_cm_x.value()
        self.cm_x1_value = round(cm_x1_value, 2)
        cm_y1_value = self.ui.left_up_cm_y.value()
        self.cm_y1_value = round(cm_y1_value, 2)
        # 左中角坐标
        px_u2_value = self.ui.left_mid_px_u.value()
        self.px_u2_value = round(px_u2_value, 2)
        px_v2_value = self.ui.left_mid_px_v.value()
        self.px_v2_value = round(px_v2_value, 2)
        cm_x2_value = self.ui.left_mid_cm_x.value()
        self.cm_x2_value = round(cm_x2_value, 2)
        cm_y2_value = self.ui.left_mid_cm_y.value()
        self.cm_y2_value = round(cm_y2_value, 2)
        # 左下角坐标
        px_u3_value = self.ui.left_down_px_u.value()
        self.px_u3_value = round(px_u3_value, 2)
        px_v3_value = self.ui.left_down_px_v.value()
        self.px_v3_value = round(px_v3_value, 2)
        cm_x3_value = self.ui.left_down_cm_x.value()
        self.cm_x3_value = round(cm_x3_value, 2)
        cm_y3_value = self.ui.left_down_cm_y.value()
        self.cm_y3_value = round(cm_y3_value, 2)
        # 下中角坐标
        px_u4_value = self.ui.bottom_mid_px_u.value()
        self.px_u4_value = round(px_u4_value, 2)
        px_v4_value = self.ui.bottom_mid_px_v.value()
        self.px_v4_value = round(px_v4_value, 2)
        cm_x4_value = self.ui.bottom_mid_cm_x.value()
        self.cm_x4_value = round(cm_x4_value, 2)
        cm_y4_value = self.ui.bottom_mid_cm_y.value()
        self.cm_y4_value = round(cm_y4_value, 2)
        # 右下角坐标
        px_u5_value = self.ui.right_down_px_u.value()
        self.px_u5_value = round(px_u5_value, 2)
        px_v5_value = self.ui.right_down_px_v.value()
        self.px_v5_value = round(px_v5_value, 2)
        cm_x5_value = self.ui.right_down_cm_x.value()
        self.cm_x5_value = round(cm_x5_value, 2)
        cm_y5_value = self.ui.right_down_cm_y.value()
        self.cm_y5_value = round(cm_y5_value, 2)
        # 右中角坐标
        px_u6_value = self.ui.right_mid_px_u.value()
        self.px_u6_value = round(px_u6_value, 2)
        px_v6_value = self.ui.right_mid_px_v.value()
        self.px_v6_value = round(px_v6_value, 2)
        cm_x6_value = self.ui.right_mid_cm_x.value()
        self.cm_x6_value = round(cm_x6_value, 2)
        cm_y6_value = self.ui.right_mid_cm_y.value()
        self.cm_y6_value = round(cm_y6_value, 2)
        # 右上角坐标
        px_u7_value = self.ui.right_up_px_u.value()
        self.px_u7_value = round(px_u7_value, 2)
        px_v7_value = self.ui.right_up_px_v.value()
        self.px_v7_value = round(px_v7_value, 2)
        cm_x7_value = self.ui.right_up_cm_x.value()
        self.cm_x7_value = round(cm_x7_value, 2)
        cm_y7_value = self.ui.right_up_cm_y.value()
        self.cm_y7_value = round(cm_y7_value, 2)
        # 上中角坐标
        px_u8_value = self.ui.top_mid_px_u.value()
        self.px_u8_value = round(px_u8_value, 2)
        px_v8_value = self.ui.top_mid_px_v.value()
        self.px_v8_value = round(px_v8_value, 2)
        cm_x8_value = self.ui.top_mid_cm_x.value()
        self.cm_x8_value = round(cm_x8_value, 2)
        cm_y8_value = self.ui.top_mid_cm_y.value()
        self.cm_y8_value = round(cm_y8_value, 2)

        if ((self.px_u1_value == 0 and self.px_v1_value == 0 and self.cm_x1_value == 0 and self.cm_y1_value == 0) or
                (self.px_u2_value == 0 and self.px_v2_value == 0 and self.cm_x2_value == 0 and self.cm_y2_value == 0) or
                (self.px_u3_value == 0 and self.px_v3_value == 0 and self.cm_x3_value == 0 and self.cm_y3_value == 0) or
                (self.px_u4_value == 0 and self.px_v4_value == 0 and self.cm_x4_value == 0 and self.cm_y4_value == 0) or
                (self.px_u5_value == 0 and self.px_v5_value == 0 and self.cm_x5_value == 0 and self.cm_y5_value == 0) or
                (self.px_u6_value == 0 and self.px_v6_value == 0 and self.cm_x6_value == 0 and self.cm_y6_value == 0) or
                (self.px_u7_value == 0 and self.px_v7_value == 0 and self.cm_x7_value == 0 and self.cm_y7_value == 0) or
                (self.px_u8_value == 0 and self.px_v8_value == 0 and self.cm_x8_value == 0 and self.cm_y8_value == 0)):
            QtWidgets.QMessageBox.warning(self, '警告', "输入坐标参数有误，请重新输入", buttons=QtWidgets.QMessageBox.Ok)
        else:
            pts_src = np.array([[self.px_u1_value, self.px_v1_value, 1.0],
                                [self.px_u2_value, self.px_v2_value, 1.0],
                                [self.px_u3_value, self.px_v3_value, 1.0],
                                [self.px_u4_value, self.px_v4_value, 1.0],
                                [self.px_u5_value, self.px_v5_value, 1.0],
                                [self.px_u6_value, self.px_v6_value, 1.0],
                                [self.px_u7_value, self.px_v7_value, 1.0],
                                [self.px_u8_value, self.px_v8_value, 1.0]
                                ])
            pts_dst = np.array([[self.cm_x1_value, self.cm_y1_value, 1.0],
                                [self.cm_x2_value, self.cm_y2_value, 1.0],
                                [self.cm_x3_value, self.cm_y3_value, 1.0],
                                [self.cm_x4_value, self.cm_y4_value, 1.0],
                                [self.cm_x5_value, self.cm_y5_value, 1.0],
                                [self.cm_x6_value, self.cm_y6_value, 1.0],
                                [self.cm_x7_value, self.cm_y7_value, 1.0],
                                [self.cm_x8_value, self.cm_y8_value, 1.0]])

            self.matrix, status = cv2.findHomography(pts_src, pts_dst, method=cv2.RANSAC, ransacReprojThreshold=1)
            print("转换矩阵", self.matrix)
            if self.matrix is not None:
                QtWidgets.QMessageBox.information(self, '校准', "校准成功", buttons=QtWidgets.QMessageBox.Ok)
                self.log.info("Coordinate of pixels:\n %s" % pts_src)
                self.log.info("Actual coordinates:\n %s" % pts_dst)
                self.log.info("Matrix of transformation:\n %s" % self.matrix)
                self.log.info("position: Parameter calibration succeeded!")
            else:
                self.log.error("position: Failure of calibration")
                QtWidgets.QMessageBox.warning(self, '警告', "输入坐标参数有误或不完整，请重新输入", buttons=QtWidgets.QMessageBox.Ok)

    def button_status(self):
        # 设置默认选中计算距离模式
        self.ui.calculate_distance.setChecked(True)
        # 默认距离计算框不可编辑
        self.ui.camera_farthest.setEnabled(False)

        self.ui.show_image.setMouseTracking(True)
        self.ui.centralwidget.setMouseTracking(True)
        self.setMouseTracking(True)

    def mode_select(self):
        if self.ui.calculate_distance.isChecked():
            # 设置角度计算框不可编辑
            self.ui.camera_angle.setEnabled(True)
            # 设置距离计算框可编辑
            self.ui.camera_farthest.setEnabled(False)
            self.ui.camera_angle.setValue(0.00)
            self.ui.camera_farthest.setValue(0.00)
        elif self.ui.calculate_angle.isChecked():
            # 设置角度计算框不可编辑
            self.ui.camera_angle.setEnabled(False)
            # 设置距离计算框可编辑
            self.ui.camera_farthest.setEnabled(True)
            self.ui.camera_angle.setValue(0.00)
            self.ui.camera_farthest.setValue(0.00)

    # 计算配置数据
    def calculate_camera_result(self):
        if self.ui.calculate_distance.isChecked():
            # 设置角度计算框不可编辑
            self.ui.camera_angle.setEnabled(True)
            # 设置距离计算框可编辑
            self.ui.camera_farthest.setEnabled(False)
            # read camera config
            height_value = self.ui.camera_height.value()
            angle_value = self.ui.camera_angle.value()
            if height_value == 0 or angle_value == 0:
                QtWidgets.QMessageBox.warning(self, '警告', "请输入正确的参数", buttons=QtWidgets.QMessageBox.Ok)
                self.log.warning("calculate distance:input data incorrect")
            else:
                # 设置距离计算框不可编辑
                self.ui.camera_farthest.setEnabled(False)
                QmyMainWindow.cal_dis(self, angle_value, height_value)
        elif self.ui.calculate_angle.isChecked():
            # 设置角度计算框不可编辑
            self.ui.camera_angle.setEnabled(False)
            # 设置距离计算框可编辑
            self.ui.camera_farthest.setEnabled(True)
            # read camera config
            height_value = self.ui.camera_height.value()
            farthest_value = self.ui.camera_farthest.value()
            if height_value == 0 or farthest_value == 0:
                QtWidgets.QMessageBox.warning(self, '警告', "请输入正确的参数", buttons=QtWidgets.QMessageBox.Ok)
                self.log.warning("camera angle:input data incorrect")
            else:
                QmyMainWindow.cal_angle(self, height_value, farthest_value)

    def cal_dis(self, angle_value, height_value):
        # 角度值转换为弧度值
        radians_value = math.radians(angle_value)
        # 计算距离
        farthest = height_value * math.tan(radians_value)
        # 保留2位小数
        final_farthest = round(farthest, 2)
        self.log.info("Calculate the furthest distance measured by the camera.")
        self.log.info("height: %s cm" % height_value)
        self.log.info("angle: %s °" % angle_value)
        self.log.info("distance: %s cm" % final_farthest)
        # 显示到UI界面
        self.ui.camera_farthest.setValue(final_farthest)

    def cal_angle(self, height_value, farthest_value):
        # 求解角度的反三角函数
        angle_value = np.arctan(farthest_value / height_value)
        # 求解度数
        final_angle = math.degrees(angle_value)
        # 保留2位小数
        final_angle = round(final_angle, 2)
        self.log.info("Calculate camera mounting Angle.")
        self.log.info("height: %s cm" % height_value)
        self.log.info("distance: %s cm" % farthest_value)
        self.log.info("angle: %s °" % final_angle)
        self.ui.camera_angle.setValue(final_angle)


if __name__ == '__main__':

    QApplication.setHighDpiScaleFactorRoundingPolicy(Qt.HighDpiScaleFactorRoundingPolicy.PassThrough)
    app = QtWidgets.QApplication(sys.argv)  # 固定的，表示程序应用
    ui = QmyMainWindow()  # 实例化Ui_MainWindow
    ui.show()  # 调用ui的show()以显示。同样show()是源于父类QtWidgets.QWidget的
    sys.exit(app.exec_())  # 不加这句，程序界面会一闪而过

