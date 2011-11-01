from django.test import TestCase
from django.test.client import Client
from django.core import mail
from mainapp.models import UserProfile,Report,ReportUpdate,ReportSubscriber
from django.db import connection
from django.contrib.auth.models import User
from django.core import mail
from django.conf import settings


class TestAccountHome(TestCase):
    fixtures = ['test_accounts.json']

    def test_user1(self):
        """ 
            user 1 has:
            -- created reports 1 and 2
            -- updated reports 2 and 3
            -- subscribed to report 4
        """
         
        c = Client()
        r = c.login(username='user1',password='user1')
        self.assertEqual(r,True)
        r = c.get('/accounts/home/',follow=True)
        self.assertEqual(r.status_code,200)
        self.assertEqual(len(r.context['reports']),4)
        # check report 4
        self.assertEqual(r.context['reports'][0].id,4)
        self.assertEqual(r.context['reports'][0].is_reporter,False)
        self.assertEqual(r.context['reports'][0].is_updater,False)
        # check report 3
        self.assertEqual(r.context['reports'][1].id,3)
        self.assertEqual(r.context['reports'][1].is_reporter,False)
        self.assertEqual(r.context['reports'][1].is_updater,True)

        # check report 2
        self.assertEqual(r.context['reports'][2].id,2)
        self.assertEqual(r.context['reports'][2].is_reporter,True)
        self.assertEqual(r.context['reports'][2].is_updater,True)
        # check report 1
        self.assertEqual(r.context['reports'][3].id,1)
        self.assertEqual(r.context['reports'][3].is_reporter,True)
        self.assertEqual(r.context['reports'][3].is_updater,False)
        
        
                         

    def test_user2(self):
        """ 
            user 2 has:
            -- created report 3
            -- updated report 1
            -- not subscribed to any report
        """
         
        c = Client()
        r = c.login(username='user2',password='user2')
        self.assertEqual(r,True)
        r = c.get('/accounts/home/',follow=True)
        self.assertEqual(r.status_code,200)

        self.assertEqual(len(r.context['reports']),2)

        # check report 3
        self.assertEqual(r.context['reports'][0].id,3)
        self.assertEqual(r.context['reports'][0].is_reporter,True)
        self.assertEqual(r.context['reports'][0].is_updater,False)

        # check report 1
        self.assertEqual(r.context['reports'][1].id,1)
        self.assertEqual(r.context['reports'][1].is_reporter,False)
        self.assertEqual(r.context['reports'][1].is_updater,True)


CREATE_PARAMS =  { 'title': 'A report created when logged in', 
                     'lat': '45.4043333270000034',
                     'lon': '-75.6870889663999975',
                     'category': 5,
                     'desc': 'The description',
                     'address': 'Some street',
                } 


UPDATE_PARAMS = { 'author': 'Clark Kent',
                  'email': 'user1@test.com',
                  'desc': 'Report 4 has been fixed',
                  'phone': '555-111-1111',
                  'is_fixed': True }

