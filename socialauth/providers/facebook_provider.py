from django.conf import settings
from django.db import models
from django.contrib.auth.models import User
from django.utils.encoding import smart_unicode
from django.core.urlresolvers import reverse
from django.core.exceptions import ImproperlyConfigured
from django.contrib.sites.models import Site
import urllib, logging

import facebook
from base import *

try:
    FACEBOOK_APP_ID = getattr(settings, 'FACEBOOK_APP_ID')
    FACEBOOK_API_KEY = getattr(settings, 'FACEBOOK_API_KEY')
    FACEBOOK_SECRET_KEY = getattr(settings, 'FACEBOOK_SECRET_KEY')
except AttributeError, e:
    raise ImproperlyConfigured, \
        "Missing settings for Facebook authentication: %s" \
        % (e)

FACEBOOK_EXTENDED_PERMISSIONS = getattr(settings, 'FACEBOOK_EXTENDED_PERMISSIONS', ())


class Facebook(Provider):
    has_secure_email = True
    
    def login_request(self, request):
        device = request.REQUEST.get("device", "user-agent")
        
        params = {}
        params["client_id"] = FACEBOOK_APP_ID
        params["redirect_uri"] = request.build_absolute_uri(self.get_login_callback_url())
        params["scope"] = "email,publish_stream,read_stream"
        
        url = ("https://graph.facebook.com/oauth/authorize?%s" % 
            urllib.urlencode(params))
        return HttpResponseRedirect(url)
    
    def logout(self, request, response):
        # Delete the facebook cookie
        response.delete_cookie("fbs_" + FACEBOOK_APP_ID)
    
    def process_login(self, request):
        cookie = facebook.get_user_from_cookie(request.COOKIES,
                                               FACEBOOK_APP_ID,
                                               FACEBOOK_SECRET_KEY)
        if cookie:
            uid = cookie['uid']
            access_token = cookie['access_token']
        else:
            # if cookie does not exist
            # assume logging in normal way
            params = {}
            params["client_id"] = FACEBOOK_APP_ID
            params["client_secret"] = FACEBOOK_SECRET_KEY
            params["redirect_uri"] = request.build_absolute_uri(
                         self.get_login_callback_url())
            params["code"] = request.GET.get('code', '')
            params['scope'] = ','.join(FACEBOOK_EXTENDED_PERMISSIONS)

            url = ("https://graph.facebook.com/oauth/access_token?"
                   + urllib.urlencode(params))

            from cgi import parse_qs
            userdata = urllib.urlopen(url).read()
            res_parse_qs = parse_qs(userdata)

            # Could be a bot query
            if not res_parse_qs.has_key('access_token'):
                return None
                
            access_token = res_parse_qs['access_token'][-1]

        graph = facebook.GraphAPI(access_token)
        fb_data = graph.get_object("me")
        if not fb_data:
            return None
        
        return dict(
            uid = fb_data['id'],
            username = fb_data.get('username', None),
            first_name=fb_data['first_name'],
            last_name=fb_data['last_name'],
            email=fb_data.get('email', None),
            url = fb_data.get('link', None),
            avatar_url = "https://graph.facebook.com/%s/picture" % (fb_data.get('username', fb_data['id']),),
            token = access_token
        )
        