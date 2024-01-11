
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

        # self.configureStylesheet()
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
        self.series_ecg = ChartUtils.create_line_series(QColor(*vars.RED), vars.LINEWIDTH)
        self.axis_x = ChartUtils.create_axis(title=None, tickCount=10, rangeMin=-vars.ECG_TIME_RANGE, rangeMax=0, labelSize=10, flip=False, labelsVisible=False, axisVisible=False)
        self.axis_y = ChartUtils.create_axis("", QColor(*vars.RED), rangeMin=-500, rangeMax=1600, labelSize=10, labelsVisible=False, axisVisible=False)

        self.chart_ecg.addSeries(self.series_ecg)
        self.chart_ecg.addAxis(self.axis_x, Qt.AlignBottom)
        self.chart_ecg.addAxis(self.axis_y, Qt.AlignRight)
        self.series_ecg.attachAxis(self.axis_x)
        self.series_ecg.attachAxis(self.axis_y)
        
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

    def control_session_intro(self, trial_lengths_s):
        self.chart_ecg.setVisible(True)
        self.controls_widget.message_box.setText(f"There will be {len(trial_lengths_s)} sessions of random lengths between {min(trial_lengths_s)} s and {max(trial_lengths_s)} s\n\n"
                                                 "During each you will count your heart beats (without taking your pulse)\n\n"
                                                 "At the end, enter the total count and the confidence in your estimate")
        self.controls_widget.message_box.updateColour("green")
        self.controls_widget.start_button.setText("Continue")
        self.controls_widget.start_button.setStyleSheet("background-color: white; color: black; border: 1px solid black;")

    def control_ready_to_start(self, trial_no, trials_per_session):
        self.chart_ecg.setVisible(True)
        self.controls_widget.message_box.setText(f"Ready to start trial {trial_no} of {trials_per_session}\n\nBegin counting your heartbeats as soon as you press start")
        self.controls_widget.message_box.updateColour("green")
        self.controls_widget.start_button.setText("Start")
        self.controls_widget.start_button.setStyleSheet("background-color: white; color: black; border: 1px solid black;")
        self.controls_widget.beat_count_input.setValue(0)
        self.controls_widget.setInputWidgetState("blank")
    
    def control_recording_beats(self):
        self.chart_ecg.setVisible(False)
        self.controls_widget.message_box.setText("Count your heart beats\nWithout checking your pulse")
        self.controls_widget.message_box.updateColour("red")
        self.controls_widget.beat_count_input.setStyleSheet("background-color: white; color: grey; border: 1px solid grey;")
        self.controls_widget.start_button.setStyleSheet("background-color: white; color: white; border: 1px solid white;")
        self.controls_widget.setInputWidgetState("blank")

    def control_recording_input(self):
        self.chart_ecg.setVisible(True)
        self.controls_widget.beat_count_input.setStyleSheet("background-color: white; color: black; border: 1px solid black;")
        self.controls_widget.message_box.setText("Enter the number of heart beats you counted")
        self.controls_widget.message_box.updateColour("green")
        self.controls_widget.start_button.setText("Submit")
        self.controls_widget.start_button.setStyleSheet("background-color: white; color: black; border: 1px solid black;")
        self.controls_widget.setInputWidgetState("beat_count_input")

    def control_recording_confidence(self):
        self.chart_ecg.setVisible(True)
        self.controls_widget.message_box.setText("On the scale below indicate how confident you are in your heartbeat count")
        self.controls_widget.message_box.updateColour("yellow")
        self.controls_widget.start_button.setText("Submit")
        self.controls_widget.start_button.setStyleSheet("background-color: white; color: black; border: 1px solid black;")
        self.controls_widget.beat_count_input.setStyleSheet("background-color: white; color: grey; border: 1px solid grey;")
        self.controls_widget.setInputWidgetState("confidence_scale")

    def control_results(self, accuracy_score, accuracy_percentile, awareness_score, awareness_percentile, awareness_p_value):
        self.chart_ecg.setVisible(True)
        self.controls_widget.message_box.setText(f"Your average accuracy was: {accuracy_score:.2f}.\nYour accuracy is in the {ordinal_suffix(np.round(accuracy_percentile,0) if not np.isnan(accuracy_percentile) else np.nan)} percentile.\n\n" \
                                                 f"Your awareness score is: {awareness_score:.2f} (p-value = {awareness_p_value:.2f}).\nYour score is in the {ordinal_suffix(np.round(awareness_percentile,0) if not np.isnan(awareness_percentile) else np.nan)} percentile")
        self.controls_widget.message_box.updateColour("green")
        self.controls_widget.start_button.setText("Start again")
        self.controls_widget.start_button.setStyleSheet("background-color: white; color: black; border: 1px solid black;")
        self.controls_widget.setInputWidgetState("blank")
        pass

    def update_ecg_series(self, ecg_times_rel_s, ecg_hist):
        series_ecg_new = []
        for i, value in enumerate(ecg_times_rel_s):
            if not np.isnan(value):
                series_ecg_new.append(QPointF(value, ecg_hist[i]))
        self.series_ecg.replace(series_ecg_new)

