from PySide6.QtWidgets import QMainWindow, QHBoxLayout, QVBoxLayout, QLabel, QPushButton, QComboBox, QGridLayout, \
    QTabWidget, QWidget, QMenu, QMenuBar
from PySide6.QtCore import QSize, Signal
from PySide6.QtGui import QIcon
from pyqtgraph import PlotWidget, PlotCurveItem, ViewBox, DateAxisItem
from scipy import fftpack
import numpy as np


QT_THEME = 'dark_teal.xml'


class Dimensions:
    WINDOW_SIZE = QSize(1024, 768)
    DEFAULT_FONT_SIZE = 11
    DEFAULT_BUTTON_WIDTH = 120
    MARGIN_EX_SM = 8
    MARGIN_SM = 12
    MARGIN_MD = 16
    MARGIN_LG = 20


class Colors:
    PLOT_BACKGROUND = 'k'
    SINGLE_CURVE = '#1de9b6'
    DOUBLE_CURVES = ['#ff1744', '#2979ff']
    TRIPLE_CURVES = ['#ff1744', '#1de9b6', '#2979ff']


class TwinXPlotWidget(PlotWidget):
    def __init__(self, title, label1, label2, range1=None, range2=None):
        super(TwinXPlotWidget, self).__init__(title=title)
        self.setBackground(Colors.PLOT_BACKGROUND)
        self.showGrid(x=True, y=True, alpha=0.5)
        p1 = self.plotItem
        p2 = ViewBox()
        p1.showAxis('right')
        p1.scene().addItem(p2)
        p1.getAxis('right').linkToView(p2)
        p2.setXLink(p1)
        for axis, label, color in zip([self.getAxis('left'), p1.getAxis('right')], [label1, label2],
                                      Colors.DOUBLE_CURVES):
            axis.setLabel(label, color=color)
            axis.setTextPen(color=color)
            axis.setPen(color=color)
        curve1 = p1.plot(pen=Colors.DOUBLE_CURVES[0], name=label1)
        curve2 = PlotCurveItem(pen=Colors.DOUBLE_CURVES[1], name=label2)
        p2.addItem(curve2)
        self.plot_widgets = [p1, p2]
        self.update_plot_size()
        p1.getViewBox().sigResized.connect(self.update_plot_size)

        if range1:
            self.setYRange(*range1)
        if range2:
            p2.setYRange(*range2)

        self.curves = [curve1, curve2]

    def update_plot_size(self):
        self.plot_widgets[1].setGeometry(self.plot_widgets[0].getViewBox().sceneBoundingRect())
        self.plot_widgets[1].linkedViewChanged(self.plot_widgets[0].getViewBox(), self.plot_widgets[1].XAxis)


