#!/usr/bin/env python
import PySide6  # force pyqtgraph & qt_material to use PySide6
from PySide6.QtWidgets import QApplication
from PySide6.QtCore import QObject, QTimer, Signal
from qt_material import apply_stylesheet
import numpy as np
import datetime
import time
import json

from gui_widgets import MainWindow, QT_THEME
from data_logger_widget import DataLoggerWidget
from zenlite_sdk import *

_DEBUG_EEG_MODE = False

EEG_WINDOW_TIME = 5  # second
IMU_WINDOW_TIME = 5  # second
PPG_WINDOW_TIME = 30  # second
ALGO_WINDOW_TIME = 2000  # second
SLEEP_STAGE_WINDOW = 30

DATA_PATH = "data"
ICON = "logo.ico"


class ListenerMetaClass(type(QObject), type(ZenLiteDeviceListener)):
    pass


class DeviceListener(QObject, ZenLiteDeviceListener, metaclass=ListenerMetaClass):
    eeg_update_signal = Signal(object)
    imu_update_signal = Signal(object)
    ppg_update_signal = Signal(object)
    algo_update_signal = Signal(dict)
    selected_ppg_mode = PPGMode.algo

    def __init__(self, gui):
        super(DeviceListener, self).__init__()
        self._gui = gui
        self._meditation_buffer = None
        self._stress_buffer = None
        self._eeg_buffer = None
        self._imu_buffer = {"acc": None, "gyro": None, "euler": None}
        self._ppg_algo_buffer = {
            "hr": None,
            "rr": None,
            "spo2": None,
            "activity": None,
            "hrv": None,
            "hrv_stress": None,
            "stress": None,
        }
        self._ppg_raw_buffer = {
            "green1_count": None,
            "green2_count": None,
            "ir_count": None,
            "red_count": None,
        }
        self._ppg_respiratory_rate = None
        self._ppg_respiratory_buffer = None
        self._sleep_stage_buffer = {
            "time": None,
            "stage": None,
            "conf": None,
            "drowsiness": None,
        }
        self._eeg_sample_rate = 0
        self._imu_sample_rate = 0
        self._ppg_sample_rate = 0

    @logwrap
    def on_device_info_ready(self, device_info):
        self._gui.on_dev_info_ready(device_info)

    def on_eeg_data(self, eeg_data):
        self.eeg_update_signal.emit(eeg_data)
        self._eeg_sample_rate = eeg_data.sample_rate
        window_size = EEG_WINDOW_TIME * eeg_data.sample_rate
        if self._eeg_buffer is None:
            self._eeg_buffer = np.array(eeg_data.eeg_data)
        else:
            self._eeg_buffer = trim_data(np.concatenate([self._eeg_buffer, eeg_data.eeg_data], 0), 0, window_size)

    def on_imu_data(self, imu_data):
        self.imu_update_signal.emit(imu_data)
        self._imu_sample_rate = imu_data.sample_rate
        window_size = IMU_WINDOW_TIME * imu_data.sample_rate
        if imu_data.acc_data is not None:
            acc = [imu_data.acc_data.x, imu_data.acc_data.y, imu_data.acc_data.z]
            if self._imu_buffer['acc'] is None:
                self._imu_buffer['acc'] = np.array(acc)
            else:
                self._imu_buffer['acc'] = trim_data(np.concatenate([self._imu_buffer['acc'], acc], 1), 1, window_size)
        if imu_data.gyro_data is not None:
            gyro = [imu_data.gyro_data.x, imu_data.gyro_data.y, imu_data.gyro_data.z]
            if self._imu_buffer['gyro'] is None:
                self._imu_buffer['gyro'] = np.array(gyro)
            else:
                self._imu_buffer['gyro'] = trim_data(np.concatenate([self._imu_buffer['gyro'], gyro], 1), 1, window_size)
        if imu_data.euler_angle_data is not None:
            euler = [imu_data.euler_angle_data.yaw, imu_data.euler_angle_data.pitch, imu_data.euler_angle_data.roll]
            if self._imu_buffer['euler'] is None:
                self._imu_buffer['euler'] = np.array(euler)
            else:
                self._imu_buffer['euler'] = trim_data(np.concatenate([self._imu_buffer['euler'], euler], 1), 1, window_size)

    def on_ppg_data(self, ppg_data):
        self.ppg_update_signal.emit(ppg_data)
        self._ppg_sample_rate = ppg_data.sample_rate
        window_size = PPG_WINDOW_TIME * ppg_data.sample_rate
        self._ppg_respiratory_rate = ppg_data.respiratory_rate
        if ppg_data.respiratory_curve is not None and len(ppg_data.respiratory_curve) > 0:
            if self._ppg_respiratory_buffer is None:
                self._ppg_respiratory_buffer = np.array(ppg_data.respiratory_curve)
            else:
                self._ppg_respiratory_buffer = trim_data(np.concatenate([self._ppg_respiratory_buffer, ppg_data.respiratory_curve], 0), 0, window_size)
        if ppg_data.raw_data is not None:
            for data in ppg_data.raw_data:
                if self._ppg_raw_buffer['green1_count'] is None:
                    self._ppg_raw_buffer['green1_count'] = np.array([data.green1_count])
                else:
                    self._ppg_raw_buffer['green1_count'] = trim_data(np.concatenate([self._ppg_raw_buffer['green1_count'], [data.green1_count]], 0), 0, window_size)
                if self._ppg_raw_buffer['green2_count'] is None:
                    self._ppg_raw_buffer['green2_count'] = np.array([data.green2_count])
                else:
                    self._ppg_raw_buffer['green2_count'] = trim_data(np.concatenate([self._ppg_raw_buffer['green2_count'], [data.green2_count]], 0), 0, window_size)
                if self._ppg_raw_buffer['ir_count'] is None:
                    self._ppg_raw_buffer['ir_count'] = np.array([data.ir_count])
                else:
                    self._ppg_raw_buffer['ir_count'] = trim_data(np.concatenate([self._ppg_raw_buffer['ir_count'], [data.ir_count]], 0), 0, window_size)
                if self._ppg_raw_buffer['red_count'] is None:
                    self._ppg_raw_buffer['red_count'] = np.array([data.red_count])
                else:
                    self._ppg_raw_buffer['red_count'] = trim_data(np.concatenate([self._ppg_raw_buffer['red_count'], [data.red_count]], 0), 0, window_size)
        if ppg_data.algo_data is not None:
            for data in ppg_data.algo_data:
                hr = [[data.hr], [data.hr_conf]]
                rr = [[data.rr], [data.rr_conf]]
                spo2 = [[data.spo2], [data.spo2_conf]]
                activity = [data.activity]
                hrv = [data.hrv]
                hrv_stress = [data.hrv_stress]
                stress = [data.stress]
                if self._ppg_algo_buffer['hr'] is None:
                    self._ppg_algo_buffer['hr'] = np.array(hr)
                else:
                    self._ppg_algo_buffer['hr'] = trim_data(np.concatenate([self._ppg_algo_buffer['hr'], hr], 1), 1, window_size)
                if data.rr_conf == 100:
                    if self._ppg_algo_buffer['rr'] is None:
                        self._ppg_algo_buffer['rr'] = np.array(rr)
                    else:
                        self._ppg_algo_buffer['rr'] = trim_data(np.concatenate([self._ppg_algo_buffer['rr'], rr], 1), 1, window_size)
                if self._ppg_algo_buffer['spo2'] is None:
                    self._ppg_algo_buffer['spo2'] = np.array(spo2)
                else:
                    self._ppg_algo_buffer['spo2'] = trim_data(np.concatenate([self._ppg_algo_buffer['spo2'], spo2], 1), 1, window_size)
                if self._ppg_algo_buffer['activity'] is None:
                    self._ppg_algo_buffer['activity'] = np.array(activity)
                else:
                    self._ppg_algo_buffer['activity'] = trim_data(np.concatenate([self._ppg_algo_buffer['activity'], activity], 0), 0, window_size)
                if data.hrv >= 0:
                    if self._ppg_algo_buffer['hrv'] is None:
                        self._ppg_algo_buffer['hrv'] = np.array(hrv)
                    else:
                        self._ppg_algo_buffer['hrv'] = trim_data(np.concatenate([self._ppg_algo_buffer['hrv'], hrv], 0), 0, window_size)
                if data.hrv_stress >= 0:
                    if self._ppg_algo_buffer['hrv_stress'] is None:
                        self._ppg_algo_buffer['hrv_stress'] = np.array(hrv_stress)
                    else:
                        self._ppg_algo_buffer['hrv_stress'] = trim_data(np.concatenate([self._ppg_algo_buffer['hrv_stress'], hrv_stress], 0), 0, window_size)
                if data.stress >= 0:
                    if self._ppg_algo_buffer['stress'] is None:
                        self._ppg_algo_buffer['stress'] = np.array(stress)
                    else:
                        self._ppg_algo_buffer['stress'] = trim_data(np.concatenate([self._ppg_algo_buffer['stress'], stress], 0), 0, window_size)

    def on_brain_wave(self, brain_wave):
        pass  # print("on_brain_wave not implemented")

    def on_error(self, error):
        pass  # print("on_error not implemented: %i" % error.code)

    def on_connectivity_change(self, connectivity):
        self._gui.on_dev_connectivity_changed(connectivity)

    def on_contact_state_change(self, contact_state):
        self._gui.on_dev_contact_state_change(contact_state)

    def on_orientation_change(self, orientation):
        self._gui.on_dev_orientation_change(orientation)

    def on_stress(self, stress):
        self.algo_update_signal.emit({"stress": stress})
        if self._stress_buffer is None:
            self._stress_buffer = np.array([stress])
        else:
            self._stress_buffer = trim_data(np.concatenate([self._stress_buffer, [stress]], 0), 0, ALGO_WINDOW_TIME)

    def on_meditation(self, meditation):
        self.algo_update_signal.emit({"meditation": meditation})
        if self._meditation_buffer is None:
            self._meditation_buffer = np.array([meditation])
        else:
            self._meditation_buffer = trim_data(np.concatenate([self._meditation_buffer, [meditation]], 0), 0, ALGO_WINDOW_TIME)

    def on_sleep_stage(self, stage, conf, drowsiness):
        self.algo_update_signal.emit(dict(zip(['stage', 'conf', 'drowsiness'], [stage, conf, drowsiness])))
        stage = stage.value
        for key, value in zip(['time', 'stage', 'conf', 'drowsiness'], [time.time(), stage, conf, drowsiness]):
            if self._sleep_stage_buffer[key] is None:
                self._sleep_stage_buffer[key] = np.array([value])
            else:
                self._sleep_stage_buffer[key] = trim_data(np.concatenate([self._sleep_stage_buffer[key], [value]], 0), 0, SLEEP_STAGE_WINDOW)

    def get_eeg_buffer_for_plot(self):
        return self._eeg_sample_rate, self._eeg_buffer if self._eeg_buffer is None else self._eeg_buffer.copy()

    def get_imu_buffer_for_plot(self):
        return self._imu_sample_rate, self._imu_buffer if self._imu_buffer is None else self._imu_buffer.copy()

    def get_ppg_buffer_for_plot(self):
        return self._ppg_sample_rate, \
               self._ppg_raw_buffer if self._ppg_raw_buffer is None else self._ppg_raw_buffer.copy(), \
               self._ppg_algo_buffer if self._ppg_algo_buffer is None else self._ppg_algo_buffer.copy()

    def get_stress_for_plot(self):
        return self._stress_buffer if self._stress_buffer is None else self._stress_buffer.copy()

    def get_meditation_for_plot(self):
        return self._meditation_buffer if self._meditation_buffer is None else self._meditation_buffer.copy()

    def get_sleep_stage_for_plot(self):
        return self._sleep_stage_buffer

    def get_respiratory_for_plot(self):
        return self._ppg_sample_rate, self._ppg_respiratory_rate, self._ppg_respiratory_buffer


