import matplotlib
matplotlib.use('Qt5Agg')

import matplotlib.pyplot as plt
import numpy as np
import neurokit2 as nk
from PySide6.QtCore import QObject
import vars
''' 
BeatTracker class
Tracks a rolling ecg signal history and calculate number of beats in a time window
'''
class BeatTracker(QObject):

    def __init__(self):
        super().__init__()
        self.ECG_HIST_SIZE = 24000 # 3 minutes of history at 130 Hz
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
        ecg_peaks = nk.ecg_findpeaks(wind_values, sampling_rate=130) 
        r_peak_ids = ecg_peaks['ECG_R_Peaks']
        self.beat_count_measured = len(r_peak_ids)
        print(f"R peaks: {r_peak_ids}")
        # Show the start time error to 3 dp
        print(f"Start time error: {start_time-wind_times[0]:.3f} s")
        print(f"End time error: {end_time-wind_times[-1]:.3f} s")
        print(f"Number of R peaks: {self.beat_count_measured:.0f}")

        if vars.SHOW_DEBUG_GRAPHS:
            self.plot_graph(wind_values, wind_times, r_peak_ids)

        return self.beat_count_measured

    def plot_graph(self, wind_values, wind_times, r_peak_ids):
        plt.figure()
        plt.plot(wind_times, wind_values)
        plt.scatter(wind_times[r_peak_ids], wind_values[r_peak_ids], c='r', marker='x')
        plt.xlabel('Time')
        plt.ylabel('ECG Value')
        plt.title('ECG Plot')
        plt.show()

    def get_ecg_wind(self, start_time, end_time):
        indices = np.where((self.ecg_times >= start_time) & (self.ecg_times <= end_time))
        return self.ecg_hist[indices], self.ecg_times[indices]