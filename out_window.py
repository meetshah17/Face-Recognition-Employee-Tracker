from PyQt5.QtGui import QImage, QPixmap
from PyQt5.uic import loadUi
from PyQt5.QtCore import pyqtSlot, QTimer, QDate, Qt
from PyQt5.QtWidgets import QDialog, QMessageBox
import cv2
import face_recognition
import numpy as np
import datetime
import os
import csv
import sqlite3

class Ui_OutputDialog(QDialog):
    def __init__(self):
        super(Ui_OutputDialog, self).__init__()
        loadUi("./outputwindow.ui", self)

        # Initialize dictionary to track clock-in/clock-out status for each employee
        self.employee_status = {}

        # Update time
        now = QDate.currentDate()
        current_date = now.toString('dd MM yyyy')
        current_time = datetime.datetime.now().strftime("%I:%M %p")
        self.Date_Label.setText(current_date)
        self.Time_Label.setText(current_time)

        self.image = None

    @pyqtSlot()
    def startVideo(self, camera_name):
        """
        :param camera_name: link of camera or usb camera
        :return:
        """
        if len(camera_name) == 1:
            self.capture = cv2.VideoCapture(int(camera_name))
        else:
            self.capture = cv2.VideoCapture(camera_name)
        self.timer = QTimer(self)  # Create Timer
        path = 'ImagesAttendance'
        if not os.path.exists(path):
            os.mkdir(path)
        # known face encoding and known face name list
        images = []
        self.class_names = []
        self.encode_list = []
        self.TimeList1 = []
        self.TimeList2 = []
        attendance_list = os.listdir(path)

        # print(attendance_list)
        for cl in attendance_list:
            cur_img = cv2.imread(f'{path}/{cl}')
            images.append(cur_img)
            self.class_names.append(os.path.splitext(cl)[0])
        for img in images:
            img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
            boxes = face_recognition.face_locations(img)
            encodes_cur_frame = face_recognition.face_encodings(img, boxes)[0]
            # encode = face_recognition.face_encodings(img)[0]
            self.encode_list.append(encodes_cur_frame)
        self.timer.timeout.connect(self.update_frame)  # Connect timeout to the output function
        self.timer.start(10)  # emit the timeout() signal at x=40ms

    def mark_attendance(self, name, action):
        """
        :param name: detected face known or unknown one
        :param action: Clock In or Clock Out
        """
        if name != 'unknown':
            if action == 'Clock In':
                if self.employee_status.get(name) == 'Clock In':
                    # Employee is already clocked in
                    QMessageBox.information(self, 'Clock In', 'You are already clocked in.')
                    return
                elif self.employee_status.get(name) == 'Clock Out':
                    # Employee is clocked out, updating status to clocked in
                    self.employee_status[name] = 'Clock In'
                else:
                    # New employee, initializing status as clocked in
                    self.employee_status[name] = 'Clock In'
            elif action == 'Clock Out':
                if self.employee_status.get(name) == 'Clock Out':
                    # Employee is already clocked out
                    QMessageBox.information(self, 'Clock Out', 'You are already clocked out.')
                    return
                elif self.employee_status.get(name) != 'Clock In':
                    # Employee is not clocked in
                    QMessageBox.information(self, 'Clock Out', 'You need to clock in first.')
                    return
                else:
                    # Updating status to clocked out
                    self.employee_status[name] = 'Clock Out'

            # Proceed with attendance marking
            with sqlite3.connect('attendance.db') as conn:
                cursor = conn.cursor()
                date_time_string = datetime.datetime.now().strftime("%d/%m/%y %H:%M:%S")
                cursor.execute("INSERT INTO attendance (name, datetime, action) VALUES (?, ?, ?)",
                               (name, date_time_string, action))
                conn.commit()
                if action == 'Clock In':
                    # Update UI for clock in
                    self.ClockInButton.setChecked(False)
                    self.NameLabel.setText(name)
                    self.StatusLabel.setText('Clocked In')
                    self.HoursLabel.setText('Measuring')
                    self.MinLabel.setText('')
                    self.Time1 = datetime.datetime.now()
                elif action == 'Clock Out':
                    # Update UI for clock out
                    self.ClockOutButton.setChecked(False)
                    self.NameLabel.setText(name)
                    self.StatusLabel.setText('Clocked Out')
                    self.Time2 = datetime.datetime.now()
                    self.ElapseList(name)
                    self.TimeList2.append(datetime.datetime.now())
                    CheckInTime = self.TimeList1[-1]
                    CheckOutTime = self.TimeList2[-1]
                    self.ElapseHours = (CheckOutTime - CheckInTime)
                    self.MinLabel.setText("{:.0f}".format(abs(self.ElapseHours.total_seconds() / 60) % 60) + 'm')
                    self.HoursLabel.setText("{:.0f}".format(abs(self.ElapseHours.total_seconds() / 60 ** 2)) + 'h')

    def face_rec_(self, frame, encode_list_known, class_names):
        """
        :param frame: frame from camera
        :param encode_list_known: known face encoding
        :param class_names: known face names
        :return:
        """
        # Initialize variables to keep track of clock in/out actions
        clock_in_action = False
        clock_out_action = False

        # Face recognition loop...
        faces_cur_frame = face_recognition.face_locations(frame)
        encodes_cur_frame = face_recognition.face_encodings(frame, faces_cur_frame)
        for encodeFace, faceLoc in zip(encodes_cur_frame, faces_cur_frame):
            match = face_recognition.compare_faces(encode_list_known, encodeFace, tolerance=0.50)
            face_dis = face_recognition.face_distance(encode_list_known, encodeFace)
            name = "unknown"
            best_match_index = np.argmin(face_dis)
            if match[best_match_index]:
                name = class_names[best_match_index].upper()
                y1, x2, y2, x1 = faceLoc
                cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)
                cv2.rectangle(frame, (x1, y2 - 20), (x2, y2), (0, 255, 0), cv2.FILLED)
                cv2.putText(frame, name, (x1 + 6, y2 - 6), cv2.FONT_HERSHEY_COMPLEX, 0.5, (255, 255, 255), 1)

                # Check if clock in or clock out button is checked
                if self.ClockInButton.isChecked():
                    if not clock_in_action:
                        self.mark_attendance(name, 'Clock In')
                        clock_in_action = True
                elif self.ClockOutButton.isChecked():
                    if not clock_out_action:
                        self.mark_attendance(name, 'Clock Out')
                        clock_out_action = True

        # Uncheck clock in/out buttons after actions are completed
        if clock_in_action:
            self.ClockInButton.setChecked(False)
        if clock_out_action:
            self.ClockOutButton.setChecked(False)

        return frame

    def showdialog(self):
        msg = QMessageBox()
        msg.setIcon(QMessageBox.Information)

        msg.setText("This is a message box")
        msg.setInformativeText("This is additional information")
        msg.setWindowTitle("MessageBox demo")
        msg.setDetailedText("The details are as follows:")
        msg.setStandardButtons(QMessageBox.Ok | QMessageBox.Cancel)


    def ElapseList(self, name):
        with sqlite3.connect('attendance.db') as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT datetime, action FROM attendance WHERE name = ?", (name,))
            rows = cursor.fetchall()

            Time1 = datetime.datetime.now()
            Time2 = datetime.datetime.now()

            for row in rows:
                datetime_str, action = row
                if action == 'Clock In':
                    Time1 = datetime.datetime.strptime(datetime_str, '%d/%m/%y %H:%M:%S')
                    self.TimeList1.append(Time1)
                elif action == 'Clock Out':
                    Time2 = datetime.datetime.strptime(datetime_str, '%d/%m/%y %H:%M:%S')
                    self.TimeList2.append(Time2)

    def update_frame(self):
        ret, self.image = self.capture.read()
        self.displayImage(self.image, self.encode_list, self.class_names, 1)

    def displayImage(self, image, encode_list, class_names, window=1):
        """
        :param image: frame from camera
        :param encode_list: known face encoding list
        :param class_names: known face names
        :param window: number of window
        :return:
        """
        image = cv2.resize(image, (640, 480))
        try:
            image = self.face_rec_(image, encode_list, class_names)
        except Exception as e:
            print(e)
        qformat = QImage.Format_Indexed8
        if len(image.shape) == 3:
            if image.shape[2] == 4:
                qformat = QImage.Format_RGBA8888
            else:
                qformat = QImage.Format_RGB888
        outImage = QImage(image, image.shape[1], image.shape[0], image.strides[0], qformat)
        outImage = outImage.rgbSwapped()

        if window == 1:
            self.imgLabel.setPixmap(QPixmap.fromImage(outImage))
            self.imgLabel.setScaledContents(True)
