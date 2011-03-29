
from django.contrib import auth
import logging

from .settings import SOCIALAUTH_PROVIDERS_MAP

def get_auth_provider(provider_name):
    try:
        return SOCIALAUTH_PROVIDERS_MAP[provider_name]()
    except KeyError:
        logging.error("Socialauth: No such provider: %s", auth_provider)


def authenticate(request):
    if request.auth:
        return auth.authenticate(auth_provider=request.auth_provider, user=request.user, **request.auth)

def del_dict_key(src_dict, key):
    if key in src_dict:
        del src_dict[key]
