from django.shortcuts import render_to_response, get_object_or_404
from django.http import HttpResponseRedirect
from mainapp.models import Report, ReportUpdate, Ward, FixMyStreetMap, ReportCountQuery, City, FaqEntry, GoogleAddressLookup
from mainapp import search
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
        address = iri_to_uri(u'/search?q=%s' % request.POST["q"])
        return HttpResponseRedirect( address )

    address = request.GET["q"]

    match_index = -1
    if request.GET.has_key("index"):
        match_index = int(request.GET["index"] or 0)

    addrs = []
    try:
        point_str = search.search_address(address, match_index, addrs)
    except search.SearchAddressDisambiguateError, e:
        # addrs = address_lookup.get_match_options()
        addr_list = ""
        for i in range(0,len(addrs)):
            link = "/search?q=" + urlquote(address) + "&index=" + str(i)
            addr_list += "<li><a href='%s'>%s</a></li>" % ( link, addrs[i] )
            addr_list += "</ul>"
        return index(request,disambiguate = addr_list )
    except search.SearchAddressException, e:
        return index(request, _(str(e)))

    pnt = fromstr(point_str, srid=4326)

    try:
        wards = search.search_wards(point_str)
    except search.SearchAddressNotSupported, e:
        return( index(request, _(str(e))))

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
