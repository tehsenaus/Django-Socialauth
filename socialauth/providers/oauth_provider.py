from django.http import HttpResponseRedirect
from oauth import oauth
import httplib, logging

from .base import Provider

class OAuth(Provider):
    def __init__(self, *args, **kwargs):
        super(OAuth, self).__init__(*args, **kwargs)
        self.oauth_driver = self.oauth_driver()
    
    def login_request(self, request, *args, **kwargs):
        request_token = self.oauth_driver.get_request_token(
                callback=request.build_absolute_uri(self.get_login_callback_url()))
        request.session[self.provider_name + '__request_token'] = request_token
        signin_url = self.oauth_driver.get_authorize_url(request_token)
        return HttpResponseRedirect(signin_url)
    
    def get_access_token(self, request):
        request_token = request.session.pop(self.provider_name + '__request_token', None)
        verifier = request.GET.get('oauth_verifier', None)
        
        if not request_token or not verifier:
            return None
        
        return self.oauth_driver.get_access_token(request_token, verifier)
        


class OAuthDriver(object):
    "Generic OAuth 1.0a driver"
    
    signature_method = oauth.OAuthSignatureMethod_HMAC_SHA1()
    
    def __init__(self):
        self.connection = httplib.HTTPSConnection(self.server_url)
        self.consumer = oauth.OAuthConsumer(self.consumer_key, self.consumer_secret)

    def get_request_token(self, callback):

        oauth_request = oauth.OAuthRequest.from_consumer_and_token(self.consumer,
                        http_url = self.request_token_url, callback=callback)
        oauth_request.sign_request(self.signature_method, self.consumer, None)

        self.connection.request(oauth_request.http_method,
                        self.request_token_url, headers = oauth_request.to_header())
        response = self.connection.getresponse().read()
        
        try:
            token = oauth.OAuthToken.from_string(response)
        except:
            raise ValueError, "Failed to get request token from response:\n%s" % (response,)
        return token

    def get_authorize_url(self, token):
        """
        Get the URL that we can redirect the user to for authorization of our
        application.
        """
        oauth_request = oauth.OAuthRequest.from_consumer_and_token(self.consumer, token=token, http_url = self.authorize_url)
        return oauth_request.to_url()

    def get_access_token(self, token, verifier):
        """
        Using the verifier we obtained through the user's authorization of
        our application, get an access code.

        Note: token is the request token returned from the call to getRequestToken

        @return an oauth.Token object with the access token.  Use it like this:
                token.key -> Key
                token.secret -> Secret Key
        """
        token.verifier = verifier
        oauth_request = oauth.OAuthRequest.from_consumer_and_token(self.consumer, token=token,
                verifier=verifier, http_url=self.access_token_url)
        oauth_request.sign_request(self.signature_method, self.consumer, token)
        
        self.connection.request(oauth_request.http_method, oauth_request.to_url()) 
        response = self.connection.getresponse().read()
        return oauth.OAuthToken.from_string(response)
