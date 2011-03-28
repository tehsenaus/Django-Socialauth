from django.db import models
from django.contrib.auth.models import User
from django.conf import settings
from .base import Provider

OPENID_AX_PROVIDER_MAP = getattr(settings, 'OPENID_AX_PROVIDER_MAP', {})


class OpenId(Provider):
    def authenticate(self, openid_key, request, provider, user=None):
        try:
            assoc = UserAssociation.objects.get(openid_key=openid_key)
            return assoc.user
        except UserAssociation.DoesNotExist:
            #fetch if openid provider provides any simple registration fields
            nickname = None
            email = None
            firstname = None
            lastname = None
            
            if request.openid and request.openid.sreg:
                email = request.openid.sreg.get('email')
                nickname = request.openid.sreg.get('nickname')
                firstname, lastname = (request.openid.sreg
                                       .get('fullname', ' ')
                                       .split(' ', 1))
            elif request.openid and request.openid.ax:
                email = \
                    (request.openid.ax
                     .getSingle('http://axschema.org/contact/email'))
                if 'google' in provider:
                    ax_schema = OPENID_AX_PROVIDER_MAP['Google']
                    firstname = (request.openid.ax
                                 .getSingle(ax_schema['firstname']))
                    lastname = (request.openid.ax
                                .getSingle(ax_schema['lastname']))
                    nickname = email.split('@')[0]
                else:
                    ax_schema = OPENID_AX_PROVIDER_MAP['Default']
                    try:
                        #should be replaced by correct schema
                        nickname = (request.openid.ax
                                    .getSingle(ax_schema['nickname']))
                    except:
                        pass
                    try:
                        (firstname, 
                            lastname) = (request.openid.ax
                                         .getSingle(ax_schema['fullname'])
                                         .split(' ', 1))
                    except:
                        pass

            if nickname is None :
                nickname =  ''.join(
                                    [random
                                     .choice('abcdefghijklmnopqrstuvwxyz')
                                     for i in xrange(10)])
            
            name_count = (User.objects
                          .filter(username__startswith=nickname)
                          .count())
            if name_count:
                username = '%s%d' % (nickname, name_count + 1)
            else:
                username = '%s' % (nickname)
                
            if email is None:
                valid_username = False
                email =  "%s@socialauth.local" % (username)
            else:
                valid_username = True
            
            if not user:
                user = User.objects.create_user(username, email or '')
                
            user.first_name = firstname or ''
            user.last_name = lastname or ''
            user.save()
    
            #create openid association
            assoc = UserAssociation()
            assoc.openid_key = openid_key
            assoc.user = user
            if email:
                assoc.email = email
            if nickname:
                assoc.nickname = nickname
            if valid_username:
                assoc.is_username_valid = True
            assoc.save()
            
            #Create AuthMeta
            # auth_meta = 
            #             AuthMeta(user=user, 
            #                        provider=provider, 
            #                        provider_model='OpenidProfile', 
            #                        provider_id=assoc.pk)
            auth_meta = AuthMeta(user=user, provider=provider)
            auth_meta.save()
            return user
        
    def GooglesAX(self,openid_response):
        email = (openid_response.ax
                 .getSingle('http://axschema.org/contact/email'))
        firstname = (openid_response.ax
                     .getSingle('http://axschema.org/namePerson/first'))
        lastname = (openid_response.ax
                    .getSingle('http://axschema.org/namePerson/last'))
        # country = 
        #    (openid_response.ax
        #        .getSingle('http://axschema.org/contact/country/home'))
        # language = 
        #    openid_response.ax.getSingle('http://axschema.org/pref/language')
        return locals()

class OpenidProfile(models.Model):
    """A class associating an User to a Openid"""
    openid_key = models.CharField(max_length=200, unique=True, db_index=True)
    
    user = models.ForeignKey(User, related_name='openid_profiles')
    is_username_valid = models.BooleanField(default=False)
    #Values which we get from openid.sreg
    email = models.EmailField()
    nickname = models.CharField(max_length=100)
    
    
    def __unicode__(self):
        return unicode(self.openid_key)
    
    def __repr__(self):
        return unicode(self.openid_key)