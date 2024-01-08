
from PySide6.QtCore import Qt, QPointF, QFile
from PySide6.QtWidgets import QVBoxLayout, QHBoxLayout, QLabel, QSpinBox, QPushButton, QWidget, QSlider, QSizePolicy, QStackedWidget, QSpacerItem 
from PySide6.QtCharts import QChartView
from PySide6.QtGui import QPainter, QColor
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
        style_file = QFile("style.qss")
        style_file.open(QFile.ReadOnly | QFile.Text)
        stylesheet = style_file.readAll()
        stylesheet = str(stylesheet, encoding="utf-8")
        self.setStyleSheet(stylesheet)

    def configureCharts(self):
        self.chart_ecg = ChartUtils.create_chart(title='', showTitle=False, showLegend=False)
        self.series_breath_acc = ChartUtils.create_line_series(QColor(*vars.RED), vars.LINEWIDTH)
        self.axis_x = ChartUtils.create_axis(title=None, tickCount=10, rangeMin=-vars.ECG_TIME_RANGE, rangeMax=0, labelSize=10, flip=False, labelsVisible=False, axisVisible=False)
        self.axis_y = ChartUtils.create_axis("", QColor(*vars.RED), rangeMin=-500, rangeMax=1600, labelSize=10, labelsVisible=False, axisVisible=False)

        self.chart_ecg.addSeries(self.series_breath_acc)
        self.chart_ecg.addAxis(self.axis_x, Qt.AlignBottom)
        self.chart_ecg.addAxis(self.axis_y, Qt.AlignRight)
        self.series_breath_acc.attachAxis(self.axis_x)
        self.series_breath_acc.attachAxis(self.axis_y)
        
    def configureLayout(self):
        layout = QVBoxLayout()

        ecg_widget = QChartView(self.chart_ecg)
        ecg_widget.setStyleSheet("background-color: transparent;")
        ecg_widget.setRenderHint(QPainter.Antialiasing)
        
        layout.addWidget(ecg_widget, stretch=1)
        layout.addWidget(self.controls_widget, stretch=3)
        layout.setContentsMargins(0, 0, 0, 0)
        self.setLayout(layout)
        self.chart_ecg.setVisible(True)

    def control_session_intro(self, trials_per_session):
        self.chart_ecg.setVisible(True)
        self.controls_widget.message_box.setText(f"There will be {trials_per_session} sessions\nDuring each you will count your heart beats without taking your pulse\nAt the end you will enter the number you counted\n and the confidence in your estimate")
        self.controls_widget.message_box.setStyleSheet(f"background-color: rgb({vars.GREEN[0]}, {vars.GREEN[1]}, {vars.GREEN[2]}); color: black;")
        self.controls_widget.start_button.setText("Continue")
        self.controls_widget.start_button.setStyleSheet("background-color: white; color: black; border: 1px solid black;")

    def control_ready_to_start(self, trial_no, trials_per_session):
        self.chart_ecg.setVisible(True)
        self.controls_widget.message_box.setText(f"Ready to start trial {trial_no} of {trials_per_session}\nBegin counting your heartbeats as soon as you press start")
        self.controls_widget.message_box.setStyleSheet(f"background-color: rgb({vars.GREEN[0]}, {vars.GREEN[1]}, {vars.GREEN[2]}); color: black;")
        self.controls_widget.start_button.setText("Start")
        self.controls_widget.start_button.setStyleSheet("background-color: white; color: black; border: 1px solid black;")
        self.controls_widget.beat_count_input.setValue(0)
        self.controls_widget.setInputWidgetState("blank")
    
    def control_recording_beats(self):
        self.chart_ecg.setVisible(False)
        self.controls_widget.message_box.setText("Count your heart beats\nWithout checking your pulse")
        self.controls_widget.message_box.setStyleSheet(f"background-color: rgb({vars.RED[0]}, {vars.RED[1]}, {vars.RED[2]}); color: white;")
        self.controls_widget.beat_count_input.setStyleSheet("background-color: white; color: grey; border: 1px solid grey;")
        self.controls_widget.start_button.setStyleSheet("background-color: white; color: white; border: 1px solid white;")
        self.controls_widget.setInputWidgetState("blank")

    def control_recording_input(self):
        self.chart_ecg.setVisible(True)
        self.controls_widget.beat_count_input.setStyleSheet("background-color: white; color: black; border: 1px solid black;")
        self.controls_widget.message_box.setText("Enter how many heart beats you counted")
        self.controls_widget.message_box.setStyleSheet(f"background-color: rgb({vars.GREEN[0]}, {vars.GREEN[1]}, {vars.GREEN[2]}); color: white;")
        self.controls_widget.start_button.setText("Submit")
        self.controls_widget.start_button.setStyleSheet("background-color: white; color: black; border: 1px solid black;")
        self.controls_widget.setInputWidgetState("beat_count_input")

    def control_recording_confidence(self):
        self.chart_ecg.setVisible(True)
        self.controls_widget.message_box.setText("Select how confident you are in your beat count on the scale")
        self.controls_widget.message_box.setStyleSheet(f"background-color: rgb({vars.YELLOW[0]}, {vars.YELLOW[1]}, {vars.YELLOW[2]}); color: black;")
        self.controls_widget.start_button.setText("Submit")
        self.controls_widget.start_button.setStyleSheet("background-color: white; color: black; border: 1px solid black;")
        self.controls_widget.beat_count_input.setStyleSheet("background-color: white; color: grey; border: 1px solid grey;")
        self.controls_widget.setInputWidgetState("confidence_scale")

    def control_results(self, accuracy_score, accuracy_percentile, awareness_score, awareness_percentile):
        self.chart_ecg.setVisible(True)
        self.controls_widget.message_box.setText(f"Your average accuracy was: {accuracy_score:.2f} ({accuracy_percentile:.0f}th percentile)\nYour awareness score is: {awareness_score:.2f} ({awareness_percentile:.0f}th percentile)")
        self.controls_widget.message_box.setStyleSheet(f"background-color: rgb({vars.GREEN[0]}, {vars.GREEN[1]}, {vars.GREEN[2]}); color: black;")
        self.controls_widget.start_button.setText("Start again")
        self.controls_widget.start_button.setStyleSheet("background-color: white; color: black; border: 1px solid black;")
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
        controls_layout.addWidget(self.input_widget, alignment=Qt.AlignCenter)
        controls_layout.addWidget(self.start_button, alignment=Qt.AlignCenter)
        controls_layout.addItem(QSpacerItem(0, 40, QSizePolicy.Minimum, QSizePolicy.Fixed))

    def configureMessageBox(self):
        self.message_box = QLabel()
        self.message_box.setStyleSheet(f"background-color: rgb({vars.YELLOW[0]}, {vars.YELLOW[1]}, {vars.YELLOW[2]}); color: black;")
        self.message_box.setText("Scanning for Polar H10 Heart rate monitors...")
        self.message_box.setMaximumWidth(800)
        self.message_box.setMinimumWidth(500)
        self.message_box.setMinimumHeight(120)
        self.message_box.setAlignment(Qt.AlignCenter)
        
    def configureStartButton(self):
        self.start_button = QPushButton("Continue")
        self.start_button.setStyleSheet("background-color: white; color: white; border: 1px solid white;")
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

    def value(self):
        return self.slider.value()