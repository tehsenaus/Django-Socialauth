import logging
import urllib
import oauth2 as oauth

from django.shortcuts import render_to_response
from django.template import RequestContext
from django.contrib.auth import authenticate, login
from django.http import HttpResponseRedirect
from django.core.urlresolvers import reverse
from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.contrib.auth.views import logout

from socialauth.models import AuthMeta
from socialauth.forms import EditProfileForm

from openid_consumer.views import begin
from socialauth.lib import oauthtwitter2 as oauthtwitter

from socialauth.lib.linkedin import *

from .settings import SOCIALAUTH_PROVIDERS_MAP

# Support for named login redirect URL
ADD_LOGIN_REDIRECT_URL_NAME = getattr(settings, 'ADD_LOGIN_REDIRECT_URL_NAME', '')
try:
    ADD_LOGIN_REDIRECT_URL = reverse(ADD_LOGIN_REDIRECT_URLNAME)
except:
    ADD_LOGIN_REDIRECT_URL = getattr(settings, 'ADD_LOGIN_REDIRECT_URL', '/')
LOGIN_REDIRECT_URL = getattr(settings, 'LOGIN_REDIRECT_URL', '')
LOGIN_URL = getattr(settings, 'LOGIN_URL', '')
LOGOUT_REDIRECT_URL = getattr(settings, 'LOGOUT_REDIRECT_URL', '')

TWITTER_CONSUMER_KEY = getattr(settings, 'TWITTER_CONSUMER_KEY', '')
TWITTER_CONSUMER_SECRET = getattr(settings, 'TWITTER_CONSUMER_SECRET', '')


def login_page(request):
    try:
        # Support for Pinax login URL
        response = HttpResponseRedirect(reverse('acct_login'))
        return response
    except:
        return render_to_response('socialauth/login_page.html', {
                              'next': request.GET.get('next', LOGIN_REDIRECT_URL),
                              },
                              context_instance=RequestContext(request))

def login_request(request, provider_name, *args, **kwargs):
    try:
        provider = SOCIALAUTH_PROVIDERS_MAP[provider_name]()
    except KeyError:
        logging.error("Socialauth: No such provider: %s", provider_name)
        return HttpResponseRedirect(reverse('socialauth_login_page'))
    
    return provider.login_request(request, *args, **kwargs)

def login_request_callback(request, provider_name, *args, **kwargs):
    try:
        provider = SOCIALAUTH_PROVIDERS_MAP[provider_name]()
    except KeyError:
        logging.error("Socialauth: No such provider: %s", provider_name)
        return HttpResponseRedirect(reverse('socialauth_login_page'))
    
    return provider.login_request_callback(request, *args, **kwargs)


def twitter_login(request):
    next = request.GET.get('next', None)
    if next:
        request.session['twitter_login_next'] = next
    
    twitter = oauthtwitter.TwitterOAuthClient(TWITTER_CONSUMER_KEY, 
                                              TWITTER_CONSUMER_SECRET)
    request_token = twitter.fetch_request_token(
                    callback=request.build_absolute_uri(
                    reverse('socialauth_twitter_login_done')))
    request.session['request_token'] = request_token.to_string()
    signin_url = twitter.authorize_token_url(request_token)
    return HttpResponseRedirect(signin_url)

