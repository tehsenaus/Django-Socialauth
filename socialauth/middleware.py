
from .settings import SOCIALAUTH_PROVIDERS_MAP
from .views import login_request

class SocialAuthMiddleware(object):
    def process_view(self, request, view_func, view_args, view_kwargs):
        request.auth = None
        
        if view_func is login_request: return
        
        provider_name = view_kwargs.get('auth_provider', None)
        if provider_name is not None:
            try:
                provider = SOCIALAUTH_PROVIDERS_MAP[provider_name]()
            except KeyError:
                logging.error("Socialauth: No such provider: %s", provider_name)
                return
            
            request.auth = provider.process_login(request)
            request.auth_provider = provider

