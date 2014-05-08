# coding=utf-8
#
# 日志操作模块，此类是唯一实例化
#

import logging, os #@UnusedImport
import logging.handlers #@UnusedImport

def LogManager(
    path        = "pubsub.log",
    terminal    = True,
    level       = logging.WARNING):
    """
    获取日志处理类
    """
    return CLogger(path, terminal, level).Instance()

class CLogger(logging.Logger):
    """ 管理系统内部的所有资源信息以及临界变量 """
    # =============================================
    # 唯一实例结束位置
    # =============================================
    # =============================================
    # 唯一实例开始位置
    # =============================================
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
    # =============================================
    # 唯一实例结束位置
    # =============================================
    

    def __init__(self, 
        path = "", 
        terminal = True,
        level = logging.WARNING):
        """ Create singleton instance """
        if CLogger.__instance is None:
            #logging.Logger.__init__(self, os.path.basename(path), logging.DEBUG)
            
            # Create and remember instance
            CLogger.__instance = CLogger.__impl()

            #
            # 本地定义日志操作
            #
            logger = logging.getLogger(os.path.basename(path))
            
            logger.setLevel(level)
    
            self._path = path
            #
            # 添加文件日志输出和控制台输出
            #
            hdlr = logging.handlers.RotatingFileHandler(path, maxBytes=0x9600000, backupCount=1) # 大小限制在150m
            # 设置输出文件格式 
            formatter = logging.Formatter(u'%(asctime)s(P:0x%(process)x T:0x%(thread)x):%(levelname)s - %(module)s@%(funcName)s@%(lineno)d: %(message)s')
            hdlr.setFormatter(formatter)
            
            # 添加日志处理模块
            logger.addHandler(hdlr)
            if terminal == True:
                ch = logging.StreamHandler()
                ch.setFormatter(formatter)
                logger.addHandler(ch)

            self._logger = logger

    def Instance(self):
        """ 返回日志句柄 """
        return self._logger
    
logger = LogManager()