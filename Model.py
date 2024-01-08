import asyncio
from PolarH10 import PolarH10
from BeatTracker import BeatTracker
from PySide6.QtCore import QObject, Signal
from bleak import BleakScanner
from datetime import datetime
import json
import os
import scipy.stats
import numpy as np
import pandas as pd
import vars

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
        self.reference_data = ReferenceData()

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

    def calculateSessionResults(self):
        return {"accuracy_score": self.session_data.calculateAverageAccuracy(), \
                "accuracy_percentile": self.reference_data.calculateAccuracyPercentile(self.session_data.calculateAverageAccuracy()), \
                "awareness_score": self.session_data.calculateAwareness(), \
                "awareness_percentile": self.reference_data.calculateAwarenessPercentile(self.session_data.calculateAwareness()) }

    def viewResults(self):
        
        self.session_data.plotSessionSummaryGraphs()
        self.session_data.saveSessionData()
        

class SessionData:

    def __init__(self):
        self.trials = []
        self.averageAccuracy = None

        data_folder = "data"
        if not os.path.exists(data_folder):
            os.makedirs(data_folder)
        timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
        filename = f"session_data_{timestamp}.json"
        self.session_filepath = os.path.join(data_folder, filename)

    def append(self, trial_data):
        self.trials.append(trial_data)

    def calculateAverageAccuracy(self):
        self.averageAccuracy = np.mean([trial["accuracy"] for trial in self.trials])
        return self.averageAccuracy

    def calculateAwareness(self):
        awareness, p_value = scipy.stats.pearsonr([trial["confidence"] for trial in self.trials], [trial["accuracy"] for trial in self.trials])
        return awareness
    
    def plotSessionSummaryGraphs(self):
        plt.figure(figsize=(10, 5))
        plt.subplot(1, 2, 1)
        plt.plot([trial["count_measured"] for trial in self.trials], [trial["count_entered"] for trial in self.trials], "o")
        plt.xlabel('Measured beat count')
        plt.ylabel('Estimated beat count')
        plt.title(f"Average accuracy: {np.mean([trial['accuracy'] for trial in self.trials]):.2f}")
        plt.xlim([0, 70])
        plt.ylim([0, 70])
        plt.subplot(1, 2, 2)
        plt.plot([trial["confidence"] for trial in self.trials], [trial["accuracy"] for trial in self.trials], "o")
        plt.xlabel('Confidence')
        plt.ylabel('Accuracy')
        plt.title(f"Awareness: {self.calculateAwareness():.2f}")
        plt.xlim([0, 10])
        plt.ylim([0, 1])
        plt.show()

    def saveSessionData(self):

        print(f"Saving data:\nself.trials: {self.trials}")
        with open(self.session_filepath, "w") as file:
            json.dump(self.trials, file, indent=4)

        print(f"Data saved to {self.session_filepath}")
    

