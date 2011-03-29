from django.conf import settings
import sys, logging
from socialauth.providers.base import Provider

SOCIALAUTH_CALLBACK_VIEW = getattr(settings, 'SOCIALAUTH_CALLBACK_VIEW', 'socialauth.views.login_request_callback')

SOCIALAUTH_PROVIDERS_MAP = {}
for p in getattr(settings, 'SOCIALAUTH_PROVIDERS', ()):
    module, sep, klass = p.rpartition('.')
    __import__(module)
    module = sys.modules[module]
    provider = getattr(module, klass)
    
    if issubclass(provider, Provider):
        SOCIALAUTH_PROVIDERS_MAP[provider.provider_name] = provider
    

logging.debug("Socialauth Providers: %s", SOCIALAUTH_PROVIDERS_MAP)
