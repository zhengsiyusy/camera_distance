打包成.exe指令：
打开本地包含pyqt5和opencv的虚拟环境：
在虚拟环境中执行以下指令：
## 1.此方法打包只生成一个.exe文件，所有依赖文件都打包到.exe中，打开软件速度较慢
pyinstaller -F -i source/logo.ico -w main.py -p source/camera.py -p source/distance.py -p loginfo/log.py 
--hidden-import camera --hidden-import distance --hidden-import log --noconsole

## 2.此方法打包生成一个文件夹，依赖包在文件夹内，软件打开速度较快
pyinstaller -D -i source/logo.ico -w main.py -p source/camera.py -p source/distance.py -p loginfo/log.py 
--hidden-import camera --hidden-import distance --hidden-import log --noconsole

## 版本兼容性问题
1. windows10上opencv-python与PyQt5版本兼容没有问题
2. windows7与linux上安装opencv-python版本要求4.2.0以下版本。否则会导致opencv在调用imshow、waitKey等方法异常，
   导致程序崩溃运行失败。

## 计算点数
使用8组点对计算转换参数
## 版本对应
此版本为0.0.1对应测距代码版本0.0.1
## 更改记录：
2022.12.26
1. 根据笔记本屏幕大小进行控件大小调整.
2. 更改配置文件生成方式，使用yaml文件生成配置信息
3. 删除原以'.cfg'的配置文件，删除日志生成信息
