from django.conf import settings
from socialauth.lib import linkedin, oauthtwitter2
from .base import *

class OAuth(Provider):
    def login_request(self, request, *args, **kwargs):
        oauth = self.oauth_driver(self.consumer_key, self.consumer_secret)
        request_token = oauth.getRequestToken(callback=request.build_absolute_uri(
                    reverse('socialauth_login_done', (self.provider_name,))))
        request.session[self.provider_name + '__request_token'] = request_token
        signin_url = linkedin.getAuthorizeUrl(request_token)
        return HttpResponseRedirect(signin_url)
    
    def login_request_callback(self, request, *args, **kwargs):
        request_token = request.session.get(self.provider_name + '__request_token', None)

        if not request_token:
            # Send them to the login page
            return HttpResponseRedirect(reverse("socialauth_login_page"))
        try:
            oauth = self.oauth_driver(self.consumer_key, self.consumer_secret)
            verifier = request.GET.get('oauth_verifier', None)
            access_token = oauth.getAccessToken(request_token,verifier)
            request.session['access_token'] = access_token
            user = authenticate(linkedin_access_token=access_token)
        except:
            user = None
    
        # if user is authenticated then login user
        if user:
            login(request, user)
        else:
            # We were not able to authenticate user
            # Redirect to login page
            del_dict_key(request.session, 'access_token')
            del_dict_key(request.session, self.provider_name + '__request_token')
            return HttpResponseRedirect(reverse('socialauth_login_page'))
    
        # authentication was successful, user is now logged in
        return HttpResponseRedirect(LOGIN_REDIRECT_URL)
        

LINKEDIN_CONSUMER_KEY = getattr(settings, 'LINKEDIN_CONSUMER_KEY', '')
LINKEDIN_CONSUMER_SECRET = getattr(settings, 'LINKEDIN_CONSUMER_SECRET', '')

class OAuthLinkedIn(OAuth):
    provider_name = "LinkedIn"
    oauth_driver = linkedin.LinkedIn
    consumer_key = LINKEDIN_CONSUMER_KEY
    consumer_secret = LINKEDIN_CONSUMER_SECRET
    
    def authenticate(self, linkedin_access_token, user=None):
        linkedin = self.oauth_driver(self.consumer_key, )
        # get their profile
        
        profile = (linkedin.ProfileApi(linkedin)
                   .getMyProfile(access_token=linkedin_access_token))

        try:
            user_profile = (LinkedInUserProfile.objects
                            .get(linkedin_uid=profile.id))
            user = user_profile.user
            return user
        except LinkedInUserProfile.DoesNotExist:
            # Create a new user
            username = 'LI:%s' % profile.id

            if not user:
                user = User(username=username)
                user.first_name, user.last_name = (profile.firstname, 
                                                   profile.lastname)
                user.email = '%s@socialauth' % (username)
                user.save()
                
            userprofile = LinkedInUserProfile(user=user, 
                                              linkedin_uid=profile.id)
            userprofile.save()
            
            auth_meta = AuthMeta(user=user, provider='LinkedIn').save()
            return user
