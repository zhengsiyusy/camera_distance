打包成.exe指令：
pyinstaller -F -i logo.ico -w main.py -p camera.py -p distance.py -p position.py
--hidden-import camera --hidden-import distance --hidden-import position --noconsole