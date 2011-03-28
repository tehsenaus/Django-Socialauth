from django.conf import settings
import sys, logging
from socialauth.providers.base import Provider

SOCIALAUTH_PROVIDERS_MAP = {}
for p in settings.AUTHENTICATION_BACKENDS:
    module, sep, klass = p.rpartition('.')
    __import__(module)
    module = sys.modules[module]
    provider = getattr(module, klass)
    
    if issubclass(provider, Provider):
        SOCIALAUTH_PROVIDERS_MAP[provider.provider_name] = provider
    

logging.debug("Socialauth Providers: %s", SOCIALAUTH_PROVIDERS_MAP)
