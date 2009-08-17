#!/usr/bin/python
# -*- coding: utf-8 -*-
"""
 Blipy - A Python API for blip.pl

 authors: Cezary Statkiewicz (cezio [at] thelirium.net), Patryk Zawadzki <patrys@pld-linux.org>
 website: http://github.com/patrys/blipy/tree/master
 license: GNU Lesser General Public License http://www.gnu.org/licenses/lgpl.html
 API: http://www.blip.pl/api-0.02.html
 version: 0.02
 
 To use it:
 import blipy
 a = blipy.Account(username, password)
 print blipy.Update.dashboard(a)
"""

from pprint import pprint
import urllib
import types
import datetime
from core import BaseApiObject, ApiException, BlipocInputError, Request, _ALL, _ALL_SINCE, SUB_ALL, SUB_FROM, SUB_TO, encode_multipart, DEBUG, UPDATE_BODY_LIMIT

cached = {}

def propertize(name, cls):
    def proxied_property(self):
        if not cached.has_key(name):
            cached[name] = {}
        if hasattr(self, '%s_path' % name):
            uri = getattr(self, '%s_path' % name)
            if not cached[name].has_key(uri):
                c = globals()[cls]
                cached[name][uri] = c.get_by_uri(self.account, uri)
            return cached[name][uri]
        else:
            return None
    return proxied_property

class Account(object):
    def __init__(self, username= None, password = None):
        self.credentials = None
        if username is not None and password is not None:
            self.set_credentials(username, password)

    def set_credentials(self, username, password):
        """
        set username and password 
        """
        self.credentials = (username, password,)

class Movie(BaseApiObject):
    __fields__ = {'id': int,
                    'url': unicode}

class Picture(BaseApiObject):
    __fields__ = {'id': int,
                    'url': unicode,
                    'update_path': unicode}
    update = property(propertize('update', 'Update'), None)

    @staticmethod
    def list(account, update_id = None):
        if update_id:
            return Picture.get_list_by_uri(account, '/pictures/%s/all_since' % update_id)
        else:
            return Picture.get_list_by_uri(account, '/pictures/all')

class Recording(BaseApiObject):
    __fields__ = {'id': int,
                    'url': unicode,
                    'update_path': unicode}
    update = property(propertize('update', 'Update'), None)

class Shortlink(BaseApiObject):
    __fields__ = {'id': int,
                    'created_at': datetime.datetime,
                    'hit_count': int,
                    'original_link': unicode,
                    'shortcode': unicode}

    @staticmethod
    def list(account, update_id = None):
        if update_id:
            return Shortlink.get_list_by_uri(account, '/shortlinks/%s/all_since' % update_id)
        else:
            return Shortlink.get_list_by_uri(account, '/shortlinks/all')

class Transport(BaseApiObject):
    __fields__ = {'id': int,
                    'name': unicode}



class Notice(BaseApiObject):
    __fields__ = {'id': int,
                  'body': unicode,
                  'user_path': unicode,
                  'created_at': datetime.datetime}
        
    @staticmethod
    def get_last(account, last_id = None, limit = None):
        uri = '/notices'
        if last_id:
            uri = '/notices/since/%s'%last_id
            
        if limit:
            uri = '%s?limit=%s'%(uri, limit)
            
        return Notice.get_list_by_uri(account, uri)
        
    @staticmethod
    def get_since(last_id = None, limit = None):
        uri = '/notices'
        if last_id:
            uri = '/notices/since/%s'%last_id
            
        if limit:
            uri = '%s?limit=%s'%(uri, limit)
            
        return Notice.get_list_by_uri(account, uri)
        
        
