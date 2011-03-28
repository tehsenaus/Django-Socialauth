from django import template
from socialauth.settings import SOCIALAUTH_PROVIDERS_MAP

register = template.Library()

@register.simple_tag
def get_calculated_username(user):
    if hasattr(user, 'openidprofile_set') and user.openidprofile_set.filter().count():
        if user.openidprofile_set.filter(is_username_valid = True).count():
            return user.openidprofile_set.filter(is_username_valid = True)[0].user.username
        else:
            from django.core.urlresolvers import  reverse
            editprof_url = reverse('socialauth_editprofile')
            return u'Anonymous User. <a href="%s">Add name</a>'%editprof_url
    else:
        return user.username

@register.simple_tag
def login_url(provider_name):
    return SOCIALAUTH_PROVIDERS_MAP[provider_name]().get_login_url()

@register.simple_tag
def login_urls():
    "Returns a JSON object mapping provider names to login urls"
    
    return "{" + ",".join(("'%s':'%s'" % (n, p().get_login_url())
                           for n,p in SOCIALAUTH_PROVIDERS_MAP.iteritems())) + "}"
