
import asyncio
from PySide6.QtCore import QTimer, Qt, QPointF, QFile, Slot
from PySide6.QtWidgets import QVBoxLayout
from PySide6.QtCharts import QChartView
from PySide6.QtGui import QPainter
from bleak import BleakScanner
import time
import numpy as np
from Model import Model
from Controller import Controller
from ChartUtils import ChartUtils
import vars

class View(QChartView):

    def __init__(self, parent=None):
        super().__init__(parent)

        self.model = Model()
        self.controls_widget = Controller()
        self.model.sensorConnected.connect(self.sensorConnectedHandler)
        self.controls_widget.beatCountingFinished.connect(self.beatCountingFinishedHandler)
        self.controls_widget.beatEntered.connect(self.beatEnteredHandler)
        self.model.beat_tracker.accuracyCalcuated.connect(self.accuracyCalculatedHandler)

        self.configureStylesheet()
        self.configureCharts()
        self.configureLayout()
        self.configureSeriesTimer()

    def configureStylesheet(self):
        # Load the stylesheet from the file
        style_file = QFile("style.qss")
        style_file.open(QFile.ReadOnly | QFile.Text)
        stylesheet = style_file.readAll()
        stylesheet = str(stylesheet, encoding="utf-8")
        self.setStyleSheet(stylesheet)

    def configureCharts(self):
        self.chart_acc = ChartUtils.create_chart(title='ECG', showTitle=False, showLegend=False)
        self.series_breath_acc = ChartUtils.create_line_series(vars.RED, vars.LINEWIDTH)
        self.axis_acc_x = ChartUtils.create_axis(title=None, tickCount=10, rangeMin=-vars.ECG_TIME_RANGE, rangeMax=0, labelSize=10, flip=False)
        self.axis_y_breath_acc = ChartUtils.create_axis("ECG (mV)", vars.RED, rangeMin=-500, rangeMax=1600, labelSize=10)

        self.chart_acc.addSeries(self.series_breath_acc)
        self.chart_acc.addAxis(self.axis_acc_x, Qt.AlignBottom)
        self.chart_acc.addAxis(self.axis_y_breath_acc, Qt.AlignRight)
        self.series_breath_acc.attachAxis(self.axis_acc_x)
        self.series_breath_acc.attachAxis(self.axis_y_breath_acc)
        
    def configureLayout(self):
        layout = QVBoxLayout()

        acc_widget = QChartView(self.chart_acc)
        acc_widget.setStyleSheet("background-color: transparent;")
        acc_widget.setRenderHint(QPainter.Antialiasing)
        
        layout.addWidget(acc_widget, stretch=3)
        layout.addWidget(self.controls_widget, stretch=1)
        layout.setContentsMargins(0, 0, 0, 0)
        self.setLayout(layout)

    def configureSeriesTimer(self):
        self.update_ecg_series_timer = QTimer()
        self.update_ecg_series_timer.timeout.connect(self.update_ecg_series)
        self.update_ecg_series_timer.setInterval(vars.UPDATE_ECG_SERIES_PERIOD)
        self.update_ecg_series_timer.start()

    @Slot()
    def sensorConnectedHandler(self):
        self.controls_widget.setStateReadyAfterDelay()

    @Slot(float, float)
    def beatCountingFinishedHandler(self, start_time, end_time):
        self.model.beat_tracker.get_beat_count_from_wind(start_time, end_time)

    @Slot(int)
    def beatEnteredHandler(self, beat_count_entered):
        self.model.beat_tracker.get_accuracy_score(beat_count_entered)

    @Slot(float)
    def accuracyCalculatedHandler(self, accuracy):
        print(f"Accuracy: {accuracy:.3f}")
    

    async def connect_polar(self):

        polar_device_found = False
        print("Looking for Polar device...")
        while not polar_device_found:

            devices = await BleakScanner.discover()
            print(f"Found {len(devices)} BLE devices")
            for device in devices:
                if device.name is not None and "Polar" in device.name:
                    polar_device_found = True
                    print(f"Found Polar device")
                    break
            if not polar_device_found:
                print("Polar device not found, retrying in 1 second")
                await asyncio.sleep(1)
        
        self.model.set_polar_sensor(device)
        await self.model.connect_sensor()

    async def disconnect_polar(self):
        await self.model.disconnect_sensor()

    def update_ecg_series(self):
            
        self.ecg_times_rel_s = self.model.beat_tracker.ecg_times - time.time_ns()/1.0e9
        series_breath_acc_new = []

        for i, value in enumerate(self.ecg_times_rel_s):
            if not np.isnan(value):
                series_breath_acc_new.append(QPointF(value, self.model.beat_tracker.ecg_hist[i]))
        self.series_breath_acc.replace(series_breath_acc_new)

    async def main(self):
        await self.connect_polar()
        await asyncio.gather(self.model.update_ecg())
    