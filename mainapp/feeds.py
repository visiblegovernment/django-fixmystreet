from django.contrib.syndication.feeds import Feed
from django.contrib.syndication.feeds import FeedDoesNotExist
from django.core.exceptions import ObjectDoesNotExist
from mainapp.models import Report, ReportUpdate, City, Ward

class LatestReports(Feed):
    title = "All FixMyStreet Reports"
    link = "/reports/"
    description = "All FixMyStreet.ca Reports"

    def items(self):
        return Report.objects.filter(is_confirmed=True).order_by('-created_at')[:30]

class LatestReportsByCity(Feed):
    
    def get_object(self, bits):
        # In case of "/rss/beats/0613/foo/bar/baz/", or other such clutter,
        # check that bits has only one member.
        if len(bits) != 1:
            raise ObjectDoesNotExist        
        return City.objects.get(id=bits[0])

    def title(self, obj):
        return "FixMyStreet.ca: Reports for %s" % obj.name

    def link(self, obj):
        if not obj:
            raise FeedDoesNotExist
        return obj.get_absolute_url()

    def description(self, obj):
        return "Problems recently reported in the city of %s" % obj.name

    def items(self, obj):
       return Report.objects.filter(is_confirmed=True,ward__city=obj.id).order_by('-created_at')[:30]


class LatestReportsByWard(Feed):
    
    def get_object(self, bits):
        # In case of "/rss/beats/0613/foo/bar/baz/", or other such clutter,
        # check that bits has only one member.
        if len(bits) != 1:
            raise ObjectDoesNotExist        
        return Ward.objects.get(id=bits[0])

    def title(self, obj):
        return "FixMyStreet.ca: Reports for %s" % obj.name

    def link(self, obj):
        if not obj:
            raise FeedDoesNotExist
        return obj.get_absolute_url()

    def description(self, obj):
        return "Problems recently reports in %s, %s" % ( obj.name, obj.city.name)

    def items(self, obj):
       return Report.objects.filter(is_confirmed=True,ward=obj.id).order_by('-created_at')[:30]

# Allow subsciption to a particular report.

class LatestUpdatesByReport(Feed):
    
    def get_object(self, bits):
        # In case of "/rss/beats/0613/foo/bar/baz/", or other such clutter,
        # check that bits has only one member.
        if len(bits) != 1:
            raise ObjectDoesNotExist        
        return Report.objects.get(id=bits[0])

    def title(self, obj):
        return "FixMyStreet.ca: Updates for Report %s" % obj.title

    def link(self, obj):
        if not obj:
            raise FeedDoesNotExist
        return obj.get_absolute_url()
    
    def item_link(self,obj):
        return( obj.report.get_absolute_url())

    def description(self, obj):
        return "Updates for FixMySteet.ca Problem Report %s" % obj.title

    def items(self, obj):
       return obj.reportupdate_set.order_by('created_at')[:30]
