
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
from mainapp import emailrules
from datetime import datetime as dt
from django.utils.safestring import mark_safe
from django.utils.translation import ugettext_lazy, ugettext as _
from contrib.transmeta import TransMeta
from contrib.stdimage import StdImageField
from django.utils.encoding import iri_to_uri
from django.contrib.gis.geos import fromstr
from django.http import Http404
from django.contrib.auth.models import User
      
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

    objects = models.GeoManager()

    def __unicode__(self):      
        return self.name
    
    def get_absolute_url(self):
        return "/cities/" + str(self.id)

    def get_rule_descriptions(self):
        rules = EmailRule.objects.filter(city=self)
        describer = emailrules.EmailRulesDesciber(rules,self)
        return( describer.values() )

    class Meta:
        db_table = u'cities'

class Councillor(models.Model):

    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    
    # this email addr. is used to send reports to if there is no 311 email for the city.
    email = models.EmailField(blank=True, null=True)
    city = models.ForeignKey(City,null=True)

    def __unicode__(self):      
        return self.first_name + " " + self.last_name

    class Meta:
        db_table = u'councillors'


        
class Ward(models.Model):
    
    name = models.CharField(max_length=100)
    number = models.IntegerField()
    councillor = models.ForeignKey(Councillor)
    city = models.ForeignKey(City)
    geom = models.MultiPolygonField( null=True)
    objects = models.GeoManager()
    
    def get_absolute_url(self):
        return "/wards/" + str(self.id)

    def __unicode__(self):      
        return self.city.name + " " + self.name

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
    
    RuleChoices = [   
    (TO_COUNCILLOR, 'Send Reports to Councillor Email Address'),
    (MATCHING_CATEGORY_CLASS, 'Send Reports Matching Category Group (eg. Parks) To This Email'),
    (NOT_MATCHING_CATEGORY_CLASS, 'Send Reports Not Matching Category Group To This Email'), ]
    
    RuleBehavior = { TO_COUNCILLOR: emailrules.ToCouncillor,
                     MATCHING_CATEGORY_CLASS: emailrules.MatchingCategoryClass,
                     NOT_MATCHING_CATEGORY_CLASS: emailrules.NotMatchingCategoryClass }
    
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

    # true if first update has been confirmed - redundant with
    # one in ReportUpdate, but makes aggregate SQL queries easier.
    
    is_confirmed = models.BooleanField(default=False)

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

class ReportCount(object):        
    def __init__(self, interval):
        self.interval = interval
    
    def dict(self):
        return({ "recent_new": "count( case when age(clock_timestamp(), reports.created_at) < interval '%s' THEN 1 ELSE null end )" % self.interval,
          "recent_fixed": "count( case when age(clock_timestamp(), reports.fixed_at) < interval '%s' AND reports.is_fixed = True THEN 1 ELSE null end )" % self.interval,
          "recent_updated": "count( case when age(clock_timestamp(), reports.updated_at) < interval '%s' AND reports.is_fixed = False and reports.updated_at != reports.created_at THEN 1 ELSE null end )" % self.interval,
          "old_fixed": "count( case when age(clock_timestamp(), reports.fixed_at) > interval '%s' AND reports.is_fixed = True THEN 1 ELSE null end )" % self.interval,
          "old_unfixed": "count( case when age(clock_timestamp(), reports.fixed_at) > interval '%s' AND reports.is_fixed = False THEN 1 ELSE null end )" % self.interval } )  
 
class ReportUpdate(models.Model):   
    report = models.ForeignKey(Report)
    desc = models.TextField(blank=True, null=True, verbose_name = ugettext_lazy("Details"))
    created_at = models.DateTimeField(auto_now_add=True)
    is_confirmed = models.BooleanField(default=False)
    is_fixed = models.BooleanField(default=False)
    confirm_token = models.CharField(max_length=255, null=True)
    email = models.EmailField(max_length=255, verbose_name = ugettext_lazy("Email"))
    author = models.CharField(max_length=255,verbose_name = ugettext_lazy("Name"))
    phone = models.CharField(max_length=255, verbose_name = ugettext_lazy("Phone") )
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
        message = render_to_string("emails/send_report_to_city/message.txt", { 'update': self })
        
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
        else:
            self.notify()
        super(ReportUpdate,self).save()
            
            
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
                           'function() { window.location.href = "/reports/new?" +"&lat="+geodjango.map_canvas_marker1.getPoint().lat().toString()+"&lon="+geodjango.map_canvas_marker1.getPoint().lng().toString(); }')        
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
    


    
class SqlQuery(object):
    """
        This is a workaround: django doesn't support our optimized 
        direct SQL queries very well.
    """
        
    def __init__(self):
        self.cursor = None
        self.index = 0
        self.results = None    

    def next(self):
        self.index = self.index + 1
    
    def get_results(self):
        if not self.cursor:
            self.cursor = connection.cursor()
            self.cursor.execute(self.sql)
            self.results = self.cursor.fetchall()
        return( self.results )

