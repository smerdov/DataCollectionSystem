#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys
from PyQt5.QtWidgets import QWidget, QGridLayout, QPushButton, QApplication,\
    QTextEdit, QLabel, QFrame, QVBoxLayout, QHBoxLayout, QLineEdit, QCheckBox, QMessageBox
from PyQt5.QtGui import QIcon, QPixmap
from PyQt5.Qt import QRect
from PyQt5 import QtGui, Qt
from queue import Queue
import time
import threading
from UDPServer import PlayerArduinoPortConverter, ListeningThread, PeriodicSendingThread, SendingThread, SLEEP_TIME
import itertools
from collections import defaultdict
from datetime import datetime
import socket
import os
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *

player_arduino_port_converter = PlayerArduinoPortConverter()
player_arduino2port = player_arduino_port_converter.get_player_arduino2port_converter()
port2player_arduino = player_arduino_port_converter.get_port2player_arduino_converter()


TIME_FORMAT4FILES = '%Y-%m-%d-%H-%M-%S'


class StatusWidget(QWidget):

    STATUS_COLORS = {
        'Idle': '#0000AA',
        'Measuring': '#00AA00',
        'NA': '#777777',
        'File error': '#AA0000',
    }

    def __init__(self, square_size = 15, timeout=2):
        super().__init__()

        self.square = QFrame(self)
        self.square.setStyleSheet("QWidget { background-color: %s }" % self.STATUS_COLORS['NA'])
        self.square.setFixedSize(square_size, square_size)
        # self.square.setMaximumHeight(25)
        self.timeout = timeout
        self.status = 'NA'


        self.label = QLabel(text=self.status, parent=self)
        # self.label.setMaximumHeight(100)
        # self.label.setSizePolicy(QSizePolicy.Minimum, QSizePolicy.Minimum)
        self.label.setMinimumSize(22, 22)
        self.label.setAlignment(Qt.AlignTop)
        # self.label.Preferred

        self.default_color = self.STATUS_COLORS['NA']
        self.update_timestamp = datetime.now().timestamp()
        self.status_color = self.STATUS_COLORS['NA']

        self.layout = QHBoxLayout(self)
        self.layout.addWidget(self.square, Qt.AlignLeft)
        self.layout.addWidget(self.label, Qt.AlignLeft)
        # self.layout.setSpacing(0)

        self.setLayout(self.layout)


    def updateStatus(self, new_status, update_timestamp=True):
        if update_timestamp:
            self.update_timestamp = datetime.now().timestamp()

        if new_status == self.status:
            return

        new_status_first_part = new_status.split(',')[0]
        new_status_color = self.STATUS_COLORS.get(new_status_first_part, self.default_color)
        if new_status_color != self.status_color:
            self.square.setStyleSheet("QWidget { background-color: %s }" % new_status_color)

        self.label.setText(new_status)


    def isOutdated(self, timeout=None, current_timestamp=None):
        if timeout is None:
            timeout = self.timeout

        if current_timestamp is None:
            current_timestamp = datetime.now().timestamp()

        return (current_timestamp - self.update_timestamp > timeout)

    # def sizeHint(self):
    #     return QSize(20, 35)



