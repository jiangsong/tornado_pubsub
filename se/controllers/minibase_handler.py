# coding=utf-8

#
# Copyright 2013 nava
#
# Licensed under the Apache License, Version 2.0 (the "License"); you may
# not use this file except in compliance with the License. You may obtain
# a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations
# under the License.

from tornado import web
import json
import os
import time
from se.auth import TrustIPAuth

class MiniBaseHandler(web.RequestHandler,
    TrustIPAuth):
    def __init__(self, application, request, **kwargs):
        web.RequestHandler.__init__(self, application, request, **kwargs)
        self.request.remote_ip = self.request.headers.get("X-Forwarded-For", self.request.remote_ip)

    def set_default_headers(self):
        self.set_header("Access-Control-Allow-Credentials", "true")
        self.set_header("Access-Control-Allow-Methods", "GET,PUT,POST,DELETE,OPTIONS")
        self.set_header("Access-Control-Allow-Headers",
            "Content-Type, Depth, User-Agent, X-File-Size, X-Requested-With, X-Requested-By, If-Modified-Since, X-File-Name, Cache-Control")

    def remote_get(self, path, call_back):
        """
        @summary: 获取指定文件远程路径文件

        @param path: 远程文件名称
        @param call_back: 获取后回调函数地址

        @return:
        """
        raise NotImplementedError("Should have implemented this" )

    def send_result(self, status, **kwargs):
        """
        @summary: 输出结果

        @param status: 操作成功标志
        @param **kwargs: 辅助描述内容

        @return:
        """
        ret_json = {"status": status}
        for key, value in kwargs.iteritems():
            ret_json[key] = value


        callbackParae = self.get_argument("callbackparam", None)
        if callbackParae is None:
            self.set_header('Content-Type', 'application/json')
            self.finish(json.dumps(ret_json))
            return
        #
        # 使用jsonp实现跨域返回
        #
        self.set_header('Content-Type', 'text/plain')
        self.finish(callbackParae + '(' + json.dumps(ret_json) + ')')

