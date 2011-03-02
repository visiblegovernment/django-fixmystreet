from django.shortcuts import render_to_response, get_object_or_404
from django.http import HttpResponseRedirect
from mainapp.models import Report, ReportUpdate, Ward, FixMyStreetMap, ReportCategory
from mainapp.forms import ReportForm,ReportUpdateForm
from django.template import Context, RequestContext

def new( request, report_id ):
    report = get_object_or_404(Report, id=report_id)
    if request.method == 'POST':    
        update_form = ReportUpdateForm( request.POST )
        if update_form.is_valid():
            update = update_form.save(commit=False)
            update.is_fixed = request.POST.has_key('is_fixed')
            update.report=report
            update.save()    
            # redirect after a POST       
            return( HttpResponseRedirect( '/reports/updates/create/' ) )
                
    else:
        update_form = ReportUpdateForm()
        
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
    
    # is the update fixed?
    if update.is_fixed:
        update.report.is_fixed = True
        update.report.fixed_at = update.created_at
    
    update.is_confirmed = True    
    update.save()

    # we track a last updated time in the report to make statistics 
    # (such as on the front page) easier.  
    
    if not update.first_update:
        update.report.updated_at = update.created_at
    else:
        update.report.updated_at = update.report.created_at
        update.report.is_confirmed = True
 
    update.report.save()
         
    # redirect to report    
    return( HttpResponseRedirect( update.report.get_absolute_url() ))
