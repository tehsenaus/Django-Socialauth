import logging
import urllib
import oauth2 as oauth

from django.shortcuts import render_to_response
from django.template import RequestContext
from django.contrib.auth import login
from django.http import HttpResponseRedirect
from django.core.urlresolvers import reverse
from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.contrib.auth.views import logout

from socialauth.models import AuthMeta
from socialauth.forms import EditProfileForm

from openid_consumer.views import begin

from . import get_auth_provider, authenticate, del_dict_key
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

NULL_CALLBACK = lambda request,user: None
 

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

def login_request(request, auth_provider, *args, **kwargs):
    provider = get_auth_provider(auth_provider)
    if not provider: return HttpResponseRedirect(reverse('socialauth_login_page'))
    
    response = provider.login_request(request, *args, **kwargs)
    
    next = request.GET.get('next', None)
    if next:
        request.session['redirect'] = next
        response.set_cookie('redirect', value=next)
    
    return response


def login_request_callback(request, auth_provider, on_login=NULL_CALLBACK, on_inactive=NULL_CALLBACK):
    """
    Default login request callback - authenticates the user, and redirects to
    the requested page. If the user is already logged in, this account is associated
    with them. 
    """
    
    user = authenticate(request)
    if not user:
        return HttpResponseRedirect(reverse('socialauth_login_page'))
    
    if not user.is_active:
        response = on_inactive(request, user)
        if response: return response
        logging.warn("User account %s disabled, attempted login from %s", user, auth_provider)
        return HttpResponseRedirect(reverse('socialauth_login_page'))
    
    login(request, user)
    
    response = on_login(request, user)
    if response: return response
    
    next = request.GET.get('next', None)
    
    if not next:
        if request.COOKIES.get('redirect', False):
            next = request.COOKIES.get('redirect')
        else:
            next = request.session.get('redirect', False)
    
    if next:
        response = HttpResponseRedirect(next)
    else:
        response = HttpResponseRedirect(settings.LOGIN_REDIRECT_URL)

    response.delete_cookie('redirect')
    del_dict_key(request.session, 'redirect')

    return response



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

