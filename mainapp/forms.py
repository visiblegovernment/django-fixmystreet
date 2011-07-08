from django import forms
from django.template.loader import render_to_string
from django.core.mail import send_mail
from fixmystreet import settings
from django.conf import settings
from mainapp.models import Ward, Report, ReportUpdate, ReportCategoryClass,ReportCategory,ReportSubscriber,DictToPoint,UserProfile
from django.utils.translation import ugettext_lazy as _
from django.contrib.gis.geos import fromstr
from django.forms.util import ErrorDict
from registration.forms import RegistrationForm
from registration.models import RegistrationProfile
from django.contrib.auth.models import User
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.sites.models import Site
from django.utils.encoding import force_unicode

class ContactForm(forms.Form):
    name = forms.CharField(max_length=100,
                           widget=forms.TextInput(attrs={ 'class': 'required' }),
                           label=_('Name'))
    email = forms.EmailField(widget=forms.TextInput(attrs=dict({ 'class': 'required' },
                                                               maxlength=200)),
                             label=_('Email'))
    body = forms.CharField(widget=forms.Textarea(attrs={ 'class': 'required' }),
                              label=_('Message'))
    
    def save(self, fail_silently=False):
        message = render_to_string("emails/contact/message.txt", self.cleaned_data )
        send_mail('FixMyStreet.ca User Message from %s' % self.cleaned_data['email'], message, 
                   settings.EMAIL_FROM_USER,[settings.ADMIN_EMAIL], fail_silently=False)


class ReportUpdateForm(forms.ModelForm):
    class Meta:
        model = ReportUpdate
        fields = ( 'desc','author','email','phone')

class ReportSubscriberForm(forms.ModelForm):
    class Meta:
        model = ReportSubscriber
        fields = ( 'email', )

    def __init__(self,data=None,files=None,initial=None, freeze_email=False):
        super(ReportSubscriberForm,self).__init__(data,files=files, initial=initial)
        if freeze_email:
            self.fields['email'].widget.attrs['readonly'] = 'readonly'
        
"""
    Do some pre-processing to
    render opt-groups (silently supported, but undocumented
    http://code.djangoproject.com/ticket/4412 )
"""
    
class CategoryChoiceField(forms.fields.ChoiceField):
    
    def __init__(self, ward=None,required=True, widget=None, label=None,
                 initial=None, help_text=None, *args, **kwargs):
        # assemble the opt groups.
        choices = []
        self.ward = ward
        choices.append( ('', _("Select a Category")) )
        if ward:
            categories = ward.city.get_categories()
            categories = categories.order_by('category_class')
        else:
            categories = []
            
        groups = {}
        for category in categories:
            catclass = str(category.category_class)
            if not groups.has_key(catclass):
                groups[catclass] = []
            groups[catclass].append((category.pk, category.name ))
        for catclass, values in groups.items():
            choices.append((catclass,values))

        super(CategoryChoiceField,self).__init__(choices=choices,required=required,widget=widget,label=label,initial=initial,help_text=help_text,*args,**kwargs)

    def clean(self, value):
        if not self.ward:
            # don't bother validating if we couldn't resolve
            # the ward... this will be picked up in another error
            return None
        
        super(CategoryChoiceField,self).clean(value)
        try:
            model = ReportCategory.objects.get(pk=value)
        except ReportCategory.DoesNotExist:
            raise ValidationError(self.error_messages['invalid_choice'])
        return model


class EditProfileForm(forms.ModelForm):
    class Meta:
        model = UserProfile
        fields = ( 'phone',)

class ReportUpdateForm(forms.ModelForm):
    class Meta:
        model = ReportUpdate
        fields = ( 'desc','author','email','phone')

    def __init__(self,data=None,files=None,initial=None, freeze_email=False):
        super(ReportUpdateForm,self).__init__(data,files=files, initial=initial)
        if freeze_email:
            self.fields['email'].widget.attrs['readonly'] = 'readonly'


