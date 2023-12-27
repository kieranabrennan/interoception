from enum import Enum
import time
from PySide6.QtCore import Qt, Signal, Slot, QTimer, QTime
from PySide6.QtWidgets import QVBoxLayout, QWidget, QPushButton, QLabel, QSpinBox

class ControlState(Enum):
    INITIALISING = 1
    READY_TO_START = 2
    RECORDING_BEATS = 3
    RECORDING_INPUT = 4
    FINISHED = 5

class Controller(QWidget):
    beatCountingFinished = Signal(float, float)
    beatEntered = Signal(int)
    
    def __init__(self):
        super().__init__()

        self.countdown_timer = CountdownTimer()
        self.state = ControlState.INITIALISING

        self.initUI()

    def initUI(self):

        controls_layout = QVBoxLayout()
        self.setLayout(controls_layout)

        self.message_box = QLabel()
        self.message_box.setStyleSheet("background-color: yellow; color: black;")
        self.message_box.setText("Connecting to sensor...")
        self.message_box.setMaximumWidth(800)
        self.message_box.setMinimumWidth(500)
        self.message_box.setMinimumHeight(60)
        self.message_box.setAlignment(Qt.AlignCenter)
        controls_layout.addWidget(self.message_box, alignment=Qt.AlignCenter)

        self.start_button = QPushButton("Start")
        self.start_button.setStyleSheet("background-color: white; color: grey; border: 1px solid grey;")
        self.start_button.setMaximumWidth(500)
        self.start_button.setMinimumWidth(100)
        self.start_button.setMinimumHeight(30)
        controls_layout.addWidget(self.start_button, alignment=Qt.AlignCenter)

        self.spin_box = QSpinBox()
        self.spin_box.setStyleSheet("background-color: white; color: grey; border: 1px solid grey;")
        self.spin_box.setRange(0, 100)
        self.spin_box.setSingleStep(1)
        self.spin_box.setValue(0)
        self.spin_box.setMaximumWidth(200)
        self.spin_box.setMinimumWidth(100)
        self.spin_box.setMinimumHeight(30)
        self.spin_box.setAlignment(Qt.AlignCenter)
        controls_layout.addWidget(self.spin_box, alignment=Qt.AlignCenter)
        self.spin_box.setEnabled(False)

        self.timer_widget = CountdownTimer()
        self.timer_widget.timerFinished.connect(self.countdownFinished)
        self.start_button.clicked.connect(self.buttonPressed)
        controls_layout.addWidget(self.timer_widget)

        self.record_start_time = None
        self.timer_sensor_connected = QTimer() # Timer to give the sensor time to connect

        self.beat_accuracy = None

    def setStateReadyAfterDelay(self):
        if self.state == ControlState.INITIALISING:
            self.timer_sensor_connected.setSingleShot(True)
            self.timer_sensor_connected.timeout.connect(self.setStateReady)
            self.timer_sensor_connected.start(4000)

    def setStateReady(self):
        self.state = ControlState.READY_TO_START
        self.message_box.setText("Press start and begin heart beat counting")
        self.message_box.setStyleSheet("background-color: green; color: black;")
        self.start_button.setStyleSheet("background-color: white; color: black; border: 1px solid black;")

    @Slot()
    def buttonPressed(self):
        if self.state == ControlState.INITIALISING:
            pass
        elif self.state == ControlState.READY_TO_START:
            self.timer_widget.startTimer()
            self.state = ControlState.RECORDING_BEATS
            self.message_box.setText("Count your heart beats\nWithout checking your pulse")
            self.message_box.setStyleSheet("background-color: red; color: white;")
            self.spin_box.setEnabled(False)
            self.spin_box.setStyleSheet("background-color: white; color: grey; border: 1px solid grey;")
            self.record_start_time = time.time_ns()/1.0e9
        elif self.state == ControlState.RECORDING_BEATS:
            pass
        elif self.state == ControlState.RECORDING_INPUT:
            self.state = ControlState.FINISHED
            self.beatEntered.emit(self.spin_box.value())
            self.message_box.setText("Finished")
            self.message_box.setStyleSheet("background-color: green; color: white;")
            self.start_button.setText("Restart")
            self.start_button.setStyleSheet("background-color: white; color: black; border: 1px solid black;")
            self.spin_box.setEnabled(False)
            self.spin_box.setStyleSheet("background-color: white; color: grey; border: 1px solid grey;")
        elif self.state == ControlState.FINISHED:
            self.state = ControlState.READY_TO_START
            self.message_box.setText("Press start and begin heart beat counting")
            self.message_box.setStyleSheet("background-color: green; color: black;")
            self.start_button.setText("Start")
            self.start_button.setStyleSheet("background-color: white; color: black; border: 1px solid black;")
            self.spin_box.setValue(0)
            self.record_start_time = None

    @Slot()
    def countdownFinished(self):
        self.state = ControlState.RECORDING_INPUT        
        self.spin_box.setEnabled(True)
        self.spin_box.setStyleSheet("background-color: white; color: black; border: 1px solid black;")
        self.message_box.setText("Enter how many heart beats you counted")
        self.message_box.setStyleSheet("background-color: green; color: white;")
        self.start_button.setText("Submit")
        self.beatCountingFinished.emit(self.record_start_time, time.time_ns()/1.0e9)

class CountdownTimer(QWidget):
    timerFinished = Signal()

    def __init__(self):
        super().__init__()

        self.initUI()

    def initUI(self):
        # Set up the main widget and layout
        layout = QVBoxLayout(self)

        # Create and configure the label to show the time
        self.time_label = QLabel("00:10")
        self.time_label.setStyleSheet("color: black;")
        self.time_label.setAlignment(Qt.AlignCenter)

        layout.addWidget(self.time_label)

        self.countdown_time = QTime(0, 0, 10)

        # Create a QTimer
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.updateTimer)

    def updateTimer(self):
        # Subtract one second
        self.countdown_time = self.countdown_time.addSecs(-1)
        
        # Update the label
        self.time_label.setText(self.countdown_time.toString("mm:ss"))

        # Stop the timer if the countdown has finished
        if self.countdown_time == QTime(0, 0, 0):
            self.timer.stop()
            self.timerFinished.emit()

    def startTimer(self):
        if not self.timer.isActive():
            self.timer.start(1000)
    
    def resetTimer(self):
        self.countdown_time = QTime(0, 0, 5)
        self.time_label.setText(self.countdown_time.toString("mm:ss"))
