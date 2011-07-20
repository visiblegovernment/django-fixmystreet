
from django.db import models, connection
from django.contrib.gis.db import models
from django.contrib.gis.maps.google import GoogleMap, GMarker, GEvent, GPolygon, GIcon
from django.template.loader import render_to_string
from fixmystreet import settings
from django import forms
from django.core.mail import send_mail, EmailMessage
import md5
import urllib
import time
import datetime
from mainapp import emailrules
from datetime import datetime as dt
from django.utils.safestring import mark_safe
from django.utils.translation import ugettext_lazy, ugettext as _
from contrib.transmeta import TransMeta
from contrib.stdimage import StdImageField
from django.utils.encoding import iri_to_uri
from django.template.defaultfilters import slugify
from django.contrib.gis.geos import fromstr
from django.http import Http404
from django.contrib.auth.models import User,Group,Permission
from registration.models import RegistrationProfile 
      
# from here: http://www.djangosnippets.org/snippets/630/        
class CCEmailMessage(EmailMessage):
    def __init__(self, subject='', body='', from_email=None, to=None, cc=None,
                 bcc=None, connection=None, attachments=None, headers=None):
        super(CCEmailMessage, self).__init__(subject, body, from_email, to,
                                           bcc, connection, attachments, headers)
        if cc:
            self.cc = list(cc)
        else:
            self.cc = []

    def recipients(self):
        """
        Returns a list of all recipients of the email
        """
        return super(CCEmailMessage, self).recipients() + self.cc 

    def message(self):
        msg = super(CCEmailMessage, self).message()
        if self.cc:
            msg['Cc'] = ', '.join(self.cc)
        return msg

class ReportCategoryClass(models.Model):
    __metaclass__ = TransMeta

    name = models.CharField(max_length=100)

    def __unicode__(self):      
        return self.name

    class Meta:
        db_table = u'report_category_classes'
        translate = ('name', )
    
class ReportCategory(models.Model):
    __metaclass__ = TransMeta

    name = models.CharField(max_length=100)
    hint = models.TextField(blank=True, null=True)
    category_class = models.ForeignKey(ReportCategoryClass)
  
    def __unicode__(self):      
        return self.category_class.name + ":" + self.name
 
    class Meta:
        db_table = u'report_categories'
        translate = ('name', 'hint', )

class ReportCategorySet(models.Model):
    ''' A category group for a particular city '''
    name = models.CharField(max_length=100)
    categories = models.ManyToManyField(ReportCategory)

    def __unicode__(self):      
        return self.name
                 
class Province(models.Model):
    name = models.CharField(max_length=100)
    abbrev = models.CharField(max_length=3)

    class Meta:
        db_table = u'province'
    
class City(models.Model):
    province = models.ForeignKey(Province)
    name = models.CharField(max_length=100)
    # the city's 311 email, if it has one.
    email = models.EmailField(blank=True, null=True)    
    category_set = models.ForeignKey(ReportCategorySet, null=True, blank=True)
    objects = models.GeoManager()

    def __unicode__(self):      
        return self.name
    
    def get_categories(self):
        if self.category_set:
            categories = self.category_set.categories
        else:
            # the 'Default' group is defined in fixtures/initial_data
            default = ReportCategorySet.objects.get(name='Default')
            categories = default.categories
        categories = categories.order_by('category_class')
        return( categories )
    
    def get_absolute_url(self):
        return "/cities/%d" %( self.id ) 

    def get_rule_descriptions(self):
        rules = EmailRule.objects.filter(city=self)
        describer = emailrules.EmailRulesDesciber(rules,self)
        return( describer.values() )

    class Meta:
        db_table = u'cities'

class Councillor(models.Model):

    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    
    # this email addr. is the destination for reports
    # if the 'Councillor' email rule is enabled
    email = models.EmailField(blank=True, null=True)
    city = models.ForeignKey(City,null=True)

    def __unicode__(self):      
        return self.first_name + " " + self.last_name

    class Meta:
        db_table = u'councillors'


        
