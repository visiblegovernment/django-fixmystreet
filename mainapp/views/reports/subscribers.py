from django.shortcuts import render_to_response, get_object_or_404
from django.http import HttpResponseRedirect
from mainapp.models import Report, ReportSubscriber
from mainapp.forms import ReportSubscriberForm
from django.template import Context, RequestContext
from django.utils.translation import ugettext as _

def new( request, report_id ):
    report = get_object_or_404(Report, id=report_id)
    error_msg = None
    
    if request.method == 'POST':    
        form = ReportSubscriberForm( request.POST )
        if form.is_valid():
           subscriber = form.save( commit = False )
           subscriber.report = report;
           if report.is_subscribed(subscriber.email):
               error_msg = _("You are already subscribed to this report.")
           else:
               subscriber.save(request)
               return( HttpResponseRedirect( '/reports/subscribers/create/' ) ) 
    else:
        form = ReportSubscriberForm()
        
    return render_to_response("reports/subscribers/new.html",
                {   "subscriber_form": form,
                    "report":  report,
                    "error_msg": error_msg, },
                context_instance=RequestContext(request))

def create( request ):
    return render_to_response("reports/subscribers/create.html",
                { },
                context_instance=RequestContext(request))
            
def confirm( request, confirm_token ):
    subscriber = get_object_or_404(ReportSubscriber, confirm_token = confirm_token )
    subscriber.is_confirmed = True
    subscriber.save(request)
    
    return render_to_response("reports/subscribers/confirm.html",
                {   "subscriber": subscriber, },
                context_instance=RequestContext(request))
    
def unsubscribe(request, confirm_token ):
    subscriber = get_object_or_404(ReportSubscriber, confirm_token = confirm_token )
    report = subscriber.report
    subscriber.delete()
    return render_to_response("reports/subscribers/message.html",
                {   "message": _("You have unsubscribed from updates to:") +  report.title, },
                context_instance=RequestContext(request))
    