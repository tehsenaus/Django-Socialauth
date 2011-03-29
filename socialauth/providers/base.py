from django.conf import settings
from django.db import models
from django.http import HttpResponseRedirect

class Provider(object):
    has_secure_email = False
    
    def login_request(self, request, *args, **kwargs):
        """
        Called to start the login process. This should return an
        appropriate HttpResponse.
        """
        raise NotImplementedError()
    
    def process_login(self, request):
        """
        Called by the middleware when an auth callback is detected. This method
        should attempt to finish the authorisation process, returning an info
        dict on success, or None on failure.
        
        At a minimum, the user info dict should be populated with:
            'uid' - a unique user ID
        
        Optional info:
            'username' - external username
            'first_name', 'last_name'
            'email'
            'url' - link to external profile
            'token' - token which can be used to access the external API 
        """
        raise NotImplementedError()
    
    def logout(self, request, response):
        pass
            
    @models.permalink
    def get_login_url(self):
        return ('socialauth_login', (self.provider_name,))
    
    @models.permalink
    def get_login_callback_url(self):
        return ('socialauth_login_callback', (self.provider_name,))
    
    class DefaultNameProperty(object):
        def __get__(self, instance, owner):
            return owner.__name__
    provider_name = DefaultNameProperty()

class ProviderModel(models.Model):
    class Meta:
        abstract = True
        app_label = 'socialauth'

