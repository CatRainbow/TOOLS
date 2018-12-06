#!/usr/bin/env python
# encoding: utf-8
# create_time: 2018.10
__author__ = 'Song shiwei'

import hiero.core as hcore
import hiero.ui as hui


def hiero_register_interest(hand_func):
    hcore.events.registerInterest("kShowContextMenu/kTimeline", hand_func)
    hcore.events.registerInterest("kShowContextMenu/kSpreadsheet", hand_func)


def add_track(seq, new_track):
    seq.addTrack(new_track)


def get_selection():
    return hui.activeView().selection()


def get_new_track(type_name):
    return hcore.VideoTrack('{}'.format(type_name))


def get_project():
    return hcore.projects()[-1]


def create_new_bin(project, shot):
    bin_name = shot.get('version').split('_')[0]
    new_bin = next((x for x in project.clipsBin().bins() if
                    x.name() == '{}_imported_clips'.format(bin_name)), None)
    if not new_bin:
        new_bin = hcore.Bin('{}_imported_clips'.format(bin_name))
        project.clipsBin().addItem(new_bin)
    return new_bin


def get_already_in_cilps(new_bin):
    return [x for x in new_bin.clips() if x.name().decode('utf-8') == shot.get('version')[:-7]]


def path_change(path):
    path.replace('/', '\\')


def check_build_repeated(shot, already_in_clips, pattern):
    new_clip = None
    new_bin_flag = True
    if len(already_in_clips) > 0:
        for clip in already_in_clips:
            if path_change(clip) == path_change(
                    shot.get(pattern)):
                print 'already in bin'
                new_bin_flag = False
                new_clip = clip
    return new_bin_flag, new_clip


def create_new_clip_in_new_bin(shot, type_group, pattern):
    new_clip = None
    if type_group == 'dailies':
        new_media_source = hcore.MediaSource(shot.get(pattern)) if shot.get(pattern) else None
        new_clip = hcore.Clip(new_media_source) if new_media_source else None

    elif type_group == 'element':
        new_media_source = hcore.MediaSource(shot.get('file'))
        new_clip = hcore.Clip(new_media_source) if new_media_source else None
    return new_clip


def create_track_item(shot, new_clip, new_bin, new_track, track_item_list):
    new_clip.setFramerate(
        hui.activeSequence().framerate() if hui.activeSequence() else hcore.TimeBase(24.0))
    new_bin_item = hcore.BinItem(new_clip)
    new_bin.addItem(new_bin_item)

    new_track_item = new_track.createTrackItem(shot.get('shot'))
    new_track_item.setSource(new_clip)

    for ti in track_item_list:
        duration = ti.duration()
        new_track_item.setSourceOut(new_track_item.sourceIn() + duration - 1)
        new_track_item.setTimelineIn(ti.timelineIn())
        new_track_item.setTimelineOut(ti.timelineIn() + duration - 1)
        new_track.addTrackItem(new_track_item)
    print 'create trackitem'