class TestLoggedInUser(TestCase):
    fixtures = ['test_accounts.json']
        
    def test_report_form(self):
        # check that default values are already filled in.
        c = Client()
        r = c.login(username='user1',password='user1')
        self.assertEquals(r, True)
        url = '/reports/?lat=%s;lon=%s' % (CREATE_PARAMS['lat'],CREATE_PARAMS['lon'] )
        r = c.get( url )
        self.assertEquals( r.status_code, 200 )
        self.assertContains(r,"Clark Kent")
        self.assertContains(r,"user1@test.com")
        self.assertContains(r,"555-111-1111")
        # check that default values are not filled in
        # for a second, anonymous user (problem in the field)
        c2 = Client()
        r = c2.get( url )
        self.assertEquals( r.status_code, 200 )
        self.assertNotContains(r,"Clark Kent")
        self.assertNotContains(r,"user1@test.com")
        self.assertNotContains(r,"555-111-1111")
        
    def test_report_submit(self):
        params = CREATE_PARAMS.copy()
        params['author' ] = "Clark Kent"
        params['email'] = 'user1@test.com'
        params['phone'] = '555-111-1111'

        c = Client()
        r = c.login(username='user1',password='user1')
        
        # starting conditions
        self.assertEqual(Report.objects.filter(title=CREATE_PARAMS['title']).count(), 0 )
        self.assertEquals(len(mail.outbox), 0)
        self.assertEqual(ReportUpdate.objects.filter(author="Clark Kent",email='user1@test.com',desc=params['desc']).count(),0)

        # file the report
        response = c.post('/reports/', params, follow=True )
        self.assertEquals( response.status_code, 200 )
        self.assertEquals(response.template[0].name, 'reports/show.html')
        
        # there's a new report
        self.assertEqual(Report.objects.filter(title=CREATE_PARAMS['title'],is_confirmed=True,is_fixed=False).count(), 1 )
        self.assertEqual(ReportUpdate.objects.filter(author="Clark Kent",email='user1@test.com',desc=params['desc'],is_confirmed=True).count(),1)
                         
        # email should be sent directly to the city
        self.assertEquals(len(mail.outbox), 1)
        self.assertEquals(mail.outbox[0].to, [u'example_city_email@yahoo.ca'])

        
    def test_update_form(self):
        # check that default values are already filled in.
        c = Client()
        r = c.login(username='user1',password='user1')
        url = '/reports/4' 
        r = c.get( url )
        self.assertEquals( r.status_code, 200 )
        self.assertContains(r,"Clark Kent")
        self.assertContains(r,"user1@test.com")
        self.assertContains(r,"555-111-1111")

        # check that default values are NOT already filled in.
        # for a second client (problem in the field)
        c2 = Client()
        r = c2.get( url )
        self.assertEquals( r.status_code, 200 )
        self.assertNotContains(r,"Clark Kent")
        self.assertNotContains(r,"user1@test.com")
        self.assertNotContains(r,"555-111-1111")

        
    def test_update_submit(self):
        c = Client()
        r = c.login(username='user1',password='user1')
        
        # starting conditions
        self.assertEquals(len(mail.outbox), 0)
        self.assertEqual(ReportUpdate.objects.filter(author="Clark Kent",email='user1@test.com',desc=UPDATE_PARAMS['desc']).count(),0)

        # file the report
        response = c.post('/reports/4/updates/', UPDATE_PARAMS, follow=True )
        self.assertEquals( response.status_code, 200 )
        
        # there's a new update
        self.assertEqual(ReportUpdate.objects.filter(report__id=4,author="Clark Kent",email='user1@test.com',desc=UPDATE_PARAMS['desc'],is_fixed=True,is_confirmed=True).count(),1)
        self.assertEqual(Report.objects.filter(id=4,is_fixed=True).count(),1)
        
        # we're redirected to the report page
        self.assertEquals(response.template[0].name, 'reports/show.html')
        # and it has our update on it.
        self.assertContains(response,UPDATE_PARAMS['desc'])
        
        # update emails go out to reporter and everyone who has subscribed.
        # in this case, 'nooneimportant@test.com', and ourselves.
        
        self.assertEquals(len(mail.outbox), 2)
        self.assertEquals(mail.outbox[0].to,[u'user1@test.com'])
        self.assertEquals(mail.outbox[1].to,[u"noone_important@test.com"])
        
    def test_subscribe_form(self):
        # check that default values are already filled in.
        c = Client()
        r = c.login(username='user2',password='user2')
        r = c.get( '/reports/4/subscribers' )
        self.assertEquals( r.status_code, 200 )
        self.assertContains(r,"user2@test.com")
        c2 = Client()
        r = c2.get( '/reports/4/subscribers' )
        self.assertEquals( r.status_code, 200 )
        self.assertNotContains(r,"user2@test.com")

        
    def test_subscribe_submit(self):
        c = Client()
        r = c.login(username='user2',password='user2')
        
        # test starting conditions.
        self.assertEquals( ReportSubscriber.objects.filter(email='user2@test.com',report=4).count(),0)
        
        response = c.post('/reports/4/subscribers/', 
                               { 'email': 'user2@test.com'} , follow=True )
        
        self.assertEquals( response.status_code, 200 )
        self.assertEquals(response.template[0].name, 'reports/subscribers/create.html')
        
        # a confirmed subscriber should be created
        # no confirmation email should be sent
        self.assertEquals( ReportSubscriber.objects.filter(email='user2@test.com',report=4, is_confirmed=True).count(),1)
        self.assertEquals(len(mail.outbox), 0)
        
