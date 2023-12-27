
from PySide6.QtCore import QTimer, Qt, QPointF, QFile
from PySide6.QtWidgets import QVBoxLayout, QHBoxLayout, QLabel, QSpinBox, QPushButton, QWidget
from PySide6.QtCharts import QChartView
from PySide6.QtGui import QPainter
import time
import numpy as np
from ChartUtils import ChartUtils
import vars

class ControlsWidget(QWidget):

    def __init__(self):
        super().__init__()
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
    
class View(QChartView):

    def __init__(self, parent=None):
        super().__init__(parent)

        self.controls_widget = ControlsWidget()

        # Anything with .model. needs to go to Controller
        self.configureStylesheet()
        self.configureCharts()
        self.configureLayout()

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

    def control_ready_to_start(self):
        self.controls_widget.message_box.setText("Press start and begin heart beat counting")
        self.controls_widget.message_box.setStyleSheet("background-color: green; color: black;")
        self.controls_widget.start_button.setText("Start")
        self.controls_widget.start_button.setStyleSheet("background-color: white; color: black; border: 1px solid black;")
        self.controls_widget.spin_box.setValue(0)
    
    def control_recording_beats(self):
        self.controls_widget.message_box.setText("Count your heart beats\nWithout checking your pulse")
        self.controls_widget.message_box.setStyleSheet("background-color: red; color: white;")
        self.controls_widget.spin_box.setEnabled(False)
        self.controls_widget.spin_box.setStyleSheet("background-color: white; color: grey; border: 1px solid grey;")

    def control_recording_input(self):
        self.controls_widget.spin_box.setEnabled(True)
        self.controls_widget.spin_box.setStyleSheet("background-color: white; color: black; border: 1px solid black;")
        self.controls_widget.message_box.setText("Enter how many heart beats you counted")
        self.controls_widget.message_box.setStyleSheet("background-color: green; color: white;")
        self.controls_widget.start_button.setText("Submit")

    def control_finished(self):
        self.controls_widget.message_box.setText("Finished")
        self.controls_widget.message_box.setStyleSheet("background-color: green; color: white;")
        self.controls_widget.start_button.setText("Restart")
        self.controls_widget.start_button.setStyleSheet("background-color: white; color: black; border: 1px solid black;")
        self.controls_widget.spin_box.setEnabled(False)
        self.controls_widget.spin_box.setStyleSheet("background-color: white; color: grey; border: 1px solid grey;")

    def update_ecg_series(self, ecg_times_rel_s, ecg_hist):
        series_breath_acc_new = []
        for i, value in enumerate(ecg_times_rel_s):
            if not np.isnan(value):
                series_breath_acc_new.append(QPointF(value, ecg_hist[i]))
        self.series_breath_acc.replace(series_breath_acc_new)