class Update(BaseApiObject):
    __fields__ = { 'id': int,
                    'body': unicode,
                    'type': unicode,
                    'user_path': unicode,
                    'recipient_path': unicode,
                    'created_at': datetime.datetime,
                    'transport': Transport,
                    'pictures_path': unicode,
                    'recording_path': unicode,
                    'movie_path': unicode}
    recipient = property(propertize('recipient', 'User'), None)
    user = property(propertize('user', 'User'), None)
    recording = property(propertize('recording', 'Recording'), None)
    movie = property(propertize('movie', 'Movie'), None)

    def get_pictures(self):
        if hasattr(self, 'pictures_path'):
            return Picture.get_list_by_uri(self.account, self.pictures_path)
        else:
            return []
    pictures = property(get_pictures, None)

    @staticmethod
    def dashboard(account, update_id = None):
        """
        retrieves user's dashboard.
        if update_id provided, it will return changes made after update_id
        """
        if update_id:
            return Update.get_list_by_uri(account, '/dashboard/since/%s' % update_id)
        else:
            return Update.get_list_by_uri(account, '/dashboard')
        

    @classmethod
    def _get_list_element_by_uri(cls, account, i):
        
        if i.get('type') == 'Status':
            return Update(account, i)
        elif i.get('type') == 'Notice':
            return Notice(account, i)
        elif i.get('type') == 'DirectedMessage':
            return DirectedMessage(account, i)
        elif i.get('type') == 'PrivateMessage':
            return PrivateMessage(account, i)
    
    @staticmethod
    def list(account, update_id = None):
        """
        retrieves user's statuses.
        if update_id provided, it will return changes made after update_id
        """
        if update_id:
            return Update.get_list_by_uri(account, '/updates/%s/since' % update_id)
        else:
            return Update.get_list_by_uri(account, '/updates')

    @classmethod
    def get(cls, account, update_id):
        """
        get specified status
        """
        return cls.get_by_uri(account, '/updates/%s' % update_id)

    @staticmethod
    def create(account, status, picture = None):
        """
        set new status
        status - text message up to UPDATE_BODY_LIMIT (160 chars)
        
        picture - [filename, filecontents,]. 
        
        """
        if len(status)> UPDATE_BODY_LIMIT:
            raise BlipocInputError('status jest dłuższy niż dopuszczalna wielkość: (%s > %s)'%(len(status), UPDATE_BODY_LIMIT) )
        post_data = {'update[body]': status}
        content_encoding = None
        if picture:
            # we don't use urllib.urlencode, because we must use mimetools, so 
            #post_data['update[picture] = picture
            # won't work
            picture.insert(0, "update[picture]")
            picture = [picture]
        content_encoding, post_data = encode_multipart(post_data, picture or [])

        r = Request(account.credentials, '/updates', 'POST', post_data, content_encoding)

        return r.do_request()

class PrivateMessage(Update):
    @staticmethod
    def list(account, update_id = None):
        """
        retrieves user's directed messages.
        if update_id provided, it will return changes made after update_id
        """
        if update_id:
            return DirectedMessage.get_list_by_uri(account, '/private_messages/%s/since' % update_id)
        else:
            return DirectedMessage.get_list_by_uri(account, '/private_messages')

    @classmethod
    def get(cls, account, update_id):
        """
        get specified status
        """
        return cls.get_by_uri(account, '/private_messages/%s' % update_id)

    @staticmethod
    def create(account, status, recipient, picture= None):
        """
        create private message
        """
        if len(status)> UPDATE_BODY_LIMIT:
            raise BlipocInputError('status jest dłuższy niż dopuszczalna wielkość: (%s > %s)'%(len(status), UPDATE_BODY_LIMIT) )
        content_encoding = None
        post_data =  {'private_message[body]': status, 'private_message[recipient]': recipient }
        if picture:
            # we don't use urllib.urlencode, because we must use mimetools, so 
            #post_data['update[picture] = picture
            # won't work
            picture.insert(0, "private_message[picture]")
            picture = [picture]
        content_encoding, post_data = encode_multipart(post_data, picture or [])
        r = Request(account.credentials, '/private_messages', 'POST',post_data, content_encoding)
        return r.do_request()

class DirectedMessage(Update):
    @staticmethod
    def list(account, update_id = None):
        """
        retrieves user's directed messages.
        if update_id provided, it will return changes made after update_id
        """
        if update_id:
            return DirectedMessage.get_list_by_uri(account, '/directed_messages/%s/since' % update_id)
        else:
            return DirectedMessage.get_list_by_uri(account, '/directed_messages')

    @classmethod
    def get(cls, account, update_id):
        """
        get specified status
        """
        return cls.get_by_uri(account, '/directed_messages/%s' % update_id)

    @staticmethod
    def create(account, status, recipient, picture = None):
        """
        create private message
        """
        if len(status)> UPDATE_BODY_LIMIT:
            raise BlipocInputError('status jest dłuższy niż dopuszczalna wielkość: (%s > %s)'%(len(status), UPDATE_BODY_LIMIT) )
        content_encoding = None
        post_data =  {'directed_message[body]': status, 'directed_message[recipient]': recipient }
        if picture:
            # we don't use urllib.urlencode, because we must use mimetools, so 
            #post_data['update[picture] = picture
            # won't work
            picture.insert(0, "directed_message[picture]")
            picture = [picture]
        content_encoding, post_data = encode_multipart(post_data, picture or [])
        r = Request(account.credentials, '/directed_messages', 'POST',post_data, content_encoding)
        return r.do_request()