class ReportForm(forms.ModelForm):
    """
    ReportForm --
    combines is_valid(), clean(), and save()
    etc. for both an update form and a report form

    (information for both models is submitted at
    the same time when a report is initially created)
    """

    class Meta:
        model = Report
        fields = ('lat','lon','title', 'address', 'category','photo')

    lat = forms.fields.CharField(widget=forms.widgets.HiddenInput)
    lon = forms.fields.CharField(widget=forms.widgets.HiddenInput)

    def __init__(self,data=None,files=None,initial=None,freeze_email=False):
        if data:
            d2p = DictToPoint(data,exceptclass=None)
        else:
            d2p = DictToPoint(initial,exceptclass=None)
        
        self.pnt = d2p.pnt()
        self.ward = d2p.ward()
        self.update_form = ReportUpdateForm(data=data,initial=initial,freeze_email=freeze_email)
        super(ReportForm,self).__init__(data,files, initial=initial)
        self.fields['category'] = CategoryChoiceField(self.ward)
    
    def clean(self):
        if self.pnt and not self.ward:
            raise forms.ValidationError("lat/lon not supported")

        # Always return the full collection of cleaned data.
        return self.cleaned_data

    def is_valid(self):
        report_valid = super(ReportForm,self).is_valid()
        update_valid = self.update_form.is_valid()
        return( update_valid and report_valid )
    
    def save(self, is_confirmed = False):
        report = super(ReportForm,self).save( commit = False )
        update = self.update_form.save(commit=False)
        
        #these are in the form for 'update'
        report.desc = update.desc
        report.author = update.author
        
        #this info is custom
        report.point = self.pnt
        report.ward = self.ward
        report.is_confirmed = is_confirmed
        update.report = report
        update.first_update = True
        update.is_confirmed = is_confirmed
        update.created_at = report.created_at
        report.save()
        update.report = report
        update.save()
        return( report )
    
    def all_errors(self):
        "returns errors for both report and update forms"
        errors = {}
        for key,value in self.errors.items():
            errors[key] = value.as_text()[2:] 

        # add errors from the update form to the end.
        for key,value in self.update_form.errors.items():
            errors[key] = value.as_text()[2:] 
            
        return( errors )
    
from social_auth.backends import get_backend


class FMSNewRegistrationForm(RegistrationForm):

    username = forms.CharField(widget=forms.widgets.HiddenInput,required=False)
    phone = forms.CharField(max_length=100,
                           widget=forms.TextInput(attrs={ 'class': 'required' }),
                           label=_('Phone'))
    first_name = forms.CharField(max_length=100,
                           widget=forms.TextInput(attrs={ 'class': 'required' }),
                           label=_('First Name'))
    last_name = forms.CharField(max_length=100,
                           widget=forms.TextInput(attrs={ 'class': 'required' }),
                           label=_('Last Name'))

    def __init__(self, *args, **kw):
        super(FMSNewRegistrationForm, self).__init__(*args, **kw)
        self.fields.keyOrder = [
            'first_name',
            'last_name',
            'email',
            'phone',
            'password1',
            'password2',
            'username' ]

    
    def save(self, profile_callback=None):
        username = self.cleaned_data.get('username',None)
        
        if username:
            # flag that there's an existing user created by 
            # social_auth.
            new_user = User.objects.get(username=username)
        else:
            # otherwise, normal registration.
            # look for a user with the same email.
            if User.objects.filter(email=self.cleaned_data.get('email')):
                new_user = User.objects.get(email=self.cleaned_data.get('email'))
            else:
                new_user = RegistrationProfile.objects.create_inactive_user(username=self.cleaned_data['email'],
                                                                    password=self.cleaned_data['password1'],
                                                                    email=self.cleaned_data['email'],
                                                                    send_email=False )        
        new_user.first_name = self.cleaned_data.get('first_name','')
        new_user.last_name = self.cleaned_data.get('last_name','')
        new_user.email = self.cleaned_data.get('email')
        new_user.set_password(self.cleaned_data.get('password1'))
        new_user.username = self.cleaned_data.get('email')
                    
        new_user.save()

        user_profile, g_or_c = UserProfile.objects.get_or_create(user=new_user)
        user_profile.phone = self.cleaned_data.get('phone','')
        user_profile.save()

        if not new_user.is_active:
            self.send_email(new_user)
            
        return( new_user )
    
    def clean_username(self):
        return self.cleaned_data['username']
    
    def clean_email(self):
        if User.objects.filter(email=self.cleaned_data['email'],is_active=True).count() != 0:
            raise forms.ValidationError(_(u'That email is already in use.'))    
        return self.cleaned_data['email']
    
    def send_email(self,new_user):
        registration_profile = RegistrationProfile.objects.get(user=new_user)
        current_site = Site.objects.get_current()
            
        subject = render_to_string('registration/activation_email_subject.txt',
                                       { 'site': current_site })
        # Email subject *must not* contain newlines
        subject = ''.join(subject.splitlines())
            
        message = render_to_string('registration/activation_email.txt',
                                       { 'activation_key': registration_profile.activation_key,
                                         'expiration_days': settings.ACCOUNT_ACTIVATION_DAYS,
                                         'site': current_site })
            
        new_user.email_user(subject, message, settings.DEFAULT_FROM_EMAIL)


# just override the AuthenticationForm username so that it's label
# says 'email'

class FMSAuthenticationForm(AuthenticationForm):
    """
    Base class for authenticating users. Extend this to get a form that accepts
    username/password logins.
    """
    username = forms.CharField(label=_("Email"), max_length=30)


  