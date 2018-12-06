#!/usr/bin/env python
# encoding: utf-8
# create_time: 2018.10
from PySide.QtCore import QAbstractTableModel, Qt

__author__ = 'Song shiwei'


class MyTableModel(QAbstractTableModel):
    def __init__(self, parent, my_list, header, *args):
        QAbstractTableModel.__init__(self, parent, *args)
        self.my_list = my_list
        self.header = header

    def rowCount(self, parent):
        return len(self.my_list)

    def columnCount(self, parent):
        return len(self.my_list[0])

    def data(self, index, role):
        if not index.isValid():
            return None
        elif role != Qt.DisplayRole:
            return None
        return self.my_list[index.row()][index.column()]

    def headerData(self, col, orientation, role):
        if orientation == Qt.Horizontal and role == Qt.DisplayRole:
            return self.header[col]
        return None
