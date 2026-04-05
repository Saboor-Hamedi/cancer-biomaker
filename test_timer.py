import sys
import threading
import time
from PySide6.QtWidgets import QApplication
from PySide6.QtCore import QTimer

def test():
    print("Secondary thread starting...")
    def callback():
        print("Callback fired!")
    
    QTimer.singleShot(0, callback)
    print("Timer scheduled.")
    time.sleep(1)

app = QApplication(sys.argv)
t = threading.Thread(target=test)
t.start()
QTimer.singleShot(2000, app.quit)
app.exec()
print("App exited.")
