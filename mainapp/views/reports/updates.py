from django.shortcuts import render_to_response, get_object_or_404
from django.http import HttpResponseRedirect
from mainapp.models import Report, ReportUpdate, Ward, FixMyStreetMap, ReportCategory
from mainapp.forms import ReportForm,ReportUpdateForm
from django.template import Context, RequestContext

def new( request, report_id ):
    report = get_object_or_404(Report, id=report_id)
    if request.method == 'POST':    
        update_form = ReportUpdateForm( request.POST, user=request.user, report=report )
        if update_form.is_valid():
            update = update_form.save()
            # redirect after a POST
            if update.is_confirmed:
                return( HttpResponseRedirect( report.get_absolute_url() ) )
            else:       
                return( HttpResponseRedirect( '/reports/updates/create/' ) )
                
    else:
        update_form = ReportUpdateForm(initial={},user=request.user)
        
    return render_to_response("reports/show.html",
                {   "report": report,
                    "google":  FixMyStreetMap(report.point),
                    "update_form": update_form,
                 },
                context_instance=RequestContext(request))    

def create( request ):
    return render_to_response("reports/updates/create.html",
                {  },
                context_instance=RequestContext(request))    

def confirm( request, confirm_token ):
    update = get_object_or_404(ReportUpdate, confirm_token = confirm_token )
    
    if update.is_confirmed:
        return( HttpResponseRedirect( update.report.get_absolute_url() ))
    
    update.confirm()
    
    # redirect to report    
    return( HttpResponseRedirect( update.report.get_absolute_url() ))
