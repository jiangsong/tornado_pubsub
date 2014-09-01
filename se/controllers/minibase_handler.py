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
from piwikapi.tracking import PiwikTracker
from piwikapi.tests.request import FakeRequest
from se import config

class MiniBaseHandler(web.RequestHandler,
    TrustIPAuth):
    def __init__(self, application, request, **kwargs):
        web.RequestHandler.__init__(self, application, request, **kwargs)
        self.request.remote_ip = self.request.headers.get("X-Forwarded-For", self.request.remote_ip)

        if self.application.enable_piwik:
            headers = {
                'HTTP_USER_AGENT': self.request.headers.get("User-Agent", "Default"),
                'REMOTE_ADDR': self.request.remote_ip,
                #'HTTP_REFERER': 'http://referer.com/somewhere/',
                'HTTP_ACCEPT_LANGUAGE': 'en-US',
                'SERVER_NAME': self.request.host,
                'PATH_INFO': self.request.path,
                'QUERY_STRING': self.request.query,
                'HTTPS': False,
            }
            request = FakeRequest(headers)
            self.piwik = PiwikTracker(config.get("piwik", "app_id", 1), request)
            self.piwik.set_api_url(config.get("piwik", "app_url", ""))
            self.piwik.set_ip(self.request.remote_ip) # Optional, to override the IP
            self.piwik.set_token_auth(config.get("piwik", "token_auth", ""))  # Optional, to override the IP
            self.tracked = False

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

    def on_finish(self):
        """Called after the end of a request.

        Override this method to perform cleanup, logging, etc.
        This method is a counterpart to `prepare`.  ``on_finish`` may
        not produce any output, as it is called after the response
        has been sent to the client.
        """
        if not self.application.enable_piwik:
            return

        if not self.tracked:
            title = self.request.path.replace("/", ".")
            if title.startswith("."):
                title = title[1:]
            self.piwik.do_track_page_view(title)

