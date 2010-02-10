from django.test import TestCase
from mainapp.models import Report,ReportUpdate,Ward,City
from mainapp.management.commands.stats import CityStatGroup,CategoryStatGroup,StatColGroup,AvgTimeToFix, PercentUnfixed, PercentFixedInDays

class StatTestCase(TestCase):
    fixtures = ['test_stats.json']
    
    def setUp(self):
        self.reports = Report.objects.filter(is_confirmed=True)
        
    def check_result(self,stat_instance,expected):
        for report in self.reports:
            stat_instance.add_report(report)
        self.assertEquals(stat_instance.result(), expected)
            

class AvgFixTestCase(StatTestCase):
    
    def test(self):
        self.check_result(AvgTimeToFix(), 9)

class UnfixedTestCase(StatTestCase):
    
    def test(self):
        self.check_result(PercentUnfixed(), .5)

class FixedInDaysTestCase(StatTestCase):
    
    def test(self):
        self.check_result(PercentFixedInDays(0,3), .25)
        self.check_result(PercentFixedInDays(3,19), .25)
        self.check_result(PercentFixedInDays(0,19), .5)
        
class ColGroupTestCase(StatTestCase):
    
    def test(self):
        group = StatColGroup( stats = [ PercentFixedInDays(0,3), PercentUnfixed() ] )
        self.check_result(group, [[ .25, .5 ]])
        self.assertEquals(group.labels(),  ['Fixed in 0-3 Days', 'Percent Unfixed'] )


class TestStatGroup1(StatColGroup):
    def __init__(self):
        super(TestStatGroup1,self).__init__(stats = [ PercentFixedInDays(0,3),PercentFixedInDays(3,18), PercentUnfixed() ])
        
        
class CategoryTestCase(StatTestCase):
    
    def test(self):
        cat_group = CategoryStatGroup(TestStatGroup1)
        self.assertEquals(cat_group.labels(),  ['Category','Fixed in 0-3 Days','Fixed in 3-18 Days', 'Percent Unfixed'] )
        self.check_result(cat_group, [[ 'All',.25, .25, .5 ], [u'Grafitti',0,.5,.5],[u'Parks',.5, 0, .5]])


class CityTestCase(StatTestCase):

    def test(self):
        cat_group = CityStatGroup(TestStatGroup1)
        self.assertEquals(cat_group.labels(),  ['City','Fixed in 0-3 Days','Fixed in 3-18 Days', 'Percent Unfixed'] )
        self.check_result(cat_group, [[ 'All',.25, .25, .5 ], [u'Oglo',.25,.25,.5]])
