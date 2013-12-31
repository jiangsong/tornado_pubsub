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
from se.pubsub import sig_pub_sub
from minibase_handler import MiniBaseHandler


class PubHandler(MiniBaseHandler):
    def get(self, chanel_id):
        """
        @summary: 向指定的消息频道广播消息

        @param chanel_id: 频道编码
        @return:
        """
        message = self.get_argument("message", chanel_id)
        receivers = self.application.pub_sub.pubish(
            chanel_id,
            message)
        self.send_result(
            True,
            chanel_id=chanel_id,
            receivers=len(receivers))


class SubHandler(MiniBaseHandler):
    @web.asynchronous
    def get(self, message_id):
        self.message_id = message_id
        self.receive_id = self.application.pub_sub.subscribe(
            self.message_id,
            self.on_message)

    @web.asynchronous
    def post(self, message_id):
        self.message_id = message_id
        self.receive_id = self.application.pub_sub.subscribe(
            self.message_id,
            self.on_message)

    def on_message(self, sender, **kw):
        """
        @summary: 响应监控消息

        @param sender:
        @param kw:
        @return:
        """
        if self.request.connection.stream.closed() or self._finished:
            return

        if self.message_id != sender:
            return

        message = kw.get("message", "no")
        self.finish(message)
        #
        # 释放监控对象
        #
        if self.message_id and self.receive_id:
             sig_pub_sub.disconnect(self.receive_id)


class PubsHandler(MiniBaseHandler):
    def post(self):
        return self._handle_pubs()
    
    def get(self):
        return self._handle_pubs()
    
    def _handle_pubs(self):
        """
        @summary: 向指定的消息频道广播消息

        @param chanel_id: 频道编码
        @return:
        """
        chanel_ids  = self.get_argument("chanelid", '')
        chanel_list = chanel_ids.split('|')
        message     = self.get_argument("message", chanel_ids)
        receivers   = []
        for chanel_id in chanel_list:
            receiver = self.application.pub_sub.pubish(
                chanel_id,
                message)
            receivers.append(receiver)

        self.send_result(
            True,
            chanel_id=chanel_ids,
            receivers=len(receivers))


class SubsHandler(MiniBaseHandler):
    @web.asynchronous
    def get(self):
        self.handle_subs()
        
    @web.asynchronous
    def post(self):
        self.handle_subs()

    def handle_subs(self):
        chanel_ids          = self.get_argument("chanelid", '')
        self.message_ids    = chanel_ids.split('|')
        self.receive_ids    = []
        for message_id in self.message_ids:
            receive_id = self.application.pub_sub.subscribe(
                message_id,
                self.on_message)
            self.receive_ids.append(receive_id)

    def on_message(self, sender, **kw):
        """
        @summary: 响应监控消息

        @param sender:
        @param kw:
        @return:
        """
        if self.request.connection.stream.closed() or self._finished:
            return

        if sender in self.receive_ids:
            return

        message = kw.get("message", "no")
        self.finish(message)
        #
        # 释放监控对象
        #
        for receive_id in self.receive_ids:
             sig_pub_sub.disconnect(receive_id)