class SleepStagePlotWidget(PlotWidget):
    def __init__(self):
        super(SleepStagePlotWidget, self).__init__(title="Sleep Stage", axisItems={'bottom': DateAxisItem()})
        self.setBackground(Colors.PLOT_BACKGROUND)
        self.showGrid(x=True, y=True, alpha=0.5)
        p1 = self.plotItem
        p2 = ViewBox()
        p1.showAxis('right')
        p1.scene().addItem(p2)
        p1.getAxis('right').linkToView(p2)
        p2.setXLink(p1)
        for axis, label, color in zip([self.getAxis('left'), p1.getAxis('right')], ['stage', 'confidence'],
                                      Colors.DOUBLE_CURVES):
            # axis.setLabel(label, color=color)
            axis.setTextPen(color=color)
            axis.setPen(color=color)
        stage_curve = p1.plot(pen=Colors.DOUBLE_CURVES[0], name='stage', symbol='o')
        drowsiness_curve = PlotCurveItem(pen=Colors.TRIPLE_CURVES[1], name='drowsiness')
        conf_curve = PlotCurveItem(pen=Colors.TRIPLE_CURVES[2], name='conf')
        p2.addItem(conf_curve)
        p2.addItem(drowsiness_curve)
        self.plot_widgets = [p1, p2]
        self.update_plot_size()
        p1.getViewBox().sigResized.connect(self.update_plot_size)

        self.setYRange(-3.5, 1)
        ticks = [list(zip([-3, -2, -1, 0, 1], ['DEEP', 'LIGHT', 'REM', 'AWK', 'UNK']))]
        self.getAxis('left').setTicks(ticks)

        p2.setYRange(0, 100)
        legend = p1.addLegend()
        legend.addItem(drowsiness_curve, drowsiness_curve.name())
        legend.addItem(conf_curve, conf_curve.name())

        self.curves = {
            "stage": stage_curve,
            "conf": conf_curve,
            "drowsiness": drowsiness_curve,
        }

    def update_plot_size(self):
        self.plot_widgets[1].setGeometry(self.plot_widgets[0].getViewBox().sceneBoundingRect())
        self.plot_widgets[1].linkedViewChanged(self.plot_widgets[0].getViewBox(), self.plot_widgets[1].XAxis)

    def update_plot(self, buffer):
        if buffer['time'] is not None:
            stages = buffer['stage'] * -1
            self.curves['stage'].setData(buffer['time'], stages)
            drowsiness = buffer['drowsiness']
            self.curves['drowsiness'].setData(buffer['time'], drowsiness)
            conf = buffer['conf'] * 100
            self.curves['conf'].setData(buffer['time'], conf)


class EEGWidget(QWidget):
    def __init__(self):
        super(EEGWidget, self).__init__()
        self.setLayout(QVBoxLayout())
        raw_plot = PlotWidget(title='Filtered EEG(uV)', labels={'bottom': 'Time(s)'})
        fft_plot = PlotWidget(title='FFT(uV/Hz)', labels={'bottom': 'Frequency(Hz)'})
        self.raw_curve = raw_plot.plot(pen=Colors.SINGLE_CURVE)
        self.fft_curve = fft_plot.plot(pen=Colors.SINGLE_CURVE)
        for plot in [raw_plot, fft_plot]:
            plot.setBackground(Colors.PLOT_BACKGROUND)
            plot.showGrid(x=True, y=True, alpha=0.7)
            self.layout().addWidget(plot)

    def update_plot(self, sr, eeg_data):
        if sr and eeg_data is not None:
            self.raw_curve.setData(np.arange(0, len(eeg_data))/sr, eeg_data)
            freqs, mags = calculate_fft(eeg_data, sr)
            self.fft_curve.setData(freqs, mags)


class IMUWidget(QWidget):
    def __init__(self):
        super(IMUWidget, self).__init__()
        self.setLayout(QVBoxLayout())
        acc_plot = PlotWidget(title='ACC(m/s^2) g=9.81')
        gyro_plot = PlotWidget(title='Gyro(dps)')
        euler_plot = PlotWidget(title='EulerAngle')
        self.acc_curves = []
        self.gyro_curves = []
        self.euler_curves = []
        for plot, curves in zip([acc_plot, gyro_plot, euler_plot],
                                [self.acc_curves, self.gyro_curves, self.euler_curves]):
            plot.setBackground(Colors.PLOT_BACKGROUND)
            plot.addLegend()
            plot.showGrid(x=True, y=True, alpha=0.7)
            labels = ["x", "y", "z"] if plot != euler_plot else ["yaw", "pitch", "roll"]
            for label, color in zip(labels, Colors.TRIPLE_CURVES):
                curves.append(plot.plot(pen=color, name=label))
            self.layout().addWidget(plot)

    def update_plot(self, sr, imu_data):
        for label, curves in zip(['acc', 'gyro', 'euler'], [self.acc_curves, self.gyro_curves, self.euler_curves]):
            if sr and imu_data[label] is not None:
                for data, curve in zip(imu_data[label], curves):
                    curve.setData(np.arange(0, len(data))/sr, data)