class ReportCountQuery(SqlQuery):
      
    def name(self):
        return self.get_results()[self.index][5]

    def recent_new(self):
        return self.get_results()[self.index][0]
    
    def recent_fixed(self):
        return self.get_results()[self.index][1]
    
    def recent_updated(self):
        return self.get_results()[self.index][2]
    
    def old_fixed(self):
        return self.get_results()[self.index][3]
    
    def old_unfixed(self):
        return self.get_results()[self.index][4]
            
    def __init__(self, interval = '1 month'):
        SqlQuery.__init__(self)
        self.base_query = """select count( case when age(clock_timestamp(), reports.created_at) < interval '%s' and reports.is_confirmed THEN 1 ELSE null end ) as recent_new,\
 count( case when age(clock_timestamp(), reports.fixed_at) < interval '%s' AND reports.is_fixed = True THEN 1 ELSE null end ) as recent_fixed,\
 count( case when age(clock_timestamp(), reports.updated_at) < interval '%s' AND reports.is_fixed = False and reports.updated_at != reports.created_at THEN 1 ELSE null end ) as recent_updated,\
 count( case when age(clock_timestamp(), reports.fixed_at) > interval '%s' AND reports.is_fixed = True THEN 1 ELSE null end ) as old_fixed,\
 count( case when age(clock_timestamp(), reports.created_at) > interval '%s' AND reports.is_confirmed AND reports.is_fixed = False THEN 1 ELSE null end ) as old_unfixed   
 """ % (interval,interval,interval,interval,interval) 
        self.sql = self.base_query + " from reports where reports.is_confirmed = true" 

class CityTotals(ReportCountQuery):

    def __init__(self, interval, city):
        ReportCountQuery.__init__(self,interval)
        self.sql = self.base_query 
        self.sql += """ from reports left join wards on reports.ward_id = wards.id left join cities on cities.id = wards.city_id 
        """ 
        self.sql += ' where reports.is_confirmed = True and wards.city_id = %d ' % city.id
        
class CityWardsTotals(ReportCountQuery):

    def __init__(self, city):
        ReportCountQuery.__init__(self,"1 month")
        self.sql = self.base_query 
        self.url_prefix = "/wards/"            
        self.sql +=  ", wards.name, wards.id, wards.number from wards "
        self.sql += """left join reports on wards.id = reports.ward_id join cities on wards.city_id = cities.id join province on cities.province_id = province.id
        """
        self.sql += "and cities.id = " + str(city.id)
        self.sql += " group by  wards.name, wards.id, wards.number order by wards.number" 
    
    def number(self):
         return(self.get_results()[self.index][7])
        
    def get_absolute_url(self):
        return( self.url_prefix + str(self.get_results()[self.index][6]))

class AllCityTotals(ReportCountQuery):

    def __init__(self):
        ReportCountQuery.__init__(self,"1 month")
        self.sql = self.base_query         
        self.url_prefix = "/cities/"            
        self.sql +=  ", cities.name, cities.id, province.name from cities "
        self.sql += """left join wards on wards.city_id = cities.id join province on cities.province_id = province.id left join reports on wards.id = reports.ward_id 
        """ 
        self.sql += "group by cities.name, cities.id, province.name order by province.name, cities.name"
           
    def get_absolute_url(self):
        return( self.url_prefix + str(self.get_results()[self.index][6]))
    
    def province(self):
        return(self.get_results()[self.index][7])
        
    def province_changed(self):
        if (self.index ==0 ):
            return( True )
        return( self.get_results()[self.index][7] != self.get_results()[self.index-1][7] )

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
    
    cities = models.ManyToManyField(City, null=True)
    
    def __unicode__(self):
        return self.user.username
    
    
class DictToPoint():
    
    def __init__(self, dict ):
        if not dict.has_key('lat') or not dict.has_key('lon'):
            raise Http404
        self.lat = dict['lat']
        self.lon = dict['lon']
        
    def __unicode__(self):
        return ("POINT(" + self.lon + " " + self.lat + ")" )
    
    def pnt(self, srid = None ):
        pntstr = self.__unicode__()
        return( fromstr( pntstr, srid=4326) )
    
    
