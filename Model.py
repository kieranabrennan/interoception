import asyncio
from PolarH10 import PolarH10
from BeatTracker import BeatTracker
from PySide6.QtCore import QObject, Signal
from bleak import BleakScanner
from datetime import datetime
import json
import os

import matplotlib
matplotlib.use('Qt5Agg')
import matplotlib.pyplot as plt

class Model(QObject):
    sensorConnected = Signal()

    def __init__(self):
        super().__init__()
        self.polar_sensor = None
        self.beat_tracker = BeatTracker()
        self.session_data = SessionData()

    def set_polar_sensor(self, device):
        self.polar_sensor = PolarH10(device)

    async def connect_sensor(self):
        await self.polar_sensor.connect()
        await self.polar_sensor.get_device_info()
        await self.polar_sensor.print_device_info()
        self.sensorConnected.emit()
        
    async def disconnect_sensor(self):
        await self.polar_sensor.disconnect()

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
        
        self.set_polar_sensor(device)
        await self.connect_sensor()

    async def disconnect_polar(self):
        await self.disconnect_sensor()

    async def update_ecg(self): 
        await self.polar_sensor.start_ecg_stream()
        
        while True:
            await asyncio.sleep(0.005)
            while not self.polar_sensor.ecg_queue_is_empty():
                self.beat_tracker.update_ecg_history(*self.polar_sensor.dequeue_ecg())

    def calculateTrialResults(self, trial_length, start_time, end_time, count_entered, confidence):
        count_measured = self.beat_tracker.get_beat_count_from_wind(start_time, end_time)
        accuracy = 1 - abs(count_measured - count_entered)/(0.5*(count_measured + count_entered))
        
        trial_data = {"trial_length": int(trial_length), "count_measured": int(count_measured), \
                      "count_entered": int(count_entered), "accuracy": float(accuracy), "confidence": float(confidence)}
        self.session_data.append(trial_data)

    def viewResults(self):
        self.session_data.plotMeasuredAgainstEstimated()
        self.session_data.plotAccuracyAgainstConfidence()
        self.session_data.saveSessionData()
        

class SessionData:

    def __init__(self):
        self.trials = []

        data_folder = "data"
        if not os.path.exists(data_folder):
            os.makedirs(data_folder)
        timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
        filename = f"session_data_{timestamp}.json"
        self.session_filepath = os.path.join(data_folder, filename)

    def append(self, trial_data):
        self.trials.append(trial_data)

    def plotMeasuredAgainstEstimated(self):
        plt.figure()
        plt.plot([trial["count_measured"] for trial in self.trials], [trial["count_entered"] for trial in self.trials], "o")
        plt.xlabel('Measured beat count')
        plt.ylabel('Estimated beat count')
        plt.title('Estimated vs Measured Beats')
        plt.legend(["Measured", "Estimated"])
        plt.xlim([0, 70])
        plt.ylim([0, 70])
        plt.show()

    def plotAccuracyAgainstConfidence(self):
        plt.figure()
        plt.plot([trial["accuracy"] for trial in self.trials], [trial["confidence"] for trial in self.trials], "o")
        plt.xlabel('Accuracy')
        plt.ylabel('Confidence')
        plt.title('Accuracy vs Confidence')
        plt.legend(["Accuracy", "Confidence"])
        plt.xlim([0, 1])
        plt.ylim([0, 1])
        plt.show()

    def saveSessionData(self):

        print(f"Saving data:\nself.trials: {self.trials}")
        with open(self.session_filepath, "w") as file:
            json.dump(self.trials, file, indent=4)

        print(f"Data saved to {self.session_filepath}")
    

    
