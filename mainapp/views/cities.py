from django.shortcuts import render_to_response, get_object_or_404
from mainapp.models import City, Report, CitiesReportCountQuery, CityReportCountQuery, CityMap
from django.template import Context, RequestContext
from django.db.models import  Count

def index(request):    
    return render_to_response("cities/index.html",
                {"report_counts": CitiesReportCountQuery() },
                context_instance=RequestContext(request))


def show( request, city_id ):
    city = get_object_or_404(City, id=city_id)
    
    #top problems
    top_problems = Report.objects.filter(ward__city=city,is_fixed=False).annotate(subscriber_count=Count('reportsubscriber' ) ).filter(subscriber_count__gte=1).order_by('-subscriber_count')[:10]
    if request.GET.has_key('test'):
        google = CityMap(city)
    else:
        google = None
        
    return render_to_response("cities/show.html",
                {"city":city,
                 "google": google,
                 'top_problems': top_problems,
                 "report_counts": CityReportCountQuery(city) },
                 context_instance=RequestContext(request))

