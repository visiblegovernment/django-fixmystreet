from django.shortcuts import render_to_response, get_object_or_404
from django.http import HttpResponseRedirect
from mainapp.models import Report, ReportUpdate, Ward, FixMyStreetMap, ReportCountQuery, City, FaqEntry, GoogleAddressLookup
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


def home(request, error_msg = None, disambiguate=None): 
    if request.subdomain:
        matching_cities = City.objects.filter(name__iexact=request.subdomain)
        if matching_cities:
            return( city_home(request, matching_cities[0], error_msg, disambiguate ) )
                    
    return render_to_response("home.html",
                {"report_counts": ReportCountQuery('1 year'),
                 "cities": City.objects.all(),
                 'error_msg': error_msg,
                 'disambiguate':disambiguate },
                context_instance=RequestContext(request))    

def search_address(request):
    if request.method == 'POST':
        address = iri_to_uri(u'/search?q=%s' % request.POST["q"])
        return HttpResponseRedirect( address )
# address = urllib.urlencode({'x':urlquote(request.POST["q"])})[2:]
# return HttpResponseRedirect("/search?q=" + address )

    address = request.GET["q"]
    address_lookup = GoogleAddressLookup( address )

    if not address_lookup.resolve():
        return home(request, _("Sorry, we couldn\'t retreive the coordinates of that location, please use the Back button on your browser and try something more specific or include the city name at the end of your search."))
    
    if not address_lookup.exists():
        return home( request, _("Sorry, we couldn\'t find the address you entered. Please try again with another intersection, address or postal code, or add the name of the city to the end of the search."))

    if address_lookup.matches_multiple() and not request.GET.has_key("index"):
        addrs = address_lookup.get_match_options()
        disambiguate_list = {}
        for i in range(0,len(addrs)):
            link = "/search?q=" + urlquote(address) + "&index=" + str(i)
            disambiguate_list[ link ] = addrs[i]
        return home(request,disambiguate = disambiguate_list )
    
    # otherwise, we have a specific match
    match_index = 0
    if request.GET.has_key("index"):
        match_index = int(request.GET["index"])
            
    point_str = "POINT(" + address_lookup.lon(match_index) + " " + address_lookup.lat(match_index) + ")"
    pnt = fromstr(point_str, srid=4326)
    wards = Ward.objects.filter(geom__contains=point_str)
    if (len(wards) == 0):
        return( home(request, _("Sorry, we don't yet have that area in our database. Please have your area councillor contact fixmystreet.ca.")))
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
        older_reports_link = "/search?q=%s;index=%i;years_ago=%i" %( urlquote(address),match_index, years_ago + 1)
    else:
        older_reports_link = None
        
    reports = Report.objects.filter(created_at__gte = date_range_start, created_at__lte = date_range_end, is_confirmed = True,point__distance_lte=(pnt,D(km=2))).distance(pnt).order_by('-created_at')
    gmap = FixMyStreetMap(pnt,True,reports)
        
    return render_to_response("search_result.html",
                {'google' : gmap,
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
