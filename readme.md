打包成.exe指令：
打开本地包含pyqt5和opencv的虚拟环境：
在虚拟环境中执行以下指令：
## 1.此方法打包只生成一个.exe文件，所有依赖文件都打包到.exe中，打开软件速度较慢
pyinstaller -F -i logo.ico -w main.py -p camera.py -p distance.py -p position.py --hidden-import camera --hidden-import distance --hidden-import position --noconsole
## 2.此方法打包生成一个文件夹，依赖包在文件夹内，软件打开速度较快
pyinstaller -D -i logo.ico -w main.py -p camera.py -p distance.py -p position.py --hidden-import camera --hidden-import distance --hidden-import position --noconsole