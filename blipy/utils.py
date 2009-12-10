#!/usr/bin/python
#-*- coding: utf-8 -*-
"""
 Blipy - A Python API for blip.pl

 authors: Cezary Statkiewicz (cezio [at] thelirium.net), Patryk Zawadzki <patrys@pld-linux.org>
 website: http://github.com/patrys/blipy/tree/master
 license: GNU Lesser General Public License http://www.gnu.org/licenses/lgpl.html
 API: http://www.blip.pl/api-0.02.html
 version: 0.02+oauth
 
"""
"""
utils.py - utilities for blipy (configuration, oauth)
"""

import time
import string, random
import hashlib

import ConfigParser
import oauth.oauth
from core import BlipocConfigError


class BlipAuth(object):
    """
    Account information (from config file)
    this is generated from BlipConfig().get_auth()

    This class replaces blipy.Account class in use as account parameter in 
    api objects. It is used to sign requests with OAuth
    """
    def __init__(self, username, auth_key, consumer_key, consumer_secret):
        self.data = {'auth_key': auth_key, 
                    'username': username,
                    'consumer_key': consumer_key,
                    'consumer_secret': consumer_secret,
                    'signature': oauth.oauth.OAuthSignatureMethod_HMAC_SHA1(),
                    'consumer': oauth.oauth.OAuthConsumer(consumer_key, consumer_secret) }

    def sign_request(self, req_class, request):
        oauth_request = oauth.oauth.OAuthRequest.from_consumer_and_token( self.data['consumer'],
                                                                    token = self.data['auth_key'], 
                                                                    http_method=req_class.method, 
                                                                    http_url=req_class.url, 
                                                                    parameters=req_class._data)
        oauth_request.sign_request(self.data['signature'], self.data['consumer'], self.data['auth_key'])
        headers = oauth_request.to_headers()
        request.headers.update(headers)


class BlipOAuth(oauth.oauth.OAuthClient):
    REQ_URL = 'http://blip.pl/oauth/request_token'
    ACC_URL = 'http://blip.pl/oauth/access_token'
    ATH_URL = 'http://blip.pl/oauth/authorize'

    def __init__(self ):
        self.connection = httplib.HTTPConnection("%s:%d" % ('blip.pl', 80))

    def fetch_request_token(self, oauth_request):
        self.connection.request(oauth_request.http_method, self.request_token_url, headers=oauth_request.to_header()) 
        response = self.connection.getresponse()
        return oauth.OAuthToken.from_string(response.read())

    def fetch_access_token(self, oauth_request):
        # via headers
        # -> OAuthToken
        self.connection.request(oauth_request.http_method, self.access_token_url, headers=oauth_request.to_header()) 
        response = self.connection.getresponse()
        return oauth.OAuthToken.from_string(response.read())

    def authorize_token(self, oauth_request):
        # via url
        # -> typically just some okay response
        self.connection.request(oauth_request.http_method, oauth_request.to_url()) 
        response = self.connection.getresponse()
        return response.read()

    def access_resource(self, oauth_request):
        # via post body
        # -> some protected resources
        headers = {'Content-Type' :'application/x-www-form-urlencoded'}
        self.connection.request('POST', RESOURCE_URL, body=oauth_request.to_postdata(), headers=headers)
        response = self.connection.getresponse()
        return response.read()


class BlipConfig(object):
    """
    BlipConfig is a wrapper around config file.
    Client application calls it with path to config file (no defaults here now),
    and generates OAuth consumer by BlipConfig.get_auth BlipAuth factory

    """
   
    def __init__(self, config_file):
        self.config_file = config_file
        self.config = ConfigParser.ConfigParser()
        try:
            self.config.readfp( open(config_file, 'r'))
        except IOError, e:
            raise BlipocConfigError('Config file: %s, error: %s'%( config_file, e))

    def set_consumer(self, consumer_key, consumer_secret):
        if not self.config.has_section('auth'):
            self.config.add_section('auth')
        self.config.set('auth', 'consumer_key', consumer_key)
        self.config.set('auth', 'consumer_secret', consumer_secret)
        self.save()

    def get_consumer(self):
        try:
            return self.config.get('auth', 'consumer_key'), self.config.get('auth', 'consumer_secret')
        except (KeyError, ConfigParser.Error,), e:
            raise BlipocConfigError('Config file %s does not contain any oauth info: %s'%(self.config_file, e))


    def get_auth_token(self):
        try:
            return self.config.get('auth', 'auth_token')
        except (KeyError, ConfigParser.Error,), e:
            raise BlipocConfigError('Config file %s does not contain any oauth info: %s'%(self.config_file, e))

    def get_auth(self):
        """
        Produces BlipAuth class
        """
        consumer_key, consumer_secret = self.get_consumer()
        auth_key = self.get_auth_token()
        username = self.config.get('auth', 'username')
        return BlipAuth(username, auth_key = auth_key, consumer_key = consumer_key, consumer_secret = consumer_secret)
    
    def start_auth(self, user, application, consumer_key = None, consumer_secret = None):
        if (not consumer_key is None) and (not consumer_secret is None):
            self.set_consumer(consumer_key, consumer_secret)


    def save(self):
        """
        saves current state to file
        """
        self.config.write(open(self.config_file, 'w'))



