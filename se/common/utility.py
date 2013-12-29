#-*-coding=utf8 -*-
'''
Created on 2013-09-25

@author: Kindac@hengwei.co
'''
try: 
    import simplejson as json
except ImportError: 
    import json
import sys, os, hashlib, inspect
import urllib
import urlparse

class CUtility(object):
    '''
    @summary: 实用工具
    '''

    @staticmethod
    def dictToJson(dict):
        '''
        @summary: 将字典转换为json字符串
        '''
        return json.dumps(dict)
    
    @staticmethod
    def splitstr(string, limit = 2, times = 4):
        '''
        @summary: 分割字符串，组装成路径
        @param string: 字符串
        @param limit: 分割的长度
        '''
        length = len(string)
        
        #
        # 如果字符串长度不足执行 times次，则
        #
        iterable = []
        for index in range(0, length - limit):
            if index % limit == 0:
                iterable.append(string[index : index + limit])
                times -= 1
            if times <= 0:
                break
        return '/'.join(iterable)
    
    @staticmethod
    def shorten(origin):
        chars = (
            "a","b","c","d","e","f","g","h",
            "i","j","k","l","m","n","o","p",
            "q","r","s","t","u","v","w","x",
            "y","z","0","1","2","3","4","5",
            "6","7","8","9","A","B","C","D",
            "E","F","G","H","I","J","K","L",
            "M","N","O","P","Q","R","S","T",
            "U","V","W","X","Y","Z",)
        
        key = "a9b542a24e1cf7e91f0d57ce21ba9533"
        #对传入网址进行MD5加密  
        hexdigest = hashlib.md5(key + origin).hexdigest()
        res = [0 for i in range(4)]
        for i in range(4):
            #把加密字符按照8位一组16进制与0x3FFFFFFF进行位与运算  
            hexint = 0x3FFFFFFF & int("0x" + hexdigest[i * 8: i*8+8], 16)  
            outChars = ""
            for j in range(7):
                #把得到的值与0x0000003D进行位与运算，取得字符数组chars索引  
                index = 0x0000003D & hexint
                #把取得的字符相加  
                outChars += chars[index]
                #每次循环按位右移5位
                hexint = hexint >> 5
            #把字符串存入对应索引的输出数组
            res[i] = outChars
        return res[0]
    
    @staticmethod
    def json_decode(var):
        '''
        @summary: 解析json格式字符串
        @param var: 字符串
        '''
        res = None
        try:
            res = json.loads(var)
        except:
            try:
                index = var.find("{")
                val   = var[index:]
                res = json.loads(val)
            except:
                pass
        return res
    
    @staticmethod
    def buildurl(url, **kwargs):
        '''
        @summary: 组装请求地址
        '''
        params  = urllib.urlencode(kwargs)
        result  = urlparse.urlparse(url)
        query = result.query
        if query and params:
            query += '&'
            query += params
        elif not query:
            query = params
        data = (result.scheme, result.netloc, result.path, result.params, query, result.fragment)
        return urlparse.urlunparse(data)
    
    @staticmethod
    def StrToUTf8(value):
        """ to unicode """
        import locale
        try:
            encoding = locale.getdefaultlocale()[1]
            if isinstance(value, str):
                value    = unicode(value, encoding, errors="ignore")
        except:
            pass
        
        return value
    
    @staticmethod
    def GetFilesFromPath(path, filter = '*.*'):
        '''
        @summary: 获取目录下的文件
        '''
        retval = []
        if not filter:
            filter = '*.*'
        match = os.path.splitext(filter)[1].upper()
        if not os.path.exists(path) or not os.path.isdir(path):
            return retval
        for root, _, files in os.walk(path) :
            for name in files:
                if match != '.*':
                    suffix = os.path.splitext(name)[1].upper()
                    if suffix != match:
                        continue
                retval.append(os.path.join(root, name))
        return retval
    
    @staticmethod
    def getRootDir():
        path = os.path.realpath(sys.path[0])        # interpreter starter's path
        if os.path.isfile(path):                    # starter is excutable file
            path      = os.path.dirname(path)
            return os.path.abspath(path)            # return excutable file's directory
        else:                                       # starter is python script
            caller_file = inspect.stack()[1][1]     # function caller's filename
            return os.path.dirname(os.path.abspath(os.path.dirname(caller_file)))# return function caller's file's directory
        
    @staticmethod
    def isExe():
        path = os.path.realpath(sys.path[0])        # interpreter starter's path
        if os.path.isfile(path):                    # starter is excutable file
            return True
        else:                                       # starter is python script
            return False