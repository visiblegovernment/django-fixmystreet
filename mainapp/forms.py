from django import forms
from django.template.loader import render_to_string
from django.core.mail import send_mail
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
from django.utils.safestring import mark_safe


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

    first_name = forms.CharField()
    last_name = forms.CharField()

    class Meta:
        model = UserProfile
        fields = ( 'first_name','last_name','phone',)
        
    # from example here:
    # http://yuji.wordpress.com/2010/02/16/django-extension-of-modeladmin-admin-views-arbitrary-form-validation-with-adminform/ 

    RELATED_FIELD_MAP = {
            'first_name': 'first_name',
            'last_name': 'last_name',
    }
        
    def __init__(self, *args, **kwargs):
        super(EditProfileForm, self).__init__(*args, **kwargs)
        if self.instance.id:
            for field, target_field in self.RELATED_FIELD_MAP.iteritems():
                self.initial[ field ] = getattr(self.instance.user, target_field )
     
    def save(self, *args, **kwargs):
          for field, target_field in self.RELATED_FIELD_MAP.iteritems():
              setattr(self.instance.user,target_field, self.cleaned_data.get(field))
          self.instance.user.save()
          super(EditProfileForm, self).save(*args, **kwargs)
     
class ReportUpdateForm(forms.ModelForm):
        
    class Meta:
        model = ReportUpdate
        fields = ('desc','author','email','phone','is_fixed')


    def __init__(self,data=None,files=None,initial={},first_update=False,user = None, report=None):
       self.user = None
       self.report = report
       self.first_update= first_update
       if user and user.is_authenticated() and UserProfile.objects.filter(user=user).exists():
           self.user = user

       if self.user:
           if not data:
               initial[ 'author' ] = user.first_name + " " + user.last_name
               initial[ 'phone' ] = user.get_profile().phone
               initial[ 'email' ] = user.email
           else:
               # this can't be overridden.

               data = data.copy()
               data['email'] = user.email
               
       super(ReportUpdateForm,self).__init__(data,files=files, initial=initial)
       
       if self.user and not data:
            self.fields['email'].widget.attrs['readonly'] = 'readonly'
    
       if first_update:
           del(self.fields['is_fixed'])
       else:
            self.fields['is_fixed'] = forms.fields.BooleanField(required=False,
                                         help_text=_('This problem has been fixed.'),
                                         label='')
              
    def save(self,commit=True):
       update = super(ReportUpdateForm,self).save( commit = False )
       if self.report:
           update.report = self.report
           
       update.first_update = self.first_update
       if self.user:
           #update.user = self.user
           update.is_confirmed = True
       if commit:
           update.save()
           if update.is_confirmed:
               update.notify()
       return( update )
           
    def as_table(self):
        "over-ridden to get rid of <br/> in help_text_html. "
        return self._html_output(
            normal_row = u'<tr%(html_class_attr)s><th>%(label)s</th><td>%(errors)s%(field)s%(help_text)s</td></tr>',
            error_row = u'<tr><td colspan="2">%s</td></tr>',
            row_ender = u'</td></tr>',
            help_text_html = u'<span class="helptext">%s</span>',
            errors_on_separate_row = False)
    
 
            
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

    def __init__(self,data=None,files=None,initial=None,user=None):
        if data:
            d2p = DictToPoint(data,exceptclass=None)
        else:
            d2p = DictToPoint(initial,exceptclass=None)
        
        self.pnt = d2p.pnt()
        self.ward = d2p.ward()
        self.update_form = ReportUpdateForm(data=data,initial=initial,user=user,first_update = True)
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
    
    def save(self):
        
        report = super(ReportForm,self).save( commit = False )
        update = self.update_form.save(commit=False)
        
        #these are in the form for 'update'
        report.desc = update.desc
        report.author = update.author
        
        #this info is custom
        report.point = self.pnt
        report.ward = self.ward
        #report.user = update.user            

        report.save()
        update.report = report
        update.save()
        
        if update.is_confirmed:
            update.notify()
        
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
            
        subject = render_to_string('registration/activation_email_subject.txt',
                                   )
        # Email subject *must not* contain newlines
        subject = ''.join(subject.splitlines())
            
        message = render_to_string('registration/activation_email.txt',
                                       { 'user': new_user,
                                         'activation_link': "%s/accounts/activate/%s/" %(settings.SITE_URL,registration_profile.activation_key),
                                         'expiration_days': settings.ACCOUNT_ACTIVATION_DAYS })
            
        new_user.email_user(subject, message, settings.EMAIL_FROM_USER)


# just override the AuthenticationForm username so that it's label
# says 'email'

class FMSAuthenticationForm(AuthenticationForm):
    """
    Base class for authenticating users. Extend this to get a form that accepts
    username/password logins.
    """
    username = forms.CharField(label=_("Email"), max_length=30)


  