from django.shortcuts import render_to_response, get_object_or_404
from mainapp.models import City, Ward, WardMap, Report
from django.template import Context, RequestContext
from django.db import connection
from django.utils.translation import ugettext_lazy, ugettext as _
import datetime

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
        older_reports_link  = ward.get_absolute_url() + "?years_ago=%i" %( years_ago + 1)
    else:
        older_reports_link = None

    reports = Report.objects.filter( created_at__gte = date_range_start, created_at__lte=date_range_end, ward = ward, is_confirmed = True ).extra( select = { 'status' : """
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
        END """ }, order_by = ['status_int'] ) 
    
    google = WardMap(ward,reports)
        
    return render_to_response("wards/show.html",
                {"ward": ward,
                 "google": google,
                 "reports": reports,
                 "date_range_start": date_range_start,
                 "date_range_end": date_range_end,
                 "older_reports_link": older_reports_link
 #                "status_display" : [ _('New Problems'), _('Older Unresolved Problems'),  _('Recently Fixed'), _('Older Fixed Problems') ] 
                },
                context_instance=RequestContext(request))