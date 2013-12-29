#coding=utf8
'''
Created on 2012-12-12
@author: jimmy
@copyright: 南京恒为网络科技有限公司
@version: 1.0.0
'''
import httplib,urllib
import urlparse
import re, mimetools, mimetypes
import os, time
from array import array

#
# multipart post标识
#
from mini import logger

BOUNDARY = '--------------%s--------------'

class CHTTPClient(object):
    '''
    @summary: 执行http请求 [POST, GET]
    '''
    def __init__(self, url):
        '''
        @summary: 构造函数
        '''
        # 默认非下载文件
        self.raw      = False
        self.response = None
        self.count    = 0
        self.__initialize(url)
            
    def __initialize(self, url):
        '''
        @summary: 初始化函数
        @param url: 访问地址
        '''
        if self.count > 10:
            raise HTTPException(300, 'ERROR REDIRECT', self._uri, '')
        self.count += 1
        self.url      = url
        #
        # 解析url地址
        #
        self._uri  = urlparse.urlparse(url)
        self._port = self._uri.port
        if self._port == None:
            self._port = 80
        self._path = url
        #
        # 创建http连接
        #
        if self._uri.scheme == 'https':
            self._port = 443
            self._conn = httplib.HTTPSConnection(self._uri.hostname, self._port)
        else:
            self._conn = httplib.HTTPConnection(self._uri.hostname, self._port)
    
    def request(self, **kwargs):
        '''
        @summary: 发送post请求
        @param path: 请求路径
        @param **kwargs: 
        '''
        self.method   = kwargs.pop('method', 'GET').upper()
        self.headers  = kwargs.pop('headers', {})
        self.data     = kwargs.get('data', None)
        #
        # 默认编码类型
        #
        contentype    = self.headers.get('Content-Type', 'application/x-www-form-urlencoded')
        
        #
        # 上传文件
        #
        if self.method == 'POST' and hasattr(self.data,'read') and not isinstance(self.data, array):
            kwargs.pop('data', None)
            self.__handle_mutipart_post(**kwargs)
        elif self.method == 'POST' and contentype == 'multipart/form-data':
            kwargs.pop('data', None)
            self.__handle_mutipart_post(**kwargs)
        #
        # 返回值预处理
        #
        try:
            self.__getresponse()
        except Exception, e:
            self._conn.close()
            raise e
        
    def __getresponse(self):
        '''
        @summary: 处理返回值
        '''
        self.response = self._conn.getresponse()
        
        pattern = re.compile('3\d{2}')
        if pattern.match(str(self.response.status)):
            location = self.response.getheader('location')
            self._conn.close()
            self.__initialize(location)
            self.request(method=self.method, headers=self.headers)
            return
        #
        # 正确的返回值处理
        #
        if self.response.status != 200:
            raise HTTPException(self.response.status, self.response.reason, self._uri, self.response.read())
        
        
    def read(self, amt = None):
        '''
        @summary: 读取返回值内容
        '''
        if self._conn or not self._conn.isclosed():
            return self.response.read(amt)
        return None
    
    def __handle_mutipart_post(self, **kwargs):
        '''
        @summary: 上传文件post请求
        '''
        #
        # 文件内容大小
        #
        clen = 0
        try:
            clen = len(self.data)
        except (TypeError, AttributeError):
            try:
                clen = self.data.len
            except AttributeError:
                try:
                    clen = os.fstat(self.data.fileno()).st_size
                except AttributeError:
                    pass
        filename = str(self.data.name.split('/')[-1])
        boundary = BOUNDARY%(mimetools.choose_boundary())
        multipart_start = ''
        #
        # 解析上传文件参数
        #
        for (key, value) in kwargs.items():
            multipart_start += '--%s\r\n' % boundary
            multipart_start += 'Content-Disposition: form-data; name="%s"' % key
            multipart_start += '\r\n\r\n' + str(value) + '\r\n'
        
        multipart_start += '--%s\r\n' % boundary
        multipart_start += 'Content-Disposition: form-data; name="files"; filename="%s"\r\n' % filename
        #
        # 获取文件mime类型
        #
        contenttype = 'application/octet-stream'
        try:
            contenttype = mimetypes.guess_type(filename)[0] or 'application/octet-stream'
        except:
            pass
        multipart_start += 'Content-Type: %s\r\n\r\n' % contenttype
        multipart_end   = '\r\n--%s--\r\n\r\n' % boundary
        multipart_start = str(multipart_start)
        multipart_end   = str(multipart_end)
        
        #
        # 需要Multipart
        #
        self.headers["Content-Length"]   = clen + len(multipart_start) + len(multipart_end)
        self.headers['Content-type']     = 'multipart/form-data; boundary=%s'% boundary
        #
        # 发送请求
        #
        self._conn.request(self.method, self._path, None, self.headers)
        self._conn.send(multipart_start)
        try:
            self._conn.send(self.data);
        except Exception, e:
            raise e
        #
        # 发送multipart结束标识
        #
        self._conn.send(multipart_end)
        
    def close(self):
        '''
        @summary: 手动关闭连接
        '''
        if self._conn:
            self._conn.close()
        
    @staticmethod
    def download(url, **kwargs):
        '''
        @summary: 上传文件
        @param url: 文件上传地址
        @param file: 本地文件或者路径
        '''
        data           = kwargs.pop('file', None)
        will_close     = False
        path           = data
        if hasattr(data,'read') and not isinstance(data, array):
            pass
        elif os.path.isdir(os.path.dirname(data)):
            data       = open(data, 'wb')
            will_close = True
        else:
            return False
        
        status = True
        try:
            httpclient = CHTTPClient(url)
            httpclient.request(method='GET')
            amt = 8192
            datablock = httpclient.read(amt)
            while datablock:
                data.write(datablock)
                datablock = httpclient.read(amt)
                
        except Exception, e:
            status = False
            time.sleep(1)
            logger.error(url)
            logger.exception(e)
        finally:
            httpclient.close()
            if data and not data.closed and will_close:
                data.close()
            if status == False and will_close:
                os.remove(path)
        return status
    
    @staticmethod
    def upload(url, **kwargs):
        '''
        @summary: 上传文件
        @param url: 文件上传地址
        @param file: 本地文件或者路径
        '''
        data           = kwargs.pop('file', None)
        will_close     = False
        if hasattr(data,'read') and not isinstance(data, array):
            pass
        elif os.path.isfile(data):
            data       = open(data, 'rb')
            will_close = True
        else:
            return False
        status = True
        try:
            kwargs['method'] ='POST'
            kwargs['data']   = data
            httpclient = CHTTPClient(url)
            httpclient.request(**kwargs)
            status = httpclient.read()
        except Exception, e:
            status = False
            logger.exception(e)
        finally:
            httpclient.close()
            if will_close and data and not data.closed:
                data.close()
        return status
        
    @staticmethod
    def quickpost(url, **kwargs):
        '''
        @summary: 简单的post方法
        @param url:  请求地址
        @param kwargs: 请求参数
        '''
        kwargs['method'] = 'post'
        retval  = None
        try:
            httpclient = CHTTPClient(url)
            httpclient.request(**kwargs)
            retval = httpclient.read()
        except Exception, e:
            logger.exception(e)
        finally:
            httpclient.close()
        return retval
    
    @staticmethod
    def quickget(url, **kwargs):
        '''
        @summary: 简单的post方法
        @param url:  请求地址
        @param kwargs: 请求参数
        '''
        kwargs['method'] = 'get'
        retval  = None
        try:
            httpclient = CHTTPClient(url)
            httpclient.request(**kwargs)
            retval = httpclient.read()
        except Exception, e:
            logger.exception(e)
        finally:
            httpclient.close()
        return retval
    
