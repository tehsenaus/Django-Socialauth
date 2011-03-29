from django.conf import settings
from django.core.exceptions import ImproperlyConfigured
from socialauth.lib import linkedin
from .oauth_provider import OAuth, OAuthDriver


class LinkedInOAuthDriver(OAuthDriver):
    server_url = 'api.linkedin.com'
    request_token_url = 'https://api.linkedin.com/uas/oauth/requestToken'
    access_token_url = 'https://api.linkedin.com/uas/oauth/accessToken'
    authorize_url = 'https://api.linkedin.com/uas/oauth/authorize'
    
    try:
        consumer_key = settings.LINKEDIN_CONSUMER_KEY
        consumer_secret = settings.LINKEDIN_CONSUMER_SECRET
    except AttributeError:
        raise ImproperlyConfigured, \
            "Missing settings for LinkedIn authentication: %s" \
            % (e)
    
    @property
    def sig_method(self):
        return self.signature_method


class LinkedIn(OAuth):
    oauth_driver = LinkedInOAuthDriver
    
    def process_login(self, request):
        linkedin_access_token = self.get_access_token(request)
        if not linkedin_access_token:
            return None
        
        profile = (linkedin.ProfileApi(self.oauth_driver)
                   .getMyProfile(access_token=linkedin_access_token))
        
        return dict(
            uid = profile.id,
            first_name = profile.firstname,
            last_name = profile.lastname,
            url = profile.profile_url,
            avatar_url = profile.picture_url,
            location = profile.location,
            company = profile.company,
            industry = profile.industry,
            headline = profile.headline,
        )

