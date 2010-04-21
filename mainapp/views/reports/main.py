from django.shortcuts import render_to_response, get_object_or_404
from django.http import HttpResponseRedirect
from mainapp.models import Report, ReportUpdate, Ward, FixMyStreetMap, ReportCategory
from mainapp.forms import ReportForm,ReportUpdateForm
from django.template import Context, RequestContext
from django.contrib.gis.geos import *
from fixmystreet import settings
from django.utils.translation import ugettext as _

def create_report( request, is_confirmed = False):
    """
        Helper method used by both internal and Open311 API.
    """
    pnt = fromstr("POINT(" + request.POST["lon"] + " " + request.POST["lat"] + ")", srid=4326)         
    update_form = ReportUpdateForm( request.POST  )   
    report_form = ReportForm( request.POST, request.FILES )
        
    # this is a lot more complicated than it has to be because of the information
    # spread across two forms.
        
    if request.POST['category_id'] != "" and update_form.is_valid() and report_form.is_valid():
        report = report_form.save( commit = False )
        update = update_form.save(commit=False)
        #these are in the form for 'update'
        report.desc = update.desc
        report.author = update.author
        #this is in neither form
        report.category_id = request.POST['category_id']
        #this info is custom
        report.point = pnt
        report.ward = Ward.objects.get(geom__contains=pnt)
        report.is_confirmed = is_confirmed
        update.report = report
        update.first_update = True
        update.is_confirmed = is_confirmed
        update.created_at = report.created_at
        report.save()
        update.report = report
        update.save(request)
        return( report )
    else:
        return None

def new( request ):
    category_error = None

    if request.method == "POST":
        # TOFIX:category ID is checked for separately as it's not part of the report form
        if request.POST['category_id']:
            report = create_report(request)
            if report:
                return( HttpResponseRedirect( report.get_absolute_url() ))
            # otherwise, there was an error with one of the forms.
        else:
            category_error = _("Please select a category")
            
    else:
        pnt = fromstr("POINT(" + request.GET["lon"] + " " + request.GET["lat"] + ")", srid=4326)
        report_form = ReportForm()
        update_form = ReportUpdateForm()
    
    
    return render_to_response("reports/new.html",
                { "lat": pnt.y,
                  "lon": pnt.x,
                  "google":  FixMyStreetMap(pnt, True),
                  "categories": ReportCategory.objects.all().order_by("category_class"),
                  "report_form": report_form,
                  "update_form": update_form, 
                  "category_error" : category_error, },
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


