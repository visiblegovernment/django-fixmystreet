from django.shortcuts import render_to_response, get_object_or_404
from django.http import HttpResponseRedirect, Http404
from mainapp.models import DictToPoint, Report, ReportUpdate, Ward, FixMyStreetMap, ReportCountQuery, City, FaqEntry
from mainapp import search
from django.template import Context, RequestContext
from django.contrib.gis.measure import D 
from django.contrib.gis.geos import *
import settings
import datetime
from django.utils.translation import ugettext as _
from django.utils.http import urlquote
from django.utils.encoding import iri_to_uri
from mainapp.views.cities import home as city_home
import logging
import os
import urllib


def home(request, location = None, error_msg =None): 

    if request.subdomain:
        matching_cities = City.objects.filter(name__iexact=request.subdomain)
        if matching_cities:
            return( city_home(request, matching_cities[0], error_msg, disambiguate ) )

    if request.GET.has_key('q'):
        location = request.GET["q"]
                    
    return render_to_response("home.html",
                {"report_counts": ReportCountQuery('1 year'),
                 "cities": City.objects.all(),
                 'search_error': error_msg,
                 'location':location,
                 'GOOGLE_KEY': settings.GMAP_KEY },
                context_instance=RequestContext(request))    

def _search_url(request,years_ago):
    return('/search?lat=%s;lon=%s;years_ago=%s' % ( request.GET['lat'], request.GET['lon'], years_ago ))
           
def search_address(request):
    if request.method == 'POST':
        address = iri_to_uri(u'/search?q=%s' % request.POST["q"])
        return HttpResponseRedirect( address )

    if request.GET.has_key('q'):
        address = request.GET["q"]
        return home( request, address, None )

    # should have a lat and lon by this time.
    dict2pt = DictToPoint( request.GET )
    pnt = dict2pt.pnt()
    wards = Ward.objects.filter(geom__contains=dict2pt.__unicode__())
    if (len(wards) == 0):
        return( home(request, None, _("Sorry, we don't yet have that area in our database. Please have your area councillor contact fixmystreet.ca.")))
    
    ward = wards[0]
    
    # calculate date range for which to return reports
    if request.GET.has_key('years_ago'):
        years_ago = int(request.GET['years_ago'])
    else:
        years_ago = 0
    yearoffset = datetime.timedelta(days = 365 * years_ago )
    
    date_range_end = datetime.datetime.now() - yearoffset
    date_range_start = date_range_end - datetime.timedelta(days =365)
    
    # do we want to show older reports?
    if Report.objects.filter(ward=ward,created_at__lte=date_range_start).count() > 1:
        older_reports_link = _search_url(request, years_ago - 1) 
    else:
        older_reports_link = None
        
    reports = Report.objects.filter(created_at__gte = date_range_start, created_at__lte = date_range_end, is_confirmed = True,point__distance_lte=(pnt,D(km=2))).distance(pnt).order_by('-created_at')
    gmap = FixMyStreetMap(pnt,True,reports)
        
    return render_to_response("search_result.html",
                {'google' : gmap,
                 'GOOGLE_KEY': settings.GMAP_KEY,
                 "pnt": pnt,
                 "enable_map": True,
                 "ward" : wards[0],
                 "reports" : reports,
                 "date_range_start": date_range_start,
                 "date_range_end": date_range_end,
                 "older_reports_link": older_reports_link },
                 context_instance=RequestContext(request))


def about(request):
   return render_to_response("about.html",{'faq_entries' : FaqEntry.objects.all().order_by('order')},
                context_instance=RequestContext(request)) 
   
def posters(request): 
   return render_to_response("posters.html",
                {'languages': settings.LANGUAGES },
                 context_instance=RequestContext(request))
      
