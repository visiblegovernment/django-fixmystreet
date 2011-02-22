from django.test import TestCase
from django.test.client import Client
from django.core import mail
from mainapp.models import Report,ReportUpdate,ReportSubscriber
import settings
import re

CREATE_PARAMS =  { 'title': 'A report from our API', 
                     'lat': '45.4043333270000034',
                     'lon': '-75.6870889663999975',
                     'category': 5,
                     'desc': 'The description',
                     'author': 'John Farmer',
                     'email': 'testcreator@hotmail.com',
                     'phone': '514-513-0475' } 

UPDATE_PARAMS = { 'author': 'John Farmer',
                      'email': 'testupdater@hotmail.com',
                      'desc': 'This problem has been fixed',
                      'phone': '514-513-0475',
                      'is_fixed': True }

class BaseCase(TestCase):
    """
        Some helper functions for our test base cases.
    """
    c = Client()

    
    def _get_confirm_url(self, email ):
        m = re.search( 'http://localhost:\d+(\S+)', email.body )
        self.assertNotEquals(m,None)
        self.assertEquals(len(m.groups()),1)
        return( str(m.group(1)))

    
class CreateReport(BaseCase):
    """
        Run through our regular report/submit/confirm/update-is-fixed/confirm
        lifecycle to make sure there's no issues, and the right
        emails are being sent.
    """

    def test(self):
        response = self.c.post('/reports/', CREATE_PARAMS, follow=True )
        self.assertEquals( response.status_code, 200 )
        self.assertEquals(response.template[0].name, 'reports/show.html')
        self.assertEqual(Report.objects.filter(title=CREATE_PARAMS['title']).count(), 1 )

        # a confirmation email should be sent to the user
        self.assertEquals(len(mail.outbox), 1)
        self.assertEquals(mail.outbox[0].to, [u'testcreator@hotmail.com'])
        
        #test confirmation link
        confirm_url = self._get_confirm_url(mail.outbox[0])
        response = self.c.get(confirm_url, follow=True)
        self.assertEquals( response.status_code, 200 )

        #now there should be two emails in our outbox
        self.assertEquals(len(mail.outbox), 2)
        self.assertEquals(mail.outbox[1].to, [u'example_city_email@yahoo.ca'])

        #now submit a 'fixed' update.
        report = Report.objects.get(title=CREATE_PARAMS['title'])
        self.assertEquals( ReportUpdate.objects.filter(report=report).count(),1)
        update_url = report.get_absolute_url() + "/updates/"
        response = self.c.post(update_url,UPDATE_PARAMS, follow=True)
        self.assertEquals( response.status_code, 200 )
        self.assertEquals( ReportUpdate.objects.filter(report=report).count(),2)
        self.assertEquals( ReportUpdate.objects.filter( report=report, is_confirmed=True).count(),1)
        # we should have sent another confirmation link
        self.assertEquals(len(mail.outbox), 3)
        self.assertEquals(mail.outbox[2].to, [u'testupdater@hotmail.com'])

        #confirm the update
        confirm_url = self._get_confirm_url(mail.outbox[2])
        response = self.c.get(confirm_url, follow=True)
        self.assertEquals( response.status_code, 200 )
        self.assertEquals( ReportUpdate.objects.filter( report=report, is_confirmed=True).count(),2)
        self.assertContains(response, UPDATE_PARAMS['desc'])
        #make sure the creator of the report gets an update.
        self.assertEquals(len(mail.outbox), 4)
        self.assertEquals(mail.outbox[3].to, [u'testcreator@hotmail.com'])


