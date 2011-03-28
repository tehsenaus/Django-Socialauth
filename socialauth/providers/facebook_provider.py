from django.conf import settings
from django.db import models
from django.contrib.auth.models import User
from django.utils.encoding import smart_unicode
from django.core.urlresolvers import reverse
from django.core.exceptions import ImproperlyConfigured
from django.contrib.sites.models import Site
import urllib, logging

import facebook
from .base import *

try:
    FACEBOOK_APP_ID = getattr(settings, 'FACEBOOK_APP_ID')
    FACEBOOK_API_KEY = getattr(settings, 'FACEBOOK_API_KEY')
    FACEBOOK_SECRET_KEY = getattr(settings, 'FACEBOOK_SECRET_KEY')
except AttributeError, e:
    raise ImproperlyConfigured, \
        "Missing settings for Facebook authentication: %s" \
        % (e)

FACEBOOK_EXTENDED_PERMISSIONS = getattr(settings, 'FACEBOOK_EXTENDED_PERMISSIONS', ())


class FacebookUserProfile(ProviderModel):
    """
    For users who login via Facebook.
    """
    facebook_uid = models.CharField(max_length=20,
                                    unique=True,
                                    db_index=True)
    
    user = models.ForeignKey(User, related_name='facebook_profiles')
    url = models.URLField(blank=True, null=True)
    
    access_token = models.CharField(max_length=255, blank=True, null=True, editable=False)

    def __unicode__(self):
        return "%s's profile" % smart_unicode(self.user)


class Facebook(Provider):
    def login_request(self, request):
        device = request.REQUEST.get("device", "user-agent")
        
        params = {}
        params["client_id"] = FACEBOOK_APP_ID
        params["redirect_uri"] = request.build_absolute_uri(self.get_login_callback_url())
        params["scope"] = "email,publish_stream,read_stream"
        
        url = ("https://graph.facebook.com/oauth/authorize?%s" % 
            urllib.urlencode(params))
        response = HttpResponseRedirect(url)
    
        return self.login_response(request, response)    
    
    def login_request_callback(self, request):
        user = authenticate(request=request)

        if not user:
            request.COOKIES.pop(FACEBOOK_API_KEY + '_session_key', None)
            request.COOKIES.pop(FACEBOOK_API_KEY + '_user', None)
    
            # TODO: maybe the project has its own login page?
            logging.warn("SOCIALAUTH: Couldn't authenticate user with Django,"
                          "redirecting to Login page")
            return HttpResponseRedirect(reverse('socialauth_login_page'))
    
        login(request, user)
        logging.debug("SOCIALAUTH: Successfully logged in with Facebook!")
        
        return self.login_success(request)
    
    def logout(self, request, response):
        # Delete the facebook cookie
        response.delete_cookie("fbs_" + FACEBOOK_APP_ID)
    
    def authenticate(self, request, user=None):
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
        uid = fb_data['id']
            
        try:
            fb_user = FacebookUserProfile.objects.get(facebook_uid=uid)
            return fb_user.user

        except FacebookUserProfile.DoesNotExist:
            username = 'FB_' + uid
            if not user:
                try:
                    user = User.objects.get(email=fb_data['email'])
                except User.DoesNotExist:
                    user = False
                
                try:
                    email = EmailAddress.objects.get(email=fb_data['email'])
                except:
                    email = False
                
            if not user and not email:
                user = User.objects.create(username=username,
                                           email=fb_data['email'],
                                           first_name=fb_data['first_name'],
                                           last_name=fb_data['last_name']
                                          )
                user.save()
                user.groups.add('1')
                
                # Pinax or user_profile support - store profile info
                try:
                    profile = user.get_profile()
                    profile.name = fb_data['first_name'] + ' ' + fb_data['last_name']
                    profile.save()
                    
                    EmailAddress(user=user,
                             email=user.email,
                             verified=True,
                             primary=True).save()
                except:
                    pass
            
            # Pinax or emailconfirmation support - email verification
            if email:
                user = email.user
                if email.verified == False:
                    email.verified = True
                    email.primary = True
                    email.save()

            link = fb_data.get('link')
            
            FacebookUserProfile(facebook_uid=uid,
                                user=user,
                                url=link,
                                access_token=access_token).save()
            
            auth_meta = AuthMeta(user=user, provider='Facebook').save()
                
            return user