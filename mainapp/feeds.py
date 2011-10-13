from django.contrib.syndication.views import Feed
from django.contrib.syndication.feeds import FeedDoesNotExist
from mainapp.models import Report, ReportUpdate, City, Ward
from django.shortcuts import get_object_or_404

class ReportFeedBase(Feed):
    description_template = 'feeds/reports_description.html'

    def item_title(self, item):
        return item.title

    def item_pubdate(self, item):
        return item.created_at
    
    def item_link(self,item):
        return item.get_absolute_url()

    
class LatestReports(ReportFeedBase):
    title = "All FixMyStreet Reports"
    link = "/reports/"
    description = "All FixMyStreet.ca Reports"

    def items(self):
        return Report.objects.filter(is_confirmed=True).order_by('-created_at')[:30]

class CityFeedBase(ReportFeedBase):
    
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


class CityIdFeed(CityFeedBase):
    ''' retrieve city by id '''
    def get_object(self, request, id ):
       return get_object_or_404(City, pk=id)

class CitySlugFeed(CityFeedBase):
    ''' retrieve city by slug '''
    def get_object(self, request, slug ):
       return get_object_or_404(City, slug=slug)
    
class WardFeedBase(ReportFeedBase):
    
    def title(self, obj):
        return "FixMyStreet.ca: Reports for %s, %s" % (obj.name, obj.city.name)

    def link(self, obj):
        if not obj:
            raise FeedDoesNotExist
        return obj.get_absolute_url()

    def description(self, obj):
        return "Problems recently reported in %s, %s" % ( obj.name, obj.city.name)

    def items(self, obj):
       return Report.objects.filter(is_confirmed=True,ward=obj.id).order_by('-created_at')[:30]


class WardIdFeed(WardFeedBase):
    ''' retrieve city by id '''
    def get_object(self, request, id ):
       return get_object_or_404(Ward, pk=id)

class WardSlugFeed(WardFeedBase):
    ''' retrieve city by slug '''
    def get_object(self, request, city_slug, ward_slug ):
       return get_object_or_404(Ward, slug=ward_slug,city__slug=city_slug)
    

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
