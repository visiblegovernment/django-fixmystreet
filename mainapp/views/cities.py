from django.shortcuts import render_to_response, get_object_or_404
from mainapp.models import City, Ward, Report, ReportCounters, CityMap
from django.template import Context, RequestContext
from django.db.models import  Count

def index(request):    
    return render_to_response("cities/index.html",
                {"report_counts": City.objects.annotate(**ReportCounters('ward__report')).order_by('province__abbrev') },
                context_instance=RequestContext(request))


def show( request, city ):    
    #top problems
    top_problems = Report.objects.filter(ward__city=city,is_fixed=False).annotate(subscriber_count=Count('reportsubscriber' ) ).filter(subscriber_count__gte=1).order_by('-subscriber_count')[:5]
    if request.GET.has_key('test'):
        google = CityMap(city)
    else:
        google = None
        
    
    return render_to_response("cities/show.html",
                {"city":city,
                 "google": google,
                 'top_problems': top_problems,
                 'city_totals' : City.objects.filter(id=city.id).annotate(**ReportCounters('ward__report','10 years'))[0],
                 "report_counts": Ward.objects.filter(city=city).annotate(**ReportCounters('report'))
                  },
                 context_instance=RequestContext(request))

def show_by_id(request, city_id ):
    print "getting city by id"
    city = get_object_or_404(City, id=city_id)
    return( show(request,city )) 

def show_by_slug(request, city_slug ):
    print "getting city by slug"
    city = get_object_or_404(City, slug=city_slug)
    return( show(request,city )) 

def home( request, city, error_msg, disambiguate ):
    #top problems
    top_problems = Report.objects.filter(ward__city=city,is_fixed=False).annotate(subscriber_count=Count('reportsubscriber' ) ).filter(subscriber_count__gte=1).order_by('-subscriber_count')[:10]
    reports_with_photos = Report.objects.filter(is_confirmed=True, ward__city=city).exclude(photo='').order_by("-created_at")[:3]
    recent_reports = Report.objects.filter(is_confirmed=True, ward__city=city).order_by("-created_at")[:5]
        
    return render_to_response("cities/home.html",
                {"report_counts": City.objects.filter(id=city.id).annotate(ReportTotalCounters('ward__report','10 years'))[0],
                 "cities": City.objects.all(),
                 'city':city,
                 'top_problems': top_problems,
                 "reports_with_photos": reports_with_photos,
                 "recent_reports": recent_reports , 
                 'error_msg': error_msg,
                 'disambiguate':disambiguate },
                context_instance=RequestContext(request))    
    