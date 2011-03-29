from django.conf import settings
from django.core.exceptions import ImproperlyConfigured
from django.utils import simplejson as json
from socialauth.lib import twitter
from oauth import oauth
import logging
from .oauth_provider import OAuth, OAuthDriver

class TwitterOAuthDriver(OAuthDriver):
    server_url = 'twitter.com'
    request_token_url = 'https://twitter.com/oauth/request_token'
    access_token_url = 'https://twitter.com/oauth/access_token'
    authorize_url = 'http://twitter.com/oauth/authorize'
    credentials_url = 'https://twitter.com/account/verify_credentials.json'
    
    try:
        consumer_key = settings.TWITTER_CONSUMER_KEY
        consumer_secret = settings.TWITTER_CONSUMER_SECRET
    except AttributeError:
        raise ImproperlyConfigured, \
            "Missing settings for Twitter authentication: %s" \
            % (e)
    
    def get_user_info(self, token):
       oauth_request = oauth.OAuthRequest.from_consumer_and_token(self.consumer, token=token, http_url=self.credentials_url)
       oauth_request.sign_request(self.signature_method, self.consumer, token)
       self.connection.request(oauth_request.http_method, oauth_request.to_url()) 
       response = self.connection.getresponse().read()
       return twitter.User.NewFromJsonDict(json.loads(response))



class Twitter(OAuth):
    """Twitter OAuth"""
    
    oauth_driver = TwitterOAuthDriver
    
    def process_login(self, request):
        '''
            authenticates the token by requesting user information
            from twitter
        '''
        
        # If we've been denied, put them back to the signin page
        # They probably meant to sign in with facebook >:D
        if request.GET.get('denied', False):
            return None
    
        access_token = self.get_access_token(request)
        if not access_token:
            logging.error("Twitter: failed to get access token")
            return None
        
        try:
            userinfo = self.oauth_driver.get_user_info(access_token)
        except Exception, e:
            # If we cannot get the user information, 
            # user cannot be authenticated
            logging.error("Twitter: failed to get user info: %s", e)
            return None
        
        first_name, sep, last_name = userinfo.name.partition(' ')
        
        return dict(
            uid=userinfo.id,
            username = userinfo.screen_name,
            url=userinfo.url,
            first_name=first_name, last_name=last_name,
            token = access_token.to_string(),
            
            avatar_url=userinfo.profile_image_url,
            location=userinfo.location,
            description=userinfo.description
        )


