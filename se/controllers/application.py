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
from se import config, logger
from pubsub_handler import PubHandler, SubHandler, PubsHandler, SubsHandler
from log_handler import LogHandler
import os
import uuid
import tornado
import time
from se.pubsub import PubSubManager, sig_logs


class SEApplication(web.Application):
    """
    @summary: Mysql数据连接应用管理模块
    """

    def __init__(self, handlers, **settings):
        web.Application.__init__(self, handlers, **settings)
        #
        # 系统记录的日志缓存
        #
        self.log_caches = []
        self.log_size = 100

        #
        # 缓存系统
        #
        self.pub_sub = PubSubManager(self)
        self.trust_ips = ["127.0.0.1"]

    def init(self):
        """
        @summary: 初始化所有部分

        @return: 初始化成功返回
        """
        #
        # 初始化处理句柄
        #
        ret = self._init_handlers()
        if not ret:
            return ret

        #
        # 初始化redis监控句柄
        #
        self.pub_sub.init()
        
        if not config.has_section("system"):
            return ret
        if not config.has_option("system", "trust_ips"):
            return ret
        
        trust_ips = config.get("system", "trust_ips", "0")
        trust_ip_list = trust_ips.split('|')
        for ip in trust_ip_list:
            if ip in self.trust_ips:
                continue
            self.trust_ips.append(ip)
        return ret

    def _init_handlers(self):
        """
        @summary: 加载应用程序模块

        @return: 初始化成功返回True，否则返回False
        """


        handlers = []
        if config.has_section("services"):
            if config.has_option("services", "enable_pub") and \
                            config.get("services", "enable_pub", "0") == "1":
                handlers.append(((r"/sub/(.+)"), SubHandler))
                handlers.append(((r"/pub/(.+)"), PubHandler))
                
                #
                # 批量订阅支持
                #
                handlers.append(((r"/subs"), SubsHandler))
                handlers.append(((r"/pubs"), PubsHandler))

        handlers.append(((r"/logs"), LogHandler))
        host_pattern = ".*$"
        if len(handlers) <= 0:
            return False

        self.add_handlers(host_pattern, handlers)
        return True

    def log_request(self, handler):
        """
        @summary: 重构每个HTTP请求统计模块，进行计数统计并在前端进行显示

        By default writes to the python root logger.  To change
        this behavior either subclass Application and override this method,
        or pass a function in the application settings dictionary as
        ``log_function``.
        """
        if "log_function" in self.settings:
            self.settings["log_function"](handler)
            return

        #
        # 解析处理服务器的
        #
        if handler.request.method == "POST" and handler.request.uri.lower() == "/logs":
            return

        if handler.get_status() < 400:
            log_method = logger.info
        elif handler.get_status() < 500:
            log_method = logger.warning
        else:
            log_method = logger.error
        request_time = 1000.0 * handler.request.request_time()
        log_msg = "%d %s %.2fms" % ( handler.get_status(),
                   handler._request_summary(), request_time)
        log_method(log_msg)

        log_item = {
            "id": str(uuid.uuid4()),
            "time": self.format_time(handler.request._start_time),
            'uri' : handler.request.uri,
            'method': handler.request.method,
            'status' : handler.get_status(),
            'RequestTime': "%.2f" % request_time,
            'UserAgent': handler.request.headers.get("User-Agent", ""),
            "body": handler.request.host + " " + handler._request_summary(),
        }

        #
        # 时间 url
        #  2013-07-18 17:40:25.903 /tasks/domain_query 200 203ms 0kb AppEngine-Google; (+http://code.google.com/appengine)
        # to_basestring is necessary for Python 3's json encoder,
        # which doesn't accept byte strings.
        #
        log_item["html"] = tornado.escape.to_basestring(
            handler.render_string("log/log.html", log=log_item))

        #
        # 缓存到内部系统中
        #
        self.log_caches.append(log_item)
        if len(self.log_caches) > self.log_size:
            self.log_caches = self.log_caches[-self.log_size:]

        sig_logs.send(new_log=[log_item])

    def format_time(self, value):
        """
        @summary 获取开始执行时间
        """
        t_value = time.localtime(value)
        t = time.strftime("%Y-%m-%d %H:%M:%S", t_value)
        s = "%s.%03d" % (t, int(round(value * 1000)) % 1000)
        return s