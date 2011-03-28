from django.conf import settings
from .oauth import OAuth

TWITTER_CONSUMER_KEY = getattr(settings, 'TWITTER_CONSUMER_KEY', '')
TWITTER_CONSUMER_SECRET = getattr(settings, 'TWITTER_CONSUMER_SECRET', '')

class Twitter(OAuth):
    """Twitter OAuth"""
    
    def authenticate(self, twitter_access_token, user=None):
        '''
            authenticates the token by requesting user information
            from twitter
        '''
        # twitter = oauthtwitter.OAuthApi(TWITTER_CONSUMER_KEY,
        #                                  TWITTER_CONSUMER_SECRET,
        #                                  twitter_access_token)
        twitter = oauthtwitter.TwitterOAuthClient(
                                            settings.TWITTER_CONSUMER_KEY,
                                            settings.TWITTER_CONSUMER_SECRET)
        try:
            userinfo = twitter.get_user_info(twitter_access_token)
        except:
            # If we cannot get the user information, 
            # user cannot be authenticated
            raise

        screen_name = userinfo.screen_name
        twitter_id = userinfo.id
        
        try:
            user_profile = (TwitterUserProfile.objects
                            .get(screen_name=screen_name))
            
            # Update Twitter Profile
            user_profile.url = userinfo.url
            user_profile.location = userinfo.location
            user_profile.description = userinfo.description
            user_profile.profile_image_url = userinfo.profile_image_url
            user_profile.save()
            
            user = user_profile.user
            return user
        except TwitterUserProfile.DoesNotExist:
            # Create new user
            if not user:
                same_name_count = (User.objects
                                   .filter(username__startswith=screen_name)
                                   .count())
                if same_name_count:
                    username = '%s%s' % (screen_name, same_name_count + 1)
                else:
                    username = screen_name
                user = User(username=username)
                name_data = userinfo.name.split()
                try:
                    first_name, last_name = (name_data[0], 
                                            ' '.join(name_data[1:]))
                except:
                    first_name, last_name =  screen_name, ''
                user.first_name, user.last_name = first_name, last_name
                #user.email = screen_name + "@socialauth"
                #user.email = '%s@example.twitter.com'%(userinfo.screen_name)
                user.save()
                
            user_profile = TwitterUserProfile(user=user, 
                                              screen_name=screen_name)
            user_profile.access_token = str(twitter_access_token)
            user_profile.url = userinfo.url
            user_profile.location = userinfo.location
            user_profile.description = userinfo.description
            user_profile.profile_image_url = userinfo.profile_image_url
            user_profile.save()
            
            auth_meta = AuthMeta(user=user, provider='Twitter').save()
                
            return user