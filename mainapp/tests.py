"""
"""

from django.test import TestCase
from mainapp.models import Report,ReportUpdate,EmailRule, City, Ward,ReportCategory,ReportCategoryClass


class EmailRuleTestBase(TestCase):
    fixtures = ['test_email_rules.json']
    
    def setUp(self):
        # these are from the fixtures file.
        self.test_categoryclass = ReportCategoryClass.objects.get(name_en='Parks')
        self.test_category = ReportCategory.objects.get(name_en='Broken or Damaged Equipment/Play Structures')
        self.not_test_category = ReportCategory.objects.get(name_en='Damaged Curb')

        self.test_city = City.objects.get(name='TestCityWithoutEmail')
        self.test_ward = Ward.objects.get(name = 'WardInCityWithNo311Email')
        self.test_report = Report(ward=self.test_ward,category=self.test_category)
    
class TestNoRules(EmailRuleTestBase):
        
    def test(self):
        self.failUnlessEqual( self.test_ward.get_emails(self.test_report), ([],[]) )


class TestNoRulesWCityEmail(EmailRuleTestBase):

    def test(self):
        ward_w_email = Ward.objects.get(name='WardInCityWith311Email')
        self.failUnlessEqual( ward_w_email.get_emails(self.test_report),([ ward_w_email.city.email ],[]) )

class TestToCouncillor(EmailRuleTestBase):

    def test(self):
        rule = EmailRule( rule=EmailRule.TO_COUNCILLOR, city = self.test_city )
        rule.save()
        self.failUnlessEqual( self.test_ward.get_emails(self.test_report), ([self.test_report.ward.councillor.email],[]) )
        


class TestMatchingCategoryClass(EmailRuleTestBase):

    def test(self):
        email = 'parks@city.ca'
        rule = EmailRule( rule=EmailRule.MATCHING_CATEGORY_CLASS, city = self.test_city, category_class = self.test_categoryclass, email=email )
        rule.save()
        self.failUnlessEqual( self.test_ward.get_emails(self.test_report), ([email],[]) )
        report2 = Report(ward=self.test_ward,category=self.not_test_category)
        self.failUnlessEqual( self.test_ward.get_emails(report2), ([],[]) )
        

class TestNotMatchingCategoryClass(EmailRuleTestBase):

    def test(self):
        email = 'parks@city.ca'
        rule = EmailRule( rule=EmailRule.NOT_MATCHING_CATEGORY_CLASS, city = self.test_city, category_class = self.test_categoryclass, email=email )
        rule.save()
        self.failUnlessEqual( self.test_ward.get_emails(self.test_report), ([],[]) )
        report2 = Report(ward=self.test_ward,category=self.not_test_category)
        self.failUnlessEqual( self.test_ward.get_emails(report2), ([email],[]) )
        
        
class TestCharlottetownRules(EmailRuleTestBase):

    def test(self):

        # simulate Charlottetown's somewhat complicated cases:
        # 
        # For all categories except Parks, send email to  not_parks1@city.com  and  not_parks2@city.com
        # with a Cc: to not_parks_cc@city.com  and  the ward councillor.
        #
        # For the category of Parks, send email to:  parks@city.com
        # with a Cc: to  parks_cc@city.com  and  the ward councillor   
        #
        parks_category = ReportCategory.objects.get(name_en='Lights Malfunctioning in Park')
        not_parks_category = ReportCategory.objects.get(name_en='Damaged Curb')
        parks_category_class = ReportCategoryClass.objects.get(name_en='Parks')
        
        # always CC the councillor
        EmailRule( is_cc=True, rule=EmailRule.TO_COUNCILLOR, city = self.test_city ).save()
        
        # parks rules
        EmailRule(rule=EmailRule.MATCHING_CATEGORY_CLASS, city =self.test_city, category_class = parks_category_class, email='parks@city.com' ).save()
        EmailRule(rule=EmailRule.MATCHING_CATEGORY_CLASS, city =self.test_city, category_class = parks_category_class, email='parks_cc@city.com', is_cc=True ).save()

        # not parks rules
        EmailRule( rule=EmailRule.NOT_MATCHING_CATEGORY_CLASS, city = self.test_city, category_class = parks_category_class, email='not_parks1@city.com' ).save()
        EmailRule( rule=EmailRule.NOT_MATCHING_CATEGORY_CLASS, city = self.test_city, category_class = parks_category_class, email='not_parks2@city.com' ).save()
        EmailRule( rule=EmailRule.NOT_MATCHING_CATEGORY_CLASS, city = self.test_city, category_class = parks_category_class, email='not_parks_cc@city.com', is_cc=True ).save()
        
        parks_report = Report(ward=self.test_ward,category = parks_category )
        self.failUnlessEqual( self.test_ward.get_emails(parks_report), ([ u'parks@city.com' ],[u"councillor_email@testward1.com", u'parks_cc@city.com'] ))
        
        not_parks_report = Report(ward=self.test_ward,category = not_parks_category )
        self.failUnlessEqual( self.test_ward.get_emails(not_parks_report), ([ u'not_parks1@city.com',u'not_parks2@city.com' ], [u"councillor_email@testward1.com",u'not_parks_cc@city.com'] ))
    