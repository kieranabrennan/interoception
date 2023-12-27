
from PySide6.QtCore import Qt, QPointF, QFile
from PySide6.QtWidgets import QVBoxLayout, QHBoxLayout, QLabel, QSpinBox, QPushButton, QWidget, QSlider, QSizePolicy, QStackedWidget, QSpacerItem 
from PySide6.QtCharts import QChartView
from PySide6.QtGui import QPainter
import numpy as np
from ChartUtils import ChartUtils
import vars

class View(QChartView):

    def __init__(self, parent=None):
        super().__init__(parent)

        self.controls_widget = ControlsWidget()

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
        self.controls_widget.beat_count_input.setValue(0)
        self.controls_widget.setInputWidgetState("blank")
    
    def control_recording_beats(self):
        self.controls_widget.message_box.setText("Count your heart beats\nWithout checking your pulse")
        self.controls_widget.message_box.setStyleSheet("background-color: red; color: white;")
        self.controls_widget.beat_count_input.setStyleSheet("background-color: white; color: grey; border: 1px solid grey;")
        self.controls_widget.setInputWidgetState("blank")

    def control_recording_input(self):
        self.controls_widget.beat_count_input.setStyleSheet("background-color: white; color: black; border: 1px solid black;")
        self.controls_widget.message_box.setText("Enter how many heart beats you counted")
        self.controls_widget.message_box.setStyleSheet("background-color: green; color: white;")
        self.controls_widget.start_button.setText("Submit")
        self.controls_widget.setInputWidgetState("beat_count_input")

    def control_recording_confidence(self):
        self.controls_widget.message_box.setText("Select how confident you are in your beat count on the scale")
        self.controls_widget.message_box.setStyleSheet("background-color: yellow; color: black;")
        self.controls_widget.start_button.setText("Submit")
        self.controls_widget.start_button.setStyleSheet("background-color: white; color: black; border: 1px solid black;")
        self.controls_widget.beat_count_input.setStyleSheet("background-color: white; color: grey; border: 1px solid grey;")
        self.controls_widget.setInputWidgetState("confidence_scale")

    def control_finished(self):
        self.controls_widget.setInputWidgetState("blank")
        pass

    def update_ecg_series(self, ecg_times_rel_s, ecg_hist):
        series_breath_acc_new = []
        for i, value in enumerate(ecg_times_rel_s):
            if not np.isnan(value):
                series_breath_acc_new.append(QPointF(value, ecg_hist[i]))
        self.series_breath_acc.replace(series_breath_acc_new)

class ControlsWidget(QWidget):

    def __init__(self):
        super().__init__()
        self.initUI()

    def initUI(self):

        self.configureMessageBox()
        self.configureStartButton()
        self.configureInputWidget()

        controls_layout = QVBoxLayout()
        self.setLayout(controls_layout)
        controls_layout.addWidget(self.message_box, alignment=Qt.AlignCenter)
        controls_layout.addWidget(self.start_button, alignment=Qt.AlignCenter)
        controls_layout.addWidget(self.input_widget, alignment=Qt.AlignCenter)

    def configureMessageBox(self):
        self.message_box = QLabel()
        self.message_box.setStyleSheet("background-color: yellow; color: black;")
        self.message_box.setText("Connecting to sensor...")
        self.message_box.setMaximumWidth(800)
        self.message_box.setMinimumWidth(500)
        self.message_box.setMinimumHeight(60)
        self.message_box.setAlignment(Qt.AlignCenter)
        
    def configureStartButton(self):
        self.start_button = QPushButton("Start")
        self.start_button.setStyleSheet("background-color: white; color: grey; border: 1px solid grey;")
        self.start_button.setMaximumWidth(500)
        self.start_button.setMinimumWidth(100)
        self.start_button.setMinimumHeight(30)
    
    def setInputWidgetState(self, state):
        if state == "blank":
            self.input_widget.setCurrentWidget(self.blank_widget)
        elif state == "beat_count_input":
            self.input_widget.setCurrentWidget(self.beat_count_input)
        elif state == "confidence_scale":
            self.input_widget.setCurrentWidget(self.confidence_scale)

    def configureInputWidget(self):
        self.beat_count_input = BeatCountInput()
        self.confidence_scale = ConfidenceScale()
        self.blank_widget = QWidget()
        self.input_widget = QStackedWidget()
        self.input_widget.addWidget(self.beat_count_input)
        self.input_widget.addWidget(self.confidence_scale)
        self.input_widget.addWidget(self.blank_widget)
        self.setInputWidgetState("blank")


class BeatCountInput(QWidget):

    def __init__(self):
        super().__init__()
        self.initUI()

    def initUI(self):
        beatCountLayout = QHBoxLayout()

        self.spin_box = QSpinBox()
        self.spin_box.setStyleSheet("background-color: white; color: grey; border: 1px solid grey;")
        self.spin_box.setRange(0, 100)
        self.spin_box.setSingleStep(1)
        self.spin_box.setValue(0)
        self.spin_box.setMaximumWidth(200)
        self.spin_box.setMinimumWidth(100)
        self.spin_box.setMinimumHeight(30)
        self.spin_box.setAlignment(Qt.AlignCenter)
        spacerLeft = QSpacerItem(40, 20, QSizePolicy.Expanding, QSizePolicy.Minimum)
        spacerRight = QSpacerItem(40, 20, QSizePolicy.Expanding, QSizePolicy.Minimum)

        beatCountLayout.addItem(spacerLeft)
        beatCountLayout.addWidget(self.spin_box)
        beatCountLayout.addItem(spacerRight)

        self.setLayout(beatCountLayout)

    def setValue(self, value):
        self.spin_box.setValue(value)

    def setStyleSheet(self, style):
        self.spin_box.setStyleSheet(style)

    def value(self):
        return self.spin_box.value()

class ConfidenceScale(QWidget):
    def __init__(self):
        super().__init__()
        self.initUI()

    def initUI(self):
        slider_layout = QHBoxLayout()
        self.setLayout(slider_layout)

        # Left label (minimum value)
        min_label = QLabel("Total guess")
        min_label.setStyleSheet("background-color: white; color: black;")
        min_label.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        min_label.setFixedWidth(200)  # Set a fixed width
        min_label.setAlignment(Qt.AlignRight)
        slider_layout.addWidget(min_label)

        # Create the slider
        self.slider = QSlider(Qt.Horizontal)
        self.slider.setMinimum(0)
        self.slider.setMaximum(10)
        self.slider.setValue(5)
        self.slider.setTickInterval(0.1)
        self.slider.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.slider.setStyleSheet("background-color: white; color: black;")
        slider_layout.addWidget(self.slider)

        # Right label (maximum value)
        max_label = QLabel("Complete confidence")
        max_label.setStyleSheet("background-color: white; color: black;")
        max_label.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        max_label.setFixedWidth(200)  # Set a fixed width
        max_label.setAlignment(Qt.AlignLeft)
        slider_layout.addWidget(max_label)
