
import asyncio
from PySide6.QtCore import QTimer, Qt, QPointF, QSize, QFile, QTime, Signal
from PySide6.QtWidgets import QVBoxLayout, QHBoxLayout, QSizePolicy, QWidget, QPushButton, QLabel, QSpinBox
from PySide6.QtCharts import QChart, QChartView, QLineSeries, QValueAxis, QScatterSeries, QSplineSeries
from PySide6.QtGui import QPen, QColor, QPainter, QFont
from bleak import BleakScanner
import time
import numpy as np
from Model import Model
from enum import Enum

class SquareWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        
    def sizeHint(self):
        return QSize(100, 100)

    def resizeEvent(self, event):
        side = min(self.width(), self.height())
        if self.width() > self.height():
            self.setMaximumHeight(side)
            self.setMaximumWidth(side)
        else:
            self.setMaximumWidth(side)
            self.setMaximumHeight(side)

class CountdownTimer(QWidget):
    timerFinished = Signal()

    def __init__(self):
        super().__init__()

        self.initUI()

    def initUI(self):
        # Set up the main widget and layout
        layout = QVBoxLayout(self)

        # Create and configure the label to show the time
        self.time_label = QLabel("00:05")
        self.time_label.setStyleSheet("color: black;")
        self.time_label.setAlignment(Qt.AlignCenter)

        layout.addWidget(self.time_label)

        self.countdown_time = QTime(0, 0, 5)

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

class ControlState(Enum):
    INITIALISING = 1
    RECORDING_BEATS = 2
    RECORDING_INPUT = 3
    FINISHED = 4

class ControlWidget(QWidget):
    def __init__(self):
        super().__init__()

        self.countdown_timer = CountdownTimer()
        self.state = ControlState.INITIALISING

        self.initUI()

    def initUI(self):

        controls_layout = QVBoxLayout()
        self.setLayout(controls_layout)

        self.start_button = QPushButton("Start")
        self.start_button.setStyleSheet("background-color: white; color: black; border: 1px solid black;")
        self.start_button.setMaximumWidth(500)
        self.start_button.setMinimumWidth(100)
        self.start_button.setMinimumHeight(30)
        controls_layout.addWidget(self.start_button, alignment=Qt.AlignCenter)

        self.message_box = QLabel()
        self.message_box.setStyleSheet("background-color: white; color: black;")
        self.message_box.setText("Press start and begin heart beat counting")
        self.message_box.setMaximumWidth(800)
        self.message_box.setMinimumWidth(500)
        self.message_box.setMinimumHeight(30)
        self.message_box.setAlignment(Qt.AlignCenter)
        controls_layout.addWidget(self.message_box, alignment=Qt.AlignCenter)

        self.spin_box = QSpinBox()
        self.spin_box.setStyleSheet("background-color: white; color: black; border: 1px solid black;")
        self.spin_box.setRange(0, 100)
        self.spin_box.setSingleStep(1)
        self.spin_box.setValue(0)
        self.spin_box.setMaximumWidth(200)
        self.spin_box.setMinimumWidth(100)
        self.spin_box.setMinimumHeight(30)
        self.spin_box.setAlignment(Qt.AlignCenter)
        controls_layout.addWidget(self.spin_box, alignment=Qt.AlignCenter)
        self.spin_box.hide()

        self.timer_widget = CountdownTimer()
        self.timer_widget.timerFinished.connect(self.countdownFinished)
        self.start_button.clicked.connect(self.buttonPressed)
        controls_layout.addWidget(self.timer_widget)

    def buttonPressed(self):
        if self.state == ControlState.INITIALISING:
            self.timer_widget.startTimer()
            self.state = ControlState.RECORDING_BEATS
            self.message_box.setText("Count your heart beats")
            self.message_box.setStyleSheet("background-color: red; color: white;")
            self.spin_box.hide()
        elif self.state == ControlState.RECORDING_BEATS:
            pass
        elif self.state == ControlState.RECORDING_INPUT:
            self.state = ControlState.FINISHED
            # TODO: Save the value of the spin box
            self.message_box.setText("Finished")
            self.message_box.setStyleSheet("background-color: green; color: white;")
            self.start_button.hide()
            self.spin_box.hide()
        else:
            pass

    def countdownFinished(self):
        self.state = ControlState.RECORDING_INPUT        
        self.spin_box.show()
        self.message_box.setText("Enter how many heart beats you counted")
        self.message_box.setStyleSheet("background-color: green; color: white;")
        self.start_button.setText("Submit")

    

