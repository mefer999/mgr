from PyQt5.QtWidgets import QApplication, QMainWindow, QWidget, QLabel, QStackedLayout, QVBoxLayout
from PyQt5.QtCore import QSize, QThread, pyqtSignal, pyqtSlot, Qt, QEventLoop, QTimer
from PyQt5.QtGui import QPixmap, QFont
from PyQt5 import QtCore
import sys, time
from face_rec import App
import RPi.GPIO as GPIO
from mfrc522 import SimpleMFRC522
from mqtt import MqttClient


class FirstPageWidget(QMainWindow):   
    def __init__(self):
        super(FirstPageWidget, self).__init__()  
        widget_logo = QWidget()
        logo = QLabel()
        logo.setPixmap(QPixmap("/home/pi/Documents/MGR/GUI/logo.jpg")) #poprawic
        logo.setScaledContents(True)
        logo_layout = QVBoxLayout()
        logo_layout.addWidget(logo)
        widget_logo.setLayout(logo_layout)
        self.setCentralWidget(widget_logo)
     
class RfidThread(QThread):
    is_good = pyqtSignal(float)
       
    def __init__(self):
        super().__init__()
        self._run_flag = True
        self.reader = SimpleMFRC522()
        
    def run(self):
        while self._run_flag:
            try:
                print("place tag")
                i, name = self.reader.read()
                print(i)
                time.sleep(1)            
            finally:
                GPIO.cleanup()
                time.sleep(1)
                self.is_good.emit(i)
          
    def stop(self):
        self._run_flag = False
        self.wait()
        
class LastWidget(QWidget):
    def __init__(self):
        super(LastWidget, self).__init__()
        
        self.label1 = QLabel(" ")
        self.label2 = QLabel("Imie Nazwisko")
        self.label3 = QLabel("OB/NB")
        self.label4 = QLabel(" ")

        self.label2.setFont(QFont('Arial', 30))
        self.label3.setFont(QFont('Arial', 30))

        self.label2.setAlignment(Qt.AlignHCenter | Qt.AlignVCenter)
        self.label3.setAlignment(Qt.AlignHCenter | Qt.AlignVCenter)

        layout = QVBoxLayout()
        layout.addWidget(self.label1)
        layout.addWidget(self.label2)
        layout.addWidget(self.label3)
        layout.addWidget(self.label4)

        self.setLayout(layout)
             
    def update_label(self, new_text2, new_text3):
        self.label2.setText(new_text2)
        self.label3.setText(new_text3) 
        
class MainWindow(QMainWindow):
    def __init__(self):
        super(MainWindow, self).__init__()
        self.setWindowTitle("MGR")
        self.setFixedSize(QSize(800, 480))       
        #layout setup
        self.layout = QStackedLayout()
        self.layout.addWidget(FirstPageWidget())
        self.layout.addWidget(App())
        self.last = LastWidget()
        self.layout.addWidget(self.last) 
        widget = QWidget()
        widget.setLayout(self.layout)
        self.setCentralWidget(widget)
        #RFID setup
        self.thread = RfidThread()
        self.thread.is_good.connect(self.check_id)
        self.thread.start()
        #MQTT client setup
        self.client = MqttClient(self)
        self.client.stateChanged.connect(self.on_stateChanged)
        self.client.messageSignal.connect(self.on_messageSignal)       
        self.client.hostname = "mqtt.eclipseprojects.io"
        self.client.connectToHost()
            
    @QtCore.pyqtSlot(int)
    def on_stateChanged(self, state):
        if state == MqttClient.Connected:          
            self.client.subscribe("evidence/person")
            self.client.subscribe("evidence/accept")
            print(state)

    @QtCore.pyqtSlot(str)
    def on_messageSignal(self, msg):
        data = msg.split()
        try:
            if data[0]!='0': #if person in database
                #get and check the topic
                topic = data[-1]
                if topic == "evidence/person":
                    print(f'{data[0]} {data[1]} STATUS: {data[2]} T: {data[3]}') #mozna usunac
                    self.layout.setCurrentIndex(1)
                elif topic == "evidence/accept":
                    txt2 = data[0]+" "+data[1]
                    txt3 = data[2]
                    self.last.update_label(txt2, txt3) #dopasowac
                    self.layout.setCurrentIndex(2)
                    loop = QEventLoop()
                    QTimer.singleShot(5000, loop.quit)
                    loop.exec_()
                    self.layout.setCurrentIndex(0)
            else:
                print("Access Denied")                               
                self.last.update_label("BRAK DOSTEPU", " ")
                self.layout.setCurrentIndex(2)
                loop = QEventLoop()
                QTimer.singleShot(5000, loop.quit)
                loop.exec_()
                self.layout.setCurrentIndex(0)                     
        except ValueError:
            print("error")

    @QtCore.pyqtSlot(str)
    def on_publishSignal(self, msg):
        print("published")
        
    def closeEvent(self, event):
        self.thread.stop()
        event.accept()
        
    @QtCore.pyqtSlot(float)
    def check_id(self, i):      
        self.client.publish("evidence/id", str(i))
     
app = QApplication(sys.argv)
a = MainWindow()
a.show()
app.exec_()
