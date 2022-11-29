打包成.exe指令：
打开本地包含pyqt5和opencv的虚拟环境：
在虚拟环境中执行以下指令：
pyinstaller -F -i logo.ico -w main.py -p camera.py -p distance.py -p position.py --hidden-import camera --hidden-import distance --hidden-import position --noconsole