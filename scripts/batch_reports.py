#!/usr/bin/env python
# encoding: utf-8

import sys
import os

path = os.path.abspath(os.path.dirname(os.path.abspath(os.path.dirname(os.path.abspath(os.path.dirname(__file__))))))
sys.path.append(path)
os.environ['DJANGO_SETTINGS_MODULE'] = 'fixmystreet.settings'

import datetime
from datetime import datetime as dt
from django.core.mail import send_mail, EmailMessage
from django.template.loader import render_to_string
from fixmystreet.mainapp.models import Ward,Report
from fixmystreet import settings


reminder_email_count = 0
councillor_email_count = 0
#
## send new reports to ward councillors                    
#for ward in Ward.objects.all():    
#    new_reports = ward.report_set.filter(ward=ward,is_confirmed=True,is_fixed=False,sent_at__isnull=True).order_by("-created_at")                        
#    if len(new_reports) > 0 :
#        subject = render_to_string("emails/batch_reports/new_reports/subject.txt", 
#                               {'ward': ward })
#        message = render_to_string("emails/batch_reports/new_reports/message.html", 
#                               {'new_reports': new_reports, 'ward': ward })
#        
#        msg = EmailMessage(subject, message,settings.EMAIL_FROM_USER,[ward.councillor.email, settings.ADMIN_EMAIL])
#        msg.content_subtype = "html"  # Main content is now text/html
#        msg.send()
#
#        print "sending report for ward " + ward.name
#        new_reports.update(sent_at=dt.now())
#        councillor_email_count += 1

# send old reports that have not been updated
one_month_ago = dt.today() - datetime.timedelta(days=31)
reminder_reports = Report.objects.filter(is_confirmed=True, is_fixed = False, reminded_at__lte=one_month_ago, updated_at__lte=one_month_ago ).order_by("ward","-created_at")  

for report in reminder_reports:
    subject = render_to_string("emails/batch_reports/reminders/subject.txt", 
                               {'report': report })
    message = render_to_string("emails/batch_reports/reminders/message.txt", 
                               {'report': report })

    send_mail(subject, message, settings.EMAIL_FROM_USER,[report.first_update().email], fail_silently=False)

    report.reminded_at = dt.now()
    report.save()
    reminder_email_count += 1

# notify admin reports were run
send_mail('Ward Summary Reports Run %s' % ( dt.now()  ), 
          '%d Report Summaries Sent to Councillors\n%d Reminders Sent' %( councillor_email_count, reminder_email_count ), 
              settings.EMAIL_FROM_USER,[settings.ADMIN_EMAIL], fail_silently=False)