class Status(Update):
    @staticmethod
    def tags(account, tag, limit=None, since = None):
        params = {}
        if isinstance(limit, int):
            params['limit'] = limit
        url = '/tags/%s'%tag
        if isinstance(since, int):
            url = url+'/since/%s'%since
        if params:
            url = '%s?%s'%(url, urllib.urlencode(params))
        return Status.get_list_by_uri(account, url)


    @staticmethod
    def list(account, update_id = None):
        """
        retrieves user's status messages.
        if update_id provided, it will return changes made after update_id
        """
        if update_id:
            return Status.get_list_by_uri(account, '/statuses/%s/all_since' % update_id)
        else:
            return Status.get_list_by_uri(account, '/statuses/all')

    @classmethod
    def get(cls, account, update_id):
        """
        get specified status
        """
        return cls.get_by_uri(account, '/statuses/%s' % update_id)

    @staticmethod
    def create(account, status):
        """
        create status message
        """
        if len(status)> UPDATE_BODY_LIMIT:
            raise BlipocInputError('status jest dłuższy niż dopuszczalna wielkość: (%s > %s)'%(len(status), UPDATE_BODY_LIMIT) )
        r = Request(account.credentials, '/statuses', 'POST', {'status[body]': status})
        return r.do_request()

class Bliposphere(BaseApiObject):
    @staticmethod
    def list(account):
        return Status.get_list_by_uri(account, '/bliposphere')

class Avatar(BaseApiObject):
    __fields__ = { 'id': int,
                    'url_15': unicode,
                    'url_30': unicode,
                    'url_50': unicode,
                    'url_90': unicode,
                    'url_120': unicode,
                    'url': unicode}

class Background(BaseApiObject):
    __fields__ = { 'id': int,
                    'url': unicode}

class User(BaseApiObject):
    __fields__ = {'id': int,
                'login': unicode,
                'avatar_path': unicode,
                'background_path': unicode,
                'current_status_path': unicode}
    current_status = property(propertize('current_status', 'Status'), None)
    avatar = property(propertize('avatar', 'Avatar'), None)
    background = property(propertize('background', 'Background'), None)
    @staticmethod
    def friends(account):
        """
        get list of user's friends
        """
        return User.get_list_by_uri(account, '/friends/')

    @classmethod
    def get(cls, account, user = None):
        """
        get user data for user
        if user is not provided, api will return current user
        """
        if user:
            return cls.get_by_uri(account, '/users/%s' % user)
        else:
            return cls.get_by_uri(account, '/users/')

def user_from_path(account, path):
    """
    user instance factory
    """
    path, u = path.strip('/').split('/', 1)
    return User.get(account, u)

class Subscription(BaseApiObject):
    __fields__ = { 'tracked_user_path': unicode,
                   'tracking_user_path': unicode,
                   'transport': Transport
                    }
    @classmethod
    def get(cls, account, user = None, direction = SUB_ALL):
        url = '/subscriptions%s'%direction
        if user:
            url = '/users/%s%s'%(user, url)
        return cls.get_list_by_uri(account, url)
    
    @staticmethod
    def set(cls, account, user):
        url = '/subscriptions/%s'%user
        r = Request(account.credentials, url, 'PUT')
        return r.do_request()
        
    @staticmethod
    def delete(cls, account, user):
        url = '/subscriptions/%s'%user
        r = Request(account.credentials, url, 'DELETE')
        return r.do_request()

if __name__ == '__main__':
    import sys
    if len(sys.argv) != 3:
        sys.exit('Usage: %s login haslo'%__file__)

    username = sys.argv[1]
    password = sys.argv[2]
    
    u = Account()

    u.set_credentials(username, password)

    import core
    core.DEBUG = True
    pm = DirectedMessage.create(u,'cezio', 'test')
    print pm
