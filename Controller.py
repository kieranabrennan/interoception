import asyncio
from enum import Enum
import time
from PySide6.QtCore import Signal, Slot, QTimer, QTime, QObject
from Model import Model
from View import View
import vars
class ControlState(Enum):
    SCANNING = 1
    INITIALISING = 2
    READY_TO_START = 3
    RECORDING_BEATS = 4
    RECORDING_INPUT = 5
    RECORDING_CONFIDENCE = 6
    RESULTS = 7

class Controller:
    
    def __init__(self):
        self.model = Model()
        self.view = View()

        self.view.setWindowTitle("Beat Tracker")
        self.view.resize(1200, 600)
        self.view.show()

        self.state = ControlState.SCANNING
        self.initialising_timer = QTimer()
        self.recording_timer = CountdownTimer(10)

        self.beat_count_accuracy = None

        self.model.sensorConnected.connect(self.sensorConnectedHandler)
        self.initialising_timer.timeout.connect(self.initialisingTimerFinishedHandler)
        self.recording_timer.timerFinished.connect(self.recordingTimerFinishedHandler)
        self.view.controls_widget.start_button.clicked.connect(self.buttonPressedHandler)
        
        self.configureSeriesTimer()

    @Slot()
    def sensorConnectedHandler(self):
        if self.state == ControlState.SCANNING:
            self.changeState(ControlState.INITIALISING)

    @Slot()
    def initialisingTimerFinishedHandler(self):
        if self.state == ControlState.INITIALISING:
            self.changeState(ControlState.READY_TO_START)

    @Slot()
    def recordingTimerFinishedHandler(self):
        if self.state == ControlState.RECORDING_BEATS:
            self.changeState(ControlState.RECORDING_INPUT)

    @Slot()
    def buttonPressedHandler(self):
        if self.state == ControlState.READY_TO_START:
            self.changeState(ControlState.RECORDING_BEATS)
        elif self.state == ControlState.RECORDING_INPUT:
            self.changeState(ControlState.RECORDING_CONFIDENCE)
        elif self.state == ControlState.RECORDING_CONFIDENCE:
            self.changeState(ControlState.RESULTS)
        elif self.state == ControlState.RESULTS:
            self.changeState(ControlState.READY_TO_START)

    def changeState(self, newState):
        enterStateHandler = {
            ControlState.SCANNING: self.enterScanningState,
            ControlState.INITIALISING: self.enterInitialisingState,
            ControlState.READY_TO_START: self.enterReadyToStartState,
            ControlState.RECORDING_BEATS: self.enterRecordingBeatsState,
            ControlState.RECORDING_INPUT: self.enterRecordingInputState,
            ControlState.RECORDING_CONFIDENCE: self.enterRecordingConfidenceState,
            ControlState.RESULTS: self.enterResultsState
        }
        enterStateHandler[newState]()
        self.state = newState

    def enterScanningState(self):
        pass

    def enterInitialisingState(self):
        self.initialising_timer.setSingleShot(True)
        self.initialising_timer.start(4000)
    
    def enterReadyToStartState(self):
        self.recording_timer.initTimer(10)
        self.view.control_ready_to_start()
        self.record_start_time = None

    def enterRecordingBeatsState(self):
        self.view.control_recording_beats()
        self.recording_timer.startTimer()
        self.record_start_time = time.time_ns()/1.0e9

    def enterRecordingInputState(self):
        self.view.control_recording_input()
        self.model.getBeatCountMeasured(self.record_start_time, time.time_ns()/1.0e9)

    def enterRecordingConfidenceState(self):
        self.view.control_recording_confidence()
        self.beat_count_accuracy = self.model.getBeatCountAccuracy(self.view.controls_widget.beat_count_input.value())

    def enterResultsState(self):
        self.view.control_results(self.beat_count_accuracy)
        self.model.setBeatCountConfidence(self.view.controls_widget.confidence_scale.value())
        self.model.saveBeatTrackingData()
        
    def updateViewWithModelData(self):
        ecg_times_rel_s = self.model.beat_tracker.ecg_times - time.time_ns()/1.0e9
        self.view.update_ecg_series(ecg_times_rel_s, self.model.beat_tracker.ecg_hist)

    def configureSeriesTimer(self):
            self.update_ecg_series_timer = QTimer()
            self.update_ecg_series_timer.timeout.connect(self.updateViewWithModelData)
            self.update_ecg_series_timer.setInterval(vars.UPDATE_ECG_SERIES_PERIOD)
            self.update_ecg_series_timer.start()

    async def main(self):
        await self.model.connect_polar()
        await asyncio.gather(self.model.update_ecg())

class CountdownTimer(QObject):
    timerFinished = Signal()

    def __init__(self, duration_s):
        super().__init__()

        self.initTimer(duration_s)
    
    def initTimer(self, duration_s):
        self.countdown_time = QTime(0, 0, duration_s)
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.updateTimer)

    def updateTimer(self):
        self.countdown_time = self.countdown_time.addSecs(-1)
        print(f"Countdown: {self.countdown_time.toString('mm:ss')}")

        # Stop the timer if the countdown has finished
        if self.countdown_time == QTime(0, 0, 0):
            self.timer.stop()
            self.timerFinished.emit()

    def startTimer(self):
        if not self.timer.isActive():
            self.timer.start(1000)
    