class ZenLiteGUI:

    def __init__(self):
        self.app = QApplication(sys.argv)
        # self._view_stack = QStackedWidget()
        # self._view_stack.setFixedSize(_WINDOW_SIZE)
        # self.splash_screen = SplashScreen(self)
        icon = get_resource_path(ICON)
        self.main_window = MainWindow(self, icon=icon, on_tab_change=None)
        apply_stylesheet(self.app, theme=QT_THEME)
        self.main_window.close_window_signal.connect(self.on_window_close)
        self.main_window.scan_button.clicked.connect(self.on_clicked_scan_button)
        self.main_window.connect_button.clicked.connect(self.on_clicked_connect_button)
        self.data_logger = DataLoggerWidget(file_exts=['.txt', '.csv'], icon=icon)
        self.data_logger.start_signal.connect(self.on_start_data_logging)
        self.data_logger.stop_signal.connect(self.on_stop_data_logging)
        self.data_logger.label_signal.connect(self.on_clicked_add_label)
        self.main_window.tools_menu.addAction("data logger", self.data_logger.show)
        self.data_filename = ""

        self.current_device = None
        self.current_device_listener = None

        self.plot_timer = QTimer()
        self.plot_timer.timeout.connect(self.on_plot_timer_timeout)
        self.plot_timer.start(100)

    """
    def on_selected_tab_changed(self, tab_index):
        if self.current_device is not None:
            if tab_index == 2 and DeviceListener.selected_ppg_mode != PPGMode.algo:
                DeviceListener.selected_ppg_mode = PPGMode.algo
                self.current_device.zl_config_ppg(PPGReportRate.sr25, PPGMode.algo)
            elif tab_index == 3 and DeviceListener.selected_ppg_mode != PPGMode.raw_data:
                DeviceListener.selected_ppg_mode = PPGMode.raw_data
                self.current_device.zl_config_ppg(PPGReportRate.sr25, PPGMode.raw_data)
    """

    def on_start_data_logging(self, label):
        folder = os.path.join(DATA_PATH, datetime.datetime.now().strftime("%Y%m%d"))
        if not os.path.exists(folder):
            os.makedirs(folder)
        file_name = "".join([datetime.datetime.now().strftime("%H-%M-%S"), "_", label])
        data_file = os.path.join(folder, file_name)
        self.data_filename = data_file

    def on_stop_data_logging(self):
        self.data_filename = ""

    def on_clicked_add_label(self, label):
        if len(self.data_filename):
            file_ext = self.data_logger.current_file_ext()
            file_name = self.data_filename + '_evt' + file_ext
            ts_now = time.time()
            if file_ext.__contains__('csv'):
                if not os.path.exists(file_name):
                    with open(file_name, 'w') as f:
                        f.write('time,event\n')
                with open(file_name, 'a') as f:
                    f.write(f'{ts_now},{label}\n')
            elif file_ext.__contains__('txt'):
                with open(file_name, 'a') as f:
                    json.dump({'time': ts_now, 'event': label}, f)
                    f.write("\n")

    def on_plot_timer_timeout(self):
        if self.current_device_listener is not None:
            sr, eeg = self.current_device_listener.get_eeg_buffer_for_plot()
            self.main_window.update_eeg_plot(sr, eeg)
            sr, imu = self.current_device_listener.get_imu_buffer_for_plot()
            self.main_window.update_imu_plot(sr, imu)
            sr, ppg_raw, ppg_algo = self.current_device_listener.get_ppg_buffer_for_plot()
            self.main_window.update_ppg_raw_plot(sr, ppg_raw)
            self.main_window.update_ppg_algo_plot(sr, ppg_algo)
            self.main_window.update_meditation_plot(self.current_device_listener.get_meditation_for_plot())
            self.main_window.update_stress_plot(self.current_device_listener.get_stress_for_plot())
            self.main_window.update_sleep_stage_plot(self.current_device_listener.get_sleep_stage_for_plot())
            self.main_window.update_respiratory_plot(*self.current_device_listener.get_respiratory_for_plot())

    def on_clicked_connect_button(self):
        device = self.main_window.dev_list_combobox.currentData()
        if device is not None:
            if self.main_window.connect_button.text() == "Connect":
                self.main_window.dev_list_combobox.setEnabled(False)
                self.main_window.connect_button.setText("Connecting")
                self.main_window.connect_button.setEnabled(False)
                if self.main_window.scan_button.text() == "Scanning":
                    self.main_window.scan_button.setText("Scan")
                    ZenLiteSDK.stop_scan()
                self.current_device = device
                self.current_device_listener = DeviceListener(self)
                self.current_device_listener.eeg_update_signal.connect(self.on_eeg_update)
                self.current_device_listener.imu_update_signal.connect(self.on_imu_update)
                self.current_device_listener.ppg_update_signal.connect(self.on_ppg_update)
                self.current_device_listener.algo_update_signal.connect(self.on_algo_update)
                self.current_device.set_listener(self.current_device_listener)
                self.current_device.connect()
            elif self.main_window.connect_button.text() == "Disconnect":
                self.main_window.connect_button.setText('Disconnecting')
                self.main_window.connect_button.setEnabled(False)
                self.current_device.disconnect()

    def on_clicked_scan_button(self):
        if self.main_window.scan_button.text() == "Scan":
            self.main_window.scan_button.setText("Scanning")
            self.main_window.dev_list_combobox.clear()
            ZenLiteSDK.start_scan(self.on_found_device)
        else:
            self.main_window.scan_button.setText("Scan")
            ZenLiteSDK.stop_scan()

    def on_found_device(self, device):
        if -1 == self.main_window.dev_list_combobox.findData(device):
            self.main_window.dev_list_combobox.addItem(device.name, device)

    def on_dev_connectivity_changed(self, connectivity):
        self.main_window.connectivity_label.setText(connectivity.name)
        if Connectivity.connected == connectivity:
            self.main_window.connect_button.setText('Disconnect')
            self.main_window.connect_button.setEnabled(True)
            self.current_device.zl_pair(self.current_device.in_pairing_mode, self.on_dev_pair_response)
        elif Connectivity.disconnected == connectivity:
            self.current_device = None
            self.current_device_listener.deleteLater()
            self.main_window.connect_button.setText("Connect")
            self.main_window.connect_button.setEnabled(True)
            self.main_window.dev_list_combobox.setEnabled(True)
            self.main_window.dev_list_combobox.clear()
            self.main_window.clear_device_info()

    @logwrap
    def update_battery(self):
        if self.main_window is None:
            fatal_error("Main Window not initialized")
        try:
            self.main_window.battery_level_label.setText(str(self.current_device.battery_level))
        except (ValueError, AttributeError) as e:
            ZLOG.LOG_ERROR("Failed to update battery value")

    def on_dev_info_ready(self, device_info):
        self.main_window.manufacturer_label.setText(device_info.manufacturer_name)
        self.main_window.model_number_label.setText(device_info.model_number)
        self.main_window.serial_number_label.setText(device_info.serial_number)
        self.main_window.hardware_revision_label.setText(device_info.hardware_revision)
        self.main_window.firmware_revision_label.setText(device_info.firmware_revision)
        self.update_battery()

    def on_dev_contact_state_change(self, contact_state):
        self.main_window.contact_label.setText(contact_state.name)

    def on_dev_orientation_change(self, orientation):
        self.main_window.orientation_label.setText(orientation.name)

    def on_dev_pair_response(self, device, res):
        print(f"[{device.name}], on_pair_response:", res.success())
        if _DEBUG_EEG_MODE:
            from example import dev_analyze_eeg
            dev_analyze_eeg(device)
        elif res.success():
            self.current_device.zl_config_afe(EEGSampleRate.sr256, self.on_afe_response)
            self.current_device.zl_config_imu(IMUSampleRate.sr50, IMUMode.acc_gyro, self.on_imu_response)
            self.current_device.zl_config_ppg(PPGReportRate.sr25, PPGMode.algo, 0, 0, self.on_ppg_response)

    def on_afe_response(self, device, res):
        print(f"[{device.name}], on_afe_response:", res.success())

    def on_imu_response(self, device, res):
        print(f"[{device.name}], on_imu_response:", res.success())

    def on_ppg_response(self, device, res):
        print(f"[{device.name}], on_ppg_response:", res.success())

    def on_eeg_update(self, eeg_data):
        self.save_data_to_file(eeg=eeg_data)

    def on_imu_update(self, imu_data):
        self.save_data_to_file(imu=imu_data)

    def on_ppg_update(self, ppg_data):
        self.save_data_to_file(ppg=ppg_data)

    def on_algo_update(self, algo_data):
        self.save_data_to_file(algo=algo_data)

    def save_data_to_file(self, eeg=None, imu=None, ppg=None, algo=None):
        if len(self.data_filename):
            file_ext = self.data_logger.current_file_ext()
            ts_now = time.time()
            if eeg:
                file_name = self.data_filename + '_eeg' + file_ext
                if file_ext.__contains__('csv'):
                    if not os.path.exists(file_name):
                        with open(file_name, 'w') as f:
                            f.write("time,ch0\n")
                    with open(file_name, 'a') as f:
                        for v in eeg.eeg_data:
                            f.write(f"{ts_now},{v}\n")
                elif file_ext.__contains__('txt'):
                    with open(file_name, 'a', newline='') as f:
                        json.dump({'time': ts_now, 'data': eeg.eeg_data, 'sample_rate': eeg.sample_rate, 'sequence_num': eeg.sequence_num}, f)
                        f.write("\n")
            if imu:
                file_name = self.data_filename + '_imu' + file_ext
                if file_ext.__contains__('csv'):
                    if not os.path.exists(file_name):
                        with open(file_name, 'w') as f:
                            f.write('time,acc.x,acc.y,acc.z,gyro.x,gyro.y,gyro.z,euler.yaw,euler.pitch,euler.roll\n')
                    data_len = len(imu.acc_data.x if imu.acc_data else (imu.gyro_data.x if imu.gyro_data else (imu.euler_angle_data.x if imu.euler_angle_data else [])))
                    imu_array = np.empty((data_len, 10))
                    imu_array.fill(np.NaN)
                    imu_array[:, 0] = ts_now
                    for i, data in enumerate([imu.acc_data, imu.gyro_data, imu.euler_angle_data]):
                        if data is not None:
                            imu_array[:, i * 3 + 1] = data.x if data != imu.euler_angle_data else data.yaw
                            imu_array[:, i * 3 + 2] = data.y if data != imu.euler_angle_data else data.pitch
                            imu_array[:, i * 3 + 3] = data.z if data != imu.euler_angle_data else data.roll
                    with open(file_name, 'a') as f:
                        for i in range(imu_array.shape[0]):
                            f.write(",".join(str(v) for v in imu_array[i]))
                            f.write('\n')
                elif file_ext.__contains__('txt'):
                    with open(file_name, 'a') as f:
                        json.dump({'time': ts_now, "sample_rate": imu.sample_rate, "acc": vars(imu.acc_data) if imu.acc_data else [], "gyro": vars(imu.gyro_data) if imu.gyro_data else [], "euler": vars(imu.euler_angle_data) if imu.euler_angle_data else []}, f)
                        f.write("\n")
            if ppg:
                # TODO: save ppg as csv
                file_name = self.data_filename + '_ppg' + ".txt"
                with open(file_name, 'a') as f:
                    json.dump({'time': ts_now, 'sample_rate': ppg.sample_rate,
                               'raw_data': [vars(i) for i in ppg.raw_data] if ppg.raw_data else [],
                               'algo_data': [vars(i) for i in ppg.algo_data] if ppg.algo_data else [],
                               'respiratory': {'rate': ppg.respiratory_rate if ppg.respiratory_rate else "None",
                                               'curve': ppg.respiratory_curve if ppg.respiratory_curve else "None",
                                               'state': ppg.respiratory_state if ppg.respiratory_state else "None"}}, f)
                    f.write("\n")
            if algo:
                # TODO: save ppg as csv
                file_name = self.data_filename + '_algo' + ".txt"
                with open(file_name, 'a') as f:
                    algo['time'] = time.time()
                    json.dump(algo, f)
                    f.write("\n")

    def on_window_close(self):
        if self.current_device is not None:
            self.current_device.disconnect()

    def start(self):
        # self._view_stack.addWidget(self.main_window)
        self.main_window.show()


def trim_data(buffer, axis, size):
    size = int(size)
    if buffer.shape[axis] >= size:
        buffer = np.delete(buffer, [i for i in range(buffer.shape[axis] - size)], axis)
    return buffer


def get_resource_path(relative_path):
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)


if __name__ == "__main__":
    zenlite_gui = ZenLiteGUI()
    zenlite_gui.start()

    sys.exit(zenlite_gui.app.exec())
