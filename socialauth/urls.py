from django.conf.urls.defaults import *
from openid_consumer.views import complete, signout
from django.views.generic.simple import direct_to_template

#Login Views
urlpatterns = patterns('socialauth.views',
    url(r'^login/$', 'login_page', name='socialauth_login_page'),
    url(r'^login/(?P<auth_provider>\w+)/$', 'login_request', name='socialauth_login'),
    url(r'^login/(?P<auth_provider>\w+)/callback/$', 'login_request_callback', name='socialauth_login_callback'),
    
    url(r'^facebook_login/xd_receiver.htm$', direct_to_template, {'template':'socialauth/xd_receiver.htm'}, name='socialauth_xd_receiver'),

    url(r'^openid_login/$', 'openid_login_page', name='socialauth_openid_login_page'),
    url(r'^yahoo_login/$', 'yahoo_login', name='socialauth_yahoo_login'),
    url(r'^yahoo_login/complete/$', complete, name='socialauth_yahoo_complete'),
    url(r'^gmail_login/$', 'gmail_login', name='socialauth_google_login'),
    url(r'^gmail_login/complete/$', complete, name='socialauth_google_complete'),
    url(r'^openid/$', 'openid_login', name='socialauth_openid_login'),
    url(r'^openid/complete/$', complete, name='socialauth_openid_complete'),
    url(r'^openid/signout/$', signout, name='openid_signout'),
    url(r'^openid/done/$', 'openid_done', name='openid_openid_done'),
)

#Other views.
urlpatterns += patterns('socialauth.views',
    url(r'^$', 'login_page', name='socialauth_index'),                        
    url(r'^logout/$', 'social_logout',  name='socialauth_social_logout'),
    url(r'^_closeDialog/$', 'closeDialog',  name='socialauth_close_dialog'),
) 