class PPGAlgoWidget(QWidget):
    def __init__(self):
        super(PPGAlgoWidget, self).__init__()
        self.setLayout(QGridLayout())
        hr_plot = TwinXPlotWidget(title="HR(bpm)", label1="hr", label2="confidence", range2=(0, 100))
        self.hr_curves = hr_plot.curves
        rr_plot = TwinXPlotWidget(title="RR(rpm)", label1="rr", label2="confidence", range2=(0, 100))
        self.rr_curves = rr_plot.curves
        spo2_plot = TwinXPlotWidget(title="SpO2(%)", label1="spo2", label2="confidence", range2=(0, 100))
        self.spo2_curves = spo2_plot.curves
        activity_plot = PlotWidget(title='Activity')
        activity_plot.setBackground(Colors.PLOT_BACKGROUND)
        activity_plot.showGrid(x=True, y=True, alpha=0.7)
        activity_plot.getAxis('left').setTicks([[(0, 'REST'), (1, 'OTHER'), (2, 'WALK'), (3, 'RUN'), (4, 'BIKE')]])
        activity_plot.setYRange(0, 4)
        self.activity_curve = activity_plot.plot(pen=Colors.SINGLE_CURVE)
        hrv_plot = PlotWidget(title='HRV(ms)')
        hrv_plot.setYRange(0, 80)
        hrv_plot.showGrid(x=True, y=True, alpha=0.7)
        self.hrv_curve = hrv_plot.plot(pen=Colors.SINGLE_CURVE)
        stress_plot = PlotWidget(title='Stress')
        stress_plot.setYRange(0, 100)
        stress_plot.showGrid(x=True, y=True, alpha=0.7)
        stress_plot.addLegend()
        self.hrv_stress_curve = stress_plot.plot(pen=Colors.DOUBLE_CURVES[0], name='hrv_stress')
        self.stress_curve = stress_plot.plot(pen=Colors.DOUBLE_CURVES[1], name='stress')

        for i, plot in enumerate([hr_plot, rr_plot, spo2_plot, activity_plot, hrv_plot, stress_plot]):
            self.layout().addWidget(plot, i // 2, i % 2, 1, 1)

    def update_plot(self, sr, ppg_data):
        if sr:
            for label, curves in zip(['hr', 'rr', 'spo2'], [self.hr_curves, self.rr_curves, self.spo2_curves]):
                if ppg_data[label] is not None:
                    for data, curve in zip(ppg_data[label], curves):
                        curve.setData(np.arange(0, len(data))/sr, data)
            if ppg_data['activity'] is not None:
                self.activity_curve.setData(np.arange(0, len(ppg_data['activity']))/sr, ppg_data['activity'])
            if ppg_data['hrv'] is not None:
                self.hrv_curve.setData(np.arange(0, len(ppg_data['hrv']))/sr, ppg_data['hrv'])
            if ppg_data['hrv'] is not None:
                self.hrv_curve.setData(np.arange(0, len(ppg_data['hrv']))/sr, ppg_data['hrv'])
            for key, curve in zip(['hrv_stress', 'stress'], [self.hrv_stress_curve, self.stress_curve]):
                if ppg_data[key] is not None:
                    curve.setData(np.arange(0, len(ppg_data[key]))/sr, ppg_data[key])


class PPGRawWidget(QWidget):
    def __init__(self):
        super(PPGRawWidget, self).__init__()
        self.setLayout(QGridLayout())
        green1_plot = PlotWidget(title='Green-1 Count')
        green2_plot = PlotWidget(title='Green-2 Count')
        ir_plot = PlotWidget(title='IR Count')
        red_plot = PlotWidget(title='Red Count')
        self.green1_curve = green1_plot.plot(pen=Colors.SINGLE_CURVE)
        self.green2_curve = green2_plot.plot(pen=Colors.SINGLE_CURVE)
        self.ir_curve = ir_plot.plot(pen=Colors.SINGLE_CURVE)
        self.red_curve = red_plot.plot(pen=Colors.SINGLE_CURVE)

        for i, plot in enumerate([green1_plot, green2_plot, ir_plot, red_plot]):
            plot.setBackground(Colors.PLOT_BACKGROUND)
            plot.showGrid(x=True, y=True, alpha=0.7)
            self.layout().addWidget(plot, i % 2, i // 2, 1, 1)

    def update_plot(self, sr, ppg_data):
        for label, curve in zip(['green1_count', 'green2_count', 'ir_count', 'red_count'],
                                [self.green1_curve, self.green2_curve, self.ir_curve, self.red_curve]):
            if sr and ppg_data[label] is not None:
                curve.setData(np.arange(0, len(ppg_data[label]))/sr, ppg_data[label].astype(np.float64))


class MainWindow(QMainWindow):
    close_window_signal = Signal()

    def __init__(self, app_ctx, parent=None, icon=None, on_tab_change=None):
        super(MainWindow, self).__init__(parent)
        self.on_tab_change = on_tab_change
        self.app_ctx = app_ctx
        self.setWindowTitle("ZenLite GUI")
        self.resize(Dimensions.WINDOW_SIZE)
        self.setStyleSheet(f'''font: {Dimensions.DEFAULT_FONT_SIZE}pt''')
        if icon:
            self.setWindowIcon(QIcon(icon))
        # layout
        mainwindow = QWidget(self)
        self.setCentralWidget(mainwindow)
        menu_bar = QMenuBar(mainwindow)
        self.setMenuBar(menu_bar)
        self.tools_menu = QMenu("Tools", self)
        menu_bar.addMenu(self.tools_menu)
        mainwindow.setLayout(QHBoxLayout())
        left_layout = QVBoxLayout()
        right_layout = QVBoxLayout()
        mainwindow.layout().addLayout(left_layout)
        mainwindow.layout().addLayout(right_layout)
        mainwindow.layout().setStretch(0, 3)
        mainwindow.layout().setStretch(1, 2)
        connection_layout = QHBoxLayout()
        data_plots_layout = QGridLayout()
        algorithm_layout = QVBoxLayout()
        information_layout = QGridLayout()
        device_info_layout = QGridLayout()
        left_layout.addLayout(connection_layout)
        left_layout.addLayout(device_info_layout)
        left_layout.addLayout(data_plots_layout)
        right_layout.addLayout(information_layout)
        right_layout.addLayout(algorithm_layout)
        # connection
        self.connect_button = QPushButton("Connect")
        self.scan_button = QPushButton("Scan")
        self.dev_list_combobox = QComboBox()
        for widget in [self.scan_button, self.dev_list_combobox, self.connect_button]:
            connection_layout.addWidget(widget)
        connection_layout.setStretch(1, 1)
        # data plots
        self.data_plot_tabs = QTabWidget()
        data_plots_layout.addWidget(self.data_plot_tabs)
        self.eeg_tab = EEGWidget()
        self.imu_tab = IMUWidget()
        self.ppg_algo_tab = PPGAlgoWidget()
        self.ppg_raw_tab = PPGRawWidget()
        for tab, title in zip([self.eeg_tab, self.imu_tab, self.ppg_algo_tab, self.ppg_raw_tab],
                              ['EEG', 'IMU', 'PPG-Algo', 'PPG-Raw']):
            self.data_plot_tabs.addTab(tab, title)
        self.data_plot_tabs.currentChanged.connect(self.on_current_tab_changed)
        # algorithm
        meditation_plot = PlotWidget(title='Meditation')
        meditation_plot.setYRange(0, 100)
        self.meditation_curve = meditation_plot.plot(pen=Colors.SINGLE_CURVE)
        stress_plot = PlotWidget(title='Stress')
        stress_plot.setYRange(0, 100)
        self.stress_curve = stress_plot.plot(pen=Colors.SINGLE_CURVE)
        self.sleep_plot = SleepStagePlotWidget()
        algorithm_layout.addWidget(self.sleep_plot)
        algorithm_layout.layout().setStretch(0, 3)
        respiratory_plot = PlotWidget(title='Respiratory')
        self.respiratory_curve = respiratory_plot.plot(pen=Colors.SINGLE_CURVE)
        for plot in [meditation_plot, stress_plot, respiratory_plot]:
            plot.setBackground(Colors.PLOT_BACKGROUND)
            plot.showGrid(x=True, y=True, alpha=0.7)
            algorithm_layout.addWidget(plot)
            algorithm_layout.layout().setStretch(algorithm_layout.count()-1, 2)

        # information
        self.connectivity_label = QLabel("-")
        self.contact_label = QLabel("-")
        self.orientation_label = QLabel("-")
        self.respiratory_label = QLabel("-")
        self.info_labels = [('Connectivity', self.connectivity_label), ('ContactState', self.contact_label),
                            ('Orientation', self.orientation_label), ('RespiratoryRate', self.respiratory_label)]
        for name, label in self.info_labels:
            information_layout.addWidget(QLabel(name), information_layout.rowCount(), 0, 1, 1)
            information_layout.addWidget(label, information_layout.rowCount()-1, 1, 1, 1)
        # device info
        self.manufacturer_label = QLabel("-")
        self.model_number_label = QLabel("-")
        self.serial_number_label = QLabel("-")
        self.hardware_revision_label = QLabel("-")
        self.firmware_revision_label = QLabel("-")
        self.battery_level_label = QLabel("-")
        self.info_keys = [('Manufacturer:', self.manufacturer_label), ('Model Number:', self.model_number_label),
                          ('Serial Number:', self.serial_number_label),
                          ('Hardware Revision:', self.hardware_revision_label),
                          ('Firmware Revision:', self.firmware_revision_label),
                          ("Battery:", self.battery_level_label)]
        info_cols = 3
        for i, (name, label) in enumerate(self.info_keys):
            device_info_layout.addWidget(QLabel(name), i / info_cols, 2 * (i % info_cols), 1, 1)
            device_info_layout.addWidget(label, i / info_cols, 2 * (i % info_cols) + 1, 1, 1)

    def set_on_tab_change_cb(self, cb):
        self.on_tab_change = cb

    def on_current_tab_changed(self, i):
        if self.on_tab_change is not None:
            self.on_tab_change(i)

    def clear_device_info(self):
        for label in self.info_keys + self.info_labels:
            label[1].setText("-")

    def update_eeg_plot(self, eeg_sr, eeg_data):
        self.eeg_tab.update_plot(eeg_sr, eeg_data)

    def update_imu_plot(self, imu_sr, imu_data):
        self.imu_tab.update_plot(imu_sr, imu_data)

    def update_ppg_raw_plot(self, ppg_sr, ppg_data):
        self.ppg_raw_tab.update_plot(ppg_sr, ppg_data)

    def update_ppg_algo_plot(self, ppg_sr, ppg_data):
        if ppg_data is not None:
            self.ppg_algo_tab.update_plot(ppg_sr, ppg_data)

    def update_meditation_plot(self, values):
        if values is not None:
            self.meditation_curve.setData(values)

    def update_stress_plot(self, values):
        if values is not None:
            self.stress_curve.setData(values)

    def update_respiratory_plot(self, sr, rate, curve):
        if rate is not None:
            self.respiratory_label.setText(str(rate))
        if curve is not None:
            self.respiratory_curve.setData(np.arange(0, len(curve))/sr, curve)

    def update_sleep_stage_plot(self, buffer):
        self.sleep_plot.update_plot(buffer)

    def closeEvent(self, event):
        super(MainWindow, self).closeEvent(event)
        self.close_window_signal.emit()


def calculate_fft(data, rate):
    sig_freq = fftpack.fftfreq(len(data), d=1.0 / rate)
    sig_fft = fftpack.fft(data)
    sig_fft = abs(sig_fft) / (rate / 2) / len(data)
    pidxs = np.where((sig_freq > 0) & (sig_freq < 50))
    return sig_freq[pidxs], sig_fft[pidxs]