# -*- coding: utf-8 -*-
###################################################################
# Author: Song shiwei
# Date  : 2018.10
###################################################################
import re

from PySide.QtGui import *
from unipath.path import Path
from buildtrack.m_table_model import MyTableModel
import util


class BuildTrackAction(QAction):
    def __init__(self):
        super(BuildTrackAction, self).__init__('New Build Track', None)
        self.trackItemList = []
        self.project = []
        self.selected_sequence = []
        self.shot_list = []
        self.triggered.connect(self.init_ui)
        self.pattern = {
            'mov': 'sg_path_to_movie',
            'seq': 'sg_path_to_frames'
        }
        self.register_interest()

    def register_interest(self):
        import hiero_util
        hiero_util.hiero_register_interest(self.event_handler())

    def event_handler(self, event):
        """
        右键菜单触发函数
        :param event:
        :return: None
        """
        import hiero_util
        event.menu.addAction(self)
        clip_name = hiero_util.get_selection()
        items = list(clip_name)

        old_shot_pattern = re.compile('^s[0-9]{3}_c[0-9]{4}$')
        new_shot_pattern = re.compile('^[A-Z]{3,4}_c[0-9]{4}$')

        self.trackItemList = [i for i in items if
                              re.match(old_shot_pattern, i.name()) or re.match(new_shot_pattern, i.name())]
        self.project = self.trackItemList[0].project().name()
        self.selected_sequence = self.trackItemList[0].sequence()
        self.shot_list = [i.name() for i in self.trackItemList]

    def init_ui(self):
        """
        init ui
        :return: None
        """
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
        """

        :param index:
        :return:
        """
        step_config = Path(__file__).parent.child('config').child('step_config.json')
        raw_data = util.open_json(step_config)
        step_data = raw_data.get('step_data')
        fmt = raw_data.get('ext')

        if index < 0: return
        type_grp = self.type_group_combobox.currentText()
        self.type_combobox.clear()
        self.formatComboBox.clear()
        self.type_combobox.addItems(step_data.get(type_grp))
        self.formatComboBox.addItems(fmt.get(type_grp))

    def selected_result(self, result_list):
        """

        :param result_list:
        :return:
        """
        selected_version = []
        for model_index in self.table_view.selectionModel().selectedRows():
            version_name = model_index.child(model_index.row(), 1).data()
            for version in result_list:
                if version.get('version') == version_name:
                    selected_version.append(version)
        return selected_version

    def data_parse(self, shot_list, pro, type_group, step_type):
        """

        :param shot_list:
        :param pro:
        :param type_group:
        :param step_type:
        :return:
        """
        data = []
        for shot in shot_list:
            resource_data = util.find_resource_data(pro, shot, step_type)
            if resource_data:
                for resource in resource_data:
                    if resource.get('sg_mrversions'):
                        sorted_versions = sorted(resource.get('sg_mrversions'), key=lambda y: y.get('name'))
                        max_version_id = sorted_versions[-1].get(id)
                        result = util.get_element_or_dailes_data(shot, type_group, max_version_id,
                                                                 self.formatComboBox.currentText())
                        data.append(result)
        return data

    def slot_parse(self):
        """

        :return:
        """

        self.table_view.selectionModel().clear()
        self.result_list = self.data_parse(self.shot_list,
                                           pro=self.project_line.text(),
                                           type_group=self.type_group_combobox.currentText(),
                                           step_type=self.type_combobox.currentText())
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
        """

        :return:
        """
        import hiero_util
        if len(self.table_view.selectionModel().selectedRows()) == 0:
            QMessageBox.critical(self, u'提示', u'你没有选中任何要导入的版本！')
            return False

        selected_version = self.selected_result(self.result_list)
        current_project = hiero_util.get_project()
        new_track = hiero_util.get_new_track(self.type_combobox.currentText())
        hiero_util.add_track(self.selected_sequence, new_track)

        for shot in selected_version:
            new_bin = hiero_util.create_new_bin(current_project, shot)

            already_in_clips = hiero_util.get_already_in_cilps(new_bin)
            new_bin_flag, new_clip = hiero_util.check_build_repeated(shot,
                                                                     already_in_clips,
                                                                     pattern=self.pattern.get(
                                                                         self.formatComboBox.currentText()))
            if not new_bin_flag:
                break
            elif new_bin_flag:
                new_clip = hiero_util.create_new_clip_in_new_bin(shot,
                                                                 type_group=self.type_group_combobox.currentText(),
                                                                 pattern=self.pattern.get(
                                                                     self.formatComboBox.currentText()))
            if new_clip:
                hiero_util.create_track_item(shot, new_clip, new_bin, new_track,
                                             track_item_list=self.trackItemList)
            else:
                print u"文件不存在或者"
