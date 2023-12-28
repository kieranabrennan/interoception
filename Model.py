import asyncio
from PolarH10 import PolarH10
from BeatTracker import BeatTracker
from PySide6.QtCore import QObject, Signal
from bleak import BleakScanner
from datetime import datetime
import json
import os

class Model(QObject):
    sensorConnected = Signal()

    def __init__(self):
        super().__init__()
        self.polar_sensor = None
        self.beat_tracker = BeatTracker()

        self.beat_count_measured = None
        self.beat_count_entered = None
        self.beat_count_accuracy = None
        self.beat_count_confidence = None

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

    def getBeatCountMeasured(self, start_time, end_time):
        self.beat_count_measured = self.beat_tracker.get_beat_count_from_wind(start_time, end_time)
        return self.beat_count_measured
        
    def getBeatCountAccuracy(self, beat_count_entered):
        self.beat_count_entered = beat_count_entered
        self.beat_count_accuracy = 1 - abs(self.beat_count_measured - self.beat_count_entered)/(0.5*(self.beat_count_measured + self.beat_count_entered))
        return self.beat_count_accuracy

    def setBeatCountConfidence(self, beat_count_confidence):
        self.beat_count_confidence = beat_count_confidence

    def saveBeatTrackingData(self):
        data = {
            "Beat count measured": self.beat_count_measured,
            "Beat count entered": self.beat_count_entered,
            "Beat count accuracy": self.beat_count_accuracy,
            "Beat count confidence": self.beat_count_confidence
        }

        data_folder = "data"
        if not os.path.exists(data_folder):
            os.makedirs(data_folder)

        timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
        filename = f"beat_tracking_data_{timestamp}.json"
        filepath = os.path.join(data_folder, filename)

        with open(filepath, "w") as file:
            json.dump(data, file, indent=4)

        print(f"Data saved to {filepath}")

                    


    