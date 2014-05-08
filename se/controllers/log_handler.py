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
from se.pubsub import sig_logs
import traceback
import time


class LogHandler(web.RequestHandler):
    def get(self):
        """
        响应get请求，用以查询统计数量
        :return:
        """
        self.render("log/logs.html", logs=reversed(self.application.log_caches))

    @web.asynchronous
    def post(self):
        """
        @summary: 响应日志系统

        @return:
        """
        self.uuid = self.get_argument("cursor", None)
        sig_logs.connect(self.on_new_logs)

    def on_new_logs(self, sender, **kwargs):
        """
        响应新日志的回调函数

        :param sender:
        :param kwargs:
        :return:
        """
        #
        # Closed client connection
        #
        if self.request.connection.stream.closed() or self._finished:
            traceback.print_stack()
            return

        logs = kwargs.get("new_log", None)
        if logs is None:
            return
        self.finish(dict(logs=logs))

class WatchHandler(web.RequestHandler):
    def get(self):
        """
        响应get请求，用以查询统计数量
        :return:
        """
        if len(self.application.pub_sub.sub_dicts) <= 0:
            self.finish("no new watch items")
            return

        current_time = time.time()
        for k, (chanel_id, start_time, _) in self.application.pub_sub.sub_dicts.iteritems():
            str = "ChanelID:%s -- UsedTime:%d<BR>" % (chanel_id, current_time - start_time)
            self.write(str)
