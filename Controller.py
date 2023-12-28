import asyncio
from enum import Enum
import time
from PySide6.QtCore import Signal, Slot, QTimer, QTime, QObject
from Model import Model
from View import View
import vars
class ControlState(Enum):
    INITIALISING = 1
    READY_TO_START = 2
    RECORDING_BEATS = 3
    RECORDING_INPUT = 4
    RECORDING_CONFIDENCE = 5
    FINISHED = 6

class Controller:
    
    def __init__(self):
        self.model = Model()
        self.view = View()

        self.view.setWindowTitle("Beat Tracker")
        self.view.resize(1200, 600)
        self.view.show()

        self.model.sensorConnected.connect(self.sensorConnectedHandler)

        self.state = ControlState.INITIALISING

        self.timer_widget = CountdownTimer()
        self.timer_widget.timerFinished.connect(self.countdownFinished)
        
        self.record_start_time = None
        self.timer_sensor_connected = QTimer() # Timer to give the sensor time to connect

        self.view.controls_widget.start_button.clicked.connect(self.buttonPressed)

        self.configureSeriesTimer()

    @Slot()
    def sensorConnectedHandler(self):
        self.setStateReadyAfterDelay()

    @Slot()
    def countdownFinished(self):
        self.state = ControlState.RECORDING_INPUT       
        self.model.getBeatCountMeasured(self.record_start_time, time.time_ns()/1.0e9)
        self.view.control_recording_input()
    
    def configureSeriesTimer(self):
        self.update_ecg_series_timer = QTimer()
        self.update_ecg_series_timer.timeout.connect(self.updateViewWithModelData)
        self.update_ecg_series_timer.setInterval(vars.UPDATE_ECG_SERIES_PERIOD)
        self.update_ecg_series_timer.start()

    def setStateReadyAfterDelay(self):
        if self.state == ControlState.INITIALISING:
            self.timer_sensor_connected.setSingleShot(True)
            self.timer_sensor_connected.timeout.connect(self.setStateReady)
            self.timer_sensor_connected.start(4000)

    def setStateReady(self):
        self.state = ControlState.READY_TO_START
        self.view.control_ready_to_start()

    @Slot()
    def buttonPressed(self):
        if self.state == ControlState.INITIALISING:
            pass
        elif self.state == ControlState.READY_TO_START:
            self.state = ControlState.RECORDING_BEATS
            self.timer_widget.startTimer()
            self.view.control_recording_beats()
            self.record_start_time = time.time_ns()/1.0e9
        elif self.state == ControlState.RECORDING_BEATS:
            pass
        elif self.state == ControlState.RECORDING_INPUT:
            self.state = ControlState.RECORDING_CONFIDENCE
            accuracy = self.model.getBeatCountAccuracy(self.view.controls_widget.beat_count_input.value())
            print(f"Accuracy: {accuracy:.3f}")
            self.view.control_recording_confidence()
        elif self.state == ControlState.RECORDING_CONFIDENCE:
            self.model.setBeatCountConfidence(self.view.controls_widget.confidence_scale.value())
            self.model.saveBeatTrackingData()
            self.state = ControlState.FINISHED
        elif self.state == ControlState.FINISHED:
            self.state = ControlState.READY_TO_START
            self.view.control_ready_to_start()
            self.record_start_time = None

    def updateViewWithModelData(self):
        ecg_times_rel_s = self.model.beat_tracker.ecg_times - time.time_ns()/1.0e9
        self.view.update_ecg_series(ecg_times_rel_s, self.model.beat_tracker.ecg_hist)

    async def main(self):
        await self.model.connect_polar()
        await asyncio.gather(self.model.update_ecg())

class CountdownTimer(QObject):
    timerFinished = Signal()

    def __init__(self):
        super().__init__()
        
        self.countdown_time = QTime(0, 0, 10)
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.updateTimer)

    def updateTimer(self):
        # Subtract one second
        self.countdown_time = self.countdown_time.addSecs(-1)
        print(f"Countdown: {self.countdown_time.toString('mm:ss')}")

        # Stop the timer if the countdown has finished
        if self.countdown_time == QTime(0, 0, 0):
            self.timer.stop()
            self.timerFinished.emit()

    def startTimer(self):
        if not self.timer.isActive():
            self.timer.start(1000)
    
    def resetTimer(self):
        self.countdown_time = QTime(0, 0, 5)
        print(f"Countdown reset to: {self.countdown_time.toString('mm:ss')}")

