#!/usr/bin/env python
# encoding: utf-8
# create_time: 2018.10
import json

import os

from buildtrack.sg import sg

SHOTGUN = sg.connect()
EXT_PATTERN = {
    'mov': 'sg_path_to_movie',
    'seq': 'sg_path_to_frames'
}


def open_json(file_path):
    """
    open json file
    :param file_path: the path of json file
    :return: json data type:dict
    """
    with open(file_path, 'r') as f:
        raw_data = json.loads(f)
    return raw_data


def finder_version(version_id):
    """

    :param version_id:
    :return:
    """
    sg_filter = [['id', 'is', version_id]]
    query_filed = ['code', 'sg_mdailies', 'sg_melement',
                   'sg_mresource', 'sg_mtask.Task.entity',
                   'sg_mtask.Task.step.Step.short_name']

    m_version = SHOTGUN.find_one('CustomEntit y11', sg_filter, query_filed)
    return m_version


def find_dailies(my_version_id, ext_format):
    """

    :param my_version_id:
    :param ext_format:
    :return:
    """
    m_version = finder_version(my_version_id)
    if m_version:
        dailies = from_version_get_dailies_and_file(m_version, ext_format)
        return dailies


def find_element(my_version_id):
    """

    :param my_version_id:
    :return:
    """
    m_version = finder_version(my_version_id)
    if m_version:
        element = from_version_get_element(m_version)
        return element


def from_version_get_dailies_and_file(m_version, ext_format):
    """

    :param m_version:
    :param ext_format:
    :return:
    """
    if m_version.get('sg_mdailies'):
        sg_filter = [['id', 'is', m_version.get('sg_mdailies').get('id')]]
        query_filed = ['code', 'sg_path_to_movie', 'sg_path_to_frames', 'created_at']
        dailies = SHOTGUN.find_one('Version', sg_filter, query_filed)

        file_path = dailies.get(EXT_PATTERN.get(ext_format)).replace('####', '1001') if dailies.get(
            EXT_PATTERN.get(ext_format)) else None

        if file_path and os.path.isfile(file_path):
            temp_dict = dict(version='{}_{}'.format(m_version.get('sg_mresource').get('name'), m_version.get('code')),
                             file=file_path)
            dailies.update(temp_dict)
            return dailies, file_path


def from_version_get_element(m_version):
    """

    :param m_version:
    :return:
    """

    if m_version.get('sg_melement') and m_version.get('sg_mresource'):

        root = (m_version.get('sg_melement').get('local_path') + 'fullres').replace('\\', '/')
        file_list = [os.path.join(x, m) for x, y, z in os.walk(root) for m in z if len(z) > 0]

        if len(file_list) > 0:
            element = dict(
                version='{}_{}'.format(m_version.get('sg_mresource').get('name'), m_version.get('code')),
                step=m_version.get('sg_mtask.Task.step.Step.short_name'),
                parten='{}-{}'.format(1001, 1001 + len(file_list) - 1),
                file='.'.join([file_list[-1].split('.')[0], '%04d', file_list[-1].split('.')[-1]])
            )
            return element


def find_resource_data(pro, shot, step_type):
    filters = [
        ['project.Project.name', 'is', pro],
        ['sg_task.Task.entity.Shot.code', 'is', shot],
        ['sg_task.Task.step.Step.short_name', 'is', step_type]
    ]
    resource_data = SHOTGUN.sg.find('CustomEntity10', filters, ['code', 'sg_mrversions'])
    return resource_data


def get_element_or_dailes_data(shot, type_group, max_mversion_id, ext_format=None):
    if type_group == 'dailies':
        data = find_dailies(max_mversion_id, ext_format)
        if data:
            dailies = dict(shot=shot).update(data)
            return dailies
    elif type_group == 'element':
        data = find_element(max_mversion_id)
        if data:
            element = dict(shot=shot).update(data)
            return element
