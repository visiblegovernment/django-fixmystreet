#!/usr/bin/env python
# encoding: utf-8

import sys
import os

path = os.path.abspath(os.path.dirname(os.path.abspath(os.path.dirname(os.path.abspath(os.path.dirname(__file__))))))
sys.path.append(path)
os.environ['DJANGO_SETTINGS_MODULE'] = 'fixmystreet.settings'

import datetime
import time
from datetime import datetime as dt
from django.core.mail import send_mail, EmailMessage
from django.template.loader import render_to_string
from fixmystreet.mainapp.models import Ward,Report
from fixmystreet import settings
import codecs
import csv

class UnicodeReader:
    def __init__(self, f, dialect=csv.excel, encoding="utf-8", **kwds):
        self.reader = csv.reader(f, dialect=dialect, **kwds)
        self.encoding = encoding

    def next(self):
        row = self.reader.next()
        return [unicode(s, self.encoding) for s in row]

    def __iter__(self):
        return self


        
 
reader = UnicodeReader(open("./neigborhood_leaders.csv", "rb"))
for association, email in reader:
    print "sending email to: " + association + " " + email
    time.sleep(20)
    subject = render_to_string("emails/batch_reports/invitations/subject.txt")
    message = render_to_string("emails/batch_reports/invitations/message.html", 
                               {'assoc': association })
    msg = EmailMessage(subject, message,settings.EMAIL_FROM_USER,[email])
    msg.content_subtype = "html"  # Main content is now text/html
    msg.send()
