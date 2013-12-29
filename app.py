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

__author__ = 'nava'

import tornado.ioloop
import os
import signal
from tornado.options import define, options, parse_command_line
from tornado.httpserver import HTTPServer
from se import logger, config
from se.controllers.application import SEApplication
#
# 全局参数设定
#
define("port", default=8080, help="run on the given port", type=int)
define("config", default=None, help="set the config file", type=str)

http_server = None
is_closing = False


def signal_handler(signum, frame):
    """
    @summary: signal call back function

    @param signum:
    @param frame:
    @return:
    """
    global is_closing
    is_closing = True


def detect_signal():
    global is_closing
    if not is_closing:
        return

    global http_server
    #
    # clean up here
    #
    http_server.stop()
    tornado.ioloop.IOLoop.instance().stop()


def main():
    #
    # 首先解析默认参数
    #
    parse_command_line()

    config_path = options.config
    if not config_path:
        config_path = os.path.join(os.path.dirname(__file__), "pubsub.ini")

    try:
        #
        # 读取配置文件
        #
        config.read(config_path)
    except:
        logger.warning("Invalid config path:%s", config_path)
        return

    root_path = os.path.dirname(os.path.abspath(__file__))
    root_path = os.path.join(root_path, "cache")
    #
    # settings
    #
    settings = {
        'debug'         : False,  # True允许自加载，便于运行中修改代码
        'static_path'   : os.path.join(os.path.dirname(__file__), "www", "statics"),
        'template_path' : os.path.join(os.path.dirname(__file__), "www", "templates"),
        'root_path'     : root_path,
        "xheaders"      : True,
    }
    handlers = [
        (r"/(favicon\.ico)", tornado.web.StaticFileHandler, dict(path=settings['static_path'])),
        (r"/statics/(.*)/?", tornado.web.StaticFileHandler, dict(path=settings['static_path'])),
        ]

    tornado_app = SEApplication(
        handlers=handlers,
        **settings
        )

    logger.info("begin to start server on port:%d", options.port)
    global http_server
    http_server = HTTPServer(tornado_app)

    try:
        http_server.listen(options.port)
    except Exception, ex:
        logger.warn("listen port:%d failed with:%s", options.port, str(ex))
        return

    tornado_app.init()
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    tornado.ioloop.PeriodicCallback(detect_signal, 1000).start()
    tornado.ioloop.IOLoop.instance().start()

if __name__ == '__main__':
    main()