class Example(QWidget):

    # STATUS_COLORS = {
    #     'Idle': '#0000AA',
    #     'Measuring': '#00AA00',
    #     'unknown': '#777777'
    # }  # TODO: make it default dict for unknown statuses?

    def __init__(self, n_players=5, n_arduinos=3, address=('255.255.255.255', 3000)):
        super().__init__()

        self.input_queue = Queue(maxsize=1000)
        self.n_players = n_players
        self.n_arduinos = n_arduinos
        self.status_widgets_dict = {}
        self.listener_threads_dict = {}
        self.ip = self.getIP()

        for n_player, n_arduino in itertools.product(range(self.n_players), range(self.n_arduinos)):
            self.status_widgets_dict[(n_player, n_arduino)] = StatusWidget()
            self.status_widgets_dict[(n_player, n_arduino)].setMaximumHeight(28)
            # self.status_widgets_dict[(n_player, n_arduino)].label.update()

            port = player_arduino2port(player_id=n_player, arduino_id=n_arduino)
            self.listener_threads_dict[(n_player, n_arduino)] = ListeningThread(
                queue=self.input_queue,
                port=port,
                # name=f'arduino_{n_player}_{n_arduino}',
                verbose=False)
            self.listener_threads_dict[(n_player, n_arduino)].start()

        self.periodic_sending_thread = PeriodicSendingThread(port=4000, address=address, msg='status;')
        self.peridoc_send = True
        self.periodic_sending_thread.start_periodic_send()
        self.periodic_sending_thread.start()

        self.sending_thread = SendingThread(port=4002, address=address)
        self.sending_thread.start()

        self.sendSetUdpIp(self.ip)
        self.sendSetFtpIp(self.ip)
        self.closed = False

        self.initUI()

    def initUI(self):
        grid = QGridLayout()
        grid.setVerticalSpacing(0)
        # grid.setVerticalSpacing(0)
        # grid.setHorizontalSpacing(0)
        # grid.setSizeConstraint()

        for n_arduino in range(self.n_arduinos):
            arduino_label = QLabel(f'Arduino_{n_arduino}')
            arduino_label.setContentsMargins(13, 0, 0, 0)
            grid.addWidget(arduino_label, 0, 1 + n_arduino)# , alignment=Qt.AlignBottom)

        for n_player in range(self.n_players):
            player_label = QLabel(f'Player_{n_player}')
            player_label.setContentsMargins(0, 0, 0, 0)
            print(type(player_label.layout()))
                # .setContentsMargins(0, -10, 0, 0)
            # player_label.setAlignment(Qt.AlignBottom)
            grid.addWidget(player_label, 1 + n_player, 0, alignment=Qt.AlignBottom)

        for n_arduino in range(self.n_arduinos):
            for n_player in range(self.n_players):
                grid.addWidget(self.status_widgets_dict[(n_player, n_arduino)], 1 + n_player, 1 + n_arduino)#, alignment=Qt.AlignLeft)


        self.button_start = QPushButton('Start', self)
        self.button_stop = QPushButton('Stop', self)

        self.button_start.clicked.connect(self.sendStart)
        self.button_stop.clicked.connect(self.sendStop)


        self.button_time_sync = QPushButton('Time sync', self)
        self.button_status = QPushButton('Status', self)
        self.button_periodic_sending = QCheckBox('Periodic Sending', self)
        self.button_periodic_sending.setChecked(True)
        self.button_periodic_sending.stateChanged.connect(self.periodicSendingChange)

        self.button_time_sync.clicked.connect(self.sendTimeSync)
        self.button_status.clicked.connect(self.sendStatus)


        self.button_set_udp = QPushButton('Set UDP IP', self)
        self.button_set_ftp = QPushButton('Set FTP IP', self)
        self.line_my_ip = QLineEdit(self)

        self.line_my_ip.setText(self.ip)
        self.button_set_udp.clicked.connect(lambda : self.sendSetUdpIp(self.line_my_ip.text()))
        self.button_set_ftp.clicked.connect(lambda : self.sendSetFtpIp(self.line_my_ip.text()))
        self.line_my_ip.setFixedWidth(120)


        current_datetime = datetime.now().strftime(TIME_FORMAT4FILES)
        # self.line_upload_date_min.setText(current_datetime)

        self.text_ftpline_0 = QLabel("Upload data from ", self)
        self.line_upload_date_min = QLineEdit(current_datetime, self)
        self.text_ftpline_1 = QLabel(" to ", self)
        self.line_upload_date_max = QLineEdit('2019-12-31-00-00-00', self)
        self.button_upload_via_ftp = QPushButton('Upload', self)

        self.line_upload_date_min.setFixedWidth(160)
        self.line_upload_date_max.setFixedWidth(160)
        self.button_upload_via_ftp.clicked.connect(lambda : self.sendUploadViaFTP(
            self.line_upload_date_min.text(), self.line_upload_date_max.text()))


        layout_horizontal_0 = QHBoxLayout()
        layout_horizontal_0.addWidget(self.button_start)
        layout_horizontal_0.addWidget(self.button_stop)

        layout_horizontal_1 = QHBoxLayout()
        layout_horizontal_1.addWidget(self.button_time_sync)
        layout_horizontal_1.addWidget(self.button_status)
        layout_horizontal_1.addWidget(self.button_periodic_sending)

        layout_horizontal_2 = QHBoxLayout()
        layout_horizontal_2.addWidget(self.line_my_ip)
        layout_horizontal_2.addWidget(self.button_set_udp)
        layout_horizontal_2.addWidget(self.button_set_ftp)

        layout_horizontal_3 = QHBoxLayout()
        layout_horizontal_3.addWidget(self.text_ftpline_0)
        layout_horizontal_3.addWidget(self.line_upload_date_min)
        layout_horizontal_3.addWidget(self.text_ftpline_1)
        layout_horizontal_3.addWidget(self.line_upload_date_max)
        layout_horizontal_3.addWidget(self.button_upload_via_ftp)

        layout_vertical = QVBoxLayout()
        layout_vertical.addLayout(grid)
        layout_vertical.addLayout(layout_horizontal_0)
        layout_vertical.addLayout(layout_horizontal_1)
        layout_vertical.addLayout(layout_horizontal_2)
        layout_vertical.addLayout(layout_horizontal_3)
        # layout_vertical.setSpacing(1)

        self.setLayout(layout_vertical)

        self.move(300, 150)
        self.setWindowTitle('Control Panel')
        self.input_queue_updater_thread = threading.Thread(target=self.input_queue_updater)
        self.input_queue_updater_thread.start()

        self.relevance_updater_thread = threading.Thread(target=self.relevance_updater)
        self.relevance_updater_thread.start()

        self.show()

    def input_queue_updater(self):
        while not self.closed:
            if self.input_queue.empty():
                time.sleep(SLEEP_TIME)
                continue

            item = self.input_queue.get(block=True)

            if item['msg_type'] == 'status':
                status = item['msg_content']
                n_player, n_arduino = port2player_arduino(item['receiving_port'])

                self.status_widgets_dict[(n_player, n_arduino)].updateStatus(new_status=status)

            time.sleep(0.001)


    def relevance_updater(self, period=0.01, timeout=2):
        while not self.closed:
            current_timestamp = datetime.now().timestamp()
            for n_player, n_arduino in itertools.product(range(self.n_players), range(self.n_arduinos)):
                status_widget = self.status_widgets_dict[(n_player, n_arduino)]

                if status_widget.isOutdated(timeout=timeout, current_timestamp=current_timestamp):
                    status_widget.updateStatus('NA')

            time.sleep(period)

    def getIP(self):
        hostname = socket.gethostname()
        ip = socket.gethostbyname(hostname)

        return ip


    def sendMsg(self, msg):
        self.sending_thread.send(msg)

    def sendStart(self):
        self.sendMsg('start;')

    def sendStop(self):
        self.sendMsg('end;')

    def sendStatus(self):
        self.sendMsg('status;')

    def sendTimeSync(self):
        self.sendMsg('time_sync;')

    def sendSetUdpIp(self, udp_ip):
        self.sendMsg(f'set udp {udp_ip};')

    def sendSetFtpIp(self, ftp_ip):
        self.sendMsg(f'set ftp {ftp_ip};')

    def sendUploadViaFTP(self, datetime_start, datetime_end):
        reply = QMessageBox.question(self, 'Are you sure?',
                                     "Are you sure you want to upload the data from Arduino's to the FTP Server? "
                                     "This may take some time, and you won't be able to start new measurements during upload",
                                     QMessageBox.Yes |
                                     QMessageBox.No,
                                     QMessageBox.No)

        if reply == QMessageBox.Yes:
            self.sendMsg(f'upload {datetime_start} {datetime_end};')


    def periodicSendingChange(self):
        self.peridoc_send = not self.peridoc_send
        if self.peridoc_send:
            self.periodic_sending_thread.start_periodic_send()
        else:
            self.periodic_sending_thread.stop_periodic_send()

    def closeEvent(self, event):
        print("CLOSING")
        self.closed = True
        self.periodic_sending_thread.closed = True
        self.periodic_sending_thread.join()

        for listener_thread_name, listener_thread in self.listener_threads_dict.items():
            listener_thread.closed = True

        time.sleep(SLEEP_TIME * 2)

        for listener_thread_name, listener_thread in self.listener_threads_dict.items():
            listener_thread.socket.close()
            listener_thread.join()
            # print(listener_thread, 'closed')

        # print('Joining sending threads...')
        self.sending_thread.join()
        self.periodic_sending_thread.join()

        # print("Joining relevance_updater_thread")
        self.relevance_updater_thread.join()
        # print("Joining input_queue_updater_thread")
        self.input_queue_updater_thread.join()

        # print('Closing the main widget')
        self.close()
        # self.destroy()




if __name__ == '__main__':
    app = QApplication(sys.argv)
    path = os.path.join(os.path.dirname(sys.modules[__name__].__file__), 'Icons/Icon_0.ico')
    app.setWindowIcon(QIcon(QPixmap(path)))
    ex = Example()
    print(ex.size())
    sys.exit(app.exec_())
