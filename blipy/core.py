# -*- coding: utf-8 -*-
#
# Blipy - A Python API for blip.pl
#
# authors: Cezary Statkiewicz (cezio [at] thelirium.net), Patryk Zawadzki <patrys@pld-linux.org>
# website: http://github.com/patrys/blipy/tree/master
#
# version: $Id: core.py 38 2008-01-28 16:18:29Z patrys $

API_VERSION = 0.02
URL = 'http://api.blip.pl'
USER_AGENT = 'blipy - Blip.pl api library for python'
DEBUG = False# to be False in stable version

import mimetypes, mimetools, base64
import datetime, time, urllib2, urllib, base64
import simplejson
from pprint import pprint

class ApiException(Exception):
    pass

class BlipocInputError(ApiException):
    pass

class BaseApiObject(object):
    """
    base blip api class for containers
    
    __fields__ - dictionary {field: field_type_class_or_type} with attributes of this type
    __values__ - dictionary with object values
    
    get_json() - method for getting json string for class instance
    
    parse_json(data, raw_json = False) - method for setting attributes from json data, if raw_json, then it will be parsed by simplejson.loads

    """
    __fields__ = {}

    def __init__(self, account = None, *args, **kwargs):
        self.__values__ = None
        self.account = account
        if args:
            try:
                self.parse_json(args[0])
            except Exception, e:
                if DEBUG:
                    print args[0]
                    print '%s'%e
                raise

    @classmethod
    def get_by_uri(cls, account, uri):
        """
        get specified status
        """
        r = Request(account.credentials, uri, 'GET', None)
        data = r.request_json()
        return cls(account, data)

    @classmethod
    def get_list_by_uri(cls, account, uri):
        """
        get specified status
        """
        r = Request(account.credentials, uri, 'GET', None)
        data = r.request_json()
        res = []
        for i in data:
            res.append(cls._get_list_element_by_uri(account, i))
        return res
    
    @classmethod
    def _get_list_element_by_uri(cls, account, i ):
        """
        list element factory
        """
        return cls(account, i)
        
    def get_json(self):
        data = {}
        for f in self.__fields__:
            # getting field value
            try:
                field = getattr( self, f)
            except AttributeError:
                # maybe if it's required field it should raise an exception?
                break
            if isinstance(field, BaseApiObject):
                data[f] = field.get_json()
            else:
                data[f] = field
        return simplejson.dumps(data)

    def parse_json(self, data, raw_json = False):
        if raw_json:
            data = simplejson.loads(data)
        data = self._parse_json(data)
        for f in data:
            if DEBUG:
                print 'setting self.%s = %s'%( f, data[f])
            setattr(self, f, data[f])
        self.__values__ = data

    def _parse_json(self, data):
        d = {}
        if not isinstance(data, dict):
            raise ApiException('Nieprawidłowe dane - spodziewano się słownika, otrzymano %s' % type(data))
        for f in self.__fields__:
            try:
                field = data[f]
            except KeyError:
                if DEBUG:
                    print 'missing key', f
                continue
            try:
                if self.__fields__[f] is datetime.datetime:
                    value = datetime.datetime.strptime(field, '%Y-%m-%d %H:%M:%S')
                elif issubclass (self.__fields__[f], BaseApiObject):
                    value = self.__fields__[f](self.account, field)
                else:
                    value = self.__fields__[f](field)
            except Exception, e:
                raise ApiException('Błąd walidacji typu dla obiektu %s: atrybut %s %s' % ( self.__class__.__name__, f, e))
            d[f] = value
        return d

    def _print(self):
        """
        TODO: rewite!!!
        
        formated object representation
        
Class1:
    attr1: value
    class_attr:
    
        Class2:
            attr2: value
            attr3: value
        
        """
        out = ''
        for f in self.__fields__:
            try:
                if isinstance(getattr(self, f), BaseApiObject):
                    tmp = getattr(self, f)._print().split()
                    out +='\t%s\n:'%f
                    out +='\n\t'.join([ '\t%s'%l for l in  tmp])
                else:
                    out += '\t%s:%s\n'%(f, getattr(self, f))
            except AttributeError:
                continue
        #####
        #out = '\n'.join( [ '\t%s : %s'%( k, getattr(self, k, '') )
        #                    for k in self.__fields__  ])
        
        out = '%s: \n%s\n'%(self.__class__.__name__, out)
        return out
        
    __str__ = _print
    __repr__ = _print

