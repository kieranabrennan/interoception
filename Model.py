import numpy as np
import asyncio
from PolarH10 import PolarH10
import time

class Model:

    def __init__(self):
        
        self.polar_sensor = None

        # Sample rates
        self.ACC_UPDATE_LOOP_PERIOD = 0.001 # s, time to sleep between accelerometer updates
        self.ACC_HIST_SAMPLE_RATE = 1000 # Hz, rate to subsample acceleration (raw data @ 200 Hz)
        
        # History sizes
        self.BR_ACC_HIST_SIZE = 1200 # 
        self.BR_HIST_SIZE = 500 # Fast breathing 20 breaths per minute, sampled once every breathing cycle, over 10 minutes this is 200 values

        # Initialisation
        self.t_last_breath_acc_update = 0

        # History array initialisation
        self.breath_acc_hist = np.full(self.BR_ACC_HIST_SIZE, np.nan)
        self.breath_acc_times = np.full(self.BR_ACC_HIST_SIZE, np.nan)
        self.breath_acc_times_rel_s = np.full(self.BR_ACC_HIST_SIZE, np.nan)
        
    def set_polar_sensor(self, device):
        self.polar_sensor = PolarH10(device)

    async def connect_sensor(self):
        await self.polar_sensor.connect()
        await self.polar_sensor.get_device_info()
        await self.polar_sensor.print_device_info()
        
    async def disconnect_sensor(self):
        await self.polar_sensor.disconnect()

    async def update_acc(self): # pmd: polar measurement data
        
        await self.polar_sensor.start_ecg_stream()
        
        while True:
            await asyncio.sleep(self.ACC_UPDATE_LOOP_PERIOD)
            
            # Updating the acceleration history
            while not self.polar_sensor.ecg_queue_is_empty():
                # Get the latest sensor data
                t, ecg = self.polar_sensor.dequeue_ecg()

                if t - self.t_last_breath_acc_update > 1/self.ACC_HIST_SAMPLE_RATE:
                    self.breath_acc_hist = np.roll(self.breath_acc_hist, -1)
                    self.breath_acc_hist[-1] = ecg
                    self.breath_acc_times = np.roll(self.breath_acc_times, -1)
                    self.breath_acc_times[-1] = t
                    self.t_last_breath_acc_update = t

                    


    