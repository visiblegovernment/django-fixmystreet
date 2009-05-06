from django.shortcuts import render_to_response, get_object_or_404
from django.http import HttpResponseRedirect
from mainapp.models import Report
from django.template import Context, RequestContext
from fixmystreet import settings
from django.template.loader import render_to_string
from django.core.mail import send_mail

def new( request, report_id ):
    report = get_object_or_404(Report, id=report_id)
    if request.method == 'GET':
        return render_to_response("reports/flags/new.html",
                { "report": report },
                context_instance=RequestContext(request))
    else:
        # send email flagging this report as being potentially offensive.
        message = render_to_string("emails/flag_report/message.txt", 
                    { 'report': report })
        send_mail('FixMyStreet.ca Report Flagged as Offensive', message, 
                   settings.EMAIL_FROM_USER,[settings.ADMIN_EMAIL], fail_silently=False)
        return HttpResponseRedirect(report.get_absolute_url() + '/flags/thanks')

def thanks( request, report_id ):
    return render_to_response("reports/flags/thanks.html", {},
                context_instance=RequestContext(request))
