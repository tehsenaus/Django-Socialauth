
from oauth_provider import *

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
