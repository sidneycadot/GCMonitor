#! /usr/bin/env python3

import gc, time, sys
from collections import Counter

from PyQt5.QtWidgets import QWidget, QApplication, QTableView, QHBoxLayout, QVBoxLayout, QHeaderView, QPushButton, QGroupBox
from PyQt5.QtCore import Qt, QVariant, QTimer, QAbstractTableModel

class GCTableModel(QAbstractTableModel):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.counts = []

    def update_counts(self, counts):
        if counts == self.counts:
            return
        self.beginResetModel()
        self.counts = counts
        self.endResetModel()

    def rowCount(self, index):
        return len(self.counts)

    def columnCount(self, index):
        return 2

    def data(self, index, role):
        if role == Qt.DisplayRole:
            row = index.row()
            col = index.column()
            if col == 0:
                return str(self.counts[row][0].__name__)
            else:
                return str(self.counts[row][1])

        return QVariant()

    def headerData(self, section, orientation, role):
        if role == Qt.DisplayRole and orientation == Qt.Horizontal:
            if section == 0:
                return "type"
            else:
                return "instances"
        return QVariant()

class GCMonitorWidget(QWidget):

    def __init__(self, update_interval_ms, *args, **kwargs):
        super().__init__(*args, **kwargs)
        layout = QVBoxLayout()

        gb1 = QGroupBox("instance counts")
        gb1_layout = QVBoxLayout()
        tableView = QTableView()
        gcmodel = GCTableModel()
        tableView.setModel(gcmodel)
        tableView.verticalHeader().hide()
        tableView.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeToContents)
        tableView.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        gb1_layout.addWidget(tableView)
        gb1.setLayout(gb1_layout)
        layout.addWidget(gb1)

        gb2 = QGroupBox("reference")
        gb2_layout = QHBoxLayout()
        gb2_layout.addStretch()
        pb = QPushButton("set reference")
        pb.clicked.connect(lambda: self.set_reference_command(True))
        gb2_layout.addWidget(pb)
        pb = QPushButton("clear reference")
        pb.clicked.connect(lambda: self.set_reference_command(False))
        gb2_layout.addWidget(pb)
        gb2_layout.addStretch()
        gb2.setLayout(gb2_layout)
        layout.addWidget(gb2)

        gb3 = QGroupBox("garbage collector commands")
        gb3_layout = QHBoxLayout()
        gb3_layout.addStretch()
        pb = QPushButton("collect(0)")
        pb.clicked.connect(lambda: gc.collect(0))
        gb3_layout.addWidget(pb)
        pb = QPushButton("collect(1)")
        pb.clicked.connect(lambda: gc.collect(1))
        gb3_layout.addWidget(pb)
        pb = QPushButton("collect(2)")
        pb.clicked.connect(lambda: gc.collect(2))
        gb3_layout.addWidget(pb)
        gb3_layout.addStretch()
        gb3.setLayout(gb3_layout)
        layout.addWidget(gb3)

        self.setLayout(layout)

        self.reference = Counter()
        self.reference_time = None
        self.reference_active = False
        self.reference_command = None  # None: keep; True: update reference; False: clear reference.

        self.gcmodel = gcmodel

        self.update_gc_info()
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_gc_info)
        self.timer.start(update_interval_ms)

    def set_reference_command(self, reference_command):
        self.reference_command = reference_command

    def update_gc_info(self):
        t1 = time.monotonic()
        objects = gc.get_objects()
        counter = Counter(type(o) for o in objects)
        if self.reference_command is not None:
            if self.reference_command:
                self.reference = counter.copy()
            else:
                self.reference.clear()
            self.reference_command = None
        counter.subtract(self.reference)
        counts = [(x, y) for (x,y) in counter.most_common() if y != 0]
        self.gcmodel.update_counts(counts)
        t2 = time.monotonic()
        duration = (t2 - t1)

        del objects

app = None # Recommended way to prevent shutdown issues.
def main():
    global app
    app = QApplication(sys.argv)
    w = GCMonitorWidget(200) # update at 5 Hz
    w.show()
    return QApplication.exec()


if __name__ == "__main__":
    exitcode = main()
    sys.exit(exitcode)
