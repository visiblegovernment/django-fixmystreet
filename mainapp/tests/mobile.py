from django.test import TestCase
from django.test.client import Client
from mainapp.models import Report,ReportUpdate
from mainapp.views.rest import MobileReportAPI
import simplejson
import md5
import settings
import binascii
import re
from django.core import mail
           
LOCAL_PARAMS =  { 'title': 'A report from our API', 
                     'lat': '45.4301269580000024',
                     'lon': '-75.6824648380000014',
                     'category_id': 5,
                     'desc': 'The description',
                     'author': 'John Farmer',
                     'email': 'testuser@hotmail.com',
                     'phone': '514-513-0475' } 

MOBILE_PARAMS =  { 'title': 'A report from our API', 
                      'lat': '45.4301269580000024',
                      'lon': '-75.6824648380000014',
                      'category': 5,
                      'first_name': 'John',
                      'last_name':'Farmer',
                      'description': 'The description',
                      'customer_email': 'testuser@hotmail.com',
                      'customer_phone': '514-513-0475' } 
    
UPDATE_PARAMS = { 'author': 'John Farmer',
                      'email': 'testuser@hotmail.com',
                      'desc': 'This problem has been fixed',
                      'phone': '514-513-0475',
                      'is_fixed': True }


class MobileTestCases(TestCase):
    """ 
        our fixture has 4 confirmed reports and one unconfirmed.
        two of the confirmed reports share the same latitude and longitude.
    """
    fixtures = ['test_rest.json']
    c = Client()
    
    def get_json(self, query):
        response = self.c.get(query)
        self.assertEquals(response.status_code,200)
        return( simplejson.loads(response.content) )
        
    def test_get_by_query(self):
        result = self.get_json('/mobile/reports.json?q=K2P1N8')
        self.assertEquals( len(result), 4 )
        
    def test_get_bad_format(self):
        response = self.c.get('/mobile/reports.unknown?q=K2P1N8')
        self.assertEquals(response.status_code,415)

    def test_get_by_lat_lon(self):
        lon = '-75.6824648380000014'
        lat = '45.4301269580000024'
        result = self.get_json('/mobile/reports.json?lat=%s;lon=%s' % (lat,lon))
        self.assertEquals( len(result), 4 )

    def test_get_by_lat_lon_with_r(self):
        lon = '-75.6824648380000014'
        lat = '45.4301269580000024'
        result = self.get_json('/mobile/reports.json?lat=%s;lon=%s;r=.002' % (lat,lon))
        self.assertEquals( len(result), 2 )

    def test_create_param_tranform(self):  
       output = MobileReportAPI._transform_params( MOBILE_PARAMS.copy() )
       self.assertEquals(output, LOCAL_PARAMS ) 

    def test_create(self):
        params = MOBILE_PARAMS.copy()
        params['device_id'] = 'iphone'
        params['timestamp'] = 'asdfasdf'
        seed = '%s:%s:%s' % ( params['customer_email'],params['timestamp'],settings.MOBILE_SECURE_KEY )
        m = md5.new( seed )
        params['api_key'] = binascii.b2a_base64(m.digest())

        response = self.c.post('/mobile/reports.json', params )
        self.assertEquals( response.status_code, 200 )
        self.assertEqual(Report.objects.filter(title=params['title']).count(), 1 )
        # mail should go directly to the city.
        self.assertEquals(len(mail.outbox), 1)
        self.assertEquals(mail.outbox[0].to, [u'example_city_email@yahoo.ca'])
        
    def test_create_no_nonce(self):
        params = MOBILE_PARAMS.copy()
        response = self.c.post('/mobile/reports.json', params )
        self.assertEquals( response.status_code, 412 )
    
    def test_create_basecase(self):
        """
            Run through our regular report/submit/confirm/update-is-fixed/confirm
            lifecycle to make sure there's no issues, and the right
            emails are being sent.
        """
        response = self.c.post('/reports/', LOCAL_PARAMS, follow=True )
        self.assertEquals( response.status_code, 200 )
        self.assertEquals(response.template[0].name, 'reports/show.html')
        self.assertEqual(Report.objects.filter(title=LOCAL_PARAMS['title']).count(), 1 )

        # a confirmation email should be sent to the user
        self.assertEquals(len(mail.outbox), 1)
        self.assertEquals(mail.outbox[0].to, [u'testuser@hotmail.com'])

        #test confirmation link
        confirm_url = self._get_confirm_url(mail.outbox[0])
        response = self.c.get(confirm_url, follow=True)
        self.assertEquals( response.status_code, 200 )

        #now there should be two emails in our outbox
        self.assertEquals(len(mail.outbox), 2)
        self.assertEquals(mail.outbox[1].to, [u'example_city_email@yahoo.ca'])

        #now submit a 'fixed' update.
        report = Report.objects.get(title=LOCAL_PARAMS['title'])
        self.assertEquals( ReportUpdate.objects.filter(report=report).count(),1)
        update_url = report.get_absolute_url() + "/updates/"
        response = self.c.post(update_url,UPDATE_PARAMS, follow=True)
        self.assertEquals( response.status_code, 200 )
        self.assertEquals( ReportUpdate.objects.filter(report=report).count(),2)
  
        # we should have sent another confirmation link
        self.assertEquals(len(mail.outbox), 3)
        self.assertEquals(mail.outbox[2].to, [u'testuser@hotmail.com'])

        #confirm the update
        confirm_url = self._get_confirm_url(mail.outbox[2])
        response = self.c.get(confirm_url, follow=True)
        self.assertEquals( response.status_code, 200 )
        
        #I guess we send an email to the user to let them know they've confirmed.
        #seems redundant.
        
        self.assertEquals(len(mail.outbox), 4)
        self.assertEquals(mail.outbox[3].to, [u'testuser@hotmail.com'])
        
    def _get_confirm_url(self, email ):
        m = re.search( 'http://localhost:\d+(\S+)', email.body )
        self.assertNotEquals(m,None)
        self.assertEquals(len(m.groups()),1)
        return( str(m.group(1)))
