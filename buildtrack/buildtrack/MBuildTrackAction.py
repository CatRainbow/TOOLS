# -*- coding: utf-8 -*-
###################################################################
# Author: Song shiwei
# Date  : 2018.10
###################################################################
import os
import re
import sg

from PySide.QtGui import *
from PySide.QtCore import *
import hiero.core as hcore
import hiero.ui as hui


class BuildTrackAction(QAction):
    def __init__(self):
        super(BuildTrackAction, self).__init__('New Build Track', None)
        self.trackItemList = []
        self.project = []
        self.selected_sequence = []
        self.shot_list = []
        hcore.events.registerInterest("kShowContextMenu/kTimeline", self.event_handler)
        hcore.events.registerInterest("kShowContextMenu/kSpreadsheet", self.event_handler)
        self.triggered.connect(self.init_ui)
        self.sg = sg.connect()
        self.pattern = {
            'mov': 'sg_path_to_movie',
            'seq': 'sg_path_to_frames'
        }

    def event_handler(self, event):
        event.menu.addAction(self)
        clip_name = hui.activeView().selection()
        items = list(clip_name)

        old_shot_pattern = re.compile('^s[0-9]{3}_c[0-9]{4}$')
        new_shot_pattern = re.compile('^[A-Z]{3,4}_c[0-9]{4}$')

        self.trackItemList = [i for i in items if
                              re.match(old_shot_pattern, i.name()) or re.match(new_shot_pattern, i.name())]
        self.project = self.trackItemList[0].project().name()
        self.selected_sequence = self.trackItemList[0].sequence()
        self.shot_list = [i.name() for i in self.trackItemList]

    def init_ui(self):
        window = QDialog()
        self.project_line = QLineEdit()
        self.project_line.setText(self.project)
        self.type_group_combobox = QComboBox()
        self.type_group_combobox.addItems(['dailies', 'element'])
        self.type_group_combobox.currentIndexChanged.connect(self.slot_update_type_combobox)

        self.type_combobox = QComboBox()
        self.type_combobox.addItems(['lay', 'ani', 'efx', 'lgt', 'pcmp', 'prep', 'cmp', 'plt'])
        self.format_label = QLabel('Format:')
        self.formatComboBox = QComboBox()
        self.formatComboBox.addItems(['seq', 'mov'])

        database_lay = QHBoxLayout()
        database_lay.addWidget(QLabel('Project:'))
        database_lay.addWidget(self.project_line)
        database_lay.addWidget(QLabel('Type Group:'))
        database_lay.addWidget(self.type_group_combobox)
        database_lay.addSpacing(10)
        database_lay.addWidget(QLabel('Pipeline:'))
        database_lay.addWidget(self.type_combobox)
        database_lay.addSpacing(10)
        database_lay.addSpacing(10)
        database_lay.addWidget(self.format_label)
        database_lay.addWidget(self.formatComboBox)
        database_lay.addStretch()

        self.table_view = QTableView()
        # self.header = ['Track Item Name', 'Incoming Version', 'Update Time']
        self.header = ['Track Item Name', 'Incoming Version']
        self.data = [(x, '--') for x in self.shot_list]
        self.table_model = MyTableModel(self, self.data, self.header)
        self.table_view.setModel(self.table_model)
        self.table_view.resizeColumnsToContents()
        self.table_view.setSelectionBehavior(QTableView.SelectRows)

        font = QFont('Courier New', 10)
        self.table_view.setFont(font)
        self.table_view.setSortingEnabled(True)

        parse_button = QPushButton(self.tr('Parse'))
        parse_button.clicked.connect(self.slot_parse)
        # self.parseButton.setEnabled(False)

        self.build_button = QPushButton(self.tr('Build'))
        self.build_button.clicked.connect(self.slot_build)
        self.build_button.setEnabled(False)
        button_lay = QHBoxLayout()
        button_lay.addWidget(parse_button)
        button_lay.addWidget(self.build_button)

        layout = QVBoxLayout()
        layout.addLayout(database_lay)
        layout.addLayout(button_lay)
        layout.addWidget(self.table_view)
        window.setLayout(layout)
        window.setWindowTitle('New Build Track')
        window.resize(800, 500)
        window.exec_()

    def slot_update_type_combobox(self, index):
        data = {
            'dailies': ['efx', 'pcmp', 'ani', 'mpt', 'lay', 'prep', 'lgt', 'cmp', 'plt'],
            'element': ['prep', 'cmp']
        }
        fmt = {
            'dailies': ['mov', 'seq'],
            'element': ['seq']
        }
        if index < 0: return
        type_grp = self.type_group_combobox.currentText()

        self.type_combobox.clear()
        self.formatComboBox.clear()
        self.type_combobox.addItems(data.get(type_grp))
        self.formatComboBox.addItems(fmt.get(type_grp))

    def selected_result(self, result_list):
        selected_version = []
        for model_index in self.table_view.selectionModel().selectedRows():
            version_name = model_index.child(model_index.row(), 1).data()
            for version in result_list:
                if version.get('version') == version_name:
                    selected_version.append(version)
        result = selected_version if len(selected_version) > 0 else None
        return result

    def find_dailies(self, my_version_id, ext_format):
        m_version = self.sg.find_one('CustomEntity11', [['id', 'is', my_version_id]],
                                     ['code', 'sg_mdailies', 'sg_melement', 'sg_mresource'])
        if m_version and m_version.get('sg_mdailies'):
            dailies = self.sg.find_one('Version', [['id', 'is', m_version.get('sg_mdailies').get('id')]],
                                       ['code', 'sg_path_to_movie', 'sg_path_to_frames', 'created_at'])
            file_path = dailies.get(self.pattern.get(ext_format)).replace('####', '1001') if dailies.get(
                self.pattern.get(ext_format)) else None

            if dailies and file_path and os.path.isfile(file_path):
                d = {'version': '{}_{}'.format(m_version.get('sg_mresource').get('name'), m_version.get('code')),
                     'file': file_path}

                dailies.update(d)
                return dailies
        else:
            return None

    def find_element(self, my_version_id):
        print '................find element....................'
        element = {}
        m_version = self.sg.find_one('CustomEntity11',
                                     [['id', 'is', my_version_id]],
                                     ['code', 'sg_mdailies', 'sg_melement', 'sg_mresource', 'sg_mtask.Task.entity',
                                      'sg_mtask.Task.step.Step.short_name'])
        print m_version, 'm_version'
        if m_version and m_version.get('sg_melement') and m_version.get('sg_mresource'):
            root = m_version.get('sg_melement').get('local_path') + 'fullres'.replace('\\', '/')
            file_list = [os.path.join(x, m) for x, y, z in os.walk(root) for m in z if len(z) > 0]
            print file_list, 'file_list'
            if len(file_list) > 0:
                element = {
                    'version': '{}_{}'.format(m_version.get('sg_mresource').get('name'), m_version.get('code')),
                    'step': m_version.get('sg_mtask.Task.step.Step.short_name'),
                    'parten': '{}-{}'.format(1001, 1001 + len(file_list) - 1),
                    'file': '.'.join([file_list[-1].split('.')[0], '%04d', file_list[-1].split('.')[-1]])
                }
        return element

    def data_parse(self, shot_list, pro, type_group, type):
        data = []
        for shot in shot_list:
            resource_count = 0
            filters = [
                ['project.Project.name', 'is', pro],
                ['sg_task.Task.entity.Shot.code', 'is', shot],
                ['sg_task.Task.step.Step.short_name', 'is', type]
            ]
            resource_data = self.sg.find('CustomEntity10', filters, ['code', 'sg_mrversions'])
            if resource_data:
                for resource in resource_data:
                    if resource.get('sg_mrversions'):
                        d = {}
                        for x in resource.get('sg_mrversions'):
                            d.update({x.get('name'): x.get('id')})
                        max_mversion = max([x.get('name') for x in resource.get('sg_mrversions')])
                        max_mversion_id = d.get(max_mversion)

                        print '---------result---------', self.find_dailies(max_mversion_id,
                                                                            self.formatComboBox.currentText())
                        if type_group == 'dailies' and self.find_dailies(max_mversion_id,
                                                                         self.formatComboBox.currentText()):
                            shot = shot if resource_count == 0 else ''
                            resource_count += 1
                            dailies = {'shot': shot}
                            dailies.update(self.find_dailies(max_mversion_id, self.formatComboBox.currentText()))

                            data.append(dailies)

                        elif type_group == 'element' and self.find_element(max_mversion_id):
                            shot = shot if resource_count == 0 else ''
                            resource_count += 1
                            element = {'shot': shot}
                            element.update(self.find_element(max_mversion_id))

                            data.append(element)
        return data

    def slot_parse(self):

        self.table_view.selectionModel().clear()
        self.table_model = MyTableModel(self, self.data, self.header)

        self.result_list = self.data_parse(self.shot_list,
                                           pro=self.project_line.text(),
                                           type_group=self.type_group_combobox.currentText(),
                                           type=self.type_combobox.currentText())

        data_list = []
        if self.result_list:
            for shot in self.result_list:
                data_list.append((shot.get('shot'), shot.get('version')))
                self.table_model = MyTableModel(self, data_list, self.header)
                self.table_view.setModel(self.table_model)
                self.table_view.resizeColumnsToContents()

                if self.table_model > 0:
                    self.build_button.setEnabled(True)

    def slot_build(self):
        print '...'

        def path_change(path):
            try:
                path.replace('/', '\\')
            except:
                pass

        if len(self.table_view.selectionModel().selectedRows()) == 0:
            QMessageBox.critical(self, u'提示', u'你没有选中任何要导入的版本！')
            return False

        selected_version = self.selected_result(self.result_list)
        # ---------------build track------------------
        current_project = hcore.projects()[-1]
        new_track = hcore.VideoTrack('{}'.format(self.type_combobox.currentText()))
        self.selected_sequence.addTrack(new_track)

        for shot in selected_version:
            # ----------------build new bin----------------
            bin_name = shot.get('version').split('_')[0]
            new_bin = next((x for x in current_project.clipsBin().bins() if
                            x.name() == '{}_imported_clips'.format(bin_name)), None)

            if new_bin is None:
                new_bin = hcore.Bin('{}_imported_clips'.format(bin_name))
                current_project.clipsBin().addItem(new_bin)

            # ----------------build new clip----------------

            already_in_clips = [x for x in new_bin.clips() if x.name().decode('utf-8') == shot.get('version')[:-7]]
            new_clip = None
            new_bin_flag = True
            if len(already_in_clips) > 0:
                for clip in already_in_clips:
                    if path_change(clip) == path_change(
                            shot.get(self.pattern.get(self.formatComboBox.currentText()))):
                        print 'already in bin'
                        new_bin_flag = False
                        new_clip = clip
                        break
            if new_bin_flag:
                # print shot
                if self.type_group_combobox.currentText() == 'dailies':
                    new_mediasource = hcore.MediaSource(shot.get(self.pattern.get(self.formatComboBox.currentText()))) \
                        if shot.get(self.pattern.get(self.formatComboBox.currentText())) \
                        else None
                    new_clip = hcore.Clip(new_mediasource) if new_mediasource else None

                elif self.type_group_combobox.currentText() == 'element':
                    new_mediasource = hcore.MediaSource(shot.get('file'))
                    new_clip = hcore.Clip(new_mediasource) if new_mediasource else None

            if new_clip:
                new_clip.setFramerate(
                    hui.activeSequence().framerate() if hui.activeSequence() else hcore.TimeBase(24.0))
                new_binitem = hcore.BinItem(new_clip)
                new_bin.addItem(new_binitem)
                print 'create clip'
                # ----------------build trackitem----------------
                new_track_item = new_track.createTrackItem(shot.get('shot'))
                new_track_item.setSource(new_clip)

                for ti in self.trackItemList:
                    duration = ti.duration()
                    new_track_item.setSourceOut(new_track_item.sourceIn() + duration - 1)
                    new_track_item.setTimelineIn(ti.timelineIn())
                    new_track_item.setTimelineOut(ti.timelineIn() + duration - 1)

                    new_track.addTrackItem(new_track_item)
                print 'create trackitem'
            else:
                print u"文件不存在或者"


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

        # def sort(self, col, order):
        #     self.emit


if __name__ == '__main__':
    pass
