from django.contrib.auth.models import User
from .models import AuthMeta

class SocialAuthBackend(object):
    def authenticate_meta(self, auth_provider, uid, user=None, username=None, password=None, email='', first_name=None, last_name=None, **kwargs):
        """
            Retrieves and creates (if necessary) authentication associations to a user account.
            If user is None, a new user account will be created.
            
            Note: if an association already exists, it is returned as-is (even if it is for a different user).
        """
        try:
            return AuthMeta.objects.get(provider=auth_provider.provider_name, uid=uid)
        except AuthMeta.DoesNotExist:
            meta = AuthMeta(provider=auth_provider.provider_name, uid=uid)
        
        if not user.is_authenticated(): user = None
        if not user:
            if (username and User.objects.filter(username=username)) or not username:
               username = "%s::%s" % (auth_provider.provider_name, username or uid)
            
            user = User.objects.create_user(
                    username=username, password=password,
                    email=email
            )
            user.first_name=first_name
            user.last_name=last_name
            user.save()
        
        meta.update(user, **kwargs)
        meta.save()
        return meta
    
    def authenticate(self, *args, **kwargs):
        meta = self.authenticate_meta(*args, **kwargs)
        return meta and meta.user
    
    def get_user(self, user_id):
        try:
            return User.objects.get(pk=user_id)
        except:
            return None

