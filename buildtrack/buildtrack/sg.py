#!/usr/bin/env python
# -*- coding: utf-8 -*-


from shotgun_api3 import Shotgun
from unipath.path import Path
import json

CONFIG_PATH = Path(__file__).parent.child('sg_config.json')


def connect():
    with open(CONFIG_PATH, 'r') as f:
        config_data = json.load(f)
        sg = Shotgun(config_data.get('DEFAULT_SERVER'), config_data.get('DEFAULT_SCRIPT'), config_data.get('DEFAULT_KEY'))
    return sg


if __name__ == '__main__':
    connect()
