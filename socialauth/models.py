from django.db import models
from django.contrib.auth.models import User
from django.utils.encoding import smart_unicode
from socialauth.providers.base import ProviderModel
import sys
from .fields import PickledObjectField
from .settings import SOCIALAUTH_PROVIDERS_MAP

# Import Model classes from all enabled providers
for provider in SOCIALAUTH_PROVIDERS_MAP.values():
    module = sys.modules[provider.__module__]
    for name in dir(module):
        item = getattr(module, name)
        if isinstance(item, type) and issubclass(item, ProviderModel):
            globals()[name] = item

class AuthMetaManager(models.Manager):
    def get_for_request(self, request):
        return self.filter(provider=request.auth_provider.provider_name, uid=request.auth['uid'])


class AuthMeta(ProviderModel):
    """Metadata for Authentication"""
    def __unicode__(self):
        return '%s - %s' % (smart_unicode(self.user), self.provider)
    
    objects = AuthMetaManager()
    
    user = models.ForeignKey(User)
    provider = models.CharField(max_length=50)
    uid = models.CharField(max_length=255)
    username = models.CharField(max_length=255, null=True, blank=True)
    url = models.TextField(null=True, blank=True)
    token = models.TextField(null=True, blank=True)
    info = PickledObjectField()
    
    class Meta:
        unique_together = ('provider','uid')
    
    def update(self, user, username=None, url=None, token=None, **info):
        self.user = user
        if username: self.username = username
        if url: self.url = url
        if token: self.token = token
        if info: self.info = info
