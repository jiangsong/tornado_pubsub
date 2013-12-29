# coding=utf-8

__author__ = 'nava'

from blinker import signal

#
# 定义全局的分发
#
sig_logs = signal("logs")

#
# 定义全局消息
#
sig_messages = signal("messages")

#
# 进行消息频道的信号量
#
sig_pub_sub = signal('pub_sub')