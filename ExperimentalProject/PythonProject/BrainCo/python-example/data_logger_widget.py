from PySide6.QtWidgets import QWidget, QPushButton, QLabel, QRadioButton, QLineEdit, QTimeEdit, QGridLayout, \
    QDateTimeEdit, QComboBox, QVBoxLayout, QHBoxLayout
from PySide6.QtCore import Qt, Signal, QTimer, QTime
from PySide6.QtGui import QIcon
import datetime
import logging


logger = logging.getLogger(__name__)


class DataLoggerWidget(QWidget):
    start_signal = Signal(str)
    stop_signal = Signal()
    label_signal = Signal(str)

    def __init__(self, file_exts, icon=None):
        super(DataLoggerWidget, self).__init__()
        if icon:
            self.setWindowIcon(QIcon(icon))
        self.setWindowTitle("data logger")
        self.setStyleSheet('''font: 11pt''')
        self.timer_label = QLabel("00:00:00")
        self.timer_label.setAlignment(Qt.AlignCenter)
        self.timer_label.setStyleSheet('''font: 30pt''')
        self.timer_radiobutton = QRadioButton("countdown")
        self.timer_timeedit = QTimeEdit()
        self.timer_timeedit.setDisplayFormat("HH:mm:ss")
        self.timer_timeedit.setCurrentSection(QDateTimeEdit.SecondSection)
        self.timer_timeedit.setTime(QTime(0, 0, 0))
        countdown_layout = QHBoxLayout()
        countdown_layout.addWidget(self.timer_radiobutton)
        countdown_layout.addWidget(self.timer_timeedit)
        self.name_lineedit = QLineEdit()
        self.ext_combobox = QComboBox()
        self.ext_combobox.addItems(file_exts)
        filename_layout = QHBoxLayout()
        filename_layout.addWidget(self.name_lineedit)
        filename_layout.addWidget(self.ext_combobox)
        self.start_button = QPushButton("start")
        self.start_button.clicked.connect(self.on_clicked_start)
        self.stop_button = QPushButton("stop")
        self.stop_button.clicked.connect(self.on_clicked_stop)
        action_layout = QHBoxLayout()
        action_layout.addWidget(self.start_button)
        action_layout.addWidget(self.stop_button)
        self.label_lineedit = QLineEdit()
        self.label_button = QPushButton("Add Label")
        self.label_button.clicked.connect(self.on_clicked_label)
        label_layout = QHBoxLayout()
        label_layout.addWidget(self.label_lineedit)
        label_layout.addWidget(self.label_button)

        self.setLayout(QVBoxLayout())

        self.layout().addWidget(self.timer_label)
        for layout in [countdown_layout, filename_layout, action_layout, label_layout]:
            self.layout().addLayout(layout)
            layout.setStretch(0, 1)
            layout.setStretch(1, 1)

        self.timer = QTimer()
        self.timer.timeout.connect(self.on_timer_timeout)
        self.timer.setInterval(100)

        self.data_duration = 0
        self.stop_button.setEnabled(False)
        self.start_time = datetime.datetime.now()

    def on_timer_timeout(self):
        now = datetime.datetime.now()
        duration = (now - self.start_time).seconds
        m, s = divmod(duration, 60)
        h, m = divmod(m, 60)
        self.timer_label.setText('{:02d}:{:02d}:{:02d}'.format(h, m, s))
        if self.data_duration and duration >= self.data_duration:
            self.on_clicked_stop()

    def on_clicked_start(self):
        self.start_signal.emit(self.name_lineedit.text())
        self.timer.start()
        self.start_button.setEnabled(False)
        self.stop_button.setEnabled(True)
        self.ext_combobox.setEnabled(False)
        self.start_time = datetime.datetime.now()
        duration = self.timer_timeedit.time()
        if self.timer_radiobutton.isChecked() and duration != QTime(0, 0, 0):
            self.data_duration = datetime.timedelta(hours=duration.hour(),
                                                    minutes=duration.minute(),
                                                    seconds=duration.second()).seconds
            logger.info("timer duration: {}".format(self.data_duration))

    def on_clicked_stop(self):
        self.timer.stop()
        self.stop_signal.emit()
        self.data_duration = 0
        self.start_button.setEnabled(True)
        self.stop_button.setEnabled(False)
        self.ext_combobox.setEnabled(True)

    def on_clicked_label(self):
        label = self.label_lineedit.text()
        if label:
            self.label_signal.emit(label)
            self.label_lineedit.clear()

    def current_file_ext(self):
        return self.ext_combobox.currentText()


if __name__ == "__main__":
    from PySide6.QtWidgets import QApplication
    import sys
    app = QApplication(sys.argv)
    win = DataLoggerWidget(file_types=['.txt', '.csv'])
    win.show()
    sys.exit(app.exec())
