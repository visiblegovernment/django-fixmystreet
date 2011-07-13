from django.conf.urls.defaults import *
from django.conf import settings
from django.http import HttpResponseRedirect
from django.contrib import admin
from mainapp.feeds import LatestReports, LatestReportsByCity, LatestReportsByWard, LatestUpdatesByReport
from mainapp.models import City
from social_auth.views import auth as social_auth
from social_auth.views import disconnect as social_disconnect
from registration.views import register
from mainapp.forms import FMSNewRegistrationForm,FMSAuthenticationForm
from mainapp.views.account import SUPPORTED_SOCIAL_PROVIDERS
from django.contrib.auth import views as auth_views
from mainapp.views.mobile import open311v2 
import mainapp.views.cities as cities


feeds = {
    'reports': LatestReports,
    'wards': LatestReportsByWard,
    'cities': LatestReportsByCity,
    'report_updates': LatestUpdatesByReport,
}

SSL_ON = not settings.DEBUG
    
admin.autodiscover()
urlpatterns = patterns('',
    (r'^admin/password_reset/$', 'django.contrib.auth.views.password_reset',{'SSL':SSL_ON}),
    (r'^password_reset/done/$', 'django.contrib.auth.views.password_reset_done'),
    (r'^reset/(?P<uidb36>[-\w]+)/(?P<token>[-\w]+)/$', 'django.contrib.auth.views.password_reset_confirm'),
    (r'^reset/done/$', 'django.contrib.auth.views.password_reset_complete'),
    (r'^admin/', admin.site.urls,{'SSL':SSL_ON}),
    (r'^feeds/(?P<url>.*)/$', 'django.contrib.syndication.views.feed', {'feed_dict': feeds}),
    (r'^i18n/', include('django.conf.urls.i18n')),
    url(r'^login/(?P<backend>[^/]+)/$', social_auth, name='begin'),
    url(r'^disconnect/(?P<backend>[^/]+)/$', social_disconnect, name='socialdisconnect'),

)

urlpatterns += patterns('mainapp.views.main',
    (r'^$', 'home', {}, 'home_url_name'),
    (r'^search', 'search_address'),
    (r'about/$', 'about',{}, 'about_url_name'),
    (r'posters/$', 'posters',{}, 'posters'),
)

urlpatterns += patterns('mainapp.views.faq',
    (r'^about/(\S+)$', 'show'),
)


urlpatterns += patterns('mainapp.views.promotion',
    (r'^promotions/(\w+)$', 'show'),
)

urlpatterns += patterns('mainapp.views.wards',
    (r'^wards/(\d+)', 'show'),       
    (r'^cities/(\d+)/wards/(\d+)', 'show_by_number'),           
)

urlpatterns += patterns('',
    (r'^cities/(\d+)$', cities.show ),       
    (r'^cities', cities.index, {}, 'cities_url_name'),
)

urlpatterns += patterns( 'mainapp.views.reports.updates',
    (r'^reports/updates/confirm/(\S+)', 'confirm'), 
    (r'^reports/updates/create/', 'create'), 
    (r'^reports/(\d+)/updates/', 'new'),
)


urlpatterns += patterns( 'mainapp.views.reports.subscribers',
    (r'^reports/subscribers/confirm/(\S+)', 'confirm'), 
    (r'^reports/subscribers/unsubscribe/(\S+)', 'unsubscribe'),
    (r'^reports/subscribers/create/', 'create'),
    (r'^reports/(\d+)/subscribers', 'new'),
)

urlpatterns += patterns( 'mainapp.views.reports.flags',
    (r'^reports/(\d+)/flags/thanks', 'thanks'),
    (r'^reports/(\d+)/flags', 'new'),
)

urlpatterns += patterns('mainapp.views.reports.main',
    (r'^reports/(\d+)$', 'show'),       
    (r'^reports/', 'new'),
)

urlpatterns += patterns('mainapp.views.contact',
    (r'^contact/thanks', 'thanks'),
    (r'^contact', 'new', {}, 'contact_url_name'),
)

urlpatterns += patterns('mainapp.views.ajax',
    (r'^ajax/categories/(\d+)', 'category_desc'),
)


urlpatterns += patterns('',
 url('^accounts/register/$', register, {'SSL':SSL_ON , 
                                        'form_class': FMSNewRegistrationForm,
                                         'extra_context': 
                                    { 'providers': SUPPORTED_SOCIAL_PROVIDERS } },name='registration_register'),
 url('^accounts/login/$',  auth_views.login, {'SSL':SSL_ON, 
                                              'template_name':'registration/login.html',
                                              'authentication_form':FMSAuthenticationForm,
                                              'extra_context': 
                     { 'providers': SUPPORTED_SOCIAL_PROVIDERS }}, name='auth_login'), 
 url(r'^accounts/logout/$',  auth_views.logout,
                           {'SSL':SSL_ON,
                            'next_page': '/'}, name='auth_logout' ),
 (r'^accounts/', include('registration.urls') )
)
 
urlpatterns += patterns('mainapp.views.account',
    url(r'^accounts/home/', 'home',{ 'SSL':SSL_ON },  name='account_home'),
    url(r'^accounts/edit/', 'edit', {'SSL':SSL_ON }, name='account_edit'),
    (r'^accounts/login/error/$', 'error'),
    url(r'^accounts/complete/(?P<backend>[^/]+)/$', 'socialauth_complete', {'SSL':SSL_ON }, name='socialauth_complete'),
)

urlpatterns += patterns('',
    (r'^open311/v2/', open311v2.xml.urls ),
)

if settings.DEBUG and 'TESTVIEW' in settings.__members__:
    urlpatterns += patterns ('',
    (r'^testview',include('django_testview.urls')))


#The following is used to serve up local media files like images
if settings.LOCAL_DEV:
    baseurlregex = r'^media/(?P<path>.*)$'
    urlpatterns += patterns('',
        (baseurlregex, 'django.views.static.serve',
        {'document_root':  settings.MEDIA_ROOT}),
    )
