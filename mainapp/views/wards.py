from django.shortcuts import render_to_response, get_object_or_404
from mainapp.models import City, Ward, WardMap, Report
from django.template import Context, RequestContext
from django.db import connection

def show_by_number( request, city_id, ward_no ):
    city= get_object_or_404(City, id=city_id)
    wards = Ward.objects.filter( city=city, number=ward_no)
    google = WardMap(wards[0],[])
    return render_to_response("wards/show.html",
                {"ward": wards[0],
                 "google": google,
                 "reports": [] },
                context_instance=RequestContext(request))    
    
def show( request, ward_id ):
    ward = get_object_or_404(Ward, id=ward_id)
    reports = Report.objects.filter( ward = ward, is_confirmed = True ).extra( select = { 'status' : """
        CASE 
        WHEN age( clock_timestamp(), created_at ) < interval '1 month' AND is_fixed = false THEN 'New Problems'
        WHEN age( clock_timestamp(), created_at ) > interval '1 month' AND is_fixed = false THEN 'Older Problems'
        WHEN age( clock_timestamp(), fixed_at ) < interval '1 month' AND is_fixed = true THEN 'Recently Fixed'
        WHEN age( clock_timestamp(), fixed_at ) > interval '1 month' AND is_fixed = true THEN 'Older Fixed Problems'
        ELSE 'Unknown Status'
        END """,
        'status_int' : """
        CASE 
        WHEN age( clock_timestamp(), created_at ) < interval '1 month' AND is_fixed = false THEN 1
        WHEN age( clock_timestamp(), created_at ) > interval '1 month' AND is_fixed = false THEN 2
        WHEN age( clock_timestamp(), fixed_at ) < interval '1 month' AND is_fixed = true THEN 3
        WHEN age( clock_timestamp(), fixed_at ) > interval '1 month' AND is_fixed = true THEN 4
        ELSE 0
        END """ }, order_by = ['status_int'] ) 
    
    google = WardMap(ward,reports)
        
    return render_to_response("wards/show.html",
                {"ward": ward,
                 "google": google,
                 "reports": reports },
                context_instance=RequestContext(request))