def twitter_login_done(request):
    request_token = request.session.get('request_token', None)
    verifier = request.GET.get('oauth_verifier', None)
    denied = request.GET.get('denied', None)
    
    # If we've been denied, put them back to the signin page
    # They probably meant to sign in with facebook >:D
    if denied:
        return HttpResponseRedirect(reverse("socialauth_login_page"))

    # If there is no request_token for session,
    # Means we didn't redirect user to twitter
    if not request_token:
        # Redirect the user to the login page,
        return HttpResponseRedirect(reverse("socialauth_login_page"))

    token = oauth.Token.from_string(request_token)

    # If the token from session and token from twitter does not match
    # means something bad happened to tokens
    if token.key != request.GET.get('oauth_token', 'no-token'):
        del_dict_key(request.session, 'request_token')
        # Redirect the user to the login page
        return HttpResponseRedirect(reverse("socialauth_login_page"))

    twitter = oauthtwitter.TwitterOAuthClient(TWITTER_CONSUMER_KEY, 
                                              TWITTER_CONSUMER_SECRET)
    access_token = twitter.fetch_access_token(token, verifier)

    request.session['access_token'] = access_token.to_string()
    user = authenticate(twitter_access_token=access_token)
  
    # if user is authenticated then login user
    if user:
        login(request, user)
    else:
        # We were not able to authenticate user
        # Redirect to login page
        del_dict_key(request.session, 'access_token')
        del_dict_key(request.session, 'request_token')
        return HttpResponseRedirect(reverse('socialauth_login_page'))

    # authentication was successful, use is now logged in
    next = request.session.get('twitter_login_next', None)
    if next:
        del_dict_key(request.session, 'twitter_login_next')
        return HttpResponseRedirect(next)
    else:
        return HttpResponseRedirect(LOGIN_REDIRECT_URL)

def openid_login(request):
    if 'openid_next' in request.GET:
        request.session['openid_next'] = request.GET.get('openid_next')
    if 'openid_identifier' in request.GET:
        user_url = request.GET.get('openid_identifier')
        request.session['openid_provider'] = user_url
        return begin(request, user_url=user_url)
    else:
        request.session['openid_provider'] = 'Openid'
        return begin(request)

def gmail_login(request):
    request.session['openid_provider'] = 'Google'
    return begin(request, user_url='https://www.google.com/accounts/o8/id')

def gmail_login_complete(request):
    pass


def yahoo_login(request):
    request.session['openid_provider'] = 'Yahoo'
    return begin(request, user_url='https://me.yahoo.com/')

def openid_done(request, provider=None):
    """
    When the request reaches here, the user has completed the Openid
    authentication flow. He has authorised us to login via Openid, so
    request.openid is populated.
    After coming here, we want to check if we are seeing this openid first time.
    If we are, we will create a new Django user for this Openid, else login the
    existing openid.
    """
    
    if not provider:
        provider = request.session.get('openid_provider', '')
    if hasattr(request,'openid') and request.openid:
        #check for already existing associations
        openid_key = str(request.openid)
    
        #authenticate and login
        try:
            user = authenticate(openid_key=openid_key, 
                                request=request, 
                                provider=provider)
        except:
            user = None
        
        if user:
            login(request, user)
            if 'openid_next' in request.session :
                openid_next = request.session.get('openid_next')
                if len(openid_next.strip()) >  0 :
                    return HttpResponseRedirect(openid_next)
            return HttpResponseRedirect(LOGIN_REDIRECT_URL)
            # redirect_url = reverse('socialauth_editprofile')
            # return HttpResponseRedirect(redirect_url)
        else:
            return HttpResponseRedirect(LOGIN_URL)
    else:
        return HttpResponseRedirect(LOGIN_URL)



def openid_login_page(request):
    return render_to_response('openid/index.html', 
                              context_instance=RequestContext(request))

def social_logout(request):
    # TODO: handle FB cookies, session etc.

    # let the openid_consumer app handle openid-related cleanup
    from openid_consumer.views import signout as oid_signout
    oid_signout(request)

    # normal logout
    logout_response = logout(request)

    if 'next' in request.GET:
        response = HttpResponseRedirect(request.GET.get('next'))
    elif LOGOUT_REDIRECT_URL:
        response = HttpResponseRedirect(LOGOUT_REDIRECT_URL)
    else:
        response = logout_response

    for provider in SOCIALAUTH_PROVIDERS_MAP.values():
        provider().logout(request, response)

    return response

def closeDialog(request):
    return HttpResponse("<script>window.close()</script>")