class Subscribe(BaseCase):
    """
       Test subscribing and unsubscribing from a report     
    """

    #    this fixture has one fixed report (id=1), and one unfixed (id=2).
    fixtures = ['test_report_basecases.json']

    def test(self):
        response = self.c.post('/reports/2/subscribers/', 
                               { 'email': 'subscriber@test.com'} , follow=True )
        self.assertEquals( response.status_code, 200 )
        self.assertEquals(response.template[0].name, 'reports/subscribers/create.html')
        
        # an unconfirmed subscriber should be created, and an email sent.
        self.assertEquals( ReportSubscriber.objects.count(),1)
        self.assertEquals( ReportSubscriber.objects.get(email='subscriber@test.com').is_confirmed,False )
        self.assertEquals(len(mail.outbox), 1)
        self.assertEquals(mail.outbox[0].to, [u'subscriber@test.com'])
        
        #confirm the subscriber
        confirm_url = self._get_confirm_url(mail.outbox[0])
        response = self.c.get(confirm_url, follow=True)
        self.assertEquals( response.status_code, 200 )

        #subscriber should now be confirmed
        self.assertEquals( ReportSubscriber.objects.get(email='subscriber@test.com').is_confirmed,True )

        # updating the report should send emails to report author, 
        # as well as all subscribers. 

        # -- send the update
        response = self.c.post('/reports/2/updates/',UPDATE_PARAMS, follow=True)
        self.assertEquals( response.status_code, 200 )
        self.assertEquals(len(mail.outbox), 2)

        # -- confirm the update
        confirm_url = self._get_confirm_url(mail.outbox[1])
        response = self.c.get(confirm_url, follow=True)
        self.assertEquals( response.status_code, 200 )

        # check that the right ppl got emails
        self.assertEquals(len(mail.outbox), 4)
        self.assertEquals(mail.outbox[2].to, [u'subscriber@test.com'])
        self.assertEquals(mail.outbox[3].to, [u'reportcreator@test.com'])
        
        # test that the subscribed user can unsubscribe with the link provided.
        unsubscribe_url = self._get_unsubscribe_url(mail.outbox[2])
        response = self.c.get(unsubscribe_url, follow=True)
        self.assertEquals( response.status_code, 200 )
        self.assertEquals( ReportSubscriber.objects.count(),0)
        
    def _get_unsubscribe_url(self,email):
        m = re.search( 'http://localhost:\d+(/reports/subscribers\S+)', email.body )
        self.assertNotEquals(m,None)
        self.assertEquals(len(m.groups()),1)
        return( str(m.group(1)))
    

"""
   Test that flagging a report sends the admin an email     
"""
class FlagReport(BaseCase):

    """ 
        this fixture has one fixed report (id=1), and one unfixed (id=2).
    """
    fixtures = ['test_report_basecases.json']
    
    def test(self):
        report = Report.objects.get(pk=2)
        flag_url = report.get_absolute_url() + "/flags/"
        response = self.c.post(flag_url,{}, follow=True)
        self.assertEquals( response.status_code, 200 )
        self.assertEquals( response.template[0].name, 'reports/flags/thanks.html')

        self.assertEquals(len(mail.outbox), 1)
        self.assertEquals(mail.outbox[0].to, [settings.ADMIN_EMAIL])
 
 
"""
    Test searching 
"""

class TestSearch(BaseCase): 

    
    fixtures = ['test_report_basecases.json']
    
    base_url = '/search'
 
    # now done in javascript
#    def test_success(self):
#        query = 'bank and slater, Ottawa'
#        response = self.c.get(self._url(query), follow=True)
#        self.assertEquals( response.status_code, 200 )
#        self.assertEquals( response.template[0].name, 'search_result.html')

#    def test_doesnt_resolve(self):
#        query = 'nowhere anywhere'
#        error = "Sorry, we couldn't find the address you entered."
#        response = self._get_error_response(query)
#        self.assertContains( response,error)
        
#    def test_ambigous(self):
#        query = 'slater street'
#        error = "That address returned more than one result."
#        response = self._get_error_response(query)
#        self.assertContains(response, error )
        
        # find the link for Ottawa
#        ottawa_link = None
#        for link,address in response.context['disambiguate'].items():
#            if address.find('Ottawa') != -1:
#                ottawa_link = link
#
#        self.assertNotEquals(ottawa_link,None)
#        
#        # follow it to make sure it works
#        response = self.c.get(ottawa_link, follow=True)
#        self.assertEquals( response.status_code, 200 )
#        self.assertEquals( response.template[0].name, 'search_result.html')
        
 
#    def test_not_in_db(self):
#        query = 'moscow, russia'
#        error = "Sorry, we don't yet have that area in our database."
#        response = self._get_error_response(query)
#        self.assertEquals( response.context['error_msg'].startswith(error),True)
    
    
    def _get_error_response(self,query):
        " check we always end up on the home page "
        response = self.c.get(self._url(query), follow=True)
        self.assertEquals( response.status_code, 200 )
        self.assertEquals( response.template[0].name, 'home.html')
        return response
    
    def _url(self,query_str):
        return( self.base_url + "?q=" + query_str )
          