class ReferenceData:

    def __init__(self):
        self.df_accuracy_awareness = None
        self.df_accuracy_confidence = None
        self.loadReferenceData()
        if vars.SHOW_DEBUG_GRAPHS:
            self.plotReferenceData()

    def calculateAccuracyPercentile(self, accuracy):
        return scipy.stats.percentileofscore(self.df_accuracy_awareness["accuracy"], accuracy)
    
    def calculateAwarenessPercentile(self, awareness):
        return scipy.stats.percentileofscore(self.df_accuracy_awareness["awareness"], awareness)

    def loadReferenceData(self):
        df_acc_aw_highacc =  pd.read_csv("reference/accuracy-awareness_high-acc.csv")
        df_acc_aw_lowacc =  pd.read_csv("reference/accuracy-awareness_low-acc.csv")
        df_acc_aw_highacc["group"] = "high-accuracy"
        df_acc_aw_lowacc["group"] = "low-accuracy"
        self.df_accuracy_awareness = pd.concat([df_acc_aw_highacc, df_acc_aw_lowacc])

        df_acc_con_highacc =  pd.read_csv("reference/accuracy-confidence_high-acc.csv")
        df_acc_con_lowacc =  pd.read_csv("reference/accuracy-confidence_low-acc.csv")
        df_acc_con_highacc["group"] = "high-accuracy"
        df_acc_con_lowacc["group"] = "low-accuracy"
        self.df_accuracy_confidence = pd.concat([df_acc_con_highacc, df_acc_con_lowacc])

        # print the first few lines of the dataframes
        print(f"df_accuracy_awareness:\n{self.df_accuracy_awareness.head()}")
        print(f"df_accuracy_confidence:\n{self.df_accuracy_confidence.head()}")
        print(self.df_accuracy_awareness.columns)


    def plotReferenceData(self):
        plt.figure(figsize=(10, 5))
        plt.subplot(2, 2, 1)
        # Histogram of accuracy coloured by group
        plt.hist([self.df_accuracy_awareness[self.df_accuracy_awareness["group"]=="high-accuracy"]["accuracy"], \
                  self.df_accuracy_awareness[self.df_accuracy_awareness["group"]=="low-accuracy"]["accuracy"]], \
                  bins=10, stacked=True, label=["high-accuracy", "low-accuracy"])
        plt.xlabel('Accuracy')
        plt.ylabel('Count')
        plt.title("Accuracy Awareness Data")

        plt.subplot(2, 2, 2)
        plt.hist([self.df_accuracy_confidence[self.df_accuracy_confidence["group"]=="high-accuracy"]["accuracy"], \
                  self.df_accuracy_confidence[self.df_accuracy_confidence["group"]=="low-accuracy"]["accuracy"]], \
                  bins=10, stacked=True, label=["high-accuracy", "low-accuracy"])
        plt.xlabel('Accuracy')
        plt.ylabel('Count')
        plt.title("Accuracy Confidence Data")
        
        plt.subplot(2, 2, 3)
        plt.hist([self.df_accuracy_awareness[self.df_accuracy_awareness["group"]=="high-accuracy"]["awareness"], \
                  self.df_accuracy_awareness[self.df_accuracy_awareness["group"]=="low-accuracy"]["awareness"]], \
                  bins=10, stacked=True, label=["high-accuracy", "low-accuracy"])
        plt.xlabel('Awareness')
        plt.ylabel('Count')

        plt.subplot(2, 2, 4)
        plt.hist([self.df_accuracy_confidence[self.df_accuracy_confidence["group"]=="high-accuracy"]["confidence"], \
                  self.df_accuracy_confidence[self.df_accuracy_confidence["group"]=="low-accuracy"]["confidence"]], \
                  bins=10, stacked=True, label=["high-accuracy", "low-accuracy"])
        plt.xlabel('Confidence')
        plt.ylabel('Count')
        
        plt.show()

        plt.figure(figsize=(10, 5))
        # Plot accuracy against awareness coloured by group
        plt.subplot(1, 2, 1)
        plt.scatter(self.df_accuracy_awareness[self.df_accuracy_awareness["group"]=="high-accuracy"]["awareness"], \
                    self.df_accuracy_awareness[self.df_accuracy_awareness["group"]=="high-accuracy"]["accuracy"], \
                    c="r", label="high-accuracy")
        plt.scatter(self.df_accuracy_awareness[self.df_accuracy_awareness["group"]=="low-accuracy"]["awareness"], \
                    self.df_accuracy_awareness[self.df_accuracy_awareness["group"]=="low-accuracy"]["accuracy"], \
                    c="b", label="low-accuracy")
        plt.xlabel('Awareness')
        plt.ylabel('Accuracy')
        plt.legend()
        plt.title("Accuracy Awareness Data")
        plt.subplot(1, 2, 2)
        plt.scatter(self.df_accuracy_confidence[self.df_accuracy_confidence["group"]=="high-accuracy"]["confidence"], \
                    self.df_accuracy_confidence[self.df_accuracy_confidence["group"]=="high-accuracy"]["accuracy"], \
                    c="r", label="high-accuracy")
        plt.scatter(self.df_accuracy_confidence[self.df_accuracy_confidence["group"]=="low-accuracy"]["confidence"], \
                    self.df_accuracy_confidence[self.df_accuracy_confidence["group"]=="low-accuracy"]["accuracy"], \
                    c="b", label="low-accuracy")
        plt.xlabel('Confidence')
        plt.ylabel('Accuracy')
        plt.legend()
        plt.title("Accuracy Confidence Data")
        plt.show()
