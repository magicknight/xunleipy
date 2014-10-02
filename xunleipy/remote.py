# -*- encoding:utf-8 -*-
from __future__ import absolute_import, unicode_literals
import json

from six.moves.urllib.parse import quote

from .base import XunLei

REMOTE_BASE_URL = 'http://homecloud.yuancheng.xunlei.com/'
DEFAULT_V = 2
DEFAULT_CT = 0


class ListType:
    downloading = 0
    finished = 1
    recycle = 2
    failed = 3


class XunLeiRemote(XunLei):

    def __init__(self, username, password):
        super(XunLeiRemote, self).__init__(username, password)
        if not self.is_login:
            self.login()

    def _request(self, method, url, **kwargs):
        url = REMOTE_BASE_URL + url

        if 'params' not in kwargs:
            kwargs['params'] = {}
        if 'data' not in kwargs:
            kwargs['data'] = {}
        if isinstance(kwargs['data'], dict):
            data = json.dumps(kwargs['data'], ensure_ascii=False)
            data = data.encode('utf-8')
            kwargs['data'] = data

        res = self.session.request(
            method=method,
            url=url,
            **kwargs
            )
        res.raise_for_status()

        data = res.json()

        if data['rtn'] != 0:
            print('request for %s failed, code:%s', url, data['rtn'])

        return data

    def _get(self, url, **kwargs):
        return self._request(
            method='get',
            url=url,
            **kwargs
        )

    def _post(self, url, **kwargs):
        return self._request(
            method='post',
            url=url,
            **kwargs
        )

    def get_remote_peer_list(self):
        '''
        listPeer 返回列表
        {
            "rtn":0,
            "peerList": [{
                "category": "",
                "status": 0,
                "name": "GUNNER_HOME",
                "vodPort": 43566,
                "company": "XUNLEI_MIPS_BE_MIPS32",
                "pid": "8498352EB4F5208X0001",
                "lastLoginTime": 1412053233,
                "accesscode": "",
                "localIP": "",
                "location": "\u6d59\u6c5f\u7701  \u8054\u901a",
                "online": 1,
                "path_list": "C:/",
                "type": 30,
                "deviceVersion": 22083310
            }]
        }
        '''

        params = {
            'type': 0,
            'v': DEFAULT_V,
            'ct': 2
        }
        res = self._get('listPeer', params=params)
        return res['peerList']

    def get_remote_task_list(
            self, peer_id, list_type=ListType.downloading, pos=0, number=10):
        '''
        list 返回列表
        {
            "recycleNum": 0,
            "serverFailNum": 0,
            "rtn": 0,
            "completeNum": 34,
            "sync": 0,
            "tasks": [{
                "failCode": 15414,
                "vipChannel": {
                    "available": 0,
                    "failCode": 0,
                    "opened": 0,
                    "type": 0,
                    "dlBytes": 0,
                    "speed": 0
                },
                "name": "Blablaba",
                "url": "magnet:?xt=urn:btih:5DF6B321CCBDEBE1D52E8E15CBFC6F002",
                "speed": 0,
                "lixianChannel": {
                    "failCode": 0,
                    "serverProgress": 0,
                    "dlBytes": 0,
                    "state": 0,
                    "serverSpeed": 0,
                    "speed": 0
                },
                "downTime": 0,
                "subList": [],
                "createTime": 1412217010,
                "state": 8,
                "remainTime": 0,
                "progress": 0,
                "path": "/tmp/thunder/volumes/C:/TDDOWNLOAD/",
                "type": 2,
                "id": "39",
                "completeTime": 0,
                "size": 0
            },
            ...
            ]
        }
        '''

        params = {
            'pid': peer_id,
            'type': list_type,
            'pos': pos,
            'number': number,
            'needUrl': 1,
            'v': DEFAULT_V,
            'ct': DEFAULT_CT
        }
        res = self._get('list', params=params)
        return res['tasks']

    def check_url(self, pid, url_list):
        '''
        urlCheck 返回数据
        {
            "rtn": 0,
            "taskInfo": {
                "failCode": 0,
                "name": ".HDTVrip.1024X576.mkv",
                "url": "ed2k://|file|%E6%B0%",
                "type": 1,
                "id": "0",
                "size": 505005442
            }
        }
        '''
        task_list = []
        for url in url_list:
            params = {
                'pid': pid,
                'url': url,
                'type': 1,
                'v': DEFAULT_V,
                'ct': DEFAULT_CT
            }
            res = self._get('urlCheck', params=params)

            if res['rtn'] == 0:
                task_info = res['taskInfo']
                task_list.append({
                    'url': task_info['url'],
                    'name': task_info['name'],
                    'filesize': task_info['size'],
                    'gcid': '',
                    'cid': ''
                })
            else:
                print(
                    'url [%s] check failed, code:%s.',
                    url,
                    task_info['failCode']
                )

        return task_list

    def add_tasks_to_remote(self, pid, path='C:/TDDOWNLOAD/', task_list=[]):
        '''
        post data:
        {
            "path":"C:/TDDOWNLOAD/",
            "tasks":[{
                "url":"ed2k://|file|%E6%B0%B8%E6%81%92.Forever...",
                "name":"永恒.Forever.S01E02.中英字幕.WEB-HR.mkv",
                "gcid":"",
                "cid":"",
                "filesize":512807020
            }]
        }

        return data:
        {
            "tasks": [{
                "name": "\u6c38\u6052.Fore76.x264.mkv",
                "url": "ed2k://|file|%E6%B0%B8%E6%81%92",
                "result": 202,
                "taskid": "48",
                "msg": "repeate_taskid:48",
                "id": 1
            }],
            "rtn": 0
        }
        '''

        if len(task_list) == 0:
            return []

        params = {
            'pid': pid,
            'v': DEFAULT_V,
            'ct': DEFAULT_CT,
        }

        data = {
            'path': path,
            'tasks': task_list
        }

        headers = {
            'Content-Type': 'application/x-www-form-urlencoded'
        }

        data = json.dumps(data)
        data = quote(data)
        data = 'json=' + data

        res = self._post(
            'createTask',
            params=params,
            data=data,
            headers=headers
        )

        return res