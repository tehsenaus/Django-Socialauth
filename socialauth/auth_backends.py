from django.contrib.auth.models import User
from django.contrib.sites.models import Site
from django.core.urlresolvers import reverse
from django.conf import settings
from django.core.files import File

from socialauth.lib import oauthtwitter2 as oauthtwitter
from socialauth.models import OpenidProfile as UserAssociation, \
TwitterUserProfile, FacebookUserProfile, LinkedInUserProfile, AuthMeta
from socialauth.lib.linkedin import *

import facebook
try:
    from emailconfirmation.models import EmailAddress
except:
    pass

import urllib
import random