class MessageBox(QLabel):

    def __init__(self):
        super().__init__()
        self.initUI()

    def initUI(self):
        self.base_style = "border-radius: 10px; color: black;"
        self.setStyleSheet(self.base_style)
        self.updateColour("yellow")
        self.setText("Scanning for Polar H10 Heart rate monitors...")
        self.setMaximumWidth(800)
        self.setMinimumWidth(500)
        self.setMinimumHeight(120)
        self.setAlignment(Qt.AlignCenter)

    def updateColour(self, colour_selection):
        colours = {
            "red": vars.RED,
            "yellow": vars.YELLOW,
            "orange": vars.ORANGE,
            "green": vars.GREEN,
            "blue": vars.BLUE,
            "gray": vars.GRAY,
            "gold": vars.GOLD
        }
        colour_rgb = colours[colour_selection]

        self.setStyleSheet(f"background-color: rgba({colour_rgb[0]}, {colour_rgb[1]}, {colour_rgb[2]}, {128}); {self.base_style}")


class ControlsWidget(QWidget):

    def __init__(self):
        super().__init__()
        self.initUI()

    def initUI(self):

        self.message_box = MessageBox()
        self.configureStartButton()
        self.configureInputWidget()

        controls_layout = QVBoxLayout()
        self.setLayout(controls_layout)
        controls_layout.addWidget(self.message_box, alignment=Qt.AlignCenter)
        controls_layout.addWidget(self.input_widget, alignment=Qt.AlignCenter)
        controls_layout.addWidget(self.start_button, alignment=Qt.AlignCenter)
        controls_layout.addItem(QSpacerItem(0, 40, QSizePolicy.Minimum, QSizePolicy.Fixed))
        
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
        min_label.setFixedWidth(150)  # Set a fixed width
        min_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        
        # Create the slider
        self.slider = QSlider(Qt.Horizontal)
        self.slider.setMinimum(0)
        self.slider.setMaximum(10)
        self.slider.setValue(5)
        self.slider.setTickInterval(0.1)
        self.slider.setFixedWidth(200)  # Set a fixed width
        self.slider.setStyleSheet("background-color: white; color: black;")
        self.slider.setStyleSheet("""
            QSlider::groove:horizontal {
                height: 10px;  /* Custom height of the slider track */
                background-color: lightgray;
                margin: 0 10px;  /* Margins for the ends of the slider */
            }

            QSlider::handle:horizontal {
                background-color: black;
                width: 2px;  /* Narrow width for the handle */
                margin: -5px 0;  /* Expand outside the groove */
                border-radius: 1px;
            }
        """)
        
        # Right label (maximum value)
        max_label = QLabel("Complete confidence")
        max_label.setStyleSheet("background-color: white; color: black;")
        max_label.setFixedWidth(150)  # Set a fixed width
        max_label.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)

        slider_layout.addWidget(min_label)
        slider_layout.addStretch()
        slider_layout.addWidget(self.slider)
        slider_layout.addStretch()
        slider_layout.addWidget(max_label)

    def value(self):
        return self.slider.value()
    

def ordinal_suffix(value):
    # Special case for 11th to 13th
    if 10 <= value % 100 <= 13:
        suffix = 'th'
    else:
        # Determine the suffix based on the last digit
        suffixes = {1: 'st', 2: 'nd', 3: 'rd'}
        suffix = suffixes.get(value % 10, 'th')
    return f"{value}{suffix}"