class HTTPException(Exception):
    '''
    @summary: http错误
    '''
    def __init__(self, code, reason, url, body):
        self.code    = code
        self.reason  = reason
        self.url     = url
        self.message = body
        
    def __str__(self):
        return (self.reason)
        
def test(a, **kwargs):
    print a
    print kwargs

if __name__=='__main__':
    '''
    '''
    
#    client = CHTTPClient('http://demo.miniyun.com/b.php?XDEBUG_SESSION_START=ECLIPSE_DBGP&KEY=13426661258783')
#    f = open('identity.py', 'rb')
#    client.request(method='post', data=f)
#    print client.read()
#    
#    f.close()
    
    
#    CHTTPClient.download('HTTP://demo.miniyun.com/windows.exe', file=os.path.join(os.path.dirname(__file__), 'windows.exe'))
    
    
    print CHTTPClient.upload('HTTP://demo.miniyun.com/index.php/container/converter/callback?XDEBUG_SESSION_START=ECLIPSE_DBGP&KEY=13426661258783',
                             file=os.path.join(os.path.dirname(__file__), '../tmp/81/4b/e7/00/dist/814be70056bf0a66c3c43fe2b1a3070b0849a504.zip'), 
                             hash= '814be70056bf0a66c3c43fe2b1a3070b0849a504', code = 0)
#    a = urllib.urlencode({'data': {'a':'中午'}})
#    print a
    
#    CHTTPClient.quickpost('http://demo.miniyun.com/b.php')

    logger.info('aaaaaaaaaaaa')
    
