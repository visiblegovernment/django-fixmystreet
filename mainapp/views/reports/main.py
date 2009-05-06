from django.shortcuts import render_to_response, get_object_or_404
from django.http import HttpResponseRedirect
from mainapp.models import Report, ReportUpdate, Ward, FixMyStreetMap, ReportCategory
from mainapp.forms import ReportForm,ReportUpdateForm
from django.template import Context, RequestContext
from django.contrib.gis.geos import *
from fixmystreet import settings
from django.utils.translation import ugettext as _


def new( request ):
    category_error = None

    if request.method == "POST":
        pnt = fromstr("POINT(" + request.POST["lon"] + " " + request.POST["lat"] + ")", srid=4326)         
        f = request.POST.copy()
        update_form = ReportUpdateForm( {'email':request.POST['email'], 'desc':request.POST['desc'],
                                         'author':request.POST['author'], 'phone': request.POST['phone']})    
        report_form = ReportForm({'title' : request.POST['title']}, request.FILES )
        
        # this is a lot more complicated than it has to be because of the infortmation
        # spread across two records.
        
        if request.POST['category_id'] != "" and update_form.is_valid() and report_form.is_valid():
            report = report_form.save( commit = False )
            report.point = pnt
            report.category_id = request.POST['category_id']
            report.author = request.POST['author']
            report.desc = request.POST['desc']
            report.ward = Ward.objects.get(geom__contains=pnt)
            report.save()
            update = update_form.save(commit=False)
            update.report = report
            update.first_update = True
            update.created_at = report.created_at
            update.save()
            return( HttpResponseRedirect( report.get_absolute_url() ))
        
         # other form errors are handled by the form objects.
        if not request.POST['category_id']:
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
    return render_to_response("reports/show.html",
                { "report": report,
                  "ward":report.ward,
                  "updates": ReportUpdate.objects.filter(report=report, is_confirmed=True).order_by("created_at")[1:], 
                  "update_form": ReportUpdateForm(), 
                  "google":  FixMyStreetMap((report.point)) },
                context_instance=RequestContext(request))


