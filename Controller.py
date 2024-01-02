import asyncio
from enum import Enum
import time
from PySide6.QtCore import Signal, Slot, QTimer, QTime, QObject
from Model import Model
from View import View
import numpy as np
import vars
class ControlState(Enum):
    SCANNING = 1
    INITIALISING = 2
    SESSION_INTRO = 3
    READY_TO_START = 4
    RECORDING_BEATS = 5
    RECORDING_INPUT = 6
    RECORDING_CONFIDENCE = 7
    RESULTS = 8

class Controller:
    
    def __init__(self):
        self.model = Model()
        self.view = View()

        self.view.setWindowTitle("Beat Tracker")
        self.view.resize(800, 500)
        self.view.show()

        self.state = ControlState.SCANNING
        self.initialising_timer = QTimer()
        self.recording_timer = CountdownTimer()

        self.model.sensorConnected.connect(self.sensorConnectedHandler)
        self.initialising_timer.timeout.connect(self.initialisingTimerFinishedHandler)
        self.recording_timer.timerFinished.connect(self.recordingTimerFinishedHandler)
        self.view.controls_widget.start_button.clicked.connect(self.buttonPressedHandler)
        
        self.configureSeriesTimer()

        self.trials_per_session = len(vars.TRIAL_LENGTHS_S)
        self.trial_id = -1
        self.trial_lengths_s = np.array(vars.TRIAL_LENGTHS_S, copy=True)
        np.random.shuffle(self.trial_lengths_s)

    @Slot()
    def sensorConnectedHandler(self):
        if self.state == ControlState.SCANNING:
            self.changeState(ControlState.INITIALISING)

    @Slot()
    def initialisingTimerFinishedHandler(self):
        if self.state == ControlState.INITIALISING:
            self.changeState(ControlState.SESSION_INTRO)

    @Slot()
    def recordingTimerFinishedHandler(self):
        if self.state == ControlState.RECORDING_BEATS:
            self.changeState(ControlState.RECORDING_INPUT)

    @Slot()
    def buttonPressedHandler(self):
        if self.state == ControlState.READY_TO_START:
            self.changeState(ControlState.RECORDING_BEATS)
        elif self.state == ControlState.SESSION_INTRO:
            self.changeState(ControlState.READY_TO_START)
        elif self.state == ControlState.RECORDING_INPUT:
            self.changeState(ControlState.RECORDING_CONFIDENCE)
        elif self.state == ControlState.RECORDING_CONFIDENCE:
            if self.trial_id < self.trials_per_session-1:
                self.changeState(ControlState.READY_TO_START)
            else:
                self.changeState(ControlState.RESULTS)
        elif self.state == ControlState.RESULTS:
            self.changeState(ControlState.SESSION_INTRO)

    def changeState(self, newState):
        exitStateHandler = {
            ControlState.SCANNING: None,
            ControlState.INITIALISING: None,
            ControlState.SESSION_INTRO: None,
            ControlState.READY_TO_START: None,
            ControlState.RECORDING_BEATS: None,
            ControlState.RECORDING_INPUT: None,
            ControlState.RECORDING_CONFIDENCE: self.exitRecordingConfidenceState,
            ControlState.RESULTS: None
        }
        if exitStateHandler[self.state] is not None:
            exitStateHandler[self.state]()
        
        enterStateHandler = {
            ControlState.SCANNING: None,
            ControlState.INITIALISING: self.enterInitialisingState,
            ControlState.SESSION_INTRO: self.enterSessionIntroState,
            ControlState.READY_TO_START: self.enterReadyToStartState,
            ControlState.RECORDING_BEATS: self.enterRecordingBeatsState,
            ControlState.RECORDING_INPUT: self.enterRecordingInputState,
            ControlState.RECORDING_CONFIDENCE: self.enterRecordingConfidenceState,
            ControlState.RESULTS: self.enterResultsState
        }
        if enterStateHandler[newState] is not None:
            enterStateHandler[newState]()
        self.state = newState

    def enterInitialisingState(self):
        self.initialising_timer.setSingleShot(True)
        self.initialising_timer.start(4000)
    
    def enterSessionIntroState(self):
        self.view.control_session_intro(self.trials_per_session)
        self.trial_id = -1

    def enterReadyToStartState(self):
        self.trial_id += 1
        self.recording_timer.initTimer(self.trial_lengths_s[self.trial_id])
        self.view.control_ready_to_start(self.trial_id+1, self.trials_per_session)
        self.record_start_time = None
        self.beat_count_estimate = None

    def enterRecordingBeatsState(self):
        self.view.control_recording_beats()
        self.recording_timer.startTimer()
        self.record_start_time = time.time_ns()/1.0e9

    def enterRecordingInputState(self):
        self.view.control_recording_input()

    def enterRecordingConfidenceState(self):
        self.beat_count_estimate = self.view.controls_widget.beat_count_input.value()
        self.view.control_recording_confidence()

    def exitRecordingConfidenceState(self):
        self.model.calculateTrialResults(self.trial_lengths_s[self.trial_id], self.record_start_time, time.time_ns()/1.0e9, \
                                         self.beat_count_estimate, self.view.controls_widget.confidence_scale.value())

    def enterResultsState(self):
        self.view.control_results()
        self.model.viewResults()
        
    # View update functions
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

    def __init__(self):
        super().__init__()

        self.timer = QTimer(self)
        self.timer.timeout.connect(self.updateTimer)

    def initTimer(self, duration_s):
        self.countdown_time = QTime(0, 0, duration_s)

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
    
