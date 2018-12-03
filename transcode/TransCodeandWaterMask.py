#!/usr/bin/env python
# -*- encoding: utf-8 -*-
# Songshiwei 2018.7.2


import os
import threading

from PySide.QtGui import *


class MDragEdit(QLineEdit):
    def __init__(self, parent):
        super(MDragEdit, self).__init__(parent)
        self.setAcceptDrops(True)

    def dragEnterEvent(self, e):
        e.accept()

    def dropEvent(self, e):
        path = str(e.mimeData().urls()[0].path())[1:]
        self.setText(path)


class MTransCodeWidget(QWidget):
    def __init__(self):
        super(MTransCodeWidget, self).__init__()
        self.mov_format = ['.mov']
        self.pic_format = ['.jpg', '.tif']
        self.other_format = ['.mp4']

        self.layout = QFormLayout()
        self.input_edit = MDragEdit(self)
        self.layout.addRow(u'输入路径', self.input_edit)
        self.out_edit = MDragEdit(self)
        self.layout.addRow(u'输出路径', self.out_edit)
        self.format_dicts = {
            'h.264': 'libx264',
            'Apple ProRes422': 'prores_aw',
            'Apple ProRes444': 'prores_ks',
            'Dnxhd': 'dnxhd'}
        self.code_format = QComboBox()
        self.code_format.addItems(self.format_dicts.keys())
        self.code_format.currentIndexChanged.connect(self.find_encode)
        self.layout.addRow(u'转码格式', self.code_format)
        self.water_mask = MDragEdit(self)
        self.layout.addRow(u'水印文件', self.water_mask)
        self.start_button = QPushButton(u'开始转码')
        self.layout.addRow(u'    ', self.start_button)
        self.setLayout(self.layout)
        self.start_button.clicked.connect(self.start)

    def find_encode(self):
        n = self.format_dicts.get(self.code_format.currentText()) if self.format_dicts.get(
            self.code_format.currentText()) else None
        return n

    @staticmethod
    def average_split_list(in_list, split_num):

        out_list = []
        while len(in_list):
            counter = 0
            thread_num = split_num
            while counter < thread_num - 1:
                if counter < len(in_list):
                    counter = counter + 1
                else:
                    counter = counter - 1
                    break
            temp_num = counter + 1
            temp_list = in_list[0:temp_num]
            # print "This is tempList : %s" % tempList
            del in_list[0:temp_num]
            out_list.append(temp_list)
        return out_list

    def start(self):

        def exec_cmd(cmd_line):
            try:
                os.system(cmd_line)
            except Exception as e:
                print "%s\t error running \r\n%s" % (cmd_line, e)

        ffmpeg_path = os.path.dirname(os.path.abspath(__file__)) + '\\ffmpeg.exe'
        water_marker = self.water_mask.text().replace('/', '\\')
        file_code = self.find_encode()
        input_path = self.input_edit.text()
        out_path = self.out_edit.text()
        mov_filters = ['overlay=-0:0',
                       'format=yuv422p',
                       'fps=24.00',
                       ]
        ffmpeg_cmd_mov = '{ffmpeg_path} -i {input_mov} -i {water_marker} -c:v {file_code} -b:v 440M -filter_complex ' \
                         '{mov_filters} -y {output_mov}'
        ffmpeg_cmd_pic = '{ffmpeg_path} -i {input_mov} -i {water_marker} -filter_complex overlay=-0:0 -y {output_mov}'

        other_cmd = '{ffmpeg_path} -i {input_mov} -i {water_marker} -c:v {file_code} -c:a copy -b:v 440M ' \
                    '-filter_complex {mov_filters} -y <output_mov>'

        tmp_cmd = ''
        cmd_list = []
        file_list = []
        dest_path = os.path.join(out_path, input_path.split('\\')[-1])
        if not os.path.exists(dest_path):
            os.makedirs(dest_path)
        for root, dirs, file_names in os.walk(input_path):
            for filename in file_names:
                file_list.append(filename)
                input_mov = os.path.join(root, filename).replace('/', '\\')
                output_mov = os.path.join(dest_path, filename).replace('/', '\\')
                ext = os.path.splitext(filename)[-1]
                if ext in self.mov_format:
                    tmp_cmd = ffmpeg_cmd_mov.format(ffmpeg_path=ffmpeg_path, input_mov=input_mov,
                                                    water_marker=water_marker,
                                                    mov_filter=','.join(mov_filters), output_mov=output_mov,
                                                    file_code=file_code)

                if ext in self.pic_format:
                    tmp_cmd = ffmpeg_cmd_pic.format(ffmpeg_path=ffmpeg_path, input_mov=input_mov,
                                                    water_marker=water_marker, output_mov=output_mov)

                if ext in self.other_format:
                    tmp_cmd = other_cmd.format(ffmpeg_path=ffmpeg_path, input_mov=input_mov, water_marker=water_marker,
                                               file_code=file_code, output_mov=output_mov,
                                               mov_filte=','.join(mov_filters))

                cmd_list.append(tmp_cmd)

        concurrency_num = 40
        # define threads_pool
        threads_pool = list(
            threading.Thread(target=exec_cmd, args=(str(cmd.decode("utf-8").encode("gbk")),)) for cmd in cmd_list)
        # average split the threads_pool
        threads_pool_split = MTransCodeWidget.average_split_list(threads_pool, concurrency_num)
        for thread_part in threads_pool_split:
            for th in thread_part:
                th.start()
            for t in thread_part:
                t.join()


if __name__ == '__main__':
    import sys

    app = QApplication(sys.argv)
    win = MTransCodeWidget()
    win.resize(500, 300)
    win.show()
    sys.exit(app.exec_())
