from django.contrib.auth.models import User
from .models import AuthMeta

class SocialAuthBackend(object):
    def authenticate_meta(self, auth_provider, uid, user=None, email=None, first_name=None, last_name=None, **kwargs):
        try:
            meta,created = AuthMeta.objects.get(provider=auth_provider.provider_name, uid=uid),False
        except AuthMeta.DoesNotExist:
            meta,created = AuthMeta(provider=auth_provider.provider_name, uid=uid),True
        
        if not user.is_authenticated(): user = None
        
        if not created and not user:
            return meta.user
        
        if not user and email and auth_provider.has_secure_email:
            # Try to lookup existing user via email address
            try:
                user = User.objects.get(email=email)
            except User.DoesNotExist:
                pass
        
        if not user:
            user = User.objects.create(
                    username="%s::%s" % (auth_provider.provider_name, uid),
                    email=email, first_name=first_name, last_name=last_name
            )
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

