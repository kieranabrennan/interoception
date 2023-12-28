import matplotlib
matplotlib.use('Qt5Agg')

import matplotlib.pyplot as plt
import numpy as np
import neurokit2 as nk
from PySide6.QtCore import QObject

''' 
BeatTracker class
Tracks a rolling ecg signal history and calculate number of beats in a time window
'''
class BeatTracker(QObject):

    def __init__(self):
        super().__init__()
        self.ECG_HIST_SIZE = 2400 # Number of samples to keep in the history
        self.ecg_hist = np.full(self.ECG_HIST_SIZE, np.nan)
        self.ecg_times = np.full(self.ECG_HIST_SIZE, np.nan)
        
        self.beat_count_measured = None
        self.beat_count_entered = None
        
    def update_ecg_history(self, t, ecg):
        self.ecg_hist = np.roll(self.ecg_hist, -1)
        self.ecg_hist[-1] = ecg
        self.ecg_times = np.roll(self.ecg_times, -1)
        self.ecg_times[-1] = t

    def get_beat_count_from_wind(self, start_time, end_time):
        wind_values, wind_times = self.get_ecg_wind(start_time, end_time)
        self.beat_count_measured = self.get_beat_count(wind_values, 130)
        # Show the start time error to 3 dp
        print(f"Start time error: {start_time-wind_times[0]:.3f} s")
        print(f"End time error: {end_time-wind_times[-1]:.3f} s")
        print(f"Number of R peaks: {self.beat_count_measured:.0f}")

        self.plot_graph(wind_values, wind_times)

        return self.beat_count_measured

    def plot_graph(self, wind_values, wind_times):
        plt.figure()
        plt.plot(wind_times, wind_values)
        plt.xlabel('Time')
        plt.ylabel('ECG Value')
        plt.title('ECG Plot')
        plt.show()

    def get_beat_count(self, ecg, sampling_rate):
        peaks = nk.ecg_findpeaks(ecg, sampling_rate=sampling_rate) 
        r_peaks = peaks['ECG_R_Peaks']
        return len(r_peaks)

    def get_ecg_wind(self, start_time, end_time):
        indices = np.where((self.ecg_times >= start_time) & (self.ecg_times <= end_time))
        return self.ecg_hist[indices], self.ecg_times[indices]