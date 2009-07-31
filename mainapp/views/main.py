from django.shortcuts import render_to_response, get_object_or_404
from django.http import HttpResponseRedirect
from mainapp.models import Report, ReportUpdate, Ward, FixMyStreetMap, ReportCountQuery, City, FaqEntry, GoogleAddressLookup
from django.template import Context, RequestContext
from django.contrib.gis.measure import D 
from django.contrib.gis.geos import *
import settings
from django.utils.translation import ugettext as _
from django.utils.http import urlquote
from django.utils.encoding import iri_to_uri
import logging
import os
import urllib



def index(request, error_msg = None, disambiguate=None): 
    reports_with_photos = Report.objects.filter(is_confirmed=True).exclude(photo='').order_by("-created_at")[:3]
    recent_reports = Report.objects.filter(is_confirmed=True).order_by("-created_at")[:5]
        
    return render_to_response("index.html",
                {"report_counts": ReportCountQuery('1 year'),
                 "cities": City.objects.all(),
                 "reports_with_photos": reports_with_photos,
                 "recent_reports": recent_reports , 
                 'error_msg': error_msg,
                 'disambiguate':disambiguate },
                context_instance=RequestContext(request))    


def search_address(request):
    if request.method == 'POST':
        print request.POST['q']
        address = iri_to_uri(u'/search?q=%s' % request.POST["q"])
        print address
        return HttpResponseRedirect( address )
#        address = urllib.urlencode({'x':urlquote(request.POST["q"])})[2:]
#        return HttpResponseRedirect("/search?q=" + address )

    address = request.GET["q"] 
    address_lookup = GoogleAddressLookup( address )

    if not address_lookup.resolve():
        return index(request, _("Sorry, we couldn\'t retreive the coordinates of that location, please use the Back button on your browser and try something more specific or include the city name at the end of your search."))
    
    if not address_lookup.exists():
        return index( request, _("Sorry, we couldn\'t find the address you entered.  Please try again with another intersection, address or postal code, or add the name of the city to the end of the search."))

    if address_lookup.matches_multiple() and not request.GET.has_key("index"):
        addrs = address_lookup.get_match_options() 
        addr_list = "" 
        for i in range(0,len(addrs)):
            link = "/search?q=" + urlquote(address) + "&index=" + str(i)
            addr_list += "<li><a href='%s'>%s</a></li>" % ( link, addrs[i] )
            addr_list += "</ul>"
        return index(request,disambiguate = addr_list )
    
    # otherwise, we have a specific match
    match_index = 0
    if request.GET.has_key("index"):
        match_index = int(request.GET["index"])
            
    point_str = "POINT(" + address_lookup.lon(match_index) + " " + address_lookup.lat(match_index) + ")"
    pnt = fromstr(point_str, srid=4326)    
    wards = Ward.objects.filter(geom__contains=point_str)
    if (len(wards) == 0):
        return( index(request, _("Sorry, we don't yet have that area in our database.  Please have your area councillor contact fixmystreet.ca.")))
    
    reports = Report.objects.filter(is_confirmed = True,point__distance_lte=(pnt,D(km=4))).distance(pnt).order_by('distance')
    gmap = FixMyStreetMap(pnt,True,reports)
        
    return render_to_response("search_result.html",
                {'google' : gmap,
                 "pnt": pnt,
                 "enable_map": True,
                 "ward" : wards[0],
                 "reports" : reports, },
                 context_instance=RequestContext(request))

def about(request):
   return render_to_response("about.html",{'faq_entries' : FaqEntry.objects.all().order_by('order')},
                context_instance=RequestContext(request))    
