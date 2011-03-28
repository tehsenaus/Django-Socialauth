from django.db import models
from django.contrib.auth.models import User
from django.utils.encoding import smart_unicode
from socialauth.providers.base import ProviderModel
import sys
from .settings import SOCIALAUTH_PROVIDERS_MAP

# Import Model classes from all enabled providers
for provider in SOCIALAUTH_PROVIDERS_MAP.values():
    module = sys.modules[provider.__module__]
    for name in dir(module):
        item = getattr(module, name)
        if isinstance(item, type) and issubclass(item, ProviderModel):
            globals()[name] = item




class TwitterUserProfile(models.Model):
    """
    For users who login via Twitter.
    """
    screen_name = models.CharField(max_length=200,
                                   unique=True,
                                   db_index=True)
    
    user = models.ForeignKey(User, related_name='twitter_profiles')
    access_token = models.CharField(max_length=255,
                                    blank=True,
                                    null=True,
                                    editable=False)
    profile_image_url = models.URLField(blank=True, null=True)
    location = models.TextField(blank=True, null=True)
    url = models.URLField(blank=True, null=True)
    description = models.CharField(max_length=160, blank=True, null=True)

    def __unicode__(self):
        return "%s's profile" % smart_unicode(self.user)
        