class Ward(models.Model):
    
    name = models.CharField(max_length=100)
    number = models.IntegerField()
    councillor = models.ForeignKey(Councillor,null=True,blank=True)
    city = models.ForeignKey(City)
    geom = models.MultiPolygonField( null=True)
    objects = models.GeoManager()
    
    # this email addr. is the destination for reports
    # if the 'Ward' email rule is enabled
    email = models.EmailField(blank=True, null=True)

    def get_absolute_url(self):
        return "/wards/%d" % ( self.id ) 

    def __unicode__(self):      
        return self.name + ", " + self.city.name  

    # return a list of email addresses to send new problems in this ward to.
    def get_emails(self,report):
        to_emails = []
        cc_emails = []
        if self.city.email:
            to_emails.append(self.city.email)
            
        # check for rules for this city.
        rules = EmailRule.objects.filter(city=self.city)
        for rule in rules:
            rule_email = rule.get_email(report)
            if rule_email:
               if not rule.is_cc: 
                   to_emails.append(rule_email)
               else:
                   cc_emails.append(rule_email)
        return( to_emails,cc_emails )

    
    def get_rule_descriptions(self):
        rules = EmailRule.objects.filter(city=self.city)
        describer = emailrules.EmailRulesDesciber(rules,self.city, self)
        return( describer.values() )
            

    class Meta:
        db_table = u'wards'

    
            
# Override where to send a report for a given city.        
#
# If no rule exists, the email destination is the 311 email address 
# for that city.
#
# Cities can have more than one rule.  If a given report matches more than
# one rule, more than one email is sent.  (Desired behaviour for cities that 
# want councillors CC'd)

class EmailRule(models.Model):
    
    TO_COUNCILLOR = 0
    MATCHING_CATEGORY_CLASS = 1
    NOT_MATCHING_CATEGORY_CLASS = 2
    TO_WARD = 3
    
    RuleChoices = [   
    (TO_COUNCILLOR, 'Send Reports to Councillor Email Address'),
    (MATCHING_CATEGORY_CLASS, 'Send Reports Matching Category Group (eg. Parks) To This Email'),
    (NOT_MATCHING_CATEGORY_CLASS, 'Send Reports Not Matching Category Group To This Email'), 
    (TO_WARD, 'Send Reports to Ward Email Address'),]
    
    RuleBehavior = { TO_COUNCILLOR: emailrules.ToCouncillor,
                     MATCHING_CATEGORY_CLASS: emailrules.MatchingCategoryClass,
                     NOT_MATCHING_CATEGORY_CLASS: emailrules.NotMatchingCategoryClass,
                     TO_WARD: emailrules.ToWard }
    
    rule = models.IntegerField(choices=RuleChoices)
    
    # is this a 'to' email or a 'cc' email
    is_cc = models.BooleanField(default=False,
            help_text="Set to true to include address in 'cc' list"

            )

    # the city this rule applies to 
    city = models.ForeignKey(City)    
    
    # filled in if this is a category class rule
    category_class = models.ForeignKey(ReportCategoryClass,null=True, blank=True,
                          verbose_name = 'Category Group',
                          help_text="Only set for 'Category Group' rule types."
                          )
    
    # filled in if this is a category rule
    #category = models.ForeignKey(ReportCategory,null=True, blank=True,
    #                    help_text="Set to send all "
    #                     )
    
    # filled in if an additional email address is required for the rule type
    email = models.EmailField(blank=True, null=True,
                        help_text="Only set for 'Category Group' rule types."
                        )
    
    def label(self):
        rule_behavior = EmailRule.RuleBehavior[ self.rule ]()
        return( rule_behavior.report_group(self) )
    
    def value(self, ward = None):
        rule_behavior = EmailRule.RuleBehavior[ self.rule ]()
        if ward:
            return( rule_behavior.value_for_ward(self,ward) )
        else:
            return( rule_behavior.value_for_city(self))
        
    def get_email(self,report):
        rule_behavior = EmailRule.RuleBehavior[ self.rule ]()
        return( rule_behavior.get_email(report,self))
    
    def __str__(self):
        rule_behavior = EmailRule.RuleBehavior[ self.rule ]()
        if self.is_cc:
            prefix = "CC:"
        else:
            prefix = "TO:"
        return( "%s - %s (%s)" % (self.city.name,rule_behavior.describe(self),prefix) )
        
class ApiKey(models.Model):
    
    WIDGET = 0
    MOBILE = 1
    
    TypeChoices = [
    (WIDGET, 'Embedded Widget'),
    (MOBILE, 'Mobile'), ]
    
    organization = models.CharField(max_length=255)
    key = models.CharField(max_length=100)
    type = models.IntegerField(choices=TypeChoices)
    contact_email = models.EmailField()
    approved = models.BooleanField(default=False)
    
    def save(self):
        if not self.key or self.key == "":
            m = md5.new()
            m.update(self.contact_email)
            m.update(str(time.time()))
            self.confirm_token = m.hexdigest()
        super(ApiKey,self).save()
        
    def __unicode__(self):
        return( str(self.organization) )

