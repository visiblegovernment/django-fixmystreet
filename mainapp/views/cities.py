from django.shortcuts import render_to_response, get_object_or_404
from mainapp.models import City, CitiesReportCountQuery, CityReportCountQuery, CityMap
from django.template import Context, RequestContext

def index(request):    
    return render_to_response("cities/index.html",
                {"report_counts": CitiesReportCountQuery() },
                context_instance=RequestContext(request))


def show( request, city_id ):
    city = get_object_or_404(City, id=city_id)
    if request.GET.has_key('test'):
        google = CityMap(city)
    else:
        google = None
        
    return render_to_response("cities/show.html",
                {"city":city,
                 "google": google,
                 "report_counts": CityReportCountQuery(city) },
                 context_instance=RequestContext(request))

