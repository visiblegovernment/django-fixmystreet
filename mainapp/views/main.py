from django.shortcuts import render_to_response, get_object_or_404
from django.http import HttpResponseRedirect, Http404
from mainapp.models import DictToPoint, Report, ReportUpdate, Ward, FixMyStreetMap, OverallReportCount, City, FaqEntry
from django.core.paginator import Paginator, InvalidPage, EmptyPage
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
                {"report_counts": OverallReportCount('1 year'),
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
    ward = dict2pt.ward()
    if not ward:
        return( home(request, None, _("Sorry, we don't yet have that area in our database. Please have your area councillor contact fixmystreet.ca.")))
    
    try:
        page_no = int(request.GET.get('page', '1'))
    except ValueError:
        page_no = 1

    reportQ = Report.objects.filter(is_confirmed = True,point__distance_lte=(pnt,D(km=2))).distance(pnt).order_by('-created_at')
    paginator = Paginator(reportQ, 100) 
    
    try:
        page = paginator.page(page_no)
    except (EmptyPage, InvalidPage):
        page = paginator.page(paginator.num_pages)

    
    reports = page.object_list
    gmap = FixMyStreetMap(pnt,True,reports)
        
    return render_to_response("search_result.html",
                {'google' : gmap,
                 'GOOGLE_KEY': settings.GMAP_KEY,
                 "pnt": pnt,
                 "enable_map": True,
                 "ward" : ward,
                 "reports" : reports,
                 "page":page,
                 "url_parms": "&lat=%s&lon=%s" %( request.GET['lat'], request.GET['lon'])
                  },
                 context_instance=RequestContext(request))


def about(request):
   return render_to_response("about.html",{'faq_entries' : FaqEntry.objects.all().order_by('order')},
                context_instance=RequestContext(request)) 
   
def posters(request): 
   return render_to_response("posters.html",
                {'languages': settings.LANGUAGES },
                 context_instance=RequestContext(request))
      
def privacy(request): 
   return render_to_response("privacy.html",
                { },
                 context_instance=RequestContext(request))