class Report(models.Model):
    title = models.CharField(max_length=100, verbose_name = ugettext_lazy("Subject"))
    category = models.ForeignKey(ReportCategory,null=True)
    ward = models.ForeignKey(Ward,null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    # last time report was updated
    updated_at = models.DateTimeField(auto_now_add=True)
    
    # time report was marked as 'fixed'
    fixed_at = models.DateTimeField(null=True)
    is_fixed = models.BooleanField(default=False)
    is_hate = models.BooleanField(default=False)
    
    # last time report was sent to city
    sent_at = models.DateTimeField(null=True)
    
    # email where the report was sent
    email_sent_to = models.EmailField(null=True)
    
    # last time a reminder was sent to the person that filed the report.
    reminded_at = models.DateTimeField(auto_now_add=True)
    
    point = models.PointField(null=True)
    photo = StdImageField(upload_to="photos", blank=True, verbose_name =  ugettext_lazy("* Photo"), size=(400, 400), thumbnail_size=(133,100))
    desc = models.TextField(blank=True, null=True, verbose_name = ugettext_lazy("Details"))
    author = models.CharField(max_length=255,verbose_name = ugettext_lazy("Name"))
    address = models.CharField(max_length=255,verbose_name = ugettext_lazy("Location"))

    # true if first update has been confirmed - redundant with
    # one in ReportUpdate, but makes aggregate SQL queries easier.
    
    is_confirmed = models.BooleanField(default=False)

    # what API did the report come in on?
    api_key = models.ForeignKey(ApiKey,null=True,blank=True)
    
    # this this report come in from a particular mobile app?
    device_id = models.CharField(max_length=100,null=True,blank=True)
    
    # who filed this report?
    objects = models.GeoManager()
    
    def is_subscribed(self, email):
        if len( self.reportsubscriber_set.filter(email=email)) != 0:
            return( True )
        return( self.first_update().email == email )
    
    def sent_at_diff(self):
        if not self.sent_at:
            return( None )
        else:
            return(  self.sent_at - self.created_at )

    def first_update(self):
        return( ReportUpdate.objects.get(report=self,first_update=True))

    def get_absolute_url(self):
        return  "/reports/" + str(self.id)
            
    class Meta:
        db_table = u'reports'
        

class ReportUpdate(models.Model):   
    report = models.ForeignKey(Report)
    desc = models.TextField(blank=True, null=True, verbose_name = ugettext_lazy("Details"))
    created_at = models.DateTimeField(auto_now_add=True)
    is_confirmed = models.BooleanField(default=False)
    is_fixed = models.BooleanField(default=False)
    confirm_token = models.CharField(max_length=255, null=True)
    email = models.EmailField(max_length=255, verbose_name = ugettext_lazy("Email"))
    author = models.CharField(max_length=255,verbose_name = ugettext_lazy("Name"))
    phone = models.CharField(max_length=255, verbose_name = ugettext_lazy("Phone"), blank=True,null=True )
    first_update = models.BooleanField(default=False)
    
    def notify(self):
        """
        Tell whoever cares that there's been an update to this report.
         -  If it's the first update, tell city officials
         -  Anything after that, tell subscribers
        """
        if self.first_update:
            self.notify_on_new()
        else:
            self.notify_on_update()
            
    def notify_on_new(self):
        # send to the city immediately.           
        subject = render_to_string("emails/send_report_to_city/subject.txt", {'update': self })
        message = render_to_string("emails/send_report_to_city/message.txt", { 'update': self, 'SITE_URL':settings.SITE_URL })
        
        to_email_addrs,cc_email_addrs = self.report.ward.get_emails(self.report)
        email_msg = CCEmailMessage(subject,message,settings.EMAIL_FROM_USER, 
                        to_email_addrs, cc_email_addrs,headers = {'Reply-To': self.email })
        if self.report.photo:
            email_msg.attach_file( self.report.photo.file.name )
        
        email_msg.send()

        # update report to show time sent to city.
        self.report.sent_at=dt.now()
        email_addr_str = ""
        for email in to_email_addrs:
            if email_addr_str != "":
                email_addr_str += ", "
            email_addr_str += email
            
        self.report.email_sent_to = email_addr_str
        self.report.save()
        
    
    def notify_on_update(self):
        subject = render_to_string("emails/report_update/subject.txt", 
                    { 'update': self })
        
        # tell our subscribers there was an update.
        for subscriber in self.report.reportsubscriber_set.all():
            unsubscribe_url = settings.SITE_URL + "/reports/subscribers/unsubscribe/" + subscriber.confirm_token
            message = render_to_string("emails/report_update/message.txt", 
               { 'update': self, 'unsubscribe_url': unsubscribe_url })
            send_mail(subject, message, 
               settings.EMAIL_FROM_USER,[subscriber.email], fail_silently=False)

        # tell the original problem reporter there was an update
        message = render_to_string("emails/report_update/message.txt", 
                    { 'update': self })
        send_mail(subject, message, 
              settings.EMAIL_FROM_USER,
              [self.report.first_update().email],  fail_silently=False)

            
    def save(self):
        # does this update require confirmation?
        if not self.is_confirmed:
            self.get_confirmation()
            super(ReportUpdate,self).save()
        else:
            # update parent report
            if not self.created_at: 
                self.created_at = datetime.datetime.now()
            if self.is_fixed:
                self.report.is_fixed = True
                self.report.fixed_at = self.created_at   
            # we track a last updated time in the report to make statistics 
            # (such as on the front page) easier.  
            if not self.first_update:
                self.report.updated_at = self.created_at
            else:
                self.report.updated_at = self.report.created_at
                self.report.is_confirmed = True
            super(ReportUpdate,self).save()
            self.report.save()

    def confirm(self):    
        self.is_confirmed = True
        self.save()
        self.notify()

            
    def get_confirmation(self):
        """ Send a confirmation email to the user. """        
        if not self.confirm_token or self.confirm_token == "":
            m = md5.new()
            m.update(self.email)
            m.update(str(time.time()))
            self.confirm_token = m.hexdigest()
            confirm_url = settings.SITE_URL + "/reports/updates/confirm/" + self.confirm_token
            message = render_to_string("emails/confirm/message.txt", 
                    { 'confirm_url': confirm_url, 'update': self })
            subject = render_to_string("emails/confirm/subject.txt", 
                    {  'update': self })
            send_mail(subject, message, 
                   settings.EMAIL_FROM_USER,[self.email], fail_silently=False)
            
        super(ReportUpdate, self).save()
    
    def title(self):
        if self.first_update :
            return self.report.title
        if self.is_fixed:
            return "Reported Fixed"
        return("Update")
        
    class Meta:
        db_table = u'report_updates'

class ReportSubscriber(models.Model):
    """ 
        Report Subscribers are notified when there's an update to an existing report.
    """
    
    report = models.ForeignKey(Report)    
    confirm_token = models.CharField(max_length=255, null=True)
    is_confirmed = models.BooleanField(default=False)    
    email = models.EmailField()
    
    class Meta:
        db_table = u'report_subscribers'

    
    def save(self):
        if not self.confirm_token or self.confirm_token == "":
            m = md5.new()
            m.update(self.email)
            m.update(str(time.time()))
            self.confirm_token = m.hexdigest()
        if not self.is_confirmed:
            confirm_url = settings.SITE_URL + "/reports/subscribers/confirm/" + self.confirm_token
            message = render_to_string("emails/subscribe/message.txt", 
                    { 'confirm_url': confirm_url, 'subscriber': self })
            send_mail('Subscribe to FixMyStreet.ca Report Updates', message, 
                   settings.EMAIL_FROM_USER,[self.email], fail_silently=False)
        super(ReportSubscriber, self).save()

 
class ReportMarker(GMarker):
    """
        A marker for an existing report.  Override the GMarker class to 
        add a numbered, coloured marker.
        
        If the report is fixed, show a green marker, otherwise red.
    """
    def __init__(self, report, icon_number ):
        if report.is_fixed:
            color = 'green'
        else:
            color = 'red'
        icon_number = icon_number
        img = "/media/images/marker/%s/marker%s.png" %( color, icon_number )
        name = 'letteredIcon%s' %( icon_number )      
        icon = GIcon(name,image=img,iconsize=(20,34))
        GMarker.__init__(self,geom=(report.point.x,report.point.y), title=report.title.replace('"',"'"), icon=icon)

    def __unicode__(self):
        "The string representation is the JavaScript API call."
        return mark_safe('GMarker(%s)' % ( self.js_params))

    
class FixMyStreetMap(GoogleMap):  
    """
        Overrides the GoogleMap class that comes with GeoDjango.  Optionally,
        show nearby reports.
    """
    def __init__(self,pnt,draggable=False,nearby_reports = [] ):  
#        self.icons = []
        markers = []
        marker = GMarker(geom=(pnt.x,pnt.y), draggable=draggable)
        if draggable:
            event = GEvent('dragend',
                           'function() { reverse_geocode (geodjango.map_canvas_marker1.getPoint()); }')        
            marker.add_event(event)
        markers.append(marker)
        
        for i in range( len( nearby_reports ) ):
            nearby_marker = ReportMarker(nearby_reports[i], str(i+1) )
            markers.append(nearby_marker)

        GoogleMap.__init__(self,center=(pnt.x,pnt.y),zoom=17,key=settings.GMAP_KEY, markers=markers, dom_id='map_canvas')

class WardMap(GoogleMap):
    """ 
        Show a single ward as a gmap overlay.  Optionally, show reports in the
        ward.
    """
    def __init__(self,ward, reports = []):
        polygons = []
        for poly in ward.geom:
                polygons.append( GPolygon( poly ) )
        markers = []
        for i in range( len( reports ) ):
            marker = ReportMarker(reports[i], str(i+1) )
            markers.append(marker)

        GoogleMap.__init__(self,zoom=13,markers=markers,key=settings.GMAP_KEY, polygons=polygons, dom_id='map_canvas')

           

class CityMap(GoogleMap):
    """
        Show all wards in a city as overlays.  Used when debugging maps for new cities.
    """
    
    def __init__(self,city):
        polygons = []
        ward = Ward.objects.filter(city=city)[:1][0]
        for ward in Ward.objects.filter(city=city):
            for poly in ward.geom:
                polygons.append( GPolygon( poly ) )
        GoogleMap.__init__(self,center=ward.geom.centroid,zoom=13,key=settings.GMAP_KEY, polygons=polygons,dom_id='map_canvas')
    

    
class CountIf(models.sql.aggregates.Aggregate):
    # take advantage of django 1.3 aggregate functionality
    # from discussion here: http://groups.google.com/group/django-users/browse_thread/thread/bd5a6b329b009cfa
    sql_function = 'COUNT'
    sql_template= '%(function)s(CASE %(condition)s WHEN true THEN 1 ELSE NULL END)'
    
    def __init__(self, lookup, **extra):
        self.lookup = lookup
        self.extra = extra

    def _default_alias(self):
        return '%s__%s' % (self.lookup, self.__class__.__name__.lower())
    default_alias = property(_default_alias)

    def add_to_query(self, query, alias, col, source, is_summary):
        super(CountIf, self).__init__(col, source, is_summary, **self.extra)
        query.aggregate_select[alias] = self
            
        
class ReportCounter(CountIf):
    """ initialize an aggregate with one of 5 typical report queries """

    CONDITIONS = {
        'recent_new' : "age(clock_timestamp(), reports.created_at) < interval '%s' and reports.is_confirmed = True",
        'recent_fixed' : "age(clock_timestamp(), reports.fixed_at) < interval '%s' AND reports.is_fixed = True",
        'recent_updated': "age(clock_timestamp(), reports.updated_at) < interval '%s' AND reports.is_fixed = False and reports.updated_at != reports.created_at",
        'old_fixed' : "age(clock_timestamp(), reports.fixed_at) > interval '%s' AND reports.is_fixed = True",
        'old_unfixed' : "age(clock_timestamp(), reports.created_at) > interval '%s' AND reports.is_confirmed = True AND reports.is_fixed = False"  
                }
    
    def __init__(self, col, key, interval ):
        super(ReportCounter,self).__init__( col, condition=self.CONDITIONS[ key ] % ( interval ) )
         
        
class ReportCounters(dict):
    """ create a dict of typical report count aggregators. """    
    def __init__(self,report_col, interval = '1 Month'):
        super(ReportCounters,self).__init__()
        for key in ReportCounter.CONDITIONS.keys():
            self[key] = ReportCounter(report_col,key,interval)
    
class OverallReportCount(dict):
    """ this query needs some intervention """
    def __init__(self, interval ):
        super(OverallReportCount,self).__init__()
        q = Report.objects.annotate(**ReportCounters('id', interval ) ).values('recent_new','recent_fixed','recent_updated')
        q.query.group_by = []
        self.update( q[0] )

class FaqEntry(models.Model):
    __metaclass__ = TransMeta

    q = models.CharField(max_length=100)
    a = models.TextField(blank=True, null=True)
    slug = models.SlugField(null=True, blank=True)
    order = models.IntegerField(null=True, blank=True)
    
    def save(self):
        super(FaqEntry, self).save()
        if self.order == None: 
            self.order = self.id + 1
            super(FaqEntry, self).save()
    
    class Meta:
        db_table = u'faq_entries'
        translate = ('q', 'a', )
       

class FaqMgr(object):
        
    def incr_order(self, faq_entry ):
        if faq_entry.order == 1:
            return
        other = FaqEntry.objects.get(order=faq_entry.order-1)
        swap_order(other[0],faq_entry)
    
    def decr_order(self, faq_entry): 
        other = FaqEntry.objects.filter(order=faq_entry.order+1)
        if len(other) == 0:
            return
        swap_order(other[0],faq_entry)
        
    def swap_order(self, entry1, entry2 ):
        entry1.order = entry2.order
        entry2.order = entry1.order
        entry1.save()
        entry2.save()
 

class PollingStation(models.Model):
    """
    This is a temporary object.  Sometimes, we get maps in the form of
    polling stations, which have to be combined into wards.
    """
    number = models.IntegerField()
    station_name = models.CharField(max_length=100, null=True)
    ward_number = models.IntegerField()
    city = models.ForeignKey(City)
    geom = models.MultiPolygonField( null=True)
    objects = models.GeoManager()

    class Meta:
        db_table = u'polling_stations'
 
 
class UserProfile(models.Model):
    user = models.ForeignKey(User, unique=True)
    
    # if user is a 'city admin' (is_staff=True),
    # this field lists all cities the user 
    # can edit through the admin 
    # panel.  
    
    cities = models.ManyToManyField(City, null=True,blank=True)
    
    # fields for 'non-admin' users:
    phone = models.CharField(max_length=255, verbose_name = ugettext_lazy("Phone"), null=True, blank=True )
    
    
    def __unicode__(self):
        return self.user.username

    
class FMSUserManager(models.Manager):   
    '''
    FMSUser and FMSUserManager integrate
    with django-social-auth and django-registration
    '''     
    def create_user(self, username, email, password=None):
        user = RegistrationProfile.objects.create_inactive_user(username,password,email,send_email=False)

        if user:
            UserProfile.objects.get_or_create(user=user)
            return FMSUser.objects.get(username=user.username)
        else:
             return( None )
     
class FMSUser(User):
    '''
    FMSUser and FMSUserManager integrate
    with django-social-auth and django-registration
    '''     
    class Meta:
        proxy = True

    objects = FMSUserManager()
    

class CityAdminManager(models.Manager):    
    PERMISSION_NAMES = [ 'Can change ward', 
                     'Can add email rule',
                     'Can change email rule',
                     'Can delete email rule',
                     'Can add councillor',
                     'Can change councillor',
                     'Can delete councillor' ]

    GROUP_NAME = 'CityAdmins'
    
    def get_group(self):
        if Group.objects.filter(name=self.GROUP_NAME).exists():
            return Group.objects.get(name=self.GROUP_NAME)
        else:
            group = Group.objects.create(name=self.GROUP_NAME)        
            for name in self.PERMISSION_NAMES:
                permission = Permission.objects.get(name=name)
                group.permissions.add(permission)
            group.save()
            return group
    
    
    def create_user(self, username, email, city, password=None):
        group = self.get_group()
        user = User.objects.create_user(username, email, password )
        user.is_staff = True
        user.groups.add(group)
        user.save()
        profile = UserProfile(user=user)
        profile.save()
        profile.cities.add(city)
        profile.save()
        return user
        
class CityAdmin(User):
    '''
        An admin user who can edit ward data for a city.
    '''     
    class Meta:
        proxy = True

    objects = CityAdminManager()
    
    

    
        
class DictToPoint():
    ''' Helper class '''
    def __init__(self, dict, exceptclass = Http404 ):
        if exceptclass and not dict.has_key('lat') or not dict.has_key('lon'):
            raise exceptclass
        
        self.lat = dict.get('lat',None)
        self.lon = dict.get('lon',None)
        self._pnt = None
        
    def __unicode__(self):
        return ("POINT(" + self.lon + " " + self.lat + ")" )
    
    def pnt(self, srid = None ):
        if self._pnt:
            return self._pnt
        if not self.lat or not self.lon:
            return None
        pntstr = self.__unicode__()
        self._pnt = fromstr( pntstr, srid=4326) 
        return self._pnt
    
    def ward(self):
        pnt = self.pnt()
        if not pnt:
            return None
        wards = Ward.objects.filter(geom__contains=pnt)[:1]
        if wards:
            return(wards[0])
        else:
            return(None)

    
    
