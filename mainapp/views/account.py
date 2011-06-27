from django.shortcuts import render_to_response, get_object_or_404
from django.http import HttpResponseRedirect
from django.core.urlresolvers import reverse
from mainapp.models import UserProfile, Report, ReportSubscriber,ReportUpdate
from mainapp.forms import FMSNewRegistrationForm,FMSAuthenticationForm, EditProfileForm
from django.template import Context, RequestContext
from django.contrib.auth.decorators import login_required
from django.db import connection,transaction
from django.db.models import Q
from django.utils.datastructures import SortedDict
from social_auth.backends import get_backend
from social_auth.models import UserSocialAuth
from django.conf import settings
from django.contrib.auth import login, REDIRECT_FIELD_NAME

LOGO_OFFSETS = {    'facebook': 0,
                    'twitter': -128,
                    'google': -192,
                    'dummy':0  
                }    

class SocialProvider(object):
    def __init__(self, name):
        self.name=name
        self.key=name.lower()
        self.logo_offset=LOGO_OFFSETS[ self.key ]
    
    def url(self):
        return '/accounts/login/%s/' % [ self.key ]
    
SUPPORTED_SOCIAL_PROVIDERS = [ 
                SocialProvider('Facebook'),
                SocialProvider('Twitter'),
                SocialProvider('Google') ]

DEFAULT_REDIRECT = getattr(settings, 'SOCIAL_AUTH_LOGIN_REDIRECT_URL', '') or \
                   getattr(settings, 'LOGIN_REDIRECT_URL', '')


@login_required
def home( request ):
    email = request.user.email
    subscriberQ = Q(reportsubscriber__email=email,reportsubscriber__is_confirmed=True)
    updaterQ = Q(reportupdate__email=email,reportupdate__is_confirmed=True)
    allreports = Report.objects.filter(subscriberQ | updaterQ).order_by('is_fixed','created_at').extra(select=SortedDict([('is_reporter','select case when bool_or(report_updates.first_update) then true else false end from report_updates where report_updates.email=%s and report_updates.is_confirmed=true and report_updates.report_id=reports.id'), 
                                                                                        ('is_updater','select case when count(report_updates.id) > 0 then true else false end from report_updates where report_updates.report_id=reports.id and report_updates.first_update=false and report_updates.email=%s and report_updates.is_confirmed=true'),                                                                                        ('days_open','case when reports.is_fixed then date(reports.fixed_at) - date(reports.created_at) else CURRENT_DATE - date(reports.created_at) end')]), select_params=( email, email )).distinct()
    return render_to_response("account/home.html",
                {"profile": request.user.get_profile(),
                 'allreports':allreports },
                context_instance=RequestContext(request))

@login_required
def edit( request ):
    if request.method == 'POST':
        form = EditProfileForm(request.POST, instance=request.user.get_profile())
        if form.is_valid():
            form.save()
            # redirect after save
            return HttpResponseRedirect( reverse('account_home'))
    else:
        form = EditProfileForm( instance=request.user.get_profile())

    return render_to_response("account/edit.html", { 'form': form },
                              context_instance=RequestContext(request))

    return render_to_response("account/edit.html")

@transaction.commit_on_success
def socialauth_complete( request, backend ):    
    """
       Authentication complete process -- override from the
       default in django-social-auth to:
        -- collect phone numbers on registration
        -- integrate with django-registration in order
           to confirm email for new users
    """
    backend = get_backend(backend, request, request.path)
    if not backend:
        return HttpResponseServerError('Incorrect authentication service')

    try:
        user = backend.auth_complete()
    except ValueError, e:  # some Authentication error ocurred
        user = None
        error_key = getattr(settings, 'SOCIAL_AUTH_ERROR_KEY', 'error_msg')
        if error_key:  # store error in session
            request.session[error_key] = str(e)

    if user: 
        backend_name = backend.AUTH_BACKEND.name
        if getattr(user, 'is_active', True):
            # a returning active user
            login(request, user)
            if getattr(settings, 'SOCIAL_AUTH_SESSION_EXPIRATION', True):
                # Set session expiration date if present and not disabled by
                # setting
                social_user = user.social_auth.get(provider=backend_name)
                if social_user.expiration_delta():
                    request.session.set_expiry(social_user.expiration_delta())
            url = request.session.pop(REDIRECT_FIELD_NAME, '') or DEFAULT_REDIRECT
            return HttpResponseRedirect(url)
        else:
            # User created but not yet activated. 
            details = { 'username':user.username,
                        'first_name':user.first_name,
                        'last_name': user.last_name }

            if user.email and user.email != '':
                details[ 'email' ] = user.email
            social_user = UserSocialAuth.objects.get(user=user)        
            form = FMSNewRegistrationForm( initial=details )
            return render_to_response("registration/registration_form.html",
                                          {'form': form,
                                           'social_connect': SocialProvider(backend.AUTH_BACKEND.name.capitalize()) },
                                          context_instance=RequestContext(request))

    # some big error.
    url = getattr(settings, 'LOGIN_ERROR_URL', settings.LOGIN_URL)
    return HttpResponseRedirect(url)


def error(request):
    error_msg = request.session.pop(settings.SOCIAL_AUTH_ERROR_KEY, None)
    return render_to_response('registration/error.html', {'social_error': error_msg},
                              RequestContext(request))


   