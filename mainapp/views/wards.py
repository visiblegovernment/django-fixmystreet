from django.shortcuts import render_to_response, get_object_or_404
from mainapp.models import City, Ward, WardMap, Report
from django.template import Context, RequestContext
from django.db import connection
from django.utils.translation import ugettext_lazy, ugettext as _
from django.core.paginator import Paginator, InvalidPage, EmptyPage

import datetime
    
def show( request, ward ):
    
    try:
        page_no = int(request.GET.get('page', '1'))
    except ValueError:
        page_no = 1

    all_reports = Report.objects.filter( ward = ward, is_confirmed = True ).extra( select = { 'status' : """
        CASE 
        WHEN age( clock_timestamp(), created_at ) < interval '1 month' AND is_fixed = false THEN 'New Problems'
        WHEN age( clock_timestamp(), created_at ) > interval '1 month' AND is_fixed = false THEN 'Older Unresolved Problems'
        WHEN age( clock_timestamp(), fixed_at ) < interval '1 month' AND is_fixed = true THEN 'Recently Fixed'
        WHEN age( clock_timestamp(), fixed_at ) > interval '1 month' AND is_fixed = true THEN 'Old Fixed'
        ELSE 'Unknown Status'
        END """,
        'status_int' : """
        CASE 
        WHEN age( clock_timestamp(), created_at ) < interval '1 month' AND is_fixed = false THEN 0
        WHEN age( clock_timestamp(), created_at ) > interval '1 month' AND is_fixed = false THEN 1
        WHEN age( clock_timestamp(), fixed_at ) < interval '1 month' AND is_fixed = true THEN 2
        WHEN age( clock_timestamp(), fixed_at ) > interval '1 month' AND is_fixed = true THEN 3
        ELSE 4
        END """ } ).order_by('-created_at') 
        
    paginator = Paginator(all_reports, 100) 
    try:
        page = paginator.page(page_no)
    except (EmptyPage, InvalidPage):
        page = paginator.page(paginator.num_pages)
        
    reports = sorted(page.object_list,key=lambda o: o.status_int )
    google = WardMap(ward,reports)
    
    return render_to_response("wards/show.html",
                {"ward": ward,
                 "google": google,
                 "page":page,
                 "reports": reports                },
                context_instance=RequestContext(request))

def show_by_id(request,ward_id):
    ward = get_object_or_404(Ward, id=ward_id)
    return(show(request,ward))

def show_by_number( request, city_id, ward_no ):
    ward = get_object_or_404( Ward,city__id=city_id, number=ward_no)
    return(show(request,ward))

def show_by_slug( request, city_slug, ward_slug ):
    ward = get_object_or_404( Ward,city__slug=city_slug, slug=ward_slug)
    return(show(request,ward))
