from django.test import TestCase
from django.test.client import Client
import os
from mainapp.models import Report
import xml.dom.minidom
from django.core import mail

PATH = os.path.dirname(__file__)         

ANON_CREATE_PARAMS =  { 'lat': '45.4198266',
                        'lon': '-75.6943189',
                        'service_code': 5,
                        'location': 'Some Street',
                        'first_name': 'John',
                        'last_name':'Farmer',
                        'title': 'Submitted by our mobile app',
                        'description': 'The description of a mobile submitted report',
                        'email': 'testuser@hotmail.com',
                        'phone': '514-513-0475' 
                    } 

LOGGEDIN_CREATE_PARAMS =  { 'title': 'A report from our API from a logged in user', 
                            'lat': '45.4301269580000024',
                            'lon': '-75.6824648380000014',
                            'location': 'Some Street',
                            'service_code': 5,
                            'description': 'The description' 
                        } 

EXPECTED_ERRORS = {
           'lat': ['lat:This field is required.'],
           'lon': ['lon:This field is required.'],
           'service_code': ['service_code:This field is required.'],
           'first_name':  None,
           'last_name': ['last_name:This field is required.'],
           'title': None,
           'description': ['description:This field is required.'],
           'email': ['email:This field is required.'],
           'phone': None  }

class Open311v2(TestCase):
    
    fixtures = ['test_rest.json']
    c = Client()

    def test_get_report(self):
        url = self._url('requests/1.xml?jurisdiction_id=oglo.fixmystreet.ca')
        response = self.c.get(url)
        self._expectXML(response, 'get_report_1.xml' )
        
    def test_get_services(self):
        url = self._url('services.xml?jurisdiction_id=oglo.fixmystreet.ca')
        response = self.c.get(url)
        self._expectXML(response, 'get_services.xml' )

    def test_get_by_lat_lon(self):
        params = { 'lon': '-75.6824648380000014',
                   'lat': '45.4301269580000024' }
        url = self._reportsUrl(params)
        response = self.c.get(url)
        self._expectXML(response, 'get_reports.xml' )

    def test_get_by_date_range(self):
        params = { 'start_date' : '2009-02-02',
                   'end_date' : '2009-02-03' }
        url = self._reportsUrl(params)
        response = self.c.get(url)
        self._expectXML(response, 'get_report_2.xml' )

    def test_get_by_end_date(self):
        params =  { 'end_date': '2009-02-02' }
        url = self._reportsUrl(params)
        response = self.c.get(url)
        self._expectXML(response, 'get_report_1.xml' )

    def test_get_by_start_date(self):
        params =  { 'start_date': '2009-02-04' }
        url = self._reportsUrl(params)
        response = self.c.get(url)
        self._expectXML(response, 'get_report_4.xml' )
        
    def _create_request(self, params,expected_errors=None, anon=True):
        
        response = self.c.post(self._reportsUrl(), params, **{ "wsgi.url_scheme" : "https" } )
        doc = xml.dom.minidom.parseString(response.content)            

        if not expected_errors:
            self.assertEquals( response.status_code, 200 )
            self.assertEqual(Report.objects.filter(desc=ANON_CREATE_PARAMS['description']).count(), 1 )
            self.assertEquals(len(mail.outbox), 1, 'an email was sent')
            if anon:
                self.assertEquals(mail.outbox[0].to, ['testuser@hotmail.com'])
            self.assertEqual(len(doc.getElementsByTagName('service_request_id')), 1, "there is a request id in the resposne")
            request_id = doc.getElementsByTagName('service_request_id')[0].childNodes[0].data
            self.assertEquals( request_id, '6', "we've created a new request" ) 
        else:
            self.assertEquals( response.status_code, 400 )
            errors = doc.getElementsByTagName('error')
            self.assertEquals(len(errors),len(expected_errors))
            for error in errors:
                error_text = error.childNodes[0].data
                self.assertEquals(error_text in expected_errors,True)
                
    def test_anon_report_post(self):
        self._create_request(ANON_CREATE_PARAMS)
    
    def _test_post_missing(self, field ):
        params = ANON_CREATE_PARAMS.copy()
        del( params[field])
        self._create_request(params,expected_errors=EXPECTED_ERRORS[field])

    def test_post_missing_title(self):
        self._test_post_missing('title')
        
    def test_post_missing_email(self):
        self._test_post_missing('email')

    def test_post_missing_phone(self):
        self._test_post_missing('phone')
    
    def test_post_missing_lname(self):    
        self._test_post_missing('last_name')

    def test_post_missing_fname(self):    
        self._test_post_missing('first_name')

    def test_post_missing_scode(self):    
        self._test_post_missing('service_code')

    def test_post_missing_desc(self):    
        self._test_post_missing('description')

    def test_post_missing_lat(self):    
        self._test_post_missing('lat')

    def test_post_multi_missing(self):    
        params = ANON_CREATE_PARAMS.copy()
        del( params['lat'])
        del( params['email'])
        errors = EXPECTED_ERRORS['lat']
        errors.extend(EXPECTED_ERRORS['email']) 
        self._create_request(params,errors)
        
    def test_bad_latlon(self):
        params = ANON_CREATE_PARAMS.copy()
        params['lat'] = '22.3232323'
        expect = ['__all__:lat/lon not supported']
        self._create_request(params,expected_errors=expect)
        

    def _url(self, url):
        return('/open311/v2/' + url )
    
    def _reportsUrl(self, params = None ):
        url = self._url('requests.xml')
        if params:
            url += '?'
            for key, value in params.items():
                url += key + "=" + value + ";"
        return url
    
    def _expectXML(self,response,filename):
        self.assertEquals(response.status_code,200)
        file = PATH + '/expected/' +filename
        expect_doc = xml.dom.minidom.parse(file)
        expect_s = expect_doc.toprettyxml()
        got_doc = xml.dom.minidom.parseString(response.content)
        got_s = got_doc.toprettyxml()
        self.maxDiff = None
        self.assertMultiLineEqual( got_s, expect_s )
        
         
ANON_UPDATE_PARAMS = { 'author': 'John Farmer',
                      'email': 'testuser@hotmail.com',
                      'desc': 'This problem has been fixed',
                      'phone': '514-513-0475',
                      'is_fixed': True }

LOGGEDIN_UPDATE_PARAMS = { 'desc': 'This problem has been fixed',
                           'is_fixed': True }