from registration.models import RegistrationProfile
from social_auth.models import UserSocialAuth

EMAIL='lala@test.com'
FNAME = 'fname'
LNAME = 'lname'
UID = '12345'
PHONE = '858-555-1212'
UPDATE_PHONE = '999-777-5555'
PASSWORD = 'pwd1'
SOCIAL_COMPLETE_URL_W_EMAIL ='/accounts/complete/dummy/?email=%s&first_name=%s&last_name=%s&uid=%s' % (  EMAIL, FNAME, LNAME, UID )
SOCIAL_COMPLETE_URL_NO_EMAIL ='/accounts/complete/dummy/?first_name=%s&last_name=%s&uid=%s' % (  FNAME, LNAME, UID )

# does not contain a UID.
SOCIAL_COMPLETE_URL_W_ERROR ='/accounts/complete/dummy/?first_name=%s&last_name=%s' % ( FNAME, LNAME )
        

REGISTER_POST = { 
                  'email': EMAIL,
                  'first_name':FNAME,
                  'last_name':LNAME,
                  'phone': PHONE,
                  'password1': 'pwd1',
                  'password2': 'pwd1'
                  }


class TestRegistration(TestCase):
    fixtures = []

    def setUp(self):
        self.curr_auth = settings.AUTHENTICATION_BACKENDS
        settings.AUTHENTICATION_BACKENDS += ('mainapp.tests.testsocial_auth.dummy_socialauth.DummyBackend',)

    def tearDown(self):
        """Restores settings to avoid breaking other tests."""
        settings.AUTHENTICATION_BACKENDS = self.curr_auth

    def test_socialuth_registration_w_noemail(self):
        # starting conditions        
        self.assertEquals(User.objects.filter(first_name=FNAME).count(),0)

        c = Client()
        response = self._do_social_auth(c,SOCIAL_COMPLETE_URL_NO_EMAIL)

        # calling the same URL twice doesn't make two sets.
        self._do_social_auth(c, SOCIAL_COMPLETE_URL_NO_EMAIL)
        
        # complete the registration.
        self._register(c)
        self._activate()
        self._login(c)
    
    def test_socialuth_registration_w_email(self):
        ''' As above, but user has email field set --
            should show up user model, and registraton form.
        '''
        # starting conditions
        self.assertEquals(User.objects.filter(email=EMAIL).count(),0)

        c = Client()
        response = self._do_social_auth(c, SOCIAL_COMPLETE_URL_W_EMAIL)

        # check that our user model has the email.
        self.assertEquals(User.objects.filter(email=EMAIL,first_name=FNAME,last_name=LNAME,is_active=False).count(),1)
        
        # check that email is in the form
        self.assertContains( response, EMAIL )

        # check that calling the same URL twice doesn't make 
        # two profiles.        

        self._do_social_auth(c, SOCIAL_COMPLETE_URL_W_EMAIL)

        # complete registration and get going.
        
        self._register(c)
        self._activate()
        self._login(c)

        
    def test_social_auth_login(self):
        c = Client()
        
        self._do_social_auth(c,SOCIAL_COMPLETE_URL_W_EMAIL)
        self._register(c)

        # activate the user.
        self._activate()
        
        # now, do social auth completion again.  are we logged in?        
        response = c.get(SOCIAL_COMPLETE_URL_W_EMAIL,follow=True)  
        self.assertEquals(response.status_code, 200 )
        self.assertEquals(response.templates[0].name, 'account/home.html')

    
    def test_normal_register(self):        
        # starting conditions
        self.assertEquals(User.objects.filter(first_name=FNAME).count(),0)

        c = Client()
        self._register(c,social_auth=False)
        self._activate()
        self._login(c)
        
    def test_edit(self):
        c = Client()
        self._register(c,social_auth=False)
        self._activate()
        self._login(c)

        # test we get the edit form
        response = c.get('/accounts/edit/',follow=True)        
        self.assertEquals(response.status_code, 200 )
        self.assertEquals(response.templates[0].name, 'account/edit.html')
        self.assertContains(response,'Editing User Profile For %s %s' % ( FNAME, LNAME ))
        self.assertContains(response,PHONE)
        
        # test submitting an updated phone #
        response = c.post( '/accounts/edit/', data={ 'phone': UPDATE_PHONE, 'first_name':FNAME, 'last_name':LNAME }, follow=True, **{ "wsgi.url_scheme" : "https" })
        self.assertEquals(response.status_code, 200 )
        self.assertEquals(response.templates[0].name, 'account/home.html')
        self.assertEquals(UserProfile.objects.filter(user__first_name=FNAME,phone=UPDATE_PHONE).count(),1)
        self.assertEquals(UserProfile.objects.filter(user__first_name=FNAME,phone=PHONE).count(),0)
        
    def test_social_auth_error(self):
        c = Client()
        response = c.get(SOCIAL_COMPLETE_URL_W_ERROR,follow=True)
        self.assertEquals(response.templates[0].name, 'registration/error.html')
        self.assertContains(response,'Missing user id')
        
    def test_normal_register_after_social_auth(self):
        c = Client()
        self._do_social_auth(c,SOCIAL_COMPLETE_URL_W_EMAIL)
        self._register(c)

        # activate the user.
        self._activate()
        
        # Empty the test outbox
        mail.outbox = []
        
        post_data = REGISTER_POST.copy()       
        response = c.post( '/accounts/register/', data=post_data, follow=True)

        #we should end up with an error
        self.assertEquals(response.status_code, 200 )
        self.assertEquals(response.templates[0].name, 'registration/registration_form.html')

    
    def _do_social_auth(self,c,url):
        response = c.get(url,follow=True)
        # we should be redirected to the registration form
        self.assertEquals( response.status_code, 200 )
        self.assertEquals(response.templates[0].name, 'registration/registration_form.html')

        # check that we've made the right models
        self.assertEquals(User.objects.filter(first_name=FNAME,last_name=LNAME,is_active=False).count(),1)
        self.assertEquals(RegistrationProfile.objects.filter(user__first_name=FNAME).count(),1)
        self.assertEquals(UserSocialAuth.objects.filter(user__first_name=FNAME,provider='dummy',uid=UID).count(),1)
        self.assertEquals(UserProfile.objects.filter(user__first_name=FNAME).count(),1)

        user = User.objects.get(first_name=FNAME)

        # make sure the form contains our defaults.
        self.assertContains( response, FNAME )
        self.assertContains( response, LNAME )
        self.assertContains( response, user.username )

        return response
    
    def _register(self, c, social_auth = True, dest= 'registration/registration_complete.html', active=False,email_expected = True):
        self.assertEquals(len(mail.outbox), 0)
        post_data = REGISTER_POST.copy()
        
        if social_auth:
            user = User.objects.get(first_name=FNAME)        
            post_data[ 'username' ] = user.username
        
        response = c.post( '/accounts/register/', data=post_data, follow=True, **{ "wsgi.url_scheme" : "https" })
        self.assertEquals(response.status_code, 200 )
        self.assertEquals(response.templates[0].name, dest)

        # check that the right models are updated
        self.assertEquals(User.objects.filter(first_name=FNAME,last_name=LNAME,email=EMAIL,username=EMAIL,is_active=active).count(),1)
        self.assertEquals(RegistrationProfile.objects.filter(user__first_name=FNAME).count(),1)
        self.assertEquals(UserProfile.objects.filter(user__first_name=FNAME,phone=PHONE).count(),1)
           
        if email_expected:
            # check that we've sent out an email
            self.assertEquals(len(mail.outbox), 1)
            self.assertEquals(mail.outbox[0].to,[EMAIL])
        else:
            self.assertEquals(len(mail.outbox), 0)
            
        return response
    
    def _activate(self):
        user = User.objects.get(first_name = FNAME)
        user.is_active = True
        user.save()
        
    def _login(self,c):
        rc = c.login(username=EMAIL,password=PASSWORD)
        self.assertEquals(rc, True)

