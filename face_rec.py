from PyQt5 import QtGui
from PyQt5.QtWidgets import QWidget, QLabel, QVBoxLayout
from PyQt5.QtGui import QPixmap
import cv2
from PyQt5.QtCore import pyqtSignal, pyqtSlot, Qt, QThread
from PyQt5 import QtCore
import numpy as np
import face_recognition
from mqtt import MqttClient

class VideoThread(QThread):
    change_pixmap_signal = pyqtSignal(np.ndarray)
    #name_signal = pyqtSignal(str)

    def __init__(self):
        super().__init__()
        self._run_flag = True

        self.mateusz_image = face_recognition.load_image_file("/home/pi/face_recognition/tests/test_images/ja.jpg")
        self.mateusz_face_encoding = face_recognition.face_encodings(self.mateusz_image)[0]

        self.known_face_encodings = [
            self.mateusz_face_encoding
            ]

        self.known_face_names = [
            "Mateusz Grzywaczewski"
        ]
        
        self.client1 = MqttClient(self)
        self.client1.stateChanged.connect(self.on_stateChanged)
        self.client1.hostname = "mqtt.eclipseprojects.io"
        self.client1.connectToHost()
        
    @QtCore.pyqtSlot(int)
    def on_stateChanged(self, state):
        if state == MqttClient.Connected:
            #self.client.subscribe("evidence/per")
            print(str(state) + " client1")

    def run(self):
        # capture from web cam
        cap = cv2.VideoCapture(0)
        cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)  
        cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
        while self._run_flag:
            ret, cv_img = cap.read()
            if ret:
                self.change_pixmap_signal.emit(cv_img)
                face_locations = []
                face_encodings = []
                face_names = []
                process_this_frame = True
                
                # Grab a single frame of video
                ret, frame = cap.read()
                # Resize frame of video to 1/4 size for faster face recognition processing
                small_frame = cv2.resize(frame, (0, 0), fx=0.25, fy=0.25)
                # Convert the image from BGR color (which OpenCV uses) to RGB color (which face_recognition uses)
                rgb_small_frame = small_frame[:, :, ::-1]
                
                # Only process every other frame of video to save time
                if process_this_frame:
                    # Find all the faces and face encodings in the current frame of video
                    face_locations = face_recognition.face_locations(rgb_small_frame)
                    face_encodings = face_recognition.face_encodings(rgb_small_frame, face_locations)

                    face_names = []
                    for face_encoding in face_encodings:
                        for _ in range(3):
                            # See if the face is a match for the known face(s)
                            matches = face_recognition.compare_faces(self.known_face_encodings, face_encoding)
                            name = "Nie rozpoznano"

                            # Or instead, use the known face with the smallest distance to the new face
                            face_distances = face_recognition.face_distance(self.known_face_encodings, face_encoding)
                            best_match_index = np.argmin(face_distances)
                            if matches[best_match_index]:
                                name = self.known_face_names[best_match_index]
                            
                            face_names.append(name)
                        msg = max(set(face_names), key=face_names.count)
                        self.client1.publish("evidence/personFace", name) #check 3 times if unknown

                process_this_frame = not process_this_frame     
        # shut down capture system
        cap.release()
  
    def stop(self):
        """Sets run flag to False and waits for thread to finish"""
        self._run_flag = False
        self.wait()


class App(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Qt live label demo")
        self.disply_width = 800
        self.display_height = 480
        #layout setup
        self.image_label = QLabel(self)
        self.image_label.resize(self.disply_width, self.display_height)
        self.image_label.setAlignment(Qt.AlignHCenter)      
        self.textLabel = QLabel('SPOJRZ W KAMERE')
        self.textLabel.setAlignment(Qt.AlignHCenter)
        vbox = QVBoxLayout()
        vbox.addWidget(self.image_label)
        vbox.addWidget(self.textLabel)
        self.setLayout(vbox)   
        #video capture thread
        self.thread = VideoThread()
        self.thread.change_pixmap_signal.connect(self.update_image)
        self.thread.start()
 
    def closeEvent(self, event):
        self.thread.stop()
        event.accept()

    @pyqtSlot(np.ndarray)
    def update_image(self, cv_img):
        """Updates the image_label with a new opencv image"""
        qt_img = self.convert_cv_qt(cv_img)
        self.image_label.setPixmap(qt_img)

    def convert_cv_qt(self, cv_img):
        """Convert from an opencv image to QPixmap"""
        rgb_image = cv2.cvtColor(cv_img, cv2.COLOR_BGR2RGB)
        h, w, ch = rgb_image.shape
        bytes_per_line = ch * w
        convert_to_Qt_format = QtGui.QImage(
            rgb_image.data, w, h, bytes_per_line, QtGui.QImage.Format_RGB888)
        p = convert_to_Qt_format.scaled(
            self.disply_width, self.display_height, Qt.KeepAspectRatio)
        return QPixmap.fromImage(p)