class Request(object):
    """
    request object for api.blip.pl
    """
    def __init__(self, credentials, url, method, data, content_type = None):
        """
        credentials = (username, password)
        url = update_url
        method = POST || GET
        data = string with POST data or dict to encode
        content_type = HTTP header with content type (multipart/form-data)
        """
        self.credentials = credentials
        self.url = '%s%s' % (URL, url)
        self.method = method
        if type(data) == dict:
            for key, val in data.iteritems():
                if isinstance(val, unicode):
                    data[key] = val.encode('utf-8')
                else:
                    data[key] = val
            data = urllib.urlencode(data)
        self.data = data
        self.content_type = content_type or  'application/x-www-form-urlencoded'
        self._debug = DEBUG
        
    def do_request(self):
        if self._debug:
            self.__print_debug('Requesting url: %s %s \n with %s data:\n %s'%(self.method, self.url, self.method, self.data))
        request = urllib2.Request(self.url)
        if self.credentials:
            request.add_header('Authorization', 
                                'Basic %s'%( base64.b64encode('%s:%s'%self.credentials )))
        request.add_header('User-Agent', USER_AGENT)
        request.add_header('X-blip-api', '%s'%API_VERSION)
        request.add_header('Accept', 'application/json')
        request.add_header('Pragma', 'no-cache')
        
        if self.data:
            request.add_data(self.data)
            request.add_header('Content-Type', self.content_type )
            request.add_header('Content-Length', len(self.data))
        try:
            response = urllib2.urlopen(request)
        except urllib2.HTTPError, e:
            # 201 - Created:
            data = e.read()
            if e.code == 201:
                return True
            raise e
            return data
        data = response.read()
        if self._debug:
            self.__print_debug(data)
        return data

    def request_json(self):
        
        data = self.do_request()
        try:
            return simplejson.loads(data)
        except (ValueError, TypeError,), e:
            print 'error during unpack: %s\n%s'%(e, data)
            raise


    def __print_debug(self, data):
        print '>>> pblipoc debug', time.ctime()
        print
        if isinstance(data, str):
            print data
        else:
            pprint(data)
        print
        
        
class _ALL(object):
    def __str__(self):
        return ''
    def __repr__(self):
        return '<_ALL BlipApi class>'
    
class _ALL_SINCE(object):
    def __str__(self):
        return ''
    def __repr__(self):
        return '<_ALL_SINCE BlipApi class>'


class _SUB_ALL(object):
    def __str__(self):
        return ''
    def __repr__(self):
        return '<%s BlipApi class>'%self.__class__.__name__

class _SUB_FROM(_SUB_ALL):
    def __str__(self):
        return '/from'

     
class _SUB_TO(_SUB_ALL):
    def __str__(self):
        return '/to'

SUB_ALL = _SUB_ALL()
SUB_FROM = _SUB_FROM()
SUB_TO = _SUB_TO()


def encode_multipart(fields, files):
    """
    fields = {form_field: form_value}
    files = ( ( form_field, file_name, file_contents,)..)

    """
    boundary = mimetools.choose_boundary()
    contents =[]
    for key, value in fields.items():
        if isinstance(value, unicode):
            value = value.encode('utf-8')
        contents.append('--%s'%boundary)
        contents.append('Content-Disposition: form-data; name="%s"' % key)
        contents.append('')
        contents.append(value)
    for (key, fname, fvalue,) in files:
        contents.append('--%s'%boundary)
        contents.append('Content-Disposition: form-data; name="%s"; filename=%s'%(key, fname,) )
        contents.append('Content-Type: %s '%(mimetypes.guess_type(fname)[0] or 'application/octet-stream'))
        contents.append('Content-Transfer-Encoding: base64')
        contents.append('')
        contents.append(fvalue)
        contents.append(base64.b64encode(fvalue))
    contents.append('--%s--'%boundary)
    contents.append('')
    content_type = "multipart/form-data; boundary=%s"%boundary
    return content_type, '\r\n'.join(contents)



if __name__ == '__main__':

    import sys
    if len(sys.argv) != 3:
        sys.exit('Usage: __init__.py login haslo')
    username = sys.argv[1]
    password = sys.argv[2]
    u = Update()

    u.set_credentials(username, password)
    #pprint(u.dashboard())
    #u.dashboard(140000) # nie działa
    #sys.exit()
    #u.get(140000)
    u.set('how do you handle f')

    u = User()
    
    u.set_credentials(username, password)
    pprint(u.friends())
    
    pprint(friends)
    pprint(u.users())
    

# $Id: api.py 41 2008-01-31 11:39:02Z patrys $
