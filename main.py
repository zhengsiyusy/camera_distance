# / -*-codeing = utf-8  -*-
# TIME : 2022/11/22 10:16
# File : my_camera_mainwindow
import os
import sys
import cv2
import math
import numpy as np
from PyQt5.QtCore import QCoreApplication, Qt
from PyQt5.QtWidgets import QMainWindow, QLabel, QWidget, QFileDialog, QApplication
from PyQt5 import QtCore, QtWidgets, QtGui
from camera import Ui_camera
from loginfo.log import init_log
from PyQt5.QtMultimedia import QCameraInfo


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
        current_path = os.getcwd()
        path = os.path.join(current_path, 'camera.log')
        self.log = init_log(path)
        self.camera = None  # QCamera对象
        self.get_camera_info()

    def get_camera_info(self):
        cameras = QCameraInfo.availableCameras()  # list[QCameraInfo]
        print(str(len(cameras)) + " camera find!")
        if len(cameras) > 0:
            camInfo = QCameraInfo.defaultCamera()
            info = camInfo.description()
            self.log.info("The camera image parameters are as follows:\n %s" % info)
            self.log.info("Camera preview image resolution: 320*240")
            self.log.info("Image resolution of shooting picture: 640*480")
        else:
            self.log.warning("The camera doesn't exist.")

    def button_status(self):
        # 设置默认选中计算距离模式
        self.ui.calculate_distance.setChecked(True)
        # 默认距离计算框不可编辑
        self.ui.camera_farthest.setEnabled(False)

        self.ui.show_image.setMouseTracking(True)
        self.ui.centralwidget.setMouseTracking(True)
        self.setMouseTracking(True)

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

    def save_parameter(self):
        if not self.timer_camera.isActive():  # 若定时器未启动
            msg = QtWidgets.QMessageBox.warning(self, '警告', "请先打开相机", buttons=QtWidgets.QMessageBox.Ok)
        else:
            self.timer_camera.stop()  # 关闭定时器
            self.cap.release()  # 释放视频流
            self.ui.frame1.clear()  # 清空视频显示区域

    def get_image(self):
        if not self.timer_camera.isActive():  # 若定时器未启动
            msg = QtWidgets.QMessageBox.warning(self, '警告', "请先打开相机", buttons=QtWidgets.QMessageBox.Ok)
        else:
            QmyMainWindow.show_camera(self, "frame2")

    def show_camera(self, port="frame1"):
        flag, self.image = self.cap.read()  # 从视频流中读取
        if not flag:
            self.log.warning("read image failed.")
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
            # 视频色彩转换回RGB，这样才是现实的颜色
            show = cv2.cvtColor(show, cv2.COLOR_BGR2RGB)
            showImage = QtGui.QImage(show.data, show.shape[1], show.shape[0], QtGui.QImage.Format_RGB888)
            self.ui.frame2.setPixmap(QtGui.QPixmap.fromImage(showImage))  # 往显示视频的Label里 显示QImage

    '''初始化所有槽函数'''
    def slot_init(self):
        self.timer_camera.timeout.connect(self.show_camera)  # 若定时器结束，则调用show_camera()
        self.ui.open_cam.clicked.connect(self.open_camera)
        # self.ui.save_para.clicked.connect(self.save_parameter)
        self.ui.get_image.clicked.connect(self.get_image)
        self.ui.calculate_camera.clicked.connect(self.calculate_camera_result)
        self.ui.calculate_position.clicked.connect(self.calculate_position_result)
        self.ui.calculate_distance.clicked['bool'].connect(self.mode_select)
        self.ui.calculate_angle.clicked['bool'].connect(self.mode_select)

    def mouseMoveEvent(self, event):  # 鼠标移动事件
        self.ui.frame2.setMouseTracking(True)
        newPos = event.pos()
        # 返回鼠标相对于窗口的x轴坐标
        snapPosX = newPos.x()
        # 返回鼠标相对于窗口的y轴坐标
        snapPosY = newPos.y()
        snapPos = QtCore.QPointF(snapPosX, snapPosY)
        self.U = snapPos.x() - 658
        self.V = snapPos.y() - 271
        self.LabImagePOS.setText("像素坐标：U:%.3f, V:%.3f " % (self.U, self.V - 20))

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
                msg = QtWidgets.QMessageBox.warning(self, '警告', "请输入正确的参数", buttons=QtWidgets.QMessageBox.Ok)
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
                msg = QtWidgets.QMessageBox.warning(self, '警告', "请输入正确的参数", buttons=QtWidgets.QMessageBox.Ok)
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

    def calculate_position_result(self):
        # position config
        # 左上角坐标
        px_u1_value = self.ui.left_up_px_u.value()
        px_u1_value = round(px_u1_value, 2)
        px_v1_value = self.ui.left_up_px_v.value()
        px_v1_value = round(px_v1_value, 2)
        cm_x1_value = self.ui.left_up_cm_x.value()
        cm_x1_value = round(cm_x1_value, 2)
        cm_y1_value = self.ui.left_up_cm_y.value()
        cm_y1_value = round(cm_y1_value, 2)
        # 左下角坐标
        px_u2_value = self.ui.left_down_px_u.value()
        px_u2_value = round(px_u2_value, 2)
        px_v2_value = self.ui.left_down_px_v.value()
        px_v2_value = round(px_v2_value, 2)
        cm_x2_value = self.ui.left_down_cm_x.value()
        cm_x2_value = round(cm_x2_value, 2)
        cm_y2_value = self.ui.left_down_cm_y.value()
        cm_y2_value = round(cm_y2_value, 2)
        # 右下角坐标
        px_u3_value = self.ui.right_down_px_u.value()
        px_u3_value = round(px_u3_value, 2)
        px_v3_value = self.ui.right_down_px_v.value()
        px_v3_value = round(px_v3_value, 2)
        cm_x3_value = self.ui.right_down_cm_x.value()
        cm_x3_value = round(cm_x3_value, 2)
        cm_y3_value = self.ui.right_down_cm_y.value()
        cm_y3_value = round(cm_y3_value, 2)
        # 右上角坐标
        px_u4_value = self.ui.right_up_px_u.value()
        px_u4_value = round(px_u4_value, 2)
        px_v4_value = self.ui.right_up_px_v.value()
        px_v4_value = round(px_v4_value, 2)
        cm_x4_value = self.ui.right_up_cm_x.value()
        cm_x4_value = round(cm_x4_value, 2)
        cm_y4_value = self.ui.right_up_cm_y.value()
        cm_y4_value = round(cm_y4_value, 2)

        pts_src = np.array([[px_u1_value, px_v1_value, 1.0],
                            [px_u2_value, px_v2_value, 1.0],
                            [px_u3_value, px_v3_value, 1.0],
                            [px_u4_value, px_v4_value, 1.0]])
        pts_dst = np.array([[cm_x1_value, cm_y1_value, 1.0],
                            [cm_x2_value, cm_y2_value, 1.0],
                            [cm_x3_value, cm_y3_value, 1.0],
                            [cm_x4_value, cm_y4_value, 1.0]])
        if ((px_u1_value == 0 and px_v1_value == 0 and cm_x1_value == 0 and cm_y1_value == 0) or
                (px_u2_value == 0 and px_v2_value == 0 and cm_x2_value == 0 and cm_y2_value == 0) or
                (px_u3_value == 0 and px_v3_value == 0 and cm_x3_value == 0 and cm_y3_value == 0) or
                (px_u4_value == 0 and px_v4_value == 0 and cm_x1_value == 0 and cm_y4_value == 0)):
            msg = QtWidgets.QMessageBox.warning(self, '警告', "输入坐标参数有误，请重新输入", buttons=QtWidgets.QMessageBox.Ok)
        matrix, status = cv2.findHomography(pts_src, pts_dst, method=cv2.RANSAC, ransacReprojThreshold=1)
        print("转换矩阵", matrix)
        if matrix is not None:
            msg = QtWidgets.QMessageBox.information(self, '校准', "校准成功", buttons=QtWidgets.QMessageBox.Ok)
            self.log.info("Coordinate of pixels:\n %s" % pts_src)
            self.log.info("Actual coordinates:\n %s" % pts_dst)
            self.log.info("Matrix of transformation:\n %s" % matrix)
            self.log.info("position: Parameter calibration succeeded!")
            with open('matrix_config.cfg', 'w') as f_cfg:
                # 发送转换矩阵方式
                # for i in range(3):
                #     for j in range(3):
                #         f_cfg.write(str(matrix[i][j]))
                #         f_cfg.write('\n')

                # 发送坐标信息方式
                f_cfg.write(str(px_u1_value))
                f_cfg.write('\n')
                f_cfg.write(str(px_v1_value))
                f_cfg.write('\n')
                f_cfg.write(str(px_u2_value))
                f_cfg.write('\n')
                f_cfg.write(str(px_v2_value))
                f_cfg.write('\n')
                f_cfg.write(str(px_u3_value))
                f_cfg.write('\n')
                f_cfg.write(str(px_v3_value))
                f_cfg.write('\n')
                f_cfg.write(str(px_u4_value))
                f_cfg.write('\n')
                f_cfg.write(str(px_v4_value))
                f_cfg.write('\n')
                f_cfg.write(str(cm_x1_value))
                f_cfg.write('\n')
                f_cfg.write(str(cm_y1_value))
                f_cfg.write('\n')
                f_cfg.write(str(cm_x2_value))
                f_cfg.write('\n')
                f_cfg.write(str(cm_y2_value))
                f_cfg.write('\n')
                f_cfg.write(str(cm_x3_value))
                f_cfg.write('\n')
                f_cfg.write(str(cm_y3_value))
                f_cfg.write('\n')
                f_cfg.write(str(cm_x4_value))
                f_cfg.write('\n')
                f_cfg.write(str(cm_y4_value))
                f_cfg.write('\n')
        else:
            self.log.error("position: Failure of calibration")


if __name__ == '__main__':
    QApplication.setHighDpiScaleFactorRoundingPolicy(Qt.HighDpiScaleFactorRoundingPolicy.PassThrough)
    app = QtWidgets.QApplication(sys.argv)  # 固定的，表示程序应用
    ui = QmyMainWindow()  # 实例化Ui_MainWindow
    ui.show()  # 调用ui的show()以显示。同样show()是源于父类QtWidgets.QWidget的
    sys.exit(app.exec_())  # 不加这句，程序界面会一闪而过
