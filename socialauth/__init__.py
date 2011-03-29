
from django.contrib import auth
import logging

def authenticate(request):
    if request.auth:
        return auth.authenticate(auth_provider=request.auth_provider, user=request.user, **request.auth)
