from mainapp.models import Report,ReportUpdate
from optparse import make_option
import csv
from django.core.management.base import NoArgsCommand,CommandError
from unicodewriter import UnicodeWriter

class StatBase(object):
    
    def results(self):
        pass
    
    def add_report(self,report):
        pass
    
class Stat(StatBase):

    def __init__(self,name):
        self.name = name
        self.count = 0
        
    def get_fix_time(self,report):
        """ a commonly used computation """
        if (not report.is_fixed) or (report.fixed_at == None):
            raise Exception("report is not fixed")
        return( report.fixed_at - report.created_at )
    
    def labels(self):
        return( [ self.name ])
    
class StatColGroup(StatBase):
    def __init__(self, stats = []):
        self.stats = stats
        
    def labels(self):
        labels = []
        for stat in self.stats:
            for label in stat.labels():
                labels.append( label )
        return( labels )
    
    def result(self):
        row = []
        for stat in self.stats:
            row.append( stat.result() )
        return( [ row ] )
        
    def add_report(self,report):
        for stat in self.stats:
            stat.add_report(report)
        
    
class StatRowGroup(StatBase):
    def __init__(self,name,newstat_fcn):
        self.name = name
        self.newstat_fcn = newstat_fcn
        self.stat_group = {}
        self.stat_group['All'] = newstat_fcn()

    def labels(self):
        labels = self.stat_group['All'].labels()
        labels.insert(0,self.name)
        return( labels )
    
    def get_group_key(self, report):
        return( None )
 
    def add_report(self,report):
        key = self.get_group_key( report )
        if not self.stat_group.has_key(key):
            self.stat_group[key] = self.newstat_fcn()
        stat = self.stat_group[key]
        stat.add_report(report)
        self.stat_group['All'].add_report(report)
        
    def result(self):
        rows = []
        for key in self.stat_group.keys():
            key_rows = self.stat_group[key].result()
            for row in key_rows:
                row.insert(0,key)
                rows.append(row)

        return( rows )

    
class CityStatGroup(StatRowGroup):
    def __init__(self,newstat_fcn):
        super(CityStatGroup,self).__init__('City',newstat_fcn)
    
    def get_group_key(self,report):
        return( report.ward.city.name )

class CategoryStatGroup(StatRowGroup):
    def __init__(self,newstat_fcn):
        super(CategoryStatGroup,self).__init__('Category',newstat_fcn)
    
    def get_group_key(self,report):
        return( report.category.category_class.name_en )
            
    
class AvgTimeToFix(Stat):  
    def __init__(self):
        super(AvgTimeToFix,self).__init__("Time To Fix")
        self.total = 0
        
    def add_report(self,report):
        if not report.is_fixed:
            return
        fix_time = self.get_fix_time(report)
        self.total += fix_time.days
        self.count += 1

    def result(self):
        if self.count == 0:
            return 0
        return( self.total / self.count )
    
class PercentFixedInDays(Stat):
    
    MAX_NUM_DAYS = 9999
    
    def __init__(self,min_num_days = 0,max_num_days = MAX_NUM_DAYS):
        if max_num_days == PercentFixedInDays.MAX_NUM_DAYS:
            name = "Fixed After %d Days" % ( min_num_days )
        else:
            name = "Fixed in %d-%d Days" % (min_num_days, max_num_days)
            
        super(PercentFixedInDays,self).__init__(name)
        self.total_fixed_in_period = 0
        self.min_num_days = min_num_days
        self.max_num_days = max_num_days
        
    def add_report(self,report):
        self.count += 1

        if not report.is_fixed:
            return
        fix_days = self.get_fix_time(report).days
        if fix_days < self.min_num_days:
            return
        if fix_days >= self.max_num_days:
            return
        
        self.total_fixed_in_period += 1    

    def result(self):
        if self.count == 0:
            return 0
        return( float(self.total_fixed_in_period) / self.count )
    

class PercentFixed(Stat):
    def __init__(self, name = "Percent Fixed", fixed_value = True):
        super(PercentFixed,self).__init__(name)
        self.total = 0
        self.fixed_value = fixed_value

    def add_report(self,report):
        self.count += 1
        if  report.is_fixed != self.fixed_value:
            return
        self.total += 1

    def result(self):
        if self.count == 0:
            return 0
        return( float(self.total) / self.count )

class PercentUnfixed(PercentFixed):
    
    def __init__(self):
        super(PercentUnfixed,self).__init__("Percent Unfixed",False)


class NumReports(Stat):

    def __init__(self):
        super(NumReports,self).__init__("Total Reports")

    def add_report(self,report):
        self.count += 1

    def result(self):
        return( self.count )

    
class StatGroup1(StatColGroup):
    
    def __init__(self):
        stats = []
        stats.append(NumReports())
        stats.append(AvgTimeToFix())
        stats.append(PercentFixed())
        stats.append(PercentUnfixed())
        stats.append(PercentFixedInDays(0,7))
        stats.append(PercentFixedInDays(7,30))
        stats.append(PercentFixedInDays(30,60))
        stats.append(PercentFixedInDays(60,180))
        stats.append(PercentFixedInDays(180,PercentFixedInDays.MAX_NUM_DAYS))

        super(StatGroup1,self).__init__(stats=stats)

class StatGroup2(CategoryStatGroup):
    def __init__(self):
        super(StatGroup2,self).__init__(StatGroup1)
        
class StatGroup3(CityStatGroup):
    def __init__(self):
        super(StatGroup3,self).__init__(StatGroup2)
        
class Command(NoArgsCommand):
    help = 'Get Time To Fix Statistics'

    def handle_noargs(self, **options):
        stat_group = StatGroup3()
        reports = Report.objects.filter(is_confirmed=True)
        for report in reports:
            stat_group.add_report(report)
        
        results = stat_group.result()
        print ",".join(stat_group.labels())
        for result_row in results:
            str_row = []
            for result in result_row:
                str_row.append(str(result))
            print ",".join(str_row)
