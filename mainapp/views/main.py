from django.shortcuts import render_to_response, get_object_or_404
from django.http import HttpResponseRedirect
from mainapp.models import Report, ReportUpdate, Ward, FixMyStreetMap, ReportCountQuery, City, FaqEntry
import urllib
import libxml2
from django.template import Context, RequestContext
from django.contrib.gis.measure import D 
from django.contrib.gis.geos import *
import settings
from django.utils.translation import ugettext as _
import logging
import os


def index(request, error_msg = None, disambiguate=None): 
    reports_with_photos = Report.objects.filter(is_confirmed=True).exclude(photo='').order_by("-created_at")[:3]
    recent_reports = Report.objects.filter(is_confirmed=True).order_by("-created_at")[:5]
        
    return render_to_response("index.html",
                {"report_counts": ReportCountQuery(),
                 "cities": City.objects.all(),
                 "reports_with_photos": reports_with_photos,
                 "recent_reports": recent_reports , 
                 'error_msg': error_msg,
                 'disambiguate':disambiguate },
                context_instance=RequestContext(request))    


def search_address(request):
    if request.method == 'POST':
        address = urllib.urlencode({'x':request.POST["q"]})[2:]
        return HttpResponseRedirect("/search?q=" + address )

    address = urllib.urlencode({'x':request.GET["q"]})[2:]
    url = "http://maps.google.ca/maps/geo?q=" + address + "&output=xml&key=" + settings.GMAP_KEY
 
    try:
        resp = urllib.urlopen(url).read()
    except:
        return index(request, _("Sorry, we couldn\'t retreive the coordinates of that location, please use the Back button on your browser and try something more specific or include the city name at the end of your search."))

    doc = libxml2.parseDoc(resp)
    xpathContext = doc.xpathNewContext()
    xpathContext.xpathRegisterNs('google', 'http://earth.google.com/kml/2.0')
    coord_nodes = xpathContext.xpathEval("//google:coordinates")

    if(len(coord_nodes) == 0):
        return index( request, _("Sorry, we couldn\'t find the address you entered.  Please try again with another intersection, address or postal code, or add the name of the city to the end of the search."))
    
    coord_index = 0
    if len(coord_nodes) > 1:
        if not request.GET.has_key("index"):
            addr_nodes = xpathContext.xpathEval("//google:address")
            addr_list = "<ul>"
            for i in range(0,len(addr_nodes)):
                link = "/search?q=" + address + "&index=" + str(i)
                addr_list += "<li><a href='%s'>%s</a></li>" % ( link, addr_nodes[i].content )
            addr_list += "</ul>"
            return index(request,disambiguate = addr_list )
        else:
            coord_index = int(request.GET["index"])
            
    coord = coord_nodes[coord_index]
    coords = coord.content.split(',')
    lat = coords[1]
    lon = coords[0]
    point_str = "POINT(" + lon + " " + lat + ")"
    pnt = fromstr(point_str, srid=4326)    
    wards = Ward.objects.filter(geom__contains=point_str)
    if (len(wards) == 0):
        return( index(request, _("Sorry, we don't yet have that area in our database.  Please have your area councillor contact fixmystreet.ca.")))
    
    #logging.debug( " %d wards returned" % len(wards) )
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
