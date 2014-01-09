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
from se import config, logger
from pubsub import sig_pub_sub
import tornadoredis
import tornado
import time
import json


class PubSubManager(object):
    REDIS_PUBSU_CHANEL_ID = "sys.pubsub.message"

    class __impl:
        """ Implementation of the singleton interface """

    # storage for the instance reference
    __instance = None

    def __getattr__(self, attr):
        """ Delegate access to implementation """
        return getattr(self.__instance, attr)

    def __setattr__(self, attr, value):
        """ Delegate access to implementation """
        return setattr(self.__instance, attr, value)

    def __init__(self, app):
        """ Create singleton instance """
        if PubSubManager.__instance is None:
            # Create and remember instance
            PubSubManager.__instance = PubSubManager.__impl()
            self.app = app
            self.redis_sub = None
            self.redis_pub = None
            
            self.chanel_message = {}
            self.sub_dicts      = {}

    @tornado.gen.engine
    def init(self):
        self.pubsub_timeout = int(config.get('system', 'pubsub_timeout'), 0)
        self.job_periodic = tornado.ioloop.PeriodicCallback(self._periodic_callback, 1000)
        self.job_periodic.start()

        if not config.has_section("redis"):
            return

        redis_enable = config.get('redis', 'enable')
        if redis_enable != "true":
            return

        redis_host = config.get('redis', 'host')
        redis_port = int(config.get('redis', 'port'), 0)
        redis_password = config.get('redis', 'password')
        self.redis_sub = tornadoredis.Client(
            host=redis_host,
            port=redis_port,
            password=redis_password)

        self.redis_pub = tornadoredis.Client(
            host=redis_host,
            port=redis_port,
            password=redis_password)
        self.redis_pub.connect()

        yield tornado.gen.Task(self.redis_sub.subscribe, self.REDIS_PUBSU_CHANEL_ID)
        self.redis_sub.listen(self.on_redis_message)

    def on_redis_message(self, msg):
        """
        响应redis发送过来的回调消息

        :param msg:
        :return:
        """
        if msg.kind != 'message' or msg.channel != self.REDIS_PUBSU_CHANEL_ID:
            return

        j_dict = json.loads(msg.body)
        chanel_id = j_dict.get("chanel_id", 0)
        message = j_dict.get("message", None)
        if chanel_id == 0 or message is None:
            return

        self.pubish(chanel_id, message, from_redis=True)

    def pubish(self, chanel_id, body, from_redis=False):
        """
        @summary: 针对制定频道发布消息

        @param chanel_id: 频道ID
        @param body: 需要发布的内容
        @return:
        """
        if from_redis is False and self.redis_pub:
            redis_message = {
                "chanel_id": chanel_id,
                "message": body}
            self.redis_pub.publish(self.REDIS_PUBSU_CHANEL_ID, json.dumps(redis_message))
            return [chanel_id]

        #
        # 广播消息内容
        #
        receivers = sig_pub_sub.send(
            chanel_id,
            message=body)
            
        #
        # 检查是否拥有对应的接受者，如果有则不保留对应的内容
        #
        if len(receivers) <= 0:
            message_list = self.chanel_message.get(chanel_id, [])
            message_list.append((body, time.clock()))
            self.chanel_message[chanel_id] = message_list

        logger.info("have %d receivers", len(receivers))
        return receivers

    def subscribe(self, handler, chanel_id, receiver):
        """
        @summary: 针对制定频道发布消息

        @param chanel_id: 频道ID
        @param body: 需要发布的内容
        @return:
        """
        message_list = self.chanel_message.get(chanel_id, [])
        if len(message_list) > 0:
            logger.info("have old %d messages", len(message_list))
            (message, start) = message_list.pop()
            tornado.ioloop.IOLoop.instance().add_callback(
                callback=lambda: receiver(chanel_id, message=message))
            return 0
            
        receiver_id = sig_pub_sub.connect(
            receiver,
            chanel_id)

        #
        # 记录到字典中
        #
        old_str, _, _ = self.sub_dicts.get(receiver_id, (" ", 0, None))
        self.sub_dicts[receiver_id] = (old_str + " " + chanel_id, time.time(), handler)
        return receiver_id

    def unsubscribe(self, receiver_id):
        """
        @summary: 取消订阅制定的频道

        @param receiver_id:
        @return:
        """
        if receiver_id is None:
            return
        if not self.sub_dicts.has_key(receiver_id):
            return
        sig_pub_sub.disconnect(receiver_id)
        del self.sub_dicts[receiver_id]

    def _periodic_callback(self):
        """
        @summary: 定时任务回调函数

        @return: 无
        """
        #
        # 释放超时消息
        #
        self._release_chanel_message()

        #
        # 释放无效超时句柄
        #
        self._release_chanel_handler()

    def _release_chanel_message(self):
        """
        释放超时消息

        :return:
        """
        current_time = time.clock()
        for k, v in self.chanel_message.items():
            i = 0
            while i < len(v):
                (_, old_time) = v[i]
                diff_time = current_time - old_time
                if diff_time > self.pubsub_timeout:
                    del v[i]
                    continue

                i += 1

            if len(v) <= 0:
                del self.chanel_message[k]

    def _release_chanel_handler(self):
        """
        释放超时消息

        :return:
        """
        current_time = time.clock()

        for receive_id in self.sub_dicts.keys():
            (chanel_id, start_time, handler) = self.sub_dicts[receive_id]
            diff_time = current_time - start_time

            #
            # 连接已经关闭
            #
            if handler == None or handler.request.connection.stream._closed == True:
                logger.info("remove closed sub chanel id:%s", chanel_id)
                self.unsubscribe(receive_id)
                continue
            if diff_time > self.pubsub_timeout:
                self.unsubscribe(receive_id)
                continue

            pass