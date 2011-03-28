from django.conf import settings
from django.db import models
from django.contrib.auth.models import User
from django.contrib.auth import authenticate, login
from django.http import HttpResponseRedirect

class Provider(object):
    def login_request(self, request, *args, **kwargs):
        raise NotImplementedError()
    
    def login_request_callback(self, request, *args, **kwargs):
        raise NotImplementedError()
    
    def login_response(self, request, response):
        "Stores redirect url in session and cookie"
        
        next = request.GET.get('next', None)
        if next:
            request.session['redirect'] = next
            response.set_cookie('redirect', value=next)
        
        return response
    
    def logout(self, request, response):
        pass
    
    def login_success(self, request):
        """
        Should be called on login success - redirects the user to the page
        they requested.
        """
        
        next = request.GET.get('next', None)
        
        if not next:
            if request.COOKIES.get('redirect', False):
                response = HttpResponseRedirect(request.COOKIES.get('redirect'))
                response.delete_cookie('redirect')
                return response
            else:
                next = request.session.get('redirect', False)
                del_dict_key(request.session, 'redirect')
        if next:
            return HttpResponseRedirect(next)
        else:
            return HttpResponseRedirect(settings.LOGIN_REDIRECT_URL)
    
    @models.permalink
    def get_login_url(self):
        return ('socialauth_login', (self.provider_name,))
    
    @models.permalink
    def get_login_callback_url(self):
        return ('socialauth_login_callback', (self.provider_name,))
    
    def get_user(self, user_id):
        try:
            return User.objects.get(pk=user_id)
        except:
            return None
    
    class DefaultNameProperty(object):
        def __get__(self, instance, owner):
            return owner.__name__
    provider_name = DefaultNameProperty()

class ProviderModel(models.Model):
    class Meta:
        abstract = True
        app_label = 'socialauth'

class AuthMeta(ProviderModel):
    """Metadata for Authentication"""
    def __unicode__(self):
        return '%s - %s' % (smart_unicode(self.user), self.provider)
    
    user = models.ForeignKey(User)
    provider = models.CharField(max_length=50)
    is_email_filled = models.BooleanField(default=False)
    is_profile_modified = models.BooleanField(default=False)


def del_dict_key(src_dict, key):
    if key in src_dict:
        del src_dict[key]
