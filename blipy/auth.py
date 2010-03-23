#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
 Blipy - A Python API for blip.pl

 authors: Cezary Statkiewicz (cezio [at] thelirium.net), Patryk Zawadzki <patrys@pld-linux.org>
 website: http://github.com/patrys/blipy/tree/master
 license: GNU Lesser General Public License http://www.gnu.org/licenses/lgpl.html
 API: http://www.blip.pl/api-0.02.html
 version: 0.02+oauth
 
"""
"""
auth.py - authentication and authorization classes
"""

import time
import base64
import string, random
import hashlib

import oauth.oauth

class BlipAuth(object):
    """
    BlipAuth is a base class for authentication and authorization. 
    Doesn't do much.

    A subclass should be used as an 'account class'.
    """
    def sign_request(self, rq_cls, reuest):
        """
        BlipAuth.sign_request method adds authentication/authorization
        headers or other processing to request.
        Method should be overwrite in subclass.
        """
        raise NotImplementedError('BlipAuth.sign_request should be overwritten in subclass')


class BasicAuth(BlipAuth):
    """
    BasicAuth(BlipAuth) is a plain, old HTTP Basic Authentication.
    """
    def __init__(self, username, password):
        """
        Just username and password here
        """
        self.data = { 'username': username,
                      'password': password
                    }

    def sign_request(self, req_class, request):
        """
        Authorization header
        """
        request.add_header('Authorization', 
                           'Basic %s' % (base64.b64encode('%(username)s:%(password)s' % 
                                        self.data )))

class OAuth(BlipAuth):
    """
    OAuth(BlipAuth) will use oauth 1.0 protocol for authorization of request.
    """
    def __init__(self, username, auth_key, consumer_key, consumer_secret):
        """
        We need username, auth_key, consumer_key, consumer_secret
        """
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

