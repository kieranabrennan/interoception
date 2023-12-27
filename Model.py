import numpy as np
import asyncio
from PolarH10 import PolarH10
from BeatTracker import BeatTracker
from PySide6.QtCore import QObject, Signal

class Model(QObject):
    sensorConnected = Signal()

    def __init__(self):
        super().__init__()
        self.polar_sensor = None
        self.beat_tracker = BeatTracker()
        
    def set_polar_sensor(self, device):
        self.polar_sensor = PolarH10(device)

    async def connect_sensor(self):
        await self.polar_sensor.connect()
        await self.polar_sensor.get_device_info()
        await self.polar_sensor.print_device_info()
        self.sensorConnected.emit()
        
    async def disconnect_sensor(self):
        await self.polar_sensor.disconnect()

    async def update_ecg(self): 
        await self.polar_sensor.start_ecg_stream()
        
        while True:
            await asyncio.sleep(0.005)
            while not self.polar_sensor.ecg_queue_is_empty():
                self.beat_tracker.update_ecg_history(*self.polar_sensor.dequeue_ecg())

                    


    