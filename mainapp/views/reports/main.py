from django.shortcuts import render_to_response, get_object_or_404
from django.http import HttpResponseRedirect,Http404
from mainapp.models import DictToPoint,Report, ReportUpdate, Ward, FixMyStreetMap, ReportCategory
from mainapp.forms import ReportForm,ReportUpdateForm
from django.template import Context, RequestContext
from django.contrib.gis.geos import *
from fixmystreet import settings
from django.utils.translation import ugettext as _



def new( request ):
    if request.method == "POST":
        pnt = DictToPoint( request.POST ).pnt()
        report_form = ReportForm( request.POST, request.FILES )
        # this checks update is_valid too
        if report_form.is_valid():
            # this saves the update as part of the report.
            report = report_form.save()
            if report:
                return( HttpResponseRedirect( report.get_absolute_url() ))
    else:
        pnt = DictToPoint( request.GET ).pnt()
        report_form = ReportForm(initial={ 'lat': request.GET['lat'],
                                           'lon': request.GET['lon'] } )

    ward=None
    wards = Ward.objects.filter(geom__contains=pnt)[:1]
    if wards:
        ward = wards[0]

    return render_to_response("reports/new.html",
                { "google": FixMyStreetMap(pnt, True),
                  "report_form": report_form,
                  "update_form": report_form.update_form,
                  'ward':ward },
                context_instance=RequestContext(request))
    
        
def show( request, report_id ):
    report = get_object_or_404(Report, id=report_id)
    subscribers = report.reportsubscriber_set.count() + 1
    return render_to_response("reports/show.html",
                { "report": report,
                  "subscribers": subscribers,
                  "ward":report.ward,
                  "updates": ReportUpdate.objects.filter(report=report, is_confirmed=True).order_by("created_at")[1:], 
                  "update_form": ReportUpdateForm(), 
                  "google":  FixMyStreetMap((report.point)) },
                context_instance=RequestContext(request))