class View(QChartView):
    
    def __init__(self, parent=None):
        super().__init__(parent)

        self.model = Model()

        # Load the stylesheet from the file
        style_file = QFile("style.qss")
        style_file.open(QFile.ReadOnly | QFile.Text)
        stylesheet = style_file.readAll()
        stylesheet = str(stylesheet, encoding="utf-8")

        # Set the stylesheet
        self.setStyleSheet(stylesheet)

        # Plot parameters
        self.RED = QColor(200, 30, 45)
        self.YELLOW = QColor(254, 191, 0)
        self.ORANGE = QColor(255, 130, 0)
        self.GREEN = QColor(50, 177, 108)
        self.BLUE = QColor(0, 119, 190)
        self.GRAY = QColor(34, 34, 34)
        self.GOLD = QColor(212, 175, 55)
        self.LINEWIDTH = 2.5
        self.DOTSIZE_SMALL = 4
        self.DOTSIZE_LARGE = 5

        # Series parameters
        self.UPDATE_BREATHING_SERIES_PERIOD = 50 # ms
        self.BREATH_ACC_TIME_RANGE = 20 # s

        # Breathing acceleration
        self.chart_acc = self.create_chart(title='ECG', showTitle=False, showLegend=False)
        self.series_breath_acc = self.create_line_series(self.RED, self.LINEWIDTH)
        self.axis_acc_x = self.create_axis(title=None, tickCount=10, rangeMin=-self.BREATH_ACC_TIME_RANGE, rangeMax=0, labelSize=10, flip=False)
        self.axis_y_breath_acc = self.create_axis("ECG (mV)", self.RED, rangeMin=-500, rangeMax=1600, labelSize=10)

        # Configure
        self.chart_acc.addSeries(self.series_breath_acc)
        self.chart_acc.addAxis(self.axis_acc_x, Qt.AlignBottom)
        self.chart_acc.addAxis(self.axis_y_breath_acc, Qt.AlignRight)
        self.series_breath_acc.attachAxis(self.axis_acc_x)
        self.series_breath_acc.attachAxis(self.axis_y_breath_acc)
        
        # Create a layout
        layout = QVBoxLayout()

        acc_widget = QChartView(self.chart_acc)
        acc_widget.setStyleSheet("background-color: transparent;")
        acc_widget.setRenderHint(QPainter.Antialiasing)

        controls_widget = ControlWidget()
        
        layout.addWidget(acc_widget, stretch=3)
        layout.addWidget(controls_widget, stretch=1)
        layout.setContentsMargins(0, 0, 0, 0)
        self.setLayout(layout)

        self.update_acc_series_timer = QTimer()
        self.update_acc_series_timer.timeout.connect(self.update_acc_series)
        self.update_acc_series_timer.setInterval(self.UPDATE_BREATHING_SERIES_PERIOD)
        self.update_acc_series_timer.start()
        
    def create_chart(self, title=None, showTitle=False, showLegend=False, margins=None):
        chart = QChart()
        chart.legend().setVisible(showLegend)
        chart.setTitle(title)
        if margins:
            chart.setMargins(margins)
            chart.layout().setContentsMargins(margins)
        return chart
    
    def create_scatter_series(self, color=None, size=5):
        if color is None:
            color = self.GRAY
        series = QScatterSeries()
        series.setMarkerSize(size)
        series.setMarkerShape(QScatterSeries.MarkerShapeCircle)
        series.setColor(color)
        series.setBorderColor(color)
        return series

    def create_line_series(self, color=None, width=2, style=None):
        if color is None:
            color = self.GRAY
        series = QLineSeries()
        pen = QPen(color)
        pen.setWidth(width)
        if style:
            pen.setStyle(style)
        series.setPen(pen)
        return series

    def create_spline_series(self, color=None, width=2):
        if color is None:
            color = self.GRAY
        series = QSplineSeries()
        pen = QPen(color)
        pen.setWidth(width)
        series.setPen(pen)
        return series

    def create_axis(self, title=None, color=None, tickCount=None, rangeMin=None, rangeMax=None, labelSize=None, flip=False):
        if color is None:
            color = self.GRAY
        axis = QValueAxis()
        axis.setTitleText(title)
        axis.setLabelsColor(color)
        axis.setTitleBrush(color)
        axis.setGridLineVisible(False)
        if tickCount:
            axis.setTickCount(tickCount)
        if rangeMin:
            axis.setMin(rangeMin)
        if rangeMax:
            axis.setMax(rangeMax)
        if labelSize:
            font = QFont()
            font.setPointSize(labelSize)
            axis.setLabelsFont(font)
        if flip:
            axis.setReverse(True)
        return axis        

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

    def update_acc_series(self):
            
        self.breath_acc_times_rel_s = self.model.breath_acc_times - time.time_ns()/1.0e9
        series_breath_acc_new = []

        for i, value in enumerate(self.breath_acc_times_rel_s):
            if not np.isnan(value):
                series_breath_acc_new.append(QPointF(value, self.model.breath_acc_hist[i]))
        self.series_breath_acc.replace(series_breath_acc_new)

    async def main(self):
        await self.connect_polar()
        await asyncio.gather(self.model.update_acc())
    